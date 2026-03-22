import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi import Query as QueryParam

from ipam.application.command_handlers import (
    BulkCreateFHRPGroupsHandler,
    BulkDeleteFHRPGroupsHandler,
    BulkUpdateFHRPGroupsHandler,
    CreateFHRPGroupHandler,
    DeleteFHRPGroupHandler,
    UpdateFHRPGroupHandler,
)
from ipam.application.commands import (
    BulkCreateFHRPGroupsCommand,
    BulkDeleteFHRPGroupsCommand,
    BulkUpdateFHRPGroupItem,
    BulkUpdateFHRPGroupsCommand,
    CreateFHRPGroupCommand,
    DeleteFHRPGroupCommand,
    UpdateFHRPGroupCommand,
)
from ipam.application.queries import GetFHRPGroupQuery, ListFHRPGroupsQuery
from ipam.application.query_handlers import GetFHRPGroupHandler, ListFHRPGroupsHandler
from ipam.infrastructure.read_model_repository import PostgresFHRPGroupReadModelRepository
from ipam.interface.schemas import (
    BulkCreateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUpdateResponse,
    CreateFHRPGroupRequest,
    FHRPGroupListResponse,
    FHRPGroupResponse,
    UpdateFHRPGroupRequest,
)
from ipam.interface.schemas import (
    BulkUpdateFHRPGroupItem as BulkUpdateFHRPGroupItemSchema,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(prefix="/fhrp-groups", tags=["fhrp-groups"])


def _get_session(request: Request):
    return request.app.state.database.session()


def _get_command_bus(request: Request, session=None) -> CommandBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresFHRPGroupReadModelRepository(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(
        CreateFHRPGroupCommand,
        CreateFHRPGroupHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        UpdateFHRPGroupCommand,
        UpdateFHRPGroupHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        DeleteFHRPGroupCommand,
        DeleteFHRPGroupHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkCreateFHRPGroupsCommand,
        BulkCreateFHRPGroupsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkUpdateFHRPGroupsCommand,
        BulkUpdateFHRPGroupsHandler(event_store, read_model_repo, event_producer),
    )
    bus.register(
        BulkDeleteFHRPGroupsCommand,
        BulkDeleteFHRPGroupsHandler(event_store, read_model_repo, event_producer),
    )
    return bus


def _get_query_bus(request: Request, session=None) -> QueryBus:
    if session is None:
        session = _get_session(request)
    read_model_repo = PostgresFHRPGroupReadModelRepository(session)

    bus = QueryBus()
    bus.register(GetFHRPGroupQuery, GetFHRPGroupHandler(read_model_repo))
    bus.register(ListFHRPGroupsQuery, ListFHRPGroupsHandler(read_model_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=FHRPGroupResponse,
)
async def create_fhrp_group(
    body: CreateFHRPGroupRequest,
    request: Request,
) -> FHRPGroupResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    group_id = await command_bus.dispatch(CreateFHRPGroupCommand(**body.model_dump()))
    await session.commit()
    result = await query_bus.dispatch(GetFHRPGroupQuery(fhrp_group_id=group_id))
    return FHRPGroupResponse(**result.model_dump())


@router.get("", response_model=FHRPGroupListResponse)
async def list_fhrp_groups(
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
) -> FHRPGroupListResponse:
    custom_field_filters = json.loads(custom_fields) if custom_fields else None
    items, total = await query_bus.dispatch(
        ListFHRPGroupsQuery(
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
    return FHRPGroupListResponse(
        items=[FHRPGroupResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.patch("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_fhrp_groups(
    body: list[BulkUpdateFHRPGroupItemSchema],
    request: Request,
) -> BulkUpdateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    updated = await command_bus.dispatch(
        BulkUpdateFHRPGroupsCommand(
            items=[
                BulkUpdateFHRPGroupItem(fhrp_group_id=i.id, **i.model_dump(exclude={"id"}, exclude_unset=True))
                for i in body
            ]
        )
    )
    await session.commit()
    return BulkUpdateResponse(updated=updated)


@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_fhrp_groups(
    body: BulkDeleteRequest,
    request: Request,
) -> BulkDeleteResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    deleted = await command_bus.dispatch(BulkDeleteFHRPGroupsCommand(ids=body.ids))
    await session.commit()
    return BulkDeleteResponse(deleted=deleted)


@router.get("/{fhrp_group_id}", response_model=FHRPGroupResponse)
async def get_fhrp_group(
    fhrp_group_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> FHRPGroupResponse:
    result = await query_bus.dispatch(GetFHRPGroupQuery(fhrp_group_id=fhrp_group_id))
    return FHRPGroupResponse(**result.model_dump())


@router.patch("/{fhrp_group_id}", response_model=FHRPGroupResponse)
async def update_fhrp_group(
    fhrp_group_id: UUID,
    body: UpdateFHRPGroupRequest,
    request: Request,
) -> FHRPGroupResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    query_bus = _get_query_bus(request, session)
    await command_bus.dispatch(
        UpdateFHRPGroupCommand(
            fhrp_group_id=fhrp_group_id,
            **body.model_dump(exclude_unset=True),
        )
    )
    await session.commit()
    result = await query_bus.dispatch(GetFHRPGroupQuery(fhrp_group_id=fhrp_group_id))
    return FHRPGroupResponse(**result.model_dump())


@router.delete("/{fhrp_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fhrp_group(
    fhrp_group_id: UUID,
    request: Request,
) -> None:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    await command_bus.dispatch(DeleteFHRPGroupCommand(fhrp_group_id=fhrp_group_id))
    await session.commit()


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateResponse,
)
async def bulk_create_fhrp_groups(
    body: list[CreateFHRPGroupRequest],
    request: Request,
) -> BulkCreateResponse:
    session = _get_session(request)
    command_bus = _get_command_bus(request, session)
    ids = await command_bus.dispatch(
        BulkCreateFHRPGroupsCommand(items=[CreateFHRPGroupCommand(**i.model_dump()) for i in body])
    )
    await session.commit()
    return BulkCreateResponse(ids=ids, count=len(ids))
