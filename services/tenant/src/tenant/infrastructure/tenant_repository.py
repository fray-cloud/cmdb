from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.domain.repository import TenantRepository
from tenant.domain.tenant import Tenant, TenantDbConfig, TenantSettings, TenantStatus
from tenant.infrastructure.models import TenantModel


class PostgresTenantRepository(TenantRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: UUID) -> Tenant | None:
        result = await self._session.get(TenantModel, entity_id)
        return self._to_entity(result) if result else None

    async def find_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(TenantModel).where(TenantModel.slug == slug)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Tenant], int]:
        count_stmt = select(sa_func.count()).select_from(TenantModel)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = select(TenantModel).order_by(TenantModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_entity(r) for r in rows], total

    async def save(self, entity: Tenant) -> Tenant:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_entity(merged)

    async def delete(self, entity_id: UUID) -> None:
        model = await self._session.get(TenantModel, entity_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: TenantModel) -> Tenant:
        db_config = None
        if model.db_config:
            db_config = TenantDbConfig(**model.db_config)
        return Tenant(
            id=model.id,
            name=model.name,
            slug=model.slug,
            status=TenantStatus(model.status),
            settings=TenantSettings(**(model.settings or {})),
            db_config=db_config,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Tenant) -> TenantModel:
        return TenantModel(
            id=entity.id,
            name=entity.name,
            slug=entity.slug,
            status=entity.status.value,
            settings=entity.settings.model_dump(),
            db_config=entity.db_config.model_dump() if entity.db_config else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
