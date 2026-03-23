from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus
from sqlalchemy.ext.asyncio import AsyncSession

from auth.group.infra.repository import PostgresGroupRepository
from auth.role.command.commands import CreateRoleCommand, DeleteRoleCommand, UpdateRoleCommand
from auth.role.command.handlers import CreateRoleHandler, DeleteRoleHandler, UpdateRoleHandler
from auth.role.infra.repository import PostgresRoleRepository
from auth.role.query.handlers import CheckPermissionHandler, GetRoleHandler, ListRolesHandler
from auth.role.query.queries import CheckPermissionQuery, GetRoleQuery, ListRolesQuery
from auth.role.router.schemas import (
    CreateRoleRequest,
    PermissionCheckResponse,
    RoleListResponse,
    RoleResponse,
    UpdateRoleRequest,
)
from auth.shared.dependencies import get_current_user
from auth.user.infra.repository import PostgresUserRepository

router = APIRouter(prefix="/roles", tags=["roles"])
permission_router = APIRouter(prefix="/permissions", tags=["permissions"])


def _get_session(request: Request) -> AsyncSession:
    return request.app.state.database.session()


def _get_command_bus(request: Request) -> CommandBus:
    session = _get_session(request)
    role_repo = PostgresRoleRepository(session)

    bus = CommandBus()
    bus.register(CreateRoleCommand, CreateRoleHandler(role_repo))
    bus.register(UpdateRoleCommand, UpdateRoleHandler(role_repo))
    bus.register(DeleteRoleCommand, DeleteRoleHandler(role_repo))
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = _get_session(request)
    user_repo = PostgresUserRepository(session)
    role_repo = PostgresRoleRepository(session)
    group_repo = PostgresGroupRepository(session)

    bus = QueryBus()
    bus.register(GetRoleQuery, GetRoleHandler(role_repo))
    bus.register(ListRolesQuery, ListRolesHandler(role_repo))
    bus.register(
        CheckPermissionQuery,
        CheckPermissionHandler(user_repo, role_repo, group_repo),
    )
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RoleResponse,
)
async def create_role(
    body: CreateRoleRequest,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RoleResponse:
    role_id = await command_bus.dispatch(
        CreateRoleCommand(
            name=body.name,
            tenant_id=body.tenant_id,
            description=body.description,
            permissions=[p.model_dump() for p in body.permissions] if body.permissions else None,
        )
    )
    result = await query_bus.dispatch(GetRoleQuery(role_id=role_id))
    return RoleResponse(**result.model_dump())


@router.get("", response_model=RoleListResponse)
async def list_roles(
    current_user: dict = Depends(get_current_user),  # noqa: B008
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RoleListResponse:
    items, total = await query_bus.dispatch(
        ListRolesQuery(
            tenant_id=current_user["tenant_id"],
            offset=params.offset,
            limit=params.limit,
        )
    )
    return RoleListResponse(
        items=[RoleResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RoleResponse:
    result = await query_bus.dispatch(GetRoleQuery(role_id=role_id))
    return RoleResponse(**result.model_dump())


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    body: UpdateRoleRequest,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RoleResponse:
    await command_bus.dispatch(
        UpdateRoleCommand(
            role_id=role_id,
            name=body.name,
            description=body.description,
            permissions=[p.model_dump() for p in body.permissions] if body.permissions else None,
        )
    )
    result = await query_bus.dispatch(GetRoleQuery(role_id=role_id))
    return RoleResponse(**result.model_dump())


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
    role_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteRoleCommand(role_id=role_id))


@permission_router.get("/check", response_model=PermissionCheckResponse)
async def check_permission(
    user_id: UUID,
    object_type: str,
    action: str,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PermissionCheckResponse:
    result = await query_bus.dispatch(CheckPermissionQuery(user_id=user_id, object_type=object_type, action=action))
    return PermissionCheckResponse(**result.model_dump())
