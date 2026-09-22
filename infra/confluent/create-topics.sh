#!/usr/bin/env bash
# Create SurgiFlow Kafka topics on Confluent Cloud (requires confluent CLI logged in).
# Usage: ./infra/confluent/create-topics.sh
set -euo pipefail

CLUSTER_ID="${CONFLUENT_CLUSTER_ID:?set CONFLUENT_CLUSTER_ID}"
ENV_ID="${CONFLUENT_ENVIRONMENT_ID:?set CONFLUENT_ENVIRONMENT_ID}"

topics=(
  surgiflow.inventory.events
  surgiflow.procedure.events
  surgiflow.order.events
  surgiflow.shipment.events
  surgiflow.procedure.requirements
  surgiflow.demand.forecast
  surgiflow.stockout.risk
  surgiflow.recommendations
)

echo "Using environment $ENV_ID cluster $CLUSTER_ID"
confluent environment use "$ENV_ID"
confluent kafka cluster use "$CLUSTER_ID"

for t in "${topics[@]}"; do
  echo "Creating topic $t ..."
  confluent kafka topic create "$t" \
    --partitions 1 \
    --config retention.ms=86400000 \
    || echo "  (exists or skipped) $t"
done

echo "Done. Verify in Cloud Console → Topics."
