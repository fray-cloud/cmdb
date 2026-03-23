from uuid import UUID

from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import BusinessRuleViolationError, ConflictError, EntityNotFoundError

from auth.role.domain.repository import RoleRepository
from auth.role.domain.role import Role
from auth.shared.domain.permission import Permission


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
