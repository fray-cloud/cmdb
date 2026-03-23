"""Data transfer objects for VLANGroup query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VLANGroupDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    min_vid: int
    max_vid: int
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
