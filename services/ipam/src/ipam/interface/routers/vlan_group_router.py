import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam

from ipam.application.command_handlers import (
    BulkCreateVLANGroupsHandler,
    BulkDeleteVLANGroupsHandler,
    BulkUpdateVLANGroupsHandler,
    CreateVLANGroupHandler,
    DeleteVLANGroupHandler,
    UpdateVLANGroupHandler,
)
from ipam.application.commands import (
    BulkCreateVLANGroupsCommand,
    BulkDeleteVLANGroupsCommand,
    BulkUpdateVLANGroupItem,
    BulkUpdateVLANGroupsCommand,
    CreateVLANGroupCommand,
    DeleteVLANGroupCommand,
    UpdateVLANGroupCommand,
)
from ipam.application.queries import GetVLANGroupQuery, ListVLANGroupsQuery
from ipam.application.query_handlers import GetVLANGroupHandler, ListVLANGroupsHandler
from ipam.infrastructure.read_model_repository import PostgresVLANGroupReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    CreateVLANGroupRequest,
    UpdateVLANGroupRequest,
    VLANGroupListResponse,
    VLANGroupResponse,
)
from ipam.interface.schemas import (
    BulkUpdateVLANGroupItem as BulkUpdateVLANGroupItemSchema,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/vlan-groups", tags=["vlan-groups"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
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


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
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
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANGroupResponse:
    vlan_group_id = await command_bus.dispatch(CreateVLANGroupCommand(**body.model_dump()))
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
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkUpdateResponse:
    updated = await command_bus.dispatch(
        BulkUpdateVLANGroupsCommand(
            items=[
                BulkUpdateVLANGroupItem(vlan_group_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True))
                for i in body
            ]
        )
    )
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_vlan_groups(
    body: BulkDeleteRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkDeleteResponse:
    deleted = await command_bus.dispatch(BulkDeleteVLANGroupsCommand(ids=body.ids))
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{vlan_group_id}", response_model=VLANGroupResponse)
async def get_vlan_group(
    vlan_group_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANGroupResponse:
    result = await query_bus.dispatch(GetVLANGroupQuery(vlan_group_id=vlan_group_id))
    return VLANGroupResponse(**result.model_dump())


@router.patch("/{vlan_group_id}", response_model=VLANGroupResponse)
async def update_vlan_group(
    vlan_group_id: UUID,
    body: UpdateVLANGroupRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> VLANGroupResponse:
    await command_bus.dispatch(
        UpdateVLANGroupCommand(vlan_group_id=vlan_group_id, **body.model_dump(exclude_unset=True))
    )
    result = await query_bus.dispatch(GetVLANGroupQuery(vlan_group_id=vlan_group_id))
    return VLANGroupResponse(**result.model_dump())


@router.delete("/{vlan_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vlan_group(
    vlan_group_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteVLANGroupCommand(vlan_group_id=vlan_group_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_vlan_groups(
    body: list[CreateVLANGroupRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(
        BulkCreateVLANGroupsCommand(items=[CreateVLANGroupCommand(**i.model_dump()) for i in body])
    )
    return BulkCreateResponse(ids=ids, count=len(ids))
