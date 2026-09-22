"""Kafka producer/consumer for SurgiFlow.

Works with:
  - Local Redpanda (PLAINTEXT) via docker-compose.kafka.yml
  - Confluent Cloud (SASL_SSL + API key/secret)

When kafka is disabled / misconfigured, publish calls are no-ops.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional

from app.config import Settings, get_settings

logger = logging.getLogger("surgiflow.kafka")

_producer = None


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Not serializable: {type(obj)}")


def kafka_config(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    conf: dict[str, Any] = {
        "bootstrap.servers": settings.effective_bootstrap,
        "client.id": settings.kafka_client_id,
    }
    protocol = settings.effective_security_protocol.upper()
    conf["security.protocol"] = protocol
    if protocol.startswith("SASL"):
        conf["sasl.mechanisms"] = settings.kafka_sasl_mechanism
        conf["sasl.username"] = settings.effective_api_key
        conf["sasl.password"] = settings.effective_api_secret
    return conf


def get_producer():
    global _producer
    settings = get_settings()
    if not settings.kafka_enabled:
        return None
    if _producer is not None:
        return _producer
    try:
        from confluent_kafka import Producer

        _producer = Producer(kafka_config(settings))
        logger.info("Kafka producer ready → %s", settings.effective_bootstrap)
        return _producer
    except Exception as exc:  # noqa: BLE001
        logger.warning("Kafka producer unavailable: %s", exc)
        return None


def publish(topic: str, value: dict[str, Any], key: str | None = None) -> bool:
    """Publish one JSON event. Returns False if Kafka is off or publish failed."""
    producer = get_producer()
    if producer is None:
        return False
    try:
        payload = json.dumps(value, default=_json_default).encode("utf-8")
        k = key.encode("utf-8") if key else None
        producer.produce(topic, value=payload, key=k)
        producer.poll(0)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Kafka publish failed (%s): %s", topic, exc)
        return False


def flush(timeout: float = 5.0) -> None:
    producer = get_producer()
    if producer is not None:
        producer.flush(timeout)


def publish_inventory(hospital_id: str, product_id: str, quantity: int, event_type: str = "INVENTORY_UPDATED") -> bool:
    s = get_settings()
    return publish(
        s.topic_inventory,
        {
            "hospital_id": hospital_id,
            "product_id": product_id,
            "quantity": quantity,
            "event_type": event_type,
            "event_time": datetime.utcnow().isoformat() + "Z",
        },
        key=f"{hospital_id}:{product_id}",
    )


def publish_procedure(
    procedure_id: str,
    hospital_id: str,
    procedure_type: str,
    scheduled_time: datetime | str,
    status: str = "SCHEDULED",
) -> bool:
    s = get_settings()
    return publish(
        s.topic_procedure,
        {
            "procedure_id": procedure_id,
            "hospital_id": hospital_id,
            "procedure_type": procedure_type,
            "scheduled_time": scheduled_time.isoformat() if isinstance(scheduled_time, datetime) else scheduled_time,
            "status": status,
            "event_time": datetime.utcnow().isoformat() + "Z",
        },
        key=procedure_id,
    )


def publish_shipment(shipment: dict[str, Any]) -> bool:
    s = get_settings()
    sid = str(shipment.get("shipment_id", ""))
    return publish(s.topic_shipment, shipment, key=sid)


def publish_requirement(procedure_type: str, product_id: str, quantity_per_procedure: int) -> bool:
    s = get_settings()
    return publish(
        s.topic_requirements,
        {
            "procedure_type": procedure_type,
            "product_id": product_id,
            "quantity_per_procedure": quantity_per_procedure,
        },
        key=f"{procedure_type}:{product_id}",
    )


def make_consumer(topics: list[str], group_id: str | None = None):
    settings = get_settings()
    if not settings.effective_bootstrap:
        return None
    from confluent_kafka import Consumer

    conf = kafka_config(settings)
    conf.update(
        {
            "group.id": group_id or settings.kafka_consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
    )
    consumer = Consumer(conf)
    consumer.subscribe(topics)
    return consumer


def consume_loop(
    topics: list[str],
    handler: Callable[[str, dict[str, Any]], None],
    group_id: str | None = None,
    stop_flag: Optional[Callable[[], bool]] = None,
) -> None:
    """Blocking consume loop. stop_flag() -> True to exit."""
    consumer = make_consumer(topics, group_id=group_id)
    if consumer is None:
        raise RuntimeError("Kafka not configured")
    try:
        while True:
            if stop_flag and stop_flag():
                break
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.warning("Kafka consumer error: %s", msg.error())
                continue
            try:
                data = json.loads(msg.value().decode("utf-8"))
                handler(msg.topic(), data)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Bad message on %s: %s", msg.topic(), exc)
    finally:
        consumer.close()
