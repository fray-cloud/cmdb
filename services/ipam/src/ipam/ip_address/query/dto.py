"""Data transfer objects for IPAddress query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IPAddressDTO(BaseModel):
    id: UUID
    address: str
    vrf_id: UUID | None
    status: str
    dns_name: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
