# Architecture

```
Postgres  --CDC-->  Kafka topics
App / What-If     -->  Kafka (inventory, shipment, …)
Kafka  --Flink MTs-->  stockout_risk, recommendations
Kafka  --Sink-->  Postgres (risk_predictions, recommendations)
FastAPI + React dashboard
```

`PIPELINE_MODE=local|hybrid|kafka` controls whether the API publishes to Kafka and/or computes risk locally.
