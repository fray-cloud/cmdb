"""Export template SQLAlchemy model — Jinja2 template storage for custom exports."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column

from ipam.shared.models_base import IPAMBase


class ExportTemplateModel(IPAMBase):
    __tablename__ = "export_templates"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    template_content: Mapped[str] = mapped_column(Text)
    output_format: Mapped[str] = mapped_column(String(20), default="text")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
