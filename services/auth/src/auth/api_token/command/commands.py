"""API token command definitions for CQRS write operations."""

from datetime import datetime
from uuid import UUID

from shared.cqrs.command import Command


class CreateAPITokenCommand(Command):
    user_id: UUID
    tenant_id: UUID
    description: str | None = None
    scopes: list[str] | None = None
    expires_at: datetime | None = None
    allowed_ips: list[str] | None = None


class RevokeAPITokenCommand(Command):
    token_id: UUID
