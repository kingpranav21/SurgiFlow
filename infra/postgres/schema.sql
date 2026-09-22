-- SurgiFlow operational + derived tables (synthetic data only)

CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit_cost NUMERIC(12,2),
    safety_stock INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    reliability_score NUMERIC(5,2)
);

CREATE TABLE IF NOT EXISTS inventory (
    hospital_id VARCHAR(50) REFERENCES hospitals(hospital_id),
    product_id VARCHAR(50) REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (hospital_id, product_id)
);

CREATE TABLE IF NOT EXISTS procedures (
    procedure_id VARCHAR(50) PRIMARY KEY,
    hospital_id VARCHAR(50) REFERENCES hospitals(hospital_id),
    procedure_type VARCHAR(100),
    scheduled_time TIMESTAMP,
    status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    hospital_id VARCHAR(50) REFERENCES hospitals(hospital_id),
    product_id VARCHAR(50) REFERENCES products(product_id),
    quantity INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) REFERENCES suppliers(supplier_id),
    hospital_id VARCHAR(50) REFERENCES hospitals(hospital_id),
    product_id VARCHAR(50) REFERENCES products(product_id),
    quantity INTEGER,
    status VARCHAR(50),
    expected_delivery TIMESTAMP,
    delay_hours INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS procedure_requirements (
    procedure_type VARCHAR(100),
    product_id VARCHAR(50) REFERENCES products(product_id),
    quantity_per_procedure INTEGER,
    PRIMARY KEY (procedure_type, product_id)
);

CREATE TABLE IF NOT EXISTS risk_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    hospital_id VARCHAR(50),
    product_id VARCHAR(50),
    risk_level VARCHAR(20),
    current_inventory INTEGER,
    projected_demand INTEGER,
    projected_inventory INTEGER,
    predicted_stockout TIMESTAMP,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id BIGSERIAL PRIMARY KEY,
    source_hospital_id VARCHAR(50),
    target_hospital_id VARCHAR(50),
    product_id VARCHAR(50),
    quantity INTEGER,
    reason TEXT,
    status VARCHAR(30) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demand_forecasts (
    forecast_id BIGSERIAL PRIMARY KEY,
    hospital_id VARCHAR(50),
    product_id VARCHAR(50),
    window_hours INTEGER,
    forecasted_demand INTEGER,
    baseline_consumption NUMERIC(10,2),
    procedure_demand INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_log (
    event_id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    hospital_id VARCHAR(50),
    product_id VARCHAR(50),
    supplier_id VARCHAR(50),
    payload JSONB,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CDC requires logical replication for Confluent Postgres CDC V2
-- Run on cloud Postgres: ALTER SYSTEM SET wal_level = logical; (Neon enables via dashboard)

CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_procedures_hospital ON procedures(hospital_id);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);
CREATE INDEX IF NOT EXISTS idx_risk_created ON risk_predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_log_time ON event_log(event_time DESC);
