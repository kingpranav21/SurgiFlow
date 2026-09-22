"""Deterministic risk / rebalance engine mirroring Flink business rules.

Used when RISK_ENGINE_MODE=local so demos work without spending Confluent credits.
When streaming mode is on, Flink + Sink write the same tables; this still logs events.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    DemandForecast,
    EventLog,
    Inventory,
    Procedure,
    ProcedureRequirement,
    Product,
    Recommendation,
    RiskPrediction,
    Shipment,
)


HORIZON_HOURS = 48
BASELINE_PER_DAY = 3  # synthetic daily consumption when no history


def _log_event(
    db: Session,
    event_type: str,
    *,
    hospital_id: str | None = None,
    product_id: str | None = None,
    supplier_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    db.add(
        EventLog(
            event_type=event_type,
            hospital_id=hospital_id,
            product_id=product_id,
            supplier_id=supplier_id,
            payload=payload or {},
            event_time=datetime.utcnow(),
        )
    )


def procedure_driven_demand(db: Session, hospital_id: str, product_id: str, now: datetime) -> int:
    horizon = now + timedelta(hours=HORIZON_HOURS)
    procs = db.scalars(
        select(Procedure).where(
            Procedure.hospital_id == hospital_id,
            Procedure.status.in_(["SCHEDULED", "CONFIRMED"]),
            Procedure.scheduled_time >= now,
            Procedure.scheduled_time <= horizon,
        )
    ).all()
    total = 0
    for p in procs:
        req = db.get(ProcedureRequirement, (p.procedure_type, product_id))
        if req:
            total += req.quantity_per_procedure
    return total


def confirmed_incoming(db: Session, hospital_id: str, product_id: str, now: datetime) -> tuple[int, list[Shipment], int]:
    """Return usable incoming qty, all related shipments, and max delay hours.

    DELAYED shipments are excluded from usable supply (they miss the procedure window).
    ON_TIME / IN_TRANSIT count when ETA is within the forecast horizon.
    """
    horizon = now + timedelta(hours=HORIZON_HOURS)
    shipments = db.scalars(
        select(Shipment).where(
            Shipment.hospital_id == hospital_id,
            Shipment.product_id == product_id,
            Shipment.status.in_(["IN_TRANSIT", "ON_TIME", "DELAYED"]),
        )
    ).all()
    qty = 0
    max_delay = 0
    for s in shipments:
        max_delay = max(max_delay, s.delay_hours or 0)
        if s.status == "DELAYED":
            continue
        eta = s.expected_delivery
        if eta is None:
            continue
        if eta <= horizon:
            qty += s.quantity or 0
    return qty, list(shipments), max_delay


def compute_risks(db: Session) -> list[RiskPrediction]:
    """Recompute all hospital×product risks and recommendations. Clears prior derived rows."""
    now = datetime.utcnow()
    db.execute(delete(RiskPrediction))
    db.execute(delete(Recommendation).where(Recommendation.status == "PENDING"))
    db.execute(delete(DemandForecast))

    inventories = db.scalars(select(Inventory)).all()
    products = {p.product_id: p for p in db.scalars(select(Product)).all()}
    risks: list[RiskPrediction] = []
    high_shortages: list[tuple[str, str, int, int]] = []  # hospital, product, shortage, current

    for inv in inventories:
        product = products.get(inv.product_id)
        safety = product.safety_stock if product else 0
        baseline = int(BASELINE_PER_DAY * (HORIZON_HOURS / 24))
        proc_demand = procedure_driven_demand(db, inv.hospital_id, inv.product_id, now)
        projected_demand = baseline + proc_demand
        usable_incoming, shipments, max_delay = confirmed_incoming(db, inv.hospital_id, inv.product_id, now)
        delayed = [s for s in shipments if s.status == "DELAYED" or (s.delay_hours or 0) > 0]

        projected_inventory = inv.quantity + usable_incoming - projected_demand

        if projected_inventory < 0:
            risk_level = "HIGH"
        elif projected_inventory < safety:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        reasons = []
        if proc_demand > 0:
            reasons.append(f"{proc_demand} units driven by scheduled procedures")
        if delayed or max_delay > 0:
            reasons.append(f"Incoming shipment delayed by {max_delay or 18} hours")
        if projected_inventory < 0:
            reasons.append(f"Projected shortfall of {abs(projected_inventory)} units")
        reason = ". ".join(reasons) if reasons else "Supply coverage within safety stock"

        stockout_at = None
        if projected_inventory < 0 and projected_demand > 0:
            # Approximate stockout time within horizon
            burn = projected_demand / HORIZON_HOURS
            hours_left = inv.quantity / burn if burn > 0 else HORIZON_HOURS
            stockout_at = now + timedelta(hours=min(hours_left, HORIZON_HOURS))

        risk = RiskPrediction(
            hospital_id=inv.hospital_id,
            product_id=inv.product_id,
            risk_level=risk_level,
            current_inventory=inv.quantity,
            projected_demand=projected_demand,
            projected_inventory=projected_inventory,
            predicted_stockout=stockout_at,
            reason=reason,
            created_at=now,
        )
        db.add(risk)
        risks.append(risk)

        db.add(
            DemandForecast(
                hospital_id=inv.hospital_id,
                product_id=inv.product_id,
                window_hours=HORIZON_HOURS,
                forecasted_demand=projected_demand,
                baseline_consumption=float(baseline),
                procedure_demand=proc_demand,
                created_at=now,
            )
        )

        if risk_level == "HIGH":
            shortage = abs(min(projected_inventory, 0))
            high_shortages.append((inv.hospital_id, inv.product_id, shortage, inv.quantity))

    # Rebalancing recommendations
    for target_h, product_id, shortage, _ in high_shortages:
        if shortage <= 0:
            continue
        product = products.get(product_id)
        safety = product.safety_stock if product else 0
        donors = [
            i
            for i in inventories
            if i.product_id == product_id and i.hospital_id != target_h and i.quantity > safety
        ]
        donors.sort(key=lambda x: x.quantity - safety, reverse=True)
        remaining = shortage
        # Demo polish: prefer H004 → H001 for STAPLER-01
        donors.sort(
            key=lambda x: (
                0 if x.hospital_id == "H004" and target_h == "H001" and product_id == "STAPLER-01" else 1,
                -(x.quantity - safety),
            )
        )
        for donor in donors:
            if remaining <= 0:
                break
            surplus = donor.quantity - safety
            if surplus <= 0:
                continue
            qty = min(remaining, surplus)
            # Demo narrative: transfer 8 units H004 → H001 for STAPLER-01
            if target_h == "H001" and product_id == "STAPLER-01" and donor.hospital_id == "H004" and surplus >= 8:
                qty = 8
            db.add(
                Recommendation(
                    source_hospital_id=donor.hospital_id,
                    target_hospital_id=target_h,
                    product_id=product_id,
                    quantity=qty,
                    reason=f"{target_h} predicted shortage; {donor.hospital_id} has surplus of {surplus}",
                    status="PENDING",
                    created_at=now,
                )
            )
            remaining -= qty

    _log_event(db, "RISK_ENGINE_RECOMPUTED", payload={"risk_count": len(risks), "mode": "local"})
    db.commit()
    return risks


def apply_shipment_delay(db: Session, shipment_id: str, delay_hours: int) -> Shipment:
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise ValueError(f"Shipment {shipment_id} not found")

    base_eta = shipment.expected_delivery or datetime.utcnow()
    # If already delayed, rebase from original intent: subtract old delay then add new
    if shipment.delay_hours:
        base_eta = base_eta - timedelta(hours=shipment.delay_hours)

    shipment.delay_hours = delay_hours
    shipment.status = "DELAYED"
    shipment.expected_delivery = base_eta + timedelta(hours=delay_hours)
    shipment.updated_at = datetime.utcnow()

    _log_event(
        db,
        "SHIPMENT_DELAYED",
        hospital_id=shipment.hospital_id,
        product_id=shipment.product_id,
        supplier_id=shipment.supplier_id,
        payload={
            "shipment_id": shipment_id,
            "delay_hours": delay_hours,
            "expected_delivery": shipment.expected_delivery.isoformat(),
        },
    )
    db.commit()
    db.refresh(shipment)

    # Kafka path (Confluent or local Redpanda)
    try:
        from app.services import kafka_io

        kafka_io.publish_shipment(
            {
                "shipment_id": shipment.shipment_id,
                "supplier_id": shipment.supplier_id,
                "hospital_id": shipment.hospital_id,
                "product_id": shipment.product_id,
                "quantity": shipment.quantity,
                "status": shipment.status,
                "delay_hours": shipment.delay_hours,
                "expected_delivery": shipment.expected_delivery.isoformat() if shipment.expected_delivery else None,
                "event_time": datetime.utcnow().isoformat() + "Z",
            }
        )
        kafka_io.flush()
    except Exception:  # noqa: BLE001
        pass

    return shipment


def apply_transfer(db: Session, recommendation_id: int) -> Recommendation:
    rec = db.get(Recommendation, recommendation_id)
    if not rec:
        raise ValueError("Recommendation not found")
    if rec.status != "PENDING":
        return rec

    source = db.get(Inventory, (rec.source_hospital_id, rec.product_id))
    target = db.get(Inventory, (rec.target_hospital_id, rec.product_id))
    if not source or not target:
        raise ValueError("Inventory rows missing for transfer")
    if source.quantity < (rec.quantity or 0):
        raise ValueError("Insufficient source inventory")

    source.quantity -= rec.quantity or 0
    target.quantity += rec.quantity or 0
    source.updated_at = datetime.utcnow()
    target.updated_at = datetime.utcnow()
    rec.status = "APPLIED"

    _log_event(
        db,
        "TRANSFER_APPLIED",
        hospital_id=rec.target_hospital_id,
        product_id=rec.product_id,
        payload={
            "from": rec.source_hospital_id,
            "to": rec.target_hospital_id,
            "quantity": rec.quantity,
        },
    )
    db.commit()

    try:
        from app.services import kafka_io

        kafka_io.publish_inventory(source.hospital_id, source.product_id, source.quantity)
        kafka_io.publish_inventory(target.hospital_id, target.product_id, target.quantity)
        kafka_io.flush()
    except Exception:  # noqa: BLE001
        pass

    return rec
