"""Phase 2 준비: 타 서비스 이벤트 수신 Consumer.

lifespan 연동은 Phase 2에서 실제 토픽이 존재할 때 추가.
"""

import logging

from shared.event.domain_event import DomainEvent
from shared.messaging.consumer import KafkaEventConsumer
from shared.messaging.serialization import EventSerializer

logger = logging.getLogger(__name__)


class CrossServiceConsumer:
    def __init__(self, bootstrap_servers: str, serializer: EventSerializer) -> None:
        self._consumer = KafkaEventConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id="ipam-cross-service",
            topics=["dcim.events", "tenancy.events"],
            serializer=serializer,
        )

    async def handle_dcim_event(self, event: DomainEvent) -> None:
        logger.info("Received DCIM event: %s (Phase 2)", event.event_type)

    async def handle_tenancy_event(self, event: DomainEvent) -> None:
        logger.info("Received Tenancy event: %s (Phase 2)", event.event_type)

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def consume(self) -> None:
        await self._consumer.consume()
