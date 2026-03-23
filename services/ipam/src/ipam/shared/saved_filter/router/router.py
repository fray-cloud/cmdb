from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.shared.saved_filter.command.commands import (
    CreateSavedFilterCommand,
    DeleteSavedFilterCommand,
    UpdateSavedFilterCommand,
)
from ipam.shared.saved_filter.command.handlers import (
    CreateSavedFilterHandler,
    DeleteSavedFilterHandler,
    UpdateSavedFilterHandler,
)
from ipam.shared.saved_filter.infra.repository import PostgresSavedFilterRepository
from ipam.shared.saved_filter.query.handlers import GetSavedFilterHandler, ListSavedFiltersHandler
from ipam.shared.saved_filter.query.queries import GetSavedFilterQuery, ListSavedFiltersQuery
from ipam.shared.saved_filter.router.schemas import (
    CreateSavedFilterRequest,
    SavedFilterListResponse,
    SavedFilterResponse,
    UpdateSavedFilterRequest,
)

router = APIRouter(prefix="/saved-filters", tags=["saved-filters"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
    repo = PostgresSavedFilterRepository(session)
    bus = CommandBus()
    bus.register(CreateSavedFilterCommand, CreateSavedFilterHandler(repo))
    bus.register(UpdateSavedFilterCommand, UpdateSavedFilterHandler(repo))
    bus.register(DeleteSavedFilterCommand, DeleteSavedFilterHandler(repo))
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    repo = PostgresSavedFilterRepository(session)
    bus = QueryBus()
    bus.register(GetSavedFilterQuery, GetSavedFilterHandler(repo))
    bus.register(ListSavedFiltersQuery, ListSavedFiltersHandler(repo))
    return bus


@router.post("", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_filter(
    body: CreateSavedFilterRequest,
    request: Request,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> SavedFilterResponse:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="X-User-ID header is required")
    filter_id = await command_bus.dispatch(
        CreateSavedFilterCommand(
            user_id=UUID(user_id),
            name=body.name,
            entity_type=body.entity_type,
            filter_config=body.filter_config,
            is_default=body.is_default,
        )
    )
    result = await query_bus.dispatch(GetSavedFilterQuery(filter_id=filter_id))
    return SavedFilterResponse(**result.model_dump())


@router.get("", response_model=SavedFilterListResponse)
async def list_saved_filters(
    request: Request,
    entity_type: str | None = None,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> SavedFilterListResponse:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="X-User-ID header is required")
    items = await query_bus.dispatch(ListSavedFiltersQuery(user_id=UUID(user_id), entity_type=entity_type))
    return SavedFilterListResponse(items=[SavedFilterResponse(**i.model_dump()) for i in items])


@router.get("/{filter_id}", response_model=SavedFilterResponse)
async def get_saved_filter(
    filter_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> SavedFilterResponse:
    result = await query_bus.dispatch(GetSavedFilterQuery(filter_id=filter_id))
    return SavedFilterResponse(**result.model_dump())


@router.patch("/{filter_id}", response_model=SavedFilterResponse)
async def update_saved_filter(
    filter_id: UUID,
    body: UpdateSavedFilterRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> SavedFilterResponse:
    await command_bus.dispatch(
        UpdateSavedFilterCommand(
            filter_id=filter_id,
            name=body.name,
            filter_config=body.filter_config,
            is_default=body.is_default,
        )
    )
    result = await query_bus.dispatch(GetSavedFilterQuery(filter_id=filter_id))
    return SavedFilterResponse(**result.model_dump())


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_filter(
    filter_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteSavedFilterCommand(filter_id=filter_id))
