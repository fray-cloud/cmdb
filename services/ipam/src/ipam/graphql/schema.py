import uuid

import strawberry
from strawberry.types import Info

from ipam.interface.graphql.gql_types import (
    ASNType,
    FHRPGroupType,
    IPAddressType,
    IPRangeType,
    PrefixType,
    RIRType,
    RouteTargetType,
    ServiceType,
    VLANGroupType,
    VLANType,
    VRFType,
)


def _dto_to_type(dto, type_cls):
    """Convert a Pydantic DTO to a Strawberry type."""
    return type_cls(**dto.model_dump())


@strawberry.type
class Query:
    # ---------------------------------------------------------------------------
    # Prefix
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def prefix(self, info: Info, id: uuid.UUID) -> PrefixType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetPrefixQuery

        dto = await query_bus.dispatch(GetPrefixQuery(prefix_id=id))
        return _dto_to_type(dto, PrefixType)

    @strawberry.field
    async def prefixes(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        vrf_id: uuid.UUID | None = None,
        status: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[PrefixType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListPrefixesQuery

        items, _ = await query_bus.dispatch(
            ListPrefixesQuery(offset=offset, limit=limit, vrf_id=vrf_id, status=status, tenant_id=tenant_id)
        )
        return [_dto_to_type(dto, PrefixType) for dto in items]

    # ---------------------------------------------------------------------------
    # IPAddress
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def ip_address(self, info: Info, id: uuid.UUID) -> IPAddressType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetIPAddressQuery

        dto = await query_bus.dispatch(GetIPAddressQuery(ip_id=id))
        return _dto_to_type(dto, IPAddressType)

    @strawberry.field
    async def ip_addresses(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        vrf_id: uuid.UUID | None = None,
        status: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[IPAddressType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListIPAddressesQuery

        items, _ = await query_bus.dispatch(
            ListIPAddressesQuery(offset=offset, limit=limit, vrf_id=vrf_id, status=status, tenant_id=tenant_id)
        )
        return [_dto_to_type(dto, IPAddressType) for dto in items]

    # ---------------------------------------------------------------------------
    # VRF
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def vrf(self, info: Info, id: uuid.UUID) -> VRFType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetVRFQuery

        dto = await query_bus.dispatch(GetVRFQuery(vrf_id=id))
        return _dto_to_type(dto, VRFType)

    @strawberry.field
    async def vrfs(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        tenant_id: uuid.UUID | None = None,
    ) -> list[VRFType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListVRFsQuery

        items, _ = await query_bus.dispatch(ListVRFsQuery(offset=offset, limit=limit, tenant_id=tenant_id))
        return [_dto_to_type(dto, VRFType) for dto in items]

    # ---------------------------------------------------------------------------
    # VLAN
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def vlan(self, info: Info, id: uuid.UUID) -> VLANType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetVLANQuery

        dto = await query_bus.dispatch(GetVLANQuery(vlan_id=id))
        return _dto_to_type(dto, VLANType)

    @strawberry.field
    async def vlans(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        group_id: uuid.UUID | None = None,
        status: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[VLANType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListVLANsQuery

        items, _ = await query_bus.dispatch(
            ListVLANsQuery(offset=offset, limit=limit, group_id=group_id, status=status, tenant_id=tenant_id)
        )
        return [_dto_to_type(dto, VLANType) for dto in items]

    # ---------------------------------------------------------------------------
    # IPRange
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def ip_range(self, info: Info, id: uuid.UUID) -> IPRangeType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetIPRangeQuery

        dto = await query_bus.dispatch(GetIPRangeQuery(range_id=id))
        return _dto_to_type(dto, IPRangeType)

    @strawberry.field
    async def ip_ranges(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        vrf_id: uuid.UUID | None = None,
        status: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[IPRangeType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListIPRangesQuery

        items, _ = await query_bus.dispatch(
            ListIPRangesQuery(offset=offset, limit=limit, vrf_id=vrf_id, status=status, tenant_id=tenant_id)
        )
        return [_dto_to_type(dto, IPRangeType) for dto in items]

    # ---------------------------------------------------------------------------
    # RIR
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def rir(self, info: Info, id: uuid.UUID) -> RIRType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetRIRQuery

        dto = await query_bus.dispatch(GetRIRQuery(rir_id=id))
        return _dto_to_type(dto, RIRType)

    @strawberry.field
    async def rirs(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
    ) -> list[RIRType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListRIRsQuery

        items, _ = await query_bus.dispatch(ListRIRsQuery(offset=offset, limit=limit))
        return [_dto_to_type(dto, RIRType) for dto in items]

    # ---------------------------------------------------------------------------
    # ASN
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def asn(self, info: Info, id: uuid.UUID) -> ASNType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetASNQuery

        dto = await query_bus.dispatch(GetASNQuery(asn_id=id))
        return _dto_to_type(dto, ASNType)

    @strawberry.field
    async def asns(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        rir_id: uuid.UUID | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[ASNType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListASNsQuery

        items, _ = await query_bus.dispatch(
            ListASNsQuery(offset=offset, limit=limit, rir_id=rir_id, tenant_id=tenant_id)
        )
        return [_dto_to_type(dto, ASNType) for dto in items]

    # ---------------------------------------------------------------------------
    # FHRPGroup
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def fhrp_group(self, info: Info, id: uuid.UUID) -> FHRPGroupType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetFHRPGroupQuery

        dto = await query_bus.dispatch(GetFHRPGroupQuery(fhrp_group_id=id))
        return _dto_to_type(dto, FHRPGroupType)

    @strawberry.field
    async def fhrp_groups(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
    ) -> list[FHRPGroupType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListFHRPGroupsQuery

        items, _ = await query_bus.dispatch(ListFHRPGroupsQuery(offset=offset, limit=limit))
        return [_dto_to_type(dto, FHRPGroupType) for dto in items]

    # ---------------------------------------------------------------------------
    # RouteTarget
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def route_target(self, info: Info, id: uuid.UUID) -> RouteTargetType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetRouteTargetQuery

        dto = await query_bus.dispatch(GetRouteTargetQuery(route_target_id=id))
        return _dto_to_type(dto, RouteTargetType)

    @strawberry.field
    async def route_targets(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        tenant_id: uuid.UUID | None = None,
    ) -> list[RouteTargetType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListRouteTargetsQuery

        items, _ = await query_bus.dispatch(ListRouteTargetsQuery(offset=offset, limit=limit, tenant_id=tenant_id))
        return [_dto_to_type(dto, RouteTargetType) for dto in items]

    # ---------------------------------------------------------------------------
    # VLANGroup
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def vlan_group(self, info: Info, id: uuid.UUID) -> VLANGroupType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetVLANGroupQuery

        dto = await query_bus.dispatch(GetVLANGroupQuery(vlan_group_id=id))
        return _dto_to_type(dto, VLANGroupType)

    @strawberry.field
    async def vlan_groups(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
        tenant_id: uuid.UUID | None = None,
    ) -> list[VLANGroupType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListVLANGroupsQuery

        items, _ = await query_bus.dispatch(ListVLANGroupsQuery(offset=offset, limit=limit, tenant_id=tenant_id))
        return [_dto_to_type(dto, VLANGroupType) for dto in items]

    # ---------------------------------------------------------------------------
    # Service
    # ---------------------------------------------------------------------------

    @strawberry.field
    async def service(self, info: Info, id: uuid.UUID) -> ServiceType:  # noqa: A002
        query_bus = info.context["query_bus"]
        from ipam.application.queries import GetServiceQuery

        dto = await query_bus.dispatch(GetServiceQuery(service_id=id))
        return _dto_to_type(dto, ServiceType)

    @strawberry.field
    async def services(
        self,
        info: Info,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ServiceType]:
        query_bus = info.context["query_bus"]
        from ipam.application.queries import ListServicesQuery

        items, _ = await query_bus.dispatch(ListServicesQuery(offset=offset, limit=limit))
        return [_dto_to_type(dto, ServiceType) for dto in items]


schema = strawberry.Schema(query=Query)
