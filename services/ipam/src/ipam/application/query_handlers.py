from shared.api.filtering import FilterOperator, FilterParam
from shared.api.sorting import SortParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.application.dto import (
    ASNDTO,
    RIRDTO,
    VLANDTO,
    VRFDTO,
    FHRPGroupDTO,
    GlobalSearchResultDTO,
    IPAddressDTO,
    IPRangeDTO,
    PrefixDTO,
    RouteTargetDTO,
    SavedFilterDTO,
    SearchResultDTO,
    ServiceDTO,
    VLANGroupDTO,
)
from ipam.application.queries import BaseListQuery
from ipam.application.read_model import (
    ASNReadModelRepository,
    FHRPGroupReadModelRepository,
    GlobalSearchRepository,
    IPAddressReadModelRepository,
    IPRangeReadModelRepository,
    PrefixReadModelRepository,
    RIRReadModelRepository,
    RouteTargetReadModelRepository,
    SavedFilterRepository,
    ServiceReadModelRepository,
    VLANGroupReadModelRepository,
    VLANReadModelRepository,
    VRFReadModelRepository,
)
from ipam.domain.ip_address import IPAddress
from ipam.domain.ip_range import IPRange
from ipam.domain.prefix import Prefix
from ipam.domain.services import (
    AvailablePrefixService,
    IPAvailabilityService,
    IPRangeUtilizationService,
    PrefixUtilizationService,
)

# ---------------------------------------------------------------------------
# Common filter builder
# ---------------------------------------------------------------------------


def _build_common_filters(
    query: BaseListQuery,
) -> tuple[list[FilterParam], list[SortParam] | None, list[str] | None, dict[str, str] | None]:
    """Build common filters, sort params, tag_slugs, and custom_field_filters from BaseListQuery."""
    filters: list[FilterParam] = []

    if query.description_contains is not None:
        filters.append(
            FilterParam(field="description", operator=FilterOperator.ILIKE, value=query.description_contains)
        )
    if query.created_after is not None:
        filters.append(
            FilterParam(field="created_at", operator=FilterOperator.GTE, value=query.created_after.isoformat())
        )
    if query.created_before is not None:
        filters.append(
            FilterParam(field="created_at", operator=FilterOperator.LTE, value=query.created_before.isoformat())
        )
    if query.updated_after is not None:
        filters.append(
            FilterParam(field="updated_at", operator=FilterOperator.GTE, value=query.updated_after.isoformat())
        )
    if query.updated_before is not None:
        filters.append(
            FilterParam(field="updated_at", operator=FilterOperator.LTE, value=query.updated_before.isoformat())
        )

    sort_params: list[SortParam] | None = None
    if query.sort_by is not None:
        sort_params = [SortParam(field=query.sort_by, direction=query.sort_dir)]

    return filters, sort_params, query.tag_slugs, query.custom_field_filters


# ---------------------------------------------------------------------------
# Prefix
# ---------------------------------------------------------------------------


class GetPrefixHandler(QueryHandler[PrefixDTO]):
    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> PrefixDTO:
        data = await self._repo.find_by_id(query.prefix_id)
        if data is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        return PrefixDTO(**data)


