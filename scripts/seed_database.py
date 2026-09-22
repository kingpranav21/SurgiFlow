#!/usr/bin/env python3
"""Seed SurgiFlow with deterministic synthetic demo data.

Demo story:
  H001 Mumbai Central — STAPLER-01 stock=9
  7 laparoscopic procedures scheduled tomorrow
  SHP182 from SUP12 — 50 units, ON_TIME (delay via What-If)
  H004 Mumbai West — STAPLER-01 surplus (21, safety 8)
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Allow running from repo root or scripts/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import (  # noqa: E402
    EventLog,
    Hospital,
    Inventory,
    Order,
    Procedure,
    ProcedureRequirement,
    Product,
    Recommendation,
    RiskPrediction,
    DemandForecast,
    Shipment,
    Supplier,
)
from app.services.risk_engine import compute_risks  # noqa: E402


HOSPITALS = [
    ("H001", "Mumbai Central Surgical", "Mumbai", "MH"),
    ("H002", "Pune Medical Center", "Pune", "MH"),
    ("H003", "Delhi Surgical Hub", "Delhi", "DL"),
    ("H004", "Mumbai West Specialty", "Mumbai", "MH"),
    ("H005", "Bengaluru Care Hospital", "Bengaluru", "KA"),
    ("H006", "Hyderabad Ortho Center", "Hyderabad", "TS"),
    ("H007", "Chennai Procedure Wing", "Chennai", "TN"),
    ("H008", "Ahmedabad MedSupply Hub", "Ahmedabad", "GJ"),
    ("H009", "Kolkata Surgical Network", "Kolkata", "WB"),
    ("H010", "Jaipur Care Alliance", "Jaipur", "RJ"),
    ("H011", "Kochi Coastal Medical", "Kochi", "KL"),
    ("H012", "Chandigarh North Clinic", "Chandigarh", "CH"),
]

PRODUCTS = [
    ("STAPLER-01", "Endoscopic Stapler", "Stapling", 4200.00, 8),
    ("TROC-10", "Trocar 10mm", "Access", 850.00, 10),
    ("TROC-5", "Trocar 5mm", "Access", 650.00, 10),
    ("CLIP-CART", "Clip Cartridge", "Clipping", 1200.00, 6),
    ("SUTURE-01", "Absorbable Suture Pack", "Closure", 180.00, 20),
    ("SPEC-BAG", "Specimen Retrieval Bag", "Retrieval", 320.00, 8),
    ("CATH-01", "Surgical Catheter Set", "Accessories", 210.00, 12),
    ("MESH-01", "Hernia Mesh Sheet", "Implants", 2400.00, 5),
    ("SCOPE-01", "Laparoscope Lens Cover", "Optics", 95.00, 15),
    ("IRRI-01", "Irrigation Tubing Kit", "Fluid", 140.00, 12),
    ("ELEC-HOOK", "Electrocautery Hook", "Energy", 780.00, 6),
    ("GRASP-01", "Grasping Forceps Tip", "Instruments", 560.00, 8),
]

# Expand to ~40 products with variants
for i in range(13, 41):
    PRODUCTS.append((f"SKU-{i:03d}", f"Surgical SKU {i}", "General", 100.0 + i * 10, 5))

SUPPLIERS = [
    ("SUP12", "MedDevice Logistics India", 0.91),
    ("SUP03", "OrthoStream Distributors", 0.88),
    ("SUP07", "AccessPort Supply Co", 0.94),
    ("SUP01", "ClipTech Regional", 0.86),
    ("SUP09", "SutureLink Partners", 0.92),
]

REQUIREMENTS = [
    ("LAPAROSCOPIC_CHOLECYSTECTOMY", "TROC-10", 2),
    ("LAPAROSCOPIC_CHOLECYSTECTOMY", "TROC-5", 2),
    ("LAPAROSCOPIC_CHOLECYSTECTOMY", "CLIP-CART", 1),
    ("LAPAROSCOPIC_CHOLECYSTECTOMY", "SUTURE-01", 2),
    ("LAPAROSCOPIC_CHOLECYSTECTOMY", "SPEC-BAG", 1),
    ("LAPAROSCOPIC_CHOLECYSTECTOMY", "STAPLER-01", 1),
    ("APPENDECTOMY", "TROC-10", 1),
    ("APPENDECTOMY", "TROC-5", 2),
    ("APPENDECTOMY", "CLIP-CART", 1),
    ("APPENDECTOMY", "SUTURE-01", 2),
    ("HERNIA_REPAIR", "MESH-01", 1),
    ("HERNIA_REPAIR", "SUTURE-01", 3),
    ("HERNIA_REPAIR", "TROC-5", 1),
    ("ARTHROSCOPY", "CATH-01", 1),
    ("ARTHROSCOPY", "IRRI-01", 2),
    ("ARTHROSCOPY", "SCOPE-01", 1),
]


def wipe(db: Session) -> None:
    for table in (
        EventLog,
        Recommendation,
        RiskPrediction,
        DemandForecast,
        Shipment,
        Order,
        Procedure,
        Inventory,
        ProcedureRequirement,
        Product,
        Hospital,
        Supplier,
    ):
        db.query(table).delete()
    db.commit()


def seed(db: Session, now: datetime | None = None) -> None:
    now = now or datetime.utcnow()
    wipe(db)

    for hid, name, city, state in HOSPITALS:
        db.add(Hospital(hospital_id=hid, name=name, city=city, state=state))
    for pid, name, cat, cost, safety in PRODUCTS:
        db.add(Product(product_id=pid, name=name, category=cat, unit_cost=cost, safety_stock=safety))
    for sid, name, score in SUPPLIERS:
        db.add(Supplier(supplier_id=sid, name=name, reliability_score=score))
    db.flush()  # products must exist before FK from procedure_requirements

    for ptype, pid, qty in REQUIREMENTS:
        db.add(ProcedureRequirement(procedure_type=ptype, product_id=pid, quantity_per_procedure=qty))
    db.flush()

    # Baseline healthy inventory across network
    core_products = [p[0] for p in PRODUCTS[:12]]
    for hid, *_ in HOSPITALS:
        for pid in core_products:
            qty = 25
            if hid == "H001" and pid == "STAPLER-01":
                qty = 9  # demo: tight stock
            elif hid == "H004" and pid == "STAPLER-01":
                qty = 21  # demo: surplus
            elif hid == "H001" and pid in ("TROC-10", "TROC-5"):
                qty = 30  # cover 7×2 procedure demand + baseline
            elif hid == "H001" and pid in ("CLIP-CART", "SUTURE-01", "SPEC-BAG"):
                qty = 25
            db.add(Inventory(hospital_id=hid, product_id=pid, quantity=qty, updated_at=now))

    # 7 laparoscopic procedures at H001 tomorrow (drive stapler demand)
    tomorrow = now + timedelta(hours=22)
    for i in range(1, 8):
        db.add(
            Procedure(
                procedure_id=f"P880{i}",
                hospital_id="H001",
                procedure_type="LAPAROSCOPIC_CHOLECYSTECTOMY",
                scheduled_time=tomorrow + timedelta(minutes=30 * i),
                status="SCHEDULED",
            )
        )
        db.add(
            EventLog(
                event_type="PROCEDURE_SCHEDULED",
                hospital_id="H001",
                product_id="STAPLER-01",
                payload={"procedure_id": f"P880{i}", "procedure_type": "LAPAROSCOPIC_CHOLECYSTECTOMY"},
                event_time=now - timedelta(minutes=10 - i),
            )
        )

    # Assorted other procedures (healthy)
    db.add(
        Procedure(
            procedure_id="P9901",
            hospital_id="H005",
            procedure_type="ARTHROSCOPY",
            scheduled_time=now + timedelta(days=1),
            status="SCHEDULED",
        )
    )
    db.add(
        Procedure(
            procedure_id="P9902",
            hospital_id="H003",
            procedure_type="HERNIA_REPAIR",
            scheduled_time=now + timedelta(days=2),
            status="SCHEDULED",
        )
    )

    # Critical demo shipment — ON_TIME initially (18h delay via What-If)
    eta = now + timedelta(hours=20)
    db.add(
        Shipment(
            shipment_id="SHP182",
            supplier_id="SUP12",
            hospital_id="H001",
            product_id="STAPLER-01",
            quantity=50,
            status="ON_TIME",
            expected_delivery=eta,
            delay_hours=0,
            updated_at=now,
        )
    )
    db.add(
        EventLog(
            event_type="SHIPMENT_CREATED",
            hospital_id="H001",
            product_id="STAPLER-01",
            supplier_id="SUP12",
            payload={"shipment_id": "SHP182", "quantity": 50, "status": "ON_TIME"},
            event_time=now - timedelta(hours=2),
        )
    )

    # Other shipments
    db.add(
        Shipment(
            shipment_id="SHP201",
            supplier_id="SUP07",
            hospital_id="H002",
            product_id="TROC-10",
            quantity=40,
            status="IN_TRANSIT",
            expected_delivery=now + timedelta(hours=12),
            delay_hours=0,
            updated_at=now,
        )
    )

    db.add(
        Order(
            order_id="ORD9821",
            hospital_id="H001",
            product_id="STAPLER-01",
            quantity=50,
            status="PLACED",
            created_at=now - timedelta(days=2),
        )
    )
    db.add(
        EventLog(
            event_type="ORDER_PLACED",
            hospital_id="H001",
            product_id="STAPLER-01",
            payload={"order_id": "ORD9821", "quantity": 50},
            event_time=now - timedelta(days=2),
        )
    )
    db.add(
        EventLog(
            event_type="INVENTORY_UPDATED",
            hospital_id="H001",
            product_id="STAPLER-01",
            payload={"quantity": 9},
            event_time=now - timedelta(hours=1),
        )
    )
    db.add(
        EventLog(
            event_type="INVENTORY_UPDATED",
            hospital_id="H004",
            product_id="STAPLER-01",
            payload={"quantity": 21, "note": "Surplus available for rebalance"},
            event_time=now - timedelta(hours=3),
        )
    )
    # Extra network color: healthy activity elsewhere
    db.add(
        EventLog(
            event_type="PROCEDURE_SCHEDULED",
            hospital_id="H005",
            product_id="CATH-01",
            payload={"procedure_id": "P9901", "procedure_type": "ARTHROSCOPY"},
            event_time=now - timedelta(minutes=25),
        )
    )
    db.add(
        EventLog(
            event_type="SHIPMENT_CREATED",
            hospital_id="H002",
            product_id="TROC-10",
            supplier_id="SUP07",
            payload={"shipment_id": "SHP201", "quantity": 40, "status": "IN_TRANSIT"},
            event_time=now - timedelta(hours=5),
        )
    )

    db.commit()
    compute_risks(db)
    print("Seeded SurgiFlow demo data.")
    print("  H001 STAPLER-01 qty=9 | 7 procedures | SHP182 ON_TIME")
    print("  H004 STAPLER-01 qty=21 (surplus)")
    print("  Run What-If delay on SHP182 to trigger HIGH risk + H004→H001 transfer.")


def apply_schema(engine) -> None:
    schema_path = ROOT / "infra" / "postgres" / "schema.sql"
    sql = schema_path.read_text()
    with engine.begin() as conn:
        conn.execute(text(sql))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SurgiFlow database")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://surgiflow:surgiflow@localhost:5432/surgiflow"),
    )
    parser.add_argument("--apply-schema", action="store_true", help="Apply schema.sql before seed")
    args = parser.parse_args()

    engine = create_engine(args.database_url)
    if args.apply_schema:
        apply_schema(engine)
        print("Schema applied.")

    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    main()
