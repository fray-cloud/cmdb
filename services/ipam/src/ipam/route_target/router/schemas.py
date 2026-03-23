from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateRouteTargetRequest(BaseModel):
    name: str
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateRouteTargetRequest(BaseModel):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateRouteTargetItem(BaseModel):
    id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class RouteTargetResponse(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class RouteTargetListResponse(BaseModel):
    items: list[RouteTargetResponse]
    total: int
    offset: int
    limit: int
