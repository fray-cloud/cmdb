"""PostgreSQL implementation of the IPAddress read model repository."""

from __future__ import annotations

import ipaddress
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from shared.api.filtering import FilterParam
from shared.api.sorting import SortParam
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.ip_address.infra.models import IPAddressReadModel
from ipam.ip_address.query.read_model import IPAddressReadModelRepository
from ipam.shared.infra.query_helpers import _apply_advanced_filters


class PostgresIPAddressReadModelRepository(IPAddressReadModelRepository):
    """PostgreSQL-backed read model repository for IP address queries and projections."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = IPAddressReadModel(
            id=aggregate.id,
            address=str(aggregate.address.address) if aggregate.address else "",
            vrf_id=aggregate.vrf_id,
            status=aggregate.status.value,
            dns_name=aggregate.dns_name,
            tenant_id=aggregate.tenant_id,
            description=aggregate.description,
            custom_fields=aggregate.custom_fields,
            tags=[str(t) for t in aggregate.tags],
            is_deleted=aggregate._deleted,
        )
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        """Return an IP address dict by primary key, or None if not found or deleted."""
        model = await self._session.get(IPAddressReadModel, entity_id)
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
        """Return a paginated list of IP address records matching the given filters."""
        base = select(IPAddressReadModel).where(IPAddressReadModel.is_deleted == sa.false())
        filtered = _apply_advanced_filters(
            base,
            IPAddressReadModel,
            filters=filters,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        count_stmt = select(func.count()).select_from(filtered.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = filtered.offset(offset).limit(limit)
        if not sort_params:
            stmt = stmt.order_by(IPAddressReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(IPAddressReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    async def exists_in_vrf(self, address: str, vrf_id: UUID | None) -> bool:
        stmt = select(func.count()).where(
            IPAddressReadModel.address == address,
            IPAddressReadModel.is_deleted == sa.false(),
        )
        if vrf_id is not None:
            stmt = stmt.where(IPAddressReadModel.vrf_id == vrf_id)
        else:
            stmt = stmt.where(IPAddressReadModel.vrf_id.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def find_by_prefix(self, network: str, vrf_id: UUID | None) -> list[dict]:
        stmt = select(IPAddressReadModel).where(
            IPAddressReadModel.is_deleted == sa.false(),
        )
        if vrf_id is not None:
            stmt = stmt.where(IPAddressReadModel.vrf_id == vrf_id)
        else:
            stmt = stmt.where(IPAddressReadModel.vrf_id.is_(None))
        result = await self._session.execute(stmt)
        prefix_net = ipaddress.ip_network(network, strict=False)
        matched = []
        for row in result.scalars().all():
            try:
                addr_str = row.address.split("/")[0]
                addr = ipaddress.ip_address(addr_str)
            except ValueError:
                continue
            if addr in prefix_net:
                matched.append(self._to_dict(row))
        return matched

    async def find_ips_in_range(self, start_address: str, end_address: str, vrf_id: UUID | None) -> list[dict]:
        stmt = select(IPAddressReadModel).where(IPAddressReadModel.is_deleted == sa.false())
        if vrf_id is not None:
            stmt = stmt.where(IPAddressReadModel.vrf_id == vrf_id)
        else:
            stmt = stmt.where(IPAddressReadModel.vrf_id.is_(None))
        result = await self._session.execute(stmt)
        start_ip = ipaddress.ip_address(start_address)
        end_ip = ipaddress.ip_address(end_address)
        matched = []
        for row in result.scalars().all():
            try:
                addr_str = row.address.split("/")[0]
                addr = ipaddress.ip_address(addr_str)
            except ValueError:
                continue
            if start_ip <= addr <= end_ip:
                matched.append(self._to_dict(row))
        return matched

    @staticmethod
    def _to_dict(model: IPAddressReadModel) -> dict:
        return {
            "id": model.id,
            "address": model.address,
            "vrf_id": model.vrf_id,
            "status": model.status,
            "dns_name": model.dns_name,
            "tenant_id": model.tenant_id,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
