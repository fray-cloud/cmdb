from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.application.command_handlers import (
    AssignRoleHandler,
    ChangePasswordHandler,
    CreateAPITokenHandler,
    CreateRoleHandler,
    DeleteRoleHandler,
    LoginHandler,
    LogoutHandler,
    RefreshTokenHandler,
    RegisterUserHandler,
    RemoveRoleHandler,
    RevokeAPITokenHandler,
    UpdateRoleHandler,
)
from auth.application.commands import (
    AssignRoleCommand,
    ChangePasswordCommand,
    CreateAPITokenCommand,
    CreateRoleCommand,
    DeleteRoleCommand,
    LoginCommand,
    LogoutCommand,
    RefreshTokenCommand,
    RegisterUserCommand,
    RemoveRoleCommand,
    RevokeAPITokenCommand,
    UpdateRoleCommand,
)
from auth.application.queries import (
    CheckPermissionQuery,
    GetRoleQuery,
    GetUserQuery,
    ListAPITokensQuery,
    ListRolesQuery,
    ListUsersQuery,
)
from auth.application.query_handlers import (
    CheckPermissionHandler,
    GetRoleHandler,
    GetUserHandler,
    ListAPITokensHandler,
    ListRolesHandler,
    ListUsersHandler,
)
from auth.infrastructure.api_token_repository import PostgresAPITokenRepository
from auth.infrastructure.group_repository import PostgresGroupRepository
from auth.infrastructure.role_repository import PostgresRoleRepository
from auth.infrastructure.user_repository import PostgresUserRepository
from auth.interface.dependencies import get_current_user
from auth.interface.schemas import (
    APITokenListResponse,
    APITokenResponse,
    AssignRoleRequest,
    AuthTokenResponse,
    CreateAPITokenRequest,
    CreateRoleRequest,
    LoginRequest,
    PermissionCheckResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RoleListResponse,
    RoleResponse,
    UpdateRoleRequest,
    UserListResponse,
    UserResponse,
)
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus

# --- Helpers ---


def _get_session(request: Request) -> AsyncSession:
    return request.app.state.database.session()


def _get_auth_command_bus(request: Request) -> CommandBus:
    session = _get_session(request)
    user_repo = PostgresUserRepository(session)
    role_repo = PostgresRoleRepository(session)

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
        LoginCommand,
        LoginHandler(
            user_repo,
            role_repo,
            request.app.state.password_service,
            request.app.state.jwt_service,
            request.app.state.rate_limiter,
        ),
    )
    bus.register(
        RefreshTokenCommand,
        RefreshTokenHandler(
            user_repo,
            role_repo,
            request.app.state.jwt_service,
            request.app.state.token_blacklist,
        ),
    )
    bus.register(
        LogoutCommand,
        LogoutHandler(
            request.app.state.jwt_service,
            request.app.state.token_blacklist,
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
    bus.register(CreateRoleCommand, CreateRoleHandler(role_repo))
    bus.register(UpdateRoleCommand, UpdateRoleHandler(role_repo))
    bus.register(DeleteRoleCommand, DeleteRoleHandler(role_repo))

    token_repo = PostgresAPITokenRepository(session)
    bus.register(
        CreateAPITokenCommand,
        CreateAPITokenHandler(token_repo, request.app.state.event_producer),
    )
    bus.register(
        RevokeAPITokenCommand,
        RevokeAPITokenHandler(token_repo, request.app.state.event_producer),
    )

    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = _get_session(request)
    user_repo = PostgresUserRepository(session)
    role_repo = PostgresRoleRepository(session)
    group_repo = PostgresGroupRepository(session)
    token_repo = PostgresAPITokenRepository(session)

    bus = QueryBus()
    bus.register(GetUserQuery, GetUserHandler(user_repo))
    bus.register(ListUsersQuery, ListUsersHandler(user_repo))
    bus.register(GetRoleQuery, GetRoleHandler(role_repo))
    bus.register(ListRolesQuery, ListRolesHandler(role_repo))
    bus.register(
        CheckPermissionQuery,
        CheckPermissionHandler(user_repo, role_repo, group_repo),
    )
    bus.register(ListAPITokensQuery, ListAPITokensHandler(token_repo))
    return bus


# =============================================================================
# Auth Router (public endpoints)
# =============================================================================

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def register(
    body: RegisterRequest,
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> UserResponse:
    user_id = await command_bus.dispatch(RegisterUserCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetUserQuery(user_id=user_id))
    return UserResponse(**result.model_dump())


@auth_router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
) -> AuthTokenResponse:
    client_ip = request.client.host if request.client else "0.0.0.0"
    result = await command_bus.dispatch(LoginCommand(**body.model_dump(), client_ip=client_ip))
    return AuthTokenResponse(**result.model_dump())


@auth_router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
) -> AuthTokenResponse:
    result = await command_bus.dispatch(RefreshTokenCommand(refresh_token=body.refresh_token))
    return AuthTokenResponse(**result.model_dump())


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshTokenRequest,
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
    _current_user: dict = Depends(get_current_user),  # noqa: B008
) -> None:
    await command_bus.dispatch(LogoutCommand(refresh_token=body.refresh_token))


