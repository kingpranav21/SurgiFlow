from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    hospitals: int
    products: int
    healthy_pct: float
    critical_risks: int
    medium_risks: int
    pending_recommendations: int
    delayed_shipments: int
    status_headline: str = "Network status unknown"
    status_detail: str = ""
    next_action: str = ""


class RiskOut(BaseModel):
    prediction_id: Optional[int] = None
    hospital_id: str
    product_id: str
    product_name: Optional[str] = None
    hospital_name: Optional[str] = None
    risk_level: str
    current_inventory: int
    projected_demand: int
    projected_inventory: int
    predicted_stockout: Optional[datetime] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    plain_english: Optional[str] = None


class RecommendationOut(BaseModel):
    recommendation_id: int
    source_hospital_id: str
    target_hospital_id: str
    source_hospital_name: Optional[str] = None
    target_hospital_name: Optional[str] = None
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    reason: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    plain_english: Optional[str] = None


class ForecastOut(BaseModel):
    hospital_id: str
    product_id: str
    window_hours: int
    forecasted_demand: int
    baseline_consumption: float
    procedure_demand: int
    current_inventory: int
    safety_stock: int
    projected_inventory: int
    series: list[dict[str, Any]] = Field(default_factory=list)


class EventOut(BaseModel):
    event_id: int
    event_type: str
    hospital_id: Optional[str] = None
    product_id: Optional[str] = None
    supplier_id: Optional[str] = None
    hospital_name: Optional[str] = None
    product_name: Optional[str] = None
    message: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    event_time: datetime


class DemoSpotlight(BaseModel):
    hospital_id: str
    hospital_name: str
    product_id: str
    product_name: str
    current_stock: int
    safety_stock: int
    scheduled_procedures: int
    procedure_type: str
    procedure_demand: int
    shipment_id: str
    shipment_status: str
    delay_hours: int
    expected_delivery: Optional[datetime] = None
    supplier_name: Optional[str] = None
    risk_level: str
    projected_inventory: int
    projected_demand: int
    surplus_hospital_id: str
    surplus_hospital_name: str
    surplus_quantity: int
    story: str
    pipeline_hint: str


class SimulateDelayRequest(BaseModel):
    shipment_id: str = "SHP182"
    delay_hours: int = Field(default=18, ge=1, le=72)


class SimulateDelayResponse(BaseModel):
    shipment_id: str
    delay_hours: int
    status: str
    expected_delivery: Optional[datetime]
    critical_risks_before: int
    critical_risks_after: int
    risks: list[RiskOut]
    recommendations: list[RecommendationOut]
    explanation: str = ""
    next_step: str = ""


class HospitalOut(BaseModel):
    hospital_id: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None


class ProductOut(BaseModel):
    product_id: str
    name: str
    category: Optional[str] = None
    unit_cost: Optional[float] = None
    safety_stock: int


class ApplyTransferRequest(BaseModel):
    recommendation_id: int
