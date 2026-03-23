"""User REST API endpoints for CRUD and role assignment."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus
from sqlalchemy.ext.asyncio import AsyncSession

from auth.role import RoleRepository
from auth.role.infra import PostgresRoleRepository
from auth.shared.dependencies import get_current_user
from auth.user.command import (
    AssignRoleCommand,
    AssignRoleHandler,
    ChangePasswordCommand,
    ChangePasswordHandler,
    RegisterUserCommand,
    RegisterUserHandler,
    RemoveRoleCommand,
    RemoveRoleHandler,
)
from auth.user.domain import UserRepository
from auth.user.infra import PostgresUserRepository
from auth.user.query import GetUserHandler, GetUserQuery, ListUsersHandler, ListUsersQuery
from auth.user.router.schemas import AssignRoleRequest, UserListResponse, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def _get_session(request: Request) -> AsyncSession:
    return request.app.state.database.session()


def _get_user_repo(request: Request) -> UserRepository:
    return PostgresUserRepository(_get_session(request))


def _get_role_repo(request: Request) -> RoleRepository:
    return PostgresRoleRepository(_get_session(request))


def _get_command_bus(request: Request) -> CommandBus:
    user_repo = _get_user_repo(request)
    role_repo = _get_role_repo(request)

    bus = CommandBus()
    bus.register(
        RegisterUserCommand,
        RegisterUserHandler(
            user_repo,
            request.app.state.password_service,
            request.app.state.event_producer,
        ),
    )
    bus.register(
        ChangePasswordCommand,
        ChangePasswordHandler(
            user_repo,
            request.app.state.password_service,
        ),
    )
    bus.register(
        AssignRoleCommand,
        AssignRoleHandler(
            user_repo,
            role_repo,
            request.app.state.event_producer,
        ),
    )
    bus.register(
        RemoveRoleCommand,
        RemoveRoleHandler(
            user_repo,
            request.app.state.event_producer,
        ),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    user_repo = _get_user_repo(request)

    bus = QueryBus()
    bus.register(GetUserQuery, GetUserHandler(user_repo))
    bus.register(ListUsersQuery, ListUsersHandler(user_repo))
    return bus


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: dict = Depends(get_current_user),  # noqa: B008
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> UserListResponse:
    """List users for the current tenant with pagination."""
    items, total = await query_bus.dispatch(
        ListUsersQuery(
            tenant_id=current_user["tenant_id"],
            offset=params.offset,
            limit=params.limit,
        )
    )
    return UserListResponse(
        items=[UserResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> UserResponse:
    """Retrieve a single user by ID."""
    result = await query_bus.dispatch(GetUserQuery(user_id=user_id))
    return UserResponse(**result.model_dump())


@router.post(
    "/{user_id}/roles",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def assign_role(
    user_id: UUID,
    body: AssignRoleRequest,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    """Assign a role to a user."""
    await command_bus.dispatch(AssignRoleCommand(user_id=user_id, role_id=body.role_id))


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    """Remove a role from a user."""
    await command_bus.dispatch(RemoveRoleCommand(user_id=user_id, role_id=role_id))
