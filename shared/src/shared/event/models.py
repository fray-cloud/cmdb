from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime as SADateTime
from sqlalchemy import Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class EventStoreBase(DeclarativeBase):
    pass


class StoredEvent(EventStoreBase):
    __tablename__ = "domain_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aggregate_id: Mapped[UUID] = mapped_column(index=True)
    event_type: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB)
    timestamp: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "ix_domain_events_agg_version",
            "aggregate_id",
            "version",
            unique=True,
        ),
    )


class StoredSnapshot(EventStoreBase):
    __tablename__ = "aggregate_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aggregate_id: Mapped[UUID] = mapped_column(index=True)
    aggregate_type: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    state: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "ix_snapshots_agg_version",
            "aggregate_id",
            "version",
            unique=True,
        ),
    )
