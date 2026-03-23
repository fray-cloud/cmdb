from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RouteTargetDTO(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
