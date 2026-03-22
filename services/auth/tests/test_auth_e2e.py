from uuid import uuid4

import pytest
from auth.application.command_handlers import (
    AssignRoleHandler,
    CreateRoleHandler,
    LoginHandler,
    RegisterUserHandler,
)
from auth.application.commands import (
    AssignRoleCommand,
    CreateRoleCommand,
    LoginCommand,
    RegisterUserCommand,
)
from auth.domain.services import PermissionChecker
from auth.infrastructure.security import BcryptPasswordService, JWTService
from shared.domain.exceptions import AuthorizationError, ConflictError

from tests.conftest import (
    FakeKafkaProducer,
    FakeLoginRateLimiter,
    InMemoryRoleRepository,
    InMemoryUserRepository,
)

TENANT_ID = uuid4()


class TestUserRegistration:
    async def test_register_user_stores_email_and_display_name(
        self,
        user_repository: InMemoryUserRepository,
        password_service: BcryptPasswordService,
        event_producer: FakeKafkaProducer,
    ) -> None:
        handler = RegisterUserHandler(user_repository, password_service, event_producer)
        command = RegisterUserCommand(
            email="alice@example.com",
            password="StrongP@ss1",
            tenant_id=TENANT_ID,
            display_name="Alice",
        )

        user_id = await handler.handle(command)

        user = await user_repository.find_by_id(user_id)
        assert user is not None
        assert user.email == "alice@example.com"
        assert user.display_name == "Alice"
        assert user.tenant_id == TENANT_ID

    async def test_duplicate_email_raises_conflict_error(
        self,
        user_repository: InMemoryUserRepository,
        password_service: BcryptPasswordService,
        event_producer: FakeKafkaProducer,
    ) -> None:
        handler = RegisterUserHandler(user_repository, password_service, event_producer)
        command = RegisterUserCommand(
            email="bob@example.com",
            password="StrongP@ss1",
            tenant_id=TENANT_ID,
        )

        await handler.handle(command)

        with pytest.raises(ConflictError, match="already exists"):
            await handler.handle(command)


class TestAuthentication:
    async def test_login_with_correct_password_returns_jwt(
        self,
        user_repository: InMemoryUserRepository,
        role_repository: InMemoryRoleRepository,
        password_service: BcryptPasswordService,
        jwt_service: JWTService,
        event_producer: FakeKafkaProducer,
        rate_limiter: FakeLoginRateLimiter,
    ) -> None:
        # Register user first
        register_handler = RegisterUserHandler(user_repository, password_service, event_producer)
        await register_handler.handle(
            RegisterUserCommand(
                email="charlie@example.com",
                password="Secret123!",
                tenant_id=TENANT_ID,
            )
        )

        # Login
        login_handler = LoginHandler(user_repository, role_repository, password_service, jwt_service, rate_limiter)
        result = await login_handler.handle(
            LoginCommand(
                email="charlie@example.com",
                password="Secret123!",
                tenant_id=TENANT_ID,
            )
        )

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        assert result.expires_in > 0

    async def test_login_with_wrong_password_raises_error(
        self,
        user_repository: InMemoryUserRepository,
        role_repository: InMemoryRoleRepository,
        password_service: BcryptPasswordService,
        jwt_service: JWTService,
        event_producer: FakeKafkaProducer,
        rate_limiter: FakeLoginRateLimiter,
    ) -> None:
        # Register user
        register_handler = RegisterUserHandler(user_repository, password_service, event_producer)
        await register_handler.handle(
            RegisterUserCommand(
                email="dave@example.com",
                password="Correct123!",
                tenant_id=TENANT_ID,
            )
        )

        # Attempt login with wrong password
        login_handler = LoginHandler(user_repository, role_repository, password_service, jwt_service, rate_limiter)
        with pytest.raises(AuthorizationError, match="Invalid email or password"):
            await login_handler.handle(
                LoginCommand(
                    email="dave@example.com",
                    password="Wrong123!",
                    tenant_id=TENANT_ID,
                )
            )

    async def test_jwt_decode_returns_matching_user_id(
        self,
        user_repository: InMemoryUserRepository,
        role_repository: InMemoryRoleRepository,
        password_service: BcryptPasswordService,
        jwt_service: JWTService,
        event_producer: FakeKafkaProducer,
        rate_limiter: FakeLoginRateLimiter,
    ) -> None:
        # Register user
        register_handler = RegisterUserHandler(user_repository, password_service, event_producer)
        user_id = await register_handler.handle(
            RegisterUserCommand(
                email="eve@example.com",
                password="Token123!",
                tenant_id=TENANT_ID,
            )
        )

        # Login
        login_handler = LoginHandler(user_repository, role_repository, password_service, jwt_service, rate_limiter)
        result = await login_handler.handle(
            LoginCommand(
                email="eve@example.com",
                password="Token123!",
                tenant_id=TENANT_ID,
            )
        )

        # Decode access token and verify user_id
        payload = jwt_service.decode_token(result.access_token)
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(TENANT_ID)
        assert payload["type"] == "access"


