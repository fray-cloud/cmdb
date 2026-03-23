"""Saved filter PostgreSQL repository implementation."""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.shared.saved_filter.infra.models import SavedFilterModel
from ipam.shared.saved_filter.query.read_model import SavedFilterRepository


class PostgresSavedFilterRepository(SavedFilterRepository):
    """PostgreSQL-backed repository for saved filter CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, filter_id: UUID) -> dict | None:
        model = await self._session.get(SavedFilterModel, filter_id)
        if model is None:
            return None
        return self._to_dict(model)

    async def find_by_user(self, user_id: UUID, entity_type: str | None = None) -> list[dict]:
        stmt = select(SavedFilterModel).where(SavedFilterModel.user_id == user_id)
        if entity_type is not None:
            stmt = stmt.where(SavedFilterModel.entity_type == entity_type)
        stmt = stmt.order_by(SavedFilterModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()]

    async def create(self, data: dict) -> UUID:
        model = SavedFilterModel(**data)
        self._session.add(model)
        await self._session.flush()
        return model.id

    async def update(self, filter_id: UUID, data: dict) -> None:
        model = await self._session.get(SavedFilterModel, filter_id)
        if model is None:
            return
        for key, value in data.items():
            setattr(model, key, value)
        await self._session.flush()

    async def delete(self, filter_id: UUID) -> None:
        model = await self._session.get(SavedFilterModel, filter_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def clear_default(self, user_id: UUID, entity_type: str) -> None:
        stmt = (
            update(SavedFilterModel)
            .where(
                SavedFilterModel.user_id == user_id,
                SavedFilterModel.entity_type == entity_type,
                SavedFilterModel.is_default == sa.true(),
            )
            .values(is_default=False)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    @staticmethod
    def _to_dict(model: SavedFilterModel) -> dict:
        return {
            "id": model.id,
            "user_id": model.user_id,
            "name": model.name,
            "entity_type": model.entity_type,
            "filter_config": model.filter_config,
            "is_default": model.is_default,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
