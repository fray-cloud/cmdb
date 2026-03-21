from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ipam.application.command_handlers import (
    BulkCreateRouteTargetsHandler,
    BulkDeleteRouteTargetsHandler,
    BulkUpdateRouteTargetsHandler,
    CreateRouteTargetHandler,
    DeleteRouteTargetHandler,
    UpdateRouteTargetHandler,
)
from ipam.application.commands import (
    BulkCreateRouteTargetsCommand,
    BulkDeleteRouteTargetsCommand,
    BulkUpdateRouteTargetItem,
    BulkUpdateRouteTargetsCommand,
    CreateRouteTargetCommand,
    DeleteRouteTargetCommand,
    UpdateRouteTargetCommand,
)
from ipam.application.queries import GetRouteTargetQuery, ListRouteTargetsQuery
from ipam.application.query_handlers import GetRouteTargetHandler, ListRouteTargetsHandler
from ipam.infrastructure.read_model_repository import PostgresRouteTargetReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    CreateRouteTargetRequest,
    RouteTargetListResponse,
    RouteTargetResponse,
    UpdateRouteTargetRequest,
)
from ipam.interface.schemas import (
    BulkUpdateRouteTargetItem as BulkUpdateRouteTargetItemSchema,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/route-targets", tags=["route-targets"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresRouteTargetReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(CreateRouteTargetCommand, CreateRouteTargetHandler(event_store, read_model_repo, event_producer))
    bus.register(UpdateRouteTargetCommand, UpdateRouteTargetHandler(event_store, read_model_repo, event_producer))
    bus.register(DeleteRouteTargetCommand, DeleteRouteTargetHandler(event_store, read_model_repo, event_producer))
    bus.register(
        BulkCreateRouteTargetsCommand,
        BulkCreateRouteTargetsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateRouteTargetsCommand,
        BulkUpdateRouteTargetsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteRouteTargetsCommand,
        BulkDeleteRouteTargetsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresRouteTargetReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetRouteTargetQuery, GetRouteTargetHandler(read_model_repo))
    bus.register(ListRouteTargetsQuery, ListRouteTargetsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RouteTargetResponse,
)
async def create_route_target(
    body: CreateRouteTargetRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RouteTargetResponse:
    route_target_id = await command_bus.dispatch(CreateRouteTargetCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetRouteTargetQuery(route_target_id=route_target_id))
    return RouteTargetResponse(**result.model_dump())


@router.get("", response_model=RouteTargetListResponse)
async def list_route_targets(
    params: OffsetParams = Depends(),  # noqa: B008
    tenant_id: UUID | None = None,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RouteTargetListResponse:
    items, total = await query_bus.dispatch(
        ListRouteTargetsQuery(
            offset=params.offset,
            limit=params.limit,
            tenant_id=tenant_id,
        )
    )
    return RouteTargetListResponse(
        items=[RouteTargetResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_route_targets(
    body: list[BulkUpdateRouteTargetItemSchema],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkUpdateResponse:
    updated = await command_bus.dispatch(
        BulkUpdateRouteTargetsCommand(
            items=[
                BulkUpdateRouteTargetItem(route_target_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True))
                for i in body
            ]
        )
    )
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_route_targets(
    body: BulkDeleteRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkDeleteResponse:
    deleted = await command_bus.dispatch(BulkDeleteRouteTargetsCommand(ids=body.ids))
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{route_target_id}", response_model=RouteTargetResponse)
async def get_route_target(
    route_target_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RouteTargetResponse:
    result = await query_bus.dispatch(GetRouteTargetQuery(route_target_id=route_target_id))
    return RouteTargetResponse(**result.model_dump())


@router.patch("/{route_target_id}", response_model=RouteTargetResponse)
async def update_route_target(
    route_target_id: UUID,
    body: UpdateRouteTargetRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RouteTargetResponse:
    await command_bus.dispatch(
        UpdateRouteTargetCommand(route_target_id=route_target_id, **body.model_dump(exclude_unset=True))
    )
    result = await query_bus.dispatch(GetRouteTargetQuery(route_target_id=route_target_id))
    return RouteTargetResponse(**result.model_dump())


@router.delete("/{route_target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route_target(
    route_target_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteRouteTargetCommand(route_target_id=route_target_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_route_targets(
    body: list[CreateRouteTargetRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(
        BulkCreateRouteTargetsCommand(items=[CreateRouteTargetCommand(**i.model_dump()) for i in body])
    )
    return BulkCreateResponse(ids=ids, count=len(ids))
