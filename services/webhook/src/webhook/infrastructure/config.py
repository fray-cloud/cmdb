from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cmdb:cmdb@postgres:5432/cmdb_webhook"
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_group_id: str = "webhook-service"
    kafka_dlq_topic: str = "webhook.dlq"
    redis_url: str = "redis://redis:6379"
    webhook_max_retries: int = 5
    webhook_retry_backoffs: list[int] = [10, 30, 120, 600, 3600]
    webhook_delivery_timeout: float = 10.0

    model_config = {"env_prefix": "WEBHOOK_"}
