from __future__ import annotations

from datetime import datetime
from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError

from webhook.application.commands import CreateWebhookCommand, DeleteWebhookCommand, UpdateWebhookCommand
from webhook.domain.repository import WebhookRepository
from webhook.domain.webhook import Webhook
from webhook.infrastructure.webhook_cache import WebhookCache


class CreateWebhookHandler(CommandHandler[UUID]):
    def __init__(self, repo: WebhookRepository, cache: WebhookCache | None = None) -> None:
        self._repo = repo
        self._cache = cache

    async def handle(self, command: CreateWebhookCommand) -> UUID:
        webhook = Webhook(
            name=command.name,
            url=command.url,
            secret=command.secret,
            event_types=command.event_types,
            tenant_id=command.tenant_id,
            description=command.description,
        )
        await self._repo.save(webhook)
        if self._cache:
            await self._cache.invalidate(command.tenant_id)
        return webhook.id


class UpdateWebhookHandler(CommandHandler[UUID]):
    def __init__(self, repo: WebhookRepository, cache: WebhookCache | None = None) -> None:
        self._repo = repo
        self._cache = cache

    async def handle(self, command: UpdateWebhookCommand) -> UUID:
        webhook = await self._repo.find_by_id(command.webhook_id)
        if webhook is None:
            raise EntityNotFoundError(f"Webhook {command.webhook_id} not found")

        if command.name is not None:
            webhook.name = command.name
        if command.url is not None:
            webhook.url = command.url
        if command.secret is not None:
            webhook.secret = command.secret
        if command.event_types is not None:
            webhook.event_types = command.event_types
        if command.is_active is not None:
            webhook.is_active = command.is_active
        if command.description is not None:
            webhook.description = command.description
        webhook.updated_at = datetime.now()

        await self._repo.save(webhook)
        if self._cache:
            await self._cache.invalidate(webhook.tenant_id)
        return webhook.id


class DeleteWebhookHandler(CommandHandler[None]):
    def __init__(self, repo: WebhookRepository, cache: WebhookCache | None = None) -> None:
        self._repo = repo
        self._cache = cache

    async def handle(self, command: DeleteWebhookCommand) -> None:
        webhook = await self._repo.find_by_id(command.webhook_id)
        if webhook is None:
            raise EntityNotFoundError(f"Webhook {command.webhook_id} not found")

        await self._repo.delete(command.webhook_id)
        if self._cache:
            await self._cache.invalidate(webhook.tenant_id)
