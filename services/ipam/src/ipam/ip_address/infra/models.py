"""SQLAlchemy read model for the IPAddress aggregate."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Computed, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column

from ipam.shared.models_base import IPAMBase


class IPAddressReadModel(IPAMBase):
    __tablename__ = "ip_addresses_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    address: Mapped[str] = mapped_column(String(50), index=True)
    vrf_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    dns_name: Mapped[str] = mapped_column(String(255), default="")
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', coalesce(address, '') || ' ' || coalesce(dns_name, '') || ' ' || coalesce(description, ''))",  # noqa: E501
            persisted=True,
        ),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_ip_addresses_read_search", "search_vector", postgresql_using="gin"),)
