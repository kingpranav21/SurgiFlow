#!/usr/bin/env python3
"""Publish light synthetic events to Kafka on an interval.

Usage:
  export KAFKA_BOOTSTRAP_SERVERS=localhost:19092
  export PIPELINE_MODE=kafka
  python scripts/stream_live.py --interval 3
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ.setdefault("PIPELINE_MODE", "kafka")

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.models import EventLog, Inventory  # noqa: E402
from app.services import kafka_io  # noqa: E402


def tick(db, touch_db: bool) -> None:
    rows = list(db.scalars(select(Inventory)).all())
    if not rows:
        print("No inventory")
        return
    # Prefer non-demo-critical rows for random consume
    candidates = [r for r in rows if not (r.hospital_id == "H001" and r.product_id == "STAPLER-01")]
    inv = random.choice(candidates or rows)
    event_type = "INVENTORY_HEARTBEAT"
    if inv.quantity > 8 and random.random() < 0.35:
        inv.quantity -= 1
        inv.updated_at = datetime.utcnow()
        event_type = "INVENTORY_CONSUMED"
        if touch_db:
            db.add(
                EventLog(
                    event_type=event_type,
                    hospital_id=inv.hospital_id,
                    product_id=inv.product_id,
                    payload={"quantity": 1, "remaining": inv.quantity},
                    event_time=datetime.utcnow(),
                )
            )
            db.commit()
    else:
        if touch_db:
            db.add(
                EventLog(
                    event_type=event_type,
                    hospital_id=inv.hospital_id,
                    product_id=inv.product_id,
                    payload={"quantity": inv.quantity},
                    event_time=datetime.utcnow(),
                )
            )
            db.commit()

    ok = kafka_io.publish_inventory(inv.hospital_id, inv.product_id, inv.quantity, event_type)
    kafka_io.flush()
    print(f"{datetime.utcnow().isoformat()} {event_type} {inv.hospital_id}/{inv.product_id}={inv.quantity} kafka={ok}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--no-db", action="store_true", help="Kafka only, do not update Postgres")
    args = parser.parse_args()
    s = get_settings()
    if not s.kafka_bootstrap_servers:
        print("Set KAFKA_BOOTSTRAP_SERVERS first")
        sys.exit(1)
    engine = create_engine(s.database_url)
    SessionLocal = sessionmaker(bind=engine)
    print(f"Streaming to {s.kafka_bootstrap_servers} every {args.interval}s")
    while True:
        with SessionLocal() as db:
            tick(db, touch_db=not args.no_db)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
