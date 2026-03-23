"""PostgreSQL-backed API token repository implementation."""

from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.api_token.domain import APIToken, APITokenRepository
from auth.shared.models import APITokenModel


class PostgresAPITokenRepository(APITokenRepository):
    """APITokenRepository implementation using PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: UUID) -> APIToken | None:
        """Find an API token by primary key."""
        result = await self._session.get(APITokenModel, entity_id)
        return self._to_entity(result) if result else None

    async def find_by_key_hash(self, key_hash: str) -> APIToken | None:
        stmt = select(APITokenModel).where(APITokenModel.key_hash == key_hash)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def find_all_by_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[APIToken], int]:
        """Return a paginated list of tokens and total count for a user."""
        count_stmt = select(sa_func.count()).select_from(APITokenModel).where(APITokenModel.user_id == user_id)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(APITokenModel)
            .where(APITokenModel.user_id == user_id)
            .order_by(APITokenModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(r) for r in result.scalars().all()], total

    async def save(self, entity: APIToken) -> APIToken:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_entity(merged)

    async def delete(self, entity_id: UUID) -> None:
        model = await self._session.get(APITokenModel, entity_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: APITokenModel) -> APIToken:
        return APIToken(
            id=model.id,
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            key_hash=model.key_hash,
            description=model.description,
            scopes=model.scopes or [],
            expires_at=model.expires_at,
            allowed_ips=model.allowed_ips or [],
            last_used_at=model.last_used_at,
            is_revoked=model.is_revoked,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(entity: APIToken) -> APITokenModel:
        return APITokenModel(
            id=entity.id,
            user_id=entity.user_id,
            tenant_id=entity.tenant_id,
            key_hash=entity.key_hash,
            description=entity.description,
            scopes=entity.scopes,
            expires_at=entity.expires_at,
            allowed_ips=entity.allowed_ips,
            last_used_at=entity.last_used_at,
            is_revoked=entity.is_revoked,
            created_at=entity.created_at,
        )
