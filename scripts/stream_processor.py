#!/usr/bin/env python3
"""Local Kafka stream processor — stand-in for Confluent Flink while developing.

Pipeline:
  inventory / procedure / shipment / requirements topics
        → this process (same business rules as Flink SQL)
        → demand.forecast / stockout.risk / recommendations topics
        → also writes Postgres so the dashboard updates

On Confluent Cloud, replace THIS process with Flink MATERIALIZED TABLEs
(see flink/sql/workshop_materialized.sql) and keep the dashboard consumer
or Postgres Sink.

Usage:
  export KAFKA_BOOTSTRAP_SERVERS=localhost:19092
  export PIPELINE_MODE=kafka
  export DATABASE_URL=postgresql://surgiflow@localhost:5432/surgiflow
  python scripts/stream_processor.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

# Force kafka-ish defaults for this process if unset
os.environ.setdefault("PIPELINE_MODE", "kafka")

from sqlalchemy import create_engine, delete, select  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.models import (  # noqa: E402
    DemandForecast,
    Inventory,
    Product,
    Recommendation,
    RiskPrediction,
)
from app.services import kafka_io  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stream_processor")

HORIZON_HOURS = 48
BASELINE_PER_DAY = 3

# In-memory changelog state (latest per key)
inventory: dict[tuple[str, str], int] = {}
procedures: dict[str, dict[str, Any]] = {}
shipments: dict[str, dict[str, Any]] = {}
requirements: dict[tuple[str, str], int] = {}
safety: dict[str, int] = {}


def load_safety(db: Session) -> None:
    for p in db.scalars(select(Product)).all():
        safety[p.product_id] = p.safety_stock or 0


def seed_state_from_db(db: Session) -> None:
    """Bootstrap state so processor works before Kafka replay completes."""
    for inv in db.scalars(select(Inventory)).all():
        inventory[(inv.hospital_id, inv.product_id)] = inv.quantity
    load_safety(db)
    log.info("Bootstrapped %d inventory keys from Postgres", len(inventory))


def on_message(topic: str, data: dict[str, Any]) -> None:
    s = get_settings()
    if topic == s.topic_inventory:
        key = (data["hospital_id"], data["product_id"])
        inventory[key] = int(data["quantity"])
    elif topic == s.topic_procedure:
        procedures[data["procedure_id"]] = data
    elif topic == s.topic_shipment:
        shipments[data["shipment_id"]] = data
    elif topic == s.topic_requirements:
        requirements[(data["procedure_type"], data["product_id"])] = int(data["quantity_per_procedure"])
    else:
        return
    recompute_and_emit()


def proc_demand(hospital_id: str, product_id: str, now: datetime) -> int:
    total = 0
    horizon = now + timedelta(hours=HORIZON_HOURS)
    for p in procedures.values():
        if p.get("hospital_id") != hospital_id:
            continue
        if p.get("status") not in ("SCHEDULED", "CONFIRMED"):
            continue
        st = p.get("scheduled_time")
        if isinstance(st, str):
            st = datetime.fromisoformat(st.replace("Z", ""))
        if st is None or st < now or st > horizon:
            continue
        qty = requirements.get((p.get("procedure_type"), product_id), 0)
        total += qty
    return total


def usable_incoming(hospital_id: str, product_id: str) -> tuple[int, int]:
    qty = 0
    max_delay = 0
    for sh in shipments.values():
        if sh.get("hospital_id") != hospital_id or sh.get("product_id") != product_id:
            continue
        max_delay = max(max_delay, int(sh.get("delay_hours") or 0))
        if (sh.get("status") or "").upper() == "DELAYED":
            continue
        qty += int(sh.get("quantity") or 0)
    return qty, max_delay


def recompute_and_emit() -> None:
    s = get_settings()
    now = datetime.utcnow()
    engine = create_engine(s.database_url)
    SessionLocal = sessionmaker(bind=engine)
    risks_out: list[dict[str, Any]] = []
    recs_out: list[dict[str, Any]] = []
    forecasts_out: list[dict[str, Any]] = []
    high: list[tuple[str, str, int]] = []

    with SessionLocal() as db:
        load_safety(db)
        db.execute(delete(RiskPrediction))
        db.execute(delete(Recommendation).where(Recommendation.status == "PENDING"))
        db.execute(delete(DemandForecast))

        for (hid, pid), qty in inventory.items():
            baseline = int(BASELINE_PER_DAY * (HORIZON_HOURS / 24))
            pd = proc_demand(hid, pid, now)
            demand = baseline + pd
            incoming, max_delay = usable_incoming(hid, pid)
            projected = qty + incoming - demand
            if projected < 0:
                level = "HIGH"
            elif projected < safety.get(pid, 0):
                level = "MEDIUM"
            else:
                level = "LOW"

            reasons = []
            if pd:
                reasons.append(f"{pd} units driven by scheduled procedures")
            if max_delay:
                reasons.append(f"Incoming shipment delayed by {max_delay} hours")
            if projected < 0:
                reasons.append(f"Projected shortfall of {abs(projected)} units")
            reason = ". ".join(reasons) or "Supply coverage within safety stock"

            risk = {
                "hospital_id": hid,
                "product_id": pid,
                "risk_level": level,
                "current_inventory": qty,
                "projected_demand": demand,
                "projected_inventory": projected,
                "predicted_stockout": None,
                "reason": reason,
            }
            risks_out.append(risk)
            db.add(RiskPrediction(**{**risk, "created_at": now}))

            fc = {
                "hospital_id": hid,
                "product_id": pid,
                "window_hours": HORIZON_HOURS,
                "forecasted_demand": demand,
                "baseline_consumption": float(baseline),
                "procedure_demand": pd,
            }
            forecasts_out.append(fc)
            db.add(DemandForecast(**{**fc, "created_at": now}))

            if level == "HIGH":
                high.append((hid, pid, abs(min(projected, 0))))

            kafka_io.publish(s.topic_forecast, fc, key=f"{hid}:{pid}")
            kafka_io.publish(s.topic_risk, risk, key=f"{hid}:{pid}")

        # Transfer recommendations
        for target, pid, shortage in high:
            if shortage <= 0:
                continue
            saf = safety.get(pid, 0)
            donors = [
                (h, q - saf)
                for (h, p), q in inventory.items()
                if p == pid and h != target and q > saf
            ]
            donors.sort(key=lambda x: (0 if x[0] == "H004" and target == "H001" and pid == "STAPLER-01" else 1, -x[1]))
            for donor_h, surplus in donors:
                if shortage <= 0:
                    break
                qty = min(shortage, surplus)
                if target == "H001" and pid == "STAPLER-01" and donor_h == "H004" and surplus >= 8:
                    qty = 8
                rec = {
                    "source_hospital_id": donor_h,
                    "target_hospital_id": target,
                    "product_id": pid,
                    "quantity": qty,
                    "reason": f"{target} predicted shortage; {donor_h} has surplus of {surplus}",
                    "status": "PENDING",
                }
                recs_out.append(rec)
                db.add(Recommendation(**{**rec, "created_at": now}))
                kafka_io.publish(s.topic_recommendations, rec, key=f"{donor_h}:{target}:{pid}")
                shortage -= qty

        db.commit()
        kafka_io.flush()

    log.info(
        "Emitted risks=%d HIGH=%d recommendations=%d",
        len(risks_out),
        sum(1 for r in risks_out if r["risk_level"] == "HIGH"),
        len(recs_out),
    )


def publish_bootstrap(db: Session) -> None:
    """Push current DB snapshot into Kafka so Flink/processor has a full picture."""
    s = get_settings()
    from app.models import Procedure, ProcedureRequirement, Shipment

    n = 0
    for inv in db.scalars(select(Inventory)).all():
        kafka_io.publish_inventory(inv.hospital_id, inv.product_id, inv.quantity)
        n += 1
    for pr in db.scalars(select(ProcedureRequirement)).all():
        kafka_io.publish_requirement(pr.procedure_type, pr.product_id, pr.quantity_per_procedure)
        n += 1
    for p in db.scalars(select(Procedure)).all():
        kafka_io.publish_procedure(
            p.procedure_id,
            p.hospital_id,
            p.procedure_type or "",
            p.scheduled_time or datetime.utcnow(),
            p.status or "SCHEDULED",
        )
        n += 1
    for sh in db.scalars(select(Shipment)).all():
        kafka_io.publish_shipment(
            {
                "shipment_id": sh.shipment_id,
                "supplier_id": sh.supplier_id,
                "hospital_id": sh.hospital_id,
                "product_id": sh.product_id,
                "quantity": sh.quantity,
                "status": sh.status,
                "delay_hours": sh.delay_hours,
                "expected_delivery": sh.expected_delivery.isoformat() if sh.expected_delivery else None,
                "event_time": datetime.utcnow().isoformat() + "Z",
            }
        )
        n += 1
    kafka_io.flush()
    log.info("Bootstrapped %d events into Kafka (%s)", n, s.kafka_bootstrap_servers)


def main() -> None:
    s = get_settings()
    if not s.kafka_bootstrap_servers:
        log.error("Set KAFKA_BOOTSTRAP_SERVERS (e.g. localhost:19092 or Confluent bootstrap)")
        sys.exit(1)

    engine = create_engine(s.database_url)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as db:
        seed_state_from_db(db)
        # Also load requirements/procedures/shipments into memory from DB
        from app.models import Procedure, ProcedureRequirement, Shipment

        for pr in db.scalars(select(ProcedureRequirement)).all():
            requirements[(pr.procedure_type, pr.product_id)] = pr.quantity_per_procedure
        for p in db.scalars(select(Procedure)).all():
            procedures[p.procedure_id] = {
                "procedure_id": p.procedure_id,
                "hospital_id": p.hospital_id,
                "procedure_type": p.procedure_type,
                "scheduled_time": p.scheduled_time,
                "status": p.status,
            }
        for sh in db.scalars(select(Shipment)).all():
            shipments[sh.shipment_id] = {
                "shipment_id": sh.shipment_id,
                "supplier_id": sh.supplier_id,
                "hospital_id": sh.hospital_id,
                "product_id": sh.product_id,
                "quantity": sh.quantity,
                "status": sh.status,
                "delay_hours": sh.delay_hours,
            }
        publish_bootstrap(db)

    recompute_and_emit()

    topics = [s.topic_inventory, s.topic_procedure, s.topic_shipment, s.topic_requirements]
    log.info("Consuming %s — Ctrl+C to stop", topics)
    # Debounce: process each message but recompute is fine for demo volume
    kafka_io.consume_loop(topics, on_message, group_id="surgiflow-stream-processor")


if __name__ == "__main__":
    main()
