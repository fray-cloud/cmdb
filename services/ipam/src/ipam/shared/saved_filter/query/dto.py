from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SavedFilterDTO(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    entity_type: str
    filter_config: dict
    is_default: bool
    created_at: datetime
    updated_at: datetime
