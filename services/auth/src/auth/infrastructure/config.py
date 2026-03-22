from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cmdb:cmdb@postgres:5432/cmdb_auth"

    kafka_bootstrap_servers: str = "kafka:9092"
    redis_url: str = "redis://redis:6379"

    rsa_private_key: str = ""
    rsa_public_key: str = ""
    rsa_private_key_path: str = ""
    rsa_public_key_path: str = ""
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    bcrypt_rounds: int = 12

    def model_post_init(self, __context: object) -> None:
        if not self.rsa_private_key and self.rsa_private_key_path:
            self.rsa_private_key = Path(self.rsa_private_key_path).read_text()
        if not self.rsa_public_key and self.rsa_public_key_path:
            self.rsa_public_key = Path(self.rsa_public_key_path).read_text()
