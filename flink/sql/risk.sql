-- Stockout risk: projected_inventory = stock + on-time incoming - demand
-- DELAYED shipments excluded from usable supply (matches local risk engine)

CREATE TABLE IF NOT EXISTS stockout_risk (
  hospital_id STRING,
  product_id STRING,
  risk_level STRING,
  current_inventory INT,
  projected_demand INT,
  projected_inventory INT,
  predicted_stockout TIMESTAMP(3),
  reason STRING,
  PRIMARY KEY (hospital_id, product_id) NOT ENFORCED
) WITH (
  'connector' = 'confluent',
  'topic' = 'surgiflow.stockout.risk',
  'value.format' = 'json-registry'
);

INSERT INTO stockout_risk
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
JOIN inventory_events AS i
  ON d.hospital_id = i.hospital_id AND d.product_id = i.product_id
LEFT JOIN (
  SELECT
    hospital_id,
    product_id,
    SUM(CASE WHEN status <> 'DELAYED' THEN quantity ELSE 0 END) AS usable_incoming,
    MAX(CASE WHEN status = 'DELAYED' THEN 1 ELSE 0 END) AS delayed_flag
  FROM shipment_events
  GROUP BY hospital_id, product_id
) AS s
  ON d.hospital_id = s.hospital_id AND d.product_id = s.product_id;
