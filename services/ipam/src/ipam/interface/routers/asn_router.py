import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.application.command_handlers import (
    BulkCreateASNsHandler,
    BulkDeleteASNsHandler,
    BulkUpdateASNsHandler,
    CreateASNHandler,
    DeleteASNHandler,
    UpdateASNHandler,
)
from ipam.application.commands import (
    BulkCreateASNsCommand,
    BulkDeleteASNsCommand,
    BulkUpdateASNItem,
    BulkUpdateASNsCommand,
    CreateASNCommand,
    DeleteASNCommand,
    UpdateASNCommand,
)
from ipam.application.queries import GetASNQuery, ListASNsQuery
from ipam.application.query_handlers import GetASNHandler, ListASNsHandler
from ipam.infrastructure.read_model_repository import PostgresASNReadModelRepository
from ipam.interface.schemas import (
    ASNListResponse,
    ASNResponse,
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    CreateASNRequest,
    UpdateASNRequest,
)
from ipam.interface.schemas import (
    BulkUpdateASNItem as BulkUpdateASNItemSchema,
)

router = APIRouter(prefix="/asns", tags=["asns"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresASNReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(CreateASNCommand, CreateASNHandler(event_store, read_model_repo, event_producer))
    bus.register(UpdateASNCommand, UpdateASNHandler(event_store, read_model_repo, event_producer))
    bus.register(DeleteASNCommand, DeleteASNHandler(event_store, read_model_repo, event_producer))
    bus.register(
        BulkCreateASNsCommand,
        BulkCreateASNsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateASNsCommand,
        BulkUpdateASNsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteASNsCommand,
        BulkDeleteASNsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresASNReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetASNQuery, GetASNHandler(read_model_repo))
    bus.register(ListASNsQuery, ListASNsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ASNResponse,
)
async def create_asn(
    body: CreateASNRequest,
    request: Request,
) -> ASNResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    asn_id = await command_bus.dispatch(CreateASNCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetASNQuery(asn_id=asn_id))
    return ASNResponse(**result.model_dump())


@router.get("", response_model=ASNListResponse)
async def list_asns(
    params: OffsetParams = Depends(),  # noqa: B008
    rir_id: UUID | None = None,
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
) -> ASNListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListASNsQuery(
            offset=params.offset,
            limit=params.limit,
            rir_id=rir_id,
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
    return ASNListResponse(
        items=[ASNResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_asns(
    body: list[BulkUpdateASNItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateASNsCommand(
            items=[BulkUpdateASNItem(asn_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_asns(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteASNsCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{asn_id}", response_model=ASNResponse)
async def get_asn(
    asn_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> ASNResponse:
    result = await query_bus.dispatch(GetASNQuery(asn_id=asn_id))
    return ASNResponse(**result.model_dump())


@router.patch("/{asn_id}", response_model=ASNResponse)
async def update_asn(
    asn_id: UUID,
    body: UpdateASNRequest,
    request: Request,
) -> ASNResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(UpdateASNCommand(asn_id=asn_id, **body.model_dump(exclude_unset=True)))
    await session.commit()
    result = await query_bus.dispatch(GetASNQuery(asn_id=asn_id))
    return ASNResponse(**result.model_dump())


@router.delete("/{asn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asn(
    asn_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteASNCommand(asn_id=asn_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_asns(
    body: list[CreateASNRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(BulkCreateASNsCommand(items=[CreateASNCommand(**i.model_dump()) for i in body]))
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
