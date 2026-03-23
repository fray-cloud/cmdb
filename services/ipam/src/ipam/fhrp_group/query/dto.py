"""FHRP Group data transfer objects for query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FHRPGroupDTO(BaseModel):
    id: UUID
    protocol: str
    group_id_value: int
    auth_type: str
    name: str
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
