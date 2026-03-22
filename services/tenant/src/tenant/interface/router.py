from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.application.command_handlers import (
    CreateTenantHandler,
    DeleteTenantHandler,
    SuspendTenantHandler,
    UpdateTenantSettingsHandler,
)
from tenant.application.commands import (
    CreateTenantCommand,
    DeleteTenantCommand,
    SuspendTenantCommand,
    UpdateTenantSettingsCommand,
)
from tenant.application.queries import GetTenantQuery, ListTenantsQuery
from tenant.application.query_handlers import GetTenantHandler, ListTenantsHandler
from tenant.infrastructure.tenant_repository import PostgresTenantRepository
from tenant.interface.schemas import (
    CreateTenantRequest,
    TenantListResponse,
    TenantResponse,
    UpdateTenantSettingsRequest,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _get_session(request: Request) -> AsyncSession:
    return request.app.state.database.session()


def _get_command_bus(request: Request) -> CommandBus:
    session = _get_session(request)
    repo = PostgresTenantRepository(session)

    bus = CommandBus()
    bus.register(
        CreateTenantCommand,
        CreateTenantHandler(
            repo,
            request.app.state.provisioner,
            request.app.state.event_producer,
        ),
    )
    bus.register(
        SuspendTenantCommand,
        SuspendTenantHandler(repo, request.app.state.event_producer),
    )
    bus.register(
        UpdateTenantSettingsCommand,
        UpdateTenantSettingsHandler(repo),
    )
    bus.register(
        DeleteTenantCommand,
        DeleteTenantHandler(repo, request.app.state.event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = _get_session(request)
    repo = PostgresTenantRepository(session)

    bus = QueryBus()
    bus.register(GetTenantQuery, GetTenantHandler(repo))
    bus.register(ListTenantsQuery, ListTenantsHandler(repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TenantResponse,
)
async def create_tenant(
    body: CreateTenantRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> TenantResponse:
    tenant_id = await command_bus.dispatch(CreateTenantCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetTenantQuery(tenant_id=tenant_id))
    return TenantResponse(**result.model_dump())


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> TenantListResponse:
    items, total = await query_bus.dispatch(ListTenantsQuery(offset=params.offset, limit=params.limit))
    return TenantListResponse(
        items=[TenantResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> TenantResponse:
    result = await query_bus.dispatch(GetTenantQuery(tenant_id=tenant_id))
    return TenantResponse(**result.model_dump())


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant_settings(
    tenant_id: UUID,
    body: UpdateTenantSettingsRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> TenantResponse:
    await command_bus.dispatch(UpdateTenantSettingsCommand(tenant_id=tenant_id, **body.model_dump()))
    result = await query_bus.dispatch(GetTenantQuery(tenant_id=tenant_id))
    return TenantResponse(**result.model_dump())


@router.post(
    "/{tenant_id}/suspend",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def suspend_tenant(
    tenant_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(SuspendTenantCommand(tenant_id=tenant_id))


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tenant(
    tenant_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteTenantCommand(tenant_id=tenant_id))
