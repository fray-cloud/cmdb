import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam

from ipam.application.command_handlers import (
    BulkCreateRIRsHandler,
    BulkDeleteRIRsHandler,
    BulkUpdateRIRsHandler,
    CreateRIRHandler,
    DeleteRIRHandler,
    UpdateRIRHandler,
)
from ipam.application.commands import (
    BulkCreateRIRsCommand,
    BulkDeleteRIRsCommand,
    BulkUpdateRIRItem,
    BulkUpdateRIRsCommand,
    CreateRIRCommand,
    DeleteRIRCommand,
    UpdateRIRCommand,
)
from ipam.application.queries import GetRIRQuery, ListRIRsQuery
from ipam.application.query_handlers import GetRIRHandler, ListRIRsHandler
from ipam.infrastructure.read_model_repository import PostgresRIRReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    CreateRIRRequest,
    RIRListResponse,
    RIRResponse,
    UpdateRIRRequest,
)
from ipam.interface.schemas import (
    BulkUpdateRIRItem as BulkUpdateRIRItemSchema,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/rirs", tags=["rirs"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresRIRReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(CreateRIRCommand, CreateRIRHandler(event_store, read_model_repo, event_producer))
    bus.register(UpdateRIRCommand, UpdateRIRHandler(event_store, read_model_repo, event_producer))
    bus.register(DeleteRIRCommand, DeleteRIRHandler(event_store, read_model_repo, event_producer))
    bus.register(
        BulkCreateRIRsCommand,
        BulkCreateRIRsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateRIRsCommand,
        BulkUpdateRIRsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteRIRsCommand,
        BulkDeleteRIRsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresRIRReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetRIRQuery, GetRIRHandler(read_model_repo))
    bus.register(ListRIRsQuery, ListRIRsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RIRResponse,
)
async def create_rir(
    body: CreateRIRRequest,
    request: Request,
) -> RIRResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    rir_id = await command_bus.dispatch(CreateRIRCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetRIRQuery(rir_id=rir_id))
    return RIRResponse(**result.model_dump())


@router.get("", response_model=RIRListResponse)
async def list_rirs(
    params: OffsetParams = Depends(),  # noqa: B008
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
) -> RIRListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListRIRsQuery(
            offset=params.offset,
            limit=params.limit,
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
    return RIRListResponse(
        items=[RIRResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_rirs(
    body: list[BulkUpdateRIRItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateRIRsCommand(
            items=[BulkUpdateRIRItem(rir_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_rirs(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteRIRsCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{rir_id}", response_model=RIRResponse)
async def get_rir(
    rir_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RIRResponse:
    result = await query_bus.dispatch(GetRIRQuery(rir_id=rir_id))
    return RIRResponse(**result.model_dump())


@router.patch("/{rir_id}", response_model=RIRResponse)
async def update_rir(
    rir_id: UUID,
    body: UpdateRIRRequest,
    request: Request,
) -> RIRResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(UpdateRIRCommand(rir_id=rir_id, **body.model_dump(exclude_unset=True)))
    await session.commit()
    result = await query_bus.dispatch(GetRIRQuery(rir_id=rir_id))
    return RIRResponse(**result.model_dump())


@router.delete("/{rir_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rir(
    rir_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteRIRCommand(rir_id=rir_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_rirs(
    body: list[CreateRIRRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(BulkCreateRIRsCommand(items=[CreateRIRCommand(**i.model_dump()) for i in body]))
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
