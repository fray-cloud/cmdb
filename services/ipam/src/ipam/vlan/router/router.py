import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.shared.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    ChangeStatusRequest,
)
from ipam.vlan.command.commands import (
    BulkCreateVLANsCommand,
    BulkDeleteVLANsCommand,
    BulkUpdateVLANItem,
    BulkUpdateVLANsCommand,
    ChangeVLANStatusCommand,
    CreateVLANCommand,
    DeleteVLANCommand,
    UpdateVLANCommand,
)
from ipam.vlan.command.handlers import (
    BulkCreateVLANsHandler,
    BulkDeleteVLANsHandler,
    BulkUpdateVLANsHandler,
    ChangeVLANStatusHandler,
    CreateVLANHandler,
    DeleteVLANHandler,
    UpdateVLANHandler,
)
from ipam.vlan.infra.repository import PostgresVLANReadModelRepository
from ipam.vlan.query.handlers import GetVLANHandler, ListVLANsHandler
from ipam.vlan.query.queries import GetVLANQuery, ListVLANsQuery
from ipam.vlan.router.schemas import (
    BulkUpdateVLANItem as BulkUpdateVLANItemSchema,
)
from ipam.vlan.router.schemas import (
    CreateVLANRequest,
    UpdateVLANRequest,
    VLANListResponse,
    VLANResponse,
)

router = APIRouter(prefix="/vlans", tags=["vlans"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
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
    bus.register(
        BulkUpdateVLANsCommand,
        BulkUpdateVLANsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteVLANsCommand,
        BulkDeleteVLANsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
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
    request: Request,
) -> VLANResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    vlan_id = await command_bus.dispatch(CreateVLANCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetVLANQuery(vlan_id=vlan_id))
    return VLANResponse(**result.model_dump())


@router.get("", response_model=VLANListResponse)
async def list_vlans(
    params: OffsetParams = Depends(),  # noqa: B008
    group_id: UUID | None = None,
    status_filter: str | None = None,
    tenant_id: UUID | None = None,
    role: str | None = None,
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
) -> VLANListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListVLANsQuery(
            offset=params.offset,
            limit=params.limit,
            group_id=group_id,
            status=status_filter,
            tenant_id=tenant_id,
            role=role,
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
    return VLANListResponse(
        items=[VLANResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_vlans(
    body: list[BulkUpdateVLANItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateVLANsCommand(
            items=[BulkUpdateVLANItem(vlan_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_vlans(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteVLANsCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


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
    request: Request,
) -> VLANResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(UpdateVLANCommand(vlan_id=vlan_id, **body.model_dump(exclude_unset=True)))
    await session.commit()
    result = await query_bus.dispatch(GetVLANQuery(vlan_id=vlan_id))
    return VLANResponse(**result.model_dump())


@router.post("/{vlan_id}/status", response_model=VLANResponse)
async def change_vlan_status(
    vlan_id: UUID,
    body: ChangeStatusRequest,
    request: Request,
) -> VLANResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(ChangeVLANStatusCommand(vlan_id=vlan_id, status=body.status))
    await session.commit()
    result = await query_bus.dispatch(GetVLANQuery(vlan_id=vlan_id))
    return VLANResponse(**result.model_dump())


@router.delete("/{vlan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vlan(
    vlan_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteVLANCommand(vlan_id=vlan_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_vlans(
    body: list[CreateVLANRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(BulkCreateVLANsCommand(items=[CreateVLANCommand(**i.model_dump()) for i in body]))
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
