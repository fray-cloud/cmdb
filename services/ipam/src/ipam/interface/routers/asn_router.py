from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ipam.application.command_handlers import (
    BulkCreateASNsHandler,
    CreateASNHandler,
    DeleteASNHandler,
    UpdateASNHandler,
)
from ipam.application.commands import (
    BulkCreateASNsCommand,
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
    CreateASNRequest,
    UpdateASNRequest,
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
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> ASNListResponse:
    items, total = await query_bus.dispatch(
        ListASNsQuery(
            offset=params.offset,
            limit=params.limit,
            rir_id=rir_id,
            tenant_id=tenant_id,
        )
    )
    return ASNListResponse(
        items=[ASNResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


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
