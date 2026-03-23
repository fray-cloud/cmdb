"""Request and response schemas for VLAN API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateVLANRequest(BaseModel):
    vid: int
    name: str
    group_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateVLANRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVLANItem(BaseModel):
    id: UUID
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VLANResponse(BaseModel):
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


class VLANListResponse(BaseModel):
    items: list[VLANResponse]
    total: int
    offset: int
    limit: int
