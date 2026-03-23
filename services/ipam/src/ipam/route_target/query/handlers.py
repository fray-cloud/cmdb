from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.route_target.query.dto import RouteTargetDTO
from ipam.route_target.query.read_model import RouteTargetReadModelRepository
from ipam.shared.query_utils import build_common_filters


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
        return [RouteTargetDTO(**item) for item in items], total
