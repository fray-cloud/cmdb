"""PostgreSQL-backed role repository implementation."""

from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.role.domain import Role, RoleRepository
from auth.shared.domain import Permission
from auth.shared.models import RoleModel


class PostgresRoleRepository(RoleRepository):
    """RoleRepository implementation using PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: UUID) -> Role | None:
        """Find a role by primary key."""
        result = await self._session.get(RoleModel, entity_id)
        return self._to_entity(result) if result else None

    async def find_by_name(self, name: str, tenant_id: UUID) -> Role | None:
        stmt = select(RoleModel).where(
            RoleModel.name == name,
            RoleModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def find_by_ids(self, role_ids: list[UUID]) -> list[Role]:
        if not role_ids:
            return []
        stmt = select(RoleModel).where(RoleModel.id.in_(role_ids))
        result = await self._session.execute(stmt)
        return [self._to_entity(r) for r in result.scalars().all()]

    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Role], int]:
        """Return a paginated list of roles and total count for a tenant."""
        count_stmt = select(sa_func.count()).select_from(RoleModel).where(RoleModel.tenant_id == tenant_id)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(RoleModel)
            .where(RoleModel.tenant_id == tenant_id)
            .order_by(RoleModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(r) for r in result.scalars().all()], total

    async def save(self, entity: Role) -> Role:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_entity(merged)

    async def delete(self, entity_id: UUID) -> None:
        model = await self._session.get(RoleModel, entity_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: RoleModel) -> Role:
        permissions = [Permission(**p) for p in (model.permissions or [])]
        return Role(
            id=model.id,
            name=model.name,
            tenant_id=model.tenant_id,
            description=model.description,
            permissions=permissions,
            is_system=model.is_system,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Role) -> RoleModel:
        return RoleModel(
            id=entity.id,
            name=entity.name,
            tenant_id=entity.tenant_id,
            description=entity.description,
            permissions=[p.model_dump() for p in entity.permissions],
            is_system=entity.is_system,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
