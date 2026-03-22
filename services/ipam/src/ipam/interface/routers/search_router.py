from fastapi import APIRouter, Depends, Request
from fastapi import Query as QueryParam

from ipam.application.queries import GlobalSearchQuery
from ipam.application.query_handlers import GlobalSearchHandler
from ipam.infrastructure.search_repository import PostgresGlobalSearchRepository
from ipam.interface.schemas import GlobalSearchResponse, SearchResultResponse
from shared.cqrs.bus import QueryBus

router = APIRouter(prefix="/search", tags=["search"])


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    search_repo = PostgresGlobalSearchRepository(session)
    bus = QueryBus()
    bus.register(GlobalSearchQuery, GlobalSearchHandler(search_repo))
    return bus


@router.get("", response_model=GlobalSearchResponse)
async def global_search(
    q: str,
    entity_types: list[str] | None = QueryParam(None),  # noqa: B008
    offset: int = 0,
    limit: int = 20,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> GlobalSearchResponse:
    result = await query_bus.dispatch(GlobalSearchQuery(q=q, entity_types=entity_types, offset=offset, limit=limit))
    return GlobalSearchResponse(
        results=[SearchResultResponse(**r.model_dump()) for r in result.results],
        total=result.total,
    )
