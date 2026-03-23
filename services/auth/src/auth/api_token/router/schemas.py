from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
