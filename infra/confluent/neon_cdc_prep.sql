-- Run on Neon (public Postgres) before creating Confluent CDC / Sink connectors.
-- Prefer the DIRECT host (no "-pooler" in hostname) for DDL + CDC.

SET search_path TO public;

-- Logical replication (Neon: enable in Project Settings → Logical Replication if prompted)
DROP PUBLICATION IF EXISTS surgiflow_pub;
CREATE PUBLICATION surgiflow_pub FOR TABLE
  public.inventory,
  public.procedures,
  public.orders,
  public.shipments;

-- Sink destination tables (usually already created by neon_bootstrap.sql)
CREATE TABLE IF NOT EXISTS public.risk_predictions (
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

CREATE TABLE IF NOT EXISTS public.recommendations (
  recommendation_id BIGSERIAL PRIMARY KEY,
  source_hospital_id VARCHAR(50),
  target_hospital_id VARCHAR(50),
  product_id VARCHAR(50),
  quantity INTEGER,
  reason TEXT,
  status VARCHAR(30) DEFAULT 'PENDING',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
