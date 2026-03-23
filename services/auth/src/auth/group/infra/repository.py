"""PostgreSQL-backed group repository implementation."""

from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.group.domain import Group, GroupRepository
from auth.shared.models import GroupModel, GroupRoleModel


class PostgresGroupRepository(GroupRepository):
    """GroupRepository implementation using PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: UUID) -> Group | None:
        """Find a group by primary key."""
        result = await self._session.get(GroupModel, entity_id)
        return self._to_entity(result) if result else None

    async def find_by_name(self, name: str, tenant_id: UUID) -> Group | None:
        stmt = select(GroupModel).where(
            GroupModel.name == name,
            GroupModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def find_by_ids(self, group_ids: list[UUID]) -> list[Group]:
        if not group_ids:
            return []
        stmt = select(GroupModel).where(GroupModel.id.in_(group_ids))
        result = await self._session.execute(stmt)
        return [self._to_entity(r) for r in result.scalars().unique().all()]

    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Group], int]:
        """Return a paginated list of groups and total count for a tenant."""
        count_stmt = select(sa_func.count()).select_from(GroupModel).where(GroupModel.tenant_id == tenant_id)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(GroupModel)
            .where(GroupModel.tenant_id == tenant_id)
            .order_by(GroupModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(r) for r in result.scalars().unique().all()], total

    async def save(self, entity: Group) -> Group:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()

        # Sync role associations
        await self._session.execute(GroupRoleModel.__table__.delete().where(GroupRoleModel.group_id == entity.id))
        for role_id in entity.role_ids:
            await self._session.execute(GroupRoleModel.__table__.insert().values(group_id=entity.id, role_id=role_id))

        await self._session.commit()
        return self._to_entity(merged)

    async def delete(self, entity_id: UUID) -> None:
        model = await self._session.get(GroupModel, entity_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: GroupModel) -> Group:
        return Group(
            id=model.id,
            name=model.name,
            tenant_id=model.tenant_id,
            role_ids=[r.id for r in model.roles],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Group) -> GroupModel:
        return GroupModel(
            id=entity.id,
            name=entity.name,
            tenant_id=entity.tenant_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
