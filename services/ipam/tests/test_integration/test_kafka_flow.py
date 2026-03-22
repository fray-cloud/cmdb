"""Kafka integration tests: real Kafka via testcontainers.

Verifies KafkaEventProducer.publish() → KafkaEventConsumer receives → event data matches.
Marked with @pytest.mark.integration — requires Docker.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from ipam.domain.events import PrefixCreated
from testcontainers.kafka import KafkaContainer

from shared.messaging.consumer import KafkaEventConsumer
from shared.messaging.producer import KafkaEventProducer
from shared.messaging.serialization import EventSerializer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TOPIC = "test.ipam.events"


@pytest.fixture(scope="session")
def kafka_container():
    with KafkaContainer("confluentinc/cp-kafka:7.6.0") as kafka:
        yield kafka


@pytest.fixture(scope="session")
def bootstrap_servers(kafka_container):
    return kafka_container.get_bootstrap_server()


@pytest.fixture
def serializer():
    s = EventSerializer()
    s.register(PrefixCreated)
    return s


@pytest.fixture
async def producer(bootstrap_servers):
    p = KafkaEventProducer(bootstrap_servers=bootstrap_servers)
    await p.start()
    yield p
    await p.stop()


# ---------------------------------------------------------------------------
# TestKafkaFlow
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestKafkaFlow:
    """Publish event via KafkaEventProducer → consume via KafkaEventConsumer → verify."""

    async def test_publish_and_consume_event(
        self,
        bootstrap_servers: str,
        producer: KafkaEventProducer,
        serializer: EventSerializer,
    ) -> None:
        # Create a test event
        agg_id = uuid4()
        event = PrefixCreated(
            aggregate_id=agg_id,
            version=1,
            network="10.0.0.0/8",
            description="Kafka test",
            status="active",
        )

        # Publish event
        await producer.publish(TOPIC, event)

        # Set up consumer
        received_events: list = []

        async def handler(evt):
            received_events.append(evt)

        consumer = KafkaEventConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id=f"test-group-{uuid4()}",
            topics=[TOPIC],
            serializer=serializer,
        )
        consumer.subscribe(PrefixCreated, handler)
        await consumer.start()

        # Consume with timeout
        try:
            await asyncio.wait_for(consumer.consume(), timeout=10.0)
        except TimeoutError:
            pass
        finally:
            await consumer.stop()

        # Verify received
        assert len(received_events) >= 1
        received = received_events[0]
        assert isinstance(received, PrefixCreated)
        assert received.aggregate_id == agg_id
        assert received.network == "10.0.0.0/8"
        assert received.description == "Kafka test"

    async def test_publish_many_events(
        self,
        bootstrap_servers: str,
        producer: KafkaEventProducer,
        serializer: EventSerializer,
    ) -> None:
        events = [
            PrefixCreated(aggregate_id=uuid4(), version=1, network="10.0.0.0/8"),
            PrefixCreated(aggregate_id=uuid4(), version=1, network="172.16.0.0/12"),
            PrefixCreated(aggregate_id=uuid4(), version=1, network="192.168.0.0/16"),
        ]

        topic = f"test.bulk.{uuid4()}"
        await producer.publish_many(topic, events)

        received_events: list = []

        async def handler(evt):
            received_events.append(evt)

        consumer = KafkaEventConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id=f"test-group-{uuid4()}",
            topics=[topic],
            serializer=serializer,
        )
        consumer.subscribe(PrefixCreated, handler)
        await consumer.start()

        try:
            await asyncio.wait_for(consumer.consume(), timeout=10.0)
        except TimeoutError:
            pass
        finally:
            await consumer.stop()

        assert len(received_events) == 3
        networks = {e.network for e in received_events}
        assert networks == {"10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"}
