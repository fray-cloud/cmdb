"""FastAPI router for IPRange CRUD and utilization endpoints."""

import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.ip_address.infra import PostgresIPAddressReadModelRepository
from ipam.ip_range.command import (
    BulkCreateIPRangesCommand,
    BulkCreateIPRangesHandler,
    BulkDeleteIPRangesCommand,
    BulkDeleteIPRangesHandler,
    BulkUpdateIPRangeItem,
    BulkUpdateIPRangesCommand,
    BulkUpdateIPRangesHandler,
    ChangeIPRangeStatusCommand,
    ChangeIPRangeStatusHandler,
    CreateIPRangeCommand,
    CreateIPRangeHandler,
    DeleteIPRangeCommand,
    DeleteIPRangeHandler,
    UpdateIPRangeCommand,
    UpdateIPRangeHandler,
)
from ipam.ip_range.infra import PostgresIPRangeReadModelRepository
from ipam.ip_range.query import (
    GetIPRangeHandler,
    GetIPRangeQuery,
    GetIPRangeUtilizationHandler,
    GetIPRangeUtilizationQuery,
    ListIPRangesHandler,
    ListIPRangesQuery,
)
from ipam.ip_range.router.schemas import (
    BulkUpdateIPRangeItem as BulkUpdateIPRangeItemSchema,
)
from ipam.ip_range.router.schemas import (
    CreateIPRangeRequest,
    IPRangeListResponse,
    IPRangeResponse,
    UpdateIPRangeRequest,
)
from ipam.shared.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    ChangeStatusRequest,
)

router = APIRouter(prefix="/ip-ranges", tags=["ip-ranges"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresIPRangeReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(
        CreateIPRangeCommand,
        CreateIPRangeHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        UpdateIPRangeCommand,
        UpdateIPRangeHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        ChangeIPRangeStatusCommand,
        ChangeIPRangeStatusHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        DeleteIPRangeCommand,
        DeleteIPRangeHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkCreateIPRangesCommand,
        BulkCreateIPRangesHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateIPRangesCommand,
        BulkUpdateIPRangesHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteIPRangesCommand,
        BulkDeleteIPRangesHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresIPRangeReadModelRepository(session)
    ip_repo = PostgresIPAddressReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetIPRangeQuery, GetIPRangeHandler(read_model_repo))
    bus.register(ListIPRangesQuery, ListIPRangesHandler(read_model_repo))
    bus.register(GetIPRangeUtilizationQuery, GetIPRangeUtilizationHandler(read_model_repo, ip_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IPRangeResponse,
)
async def create_ip_range(
    body: CreateIPRangeRequest,
    request: Request,
) -> IPRangeResponse:
    """Create a new IP range."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    range_id = await command_bus.dispatch(CreateIPRangeCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.get("", response_model=IPRangeListResponse)
async def list_ip_ranges(
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
) -> IPRangeListResponse:
    """List IP ranges with pagination, filtering, and sorting."""
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListIPRangesQuery(
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
    return IPRangeListResponse(
        items=[IPRangeResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_ip_ranges(
    body: list[BulkUpdateIPRangeItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    """Bulk update multiple IP ranges."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateIPRangesCommand(
            items=[
                BulkUpdateIPRangeItem(range_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body
            ]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_ip_ranges(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    """Bulk delete multiple IP ranges by ID."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteIPRangesCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{range_id}", response_model=IPRangeResponse)
async def get_ip_range(
    range_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPRangeResponse:
    """Retrieve a single IP range by ID."""
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.patch("/{range_id}", response_model=IPRangeResponse)
async def update_ip_range(
    range_id: UUID,
    body: UpdateIPRangeRequest,
    request: Request,
) -> IPRangeResponse:
    """Partially update an IP range."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(UpdateIPRangeCommand(range_id=range_id, **body.model_dump(exclude_unset=True)))
    await session.commit()
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.post("/{range_id}/status", response_model=IPRangeResponse)
async def change_ip_range_status(
    range_id: UUID,
    body: ChangeStatusRequest,
    request: Request,
) -> IPRangeResponse:
    """Change the lifecycle status of an IP range."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(ChangeIPRangeStatusCommand(range_id=range_id, status=body.status))
    await session.commit()
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.delete("/{range_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ip_range(
    range_id: UUID,
    request: Request,
) -> None:
    """Delete an IP range by ID."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteIPRangeCommand(range_id=range_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_ip_ranges(
    body: list[CreateIPRangeRequest],
    request: Request,
) -> BulkCreateResponse:
    """Bulk create multiple IP ranges."""
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(
        BulkCreateIPRangesCommand(items=[CreateIPRangeCommand(**i.model_dump()) for i in body])
    )
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))


@router.get("/{range_id}/utilization")
async def get_ip_range_utilization(
    range_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> dict:
    """Get address utilization for an IP range."""
    utilization = await query_bus.dispatch(GetIPRangeUtilizationQuery(range_id=range_id))
    return {"range_id": range_id, "utilization": utilization}
