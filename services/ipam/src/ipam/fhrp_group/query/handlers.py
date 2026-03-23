from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.fhrp_group.query.dto import FHRPGroupDTO
from ipam.fhrp_group.query.read_model import FHRPGroupReadModelRepository
from ipam.shared.query_utils import build_common_filters


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
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [FHRPGroupDTO(**item) for item in items], total
