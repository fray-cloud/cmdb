from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateFHRPGroupRequest(BaseModel):
    protocol: str
    group_id_value: int
    auth_type: str = "plaintext"
    auth_key: str = ""
    name: str = ""
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateFHRPGroupRequest(BaseModel):
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateFHRPGroupItem(BaseModel):
    id: UUID
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class FHRPGroupResponse(BaseModel):
    id: UUID
    protocol: str
    group_id_value: int
    auth_type: str
    name: str
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class FHRPGroupListResponse(BaseModel):
    items: list[FHRPGroupResponse]
    total: int
    offset: int
    limit: int
