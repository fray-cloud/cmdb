from types import TracebackType

from aiokafka import AIOKafkaProducer

from shared.event.domain_event import DomainEvent
from shared.messaging.serialization import EventSerializer


class KafkaEventProducer:
    def __init__(
        self,
        bootstrap_servers: str,
        serializer: EventSerializer | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._serializer = serializer or EventSerializer()
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def publish(self, topic: str, event: DomainEvent) -> None:
        if self._producer is None:
            raise RuntimeError("Producer not started")
        key = str(event.aggregate_id).encode("utf-8")
        value = self._serializer.serialize(event)
        await self._producer.send_and_wait(topic, value=value, key=key)

    async def publish_many(self, topic: str, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(topic, event)

    async def __aenter__(self) -> "KafkaEventProducer":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()
