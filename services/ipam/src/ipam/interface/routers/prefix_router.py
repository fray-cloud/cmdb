from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ipam.application.command_handlers import (
    BulkCreatePrefixesHandler,
    ChangePrefixStatusHandler,
    CreatePrefixHandler,
    DeletePrefixHandler,
    UpdatePrefixHandler,
)
from ipam.application.commands import (
    BulkCreatePrefixesCommand,
    ChangePrefixStatusCommand,
    CreatePrefixCommand,
    DeletePrefixCommand,
    UpdatePrefixCommand,
)
from ipam.application.queries import (
    GetAvailableIPsQuery,
    GetAvailablePrefixesQuery,
    GetPrefixChildrenQuery,
    GetPrefixQuery,
    GetPrefixUtilizationQuery,
    ListPrefixesQuery,
)
from ipam.application.query_handlers import (
    GetAvailableIPsHandler,
    GetAvailablePrefixesHandler,
    GetPrefixChildrenHandler,
    GetPrefixHandler,
    GetPrefixUtilizationHandler,
    ListPrefixesHandler,
)
from ipam.infrastructure.read_model_repository import (
    PostgresIPAddressReadModelRepository,
    PostgresPrefixReadModelRepository,
)
from ipam.interface.schemas import (
    BulkCreateResponse,
    ChangeStatusRequest,
    CreatePrefixRequest,
    PrefixListResponse,
    PrefixResponse,
    UpdatePrefixRequest,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/prefixes", tags=["prefixes"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
    read_model_repo = PostgresPrefixReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(CreatePrefixCommand, CreatePrefixHandler(event_store, read_model_repo, event_producer))
    bus.register(UpdatePrefixCommand, UpdatePrefixHandler(event_store, read_model_repo, event_producer))
    bus.register(
        ChangePrefixStatusCommand,
        ChangePrefixStatusHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(DeletePrefixCommand, DeletePrefixHandler(event_store, read_model_repo, event_producer))
    bus.register(
        BulkCreatePrefixesCommand,
        BulkCreatePrefixesHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
    prefix_repo = PostgresPrefixReadModelRepository(session)
    ip_repo = PostgresIPAddressReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetPrefixQuery, GetPrefixHandler(prefix_repo))
    bus.register(ListPrefixesQuery, ListPrefixesHandler(prefix_repo))
    bus.register(GetPrefixChildrenQuery, GetPrefixChildrenHandler(prefix_repo))
    bus.register(GetPrefixUtilizationQuery, GetPrefixUtilizationHandler(prefix_repo, ip_repo))
    bus.register(GetAvailablePrefixesQuery, GetAvailablePrefixesHandler(prefix_repo))
    bus.register(GetAvailableIPsQuery, GetAvailableIPsHandler(prefix_repo, ip_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PrefixResponse,
)
async def create_prefix(
    body: CreatePrefixRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PrefixResponse:
    prefix_id = await command_bus.dispatch(CreatePrefixCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.get("", response_model=PrefixListResponse)
async def list_prefixes(
    params: OffsetParams = Depends(),  # noqa: B008
    vrf_id: UUID | None = None,
    status_filter: str | None = None,
    tenant_id: UUID | None = None,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PrefixListResponse:
    items, total = await query_bus.dispatch(
        ListPrefixesQuery(
            offset=params.offset,
            limit=params.limit,
            vrf_id=vrf_id,
            status=status_filter,
            tenant_id=tenant_id,
        )
    )
    return PrefixListResponse(
        items=[PrefixResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{prefix_id}", response_model=PrefixResponse)
async def get_prefix(
    prefix_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PrefixResponse:
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.patch("/{prefix_id}", response_model=PrefixResponse)
async def update_prefix(
    prefix_id: UUID,
    body: UpdatePrefixRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PrefixResponse:
    await command_bus.dispatch(UpdatePrefixCommand(prefix_id=prefix_id, **body.model_dump(exclude_unset=True)))
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.post("/{prefix_id}/status", response_model=PrefixResponse)
async def change_prefix_status(
    prefix_id: UUID,
    body: ChangeStatusRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PrefixResponse:
    await command_bus.dispatch(ChangePrefixStatusCommand(prefix_id=prefix_id, status=body.status))
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.delete("/{prefix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prefix(
    prefix_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeletePrefixCommand(prefix_id=prefix_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_prefixes(
    body: list[CreatePrefixRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(
        BulkCreatePrefixesCommand(items=[CreatePrefixCommand(**i.model_dump()) for i in body])
    )
    return BulkCreateResponse(ids=ids, count=len(ids))


@router.get("/{prefix_id}/children", response_model=list[PrefixResponse])
async def get_prefix_children(
    prefix_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> list[PrefixResponse]:
    children = await query_bus.dispatch(GetPrefixChildrenQuery(prefix_id=prefix_id))
    return [PrefixResponse(**c.model_dump()) for c in children]


@router.get("/{prefix_id}/utilization")
async def get_prefix_utilization(
    prefix_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> dict:
    utilization = await query_bus.dispatch(GetPrefixUtilizationQuery(prefix_id=prefix_id))
    return {"prefix_id": prefix_id, "utilization": utilization}


@router.get("/{prefix_id}/available-prefixes")
async def get_available_prefixes(
    prefix_id: UUID,
    desired_prefix_length: int = 24,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> dict:
    available = await query_bus.dispatch(
        GetAvailablePrefixesQuery(prefix_id=prefix_id, desired_prefix_length=desired_prefix_length)
    )
    return {"prefix_id": prefix_id, "available_prefixes": available}


@router.get("/{prefix_id}/available-ips")
async def get_available_ips(
    prefix_id: UUID,
    count: int = 1,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> dict:
    available = await query_bus.dispatch(GetAvailableIPsQuery(prefix_id=prefix_id, count=count))
    return {"prefix_id": prefix_id, "available_ips": available}
