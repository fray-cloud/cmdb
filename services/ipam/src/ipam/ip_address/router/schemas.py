"""Request and response schemas for IPAddress API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateIPAddressRequest(BaseModel):
    address: str
    vrf_id: UUID | None = None
    status: str = "active"
    dns_name: str = ""
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateIPAddressRequest(BaseModel):
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateIPAddressItem(BaseModel):
    id: UUID
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class IPAddressResponse(BaseModel):
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


class IPAddressListResponse(BaseModel):
    items: list[IPAddressResponse]
    total: int
    offset: int
    limit: int
