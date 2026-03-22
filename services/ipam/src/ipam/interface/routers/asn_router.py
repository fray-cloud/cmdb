import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam

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
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/asns", tags=["asns"])


def _get_command_bus(request: Request) -> CommandBus:
    session = request.app.state.database.session()
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


def _get_query_bus(request: Request) -> QueryBus:
    session = request.app.state.database.session()
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
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> ASNResponse:
    asn_id = await command_bus.dispatch(CreateASNCommand(**body.model_dump()))
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
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkUpdateResponse:
    updated = await command_bus.dispatch(
        BulkUpdateASNsCommand(
            items=[BulkUpdateASNItem(asn_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body]
        )
    )
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_asns(
    body: BulkDeleteRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkDeleteResponse:
    deleted = await command_bus.dispatch(BulkDeleteASNsCommand(ids=body.ids))
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
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> ASNResponse:
    await command_bus.dispatch(UpdateASNCommand(asn_id=asn_id, **body.model_dump(exclude_unset=True)))
    result = await query_bus.dispatch(GetASNQuery(asn_id=asn_id))
    return ASNResponse(**result.model_dump())


@router.delete("/{asn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asn(
    asn_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteASNCommand(asn_id=asn_id))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_asns(
    body: list[CreateASNRequest],
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> BulkCreateResponse:
    ids = await command_bus.dispatch(BulkCreateASNsCommand(items=[CreateASNCommand(**i.model_dump()) for i in body]))
    return BulkCreateResponse(ids=ids, count=len(ids))
