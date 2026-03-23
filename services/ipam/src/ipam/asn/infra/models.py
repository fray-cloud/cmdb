"""ASN SQLAlchemy read model — denormalized projection table for ASN queries."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Computed, DateTime, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column

from ipam.shared.models_base import IPAMBase


class ASNReadModel(IPAMBase):
    __tablename__ = "asns_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    asn: Mapped[int] = mapped_column(Integer, index=True)
    rir_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', asn::text || ' ' || coalesce(description, ''))", persisted=True),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_asns_read_search", "search_vector", postgresql_using="gin"),)
