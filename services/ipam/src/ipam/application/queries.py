from datetime import datetime
from typing import Any
from uuid import UUID

from shared.cqrs.query import Query

# --- Base ---


class BaseListQuery(Query):
    offset: int = 0
    limit: int = 50
    description_contains: str | None = None
    tag_slugs: list[str] | None = None
    custom_field_filters: dict[str, Any] | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None
    sort_by: str | None = None
    sort_dir: str = "asc"


# --- Prefix ---


class GetPrefixQuery(Query):
    prefix_id: UUID


class ListPrefixesQuery(BaseListQuery):
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None
    role: str | None = None


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


class ListIPAddressesQuery(BaseListQuery):
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


# --- VRF ---


class GetVRFQuery(Query):
    vrf_id: UUID


class ListVRFsQuery(BaseListQuery):
    tenant_id: UUID | None = None


# --- VLAN ---


class GetVLANQuery(Query):
    vlan_id: UUID


class ListVLANsQuery(BaseListQuery):
    group_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


# --- IPRange ---


class GetIPRangeQuery(Query):
    range_id: UUID


class ListIPRangesQuery(BaseListQuery):
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


class GetIPRangeUtilizationQuery(Query):
    range_id: UUID


# --- RIR ---


class GetRIRQuery(Query):
    rir_id: UUID


class ListRIRsQuery(BaseListQuery):
    pass


# --- ASN ---


class GetASNQuery(Query):
    asn_id: UUID


class ListASNsQuery(BaseListQuery):
    rir_id: UUID | None = None
    tenant_id: UUID | None = None


# --- FHRPGroup ---


class GetFHRPGroupQuery(Query):
    fhrp_group_id: UUID


class ListFHRPGroupsQuery(BaseListQuery):
    pass


# --- RouteTarget ---


class GetRouteTargetQuery(Query):
    route_target_id: UUID


class ListRouteTargetsQuery(BaseListQuery):
    tenant_id: UUID | None = None


# --- VLANGroup ---


class GetVLANGroupQuery(Query):
    vlan_group_id: UUID


class ListVLANGroupsQuery(BaseListQuery):
    tenant_id: UUID | None = None


# --- Service ---


class GetServiceQuery(Query):
    service_id: UUID


class ListServicesQuery(BaseListQuery):
    pass


# --- Saved Filter ---


class GetSavedFilterQuery(Query):
    filter_id: UUID


class ListSavedFiltersQuery(Query):
    user_id: UUID
    entity_type: str | None = None


# --- Global Search ---


class GlobalSearchQuery(Query):
    q: str
    entity_types: list[str] | None = None
    offset: int = 0
    limit: int = 20
