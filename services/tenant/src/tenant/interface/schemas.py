from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from tenant.domain.tenant import TenantStatus


class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    custom_domain: str | None = None
    logo_url: str | None = None
    theme: str | None = None


class UpdateTenantSettingsRequest(BaseModel):
    custom_domain: str | None = None
    logo_url: str | None = None
    theme: str | None = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: TenantStatus
    settings: dict
    db_name: str | None
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    offset: int
    limit: int
