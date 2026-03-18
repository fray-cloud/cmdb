import asyncio
from pathlib import Path

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tenant.domain.tenant import TenantDbConfig
from tenant.infrastructure.config import Settings


class TenantDbProvisioner:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def provision(self, slug: str) -> TenantDbConfig:
        db_name = f"cmdb_tenant_{slug}"
        db_config = TenantDbConfig(
            db_host=self._settings.postgres_host,
            db_port=self._settings.postgres_port,
            db_name=db_name,
            db_user=self._settings.postgres_user,
            db_password=self._settings.postgres_password,
        )

        await self._create_database(db_name)
        await self._run_migrations(db_config)

        return db_config

    async def _create_database(self, db_name: str) -> None:
        s = self._settings
        admin_url = (
            f"postgresql+asyncpg://{s.postgres_user}:{s.postgres_password}@{s.postgres_host}:{s.postgres_port}/postgres"
        )
        engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :name"),
                    {"name": db_name},
                )
                if result.scalar() is None:
                    await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        finally:
            await engine.dispose()

    async def _run_migrations(self, db_config: TenantDbConfig) -> None:
        def _run() -> None:
            alembic_cfg = AlembicConfig()
            script_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "alembic_tenant_db")
            alembic_cfg.set_main_option("script_location", script_dir)
            alembic_cfg.set_main_option("sqlalchemy.url", db_config.sync_url)
            alembic_command.upgrade(alembic_cfg, "head")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _run)
