import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam

from ipam.application.command_handlers import (
    BulkCreateIPAddressesHandler,
    BulkDeleteIPAddressesHandler,
    BulkUpdateIPAddressesHandler,
    ChangeIPAddressStatusHandler,
    CreateIPAddressHandler,
    DeleteIPAddressHandler,
    UpdateIPAddressHandler,
)
from ipam.application.commands import (
    BulkCreateIPAddressesCommand,
    BulkDeleteIPAddressesCommand,
    BulkUpdateIPAddressesCommand,
    BulkUpdateIPAddressItem,
    ChangeIPAddressStatusCommand,
    CreateIPAddressCommand,
    DeleteIPAddressCommand,
    UpdateIPAddressCommand,
)
from ipam.application.queries import GetIPAddressQuery, ListIPAddressesQuery
from ipam.application.query_handlers import GetIPAddressHandler, ListIPAddressesHandler
from ipam.infrastructure.read_model_repository import PostgresIPAddressReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    ChangeStatusRequest,
    CreateIPAddressRequest,
    IPAddressListResponse,
    IPAddressResponse,
    UpdateIPAddressRequest,
)
from ipam.interface.schemas import (
    BulkUpdateIPAddressItem as BulkUpdateIPAddressItemSchema,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/ip-addresses", tags=["ip-addresses"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresIPAddressReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(
        CreateIPAddressCommand,
        CreateIPAddressHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        UpdateIPAddressCommand,
        UpdateIPAddressHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        ChangeIPAddressStatusCommand,
        ChangeIPAddressStatusHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        DeleteIPAddressCommand,
        DeleteIPAddressHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkCreateIPAddressesCommand,
        BulkCreateIPAddressesHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateIPAddressesCommand,
        BulkUpdateIPAddressesHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteIPAddressesCommand,
        BulkDeleteIPAddressesHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresIPAddressReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetIPAddressQuery, GetIPAddressHandler(read_model_repo))
    bus.register(ListIPAddressesQuery, ListIPAddressesHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IPAddressResponse,
)
async def create_ip_address(
    body: CreateIPAddressRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPAddressResponse:
    ip_id = await command_bus.dispatch(CreateIPAddressCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetIPAddressQuery(ip_id=ip_id))
    return IPAddressResponse(**result.model_dump())


@router.get("", response_model=IPAddressListResponse)
async def list_ip_addresses(
    params: OffsetParams = Depends(),  # noqa: B008
    vrf_id: UUID | None = None,
    status_filter: str | None = None,
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
) -> IPAddressListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListIPAddressesQuery(
            offset=params.offset,
            limit=params.limit,
            vrf_id=vrf_id,
            status=status_filter,
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
    return IPAddressListResponse(
        items=[IPAddressResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_ip_addresses(
    body: list[BulkUpdateIPAddressItemSchema],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkUpdateResponse:
    updated = await command_bus.dispatch(
        BulkUpdateIPAddressesCommand(
            items=[
                BulkUpdateIPAddressItem(ip_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body
            ]
        )
    )
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_ip_addresses(
    body: BulkDeleteRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkDeleteResponse:
    deleted = await command_bus.dispatch(BulkDeleteIPAddressesCommand(ids=body.ids))
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{ip_id}", response_model=IPAddressResponse)
async def get_ip_address(
    ip_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPAddressResponse:
    result = await query_bus.dispatch(GetIPAddressQuery(ip_id=ip_id))
    return IPAddressResponse(**result.model_dump())


@router.patch("/{ip_id}", response_model=IPAddressResponse)
async def update_ip_address(
    ip_id: UUID,
    body: UpdateIPAddressRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPAddressResponse:
    await command_bus.dispatch(UpdateIPAddressCommand(ip_id=ip_id, **body.model_dump(exclude_unset=True)))
    result = await query_bus.dispatch(GetIPAddressQuery(ip_id=ip_id))
    return IPAddressResponse(**result.model_dump())


@router.post("/{ip_id}/status", response_model=IPAddressResponse)
async def change_ip_address_status(
    ip_id: UUID,
    body: ChangeStatusRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPAddressResponse:
    await command_bus.dispatch(ChangeIPAddressStatusCommand(ip_id=ip_id, status=body.status))
    result = await query_bus.dispatch(GetIPAddressQuery(ip_id=ip_id))
    return IPAddressResponse(**result.model_dump())


@router.delete("/{ip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ip_address(
    ip_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteIPAddressCommand(ip_id=ip_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_ip_addresses(
    body: list[CreateIPAddressRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(
        BulkCreateIPAddressesCommand(items=[CreateIPAddressCommand(**i.model_dump()) for i in body])
    )
    return BulkCreateResponse(ids=ids, count=len(ids))
