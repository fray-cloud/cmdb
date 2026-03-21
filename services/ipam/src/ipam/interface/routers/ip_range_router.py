from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ipam.application.command_handlers import (
    BulkCreateIPRangesHandler,
    ChangeIPRangeStatusHandler,
    CreateIPRangeHandler,
    DeleteIPRangeHandler,
    UpdateIPRangeHandler,
)
from ipam.application.commands import (
    BulkCreateIPRangesCommand,
    ChangeIPRangeStatusCommand,
    CreateIPRangeCommand,
    DeleteIPRangeCommand,
    UpdateIPRangeCommand,
)
from ipam.application.queries import GetIPRangeQuery, GetIPRangeUtilizationQuery, ListIPRangesQuery
from ipam.application.query_handlers import GetIPRangeHandler, GetIPRangeUtilizationHandler, ListIPRangesHandler
from ipam.infrastructure.read_model_repository import (
    PostgresIPAddressReadModelRepository,
    PostgresIPRangeReadModelRepository,
)
from ipam.interface.schemas import (
    BulkCreateResponse,
    ChangeStatusRequest,
    CreateIPRangeRequest,
    IPRangeListResponse,
    IPRangeResponse,
    UpdateIPRangeRequest,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/ip-ranges", tags=["ip-ranges"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
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
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
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
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPRangeResponse:
    range_id = await command_bus.dispatch(CreateIPRangeCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.get("", response_model=IPRangeListResponse)
async def list_ip_ranges(
    params: OffsetParams = Depends(),  # noqa: B008
    vrf_id: UUID | None = None,
    status_filter: str | None = None,
    tenant_id: UUID | None = None,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPRangeListResponse:
    items, total = await query_bus.dispatch(
        ListIPRangesQuery(
            offset=params.offset,
            limit=params.limit,
            vrf_id=vrf_id,
            status=status_filter,
            tenant_id=tenant_id,
        )
    )
    return IPRangeListResponse(
        items=[IPRangeResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{range_id}", response_model=IPRangeResponse)
async def get_ip_range(
    range_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPRangeResponse:
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.patch("/{range_id}", response_model=IPRangeResponse)
async def update_ip_range(
    range_id: UUID,
    body: UpdateIPRangeRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPRangeResponse:
    await command_bus.dispatch(UpdateIPRangeCommand(range_id=range_id, **body.model_dump(exclude_unset=True)))
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.post("/{range_id}/status", response_model=IPRangeResponse)
async def change_ip_range_status(
    range_id: UUID,
    body: ChangeStatusRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> IPRangeResponse:
    await command_bus.dispatch(ChangeIPRangeStatusCommand(range_id=range_id, status=body.status))
    result = await query_bus.dispatch(GetIPRangeQuery(range_id=range_id))
    return IPRangeResponse(**result.model_dump())


@router.delete("/{range_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ip_range(
    range_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteIPRangeCommand(range_id=range_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_ip_ranges(
    body: list[CreateIPRangeRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(
        BulkCreateIPRangesCommand(items=[CreateIPRangeCommand(**i.model_dump()) for i in body])
    )
    return BulkCreateResponse(ids=ids, count=len(ids))


@router.get("/{range_id}/utilization")
async def get_ip_range_utilization(
    range_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> dict:
    utilization = await query_bus.dispatch(GetIPRangeUtilizationQuery(range_id=range_id))
    return {"range_id": range_id, "utilization": utilization}
