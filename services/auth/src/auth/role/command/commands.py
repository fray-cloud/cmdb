from uuid import UUID

from shared.cqrs.command import Command


class CreateRoleCommand(Command):
    name: str
    tenant_id: UUID
    description: str | None = None
    permissions: list[dict] | None = None


class UpdateRoleCommand(Command):
    role_id: UUID
    name: str | None = None
    description: str | None = None
    permissions: list[dict] | None = None


class DeleteRoleCommand(Command):
    role_id: UUID
