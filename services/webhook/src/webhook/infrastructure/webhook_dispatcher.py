import json
import logging

from webhook.domain.webhook import Webhook
from webhook.domain.webhook_log import WebhookEventLog
from webhook.infrastructure.database import Database
from webhook.infrastructure.repository import PostgresWebhookLogRepository
from webhook.infrastructure.retry_manager import RetryManager
from webhook.infrastructure.webhook_delivery import WebhookDeliveryService

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    def __init__(
        self,
        database: Database,
        delivery_service: WebhookDeliveryService,
        retry_manager: RetryManager,
    ) -> None:
        self._database = database
        self._delivery_service = delivery_service
        self._retry_manager = retry_manager

    async def dispatch(self, webhook: Webhook, payload: dict, event_type: str, attempt: int = 1) -> None:
        result = await self._delivery_service.deliver(
            url=webhook.url,
            payload=payload,
            secret=webhook.secret,
            event_type=event_type,
            webhook_id=str(webhook.id),
        )

        log = WebhookEventLog(
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=payload.get("aggregate_id", ""),
            request_url=webhook.url,
            request_body=json.dumps(payload, default=str)[:8192],
            response_status=result.status_code,
            response_body=result.response_body,
            error_message=result.error_message,
            attempt=attempt,
            duration_ms=result.duration_ms,
            success=result.success,
        )
        await self._save_log(log)

        if not result.success:
            scheduled = await self._retry_manager.schedule_retry(
                webhook_id=str(webhook.id),
                event_payload=payload,
                event_type=event_type,
                attempt=attempt + 1,
            )
            if not scheduled:
                logger.warning("Max retries exceeded for webhook %s, event %s", webhook.id, event_type)

    async def _save_log(self, log: WebhookEventLog) -> None:
        repo = PostgresWebhookLogRepository(self._database)
        await repo.save(log)
