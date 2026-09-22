from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApplyTransferRequest,
    DashboardSummary,
    DemoSpotlight,
    EventOut,
    ForecastOut,
    HospitalOut,
    ProductOut,
    RecommendationOut,
    RiskOut,
    SimulateDelayRequest,
    SimulateDelayResponse,
)
from app.config import get_settings
from app.db.session import get_db
from app.models import (
    DemandForecast,
    EventLog,
    Hospital,
    Inventory,
    Procedure,
    Product,
    Recommendation,
    RiskPrediction,
    Shipment,
    Supplier,
)
from app.services import risk_engine

router = APIRouter(prefix="/api")

EVENT_LABELS = {
    "PROCEDURE_SCHEDULED": "Procedure scheduled",
    "SHIPMENT_CREATED": "Shipment created",
    "SHIPMENT_DELAYED": "Shipment delayed",
    "ORDER_PLACED": "Order placed",
    "INVENTORY_UPDATED": "Inventory updated",
    "INVENTORY_CONSUMED": "Inventory consumed",
    "INVENTORY_HEARTBEAT": "Inventory heartbeat",
    "TRANSFER_APPLIED": "Transfer applied",
    "RISK_ENGINE_RECOMPUTED": "Risks recalculated",
}


def _latest_risks(db: Session) -> list[RiskPrediction]:
    """Return latest risk row per hospital×product."""
    rows = db.scalars(select(RiskPrediction).order_by(RiskPrediction.created_at.desc())).all()
    seen: set[tuple[str, str]] = set()
    latest: list[RiskPrediction] = []
    for r in rows:
        key = (r.hospital_id or "", r.product_id or "")
        if key in seen:
            continue
        seen.add(key)
        latest.append(r)
    return latest


def _plain_risk(r: RiskPrediction, product_name: str | None, hospital_name: str | None) -> str:
    pname = product_name or r.product_id
    hname = hospital_name or r.hospital_id
    if r.risk_level == "HIGH":
        return (
            f"{hname} may run out of {pname} within the next 48 hours "
            f"(stock {r.current_inventory}, need ~{r.projected_demand})."
        )
    if r.risk_level == "MEDIUM":
        return f"{hname} is below safety stock for {pname}. Watch closely."
    return f"{hname} has healthy coverage for {pname}."


def _enrich_risk(db: Session, r: RiskPrediction) -> RiskOut:
    product = db.get(Product, r.product_id) if r.product_id else None
    hospital = db.get(Hospital, r.hospital_id) if r.hospital_id else None
    pname = product.name if product else None
    hname = hospital.name if hospital else None
    return RiskOut(
        prediction_id=r.prediction_id,
        hospital_id=r.hospital_id or "",
        product_id=r.product_id or "",
        product_name=pname,
        hospital_name=hname,
        risk_level=r.risk_level or "LOW",
        current_inventory=r.current_inventory or 0,
        projected_demand=r.projected_demand or 0,
        projected_inventory=r.projected_inventory or 0,
        predicted_stockout=r.predicted_stockout,
        reason=r.reason,
        created_at=r.created_at,
        plain_english=_plain_risk(r, pname, hname),
    )


def _enrich_rec(db: Session, r: Recommendation) -> RecommendationOut:
    product = db.get(Product, r.product_id) if r.product_id else None
    source = db.get(Hospital, r.source_hospital_id) if r.source_hospital_id else None
    target = db.get(Hospital, r.target_hospital_id) if r.target_hospital_id else None
    pname = product.name if product else r.product_id
    sname = source.name if source else r.source_hospital_id
    tname = target.name if target else r.target_hospital_id
    return RecommendationOut(
        recommendation_id=r.recommendation_id,
        source_hospital_id=r.source_hospital_id or "",
        target_hospital_id=r.target_hospital_id or "",
        source_hospital_name=sname,
        target_hospital_name=tname,
        product_id=r.product_id or "",
        product_name=product.name if product else None,
        quantity=r.quantity or 0,
        reason=r.reason,
        status=r.status,
        created_at=r.created_at,
        plain_english=(
            f"Move {r.quantity} {pname} from {sname} (surplus) to {tname} (at risk) "
            f"to protect scheduled surgeries."
        ),
    )


