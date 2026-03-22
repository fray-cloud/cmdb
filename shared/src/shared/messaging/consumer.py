import logging
from collections.abc import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

from shared.event.domain_event import DomainEvent
from shared.messaging.producer import KafkaEventProducer
from shared.messaging.serialization import EventSerializer

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class KafkaEventConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        serializer: EventSerializer | None = None,
        dlq_topic: str | None = None,
        dlq_producer: KafkaEventProducer | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._topics = topics
        self._serializer = serializer or EventSerializer()
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}
        self._dlq_topic = dlq_topic
        self._dlq_producer = dlq_producer
        self._consumer: AIOKafkaConsumer | None = None

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            enable_auto_commit=False,
        )
        await self._consumer.start()

    async def stop(self) -> None:
        if self._consumer:
            await self._consumer.stop()

    async def consume(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Consumer not started")
        async for msg in self._consumer:
            try:
                event = self._serializer.deserialize(msg.value)
                handlers = self._handlers.get(type(event), [])
                for handler in handlers:
                    await handler(event)
                await self._consumer.commit()
            except Exception:
                logger.exception("Failed to process message from %s", msg.topic)
                await self._send_to_dlq(msg)
                await self._consumer.commit()

    async def _send_to_dlq(self, msg: object) -> None:
        if self._dlq_producer and self._dlq_topic:
            if self._dlq_producer._producer is None:
                return
            await self._dlq_producer._producer.send_and_wait(
                self._dlq_topic,
                value=msg.value,  # type: ignore[attr-defined]
                key=msg.key,  # type: ignore[attr-defined]
            )
