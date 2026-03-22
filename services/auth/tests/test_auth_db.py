"""Auth Docker integration tests: real PostgreSQL via testcontainers.

Verifies User CRUD with real database persistence.
Marked with @pytest.mark.integration — requires Docker.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from auth.domain.user import User
from auth.infrastructure.models import AuthBase
from auth.infrastructure.user_repository import PostgresUserRepository
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

TENANT_ID = uuid4()


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
        await conn.run_sync(AuthBase.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        for table in reversed(AuthBase.metadata.sorted_tables):
            await session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        await session.commit()


# ---------------------------------------------------------------------------
# TestAuthDB
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAuthDB:
    """Create user -> persist -> retrieve by email -> verify fields."""

    async def test_create_user_persists_to_db(self, session: AsyncSession) -> None:
        repo = PostgresUserRepository(session)

        user = User.create(
            email="alice@example.com",
            password_hash="hashed_password_123",
            tenant_id=TENANT_ID,
            display_name="Alice",
        )
        saved = await repo.save(user)

        assert saved.id == user.id
        assert saved.email == "alice@example.com"

    async def test_retrieve_user_by_email(self, session: AsyncSession) -> None:
        repo = PostgresUserRepository(session)

        user = User.create(
            email="bob@example.com",
            password_hash="hashed_password_456",
            tenant_id=TENANT_ID,
            display_name="Bob",
        )
        await repo.save(user)

        found = await repo.find_by_email("bob@example.com", TENANT_ID)
        assert found is not None
        assert found.id == user.id
        assert found.email == "bob@example.com"
        assert found.display_name == "Bob"
        assert found.tenant_id == TENANT_ID

    async def test_retrieve_non_existent_email_returns_none(self, session: AsyncSession) -> None:
        repo = PostgresUserRepository(session)

        found = await repo.find_by_email("nobody@example.com", TENANT_ID)
        assert found is None

    async def test_find_by_id_returns_user(self, session: AsyncSession) -> None:
        repo = PostgresUserRepository(session)

        user = User.create(
            email="charlie@example.com",
            password_hash="hashed_pw",
            tenant_id=TENANT_ID,
        )
        await repo.save(user)

        found = await repo.find_by_id(user.id)
        assert found is not None
        assert found.email == "charlie@example.com"

    async def test_delete_user_removes_from_db(self, session: AsyncSession) -> None:
        repo = PostgresUserRepository(session)

        user = User.create(
            email="dave@example.com",
            password_hash="hashed_pw",
            tenant_id=TENANT_ID,
        )
        await repo.save(user)

        await repo.delete(user.id)

        found = await repo.find_by_id(user.id)
        assert found is None
