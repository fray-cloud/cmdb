from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateRIRRequest(BaseModel):
    name: str
    is_private: bool = False
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateRIRRequest(BaseModel):
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateRIRItem(BaseModel):
    id: UUID
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class RIRResponse(BaseModel):
    id: UUID
    name: str
    is_private: bool
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class RIRListResponse(BaseModel):
    items: list[RIRResponse]
    total: int
    offset: int
    limit: int
