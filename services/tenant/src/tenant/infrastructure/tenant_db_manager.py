from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tenant.domain.tenant import TenantDbConfig


class TenantDbManager:
    def __init__(self) -> None:
        self._engines: dict[str, AsyncEngine] = {}
        self._session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}

    def register(self, tenant_id: str, db_config: TenantDbConfig) -> None:
        if tenant_id not in self._engines:
            engine = create_async_engine(
                db_config.url,
                echo=False,
                pool_size=5,
                max_overflow=10,
            )
            self._engines[tenant_id] = engine
            self._session_factories[tenant_id] = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    def get_session(self, tenant_id: str) -> AsyncSession:
        factory = self._session_factories.get(tenant_id)
        if factory is None:
            raise KeyError(f"No database registered for tenant {tenant_id}")
        return factory()

    async def close_all(self) -> None:
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._session_factories.clear()
