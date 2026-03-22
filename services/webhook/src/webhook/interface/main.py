import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from shared.api.errors import domain_exception_handler
from shared.api.middleware import CorrelationIdMiddleware
from shared.domain.exceptions import DomainError

from webhook.infrastructure.config import Settings
from webhook.infrastructure.database import Database
from webhook.infrastructure.retry_manager import RetryManager
from webhook.infrastructure.webhook_cache import WebhookCache
from webhook.infrastructure.webhook_consumer import RetryWorker, WebhookConsumerWorker
from webhook.infrastructure.webhook_delivery import WebhookDeliveryService
from webhook.infrastructure.webhook_dispatcher import WebhookDispatcher
from webhook.interface.routers.webhook_router import router as webhook_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()
    database = Database(settings.database_url)

    delivery_service = WebhookDeliveryService(timeout=settings.webhook_delivery_timeout)
    await delivery_service.start()

    retry_manager = RetryManager(
        settings.redis_url,
        max_retries=settings.webhook_max_retries,
        backoffs=settings.webhook_retry_backoffs,
    )
    await retry_manager.connect()

    webhook_cache = WebhookCache(settings.redis_url)
    await webhook_cache.connect()

    dispatcher = WebhookDispatcher(database, delivery_service, retry_manager)

    consumer = WebhookConsumerWorker(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_group_id,
        database=database,
        dispatcher=dispatcher,
        cache=webhook_cache,
        dlq_topic=settings.kafka_dlq_topic,
    )
    await consumer.start()
    consumer_task = asyncio.create_task(consumer.consume())

    retry_worker = RetryWorker(
        retry_manager=retry_manager,
        database=database,
        dispatcher=dispatcher,
        cache=webhook_cache,
    )
    retry_task = asyncio.create_task(retry_worker.run())

    app.state.database = database
    app.state.settings = settings
    app.state.delivery_service = delivery_service
    app.state.webhook_cache = webhook_cache

    yield

    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task
    await consumer.stop()

    await retry_worker.stop()
    retry_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await retry_task

    await delivery_service.stop()
    await retry_manager.close()
    await webhook_cache.close()
    await database.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="CMDB Webhook Service",
        version="1.0.0",
        description="Webhook delivery service for CMDB domain events.",
        openapi_tags=[{"name": "webhooks", "description": "Webhook registration and delivery logs"}],
        lifespan=lifespan,
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.include_router(webhook_router, prefix="/api/v1")

    @app.get("/health", include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
