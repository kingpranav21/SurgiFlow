# Flink SQL

Use `sql/confluent_json_materialized.sql` in Confluent SQL Workspace (one statement at a time).

Older drafts: `workshop_materialized.sql`, `00_sources.sql`, etc.

Local stand-in without Flink:

```bash
docker compose -f docker-compose.kafka.yml up -d
PIPELINE_MODE=hybrid KAFKA_BOOTSTRAP_SERVERS=localhost:19092 \
  python scripts/stream_processor.py
```

Drop materialized tables when not demoing to avoid CFU charges.
