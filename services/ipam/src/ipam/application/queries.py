from uuid import UUID

from shared.cqrs.query import Query

# --- Prefix ---


class GetPrefixQuery(Query):
    prefix_id: UUID


class ListPrefixesQuery(Query):
    offset: int = 0
    limit: int = 50
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


class GetPrefixChildrenQuery(Query):
    prefix_id: UUID


class GetPrefixUtilizationQuery(Query):
    prefix_id: UUID


class GetAvailablePrefixesQuery(Query):
    prefix_id: UUID
    desired_prefix_length: int


class GetAvailableIPsQuery(Query):
    prefix_id: UUID
    count: int = 1


# --- IPAddress ---


class GetIPAddressQuery(Query):
    ip_id: UUID


class ListIPAddressesQuery(Query):
    offset: int = 0
    limit: int = 50
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


# --- VRF ---


class GetVRFQuery(Query):
    vrf_id: UUID


class ListVRFsQuery(Query):
    offset: int = 0
    limit: int = 50
    tenant_id: UUID | None = None


# --- VLAN ---


class GetVLANQuery(Query):
    vlan_id: UUID


class ListVLANsQuery(Query):
    offset: int = 0
    limit: int = 50
    group_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


# --- IPRange ---


class GetIPRangeQuery(Query):
    range_id: UUID


class ListIPRangesQuery(Query):
    offset: int = 0
    limit: int = 50
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


class GetIPRangeUtilizationQuery(Query):
    range_id: UUID


# --- RIR ---


class GetRIRQuery(Query):
    rir_id: UUID


class ListRIRsQuery(Query):
    offset: int = 0
    limit: int = 50


# --- ASN ---


class GetASNQuery(Query):
    asn_id: UUID


class ListASNsQuery(Query):
    offset: int = 0
    limit: int = 50
    rir_id: UUID | None = None
    tenant_id: UUID | None = None


# --- FHRPGroup ---


class GetFHRPGroupQuery(Query):
    fhrp_group_id: UUID


class ListFHRPGroupsQuery(Query):
    offset: int = 0
    limit: int = 50


# --- RouteTarget ---


class GetRouteTargetQuery(Query):
    route_target_id: UUID


class ListRouteTargetsQuery(Query):
    offset: int = 0
    limit: int = 50
    tenant_id: UUID | None = None


# --- VLANGroup ---


class GetVLANGroupQuery(Query):
    vlan_group_id: UUID


class ListVLANGroupsQuery(Query):
    offset: int = 0
    limit: int = 50
    tenant_id: UUID | None = None


# --- Service ---


class GetServiceQuery(Query):
    service_id: UUID


class ListServicesQuery(Query):
    offset: int = 0
    limit: int = 50
