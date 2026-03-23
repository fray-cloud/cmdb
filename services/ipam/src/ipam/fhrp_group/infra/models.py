"""FHRP Group SQLAlchemy read model — denormalized projection table."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Computed, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column

from ipam.shared.models_base import IPAMBase


class FHRPGroupReadModel(IPAMBase):
    __tablename__ = "fhrp_groups_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    protocol: Mapped[str] = mapped_column(String(20))
    group_id_value: Mapped[int] = mapped_column(Integer)
    auth_type: Mapped[str] = mapped_column(String(20))
    auth_key: Mapped[str] = mapped_column(String(255), default="")
    name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(protocol, '') || ' ' || coalesce(description, ''))",  # noqa: E501
            persisted=True,
        ),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_fhrp_groups_read_search", "search_vector", postgresql_using="gin"),)
