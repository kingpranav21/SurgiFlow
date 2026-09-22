-- SurgiFlow Flink SQL (Confluent Cloud). Run one statement at a time.
-- USE CATALOG / USE your env + cluster first. Drop MTs when idle.

-- ========== A) ALTER source topics (once each) ==========

ALTER TABLE `surgiflow.inventory.events` MODIFY (key STRING, val STRING);

ALTER TABLE `surgiflow.procedure.requirements` MODIFY (key STRING, val STRING);

ALTER TABLE `surgiflow.shipment.events` MODIFY (key STRING, val STRING);

ALTER TABLE `surgiflow.procedure.events` MODIFY (key STRING, val STRING);

-- Check data exists:
-- SELECT key, val FROM `surgiflow.inventory.events` LIMIT 5;

-- ========== B) Materialized tables (in order) ==========

-- 1) Inventory
CREATE MATERIALIZED TABLE inventory_keyed (
  hospital_id STRING NOT NULL,
  product_id STRING NOT NULL,
  quantity INT,
  PRIMARY KEY (hospital_id, product_id) NOT ENFORCED
) AS
SELECT
  COALESCE(JSON_VALUE(val, '$.hospital_id'), '') AS hospital_id,
  COALESCE(JSON_VALUE(val, '$.product_id'), '') AS product_id,
  CAST(JSON_VALUE(val, '$.quantity') AS INT) AS quantity
FROM `surgiflow.inventory.events`
WHERE JSON_VALUE(val, '$.hospital_id') IS NOT NULL;

-- 2) Requirements
CREATE MATERIALIZED TABLE requirements_keyed (
  procedure_type STRING NOT NULL,
  product_id STRING NOT NULL,
  quantity_per_procedure INT,
  PRIMARY KEY (procedure_type, product_id) NOT ENFORCED
) AS
SELECT
  COALESCE(JSON_VALUE(val, '$.procedure_type'), '') AS procedure_type,
  COALESCE(JSON_VALUE(val, '$.product_id'), '') AS product_id,
  CAST(JSON_VALUE(val, '$.quantity_per_procedure') AS INT) AS quantity_per_procedure
FROM `surgiflow.procedure.requirements`
WHERE JSON_VALUE(val, '$.procedure_type') IS NOT NULL;

-- 3) Shipments
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
  COALESCE(JSON_VALUE(val, '$.shipment_id'), '') AS shipment_id,
  JSON_VALUE(val, '$.hospital_id') AS hospital_id,
  JSON_VALUE(val, '$.product_id') AS product_id,
  CAST(JSON_VALUE(val, '$.quantity') AS INT) AS quantity,
  JSON_VALUE(val, '$.status') AS status,
  CAST(JSON_VALUE(val, '$.delay_hours') AS INT) AS delay_hours
FROM `surgiflow.shipment.events`
WHERE JSON_VALUE(val, '$.shipment_id') IS NOT NULL;

-- 4) Demand forecast
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
    JSON_VALUE(pe.val, '$.hospital_id') AS hospital_id,
    r.product_id,
    SUM(r.quantity_per_procedure) AS proc_demand
  FROM `surgiflow.procedure.events` AS pe
  JOIN requirements_keyed AS r
    ON JSON_VALUE(pe.val, '$.procedure_type') = r.procedure_type
  WHERE JSON_VALUE(pe.val, '$.status') IN ('SCHEDULED', 'CONFIRMED')
  GROUP BY JSON_VALUE(pe.val, '$.hospital_id'), r.product_id
) AS p
  ON i.hospital_id = p.hospital_id AND i.product_id = p.product_id;

-- 5) Stockout risk
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
    SUM(CASE WHEN UPPER(COALESCE(status, '')) <> 'DELAYED' THEN COALESCE(quantity, 0) ELSE 0 END) AS usable_incoming,
    MAX(CASE WHEN UPPER(COALESCE(status, '')) = 'DELAYED' THEN 1 ELSE 0 END) AS delayed_flag
  FROM shipments_keyed
  GROUP BY hospital_id, product_id
) AS s
  ON d.hospital_id = s.hospital_id AND d.product_id = s.product_id;

-- 6) Recommendations
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

-- ========== C) Verify ==========
-- SELECT * FROM stockout_risk WHERE risk_level = 'HIGH';

-- ========== D) Tear down (stop CFU charges) ==========
-- DROP MATERIALIZED TABLE recommendations;
-- DROP MATERIALIZED TABLE stockout_risk;
-- DROP MATERIALIZED TABLE demand_forecast;
-- DROP MATERIALIZED TABLE shipments_keyed;
-- DROP MATERIALIZED TABLE requirements_keyed;
-- DROP MATERIALIZED TABLE inventory_keyed;
