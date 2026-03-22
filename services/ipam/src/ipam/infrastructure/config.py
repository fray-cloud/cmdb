from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cmdb:cmdb@postgres:5432/cmdb_ipam"
    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "cmdb"
    db_password: str = "cmdb"
    kafka_bootstrap_servers: str = "kafka:9092"
    redis_url: str = "redis://redis:6379"

    def tenant_db_url(self, tenant_slug: str) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/cmdb_tenant_{tenant_slug}"

    model_config = {"env_prefix": "IPAM_"}
