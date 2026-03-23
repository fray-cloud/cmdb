from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.shared.saved_filter.query.dto import SavedFilterDTO
from ipam.shared.saved_filter.query.read_model import SavedFilterRepository


class GetSavedFilterHandler(QueryHandler[SavedFilterDTO]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, query: Query) -> SavedFilterDTO:
        data = await self._repo.find_by_id(query.filter_id)
        if data is None:
            raise EntityNotFoundError(f"SavedFilter {query.filter_id} not found")
        return SavedFilterDTO(**data)


class ListSavedFiltersHandler(QueryHandler[list[SavedFilterDTO]]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, query: Query) -> list[SavedFilterDTO]:
        items = await self._repo.find_by_user(query.user_id, query.entity_type)
        return [SavedFilterDTO(**item) for item in items]
