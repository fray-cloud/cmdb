from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column

from ipam.shared.models_base import IPAMBase


class SavedFilterModel(IPAMBase):
    __tablename__ = "saved_filters"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), index=True)
    name: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(50))
    filter_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_saved_filters_user_entity", "user_id", "entity_type"),)
