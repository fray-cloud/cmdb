import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.route_target.command.commands import (
    BulkCreateRouteTargetsCommand,
    BulkDeleteRouteTargetsCommand,
    BulkUpdateRouteTargetItem,
    BulkUpdateRouteTargetsCommand,
    CreateRouteTargetCommand,
    DeleteRouteTargetCommand,
    UpdateRouteTargetCommand,
)
from ipam.route_target.command.handlers import (
    BulkCreateRouteTargetsHandler,
    BulkDeleteRouteTargetsHandler,
    BulkUpdateRouteTargetsHandler,
    CreateRouteTargetHandler,
    DeleteRouteTargetHandler,
    UpdateRouteTargetHandler,
)
from ipam.route_target.infra.repository import PostgresRouteTargetReadModelRepository
from ipam.route_target.query.handlers import GetRouteTargetHandler, ListRouteTargetsHandler
from ipam.route_target.query.queries import GetRouteTargetQuery, ListRouteTargetsQuery
from ipam.route_target.router.schemas import (
    BulkUpdateRouteTargetItem as BulkUpdateRouteTargetItemSchema,
)
from ipam.route_target.router.schemas import (
    CreateRouteTargetRequest,
    RouteTargetListResponse,
    RouteTargetResponse,
    UpdateRouteTargetRequest,
)
from ipam.shared.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
)

router = APIRouter(prefix="/route-targets", tags=["route-targets"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
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


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
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
    request: Request,
) -> RouteTargetResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    route_target_id = await command_bus.dispatch(CreateRouteTargetCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetRouteTargetQuery(route_target_id=route_target_id))
    return RouteTargetResponse(**result.model_dump())


@router.get("", response_model=RouteTargetListResponse)
async def list_route_targets(
    params: OffsetParams = Depends(),  # noqa: B008
    tenant_id: UUID | None = None,
    description_contains: str | None = None,
    tag_slugs: list[str] | None = QueryParam(None),  # noqa: B008
    custom_fields: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
    sort_by: str | None = None,
    sort_dir: str = "asc",
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RouteTargetListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListRouteTargetsQuery(
            offset=params.offset,
            limit=params.limit,
            tenant_id=tenant_id,
            description_contains=description_contains,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
            created_after=created_after,
            created_before=created_before,
            updated_after=updated_after,
            updated_before=updated_before,
            sort_by=sort_by,
            sort_dir=sort_dir,
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
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateRouteTargetsCommand(
            items=[
                BulkUpdateRouteTargetItem(route_target_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True))
                for i in body
            ]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_route_targets(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteRouteTargetsCommand(ids=body.ids))
    await session.commit()
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
    request: Request,
) -> RouteTargetResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(
        UpdateRouteTargetCommand(route_target_id=route_target_id, **body.model_dump(exclude_unset=True))
    )
    await session.commit()
    result = await query_bus.dispatch(GetRouteTargetQuery(route_target_id=route_target_id))
    return RouteTargetResponse(**result.model_dump())


@router.delete("/{route_target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route_target(
    route_target_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteRouteTargetCommand(route_target_id=route_target_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_route_targets(
    body: list[CreateRouteTargetRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(
        BulkCreateRouteTargetsCommand(items=[CreateRouteTargetCommand(**i.model_dump()) for i in body])
    )
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
