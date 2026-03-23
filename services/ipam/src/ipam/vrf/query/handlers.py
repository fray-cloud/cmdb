from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.shared.query_utils import build_common_filters
from ipam.vrf.query.dto import VRFDTO
from ipam.vrf.query.read_model import VRFReadModelRepository


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
        return [VRFDTO(**item) for item in items], total
