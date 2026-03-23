"""Service REST API router — CRUD and bulk endpoints for network services."""

import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

from ipam.service_entity.command import (
    BulkCreateServicesCommand,
    BulkCreateServicesHandler,
    BulkDeleteServicesCommand,
    BulkDeleteServicesHandler,
    BulkUpdateServiceItem,
    BulkUpdateServicesCommand,
    BulkUpdateServicesHandler,
    CreateServiceCommand,
    CreateServiceHandler,
    DeleteServiceCommand,
    DeleteServiceHandler,
    UpdateServiceCommand,
    UpdateServiceHandler,
)
from ipam.service_entity.infra import PostgresServiceReadModelRepository
from ipam.service_entity.query import GetServiceHandler, GetServiceQuery, ListServicesHandler, ListServicesQuery
from ipam.service_entity.router.schemas import (
    BulkUpdateServiceItem as BulkUpdateServiceItemSchema,
)
from ipam.service_entity.router.schemas import (
    CreateServiceRequest,
    ServiceListResponse,
    ServiceResponse,
    UpdateServiceRequest,
)
from ipam.shared.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
)

router = APIRouter(prefix="/services", tags=["services"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresServiceReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(CreateServiceCommand, CreateServiceHandler(event_store, read_model_repo, event_producer))
    bus.register(UpdateServiceCommand, UpdateServiceHandler(event_store, read_model_repo, event_producer))
    bus.register(DeleteServiceCommand, DeleteServiceHandler(event_store, read_model_repo, event_producer))
    bus.register(
        BulkCreateServicesCommand,
        BulkCreateServicesHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateServicesCommand,
        BulkUpdateServicesHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteServicesCommand,
        BulkDeleteServicesHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresServiceReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetServiceQuery, GetServiceHandler(read_model_repo))
    bus.register(ListServicesQuery, ListServicesHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ServiceResponse,
)
async def create_service(
    body: CreateServiceRequest,
    request: Request,
) -> ServiceResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    service_id = await command_bus.dispatch(CreateServiceCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetServiceQuery(service_id=service_id))
    return ServiceResponse(**result.model_dump())


@router.get("", response_model=ServiceListResponse)
async def list_services(
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
) -> ServiceListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListServicesQuery(
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
    return ServiceListResponse(
        items=[ServiceResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_services(
    body: list[BulkUpdateServiceItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateServicesCommand(
            items=[
                BulkUpdateServiceItem(service_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True)) for i in body
            ]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_services(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteServicesCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> ServiceResponse:
    result = await query_bus.dispatch(GetServiceQuery(service_id=service_id))
    return ServiceResponse(**result.model_dump())


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    body: UpdateServiceRequest,
    request: Request,
) -> ServiceResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(UpdateServiceCommand(service_id=service_id, **body.model_dump(exclude_unset=True)))
    await session.commit()
    result = await query_bus.dispatch(GetServiceQuery(service_id=service_id))
    return ServiceResponse(**result.model_dump())


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteServiceCommand(service_id=service_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_services(
    body: list[CreateServiceRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(
        BulkCreateServicesCommand(items=[CreateServiceCommand(**i.model_dump()) for i in body])
    )
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
