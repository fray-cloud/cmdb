import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from event.infrastructure.config import Settings
from event.infrastructure.database import Database
from event.infrastructure.event_consumer import EventConsumerWorker
from event.interface.router import router
from shared.api.errors import domain_exception_handler
from shared.api.middleware import CorrelationIdMiddleware
from shared.domain.exceptions import DomainError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()

    database = Database(settings.database_url)

    session_factory = async_sessionmaker(
        database.engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    consumer = EventConsumerWorker(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_group_id,
        session_factory=session_factory,
        dlq_topic=settings.kafka_dlq_topic,
    )
    await consumer.start()

    consumer_task = asyncio.create_task(consumer.consume())

    app.state.database = database
    app.state.settings = settings
    app.state.consumer = consumer

    yield

    await consumer.stop()
    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task
    await database.close()


def create_app() -> FastAPI:
    app = FastAPI(title="CMDB Event Service", lifespan=lifespan)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.include_router(router)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
