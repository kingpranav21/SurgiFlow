# SurgiFlow

Real-time surgical supply inventory risk and transfer recommendations.

Events flow Postgres → Kafka → Flink → dashboard. Synthetic hospital data only.

## Stack

- FastAPI + React
- PostgreSQL
- Confluent Cloud (Kafka, Flink, Connect, Schema Registry)

## Local run

Python 3.11+, Node 20+, Postgres.

```bash
docker compose up -d postgres   # or local Postgres

python3.11 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
python scripts/seed_database.py --apply-schema

cd backend && uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 — What-If delay on shipment `SHP182` (18h).

## Kafka (optional local)

```bash
docker compose -f docker-compose.kafka.yml up -d
# .env: PIPELINE_MODE=hybrid, KAFKA_BOOTSTRAP_SERVERS=localhost:19092, PLAINTEXT
python scripts/stream_processor.py
python scripts/stream_live.py
```

## Confluent

- Topics / connector JSON: `infra/confluent/`
- Flink SQL: `flink/sql/confluent_json_materialized.sql`
- Tear down: `infra/confluent/teardown.sh` (delete connectors; drop Flink MTs when idle)

## Layout

```
backend/   API
frontend/  UI
flink/sql/ Flink statements
schemas/   JSON schemas
scripts/   seed / stream helpers
infra/     Postgres + Confluent configs
```
