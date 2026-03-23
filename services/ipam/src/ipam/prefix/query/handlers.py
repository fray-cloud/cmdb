"""Query handlers for Prefix read operations."""

from uuid import UUID

from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.ip_address.query.read_model import IPAddressReadModelRepository
from ipam.prefix import Prefix, PrefixNetwork, PrefixStatus
from ipam.prefix.query.dto import PrefixDTO
from ipam.prefix.query.read_model import PrefixReadModelRepository
from ipam.shared.query_utils import build_common_filters, reconstruct_ip
from ipam.shared.services import AvailablePrefixService, IPAvailabilityService, PrefixUtilizationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reconstruct_prefix(data: dict) -> Prefix:
    """Reconstruct a Prefix domain object from read model data for domain service use."""
    prefix = Prefix(aggregate_id=UUID(str(data["id"])))
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


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


class GetPrefixHandler(QueryHandler[PrefixDTO]):
    """Retrieve a single prefix by ID from the read model."""

    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> PrefixDTO:
        """Fetch a prefix by ID and return its DTO representation."""
        data = await self._repo.find_by_id(query.prefix_id)
        if data is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        return PrefixDTO(**data)


class ListPrefixesHandler(QueryHandler[tuple[list[PrefixDTO], int]]):
    """Retrieve a paginated, filterable list of prefixes."""

    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[PrefixDTO], int]:
        """Build filters from query params and return matching prefixes with total count."""
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
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
    """Retrieve child prefixes contained within a parent prefix."""

    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> list[PrefixDTO]:
        """Find all prefixes that are subnets of the given parent prefix."""
        parent = await self._repo.find_by_id(query.prefix_id)
        if parent is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        children = await self._repo.find_children(parent["network"], parent.get("vrf_id"))
        return [PrefixDTO(**child) for child in children]


class GetPrefixUtilizationHandler(QueryHandler[float]):
    """Calculate address space utilization for a prefix."""

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
        """Return the utilization ratio of the prefix address space."""
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
        ip_addresses = [reconstruct_ip(ip) for ip in ips_data]
        result = self._service.calculate(prefix, child_prefixes, ip_addresses)

        if self._cache is not None:
            await self._cache.set_json(cache_key, result)

        return result


class GetAvailablePrefixesHandler(QueryHandler[list[str]]):
    """Find available sub-prefixes within a parent prefix."""

    def __init__(self, read_model_repo: PrefixReadModelRepository) -> None:
        self._repo = read_model_repo
        self._service = AvailablePrefixService()

    async def handle(self, query: Query) -> list[str]:
        """Return available sub-prefixes of the desired length."""
        data = await self._repo.find_by_id(query.prefix_id)
        if data is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        parent = _reconstruct_prefix(data)
        children_data = await self._repo.find_children(data["network"], data.get("vrf_id"))
        child_prefixes = [_reconstruct_prefix(c) for c in children_data]
        return self._service.find_available(parent, child_prefixes, query.desired_prefix_length)


class GetAvailableIPsHandler(QueryHandler[list[str]]):
    """Find available IP addresses within a prefix."""

    def __init__(
        self,
        prefix_repo: PrefixReadModelRepository,
        ip_repo: IPAddressReadModelRepository,
    ) -> None:
        self._prefix_repo = prefix_repo
        self._ip_repo = ip_repo
        self._service = IPAvailabilityService()

    async def handle(self, query: Query) -> list[str]:
        """Return a list of unallocated IP addresses from the prefix."""
        data = await self._prefix_repo.find_by_id(query.prefix_id)
        if data is None:
            raise EntityNotFoundError(f"Prefix {query.prefix_id} not found")
        prefix = _reconstruct_prefix(data)
        ips_data = await self._ip_repo.find_by_prefix(data["network"], data.get("vrf_id"))
        used_addresses = [reconstruct_ip(ip) for ip in ips_data]
        return self._service.find_available(prefix, used_addresses, query.count)
