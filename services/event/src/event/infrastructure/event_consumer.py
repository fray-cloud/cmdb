import json
import logging
import re
from datetime import UTC, datetime
from uuid import UUID

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from event.infrastructure.changelog_repository import ChangeLogRepository
from event.infrastructure.event_repository import EventRepository

logger = logging.getLogger(__name__)

# Map event name suffix to action
ACTION_PATTERNS = [
    (re.compile(r"Created$"), "created"),
    (re.compile(r"Updated$"), "updated"),
    (re.compile(r"Changed$"), "updated"),
    (re.compile(r"Deleted$"), "deleted"),
    (re.compile(r"Suspended$"), "suspended"),
    (re.compile(r"Locked$"), "locked"),
    (re.compile(r"Assigned$"), "assigned"),
    (re.compile(r"Removed$"), "removed"),
    (re.compile(r"Revoked$"), "revoked"),
    (re.compile(r"Generated$"), "created"),
]


def _extract_aggregate_type(event_type: str) -> str:
    """Extract aggregate type from event_type string.

    Example: 'auth.domain.events.UserCreated' → 'user'
    """
    parts = event_type.rsplit(".", 1)
    event_name = parts[-1] if parts else event_type

    # Remove action suffix to get the entity name
    for pattern, _ in ACTION_PATTERNS:
        match = pattern.search(event_name)
        if match:
            entity = event_name[: match.start()]
            return entity.lower() if entity else "unknown"

    return event_name.lower()


def _extract_action(event_type: str) -> str:
    """Extract action from event_type string.

    Example: 'auth.domain.events.UserCreated' → 'created'
    """
    parts = event_type.rsplit(".", 1)
    event_name = parts[-1] if parts else event_type

    for pattern, action in ACTION_PATTERNS:
        if pattern.search(event_name):
            return action

    return "changed"


class EventConsumerWorker:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        session_factory: async_sessionmaker[AsyncSession],
        dlq_topic: str = "events.dlq",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._session_factory = session_factory
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
        logger.info("Event consumer started (pattern: *.events)")

    async def stop(self) -> None:
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        if self._dlq_producer:
            await self._dlq_producer.stop()
        logger.info("Event consumer stopped")

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
                logger.exception("Failed to process message from %s", msg.topic)
                await self._send_to_dlq(msg)
                await self._consumer.commit()

    async def _process_message(self, msg: object) -> None:
        raw = json.loads(msg.value)  # type: ignore[attr-defined]

        aggregate_id = raw.get("aggregate_id")
        event_type = raw.get("event_type", "")
        version = raw.get("version", 0)
        timestamp_str = raw.get("timestamp")

        if not aggregate_id or not event_type:
            logger.warning("Skipping message with missing aggregate_id or event_type")
            return

        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now(UTC)

        aggregate_type = _extract_aggregate_type(event_type)
        action = _extract_action(event_type)

        async with self._session_factory() as session:
            event_repo = EventRepository(session)
            changelog_repo = ChangeLogRepository(session)

            await event_repo.append(
                {
                    "aggregate_id": UUID(aggregate_id),
                    "aggregate_type": aggregate_type,
                    "event_type": event_type,
                    "version": version,
                    "payload": raw,
                    "timestamp": timestamp,
                }
            )

            await changelog_repo.create(
                {
                    "aggregate_id": UUID(aggregate_id),
                    "aggregate_type": aggregate_type,
                    "action": action,
                    "event_type": event_type,
                    "user_id": _try_uuid(raw.get("user_id")),
                    "tenant_id": _try_uuid(raw.get("tenant_id")),
                    "correlation_id": raw.get("correlation_id"),
                    "timestamp": timestamp,
                }
            )

    async def _send_to_dlq(self, msg: object) -> None:
        if self._dlq_producer:
            await self._dlq_producer.send_and_wait(
                self._dlq_topic,
                value=msg.value,  # type: ignore[attr-defined]
                key=msg.key,  # type: ignore[attr-defined]
            )


def _try_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return None
