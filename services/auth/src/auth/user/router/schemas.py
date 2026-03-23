"""Request and response schemas for user endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from auth.user.domain import UserStatus


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    tenant_id: UUID
    display_name: str | None = Field(None, max_length=255)


class UserResponse(BaseModel):
    id: UUID
    email: str
    tenant_id: UUID
    status: UserStatus
    display_name: str | None
    role_ids: list[UUID]
    group_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    offset: int
    limit: int


class AssignRoleRequest(BaseModel):
    role_id: UUID
