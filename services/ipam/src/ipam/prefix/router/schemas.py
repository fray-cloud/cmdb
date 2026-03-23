from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreatePrefixRequest(BaseModel):
    network: str
    vrf_id: UUID | None = None
    vlan_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdatePrefixRequest(BaseModel):
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdatePrefixItem(BaseModel):
    id: UUID
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class PrefixResponse(BaseModel):
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


class PrefixListResponse(BaseModel):
    items: list[PrefixResponse]
    total: int
    offset: int
    limit: int
