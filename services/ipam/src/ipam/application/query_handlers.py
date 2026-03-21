from ipam.application.dto import (
    ASNDTO,
    RIRDTO,
    VLANDTO,
    VRFDTO,
    FHRPGroupDTO,
    IPAddressDTO,
    IPRangeDTO,
    PrefixDTO,
)
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
from ipam.domain.ip_address import IPAddress
from ipam.domain.prefix import Prefix
from ipam.domain.services import AvailablePrefixService, IPAvailabilityService, PrefixUtilizationService
from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

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
        filters: list[FilterParam] = []
        if query.vrf_id is not None:
            filters.append(FilterParam(field="vrf_id", operator=FilterOperator.EQ, value=str(query.vrf_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit, filters=filters or None)
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
        filters: list[FilterParam] = []
        if query.vrf_id is not None:
            filters.append(FilterParam(field="vrf_id", operator=FilterOperator.EQ, value=str(query.vrf_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit, filters=filters or None)
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
        filters: list[FilterParam] = []
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit, filters=filters or None)
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
        filters: list[FilterParam] = []
        if query.group_id is not None:
            filters.append(FilterParam(field="group_id", operator=FilterOperator.EQ, value=str(query.group_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit, filters=filters or None)
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
        filters: list[FilterParam] = []
        if query.vrf_id is not None:
            filters.append(FilterParam(field="vrf_id", operator=FilterOperator.EQ, value=str(query.vrf_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit, filters=filters or None)
        return [IPRangeDTO(**item) for item in items], total


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
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit)
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
        filters: list[FilterParam] = []
        if query.rir_id is not None:
            filters.append(FilterParam(field="rir_id", operator=FilterOperator.EQ, value=str(query.rir_id)))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit, filters=filters or None)
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
        items, total = await self._repo.find_all(offset=query.offset, limit=query.limit)
        return [FHRPGroupDTO(**item) for item in items], total


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
