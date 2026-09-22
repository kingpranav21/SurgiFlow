-- Demand forecast: baseline consumption (3/day over 48h = 6) + procedure demand

CREATE TABLE IF NOT EXISTS demand_forecast (
  hospital_id STRING,
  product_id STRING,
  window_hours INT,
  forecasted_demand INT,
  baseline_consumption DOUBLE,
  procedure_demand INT,
  PRIMARY KEY (hospital_id, product_id) NOT ENFORCED
) WITH (
  'connector' = 'confluent',
  'topic' = 'surgiflow.demand.forecast',
  'value.format' = 'json-registry'
);

INSERT INTO demand_forecast
SELECT
  i.hospital_id,
  i.product_id,
  48 AS window_hours,
  CAST(6 + COALESCE(p.proc_demand, 0) AS INT) AS forecasted_demand,
  CAST(6 AS DOUBLE) AS baseline_consumption,
  CAST(COALESCE(p.proc_demand, 0) AS INT) AS procedure_demand
FROM inventory_events AS i
LEFT JOIN (
  SELECT
    pe.hospital_id,
    pr.product_id,
    SUM(pr.quantity_per_procedure) AS proc_demand
  FROM procedure_events AS pe
  JOIN procedure_requirements AS pr
    ON pe.procedure_type = pr.procedure_type
  WHERE pe.status IN ('SCHEDULED', 'CONFIRMED')
  GROUP BY pe.hospital_id, pr.product_id
) AS p
  ON i.hospital_id = p.hospital_id AND i.product_id = p.product_id;