def _event_message(db: Session, e: EventLog) -> str:
    payload = e.payload or {}
    label = EVENT_LABELS.get(e.event_type, e.event_type.replace("_", " ").title())
    hospital = db.get(Hospital, e.hospital_id) if e.hospital_id else None
    product = db.get(Product, e.product_id) if e.product_id else None
    h = hospital.name if hospital else (e.hospital_id or "")
    p = product.name if product else (e.product_id or "")

    if e.event_type == "SHIPMENT_DELAYED":
        hours = payload.get("delay_hours", "?")
        return f"{label}: supplier shipment for {p} to {h} delayed by {hours} hours"
    if e.event_type == "PROCEDURE_SCHEDULED":
        ptype = payload.get("procedure_type", "procedure")
        return f"{label}: {h} booked {ptype.replace('_', ' ').title()}"
    if e.event_type == "TRANSFER_APPLIED":
        return (
            f"{label}: moved {payload.get('quantity', '?')} {p} "
            f"from {payload.get('from')} → {payload.get('to')}"
        )
    if e.event_type == "ORDER_PLACED":
        return f"{label}: {h} ordered {payload.get('quantity', '?')} {p}"
    if e.event_type == "INVENTORY_UPDATED":
        return f"{label}: {h} now holds {payload.get('quantity', '?')} {p}"
    if e.event_type == "RISK_ENGINE_RECOMPUTED":
        return f"{label}: streaming rules refreshed network risk board"
    if h and p:
        return f"{label}: {h} · {p}"
    if h:
        return f"{label}: {h}"
    return label


def _status_copy(critical: int, pending: int, delayed: int) -> tuple[str, str, str]:
    if critical > 0 and pending > 0:
        return (
            f"{critical} critical stockout risk{'s' if critical != 1 else ''} need action",
            "Streaming forecast shows demand exceeding available supply. Review recommended transfers.",
            "Open Recommendations and apply a transfer, or inspect Inventory Risk for details.",
        )
    if critical > 0:
        return (
            f"{critical} critical risk{'s' if critical != 1 else ''} detected",
            "A shipment delay or procedure surge is pushing inventory below projected demand.",
            "Check Inventory Risk, then run or review Recommendations.",
        )
    if delayed > 0:
        return (
            "Network stable after rebalancing",
            "A shipment is still marked delayed, but transfers or stock cover the demand window.",
            "Reset the demo from What-If if you want to replay the delay scenario.",
        )
    return (
        "All clear — supply coverage looks healthy",
        "Inventory, procedures, and on-time shipments currently cover the next 48 hours.",
        "Try What-If: delay shipment SHP182 by 18 hours to see SurgiFlow react in real time.",
    )


@router.get("/health")
def health():
    return {"status": "ok", "service": "surgiflow"}


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    hospitals = db.scalar(select(func.count()).select_from(Hospital)) or 0
    products = db.scalar(select(func.count()).select_from(Product)) or 0
    risks = _latest_risks(db)
    critical = sum(1 for r in risks if r.risk_level == "HIGH")
    medium = sum(1 for r in risks if r.risk_level == "MEDIUM")
    total = len(risks) or 1
    healthy = sum(1 for r in risks if r.risk_level == "LOW")
    pending = (
        db.scalar(select(func.count()).select_from(Recommendation).where(Recommendation.status == "PENDING")) or 0
    )
    delayed = (
        db.scalar(select(func.count()).select_from(Shipment).where(Shipment.status == "DELAYED")) or 0
    )
    headline, detail, next_action = _status_copy(critical, pending, delayed)
    return DashboardSummary(
        hospitals=hospitals,
        products=products,
        healthy_pct=round(100.0 * healthy / total, 1),
        critical_risks=critical,
        medium_risks=medium,
        pending_recommendations=pending,
        delayed_shipments=delayed,
        status_headline=headline,
        status_detail=detail,
        next_action=next_action,
    )


