"""IPAM Docker integration tests: real PostgreSQL via testcontainers.

These tests require Docker and are marked with @pytest.mark.integration.
Run with: uv run --package cmdb-ipam pytest services/ipam/tests/ -m integration
"""

from __future__ import annotations

import pytest
from ipam.application.command_handlers import (
    CreatePrefixHandler,
    DeletePrefixHandler,
    UpdatePrefixHandler,
)
from ipam.application.commands import (
    CreatePrefixCommand,
    DeletePrefixCommand,
    UpdatePrefixCommand,
)
from ipam.application.queries import ListPrefixesQuery
from ipam.application.query_handlers import GetPrefixHandler, ListPrefixesHandler
from ipam.domain.events import PrefixCreated, PrefixDeleted, PrefixUpdated
from ipam.infrastructure.models import IPAMBase
from ipam.infrastructure.read_model_repository import PostgresPrefixReadModelRepository
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from shared.event.models import EventStoreBase
from shared.event.pg_store import PostgresEventStore

from .conftest import FakeKafkaProducer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
async def engine(postgres_container):
    url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url)
    async with eng.begin() as conn:
        await conn.run_sync(IPAMBase.metadata.create_all)
        await conn.run_sync(EventStoreBase.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        # TRUNCATE all tables after each test
        for table in reversed(IPAMBase.metadata.sorted_tables):
            await session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        for table in reversed(EventStoreBase.metadata.sorted_tables):
            await session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        await session.commit()


@pytest.fixture
def session_factory(session):
    """Return an async context manager that yields the existing session."""

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _factory():
        yield session

    return _factory


@pytest.fixture
def event_store(session_factory):
    store = PostgresEventStore(session_factory)
    store.register_event_type(PrefixCreated)
    store.register_event_type(PrefixUpdated)
    store.register_event_type(PrefixDeleted)
    return store


@pytest.fixture
def prefix_read_repo(session):
    return PostgresPrefixReadModelRepository(session)


@pytest.fixture
def kafka_producer():
    return FakeKafkaProducer()


@pytest.fixture
def create_handler(event_store, prefix_read_repo, kafka_producer):
    return CreatePrefixHandler(event_store, prefix_read_repo, kafka_producer)


@pytest.fixture
def update_handler(event_store, prefix_read_repo, kafka_producer):
    return UpdatePrefixHandler(event_store, prefix_read_repo, kafka_producer)


@pytest.fixture
def delete_handler(event_store, prefix_read_repo, kafka_producer):
    return DeletePrefixHandler(event_store, prefix_read_repo, kafka_producer)


@pytest.fixture
def get_handler(prefix_read_repo):
    return GetPrefixHandler(prefix_read_repo)


@pytest.fixture
def list_handler(prefix_read_repo):
    return ListPrefixesHandler(prefix_read_repo)


# ---------------------------------------------------------------------------
# TestPrefixCRUDWithDB
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPrefixCRUDWithDB:
    """Full CRUD cycle with real PostgreSQL: create, read, update, delete."""

    async def test_create_prefix_persists_event(
        self,
        create_handler: CreatePrefixHandler,
        session: AsyncSession,
    ) -> None:
        prefix_id = await create_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8", description="DB test"),
        )

        # Verify event persisted in domain_events table
        result = await session.execute(
            text("SELECT * FROM domain_events WHERE aggregate_id = :agg_id"),
            {"agg_id": str(prefix_id)},
        )
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0].event_type.endswith("PrefixCreated")

    async def test_create_prefix_persists_read_model(
        self,
        create_handler: CreatePrefixHandler,
        session: AsyncSession,
    ) -> None:
        prefix_id = await create_handler.handle(
            CreatePrefixCommand(network="192.168.1.0/24", description="Read model test"),
        )

        # Verify read model persisted in prefixes_read table
        result = await session.execute(
            text("SELECT * FROM prefixes_read WHERE id = :id"),
            {"id": str(prefix_id)},
        )
        row = result.fetchone()
        assert row is not None
        assert row.network == "192.168.1.0/24"
        assert row.description == "Read model test"

    async def test_query_returns_created_prefix(
        self,
        create_handler: CreatePrefixHandler,
        list_handler: ListPrefixesHandler,
    ) -> None:
        prefix_id = await create_handler.handle(
            CreatePrefixCommand(network="172.16.0.0/12", description="Queryable"),
        )

        items, total = await list_handler.handle(ListPrefixesQuery())
        assert total == 1
        assert items[0].id == prefix_id
        assert items[0].network == "172.16.0.0/12"

    async def test_update_persists_in_db(
        self,
        create_handler: CreatePrefixHandler,
        update_handler: UpdatePrefixHandler,
        get_handler: GetPrefixHandler,
        session: AsyncSession,
    ) -> None:
        from ipam.application.queries import GetPrefixQuery

        prefix_id = await create_handler.handle(
            CreatePrefixCommand(network="10.1.0.0/16", description="Original"),
        )

        await update_handler.handle(
            UpdatePrefixCommand(prefix_id=prefix_id, description="Updated via DB"),
        )

        dto = await get_handler.handle(GetPrefixQuery(prefix_id=prefix_id))
        assert dto.description == "Updated via DB"

        # Verify two events in store
        result = await session.execute(
            text("SELECT COUNT(*) FROM domain_events WHERE aggregate_id = :agg_id"),
            {"agg_id": str(prefix_id)},
        )
        assert result.scalar_one() == 2

    async def test_delete_marks_as_deleted(
        self,
        create_handler: CreatePrefixHandler,
        delete_handler: DeletePrefixHandler,
        list_handler: ListPrefixesHandler,
        session: AsyncSession,
    ) -> None:
        prefix_id = await create_handler.handle(
            CreatePrefixCommand(network="10.2.0.0/16"),
        )

        await delete_handler.handle(DeletePrefixCommand(prefix_id=prefix_id))

        # List should return nothing (deleted prefix excluded)
        items, total = await list_handler.handle(ListPrefixesQuery())
        assert total == 0

        # But the read model row still exists with is_deleted=True
        result = await session.execute(
            text("SELECT is_deleted FROM prefixes_read WHERE id = :id"),
            {"id": str(prefix_id)},
        )
        row = result.fetchone()
        assert row is not None
        assert row.is_deleted is True


# ---------------------------------------------------------------------------
# TestFilteringWithDB
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFilteringWithDB:
    """Filtering with real PostgreSQL: status filter + description ILIKE."""

    async def test_filter_by_status(
        self,
        create_handler: CreatePrefixHandler,
        list_handler: ListPrefixesHandler,
    ) -> None:
        await create_handler.handle(CreatePrefixCommand(network="10.0.0.0/8", status="active"))
        await create_handler.handle(CreatePrefixCommand(network="172.16.0.0/12", status="reserved"))
        await create_handler.handle(CreatePrefixCommand(network="192.168.0.0/16", status="active"))

        items, total = await list_handler.handle(ListPrefixesQuery(status="active"))
        assert total == 2
        assert all(item.status == "active" for item in items)

    async def test_filter_by_description_contains(
        self,
        create_handler: CreatePrefixHandler,
        list_handler: ListPrefixesHandler,
    ) -> None:
        await create_handler.handle(CreatePrefixCommand(network="10.0.0.0/8", description="Production network"))
        await create_handler.handle(CreatePrefixCommand(network="172.16.0.0/12", description="Development lab"))
        await create_handler.handle(CreatePrefixCommand(network="192.168.0.0/16", description="Production servers"))

        items, total = await list_handler.handle(
            ListPrefixesQuery(description_contains="production"),
        )
        assert total == 2
        assert all("roduction" in item.description for item in items)
