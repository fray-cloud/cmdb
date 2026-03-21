from __future__ import annotations

import ipaddress
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.application.read_model import (
    ASNReadModelRepository,
    FHRPGroupReadModelRepository,
    IPAddressReadModelRepository,
    IPRangeReadModelRepository,
    PrefixReadModelRepository,
    RIRReadModelRepository,
    VLANReadModelRepository,
    VRFReadModelRepository,
)
from ipam.infrastructure.models import (
    ASNReadModel,
    FHRPGroupReadModel,
    IPAddressReadModel,
    IPRangeReadModel,
    PrefixReadModel,
    RIRReadModel,
    VLANReadModel,
    VRFReadModel,
)
from shared.api.filtering import FilterParam, apply_filters

# ---------------------------------------------------------------------------
# Prefix
# ---------------------------------------------------------------------------


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
    ) -> tuple[list[dict], int]:
        stmt = select(PrefixReadModel).where(PrefixReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, PrefixReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(PrefixReadModel.created_at.desc())
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


# ---------------------------------------------------------------------------
# IP Address
# ---------------------------------------------------------------------------


class PostgresIPAddressReadModelRepository(IPAddressReadModelRepository):
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
    ) -> tuple[list[dict], int]:
        stmt = select(IPAddressReadModel).where(IPAddressReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, IPAddressReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(IPAddressReadModel.created_at.desc())
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


# ---------------------------------------------------------------------------
# VRF
# ---------------------------------------------------------------------------


class PostgresVRFReadModelRepository(VRFReadModelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = VRFReadModel(
            id=aggregate.id,
            name=aggregate.name,
            rd=aggregate.rd.rd if aggregate.rd else None,
            tenant_id=aggregate.tenant_id,
            description=aggregate.description,
            custom_fields=aggregate.custom_fields,
            tags=[str(t) for t in aggregate.tags],
            is_deleted=aggregate._deleted,
        )
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        model = await self._session.get(VRFReadModel, entity_id)
        if model is None or model.is_deleted:
            return None
        return self._to_dict(model)

    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: list[FilterParam] | None = None,
    ) -> tuple[list[dict], int]:
        stmt = select(VRFReadModel).where(VRFReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, VRFReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(VRFReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(VRFReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    async def find_by_name(self, name: str) -> dict | None:
        stmt = select(VRFReadModel).where(
            VRFReadModel.name == name,
            VRFReadModel.is_deleted == sa.false(),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_dict(model) if model else None

    @staticmethod
    def _to_dict(model: VRFReadModel) -> dict:
        return {
            "id": model.id,
            "name": model.name,
            "rd": model.rd,
            "tenant_id": model.tenant_id,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }


# ---------------------------------------------------------------------------
# VLAN
# ---------------------------------------------------------------------------


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
    ) -> tuple[list[dict], int]:
        stmt = select(VLANReadModel).where(VLANReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, VLANReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(VLANReadModel.created_at.desc())
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


# ---------------------------------------------------------------------------
# IP Range
# ---------------------------------------------------------------------------


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
    ) -> tuple[list[dict], int]:
        stmt = select(IPRangeReadModel).where(IPRangeReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, IPRangeReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(IPRangeReadModel.created_at.desc())
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


# ---------------------------------------------------------------------------
# RIR
# ---------------------------------------------------------------------------


class PostgresRIRReadModelRepository(RIRReadModelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = RIRReadModel(
            id=aggregate.id,
            name=aggregate.name,
            is_private=aggregate.is_private,
            description=aggregate.description,
            custom_fields=aggregate.custom_fields,
            tags=[str(t) for t in aggregate.tags],
            is_deleted=aggregate._deleted,
        )
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        model = await self._session.get(RIRReadModel, entity_id)
        if model is None or model.is_deleted:
            return None
        return self._to_dict(model)

    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: list[FilterParam] | None = None,
    ) -> tuple[list[dict], int]:
        stmt = select(RIRReadModel).where(RIRReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, RIRReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(RIRReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(RIRReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    async def find_by_name(self, name: str) -> dict | None:
        stmt = select(RIRReadModel).where(
            RIRReadModel.name == name,
            RIRReadModel.is_deleted == sa.false(),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_dict(model) if model else None

    @staticmethod
    def _to_dict(model: RIRReadModel) -> dict:
        return {
            "id": model.id,
            "name": model.name,
            "is_private": model.is_private,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }


# ---------------------------------------------------------------------------
# ASN
# ---------------------------------------------------------------------------


class PostgresASNReadModelRepository(ASNReadModelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        model = ASNReadModel(
            id=aggregate.id,
            asn=aggregate.asn.asn if aggregate.asn else 0,
            rir_id=aggregate.rir_id,
            tenant_id=aggregate.tenant_id,
            description=aggregate.description,
            custom_fields=aggregate.custom_fields,
            tags=[str(t) for t in aggregate.tags],
            is_deleted=aggregate._deleted,
        )
        await self._session.merge(model)
        await self._session.flush()

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        model = await self._session.get(ASNReadModel, entity_id)
        if model is None or model.is_deleted:
            return None
        return self._to_dict(model)

    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: list[FilterParam] | None = None,
    ) -> tuple[list[dict], int]:
        stmt = select(ASNReadModel).where(ASNReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, ASNReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(ASNReadModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_dict(r) for r in result.scalars().all()], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        model = await self._session.get(ASNReadModel, entity_id)
        if model:
            model.is_deleted = True
            await self._session.flush()

    async def find_by_asn(self, asn: int) -> dict | None:
        stmt = select(ASNReadModel).where(
            ASNReadModel.asn == asn,
            ASNReadModel.is_deleted == sa.false(),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_dict(model) if model else None

    @staticmethod
    def _to_dict(model: ASNReadModel) -> dict:
        return {
            "id": model.id,
            "asn": model.asn,
            "rir_id": model.rir_id,
            "tenant_id": model.tenant_id,
            "description": model.description,
            "custom_fields": model.custom_fields,
            "tags": [UUID(t) if isinstance(t, str) else t for t in (model.tags or [])],
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }


# ---------------------------------------------------------------------------
# FHRP Group
# ---------------------------------------------------------------------------


class PostgresFHRPGroupReadModelRepository(FHRPGroupReadModelRepository):
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
    ) -> tuple[list[dict], int]:
        stmt = select(FHRPGroupReadModel).where(FHRPGroupReadModel.is_deleted == sa.false())
        if filters:
            stmt = apply_filters(stmt, FHRPGroupReadModel, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(FHRPGroupReadModel.created_at.desc())
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
