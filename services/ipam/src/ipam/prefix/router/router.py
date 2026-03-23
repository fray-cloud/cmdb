import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.ip_address.infra.repository import PostgresIPAddressReadModelRepository
from ipam.prefix.command.commands import (
    BulkCreatePrefixesCommand,
    BulkDeletePrefixesCommand,
    BulkUpdatePrefixesCommand,
    BulkUpdatePrefixItem,
    ChangePrefixStatusCommand,
    CreatePrefixCommand,
    DeletePrefixCommand,
    UpdatePrefixCommand,
)
from ipam.prefix.command.handlers import (
    BulkCreatePrefixesHandler,
    BulkDeletePrefixesHandler,
    BulkUpdatePrefixesHandler,
    ChangePrefixStatusHandler,
    CreatePrefixHandler,
    DeletePrefixHandler,
    UpdatePrefixHandler,
)
from ipam.prefix.infra.repository import PostgresPrefixReadModelRepository
from ipam.prefix.query.handlers import (
    GetAvailableIPsHandler,
    GetAvailablePrefixesHandler,
    GetPrefixChildrenHandler,
    GetPrefixHandler,
    GetPrefixUtilizationHandler,
    ListPrefixesHandler,
)
from ipam.prefix.query.queries import (
    GetAvailableIPsQuery,
    GetAvailablePrefixesQuery,
    GetPrefixChildrenQuery,
    GetPrefixQuery,
    GetPrefixUtilizationQuery,
    ListPrefixesQuery,
)
from ipam.prefix.router.schemas import (
    BulkUpdatePrefixItem as BulkUpdatePrefixSchema,
)
from ipam.prefix.router.schemas import (
    CreatePrefixRequest,
    PrefixListResponse,
    PrefixResponse,
    UpdatePrefixRequest,
)
from ipam.shared.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    ChangeStatusRequest,
)

router = APIRouter(prefix="/prefixes", tags=["prefixes"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
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
    bus.register(
        BulkUpdatePrefixesCommand,
        BulkUpdatePrefixesHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeletePrefixesCommand,
        BulkDeletePrefixesHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
    prefix_repo = PostgresPrefixReadModelRepository(session)
    ip_repo = PostgresIPAddressReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetPrefixQuery, GetPrefixHandler(prefix_repo))
    bus.register(ListPrefixesQuery, ListPrefixesHandler(prefix_repo))
    bus.register(GetPrefixChildrenQuery, GetPrefixChildrenHandler(prefix_repo))
    cache = getattr(request.app.state, "cache", None)
    bus.register(GetPrefixUtilizationQuery, GetPrefixUtilizationHandler(prefix_repo, ip_repo, cache=cache))
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
    request: Request,
) -> PrefixResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    prefix_id = await command_bus.dispatch(CreatePrefixCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.get("/{prefix_id}", response_model=PrefixResponse)
async def get_prefix(
    prefix_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PrefixResponse:
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.get("", response_model=PrefixListResponse)
async def list_prefixes(
    params: OffsetParams = Depends(),  # noqa: B008
    vrf_id: UUID | None = None,
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
) -> PrefixListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListPrefixesQuery(
            offset=params.offset,
            limit=params.limit,
            vrf_id=vrf_id,
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
    return PrefixListResponse(
        items=[PrefixResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/{prefix_id}", response_model=PrefixResponse)
async def update_prefix(
    prefix_id: UUID,
    body: UpdatePrefixRequest,
    request: Request,
) -> PrefixResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(UpdatePrefixCommand(prefix_id=prefix_id, **body.model_dump(exclude_unset=True)))
    await session.commit()
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.post("/{prefix_id}/status", response_model=PrefixResponse)
async def change_prefix_status(
    prefix_id: UUID,
    body: ChangeStatusRequest,
    request: Request,
) -> PrefixResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(ChangePrefixStatusCommand(prefix_id=prefix_id, new_status=body.status))
    await session.commit()
    result = await query_bus.dispatch(GetPrefixQuery(prefix_id=prefix_id))
    return PrefixResponse(**result.model_dump())


@router.delete("/{prefix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prefix(
    prefix_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeletePrefixCommand(prefix_id=prefix_id))
    await session.commit()


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_prefixes(
    body: list[BulkUpdatePrefixSchema],
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdatePrefixesCommand(
            items=[
                BulkUpdatePrefixItem(prefix_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body
            ]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_prefixes(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeletePrefixesCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


@router.post("/bulk", response_model=BulkCreateResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_prefixes(
    body: list[CreatePrefixRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    commands = [CreatePrefixCommand(**b.model_dump()) for b in body]
    ids = await command_bus.dispatch(BulkCreatePrefixesCommand(items=commands))
    await session.commit()
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
    return {"utilization": utilization}


@router.get("/{prefix_id}/available-prefixes")
async def get_available_prefixes(
    prefix_id: UUID,
    desired_prefix_length: int = 24,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> dict:
    available = await query_bus.dispatch(
        GetAvailablePrefixesQuery(prefix_id=prefix_id, desired_prefix_length=desired_prefix_length)
    )
    return {"available_prefixes": available}


@router.get("/{prefix_id}/available-ips")
async def get_available_ips(
    prefix_id: UUID,
    count: int = 1,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> dict:
    available = await query_bus.dispatch(GetAvailableIPsQuery(prefix_id=prefix_id, count=count))
    return {"available_ips": available}
