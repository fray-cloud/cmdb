from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cmdb:cmdb@postgres:5432/cmdb_event"
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_group_id: str = "event-service"
    kafka_dlq_topic: str = "events.dlq"
