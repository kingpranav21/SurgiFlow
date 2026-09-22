from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://surgiflow:surgiflow@localhost:5432/surgiflow"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # local = Python risk engine only
    # kafka = produce+consume via Kafka; local stream_processor OR Confluent Flink does compute
    # hybrid = Kafka publish AND local engine (safe demo while Flink warms up)
    pipeline_mode: str = "local"

    # Kafka / Confluent Cloud
    kafka_bootstrap_servers: str = ""
    kafka_api_key: str = ""
    kafka_api_secret: str = ""
    kafka_security_protocol: str = "PLAINTEXT"  # PLAINTEXT | SASL_SSL
    kafka_sasl_mechanism: str = "PLAIN"
    kafka_client_id: str = "surgiflow-api"
    kafka_consumer_group: str = "surgiflow-dashboard"

    # Aliases from older .env.example
    confluent_bootstrap_servers: str = ""
    confluent_api_key: str = ""
    confluent_api_secret: str = ""

    topic_inventory: str = "surgiflow.inventory.events"
    topic_procedure: str = "surgiflow.procedure.events"
    topic_order: str = "surgiflow.order.events"
    topic_shipment: str = "surgiflow.shipment.events"
    topic_requirements: str = "surgiflow.procedure.requirements"
    topic_forecast: str = "surgiflow.demand.forecast"
    topic_risk: str = "surgiflow.stockout.risk"
    topic_recommendations: str = "surgiflow.recommendations"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def effective_bootstrap(self) -> str:
        return (self.kafka_bootstrap_servers or self.confluent_bootstrap_servers or "").strip()

    @property
    def effective_api_key(self) -> str:
        return self.kafka_api_key or self.confluent_api_key

    @property
    def effective_api_secret(self) -> str:
        return self.kafka_api_secret or self.confluent_api_secret

    @property
    def effective_security_protocol(self) -> str:
        if self.effective_bootstrap and "confluent.cloud" in self.effective_bootstrap:
            return "SASL_SSL"
        return self.kafka_security_protocol

    @property
    def kafka_enabled(self) -> bool:
        return bool(self.effective_bootstrap) and self.pipeline_mode in (
            "kafka",
            "hybrid",
            "confluent",
        )

    @property
    def use_local_risk_engine(self) -> bool:
        return self.pipeline_mode in ("local", "hybrid")

    # Back-compat alias used by older routes
    @property
    def risk_engine_mode(self) -> str:
        return "local" if self.use_local_risk_engine else "streaming"


@lru_cache
def get_settings() -> Settings:
    return Settings()
