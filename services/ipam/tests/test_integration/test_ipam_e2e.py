"""IPAM E2E mock tests: full command → event → read model → query flow.

These tests use InMemoryEventStore + InMemoryPrefixReadModelRepository + FakeKafkaProducer.
No Docker required — they run as regular (non-integration) tests.
"""

from __future__ import annotations

from uuid import UUID

from ipam.application.command_handlers import (
    BulkCreatePrefixesHandler,
    CreatePrefixHandler,
    DeletePrefixHandler,
    UpdatePrefixHandler,
)
from ipam.application.commands import (
    BulkCreatePrefixesCommand,
    CreatePrefixCommand,
    DeletePrefixCommand,
    UpdatePrefixCommand,
)
from ipam.application.queries import GetPrefixQuery, ListPrefixesQuery
from ipam.application.query_handlers import GetPrefixHandler, ListPrefixesHandler
from ipam.domain.events import PrefixCreated, PrefixDeleted, PrefixUpdated

from .conftest import FakeKafkaProducer, InMemoryEventStore, InMemoryPrefixReadModelRepository


class TestCreatePrefixE2E:
    """Create Prefix → verify event stored → verify read model → query returns it."""

    async def test_create_prefix_stores_event(
        self,
        create_prefix_handler: CreatePrefixHandler,
        event_store: InMemoryEventStore,
    ) -> None:
        command = CreatePrefixCommand(network="10.0.0.0/8", description="Test prefix")
        prefix_id = await create_prefix_handler.handle(command)

        events = event_store.get_events(prefix_id)
        assert len(events) == 1
        assert isinstance(events[0], PrefixCreated)
        assert events[0].network == "10.0.0.0/8"
        assert events[0].aggregate_id == prefix_id

    async def test_create_prefix_populates_read_model(
        self,
        create_prefix_handler: CreatePrefixHandler,
        prefix_read_repo: InMemoryPrefixReadModelRepository,
    ) -> None:
        command = CreatePrefixCommand(network="192.168.1.0/24", description="LAN")
        prefix_id = await create_prefix_handler.handle(command)

        data = await prefix_read_repo.find_by_id(prefix_id)
        assert data is not None
        assert data["network"] == "192.168.1.0/24"
        assert data["description"] == "LAN"
        assert data["status"] == "active"

    async def test_create_prefix_publishes_kafka_event(
        self,
        create_prefix_handler: CreatePrefixHandler,
        kafka_producer: FakeKafkaProducer,
    ) -> None:
        command = CreatePrefixCommand(network="172.16.0.0/12")
        await create_prefix_handler.handle(command)

        kafka_events = kafka_producer.get_events("ipam.events")
        assert len(kafka_events) == 1
        assert isinstance(kafka_events[0], PrefixCreated)

    async def test_create_prefix_queryable(
        self,
        create_prefix_handler: CreatePrefixHandler,
        get_prefix_handler: GetPrefixHandler,
        list_prefixes_handler: ListPrefixesHandler,
    ) -> None:
        command = CreatePrefixCommand(network="10.1.0.0/16", description="Queryable")
        prefix_id = await create_prefix_handler.handle(command)

        # GetPrefixQuery
        dto = await get_prefix_handler.handle(GetPrefixQuery(prefix_id=prefix_id))
        assert dto.network == "10.1.0.0/16"
        assert dto.description == "Queryable"

        # ListPrefixesQuery
        items, total = await list_prefixes_handler.handle(ListPrefixesQuery())
        assert total == 1
        assert items[0].id == prefix_id

    async def test_create_prefix_with_all_fields(
        self,
        create_prefix_handler: CreatePrefixHandler,
        get_prefix_handler: GetPrefixHandler,
    ) -> None:
        command = CreatePrefixCommand(
            network="10.2.0.0/16",
            status="reserved",
            role="infrastructure",
            description="Full fields",
            custom_fields={"site": "dc1"},
        )
        prefix_id = await create_prefix_handler.handle(command)

        dto = await get_prefix_handler.handle(GetPrefixQuery(prefix_id=prefix_id))
        assert dto.status == "reserved"
        assert dto.role == "infrastructure"
        assert dto.custom_fields == {"site": "dc1"}


class TestUpdatePrefixE2E:
    """Update Prefix → verify update event → verify read model updated."""

    async def test_update_prefix_stores_event(
        self,
        create_prefix_handler: CreatePrefixHandler,
        update_prefix_handler: UpdatePrefixHandler,
        event_store: InMemoryEventStore,
    ) -> None:
        prefix_id = await create_prefix_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8"),
        )

        await update_prefix_handler.handle(
            UpdatePrefixCommand(prefix_id=prefix_id, description="Updated"),
        )

        events = event_store.get_events(prefix_id)
        assert len(events) == 2
        assert isinstance(events[0], PrefixCreated)
        assert isinstance(events[1], PrefixUpdated)
        assert events[1].description == "Updated"

    async def test_update_prefix_updates_read_model(
        self,
        create_prefix_handler: CreatePrefixHandler,
        update_prefix_handler: UpdatePrefixHandler,
        get_prefix_handler: GetPrefixHandler,
    ) -> None:
        prefix_id = await create_prefix_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8", description="Original"),
        )

        await update_prefix_handler.handle(
            UpdatePrefixCommand(prefix_id=prefix_id, description="Updated", role="infra"),
        )

        dto = await get_prefix_handler.handle(GetPrefixQuery(prefix_id=prefix_id))
        assert dto.description == "Updated"
        assert dto.role == "infra"
        assert dto.network == "10.0.0.0/8"  # Unchanged

    async def test_update_prefix_publishes_kafka_event(
        self,
        create_prefix_handler: CreatePrefixHandler,
        update_prefix_handler: UpdatePrefixHandler,
        kafka_producer: FakeKafkaProducer,
    ) -> None:
        prefix_id = await create_prefix_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8"),
        )

        await update_prefix_handler.handle(
            UpdatePrefixCommand(prefix_id=prefix_id, description="Updated"),
        )

        kafka_events = kafka_producer.get_events("ipam.events")
        assert len(kafka_events) == 2
        assert isinstance(kafka_events[1], PrefixUpdated)


