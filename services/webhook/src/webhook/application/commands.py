from uuid import UUID

from shared.cqrs.command import Command


class CreateWebhookCommand(Command):
    name: str
    url: str
    secret: str
    event_types: list[str]
    tenant_id: UUID | None = None
    description: str = ""


class UpdateWebhookCommand(Command):
    webhook_id: UUID
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None
    description: str | None = None


class DeleteWebhookCommand(Command):
    webhook_id: UUID
