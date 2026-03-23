from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ServiceDTO(BaseModel):
    id: UUID
    name: str
    protocol: str
    ports: list[int]
    ip_addresses: list[UUID]
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