# =============================================================================
# User Router (authenticated endpoints)
# =============================================================================

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("", response_model=UserListResponse)
async def list_users(
    current_user: dict = Depends(get_current_user),  # noqa: B008
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> UserListResponse:
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


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> UserResponse:
    result = await query_bus.dispatch(GetUserQuery(user_id=user_id))
    return UserResponse(**result.model_dump())


@user_router.post(
    "/{user_id}/roles",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def assign_role(
    user_id: UUID,
    body: AssignRoleRequest,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(AssignRoleCommand(user_id=user_id, role_id=body.role_id))


@user_router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(RemoveRoleCommand(user_id=user_id, role_id=role_id))


# =============================================================================
# Role Router (authenticated endpoints)
# =============================================================================

role_router = APIRouter(prefix="/roles", tags=["roles"])


@role_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RoleResponse,
)
async def create_role(
    body: CreateRoleRequest,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
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


@role_router.get("", response_model=RoleListResponse)
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


@role_router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> RoleResponse:
    result = await query_bus.dispatch(GetRoleQuery(role_id=role_id))
    return RoleResponse(**result.model_dump())


@role_router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    body: UpdateRoleRequest,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
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


@role_router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
    role_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteRoleCommand(role_id=role_id))


# =============================================================================
# API Token Router (authenticated endpoints)
# =============================================================================

api_token_router = APIRouter(prefix="/api-tokens", tags=["api-tokens"])


@api_token_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=APITokenResponse,
)
async def create_api_token(
    body: CreateAPITokenRequest,
    current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
) -> APITokenResponse:
    result = await command_bus.dispatch(
        CreateAPITokenCommand(
            user_id=current_user["user_id"],
            tenant_id=current_user["tenant_id"],
            description=body.description,
            scopes=body.scopes,
            expires_at=body.expires_at,
            allowed_ips=body.allowed_ips,
        )
    )
    return APITokenResponse(**result.model_dump())


@api_token_router.get("", response_model=APITokenListResponse)
async def list_api_tokens(
    current_user: dict = Depends(get_current_user),  # noqa: B008
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> APITokenListResponse:
    items, total = await query_bus.dispatch(
        ListAPITokensQuery(
            user_id=current_user["user_id"],
            offset=params.offset,
            limit=params.limit,
        )
    )
    return APITokenListResponse(
        items=[APITokenResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@api_token_router.delete(
    "/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_api_token(
    token_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_auth_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(RevokeAPITokenCommand(token_id=token_id))


# =============================================================================
# Permission Check Router (internal)
# =============================================================================

permission_router = APIRouter(prefix="/permissions", tags=["permissions"])


@permission_router.get("/check", response_model=PermissionCheckResponse)
async def check_permission(
    user_id: UUID,
    object_type: str,
    action: str,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> PermissionCheckResponse:
    result = await query_bus.dispatch(CheckPermissionQuery(user_id=user_id, object_type=object_type, action=action))
    return PermissionCheckResponse(**result.model_dump())
