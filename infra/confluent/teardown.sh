#!/usr/bin/env bash
# Tear down billable Confluent resources after a demo session.
# Pausing connectors does NOT stop task-hour charges — DELETE them.
set -euo pipefail

echo "=== SurgiFlow Confluent tear-down ==="
echo "This script lists connector names to delete via Confluent CLI."
echo "Flink statements must be STOPPED in the Flink workspace UI/CLI."
echo ""

if ! command -v confluent >/dev/null 2>&1; then
  echo "confluent CLI not found. Delete manually in Cloud Console:"
  echo "  1. Connectors → delete surgiflow-postgres-cdc and surgiflow-postgres-sink"
  echo "  2. Flink → stop all running statements"
  echo "  3. Check Billing → confirm burn rate dropped"
  exit 0
fi

ENV_ID="${CONFLUENT_ENVIRONMENT_ID:-}"
if [[ -n "$ENV_ID" ]]; then
  confluent environment use "$ENV_ID" || true
fi

echo "Listing connectors..."
confluent connect cluster list || true

for name in surgiflow-postgres-cdc surgiflow-postgres-sink; do
  echo "Attempting delete: $name"
  confluent connect cluster delete --cluster "$name" -y 2>/dev/null \
    || confluent connect delete "$name" -y 2>/dev/null \
    || echo "  Delete $name manually in Console if CLI syntax differs"
done

echo ""
echo "Next: open Flink workspace and STOP every statement."
echo "Optional: delete topics if idle for days (keeps Basic eCKU at zero)."
echo "Check https://confluent.cloud → Billing daily."
