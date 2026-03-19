from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ipam.application.command_handlers import (
    BulkCreateVLANsHandler,
    ChangeVLANStatusHandler,
    CreateVLANHandler,
    DeleteVLANHandler,
    UpdateVLANHandler,
)
from ipam.application.commands import (
    BulkCreateVLANsCommand,
    ChangeVLANStatusCommand,
    CreateVLANCommand,
    DeleteVLANCommand,
    UpdateVLANCommand,
)
from ipam.application.queries import GetVLANQuery, ListVLANsQuery
from ipam.application.query_handlers import GetVLANHandler, ListVLANsHandler
from ipam.infrastructure.read_model_repository import PostgresVLANReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    ChangeStatusRequest,
    CreateVLANRequest,
    UpdateVLANRequest,
    VLANListResponse,
    VLANResponse,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/vlans", tags=["vlans"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresVLANReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(
        CreateVLANCommand,
        CreateVLANHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        UpdateVLANCommand,
        UpdateVLANHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        ChangeVLANStatusCommand,
        ChangeVLANStatusHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        DeleteVLANCommand,
        DeleteVLANHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkCreateVLANsCommand,
        BulkCreateVLANsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresVLANReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetVLANQuery, GetVLANHandler(read_model_repo))
    bus.register(ListVLANsQuery, ListVLANsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=VLANResponse,
)
async def create_vlan(
    body: CreateVLANRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANResponse:
    vlan_id = await command_bus.dispatch(CreateVLANCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetVLANQuery(vlan_id=vlan_id))
    return VLANResponse(**result.model_dump())


@router.get("", response_model=VLANListResponse)
async def list_vlans(
    params: OffsetParams = Depends(),  # noqa: B008
    group_id: UUID | None = None,
    status_filter: str | None = None,
    tenant_id: UUID | None = None,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANListResponse:
    items, total = await query_bus.dispatch(
        ListVLANsQuery(
            offset=params.offset,
            limit=params.limit,
            group_id=group_id,
            status=status_filter,
            tenant_id=tenant_id,
        )
    )
    return VLANListResponse(
        items=[VLANResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{vlan_id}", response_model=VLANResponse)
async def get_vlan(
    vlan_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANResponse:
    result = await query_bus.dispatch(GetVLANQuery(vlan_id=vlan_id))
    return VLANResponse(**result.model_dump())


@router.patch("/{vlan_id}", response_model=VLANResponse)
async def update_vlan(
    vlan_id: UUID,
    body: UpdateVLANRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANResponse:
    await command_bus.dispatch(UpdateVLANCommand(vlan_id=vlan_id, **body.model_dump(exclude_unset=True)))
    result = await query_bus.dispatch(GetVLANQuery(vlan_id=vlan_id))
    return VLANResponse(**result.model_dump())


@router.post("/{vlan_id}/status", response_model=VLANResponse)
async def change_vlan_status(
    vlan_id: UUID,
    body: ChangeStatusRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANResponse:
    await command_bus.dispatch(ChangeVLANStatusCommand(vlan_id=vlan_id, status=body.status))
    result = await query_bus.dispatch(GetVLANQuery(vlan_id=vlan_id))
    return VLANResponse(**result.model_dump())


@router.delete("/{vlan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vlan(
    vlan_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteVLANCommand(vlan_id=vlan_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_vlans(
    body: list[CreateVLANRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(BulkCreateVLANsCommand(items=[CreateVLANCommand(**i.model_dump()) for i in body]))
    return BulkCreateResponse(ids=ids, count=len(ids))
