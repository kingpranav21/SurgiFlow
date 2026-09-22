-- SurgiFlow Flink SQL — demand / risk / recommendations
-- Run in Confluent Cloud Flink workspace (MAX_CFU=5).
-- STOP statements when not demoing ($0.21/CFU-hour).

-- Adjust catalog/database names to your Confluent environment.
-- Example: USE CATALOG `your-env`; USE `your-cluster`;

-- ---------------------------------------------------------------------------
-- Source tables (map to CDC topics — field names may need SMT/unwrap adjust)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS inventory_events (
  hospital_id STRING,
  product_id STRING,
  quantity INT,
  updated_at TIMESTAMP(3),
  PRIMARY KEY (hospital_id, product_id) NOT ENFORCED
) WITH (
  'connector' = 'confluent',
  'topic' = 'surgiflow.inventory.events',
  'value.format' = 'json-registry',
  'scan.startup.mode' = 'earliest-offset'
);

CREATE TABLE IF NOT EXISTS procedure_events (
  procedure_id STRING,
  hospital_id STRING,
  procedure_type STRING,
  scheduled_time TIMESTAMP(3),
  status STRING,
  PRIMARY KEY (procedure_id) NOT ENFORCED
) WITH (
  'connector' = 'confluent',
  'topic' = 'surgiflow.procedure.events',
  'value.format' = 'json-registry',
  'scan.startup.mode' = 'earliest-offset'
);

CREATE TABLE IF NOT EXISTS shipment_events (
  shipment_id STRING,
  supplier_id STRING,
  hospital_id STRING,
  product_id STRING,
  quantity INT,
  status STRING,
  delay_hours INT,
  expected_delivery TIMESTAMP(3),
  PRIMARY KEY (shipment_id) NOT ENFORCED
) WITH (
  'connector' = 'confluent',
  'topic' = 'surgiflow.shipment.events',
  'value.format' = 'json-registry',
  'scan.startup.mode' = 'earliest-offset'
);

-- Static procedure→product map (seed once or use a changelog topic)
CREATE TABLE IF NOT EXISTS procedure_requirements (
  procedure_type STRING,
  product_id STRING,
  quantity_per_procedure INT,
  PRIMARY KEY (procedure_type, product_id) NOT ENFORCED
) WITH (
  'connector' = 'confluent',
  'topic' = 'surgiflow.procedure.requirements',
  'value.format' = 'json-registry'
);
