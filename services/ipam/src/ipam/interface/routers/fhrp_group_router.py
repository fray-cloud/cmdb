from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ipam.application.command_handlers import (
    BulkCreateFHRPGroupsHandler,
    CreateFHRPGroupHandler,
    DeleteFHRPGroupHandler,
    UpdateFHRPGroupHandler,
)
from ipam.application.commands import (
    BulkCreateFHRPGroupsCommand,
    CreateFHRPGroupCommand,
    DeleteFHRPGroupCommand,
    UpdateFHRPGroupCommand,
)
from ipam.application.queries import GetFHRPGroupQuery, ListFHRPGroupsQuery
from ipam.application.query_handlers import GetFHRPGroupHandler, ListFHRPGroupsHandler
from ipam.infrastructure.read_model_repository import PostgresFHRPGroupReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    CreateFHRPGroupRequest,
    FHRPGroupListResponse,
    FHRPGroupResponse,
    UpdateFHRPGroupRequest,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/fhrp-groups", tags=["fhrp-groups"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresFHRPGroupReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(
        CreateFHRPGroupCommand,
        CreateFHRPGroupHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        UpdateFHRPGroupCommand,
        UpdateFHRPGroupHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        DeleteFHRPGroupCommand,
        DeleteFHRPGroupHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkCreateFHRPGroupsCommand,
        BulkCreateFHRPGroupsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresFHRPGroupReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetFHRPGroupQuery, GetFHRPGroupHandler(read_model_repo))
    bus.register(ListFHRPGroupsQuery, ListFHRPGroupsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=FHRPGroupResponse,
)
async def create_fhrp_group(
    body: CreateFHRPGroupRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> FHRPGroupResponse:
    group_id = await command_bus.dispatch(CreateFHRPGroupCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetFHRPGroupQuery(fhrp_group_id=group_id))
    return FHRPGroupResponse(**result.model_dump())


@router.get("", response_model=FHRPGroupListResponse)
async def list_fhrp_groups(
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> FHRPGroupListResponse:
    items, total = await query_bus.dispatch(ListFHRPGroupsQuery(offset=params.offset, limit=params.limit))
    return FHRPGroupListResponse(
        items=[FHRPGroupResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{fhrp_group_id}", response_model=FHRPGroupResponse)
async def get_fhrp_group(
    fhrp_group_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> FHRPGroupResponse:
    result = await query_bus.dispatch(GetFHRPGroupQuery(fhrp_group_id=fhrp_group_id))
    return FHRPGroupResponse(**result.model_dump())


@router.patch("/{fhrp_group_id}", response_model=FHRPGroupResponse)
async def update_fhrp_group(
    fhrp_group_id: UUID,
    body: UpdateFHRPGroupRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> FHRPGroupResponse:
    await command_bus.dispatch(
        UpdateFHRPGroupCommand(
            fhrp_group_id=fhrp_group_id,
            **body.model_dump(exclude_unset=True),
        )
    )
    result = await query_bus.dispatch(GetFHRPGroupQuery(fhrp_group_id=fhrp_group_id))
    return FHRPGroupResponse(**result.model_dump())


@router.delete("/{fhrp_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fhrp_group(
    fhrp_group_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteFHRPGroupCommand(fhrp_group_id=fhrp_group_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_fhrp_groups(
    body: list[CreateFHRPGroupRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(
        BulkCreateFHRPGroupsCommand(items=[CreateFHRPGroupCommand(**i.model_dump()) for i in body])
    )
    return BulkCreateResponse(ids=ids, count=len(ids))
