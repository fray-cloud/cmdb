from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from shared.cqrs.bus import CommandBus, QueryBus

from tenant.application.command_handlers import CreateTenantHandler
from tenant.application.commands import CreateTenantCommand
from tenant.application.queries import GetTenantQuery, ListTenantsQuery
from tenant.application.query_handlers import GetTenantHandler, ListTenantsHandler
from tenant.infrastructure.tenant_repository import PostgresTenantRepository
from tenant.interface.schemas import CreateTenantRequest, TenantResponse

setup_router = APIRouter(prefix="/setup", tags=["setup"])


class SetupStatusResponse(BaseModel):
    initialized: bool


@setup_router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(request: Request) -> SetupStatusResponse:
    session = request.app.state.database.session()
    repo = PostgresTenantRepository(session)
    bus = QueryBus()
    bus.register(ListTenantsQuery, ListTenantsHandler(repo))
    items, total = await bus.dispatch(ListTenantsQuery(offset=0, limit=1))
    return SetupStatusResponse(initialized=total > 0)


@setup_router.post("/create-tenant", response_model=TenantResponse)
async def setup_create_tenant(
    body: CreateTenantRequest,
    request: Request,
) -> TenantResponse:
    # Only allow if not yet initialized
    session = request.app.state.database.session()
    repo = PostgresTenantRepository(session)

    query_bus = QueryBus()
    query_bus.register(ListTenantsQuery, ListTenantsHandler(repo))
    query_bus.register(GetTenantQuery, GetTenantHandler(repo))

    _, total = await query_bus.dispatch(ListTenantsQuery(offset=0, limit=1))
    if total > 0:
        raise HTTPException(status_code=403, detail="System already initialized")

    command_bus = CommandBus()
    command_bus.register(
        CreateTenantCommand,
        CreateTenantHandler(repo, request.app.state.provisioner, request.app.state.event_producer),
    )
    tenant_id = await command_bus.dispatch(CreateTenantCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetTenantQuery(tenant_id=tenant_id))
    return TenantResponse(**result.model_dump())
