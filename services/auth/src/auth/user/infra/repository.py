from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.shared.models import UserGroupModel, UserModel, UserRoleModel
from auth.user.domain.repository import UserRepository
from auth.user.domain.user import User, UserStatus


class PostgresUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: UUID) -> User | None:
        result = await self._session.get(UserModel, entity_id)
        return self._to_entity(result) if result else None

    async def find_by_email(self, email: str, tenant_id: UUID) -> User | None:
        stmt = select(UserModel).where(
            UserModel.email == email,
            UserModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[User], int]:
        count_stmt = select(sa_func.count()).select_from(UserModel).where(UserModel.tenant_id == tenant_id)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(UserModel)
            .where(UserModel.tenant_id == tenant_id)
            .order_by(UserModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().unique().all()
        return [self._to_entity(r) for r in rows], total

    async def save(self, entity: User) -> User:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()

        # Sync role associations
        await self._session.execute(UserRoleModel.__table__.delete().where(UserRoleModel.user_id == entity.id))
        for role_id in entity.role_ids:
            await self._session.execute(UserRoleModel.__table__.insert().values(user_id=entity.id, role_id=role_id))

        # Sync group associations
        await self._session.execute(UserGroupModel.__table__.delete().where(UserGroupModel.user_id == entity.id))
        for group_id in entity.group_ids:
            await self._session.execute(UserGroupModel.__table__.insert().values(user_id=entity.id, group_id=group_id))

        await self._session.commit()
        return self._to_entity(merged)

    async def delete(self, entity_id: UUID) -> None:
        model = await self._session.get(UserModel, entity_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            tenant_id=model.tenant_id,
            status=UserStatus(model.status),
            display_name=model.display_name,
            role_ids=[r.id for r in model.roles],
            group_ids=[g.id for g in model.groups],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email,
            password_hash=entity.password_hash,
            tenant_id=entity.tenant_id,
            status=entity.status.value,
            display_name=entity.display_name,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
