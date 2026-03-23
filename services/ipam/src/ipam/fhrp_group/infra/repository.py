"""FHRP Group PostgreSQL read model repository implementation."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from shared.api.filtering import FilterParam
from shared.api.sorting import SortParam
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.fhrp_group.infra.models import FHRPGroupReadModel
from ipam.fhrp_group.query.read_model import FHRPGroupReadModelRepository
from ipam.shared.infra.query_helpers import _apply_advanced_filters


class PostgresFHRPGroupReadModelRepository(FHRPGroupReadModelRepository):
    """PostgreSQL-backed read model repository for FHRP Group queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = FHRPGroupReadModel(
            id=aggregate.id,
            protocol=aggregate.protocol.value if aggregate.protocol else "",
            group_id_value=aggregate.group_id_value,
            auth_type=aggregate.auth_type.value,
            auth_key=aggregate.auth_key,
            name=aggregate.name,
            description=aggregate.description,
            custom_fields=aggregate.custom_fields,
            tags=[str(t) for t in aggregate.tags],
            is_deleted=aggregate._deleted,
        )
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        """Find a single FHRP Group by ID, returning None if not found or deleted."""
        model = await self._session.get(FHRPGroupReadModel, entity_id)
        if model is None or model.is_deleted:
            return None
        return self._to_dict(model)

    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: list[FilterParam] | None = None,
        sort_params: list[SortParam] | None = None,
        tag_slugs: list[str] | None = None,
        custom_field_filters: dict[str, str] | None = None,
    ) -> tuple[list[dict], int]:
        """Return a paginated, filtered list of FHRP Groups with total count."""
        base = select(FHRPGroupReadModel).where(FHRPGroupReadModel.is_deleted == sa.false())
        filtered = _apply_advanced_filters(
            base,
            FHRPGroupReadModel,
            filters=filters,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        count_stmt = select(func.count()).select_from(filtered.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = filtered.offset(offset).limit(limit)
        if not sort_params:
            stmt = stmt.order_by(FHRPGroupReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(FHRPGroupReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    @staticmethod
    def _to_dict(model: FHRPGroupReadModel) -> dict:
        return {
            "id": model.id,
            "protocol": model.protocol,
            "group_id_value": model.group_id_value,
            "auth_type": model.auth_type,
            "auth_key": model.auth_key,
            "name": model.name,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
