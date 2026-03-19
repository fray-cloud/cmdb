import hashlib
import secrets
from uuid import UUID

from auth.application.dto import APITokenDTO, AuthTokenDTO
from auth.domain.api_token import APIToken
from auth.domain.permission import Permission
from auth.domain.repository import APITokenRepository, RoleRepository, UserRepository
from auth.domain.role import Role
from auth.domain.user import User
from auth.infrastructure.login_rate_limiter import LoginRateLimiter
from auth.infrastructure.security import BcryptPasswordService, JWTService
from auth.infrastructure.token_blacklist import RedisTokenBlacklist
from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import (
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    EntityNotFoundError,
)
from shared.messaging.producer import KafkaEventProducer


class RegisterUserHandler(CommandHandler[UUID]):
    def __init__(
        self,
        repository: UserRepository,
        password_service: BcryptPasswordService,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._password_service = password_service
        self._event_producer = event_producer

    async def handle(self, command: Command) -> UUID:
        existing = await self._repository.find_by_email(command.email, command.tenant_id)
        if existing is not None:
            raise ConflictError(f"User with email '{command.email}' already exists")

        password_hash = await self._password_service.hash_async(command.password)

        user = User.create(
            email=command.email,
            password_hash=password_hash,
            tenant_id=command.tenant_id,
            display_name=command.display_name,
        )

        await self._repository.save(user)

        for event in user.collect_events():
            await self._event_producer.publish("auth.events", event)

        return user.id


class LoginHandler(CommandHandler[AuthTokenDTO]):
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
    def __init__(
        self,
        jwt_service: JWTService,
        token_blacklist: RedisTokenBlacklist,
    ) -> None:
        self._jwt_service = jwt_service
        self._token_blacklist = token_blacklist

    async def handle(self, command: Command) -> None:
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


class ChangePasswordHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: UserRepository,
        password_service: BcryptPasswordService,
    ) -> None:
        self._repository = repository
        self._password_service = password_service

    async def handle(self, command: Command) -> None:
        user = await self._repository.find_by_id(command.user_id)
        if user is None:
            raise EntityNotFoundError(f"User {command.user_id} not found")

        if not await self._password_service.verify_async(command.old_password, user.password_hash):
            raise AuthorizationError("Current password is incorrect")

        new_hash = await self._password_service.hash_async(command.new_password)
        user.change_password(new_hash)
        await self._repository.save(user)


class AssignRoleHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: UserRepository,
        role_repository: RoleRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._role_repository = role_repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> None:
        user = await self._repository.find_by_id(command.user_id)
        if user is None:
            raise EntityNotFoundError(f"User {command.user_id} not found")

        role = await self._role_repository.find_by_id(command.role_id)
        if role is None:
            raise EntityNotFoundError(f"Role {command.role_id} not found")

        user.assign_role(command.role_id)
        await self._repository.save(user)

        for event in user.collect_events():
            await self._event_producer.publish("auth.events", event)


class RemoveRoleHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: UserRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> None:
        user = await self._repository.find_by_id(command.user_id)
        if user is None:
            raise EntityNotFoundError(f"User {command.user_id} not found")

        user.remove_role(command.role_id)
        await self._repository.save(user)

        for event in user.collect_events():
            await self._event_producer.publish("auth.events", event)


class CreateRoleHandler(CommandHandler[UUID]):
    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        self._repository = repository

    async def handle(self, command: Command) -> UUID:
        existing = await self._repository.find_by_name(command.name, command.tenant_id)
        if existing is not None:
            raise ConflictError(f"Role '{command.name}' already exists")

        permissions = []
        if command.permissions:
            permissions = [Permission(**p) for p in command.permissions]

        role = Role.create(
            name=command.name,
            tenant_id=command.tenant_id,
            description=command.description,
            permissions=permissions,
        )

        await self._repository.save(role)
        return role.id


class UpdateRoleHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        self._repository = repository

    async def handle(self, command: Command) -> None:
        role = await self._repository.find_by_id(command.role_id)
        if role is None:
            raise EntityNotFoundError(f"Role {command.role_id} not found")

        if role.is_system:
            raise BusinessRuleViolationError("Cannot modify system role")

        if command.name is not None:
            role.name = command.name
        if command.description is not None:
            role.description = command.description
        if command.permissions is not None:
            role.permissions = [Permission(**p) for p in command.permissions]

        from datetime import datetime

        role.updated_at = datetime.now()
        await self._repository.save(role)


class DeleteRoleHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        self._repository = repository

    async def handle(self, command: Command) -> None:
        role = await self._repository.find_by_id(command.role_id)
        if role is None:
            raise EntityNotFoundError(f"Role {command.role_id} not found")

        if role.is_system:
            raise BusinessRuleViolationError("Cannot delete system role")

        await self._repository.delete(command.role_id)


class CreateAPITokenHandler(CommandHandler[APITokenDTO]):
    def __init__(
        self,
        repository: APITokenRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> APITokenDTO:
        raw_key = secrets.token_urlsafe(48)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        token = APIToken.create(
            user_id=command.user_id,
            tenant_id=command.tenant_id,
            key_hash=key_hash,
            description=command.description,
            scopes=command.scopes,
            expires_at=command.expires_at,
            allowed_ips=command.allowed_ips,
        )

        await self._repository.save(token)

        for event in token.collect_events():
            await self._event_producer.publish("auth.events", event)

        return APITokenDTO(
            id=token.id,
            user_id=token.user_id,
            tenant_id=token.tenant_id,
            description=token.description,
            scopes=token.scopes,
            expires_at=token.expires_at,
            allowed_ips=token.allowed_ips,
            is_revoked=token.is_revoked,
            created_at=token.created_at,
            key=raw_key,
        )


class RevokeAPITokenHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: APITokenRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> None:
        token = await self._repository.find_by_id(command.token_id)
        if token is None:
            raise EntityNotFoundError(f"API Token {command.token_id} not found")

        token.revoke()
        await self._repository.save(token)

        for event in token.collect_events():
            await self._event_producer.publish("auth.events", event)
