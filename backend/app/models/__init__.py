from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Hospital(Base):
    __tablename__ = "hospitals"
    hospital_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    safety_stock: Mapped[int] = mapped_column(Integer, default=0)


class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    reliability_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))


class Inventory(Base):
    __tablename__ = "inventory"
    hospital_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Procedure(Base):
    __tablename__ = "procedures"
    procedure_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    hospital_id: Mapped[str] = mapped_column(String(50))
    procedure_type: Mapped[Optional[str]] = mapped_column(String(100))
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[Optional[str]] = mapped_column(String(50))


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    hospital_id: Mapped[str] = mapped_column(String(50))
    product_id: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Shipment(Base):
    __tablename__ = "shipments"
    shipment_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(50))
    hospital_id: Mapped[str] = mapped_column(String(50))
    product_id: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    expected_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delay_hours: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProcedureRequirement(Base):
    __tablename__ = "procedure_requirements"
    procedure_type: Mapped[str] = mapped_column(String(100), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    quantity_per_procedure: Mapped[int] = mapped_column(Integer)


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    prediction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hospital_id: Mapped[Optional[str]] = mapped_column(String(50))
    product_id: Mapped[Optional[str]] = mapped_column(String(50))
    risk_level: Mapped[Optional[str]] = mapped_column(String(20))
    current_inventory: Mapped[Optional[int]] = mapped_column(Integer)
    projected_demand: Mapped[Optional[int]] = mapped_column(Integer)
    projected_inventory: Mapped[Optional[int]] = mapped_column(Integer)
    predicted_stockout: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"
    recommendation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_hospital_id: Mapped[Optional[str]] = mapped_column(String(50))
    target_hospital_id: Mapped[Optional[str]] = mapped_column(String(50))
    product_id: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"
    forecast_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hospital_id: Mapped[Optional[str]] = mapped_column(String(50))
    product_id: Mapped[Optional[str]] = mapped_column(String(50))
    window_hours: Mapped[Optional[int]] = mapped_column(Integer)
    forecasted_demand: Mapped[Optional[int]] = mapped_column(Integer)
    baseline_consumption: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    procedure_demand: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EventLog(Base):
    __tablename__ = "event_log"
    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100))
    hospital_id: Mapped[Optional[str]] = mapped_column(String(50))
    product_id: Mapped[Optional[str]] = mapped_column(String(50))
    supplier_id: Mapped[Optional[str]] = mapped_column(String(50))
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    event_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
