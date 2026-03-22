import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.application.command_handlers import (
    BulkCreateVRFsHandler,
    BulkDeleteVRFsHandler,
    BulkUpdateVRFsHandler,
    CreateVRFHandler,
    DeleteVRFHandler,
    UpdateVRFHandler,
)
from ipam.application.commands import (
    BulkCreateVRFsCommand,
    BulkDeleteVRFsCommand,
    BulkUpdateVRFItem,
    BulkUpdateVRFsCommand,
    CreateVRFCommand,
    DeleteVRFCommand,
    UpdateVRFCommand,
)
from ipam.application.queries import GetVRFQuery, ListVRFsQuery
from ipam.application.query_handlers import GetVRFHandler, ListVRFsHandler
from ipam.infrastructure.read_model_repository import PostgresVRFReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    CreateVRFRequest,
    UpdateVRFRequest,
    VRFListResponse,
    VRFResponse,
)
from ipam.interface.schemas import (
    BulkUpdateVRFItem as BulkUpdateVRFItemSchema,
)

router = APIRouter(prefix="/vrfs", tags=["vrfs"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
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
    bus.register(
        BulkUpdateVRFsCommand,
        BulkUpdateVRFsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteVRFsCommand,
        BulkDeleteVRFsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
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
    request: Request,
) -> VRFResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    vrf_id = await command_bus.dispatch(CreateVRFCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetVRFQuery(vrf_id=vrf_id))
    return VRFResponse(**result.model_dump())


@router.get("", response_model=VRFListResponse)
async def list_vrfs(
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
) -> VRFListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListVRFsQuery(
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
    return VRFListResponse(
        items=[VRFResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_vrfs(
    body: list[BulkUpdateVRFItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateVRFsCommand(
            items=[BulkUpdateVRFItem(vrf_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_vrfs(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteVRFsCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


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
    request: Request,
) -> VRFResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(UpdateVRFCommand(vrf_id=vrf_id, **body.model_dump(exclude_unset=True)))
    await session.commit()
    result = await query_bus.dispatch(GetVRFQuery(vrf_id=vrf_id))
    return VRFResponse(**result.model_dump())


@router.delete("/{vrf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vrf(
    vrf_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteVRFCommand(vrf_id=vrf_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_vrfs(
    body: list[CreateVRFRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(BulkCreateVRFsCommand(items=[CreateVRFCommand(**i.model_dump()) for i in body]))
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
