from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
