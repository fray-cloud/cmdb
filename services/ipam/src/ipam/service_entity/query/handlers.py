from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.service_entity.query.dto import ServiceDTO
from ipam.service_entity.query.read_model import ServiceReadModelRepository
from ipam.shared.query_utils import build_common_filters


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
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [ServiceDTO(**item) for item in items], total
