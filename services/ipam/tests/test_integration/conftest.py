"""Fixtures for IPAM integration tests (in-memory, no Docker required)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import pytest
from ipam.prefix.command.handlers import (
    BulkCreatePrefixesHandler,
    CreatePrefixHandler,
    DeletePrefixHandler,
    UpdatePrefixHandler,
)
from ipam.prefix.query.handlers import GetPrefixHandler, ListPrefixesHandler
from ipam.prefix.query.read_model import PrefixReadModelRepository
from shared.domain.exceptions import ConflictError
from shared.event.domain_event import DomainEvent

# ---------------------------------------------------------------------------
# InMemoryEventStore
# ---------------------------------------------------------------------------


class InMemoryEventStore:
    """In-memory event store for mock integration tests.

    Matches the PostgresEventStore interface used by command handlers:
    - append(aggregate_id, events, expected_version, *, aggregate=None, session=None)
    - load_aggregate(aggregate_cls, aggregate_id)
    - load_stream(aggregate_id, after_version=0)
    - load_snapshot(aggregate_id)
    - save_snapshot(aggregate_id, state, version)
    """

    def __init__(self) -> None:
        self._events: dict[UUID, list[DomainEvent]] = {}
        self._versions: dict[UUID, int] = {}
        self._snapshots: dict[UUID, tuple[dict[str, Any], int]] = {}

    async def append(
        self,
        aggregate_id: UUID,
        events: list[DomainEvent],
        expected_version: int,
        *,
        aggregate: Any = None,
        session: Any = None,
    ) -> None:
        current_version = self._versions.get(aggregate_id, 0)
        if current_version != expected_version:
            raise ConflictError(
                f"Expected version {expected_version}, but current version is {current_version}",
                details={
                    "aggregate_id": str(aggregate_id),
                    "expected_version": expected_version,
                    "current_version": current_version,
                },
            )
        if aggregate_id not in self._events:
            self._events[aggregate_id] = []
        self._events[aggregate_id].extend(events)
        self._versions[aggregate_id] = current_version + len(events)

    async def load_aggregate(self, aggregate_cls: type, aggregate_id: UUID) -> Any | None:
        snapshot_data = await self.load_snapshot(aggregate_id)
        if snapshot_data is not None:
            state, snapshot_version = snapshot_data
            aggregate = aggregate_cls.from_snapshot(aggregate_id, state, snapshot_version)
            events = await self.load_stream(aggregate_id, after_version=snapshot_version)
        else:
            events = await self.load_stream(aggregate_id)
            if not events:
                return None
            aggregate = aggregate_cls(aggregate_id=aggregate_id)
            snapshot_version = 0

        aggregate.load_from_history(events)
        return aggregate

    async def load_stream(
        self, aggregate_id: UUID, after_version: int = 0, *, session: Any = None
    ) -> list[DomainEvent]:
        all_events = self._events.get(aggregate_id, [])
        return [e for e in all_events if e.version > after_version]

    async def load_snapshot(self, aggregate_id: UUID) -> tuple[dict[str, Any], int] | None:
        return self._snapshots.get(aggregate_id)

    async def save_snapshot(self, aggregate_id: UUID, state: dict[str, Any], version: int) -> None:
        self._snapshots[aggregate_id] = (state, version)

    def get_events(self, aggregate_id: UUID) -> list[DomainEvent]:
        """Helper: return all stored events for an aggregate (for test assertions)."""
        return list(self._events.get(aggregate_id, []))

    def all_events(self) -> list[DomainEvent]:
        """Helper: return all stored events across all aggregates."""
        result: list[DomainEvent] = []
        for events in self._events.values():
            result.extend(events)
        return result


# ---------------------------------------------------------------------------
# FakeKafkaProducer
# ---------------------------------------------------------------------------


class FakeKafkaProducer:
    """Collects published events for assertion instead of sending to Kafka."""

    def __init__(self) -> None:
        self.published: list[tuple[str, DomainEvent]] = []

    async def publish(self, topic: str, event: DomainEvent) -> None:
        self.published.append((topic, event))

    async def publish_many(self, topic: str, events: list[DomainEvent]) -> None:
        for event in events:
            self.published.append((topic, event))

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    def get_events(self, topic: str | None = None) -> list[DomainEvent]:
        """Helper: return published events, optionally filtered by topic."""
        if topic is None:
            return [e for _, e in self.published]
        return [e for t, e in self.published if t == topic]


# ---------------------------------------------------------------------------
# InMemoryPrefixReadModelRepository
# ---------------------------------------------------------------------------


class InMemoryPrefixReadModelRepository(PrefixReadModelRepository):
    """In-memory read model repository for Prefix aggregates."""

    def __init__(self) -> None:
        self._data: dict[UUID, dict] = {}

    async def upsert_from_aggregate(self, aggregate: Any) -> None:
        now = datetime.now()
        existing = self._data.get(aggregate.id)
        created_at = existing["created_at"] if existing else now
        self._data[aggregate.id] = {
            "id": aggregate.id,
            "network": str(aggregate.network.network) if aggregate.network else None,
            "vrf_id": aggregate.vrf_id,
            "vlan_id": aggregate.vlan_id,
            "status": aggregate.status.value,
            "role": aggregate.role,
            "tenant_id": aggregate.tenant_id,
            "description": aggregate.description,
            "custom_fields": aggregate.custom_fields,
            "tags": list(aggregate.tags),
            "created_at": created_at,
            "updated_at": now,
        }

    async def find_by_id(self, entity_id: UUID) -> dict | None:
        data = self._data.get(entity_id)
        if data is None:
            return None
        if data.get("_deleted"):
            return None
        return dict(data)

    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: Any = None,
        sort_params: Any = None,
        tag_slugs: Any = None,
        custom_field_filters: Any = None,
    ) -> tuple[list[dict], int]:
        items = [d for d in self._data.values() if not d.get("_deleted")]
        total = len(items)
        return items[offset : offset + limit], total

    async def mark_deleted(self, entity_id: UUID) -> None:
        if entity_id in self._data:
            self._data[entity_id]["_deleted"] = True

    async def find_children(self, parent_network: str, vrf_id: UUID | None) -> list[dict]:
        import ipaddress

        parent_net = ipaddress.ip_network(parent_network, strict=False)
        children: list[dict] = []
        for data in self._data.values():
            if data.get("_deleted"):
                continue
            if data.get("vrf_id") != vrf_id:
                continue
            try:
                child_net = ipaddress.ip_network(data["network"], strict=False)
            except (ValueError, TypeError):
                continue
            if child_net != parent_net and child_net.subnet_of(parent_net):
                children.append(dict(data))
        return children

    async def find_by_vrf(self, vrf_id: UUID, *, offset: int = 0, limit: int = 50) -> tuple[list[dict], int]:
        items = [d for d in self._data.values() if not d.get("_deleted") and d.get("vrf_id") == vrf_id]
        total = len(items)
        return items[offset : offset + limit], total


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def event_store() -> InMemoryEventStore:
    return InMemoryEventStore()


@pytest.fixture
def kafka_producer() -> FakeKafkaProducer:
    return FakeKafkaProducer()


@pytest.fixture
def prefix_read_repo() -> InMemoryPrefixReadModelRepository:
    return InMemoryPrefixReadModelRepository()


@pytest.fixture
def create_prefix_handler(
    event_store: InMemoryEventStore,
    prefix_read_repo: InMemoryPrefixReadModelRepository,
    kafka_producer: FakeKafkaProducer,
) -> CreatePrefixHandler:
    return CreatePrefixHandler(event_store, prefix_read_repo, kafka_producer)


@pytest.fixture
def update_prefix_handler(
    event_store: InMemoryEventStore,
    prefix_read_repo: InMemoryPrefixReadModelRepository,
    kafka_producer: FakeKafkaProducer,
) -> UpdatePrefixHandler:
    return UpdatePrefixHandler(event_store, prefix_read_repo, kafka_producer)


@pytest.fixture
def delete_prefix_handler(
    event_store: InMemoryEventStore,
    prefix_read_repo: InMemoryPrefixReadModelRepository,
    kafka_producer: FakeKafkaProducer,
) -> DeletePrefixHandler:
    return DeletePrefixHandler(event_store, prefix_read_repo, kafka_producer)


@pytest.fixture
def bulk_create_prefix_handler(
    event_store: InMemoryEventStore,
    prefix_read_repo: InMemoryPrefixReadModelRepository,
    kafka_producer: FakeKafkaProducer,
) -> BulkCreatePrefixesHandler:
    return BulkCreatePrefixesHandler(event_store, prefix_read_repo, kafka_producer)


@pytest.fixture
def get_prefix_handler(
    prefix_read_repo: InMemoryPrefixReadModelRepository,
) -> GetPrefixHandler:
    return GetPrefixHandler(prefix_read_repo)


@pytest.fixture
def list_prefixes_handler(
    prefix_read_repo: InMemoryPrefixReadModelRepository,
) -> ListPrefixesHandler:
    return ListPrefixesHandler(prefix_read_repo)
