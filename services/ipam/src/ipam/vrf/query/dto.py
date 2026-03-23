"""Data transfer objects for VRF query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VRFDTO(BaseModel):
    id: UUID
    name: str
    rd: str | None
    import_targets: list[UUID]
    export_targets: list[UUID]
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
