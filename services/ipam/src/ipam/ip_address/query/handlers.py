"""Query handlers for IPAddress read operations."""

from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.ip_address.query.dto import IPAddressDTO
from ipam.ip_address.query.read_model import IPAddressReadModelRepository
from ipam.shared.query_utils import build_common_filters


class GetIPAddressHandler(QueryHandler[IPAddressDTO]):
    """Retrieve a single IP address by ID from the read model."""

    def __init__(self, read_model_repo: IPAddressReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> IPAddressDTO:
        """Fetch an IP address by ID and return its DTO representation."""
        data = await self._repo.find_by_id(query.ip_id)
        if data is None:
            raise EntityNotFoundError(f"IPAddress {query.ip_id} not found")
        return IPAddressDTO(**data)


class ListIPAddressesHandler(QueryHandler[tuple[list[IPAddressDTO], int]]):
    """Retrieve a paginated, filterable list of IP addresses."""

    def __init__(self, read_model_repo: IPAddressReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[IPAddressDTO], int]:
        """Build filters from query params and return matching IP addresses with total count."""
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
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