class ListPrefixesHandler(QueryHandler[tuple[list[PrefixDTO], int]]):
    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[PrefixDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.vrf_id is not None:
            filters.append(FilterParam(field="vrf_id", operator=FilterOperator.EQ, value=str(query.vrf_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        if query.role is not None:
            filters.append(FilterParam(field="role", operator=FilterOperator.EQ, value=query.role))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [PrefixDTO(**item) for item in items], total


class GetPrefixChildrenHandler(QueryHandler[list[PrefixDTO]]):
    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> list[PrefixDTO]:
        parent = await self._repo.find_by_id(query.prefix_id)
        if parent is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        children = await self._repo.find_children(parent["network"], parent.get("vrf_id"))
        return [PrefixDTO(**child) for child in children]


class GetPrefixUtilizationHandler(QueryHandler[float]):
    def __init__(
        self,
        prefix_repo: PrefixReadModelRepository,
        ip_repo: IPAddressReadModelRepository,
        cache: object | None = None,
    ) -> None:
        self._prefix_repo = prefix_repo
        self._ip_repo = ip_repo
        self._service = PrefixUtilizationService()
        self._cache = cache

    async def handle(self, query: Query) -> float:
        if self._cache is not None:
            cache_key = f"prefix_utilization:{query.prefix_id}"
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return cached

        data = await self._prefix_repo.find_by_id(query.prefix_id)
        if data is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        prefix = _reconstruct_prefix(data)
        children_data = await self._prefix_repo.find_children(data["network"], data.get("vrf_id"))
        child_prefixes = [_reconstruct_prefix(c) for c in children_data]
        ips_data = await self._ip_repo.find_by_prefix(data["network"], data.get("vrf_id"))
        ip_addresses = [_reconstruct_ip(ip) for ip in ips_data]
        result = self._service.calculate(prefix, child_prefixes, ip_addresses)

        if self._cache is not None:
            await self._cache.set_json(cache_key, result)

        return result


class GetAvailablePrefixesHandler(QueryHandler[list[str]]):
    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo
        self._service = AvailablePrefixService()

    async def handle(self, query: Query) -> list[str]:
        data = await self._repo.find_by_id(query.prefix_id)
        if data is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        parent = _reconstruct_prefix(data)
        children_data = await self._repo.find_children(data["network"], data.get("vrf_id"))
        child_prefixes = [_reconstruct_prefix(c) for c in children_data]
        return self._service.find_available(parent, child_prefixes, query.desired_prefix_length)


class GetAvailableIPsHandler(QueryHandler[list[str]]):
    def __init__(
        self,
        prefix_repo: PrefixReadModelRepository,
        ip_repo: IPAddressReadModelRepository,
    ) -> None:
        self._prefix_repo = prefix_repo
        self._ip_repo = ip_repo
        self._service = IPAvailabilityService()

    async def handle(self, query: Query) -> list[str]:
        data = await self._prefix_repo.find_by_id(query.prefix_id)
        if data is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        prefix = _reconstruct_prefix(data)
        ips_data = await self._ip_repo.find_by_prefix(data["network"], data.get("vrf_id"))
        used_addresses = [_reconstruct_ip(ip) for ip in ips_data]
        return self._service.find_available(prefix, used_addresses, query.count)


# ---------------------------------------------------------------------------
# IPAddress
# ---------------------------------------------------------------------------


class GetIPAddressHandler(QueryHandler[IPAddressDTO]):
    def __init__(self, read_model_repo: IPAddressReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> IPAddressDTO:
        data = await self._repo.find_by_id(query.ip_id)
        if data is None:
            raise EntityNotFoundError(f"IPAddress {query.ip_id} not found")
        return IPAddressDTO(**data)


class ListIPAddressesHandler(QueryHandler[tuple[list[IPAddressDTO], int]]):
    def __init__(self, read_model_repo: IPAddressReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[IPAddressDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.vrf_id is not None:
            filters.append(FilterParam(field="vrf_id", operator=FilterOperator.EQ, value=str(query.vrf_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [IPAddressDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# VRF
# ---------------------------------------------------------------------------


class GetVRFHandler(QueryHandler[VRFDTO]):
    def __init__(self, read_model_repo: VRFReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> VRFDTO:
        data = await self._repo.find_by_id(query.vrf_id)
        if data is None:
            raise EntityNotFoundError(f"VRF {query.vrf_id} not found")
        return VRFDTO(**data)


class ListVRFsHandler(QueryHandler[tuple[list[VRFDTO], int]]):
    def __init__(self, read_model_repo: VRFReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[VRFDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [VRFDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# VLAN
# ---------------------------------------------------------------------------


class GetVLANHandler(QueryHandler[VLANDTO]):
    def __init__(self, read_model_repo: VLANReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> VLANDTO:
        data = await self._repo.find_by_id(query.vlan_id)
        if data is None:
            raise EntityNotFoundError(f"VLAN {query.vlan_id} not found")
        return VLANDTO(**data)


class ListVLANsHandler(QueryHandler[tuple[list[VLANDTO], int]]):
    def __init__(self, read_model_repo: VLANReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[VLANDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.group_id is not None:
            filters.append(FilterParam(field="group_id", operator=FilterOperator.EQ, value=str(query.group_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [VLANDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# IPRange
# ---------------------------------------------------------------------------


class GetIPRangeHandler(QueryHandler[IPRangeDTO]):
    def __init__(self, read_model_repo: IPRangeReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> IPRangeDTO:
        data = await self._repo.find_by_id(query.range_id)
        if data is None:
            raise EntityNotFoundError(f"IPRange {query.range_id} not found")
        return IPRangeDTO(**data)


class ListIPRangesHandler(QueryHandler[tuple[list[IPRangeDTO], int]]):
    def __init__(self, read_model_repo: IPRangeReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[IPRangeDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.vrf_id is not None:
            filters.append(FilterParam(field="vrf_id", operator=FilterOperator.EQ, value=str(query.vrf_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [IPRangeDTO(**item) for item in items], total


class GetIPRangeUtilizationHandler(QueryHandler[float]):
    def __init__(
        self,
        range_repo: IPRangeReadModelRepository,
        ip_repo: IPAddressReadModelRepository,
    ) -> None:
        self._range_repo = range_repo
        self._ip_repo = ip_repo
        self._service = IPRangeUtilizationService()

    async def handle(self, query: Query) -> float:
        data = await self._range_repo.find_by_id(query.range_id)
        if data is None:
            raise EntityNotFoundError(f"IPRange {query.range_id} not found")
        ip_range = _reconstruct_ip_range(data)
        ips_data = await self._ip_repo.find_ips_in_range(data["start_address"], data["end_address"], data.get("vrf_id"))
        used_addresses = [_reconstruct_ip(ip) for ip in ips_data]
        return self._service.calculate(ip_range, used_addresses)


# ---------------------------------------------------------------------------
# RIR
# ---------------------------------------------------------------------------


class GetRIRHandler(QueryHandler[RIRDTO]):
    def __init__(self, read_model_repo: RIRReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> RIRDTO:
        data = await self._repo.find_by_id(query.rir_id)
        if data is None:
            raise EntityNotFoundError(f"RIR {query.rir_id} not found")
        return RIRDTO(**data)


class ListRIRsHandler(QueryHandler[tuple[list[RIRDTO], int]]):
    def __init__(self, read_model_repo: RIRReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[RIRDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [RIRDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# ASN
# ---------------------------------------------------------------------------


class GetASNHandler(QueryHandler[ASNDTO]):
    def __init__(self, read_model_repo: ASNReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> ASNDTO:
        data = await self._repo.find_by_id(query.asn_id)
        if data is None:
            raise EntityNotFoundError(f"ASN {query.asn_id} not found")
        return ASNDTO(**data)


class ListASNsHandler(QueryHandler[tuple[list[ASNDTO], int]]):
    def __init__(self, read_model_repo: ASNReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[ASNDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.rir_id is not None:
            filters.append(FilterParam(field="rir_id", operator=FilterOperator.EQ, value=str(query.rir_id)))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [ASNDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# FHRPGroup
# ---------------------------------------------------------------------------


class GetFHRPGroupHandler(QueryHandler[FHRPGroupDTO]):
    def __init__(self, read_model_repo: FHRPGroupReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> FHRPGroupDTO:
        data = await self._repo.find_by_id(query.fhrp_group_id)
        if data is None:
            raise EntityNotFoundError(f"FHRPGroup {query.fhrp_group_id} not found")
        return FHRPGroupDTO(**data)


class ListFHRPGroupsHandler(QueryHandler[tuple[list[FHRPGroupDTO], int]]):
    def __init__(self, read_model_repo: FHRPGroupReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[FHRPGroupDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [FHRPGroupDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# RouteTarget
# ---------------------------------------------------------------------------


class GetRouteTargetHandler(QueryHandler[RouteTargetDTO]):
    def __init__(self, read_model_repo: RouteTargetReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> RouteTargetDTO:
        data = await self._repo.find_by_id(query.route_target_id)
        if data is None:
            raise EntityNotFoundError(f"RouteTarget {query.route_target_id} not found")
        return RouteTargetDTO(**data)


class ListRouteTargetsHandler(QueryHandler[tuple[list[RouteTargetDTO], int]]):
    def __init__(self, read_model_repo: RouteTargetReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[RouteTargetDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [RouteTargetDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# VLANGroup
# ---------------------------------------------------------------------------


class GetVLANGroupHandler(QueryHandler[VLANGroupDTO]):
    def __init__(self, read_model_repo: VLANGroupReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> VLANGroupDTO:
        data = await self._repo.find_by_id(query.vlan_group_id)
        if data is None:
            raise EntityNotFoundError(f"VLANGroup {query.vlan_group_id} not found")
        return VLANGroupDTO(**data)


class ListVLANGroupsHandler(QueryHandler[tuple[list[VLANGroupDTO], int]]):
    def __init__(self, read_model_repo: VLANGroupReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[VLANGroupDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [VLANGroupDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class GetServiceHandler(QueryHandler[ServiceDTO]):
    def __init__(self, read_model_repo: ServiceReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> ServiceDTO:
        data = await self._repo.find_by_id(query.service_id)
        if data is None:
            raise EntityNotFoundError(f"Service {query.service_id} not found")
        return ServiceDTO(**data)


class ListServicesHandler(QueryHandler[tuple[list[ServiceDTO], int]]):
    def __init__(self, read_model_repo: ServiceReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[ServiceDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [ServiceDTO(**item) for item in items], total


# ---------------------------------------------------------------------------
# Saved Filter
# ---------------------------------------------------------------------------


class GetSavedFilterHandler(QueryHandler[SavedFilterDTO]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, query: Query) -> SavedFilterDTO:
        data = await self._repo.find_by_id(query.filter_id)
        if data is None:
            raise EntityNotFoundError(f"SavedFilter {query.filter_id} not found")
        return SavedFilterDTO(**data)


class ListSavedFiltersHandler(QueryHandler[list[SavedFilterDTO]]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, query: Query) -> list[SavedFilterDTO]:
        items = await self._repo.find_by_user(query.user_id, query.entity_type)
        return [SavedFilterDTO(**item) for item in items]


# ---------------------------------------------------------------------------
# Global Search
# ---------------------------------------------------------------------------


class GlobalSearchHandler(QueryHandler[GlobalSearchResultDTO]):
    def __init__(self, search_repo: GlobalSearchRepository) -> None:
        self._repo = search_repo

    async def handle(self, query: Query) -> GlobalSearchResultDTO:
        results, total = await self._repo.search(query.q, query.entity_types, query.offset, query.limit)
        return GlobalSearchResultDTO(
            results=[SearchResultDTO(**r) for r in results],
            total=total,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reconstruct_prefix(data: dict) -> Prefix:
    """Reconstruct a Prefix domain object from read model data for domain service use."""
    from uuid import UUID

    prefix = Prefix(aggregate_id=UUID(str(data["id"])))
    from ipam.domain.value_objects import PrefixNetwork, PrefixStatus

    prefix.network = PrefixNetwork(network=data["network"]) if data.get("network") else None
    prefix.vrf_id = UUID(str(data["vrf_id"])) if data.get("vrf_id") else None
    prefix.vlan_id = UUID(str(data["vlan_id"])) if data.get("vlan_id") else None
    prefix.status = PrefixStatus(data["status"])
    prefix.role = data.get("role")
    prefix.tenant_id = UUID(str(data["tenant_id"])) if data.get("tenant_id") else None
    prefix.description = data.get("description", "")
    prefix.custom_fields = data.get("custom_fields", {})
    prefix.tags = [UUID(str(t)) for t in data.get("tags", [])]
    return prefix


def _reconstruct_ip_range(data: dict) -> IPRange:
    """Reconstruct an IPRange domain object from read model data for domain service use."""
    from uuid import UUID

    from ipam.domain.value_objects import IPAddressValue, IPRangeStatus

    ip_range = IPRange(aggregate_id=UUID(str(data["id"])))
    ip_range.start_address = IPAddressValue(address=data["start_address"]) if data.get("start_address") else None
    ip_range.end_address = IPAddressValue(address=data["end_address"]) if data.get("end_address") else None
    ip_range.vrf_id = UUID(str(data["vrf_id"])) if data.get("vrf_id") else None
    ip_range.status = IPRangeStatus(data["status"])
    ip_range.tenant_id = UUID(str(data["tenant_id"])) if data.get("tenant_id") else None
    ip_range.description = data.get("description", "")
    ip_range.custom_fields = data.get("custom_fields", {})
    ip_range.tags = [UUID(str(t)) for t in data.get("tags", [])]
    return ip_range


def _reconstruct_ip(data: dict) -> IPAddress:
    """Reconstruct an IPAddress domain object from read model data for domain service use."""
    from uuid import UUID

    from ipam.domain.value_objects import IPAddressStatus, IPAddressValue

    ip = IPAddress(aggregate_id=UUID(str(data["id"])))
    ip.address = IPAddressValue(address=data["address"]) if data.get("address") else None
    ip.vrf_id = UUID(str(data["vrf_id"])) if data.get("vrf_id") else None
    ip.status = IPAddressStatus(data["status"])
    ip.dns_name = data.get("dns_name", "")
    ip.tenant_id = UUID(str(data["tenant_id"])) if data.get("tenant_id") else None
    ip.description = data.get("description", "")
    ip.custom_fields = data.get("custom_fields", {})
    ip.tags = [UUID(str(t)) for t in data.get("tags", [])]
    return ip
