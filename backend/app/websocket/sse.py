import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import EventLog, RiskPrediction

router = APIRouter()


@router.get("/api/stream/events")
async def stream_events(request: Request):
    """Server-Sent Events: push new event_log + risk snapshot every 2s."""

    async def generator():
        last_event_id = 0
        while True:
            if await request.is_disconnected():
                break
            db = SessionLocal()
            try:
                events = db.scalars(
                    select(EventLog)
                    .where(EventLog.event_id > last_event_id)
                    .order_by(EventLog.event_id.asc())
                    .limit(20)
                ).all()
                for e in events:
                    last_event_id = e.event_id
                    payload = {
                        "type": "event",
                        "data": {
                            "event_id": e.event_id,
                            "event_type": e.event_type,
                            "hospital_id": e.hospital_id,
                            "product_id": e.product_id,
                            "supplier_id": e.supplier_id,
                            "payload": e.payload,
                            "event_time": e.event_time.isoformat() if e.event_time else None,
                        },
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                # Periodic risk pulse for dashboard badges
                high = (
                    db.scalars(select(RiskPrediction).where(RiskPrediction.risk_level == "HIGH")).all()
                )
                # Deduplicate by hospital×product keeping latest created_at
                seen = {}
                for r in high:
                    key = (r.hospital_id, r.product_id)
                    if key not in seen or (r.created_at and seen[key].created_at and r.created_at > seen[key].created_at):
                        seen[key] = r
                pulse = {
                    "type": "risk_pulse",
                    "data": {
                        "critical_risks": len(seen),
                        "ts": datetime.utcnow().isoformat(),
                    },
                }
                yield f"data: {json.dumps(pulse)}\n\n"
            finally:
                db.close()
            await asyncio.sleep(2)

    return StreamingResponse(generator(), media_type="text/event-stream")
