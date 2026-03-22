from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class SharedBase(DeclarativeBase):
    pass


class CustomFieldDefinitionModel(SharedBase):
    __tablename__ = "custom_field_definitions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    content_type: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    field_type: Mapped[str] = mapped_column(String(20))
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    default_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    choices: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    validation_regex: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())


class TagModel(SharedBase):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str] = mapped_column(String(7), default="#9e9e9e")
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())


class TagAssignmentModel(SharedBase):
    __tablename__ = "tag_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id"))
    content_type: Mapped[str] = mapped_column(String(100))
    object_id: Mapped[UUID]

    __table_args__ = (
        Index("ix_tag_assignments_content_object", "content_type", "object_id"),
        Index(
            "ix_tag_assignments_unique",
            "tag_id",
            "content_type",
            "object_id",
            unique=True,
        ),
    )
