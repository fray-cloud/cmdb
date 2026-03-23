"""Data transfer objects for Prefix query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PrefixDTO(BaseModel):
    id: UUID
    network: str
    vrf_id: UUID | None
    vlan_id: UUID | None
    status: str
    role: str | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
