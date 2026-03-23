from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.rir.query.dto import RIRDTO
from ipam.rir.query.read_model import RIRReadModelRepository
from ipam.shared.query_utils import build_common_filters


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
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [RIRDTO(**item) for item in items], total
