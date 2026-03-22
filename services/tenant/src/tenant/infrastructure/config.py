from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cmdb:cmdb@postgres:5432/cmdb_tenant"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "cmdb"
    postgres_password: str = "cmdb"

    kafka_bootstrap_servers: str = "kafka:9092"
    redis_url: str = "redis://redis:6379"