@router.get("/dashboard/spotlight", response_model=DemoSpotlight)
def dashboard_spotlight(db: Session = Depends(get_db)):
    """Human-readable demo focus: H001 Endoscopic Stapler story."""
    hospital = db.get(Hospital, "H001")
    product = db.get(Product, "STAPLER-01")
    inv = db.get(Inventory, ("H001", "STAPLER-01"))
    donor = db.get(Hospital, "H004")
    donor_inv = db.get(Inventory, ("H004", "STAPLER-01"))
    shipment = db.get(Shipment, "SHP182")
    supplier = db.get(Supplier, shipment.supplier_id) if shipment else None
    procs = db.scalars(
        select(Procedure).where(
            Procedure.hospital_id == "H001",
            Procedure.procedure_type == "LAPAROSCOPIC_CHOLECYSTECTOMY",
            Procedure.status.in_(["SCHEDULED", "CONFIRMED"]),
        )
    ).all()
    risk = db.scalars(
        select(RiskPrediction)
        .where(RiskPrediction.hospital_id == "H001", RiskPrediction.product_id == "STAPLER-01")
        .order_by(RiskPrediction.created_at.desc())
        .limit(1)
    ).first()

    stock = inv.quantity if inv else 0
    demand = risk.projected_demand if risk else 0
    proj = risk.projected_inventory if risk else 0
    level = risk.risk_level if risk else "LOW"
    status = shipment.status if shipment else "UNKNOWN"
    delay = shipment.delay_hours if shipment else 0
    surplus = max(0, (donor_inv.quantity if donor_inv else 0) - (product.safety_stock if product else 0))

    if level == "HIGH":
        story = (
            f"Mumbai Central Surgical only has {stock} Endoscopic Staplers on hand, but "
            f"{len(procs)} laparoscopic cases need about {demand} units in the next 48 hours. "
            f"Shipment SHP182 is {status.lower()}"
            + (f" by {delay} hours" if delay else "")
            + ", so inbound supply is not counted. Surplus at Mumbai West can cover the gap."
        )
    elif status == "DELAYED":
        story = (
            f"Shipment SHP182 is delayed, but coverage was restored"
            f"{' after a network transfer' if stock >= 15 else ''}. "
            f"Current stock at Mumbai Central is {stock} staplers."
        )
    else:
        story = (
            f"Mumbai Central Surgical has {stock} Endoscopic Staplers and {len(procs)} procedures booked. "
            f"Shipment SHP182 from the supplier is still on time, so projected coverage stays healthy. "
            f"Delay that shipment in What-If to watch risk appear in real time."
        )

    return DemoSpotlight(
        hospital_id="H001",
        hospital_name=hospital.name if hospital else "H001",
        product_id="STAPLER-01",
        product_name=product.name if product else "STAPLER-01",
        current_stock=stock,
        safety_stock=product.safety_stock if product else 8,
        scheduled_procedures=len(procs),
        procedure_type="Laparoscopic cholecystectomy",
        procedure_demand=len(procs),  # 1 stapler per procedure
        shipment_id="SHP182",
        shipment_status=status or "UNKNOWN",
        delay_hours=delay or 0,
        expected_delivery=shipment.expected_delivery if shipment else None,
        supplier_name=supplier.name if supplier else None,
        risk_level=level or "LOW",
        projected_inventory=proj or 0,
        projected_demand=demand or 0,
        surplus_hospital_id="H004",
        surplus_hospital_name=donor.name if donor else "H004",
        surplus_quantity=surplus,
        story=story,
        pipeline_hint=(
            "Postgres change → Kafka (CDC) → Flink forecast/risk → recommendation → dashboard"
        ),
    )


@router.get("/hospitals", response_model=list[HospitalOut])
def list_hospitals(db: Session = Depends(get_db)):
    rows = db.scalars(select(Hospital).order_by(Hospital.hospital_id)).all()
    return [HospitalOut(hospital_id=h.hospital_id, name=h.name, city=h.city, state=h.state) for h in rows]


@router.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    rows = db.scalars(select(Product).order_by(Product.product_id)).all()
    return [
        ProductOut(
            product_id=p.product_id,
            name=p.name,
            category=p.category,
            unit_cost=float(p.unit_cost) if p.unit_cost is not None else None,
            safety_stock=p.safety_stock or 0,
        )
        for p in rows
    ]


@router.get("/risks", response_model=list[RiskOut])
def list_risks(db: Session = Depends(get_db), level: str | None = None):
    risks = _latest_risks(db)
    if level:
        risks = [r for r in risks if (r.risk_level or "").upper() == level.upper()]
    # HIGH first
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    risks.sort(key=lambda r: order.get(r.risk_level or "LOW", 9))
    return [_enrich_risk(db, r) for r in risks]


@router.get("/risks/{hospital_id}/{product_id}", response_model=RiskOut)
def get_risk(hospital_id: str, product_id: str, db: Session = Depends(get_db)):
    row = db.scalars(
        select(RiskPrediction)
        .where(RiskPrediction.hospital_id == hospital_id, RiskPrediction.product_id == product_id)
        .order_by(RiskPrediction.created_at.desc())
        .limit(1)
    ).first()
    if not row:
        raise HTTPException(404, "Risk not found")
    return _enrich_risk(db, row)


