from __future__ import annotations

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from shared.api.filtering import FilterParam
from shared.api.sorting import SortParam
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.shared.infra.query_helpers import _apply_advanced_filters
from ipam.vlan.infra.models import VLANReadModel
from ipam.vlan.query.read_model import VLANReadModelRepository


class PostgresVLANReadModelRepository(VLANReadModelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = VLANReadModel(
            id=aggregate.id,
            vid=aggregate.vid.vid if aggregate.vid else 0,
            name=aggregate.name,
            group_id=aggregate.group_id,
            status=aggregate.status.value,
            role=aggregate.role,
            tenant_id=aggregate.tenant_id,
            description=aggregate.description,
            custom_fields=aggregate.custom_fields,
            tags=[str(t) for t in aggregate.tags],
            is_deleted=aggregate._deleted,
        )
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        model = await self._session.get(VLANReadModel, entity_id)
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
        base = select(VLANReadModel).where(VLANReadModel.is_deleted == sa.false())
        filtered = _apply_advanced_filters(
            base,
            VLANReadModel,
            filters=filters,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        count_stmt = select(func.count()).select_from(filtered.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = filtered.offset(offset).limit(limit)
        if not sort_params:
            stmt = stmt.order_by(VLANReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(VLANReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    async def find_by_vid(self, vid: int, group_id: UUID | None) -> dict | None:
        stmt = select(VLANReadModel).where(
            VLANReadModel.vid == vid,
            VLANReadModel.is_deleted == sa.false(),
        )
        if group_id is not None:
            stmt = stmt.where(VLANReadModel.group_id == group_id)
        else:
            stmt = stmt.where(VLANReadModel.group_id.is_(None))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_dict(model) if model else None

    @staticmethod
    def _to_dict(model: VLANReadModel) -> dict:
        return {
            "id": model.id,
            "vid": model.vid,
            "name": model.name,
            "group_id": model.group_id,
            "status": model.status,
            "role": model.role,
            "tenant_id": model.tenant_id,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
