from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from auth.domain.user import UserStatus

# --- Auth ---


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    tenant_id: UUID
    display_name: str | None = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: UUID


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Users ---


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


# --- Roles ---


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


# --- API Tokens ---


class CreateAPITokenRequest(BaseModel):
    description: str | None = Field(None, max_length=1024)
    scopes: list[str] | None = None
    expires_at: datetime | None = None
    allowed_ips: list[str] | None = None


class APITokenResponse(BaseModel):
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


class APITokenListResponse(BaseModel):
    items: list[APITokenResponse]
    total: int
    offset: int
    limit: int


# --- Permissions ---


class PermissionCheckResponse(BaseModel):
    allowed: bool
