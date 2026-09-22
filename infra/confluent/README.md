# Confluent configs

Topics: see `topics.txt` / `create-topics.sh`

Connectors (1 task each):

- `cdc-postgres-source.json` — Postgres CDC Source V2
- `postgres-sink-risk.json` — `stockout_risk` → `risk_predictions`
- `postgres-sink-recommendations.json` — `recommendations` → `recommendations`

Neon prep: `neon_bootstrap.sql`, `neon_cdc_prep.sql` (use Neon **direct** host, not `-pooler`).

Tear down: `./teardown.sh` or delete connectors in the UI (pause still bills).
