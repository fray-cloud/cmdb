from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime as SADateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class TenantBase(DeclarativeBase):
    pass


class TenantModel(TenantBase):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    db_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
