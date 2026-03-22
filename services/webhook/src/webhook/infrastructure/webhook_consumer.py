import asyncio
import json
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from webhook.infrastructure.database import Database
from webhook.infrastructure.repository import PostgresWebhookRepository
from webhook.infrastructure.webhook_cache import WebhookCache
from webhook.infrastructure.webhook_dispatcher import WebhookDispatcher

logger = logging.getLogger(__name__)


class WebhookConsumerWorker:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        database: Database,
        dispatcher: WebhookDispatcher,
        cache: WebhookCache,
        dlq_topic: str = "webhook.dlq",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._database = database
        self._dispatcher = dispatcher
        self._cache = cache
        self._dlq_topic = dlq_topic
        self._consumer: AIOKafkaConsumer | None = None
        self._dlq_producer: AIOKafkaProducer | None = None
        self._running = False

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            enable_auto_commit=False,
        )
        self._consumer.subscribe(pattern=r".*\.events")
        await self._consumer.start()
        self._dlq_producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
        await self._dlq_producer.start()
        self._running = True
        logger.info("Webhook consumer started (pattern: *.events)")

    async def stop(self) -> None:
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        if self._dlq_producer:
            await self._dlq_producer.stop()
        logger.info("Webhook consumer stopped")

    async def consume(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Consumer not started")
        async for msg in self._consumer:
            if not self._running:
                break
            try:
                await self._process_message(msg)
                await self._consumer.commit()
            except Exception:
                logger.exception("Failed to process webhook message from %s", msg.topic)
                await self._send_to_dlq(msg)
                await self._consumer.commit()

    async def _process_message(self, msg: object) -> None:
        raw = json.loads(msg.value)  # type: ignore[attr-defined]
        event_type = raw.get("event_type", "")
        if not event_type:
            return

        event_tenant_id = raw.get("tenant_id")
        event_tenant_uuid = UUID(event_tenant_id) if event_tenant_id else None

        # Get matching webhooks
        if event_tenant_uuid is not None:
            # Tenant-scoped event -> only webhooks for this tenant
            webhooks = await self._get_active_webhooks(event_tenant_uuid)
        else:
            # Global event (no tenant_id) -> all active webhooks
            webhooks = await self._get_all_active_webhooks()

        for webhook in webhooks:
            if webhook.matches_event(event_type):
                await self._dispatcher.dispatch(webhook, raw, event_type)

    async def _get_active_webhooks(self, tenant_id: UUID) -> list:
        # Try cache first
        cached = await self._cache.get_active_webhooks(tenant_id)
        if cached is not None:
            return cached
        # Miss -> query DB
        repo = PostgresWebhookRepository(self._database)
        webhooks = await repo.find_active_for_tenant(tenant_id)
        await self._cache.set_active_webhooks(tenant_id, webhooks)
        return webhooks

    async def _get_all_active_webhooks(self) -> list:
        # For global events, get all active webhooks (cache key: _global)
        cached = await self._cache.get_active_webhooks(None)
        if cached is not None:
            return cached
        repo = PostgresWebhookRepository(self._database)
        webhooks_list, _ = await repo.find_all(is_active=True, limit=1000)
        await self._cache.set_active_webhooks(None, webhooks_list)
        return webhooks_list

    async def _send_to_dlq(self, msg: object) -> None:
        if self._dlq_producer:
            await self._dlq_producer.send_and_wait(
                self._dlq_topic,
                value=msg.value,  # type: ignore[attr-defined]
                key=msg.key,  # type: ignore[attr-defined]
            )


class RetryWorker:
    def __init__(
        self,
        retry_manager: "RetryManager",  # noqa: F821
        database: Database,
        dispatcher: WebhookDispatcher,
        cache: WebhookCache,
        poll_interval: float = 5.0,
    ) -> None:
        from webhook.infrastructure.retry_manager import RetryManager  # noqa: F811

        self._retry_manager: RetryManager = retry_manager
        self._database = database
        self._dispatcher = dispatcher
        self._cache = cache
        self._poll_interval = poll_interval
        self._running = True

    async def run(self) -> None:
        while self._running:
            try:
                items = await self._retry_manager.get_due_retries()
                for item in items:
                    repo = PostgresWebhookRepository(self._database)
                    webhook = await repo.find_by_id(UUID(item.webhook_id))
                    if webhook and webhook.is_active:
                        await self._dispatcher.dispatch(webhook, item.event_payload, item.event_type, item.attempt)
                    else:
                        logger.info("Skipping retry for deleted/inactive webhook %s", item.webhook_id)
            except Exception:
                logger.exception("Error processing retries")
            await asyncio.sleep(self._poll_interval)

    async def stop(self) -> None:
        self._running = False
