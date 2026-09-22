#!/usr/bin/env python3
"""Generate ongoing synthetic consumption / inventory tick events for live demos."""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import EventLog, Inventory  # noqa: E402
from app.services.risk_engine import compute_risks  # noqa: E402


def tick(db, recompute: bool) -> None:
    rows = db.scalars(select(Inventory)).all()
    if not rows:
        print("No inventory rows.")
        return
    inv = random.choice(rows)
    # Soft consume 0–1 unit, never go below 1 for non-demo rows
    if inv.hospital_id == "H001" and inv.product_id == "STAPLER-01":
        # Keep demo stock stable unless explicitly simulating
        db.add(
            EventLog(
                event_type="INVENTORY_HEARTBEAT",
                hospital_id=inv.hospital_id,
                product_id=inv.product_id,
                payload={"quantity": inv.quantity},
                event_time=datetime.utcnow(),
            )
        )
    else:
        delta = random.choice([0, 0, 1])
        if delta and inv.quantity > 5:
            inv.quantity -= delta
            inv.updated_at = datetime.utcnow()
            db.add(
                EventLog(
                    event_type="INVENTORY_CONSUMED",
                    hospital_id=inv.hospital_id,
                    product_id=inv.product_id,
                    payload={"quantity": delta, "remaining": inv.quantity},
                    event_time=datetime.utcnow(),
                )
            )
    db.commit()
    if recompute:
        compute_risks(db)
    print(f"{datetime.utcnow().isoformat()} tick ok")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", "postgresql://surgiflow:surgiflow@localhost:5432/surgiflow"))
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--recompute", action="store_true")
    args = parser.parse_args()

    engine = create_engine(args.database_url)
    SessionLocal = sessionmaker(bind=engine)
    while True:
        with SessionLocal() as db:
            tick(db, args.recompute)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
