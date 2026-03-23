"""Data transfer objects for IPRange query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IPRangeDTO(BaseModel):
    id: UUID
    start_address: str
    end_address: str
    vrf_id: UUID | None
    status: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
