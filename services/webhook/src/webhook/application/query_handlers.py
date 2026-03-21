from __future__ import annotations

from shared.cqrs.query import QueryHandler
from shared.domain.exceptions import EntityNotFoundError
from webhook.application.dto import WebhookDTO, WebhookLogDTO
from webhook.application.queries import GetWebhookQuery, ListWebhookLogsQuery, ListWebhooksQuery
from webhook.domain.repository import WebhookLogRepository, WebhookRepository


class GetWebhookHandler(QueryHandler[WebhookDTO]):
    def __init__(self, repo: WebhookRepository) -> None:
        self._repo = repo

    async def handle(self, query: GetWebhookQuery) -> WebhookDTO:
        webhook = await self._repo.find_by_id(query.webhook_id)
        if webhook is None:
            raise EntityNotFoundError(f"Webhook {query.webhook_id} not found")
        return WebhookDTO.model_validate(webhook.model_dump())


class ListWebhooksHandler(QueryHandler[tuple[list[WebhookDTO], int]]):
    def __init__(self, repo: WebhookRepository) -> None:
        self._repo = repo

    async def handle(self, query: ListWebhooksQuery) -> tuple[list[WebhookDTO], int]:
        webhooks, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            is_active=query.is_active,
            tenant_id=query.tenant_id,
        )
        return [WebhookDTO.model_validate(w.model_dump()) for w in webhooks], total


class ListWebhookLogsHandler(QueryHandler[tuple[list[WebhookLogDTO], int]]):
    def __init__(self, log_repo: WebhookLogRepository) -> None:
        self._log_repo = log_repo

    async def handle(self, query: ListWebhookLogsQuery) -> tuple[list[WebhookLogDTO], int]:
        logs, total = await self._log_repo.find_by_webhook(
            query.webhook_id,
            offset=query.offset,
            limit=query.limit,
        )
        return [WebhookLogDTO.model_validate(log.model_dump()) for log in logs], total
