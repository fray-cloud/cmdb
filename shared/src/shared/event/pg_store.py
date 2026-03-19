import json
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.domain.exceptions import ConflictError
from shared.event.domain_event import DomainEvent
from shared.event.models import StoredEvent, StoredSnapshot
from shared.event.snapshot import SnapshotStrategy
from shared.event.store import EventStore


class PostgresEventStore(EventStore):
    def __init__(
        self,
        session_factory: Callable[..., AsyncSession],
        snapshot_strategy: SnapshotStrategy | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._snapshot_strategy = snapshot_strategy or SnapshotStrategy()
        self._event_registry: dict[str, type[DomainEvent]] = {}

    def register_event_type(self, event_cls: type[DomainEvent]) -> None:
        key = f"{event_cls.__module__}.{event_cls.__qualname__}"
        self._event_registry[key] = event_cls

    @asynccontextmanager
    async def _get_session(self, session: AsyncSession | None = None) -> AsyncGenerator[tuple[AsyncSession, bool]]:
        if session is not None:
            yield session, False
        else:
            async with self._session_factory() as new_session:
                yield new_session, True

    async def append(
        self,
        aggregate_id: UUID,
        events: list[DomainEvent],
        expected_version: int,
        *,
        session: AsyncSession | None = None,
    ) -> None:
        async with self._get_session(session) as (sess, owns_session):
            result = await sess.execute(
                select(StoredEvent.version)
                .where(StoredEvent.aggregate_id == aggregate_id)
                .order_by(StoredEvent.version.desc())
                .limit(1)
            )
            current_version = result.scalar() or 0

            if current_version != expected_version:
                raise ConflictError(
                    f"Expected version {expected_version}, but current version is {current_version}",
                    details={
                        "aggregate_id": str(aggregate_id),
                        "expected_version": expected_version,
                        "current_version": current_version,
                    },
                )

            for event in events:
                stored = StoredEvent(
                    aggregate_id=event.aggregate_id,
                    event_type=event.event_type,
                    version=event.version,
                    payload=json.loads(event.model_dump_json()),
                    timestamp=event.timestamp,
                )
                sess.add(stored)

            if owns_session:
                await sess.commit()

    async def load_stream(
        self,
        aggregate_id: UUID,
        after_version: int = 0,
        *,
        session: AsyncSession | None = None,
    ) -> list[DomainEvent]:
        async with self._get_session(session) as (sess, _):
            result = await sess.execute(
                select(StoredEvent)
                .where(
                    StoredEvent.aggregate_id == aggregate_id,
                    StoredEvent.version > after_version,
                )
                .order_by(StoredEvent.version)
            )
            rows = result.scalars().all()

            events: list[DomainEvent] = []
            for row in rows:
                event_cls = self._event_registry.get(row.event_type)
                if event_cls is None:
                    event_cls = DomainEvent
                events.append(event_cls.model_validate(row.payload))
            return events

    async def load_snapshot(
        self,
        aggregate_id: UUID,
    ) -> tuple[dict[str, Any], int] | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(StoredSnapshot)
                .where(StoredSnapshot.aggregate_id == aggregate_id)
                .order_by(StoredSnapshot.version.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return row.state, row.version

    async def save_snapshot(
        self,
        aggregate_id: UUID,
        state: dict[str, Any],
        version: int,
    ) -> None:
        async with self._session_factory() as session:
            snapshot = StoredSnapshot(
                aggregate_id=aggregate_id,
                aggregate_type="",
                version=version,
                state=state,
            )
            session.add(snapshot)
            await session.commit()
