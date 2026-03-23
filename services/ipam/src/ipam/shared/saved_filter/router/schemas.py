from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateSavedFilterRequest(BaseModel):
    name: str
    entity_type: str
    filter_config: dict = {}
    is_default: bool = False


class UpdateSavedFilterRequest(BaseModel):
    name: str | None = None
    filter_config: dict | None = None
    is_default: bool | None = None


class SavedFilterResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    entity_type: str
    filter_config: dict
    is_default: bool
    created_at: datetime
    updated_at: datetime


class SavedFilterListResponse(BaseModel):
    items: list[SavedFilterResponse]
