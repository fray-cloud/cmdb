from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ipam.application.command_handlers import (
    BulkCreateVRFsHandler,
    CreateVRFHandler,
    DeleteVRFHandler,
    UpdateVRFHandler,
)
from ipam.application.commands import (
    BulkCreateVRFsCommand,
    CreateVRFCommand,
    DeleteVRFCommand,
    UpdateVRFCommand,
)
from ipam.application.queries import GetVRFQuery, ListVRFsQuery
from ipam.application.query_handlers import GetVRFHandler, ListVRFsHandler
from ipam.infrastructure.read_model_repository import PostgresVRFReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    CreateVRFRequest,
    UpdateVRFRequest,
    VRFListResponse,
    VRFResponse,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/vrfs", tags=["vrfs"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresVRFReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(CreateVRFCommand, CreateVRFHandler(event_store, read_model_repo, event_producer))
    bus.register(UpdateVRFCommand, UpdateVRFHandler(event_store, read_model_repo, event_producer))
    bus.register(DeleteVRFCommand, DeleteVRFHandler(event_store, read_model_repo, event_producer))
    bus.register(
        BulkCreateVRFsCommand,
        BulkCreateVRFsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresVRFReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetVRFQuery, GetVRFHandler(read_model_repo))
    bus.register(ListVRFsQuery, ListVRFsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=VRFResponse,
)
async def create_vrf(
    body: CreateVRFRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VRFResponse:
    vrf_id = await command_bus.dispatch(CreateVRFCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetVRFQuery(vrf_id=vrf_id))
    return VRFResponse(**result.model_dump())


@router.get("", response_model=VRFListResponse)
async def list_vrfs(
    params: OffsetParams = Depends(),  # noqa: B008
    tenant_id: UUID | None = None,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VRFListResponse:
    items, total = await query_bus.dispatch(
        ListVRFsQuery(offset=params.offset, limit=params.limit, tenant_id=tenant_id)
    )
    return VRFListResponse(
        items=[VRFResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{vrf_id}", response_model=VRFResponse)
async def get_vrf(
    vrf_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VRFResponse:
    result = await query_bus.dispatch(GetVRFQuery(vrf_id=vrf_id))
    return VRFResponse(**result.model_dump())


@router.patch("/{vrf_id}", response_model=VRFResponse)
async def update_vrf(
    vrf_id: UUID,
    body: UpdateVRFRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VRFResponse:
    await command_bus.dispatch(UpdateVRFCommand(vrf_id=vrf_id, **body.model_dump(exclude_unset=True)))
    result = await query_bus.dispatch(GetVRFQuery(vrf_id=vrf_id))
    return VRFResponse(**result.model_dump())


@router.delete("/{vrf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vrf(
    vrf_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteVRFCommand(vrf_id=vrf_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_vrfs(
    body: list[CreateVRFRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(BulkCreateVRFsCommand(items=[CreateVRFCommand(**i.model_dump()) for i in body]))
    return BulkCreateResponse(ids=ids, count=len(ids))
