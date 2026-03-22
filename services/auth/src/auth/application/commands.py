from datetime import datetime
from uuid import UUID

from shared.cqrs.command import Command


class RegisterUserCommand(Command):
    email: str
    password: str
    tenant_id: UUID
    display_name: str | None = None


class LoginCommand(Command):
    email: str
    password: str
    tenant_id: UUID
    client_ip: str = "0.0.0.0"


class RefreshTokenCommand(Command):
    refresh_token: str


class LogoutCommand(Command):
    refresh_token: str


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


class CreateAPITokenCommand(Command):
    user_id: UUID
    tenant_id: UUID
    description: str | None = None
    scopes: list[str] | None = None
    expires_at: datetime | None = None
    allowed_ips: list[str] | None = None


class RevokeAPITokenCommand(Command):
    token_id: UUID