class TestRolePermissions:
    async def test_assign_role_with_permissions_grants_access(
        self,
        user_repository: InMemoryUserRepository,
        role_repository: InMemoryRoleRepository,
        password_service: BcryptPasswordService,
        event_producer: FakeKafkaProducer,
    ) -> None:
        # Register user
        register_handler = RegisterUserHandler(user_repository, password_service, event_producer)
        user_id = await register_handler.handle(
            RegisterUserCommand(
                email="frank@example.com",
                password="Role123!",
                tenant_id=TENANT_ID,
            )
        )

        # Create role with permission
        create_role_handler = CreateRoleHandler(role_repository)
        role_id = await create_role_handler.handle(
            CreateRoleCommand(
                name="editor",
                tenant_id=TENANT_ID,
                permissions=[{"object_type": "prefix", "actions": ["view", "add", "change"]}],
            )
        )

        # Assign role to user
        assign_handler = AssignRoleHandler(user_repository, role_repository, event_producer)
        await assign_handler.handle(AssignRoleCommand(user_id=user_id, role_id=role_id))

        # Check permission
        user = await user_repository.find_by_id(user_id)
        roles = await role_repository.find_by_ids(user.role_ids)

        checker = PermissionChecker()
        assert checker.has_permission(user, roles, [], "prefix", "view") is True
        assert checker.has_permission(user, roles, [], "prefix", "add") is True
        assert checker.has_permission(user, roles, [], "prefix", "change") is True

    async def test_unassigned_permission_is_denied(
        self,
        user_repository: InMemoryUserRepository,
        role_repository: InMemoryRoleRepository,
        password_service: BcryptPasswordService,
        event_producer: FakeKafkaProducer,
    ) -> None:
        # Register user
        register_handler = RegisterUserHandler(user_repository, password_service, event_producer)
        user_id = await register_handler.handle(
            RegisterUserCommand(
                email="grace@example.com",
                password="Perm123!",
                tenant_id=TENANT_ID,
            )
        )

        # Create role with limited permissions
        create_role_handler = CreateRoleHandler(role_repository)
        role_id = await create_role_handler.handle(
            CreateRoleCommand(
                name="viewer",
                tenant_id=TENANT_ID,
                permissions=[{"object_type": "prefix", "actions": ["view"]}],
            )
        )

        # Assign role
        assign_handler = AssignRoleHandler(user_repository, role_repository, event_producer)
        await assign_handler.handle(AssignRoleCommand(user_id=user_id, role_id=role_id))

        # Check that "delete" action is denied
        user = await user_repository.find_by_id(user_id)
        roles = await role_repository.find_by_ids(user.role_ids)

        checker = PermissionChecker()
        assert checker.has_permission(user, roles, [], "prefix", "delete") is False
        # Also check a completely unrelated object_type
        assert checker.has_permission(user, roles, [], "vlan", "view") is False


class TestTokenLifecycle:
    async def test_access_token_has_correct_claims(
        self,
        jwt_service: JWTService,
    ) -> None:
        user_id = uuid4()
        tenant_id = uuid4()

        token = jwt_service.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=["admin"],
        )

        payload = jwt_service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["type"] == "access"
        assert payload["roles"] == ["admin"]
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    async def test_refresh_token_has_refresh_type(
        self,
        jwt_service: JWTService,
    ) -> None:
        user_id = uuid4()
        tenant_id = uuid4()

        token = jwt_service.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
        )

        payload = jwt_service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["type"] == "refresh"
        assert "roles" not in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
