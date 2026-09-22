#!/usr/bin/env python3
"""Run the deterministic demo scenario: delay SHP182 and print risk/recommendation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import Recommendation, RiskPrediction  # noqa: E402
from app.services.risk_engine import apply_shipment_delay, compute_risks  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", "postgresql://surgiflow:surgiflow@localhost:5432/surgiflow"))
    parser.add_argument("--delay-hours", type=int, default=18)
    parser.add_argument("--shipment-id", default="SHP182")
    args = parser.parse_args()

    engine = create_engine(args.database_url)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as db:
        before = db.scalars(select(RiskPrediction).where(RiskPrediction.risk_level == "HIGH")).all()
        print(f"Critical risks before: {len({(r.hospital_id, r.product_id) for r in before})}")
        apply_shipment_delay(db, args.shipment_id, args.delay_hours)
        compute_risks(db)
        highs = db.scalars(select(RiskPrediction).where(RiskPrediction.risk_level == "HIGH")).all()
        seen = {}
        for r in highs:
            seen[(r.hospital_id, r.product_id)] = r
        print(f"Critical risks after: {len(seen)}")
        for r in seen.values():
            print(f"  {r.hospital_id} {r.product_id} stock={r.current_inventory} demand={r.projected_demand} proj={r.projected_inventory}")
            print(f"    {r.reason}")
        recs = db.scalars(select(Recommendation).where(Recommendation.status == "PENDING")).all()
        for rec in recs:
            print(f"  TRANSFER {rec.quantity} {rec.product_id}: {rec.source_hospital_id} → {rec.target_hospital_id}")


if __name__ == "__main__":
    main()