class TestDeletePrefixE2E:
    """Delete Prefix → verify delete event → verify read model marked deleted."""

    async def test_delete_prefix_stores_event(
        self,
        create_prefix_handler: CreatePrefixHandler,
        delete_prefix_handler: DeletePrefixHandler,
        event_store: InMemoryEventStore,
    ) -> None:
        prefix_id = await create_prefix_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8"),
        )

        await delete_prefix_handler.handle(DeletePrefixCommand(prefix_id=prefix_id))

        events = event_store.get_events(prefix_id)
        assert len(events) == 2
        assert isinstance(events[1], PrefixDeleted)

    async def test_delete_prefix_marks_read_model_deleted(
        self,
        create_prefix_handler: CreatePrefixHandler,
        delete_prefix_handler: DeletePrefixHandler,
        prefix_read_repo: InMemoryPrefixReadModelRepository,
    ) -> None:
        prefix_id = await create_prefix_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8"),
        )

        # Exists before delete
        assert await prefix_read_repo.find_by_id(prefix_id) is not None

        await delete_prefix_handler.handle(DeletePrefixCommand(prefix_id=prefix_id))

        # Gone after delete
        assert await prefix_read_repo.find_by_id(prefix_id) is None

    async def test_delete_prefix_excluded_from_list(
        self,
        create_prefix_handler: CreatePrefixHandler,
        delete_prefix_handler: DeletePrefixHandler,
        list_prefixes_handler: ListPrefixesHandler,
    ) -> None:
        prefix_id = await create_prefix_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8"),
        )
        await create_prefix_handler.handle(
            CreatePrefixCommand(network="192.168.0.0/16"),
        )

        await delete_prefix_handler.handle(DeletePrefixCommand(prefix_id=prefix_id))

        items, total = await list_prefixes_handler.handle(ListPrefixesQuery())
        assert total == 1
        assert items[0].network == "192.168.0.0/16"

    async def test_delete_prefix_publishes_kafka_event(
        self,
        create_prefix_handler: CreatePrefixHandler,
        delete_prefix_handler: DeletePrefixHandler,
        kafka_producer: FakeKafkaProducer,
    ) -> None:
        prefix_id = await create_prefix_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8"),
        )

        await delete_prefix_handler.handle(DeletePrefixCommand(prefix_id=prefix_id))

        kafka_events = kafka_producer.get_events("ipam.events")
        assert len(kafka_events) == 2
        assert isinstance(kafka_events[1], PrefixDeleted)


class TestBulkCreatePrefixesE2E:
    """BulkCreate multiple prefixes → verify all created."""

    async def test_bulk_create_stores_all_events(
        self,
        bulk_create_prefix_handler: BulkCreatePrefixesHandler,
        event_store: InMemoryEventStore,
    ) -> None:
        command = BulkCreatePrefixesCommand(
            items=[
                CreatePrefixCommand(network="10.0.0.0/8", description="Net A"),
                CreatePrefixCommand(network="172.16.0.0/12", description="Net B"),
                CreatePrefixCommand(network="192.168.0.0/16", description="Net C"),
            ]
        )
        ids = await bulk_create_prefix_handler.handle(command)

        assert len(ids) == 3
        all_events = event_store.all_events()
        assert len(all_events) == 3
        assert all(isinstance(e, PrefixCreated) for e in all_events)

    async def test_bulk_create_populates_read_model(
        self,
        bulk_create_prefix_handler: BulkCreatePrefixesHandler,
        list_prefixes_handler: ListPrefixesHandler,
    ) -> None:
        command = BulkCreatePrefixesCommand(
            items=[
                CreatePrefixCommand(network="10.0.0.0/8"),
                CreatePrefixCommand(network="172.16.0.0/12"),
            ]
        )
        await bulk_create_prefix_handler.handle(command)

        items, total = await list_prefixes_handler.handle(ListPrefixesQuery())
        assert total == 2

    async def test_bulk_create_publishes_all_kafka_events(
        self,
        bulk_create_prefix_handler: BulkCreatePrefixesHandler,
        kafka_producer: FakeKafkaProducer,
    ) -> None:
        command = BulkCreatePrefixesCommand(
            items=[
                CreatePrefixCommand(network="10.0.0.0/8"),
                CreatePrefixCommand(network="172.16.0.0/12"),
                CreatePrefixCommand(network="192.168.0.0/16"),
            ]
        )
        await bulk_create_prefix_handler.handle(command)

        kafka_events = kafka_producer.get_events("ipam.events")
        assert len(kafka_events) == 3

    async def test_bulk_create_returns_unique_ids(
        self,
        bulk_create_prefix_handler: BulkCreatePrefixesHandler,
    ) -> None:
        command = BulkCreatePrefixesCommand(
            items=[
                CreatePrefixCommand(network="10.0.0.0/8"),
                CreatePrefixCommand(network="172.16.0.0/12"),
            ]
        )
        ids = await bulk_create_prefix_handler.handle(command)

        assert len(ids) == 2
        assert len(set(ids)) == 2  # All unique
        assert all(isinstance(id_, UUID) for id_ in ids)
