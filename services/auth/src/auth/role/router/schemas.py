"""Request and response schemas for role endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PermissionSchema(BaseModel):
    object_type: str
    actions: list[str]


class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    tenant_id: UUID
    description: str | None = Field(None, max_length=1024)
    permissions: list[PermissionSchema] | None = None


class UpdateRoleRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1024)
    permissions: list[PermissionSchema] | None = None


class RoleResponse(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID
    description: str | None
    permissions: list[PermissionSchema]
    is_system: bool
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    items: list[RoleResponse]
    total: int
    offset: int
    limit: int


class PermissionCheckResponse(BaseModel):
    allowed: bool
