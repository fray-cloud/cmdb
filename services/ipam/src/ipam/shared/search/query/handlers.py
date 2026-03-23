"""Global search query handler — full-text search across all IPAM entities."""

from shared.cqrs.query import Query, QueryHandler

from ipam.shared.search.query.dto import GlobalSearchResultDTO, SearchResultDTO
from ipam.shared.search.query.read_model import GlobalSearchRepository


class GlobalSearchHandler(QueryHandler[GlobalSearchResultDTO]):
    """Handle GlobalSearchQuery by searching across all IPAM read models."""

    def __init__(self, search_repo: GlobalSearchRepository) -> None:
        self._repo = search_repo

    async def handle(self, query: Query) -> GlobalSearchResultDTO:
        results, total = await self._repo.search(query.q, query.entity_types, query.offset, query.limit)
        return GlobalSearchResultDTO(
            results=[SearchResultDTO(**r) for r in results],
            total=total,
        )
