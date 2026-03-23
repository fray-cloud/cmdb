"""Request and response schemas for VLANGroup API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateVLANGroupRequest(BaseModel):
    name: str
    slug: str
    min_vid: int = 1
    max_vid: int = 4094
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateVLANGroupRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    min_vid: int | None = None
    max_vid: int | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVLANGroupItem(BaseModel):
    id: UUID
    name: str | None = None
    description: str | None = None
    min_vid: int | None = None
    max_vid: int | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VLANGroupResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    min_vid: int
    max_vid: int
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class VLANGroupListResponse(BaseModel):
    items: list[VLANGroupResponse]
    total: int
    offset: int
    limit: int
