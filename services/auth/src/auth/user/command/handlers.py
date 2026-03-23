"""Command handlers for user registration, password changes, and role management."""

from uuid import UUID

from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import AuthorizationError, ConflictError, EntityNotFoundError
from shared.messaging.producer import KafkaEventProducer

from auth.role import RoleRepository
from auth.shared.security import BcryptPasswordService
from auth.user.domain import UserRepository
from auth.user.domain.user import User


class RegisterUserHandler(CommandHandler[UUID]):
    """Handles user registration with duplicate-email checking."""

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
        """Register a new user and publish domain events."""
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


class ChangePasswordHandler(CommandHandler[None]):
    """Handles password change after verifying the current password."""

    def __init__(
        self,
        repository: UserRepository,
        password_service: BcryptPasswordService,
    ) -> None:
        self._repository = repository
        self._password_service = password_service

    async def handle(self, command: Command) -> None:
        """Verify old password and update to the new password hash."""
        user = await self._repository.find_by_id(command.user_id)
        if user is None:
            raise EntityNotFoundError(f"User {command.user_id} not found")

        if not await self._password_service.verify_async(command.old_password, user.password_hash):
            raise AuthorizationError("Current password is incorrect")

        new_hash = await self._password_service.hash_async(command.new_password)
        user.change_password(new_hash)
        await self._repository.save(user)


class AssignRoleHandler(CommandHandler[None]):
    """Handles assigning a role to a user."""

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
        """Assign a role to the user and publish domain events."""
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
    """Handles removing a role from a user."""

    def __init__(
        self,
        repository: UserRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> None:
        """Remove a role from the user and publish domain events."""
        user = await self._repository.find_by_id(command.user_id)
        if user is None:
            raise EntityNotFoundError(f"User {command.user_id} not found")

        user.remove_role(command.role_id)
        await self._repository.save(user)

        for event in user.collect_events():
            await self._event_producer.publish("auth.events", event)
