"""Tenant isolation integration tests: real PostgreSQL via testcontainers.

Verifies that queries filtered by tenant_id return only that tenant's data.
Marked with @pytest.mark.integration — requires Docker.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from ipam.application.command_handlers import CreatePrefixHandler
from ipam.application.commands import CreatePrefixCommand
from ipam.application.queries import ListPrefixesQuery
from ipam.application.query_handlers import ListPrefixesHandler
from ipam.domain.events import PrefixCreated
from ipam.infrastructure.models import IPAMBase
from ipam.infrastructure.read_model_repository import PostgresPrefixReadModelRepository
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from shared.event.models import EventStoreBase
from shared.event.pg_store import PostgresEventStore

from .conftest import FakeKafkaProducer

TENANT_A = uuid4()
TENANT_B = uuid4()


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
        for table in reversed(IPAMBase.metadata.sorted_tables):
            await session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        for table in reversed(EventStoreBase.metadata.sorted_tables):
            await session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        await session.commit()


@pytest.fixture
def session_factory(session):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _factory():
        yield session

    return _factory


@pytest.fixture
def event_store(session_factory):
    store = PostgresEventStore(session_factory)
    store.register_event_type(PrefixCreated)
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
def list_handler(prefix_read_repo):
    return ListPrefixesHandler(prefix_read_repo)


# ---------------------------------------------------------------------------
# TestTenantIsolation
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTenantIsolation:
    """Verify that listing prefixes with a tenant_id filter returns only that tenant's data."""

    async def test_tenant_a_sees_only_own_prefixes(
        self,
        create_handler: CreatePrefixHandler,
        list_handler: ListPrefixesHandler,
    ) -> None:
        # Create prefixes for tenant A
        await create_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8", tenant_id=TENANT_A, description="Tenant A net"),
        )
        await create_handler.handle(
            CreatePrefixCommand(network="10.1.0.0/16", tenant_id=TENANT_A, description="Tenant A subnet"),
        )

        # Create prefix for tenant B
        await create_handler.handle(
            CreatePrefixCommand(network="172.16.0.0/12", tenant_id=TENANT_B, description="Tenant B net"),
        )

        # Query with tenant A filter
        items, total = await list_handler.handle(ListPrefixesQuery(tenant_id=TENANT_A))
        assert total == 2
        assert all(item.tenant_id == TENANT_A for item in items)

    async def test_tenant_b_sees_only_own_prefixes(
        self,
        create_handler: CreatePrefixHandler,
        list_handler: ListPrefixesHandler,
    ) -> None:
        # Create prefixes for tenant A
        await create_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8", tenant_id=TENANT_A),
        )

        # Create prefixes for tenant B
        await create_handler.handle(
            CreatePrefixCommand(network="172.16.0.0/12", tenant_id=TENANT_B),
        )
        await create_handler.handle(
            CreatePrefixCommand(network="192.168.0.0/16", tenant_id=TENANT_B),
        )

        # Query with tenant B filter
        items, total = await list_handler.handle(ListPrefixesQuery(tenant_id=TENANT_B))
        assert total == 2
        assert all(item.tenant_id == TENANT_B for item in items)

    async def test_no_filter_returns_all_tenants(
        self,
        create_handler: CreatePrefixHandler,
        list_handler: ListPrefixesHandler,
    ) -> None:
        await create_handler.handle(
            CreatePrefixCommand(network="10.0.0.0/8", tenant_id=TENANT_A),
        )
        await create_handler.handle(
            CreatePrefixCommand(network="172.16.0.0/12", tenant_id=TENANT_B),
        )

        # Query without tenant filter
        items, total = await list_handler.handle(ListPrefixesQuery())
        assert total == 2
