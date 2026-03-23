from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateVRFRequest(BaseModel):
    name: str
    rd: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateVRFRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVRFItem(BaseModel):
    id: UUID
    name: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VRFResponse(BaseModel):
    id: UUID
    name: str
    rd: str | None
    tenant_id: UUID | None
    description: str
    import_targets: list[UUID]
    export_targets: list[UUID]
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class VRFListResponse(BaseModel):
    items: list[VRFResponse]
    total: int
    offset: int
    limit: int
