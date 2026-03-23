from __future__ import annotations

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from shared.api.filtering import FilterParam
from shared.api.sorting import SortParam
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.ip_range.infra.models import IPRangeReadModel
from ipam.ip_range.query.read_model import IPRangeReadModelRepository
from ipam.shared.infra.query_helpers import _apply_advanced_filters


class PostgresIPRangeReadModelRepository(IPRangeReadModelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = IPRangeReadModel(
            id=aggregate.id,
            start_address=aggregate.start_address.address if aggregate.start_address else "",
            end_address=aggregate.end_address.address if aggregate.end_address else "",
            vrf_id=aggregate.vrf_id,
            status=aggregate.status.value,
            tenant_id=aggregate.tenant_id,
            description=aggregate.description,
            custom_fields=aggregate.custom_fields,
            tags=[str(t) for t in aggregate.tags],
            is_deleted=aggregate._deleted,
        )
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        model = await self._session.get(IPRangeReadModel, entity_id)
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
        base = select(IPRangeReadModel).where(IPRangeReadModel.is_deleted == sa.false())
        filtered = _apply_advanced_filters(
            base,
            IPRangeReadModel,
            filters=filters,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        count_stmt = select(func.count()).select_from(filtered.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = filtered.offset(offset).limit(limit)
        if not sort_params:
            stmt = stmt.order_by(IPRangeReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(IPRangeReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    @staticmethod
    def _to_dict(model: IPRangeReadModel) -> dict:
        return {
            "id": model.id,
            "start_address": model.start_address,
            "end_address": model.end_address,
            "vrf_id": model.vrf_id,
            "status": model.status,
            "tenant_id": model.tenant_id,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
