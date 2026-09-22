-- Transfer recommendations when risk is HIGH: move surplus from donor hospitals

CREATE TABLE IF NOT EXISTS recommendations_out (
  source_hospital_id STRING,
  target_hospital_id STRING,
  product_id STRING,
  quantity INT,
  reason STRING,
  status STRING,
  PRIMARY KEY (source_hospital_id, target_hospital_id, product_id) NOT ENFORCED
) WITH (
  'connector' = 'confluent',
  'topic' = 'surgiflow.recommendations',
  'value.format' = 'json-registry'
);

-- Simplified: recommend from H004 → H001 for STAPLER-01 when H001 is HIGH
-- Surplus → deficit transfer recommendation.

INSERT INTO recommendations_out
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
