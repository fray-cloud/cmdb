from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from auth.domain.user import UserStatus


class UserDTO(BaseModel):
    id: UUID
    email: str
    tenant_id: UUID
    status: UserStatus
    display_name: str | None
    role_ids: list[UUID]
    group_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class AuthTokenDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RoleDTO(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID
    description: str | None
    permissions: list[dict]
    is_system: bool
    created_at: datetime
    updated_at: datetime


class GroupDTO(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID
    role_ids: list[UUID]
    created_at: datetime
    updated_at: datetime


class APITokenDTO(BaseModel):
    id: UUID
    user_id: UUID
    tenant_id: UUID
    description: str | None
    scopes: list[str]
    expires_at: datetime | None
    allowed_ips: list[str]
    is_revoked: bool
    created_at: datetime
    key: str | None = None


class PermissionCheckDTO(BaseModel):
    allowed: bool
