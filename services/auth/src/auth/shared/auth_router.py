"""Authentication router for register, login, refresh, logout, and token validation."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from shared.cqrs.bus import CommandBus, QueryBus
from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import AuthorizationError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.role import RoleRepository
from auth.role.infra import PostgresRoleRepository
from auth.shared.dependencies import get_current_user
from auth.shared.login_rate_limiter import LoginRateLimiter
from auth.shared.security import BcryptPasswordService, JWTService
from auth.shared.token_blacklist import RedisTokenBlacklist
from auth.user.command import RegisterUserCommand, RegisterUserHandler
from auth.user.domain import UserRepository
from auth.user.infra import PostgresUserRepository
from auth.user.query import GetUserHandler, GetUserQuery
from auth.user.router import RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Auth-specific DTOs ---


class AuthTokenDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Auth-specific Commands ---


class LoginCommand(Command):
    email: str
    password: str
    tenant_id: UUID
    client_ip: str = "0.0.0.0"


class RefreshTokenCommand(Command):
    refresh_token: str


class LogoutCommand(Command):
    refresh_token: str


# --- Auth-specific Schemas ---


class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: UUID


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Auth-specific Handlers ---


class LoginHandler(CommandHandler[AuthTokenDTO]):
    """Handles user login with rate limiting and credential verification."""

    def __init__(
        self,
        repository: UserRepository,
        role_repository: RoleRepository,
        password_service: BcryptPasswordService,
        jwt_service: JWTService,
        rate_limiter: LoginRateLimiter,
    ) -> None:
        self._repository = repository
        self._role_repository = role_repository
        self._password_service = password_service
        self._jwt_service = jwt_service
        self._rate_limiter = rate_limiter

    async def handle(self, command: Command) -> AuthTokenDTO:
        """Authenticate user credentials and return JWT token pair."""
        if await self._rate_limiter.is_locked(command.email, command.client_ip):
            raise AuthorizationError("Too many login attempts. Please try again later.")

        user = await self._repository.find_by_email(command.email, command.tenant_id)
        if user is None:
            await self._rate_limiter.record_failure(command.email, command.client_ip)
            raise AuthorizationError("Invalid email or password")

        if not await self._password_service.verify_async(command.password, user.password_hash):
            await self._rate_limiter.record_failure(command.email, command.client_ip)
            raise AuthorizationError("Invalid email or password")

        if user.status != "active":
            raise AuthorizationError(f"User account is {user.status}")

        await self._rate_limiter.reset(command.email, command.client_ip)

        roles = await self._role_repository.find_by_ids(user.role_ids)
        role_names = [r.name for r in roles]

        access_token = self._jwt_service.create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=role_names,
        )
        refresh_token = self._jwt_service.create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
        )

        return AuthTokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._jwt_service.access_expire_minutes * 60,
        )


class RefreshTokenHandler(CommandHandler[AuthTokenDTO]):
    """Handles access token refresh using a valid refresh token."""

    def __init__(
        self,
        repository: UserRepository,
        role_repository: RoleRepository,
        jwt_service: JWTService,
        token_blacklist: RedisTokenBlacklist,
    ) -> None:
        self._repository = repository
        self._role_repository = role_repository
        self._jwt_service = jwt_service
        self._token_blacklist = token_blacklist

    async def handle(self, command: Command) -> AuthTokenDTO:
        """Validate the refresh token and issue a new access token."""
        try:
            payload = self._jwt_service.decode_token(command.refresh_token)
        except Exception as exc:
            raise AuthorizationError("Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise AuthorizationError("Invalid token type")

        jti = payload.get("jti")
        if jti and await self._token_blacklist.is_blacklisted(jti):
            raise AuthorizationError("Token has been revoked")

        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])

        user = await self._repository.find_by_id(user_id)
        if user is None or user.status != "active":
            raise AuthorizationError("User not found or inactive")

        roles = await self._role_repository.find_by_ids(user.role_ids)
        role_names = [r.name for r in roles]

        access_token = self._jwt_service.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=role_names,
        )

        return AuthTokenDTO(
            access_token=access_token,
            refresh_token=command.refresh_token,
            expires_in=self._jwt_service.access_expire_minutes * 60,
        )


class LogoutHandler(CommandHandler[None]):
    """Handles logout by blacklisting the refresh token."""

    def __init__(
        self,
        jwt_service: JWTService,
        token_blacklist: RedisTokenBlacklist,
    ) -> None:
        self._jwt_service = jwt_service
        self._token_blacklist = token_blacklist

    async def handle(self, command: Command) -> None:
        """Blacklist the refresh token's JTI for its remaining lifetime."""
        try:
            payload = self._jwt_service.decode_token(command.refresh_token)
        except Exception:
            return  # Already invalid, nothing to do

        jti = payload.get("jti")
        if jti:
            import time

            exp = payload.get("exp", 0)
            remaining = max(int(exp - time.time()), 0)
            if remaining > 0:
                await self._token_blacklist.blacklist(jti, remaining)


# --- Bus Helpers ---


def _get_session(request: Request) -> AsyncSession:
    return request.app.state.database.session()


def _get_command_bus(request: Request) -> CommandBus:
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
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = _get_session(request)
    user_repo = PostgresUserRepository(session)

    bus = QueryBus()
    bus.register(GetUserQuery, GetUserHandler(user_repo))
    return bus


# --- Endpoints ---


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def register(
    body: RegisterRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> UserResponse:
    """Register a new user account."""
    user_id = await command_bus.dispatch(RegisterUserCommand(**body.model_dump()))
    result = await query_bus.dispatch(GetUserQuery(user_id=user_id))
    return UserResponse(**result.model_dump())


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> AuthTokenResponse:
    """Authenticate a user and return access/refresh tokens."""
    client_ip = request.client.host if request.client else "0.0.0.0"
    result = await command_bus.dispatch(LoginCommand(**body.model_dump(), client_ip=client_ip))
    return AuthTokenResponse(**result.model_dump())


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> AuthTokenResponse:
    """Refresh an access token using a valid refresh token."""
    result = await command_bus.dispatch(RefreshTokenCommand(refresh_token=body.refresh_token))
    return AuthTokenResponse(**result.model_dump())


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshTokenRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    _current_user: dict = Depends(get_current_user),  # noqa: B008
) -> None:
    """Log out by blacklisting the refresh token."""
    await command_bus.dispatch(LogoutCommand(refresh_token=body.refresh_token))


@router.get("/validate", status_code=status.HTTP_200_OK, include_in_schema=False)
async def validate(
    current_user: dict = Depends(get_current_user),  # noqa: B008
) -> None:
    """Validate the current access token and return user info in headers."""
    from fastapi.responses import Response

    response = Response(status_code=200)
    response.headers["X-User-ID"] = str(current_user["user_id"])
    response.headers["X-Tenant-ID"] = str(current_user["tenant_id"])
    return response
