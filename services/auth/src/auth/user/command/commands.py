from uuid import UUID

from shared.cqrs.command import Command


class RegisterUserCommand(Command):
    email: str
    password: str
    tenant_id: UUID
    display_name: str | None = None


class ChangePasswordCommand(Command):
    user_id: UUID
    old_password: str
    new_password: str


class AssignRoleCommand(Command):
    user_id: UUID
    role_id: UUID


class RemoveRoleCommand(Command):
    user_id: UUID
    role_id: UUID
