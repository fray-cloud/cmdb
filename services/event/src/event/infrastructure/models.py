from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime as SADateTime
from sqlalchemy import Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class EventBase(DeclarativeBase):
    pass


class StoredEventModel(EventBase):
    __tablename__ = "stored_events"
    __table_args__ = (UniqueConstraint("aggregate_id", "version", name="uq_event_aggregate_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aggregate_id: Mapped[UUID] = mapped_column(index=True)
    aggregate_type: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now(), index=True)


class ChangeLogModel(EventBase):
    __tablename__ = "change_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aggregate_id: Mapped[UUID] = mapped_column(index=True)
    aggregate_type: Mapped[str] = mapped_column(String(255), index=True)
    action: Mapped[str] = mapped_column(String(50))
    event_type: Mapped[str] = mapped_column(Text)
    user_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now(), index=True)


class JournalEntryModel(EventBase):
    __tablename__ = "journal_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(100))
    object_id: Mapped[UUID]
    entry_type: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str] = mapped_column(Text)
    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_journal_object", "object_type", "object_id"),
        Index("ix_journal_tenant", "tenant_id"),
    )
