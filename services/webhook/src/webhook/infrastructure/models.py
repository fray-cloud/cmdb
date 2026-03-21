from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class WebhookBase(DeclarativeBase):
    pass


class WebhookModel(WebhookBase):
    __tablename__ = "webhooks"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(Text)
    secret: Mapped[str] = mapped_column(String(255))
    event_types: Mapped[list] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WebhookEventLogModel(WebhookBase):
    __tablename__ = "webhook_event_logs"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    webhook_id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), index=True)
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    request_url: Mapped[str] = mapped_column(Text)
    request_body: Mapped[str] = mapped_column(Text)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
