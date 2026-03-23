from __future__ import annotations

import ipaddress
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from shared.api.filtering import FilterParam
from shared.api.sorting import SortParam
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.prefix.infra.models import PrefixReadModel
from ipam.prefix.query.read_model import PrefixReadModelRepository
from ipam.shared.infra.query_helpers import _apply_advanced_filters


class PostgresPrefixReadModelRepository(PrefixReadModelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = PrefixReadModel(
            id=aggregate.id,
            network=str(aggregate.network.network) if aggregate.network else "",
            vrf_id=aggregate.vrf_id,
            vlan_id=aggregate.vlan_id,
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
        model = await self._session.get(PrefixReadModel, entity_id)
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
        base = select(PrefixReadModel).where(PrefixReadModel.is_deleted == sa.false())
        filtered = _apply_advanced_filters(
            base,
            PrefixReadModel,
            filters=filters,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        count_stmt = select(func.count()).select_from(filtered.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = filtered.offset(offset).limit(limit)
        if not sort_params:
            stmt = stmt.order_by(PrefixReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(PrefixReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    async def find_children(self, parent_network: str, vrf_id: UUID | None) -> list[dict]:
        stmt = select(PrefixReadModel).where(
            PrefixReadModel.is_deleted == sa.false(),
            PrefixReadModel.network != parent_network,
        )
        if vrf_id is not None:
            stmt = stmt.where(PrefixReadModel.vrf_id == vrf_id)
        else:
            stmt = stmt.where(PrefixReadModel.vrf_id.is_(None))
        result = await self._session.execute(stmt)
        parent_net = ipaddress.ip_network(parent_network, strict=False)
        children = []
        for row in result.scalars().all():
            try:
                child_net = ipaddress.ip_network(row.network, strict=False)
            except ValueError:
                continue
            if child_net.subnet_of(parent_net):
                children.append(self._to_dict(row))
        return children

    async def find_by_vrf(self, vrf_id: UUID, *, offset: int = 0, limit: int = 50) -> tuple[list[dict], int]:
        stmt = select(PrefixReadModel).where(
            PrefixReadModel.vrf_id == vrf_id,
            PrefixReadModel.is_deleted == sa.false(),
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(PrefixReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    @staticmethod
    def _to_dict(model: PrefixReadModel) -> dict:
        return {
            "id": model.id,
            "network": model.network,
            "vrf_id": model.vrf_id,
            "vlan_id": model.vlan_id,
            "status": model.status,
            "role": model.role,
            "tenant_id": model.tenant_id,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
