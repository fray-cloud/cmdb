from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from auth.user.domain.user import UserStatus


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
