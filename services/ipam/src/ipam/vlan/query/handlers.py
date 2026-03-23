"""Query handlers for VLAN read operations."""

from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.shared.query_utils import build_common_filters
from ipam.vlan.query.dto import VLANDTO
from ipam.vlan.query.read_model import VLANReadModelRepository


class GetVLANHandler(QueryHandler[VLANDTO]):
    """Retrieve a single VLAN by ID from the read model."""

    def __init__(self, read_model_repo: VLANReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> VLANDTO:
        """Fetch a VLAN by ID and return its DTO representation."""
        data = await self._repo.find_by_id(query.vlan_id)
        if data is None:
            raise EntityNotFoundError(f"VLAN {query.vlan_id} not found")
        return VLANDTO(**data)


class ListVLANsHandler(QueryHandler[tuple[list[VLANDTO], int]]):
    """Retrieve a paginated, filterable list of VLANs."""

    def __init__(self, read_model_repo: VLANReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[VLANDTO], int]:
        """Build filters from query params and return matching VLANs with total count."""
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
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