@router.get("/forecasts/{hospital_id}/{product_id}", response_model=ForecastOut)
def get_forecast(hospital_id: str, product_id: str, db: Session = Depends(get_db)):
    fc = db.scalars(
        select(DemandForecast)
        .where(DemandForecast.hospital_id == hospital_id, DemandForecast.product_id == product_id)
        .order_by(DemandForecast.created_at.desc())
        .limit(1)
    ).first()
    inv = db.get(Inventory, (hospital_id, product_id))
    product = db.get(Product, product_id)
    risk = db.scalars(
        select(RiskPrediction)
        .where(RiskPrediction.hospital_id == hospital_id, RiskPrediction.product_id == product_id)
        .order_by(RiskPrediction.created_at.desc())
        .limit(1)
    ).first()

    current = inv.quantity if inv else 0
    safety = product.safety_stock if product else 0
    demand = fc.forecasted_demand if fc else 0
    window = fc.window_hours if fc else 48
    projected = risk.projected_inventory if risk else current - demand

    # Build simple series for chart
    series = []
    now = datetime.utcnow()
    burn = demand / window if window else 0
    for h in range(0, window + 1, 4):
        series.append(
            {
                "hour": h,
                "time": (now + timedelta(hours=h)).isoformat(),
                "inventory": max(0, round(current - burn * h, 1)),
                "demand_cumulative": round(burn * h, 1),
                "safety_stock": safety,
            }
        )

    return ForecastOut(
        hospital_id=hospital_id,
        product_id=product_id,
        window_hours=window,
        forecasted_demand=demand or 0,
        baseline_consumption=float(fc.baseline_consumption or 0) if fc else 0,
        procedure_demand=fc.procedure_demand or 0 if fc else 0,
        current_inventory=current,
        safety_stock=safety,
        projected_inventory=projected or 0,
        series=series,
    )


@router.get("/recommendations", response_model=list[RecommendationOut])
def list_recommendations(db: Session = Depends(get_db)):
    rows = db.scalars(select(Recommendation).order_by(Recommendation.created_at.desc())).all()
    return [_enrich_rec(db, r) for r in rows]


