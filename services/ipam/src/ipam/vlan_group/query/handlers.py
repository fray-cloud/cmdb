"""Query handlers for VLANGroup read operations."""

from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.shared.query_utils import build_common_filters
from ipam.vlan_group.query.dto import VLANGroupDTO
from ipam.vlan_group.query.read_model import VLANGroupReadModelRepository


class GetVLANGroupHandler(QueryHandler[VLANGroupDTO]):
    """Retrieve a single VLAN group by ID from the read model."""

    def __init__(self, read_model_repo: VLANGroupReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> VLANGroupDTO:
        """Fetch a VLAN group by ID and return its DTO representation."""
        data = await self._repo.find_by_id(query.vlan_group_id)
        if data is None:
            raise EntityNotFoundError(f"VLANGroup {query.vlan_group_id} not found")
        return VLANGroupDTO(**data)


class ListVLANGroupsHandler(QueryHandler[tuple[list[VLANGroupDTO], int]]):
    """Retrieve a paginated, filterable list of VLAN groups."""

    def __init__(self, read_model_repo: VLANGroupReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[VLANGroupDTO], int]:
        """Build filters from query params and return matching VLAN groups with total count."""
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
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
