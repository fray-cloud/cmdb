from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateASNRequest(BaseModel):
    asn: int
    rir_id: UUID | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateASNRequest(BaseModel):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateASNItem(BaseModel):
    id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ASNResponse(BaseModel):
    id: UUID
    asn: int
    rir_id: UUID | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class ASNListResponse(BaseModel):
    items: list[ASNResponse]
    total: int
    offset: int
    limit: int
