from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VLANDTO(BaseModel):
    id: UUID
    vid: int
    name: str
    group_id: UUID | None
    status: str
    role: str | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
