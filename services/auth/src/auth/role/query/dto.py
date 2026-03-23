"""Role data transfer objects for query responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RoleDTO(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID
    description: str | None
    permissions: list[dict]
    is_system: bool
    created_at: datetime
    updated_at: datetime
