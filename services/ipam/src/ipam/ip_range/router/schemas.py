from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateIPRangeRequest(BaseModel):
    start_address: str
    end_address: str
    vrf_id: UUID | None = None
    status: str = "active"
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateIPRangeRequest(BaseModel):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateIPRangeItem(BaseModel):
    id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class IPRangeResponse(BaseModel):
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


class IPRangeListResponse(BaseModel):
    items: list[IPRangeResponse]
    total: int
    offset: int
    limit: int