@router.get("/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db), limit: int = 50):
    rows = db.scalars(select(EventLog).order_by(EventLog.event_time.desc()).limit(limit)).all()
    out: list[EventOut] = []
    for e in rows:
        hospital = db.get(Hospital, e.hospital_id) if e.hospital_id else None
        product = db.get(Product, e.product_id) if e.product_id else None
        out.append(
            EventOut(
                event_id=e.event_id,
                event_type=e.event_type,
                hospital_id=e.hospital_id,
                product_id=e.product_id,
                supplier_id=e.supplier_id,
                hospital_name=hospital.name if hospital else None,
                product_name=product.name if product else None,
                message=_event_message(db, e),
                payload=e.payload,
                event_time=e.event_time,
            )
        )
    return out


@router.post("/simulate/shipment-delay", response_model=SimulateDelayResponse)
def simulate_shipment_delay(body: SimulateDelayRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    before = sum(1 for r in _latest_risks(db) if r.risk_level == "HIGH")

    try:
        shipment = risk_engine.apply_shipment_delay(db, body.shipment_id, body.delay_hours)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e

    if settings.use_local_risk_engine:
        risk_engine.compute_risks(db)

    after_risks = _latest_risks(db)
    after = sum(1 for r in after_risks if r.risk_level == "HIGH")
    recs = db.scalars(
        select(Recommendation).where(Recommendation.status == "PENDING").order_by(Recommendation.created_at.desc())
    ).all()

    explanation = (
        f"Shipment {shipment.shipment_id} is now DELAYED by {body.delay_hours} hours, so inbound staplers "
        f"no longer count toward the next 48-hour supply window. Critical risks moved from {before} to {after}."
    )
    next_step = (
        "Open Recommendations and apply the H004 → H001 transfer to protect the scheduled surgeries."
        if after > before
        else "Review Inventory Risk to see how coverage changed."
    )

    return SimulateDelayResponse(
        shipment_id=shipment.shipment_id,
        delay_hours=shipment.delay_hours,
        status=shipment.status or "DELAYED",
        expected_delivery=shipment.expected_delivery,
        critical_risks_before=before,
        critical_risks_after=after,
        risks=[_enrich_risk(db, r) for r in after_risks if r.risk_level == "HIGH"],
        recommendations=[_enrich_rec(db, r) for r in recs],
        explanation=explanation,
        next_step=next_step,
    )


@router.post("/demo/reset")
def reset_demo(db: Session = Depends(get_db)):
    """Reset SHP182 to ON_TIME and recompute — replay the demo without reseeding everything."""
    settings = get_settings()
    shipment = db.get(Shipment, "SHP182")
    if not shipment:
        raise HTTPException(404, "Demo shipment SHP182 not found — run seed_database.py")

    if shipment.delay_hours:
        if shipment.expected_delivery:
            shipment.expected_delivery = shipment.expected_delivery - timedelta(hours=shipment.delay_hours)
        shipment.delay_hours = 0
    shipment.status = "ON_TIME"
    shipment.updated_at = datetime.utcnow()

    h001 = db.get(Inventory, ("H001", "STAPLER-01"))
    h004 = db.get(Inventory, ("H004", "STAPLER-01"))
    if h001:
        h001.quantity = 9
        h001.updated_at = datetime.utcnow()
    if h004:
        h004.quantity = 21
        h004.updated_at = datetime.utcnow()

    db.add(
        EventLog(
            event_type="SHIPMENT_CREATED",
            hospital_id="H001",
            product_id="STAPLER-01",
            supplier_id=shipment.supplier_id,
            payload={"shipment_id": "SHP182", "status": "ON_TIME", "note": "Demo reset"},
            event_time=datetime.utcnow(),
        )
    )
    db.commit()

    try:
        from app.services import kafka_io

        kafka_io.publish_shipment(
            {
                "shipment_id": shipment.shipment_id,
                "supplier_id": shipment.supplier_id,
                "hospital_id": shipment.hospital_id,
                "product_id": shipment.product_id,
                "quantity": shipment.quantity,
                "status": "ON_TIME",
                "delay_hours": 0,
                "expected_delivery": shipment.expected_delivery.isoformat() if shipment.expected_delivery else None,
                "event_time": datetime.utcnow().isoformat() + "Z",
            }
        )
        if h001:
            kafka_io.publish_inventory(h001.hospital_id, h001.product_id, h001.quantity)
        if h004:
            kafka_io.publish_inventory(h004.hospital_id, h004.product_id, h004.quantity)
        kafka_io.flush()
    except Exception:  # noqa: BLE001
        pass

    if settings.use_local_risk_engine:
        risk_engine.compute_risks(db)

    return {
        "status": "ok",
        "message": "Demo reset: SHP182 is ON_TIME, H001 stock=9, H004 stock=21. Critical risks should be 0.",
        "pipeline_mode": settings.pipeline_mode,
        "kafka_enabled": settings.kafka_enabled,
    }


@router.post("/recommendations/apply", response_model=RecommendationOut)
def apply_recommendation(body: ApplyTransferRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        rec = risk_engine.apply_transfer(db, body.recommendation_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    out = _enrich_rec(db, rec)

    if settings.use_local_risk_engine:
        risk_engine.compute_risks(db)

    return out


@router.get("/pipeline/status")
def pipeline_status():
    """Kafka / pipeline connectivity status."""
    s = get_settings()
    return {
        "pipeline_mode": s.pipeline_mode,
        "kafka_enabled": s.kafka_enabled,
        "kafka_bootstrap_servers": s.effective_bootstrap or None,
        "use_local_risk_engine": s.use_local_risk_engine,
        "topics": {
            "inventory": s.topic_inventory,
            "procedure": s.topic_procedure,
            "shipment": s.topic_shipment,
            "forecast": s.topic_forecast,
            "risk": s.topic_risk,
            "recommendations": s.topic_recommendations,
        },
        "hint": (
            "Set PIPELINE_MODE=hybrid|kafka and KAFKA_BOOTSTRAP_SERVERS, "
            "run scripts/stream_processor.py (local) or Flink SQL (Confluent)."
            if not s.kafka_enabled
            else "Kafka publish path is ON. Ensure Flink or stream_processor is consuming."
        ),
    }


@router.post("/risks/recompute")
def recompute_risks(db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.use_local_risk_engine:
        return {
            "status": "skipped",
            "reason": "streaming mode — Flink/stream_processor owns risk computation",
        }
    risks = risk_engine.compute_risks(db)
    return {"status": "ok", "risk_count": len(risks)}
