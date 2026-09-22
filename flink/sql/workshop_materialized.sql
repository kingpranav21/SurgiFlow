-- SurgiFlow Flink SQL (MATERIALIZED TABLE style)
--
-- Run in Flink SQL Workspace after USE CATALOG / USE your cluster.
-- Drop materialized tables when idle.
--
-- Topics must already exist (see infra/confluent/create-topics.sh).
-- Events are produced by SurgiFlow API / scripts/stream_live.py
-- (or Postgres CDC if you configure the connector).

-- ---------------------------------------------------------------------------
-- 1) Latest inventory per hospital×product
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED TABLE inventory_keyed (
  hospital_id STRING NOT NULL,
  product_id STRING NOT NULL,
  quantity INT,
  PRIMARY KEY (hospital_id, product_id) NOT ENFORCED
) AS
SELECT
  COALESCE(hospital_id, '') AS hospital_id,
  COALESCE(product_id, '') AS product_id,
  quantity
FROM `surgiflow.inventory.events`;

-- ---------------------------------------------------------------------------
-- 2) Procedure requirements lookup
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED TABLE requirements_keyed (
  procedure_type STRING NOT NULL,
  product_id STRING NOT NULL,
  quantity_per_procedure INT,
  PRIMARY KEY (procedure_type, product_id) NOT ENFORCED
) AS
SELECT
  COALESCE(procedure_type, '') AS procedure_type,
  COALESCE(product_id, '') AS product_id,
  quantity_per_procedure
FROM `surgiflow.procedure.requirements`;

-- ---------------------------------------------------------------------------
-- 3) Latest shipment status (DELAYED shipments excluded later)
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED TABLE shipments_keyed (
  shipment_id STRING NOT NULL,
  hospital_id STRING,
  product_id STRING,
  quantity INT,
  status STRING,
  delay_hours INT,
  PRIMARY KEY (shipment_id) NOT ENFORCED
) AS
SELECT
  COALESCE(shipment_id, '') AS shipment_id,
  hospital_id,
  product_id,
  quantity,
  status,
  delay_hours
FROM `surgiflow.shipment.events`;

-- ---------------------------------------------------------------------------
-- 4) Demand forecast = baseline (6 / 48h) + procedure-driven demand
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED TABLE demand_forecast AS
SELECT
  i.hospital_id,
  i.product_id,
  48 AS window_hours,
  CAST(6 + COALESCE(p.proc_demand, 0) AS INT) AS forecasted_demand,
  CAST(6 AS DOUBLE) AS baseline_consumption,
  CAST(COALESCE(p.proc_demand, 0) AS INT) AS procedure_demand
FROM inventory_keyed AS i
LEFT JOIN (
  SELECT
    pe.hospital_id,
    r.product_id,
    SUM(r.quantity_per_procedure) AS proc_demand
  FROM `surgiflow.procedure.events` AS pe
  JOIN requirements_keyed AS r
    ON pe.procedure_type = r.procedure_type
  WHERE pe.status IN ('SCHEDULED', 'CONFIRMED')
  GROUP BY pe.hospital_id, r.product_id
) AS p
  ON i.hospital_id = p.hospital_id AND i.product_id = p.product_id;

-- ---------------------------------------------------------------------------
-- 5) Stockout risk (DELAYED inbound does not count as supply)
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED TABLE stockout_risk AS
SELECT
  d.hospital_id,
  d.product_id,
  CASE
    WHEN (i.quantity + COALESCE(s.usable_incoming, 0) - d.forecasted_demand) < 0 THEN 'HIGH'
    WHEN (i.quantity + COALESCE(s.usable_incoming, 0) - d.forecasted_demand) < 8 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_level,
  i.quantity AS current_inventory,
  d.forecasted_demand AS projected_demand,
  (i.quantity + COALESCE(s.usable_incoming, 0) - d.forecasted_demand) AS projected_inventory,
  CAST(NULL AS TIMESTAMP(3)) AS predicted_stockout,
  CONCAT(
    'Procedure demand ', CAST(d.procedure_demand AS STRING),
    CASE WHEN COALESCE(s.delayed_flag, 0) = 1
      THEN '. Incoming shipment delayed'
      ELSE ''
    END
  ) AS reason
FROM demand_forecast AS d
JOIN inventory_keyed AS i
  ON d.hospital_id = i.hospital_id AND d.product_id = i.product_id
LEFT JOIN (
  SELECT
    hospital_id,
    product_id,
    SUM(CASE WHEN UPPER(status) <> 'DELAYED' THEN quantity ELSE 0 END) AS usable_incoming,
    MAX(CASE WHEN UPPER(status) = 'DELAYED' THEN 1 ELSE 0 END) AS delayed_flag
  FROM shipments_keyed
  GROUP BY hospital_id, product_id
) AS s
  ON d.hospital_id = s.hospital_id AND d.product_id = s.product_id;

-- ---------------------------------------------------------------------------
-- 6) Transfer recommendation for the demo story (H004 → H001 staplers)
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED TABLE recommendations AS
SELECT
  'H004' AS source_hospital_id,
  r.hospital_id AS target_hospital_id,
  r.product_id,
  8 AS quantity,
  'H001 predicted shortage; H004 has surplus' AS reason,
  'PENDING' AS status
FROM stockout_risk AS r
WHERE r.hospital_id = 'H001'
  AND r.product_id = 'STAPLER-01'
  AND r.risk_level = 'HIGH';

-- Inspect:
-- SELECT * FROM stockout_risk WHERE risk_level = 'HIGH';

-- Cleanup (stop CFU burn):
-- DROP MATERIALIZED TABLE recommendations;
-- DROP MATERIALIZED TABLE stockout_risk;
-- DROP MATERIALIZED TABLE demand_forecast;
-- DROP MATERIALIZED TABLE shipments_keyed;
-- DROP MATERIALIZED TABLE requirements_keyed;
-- DROP MATERIALIZED TABLE inventory_keyed;
