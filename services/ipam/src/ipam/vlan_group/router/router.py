"""FastAPI router for VLANGroup CRUD endpoints."""

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
)
from ipam.vlan_group.command import (
    BulkCreateVLANGroupsCommand,
    BulkCreateVLANGroupsHandler,
    BulkDeleteVLANGroupsCommand,
    BulkDeleteVLANGroupsHandler,
    BulkUpdateVLANGroupItem,
    BulkUpdateVLANGroupsCommand,
    BulkUpdateVLANGroupsHandler,
    CreateVLANGroupCommand,
    CreateVLANGroupHandler,
    DeleteVLANGroupCommand,
    DeleteVLANGroupHandler,
    UpdateVLANGroupCommand,
    UpdateVLANGroupHandler,
)
from ipam.vlan_group.infra import PostgresVLANGroupReadModelRepository
from ipam.vlan_group.query import GetVLANGroupHandler, GetVLANGroupQuery, ListVLANGroupsHandler, ListVLANGroupsQuery
from ipam.vlan_group.router.schemas import (
    BulkUpdateVLANGroupItem as BulkUpdateVLANGroupItemSchema,
)
from ipam.vlan_group.router.schemas import (
    CreateVLANGroupRequest,
    UpdateVLANGroupRequest,
    VLANGroupListResponse,
    VLANGroupResponse,
)

router = APIRouter(prefix="/vlan-groups", tags=["vlan-groups"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresVLANGroupReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(CreateVLANGroupCommand, CreateVLANGroupHandler(event_store, read_model_repo, event_producer))
    bus.register(UpdateVLANGroupCommand, UpdateVLANGroupHandler(event_store, read_model_repo, event_producer))
    bus.register(DeleteVLANGroupCommand, DeleteVLANGroupHandler(event_store, read_model_repo, event_producer))
    bus.register(
        BulkCreateVLANGroupsCommand,
        BulkCreateVLANGroupsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateVLANGroupsCommand,
        BulkUpdateVLANGroupsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteVLANGroupsCommand,
        BulkDeleteVLANGroupsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresVLANGroupReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetVLANGroupQuery, GetVLANGroupHandler(read_model_repo))
    bus.register(ListVLANGroupsQuery, ListVLANGroupsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=VLANGroupResponse,
)
async def create_vlan_group(
    body: CreateVLANGroupRequest,
    request: Request,
) -> VLANGroupResponse:
    """Create a new VLAN group."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    vlan_group_id = await command_bus.dispatch(CreateVLANGroupCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetVLANGroupQuery(vlan_group_id=vlan_group_id))
    return VLANGroupResponse(**result.model_dump())


@router.get("", response_model=VLANGroupListResponse)
async def list_vlan_groups(
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
) -> VLANGroupListResponse:
    """List VLAN groups with pagination, filtering, and sorting."""
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListVLANGroupsQuery(
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
    return VLANGroupListResponse(
        items=[VLANGroupResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_vlan_groups(
    body: list[BulkUpdateVLANGroupItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    """Bulk update multiple VLAN groups."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateVLANGroupsCommand(
            items=[
                BulkUpdateVLANGroupItem(vlan_group_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True))
                for i in body
            ]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_vlan_groups(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    """Bulk delete multiple VLAN groups by ID."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteVLANGroupsCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{vlan_group_id}", response_model=VLANGroupResponse)
async def get_vlan_group(
    vlan_group_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANGroupResponse:
    """Retrieve a single VLAN group by ID."""
    result = await query_bus.dispatch(GetVLANGroupQuery(vlan_group_id=vlan_group_id))
    return VLANGroupResponse(**result.model_dump())


@router.patch("/{vlan_group_id}", response_model=VLANGroupResponse)
async def update_vlan_group(
    vlan_group_id: UUID,
    body: UpdateVLANGroupRequest,
    request: Request,
) -> VLANGroupResponse:
    """Partially update a VLAN group."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(
        UpdateVLANGroupCommand(vlan_group_id=vlan_group_id, **body.model_dump(exclude_unset=True))
    )
    await session.commit()
    result = await query_bus.dispatch(GetVLANGroupQuery(vlan_group_id=vlan_group_id))
    return VLANGroupResponse(**result.model_dump())


@router.delete("/{vlan_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vlan_group(
    vlan_group_id: UUID,
    request: Request,
) -> None:
    """Delete a VLAN group by ID."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteVLANGroupCommand(vlan_group_id=vlan_group_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_vlan_groups(
    body: list[CreateVLANGroupRequest],
    request: Request,
) -> BulkCreateResponse:
    """Bulk create multiple VLAN groups."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(
        BulkCreateVLANGroupsCommand(items=[CreateVLANGroupCommand(**i.model_dump()) for i in body])
    )
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
