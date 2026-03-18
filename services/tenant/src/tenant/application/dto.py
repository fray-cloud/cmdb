from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from tenant.domain.tenant import TenantStatus


class TenantDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    status: TenantStatus
    settings: dict
    db_name: str | None
    created_at: datetime
    updated_at: datetime
