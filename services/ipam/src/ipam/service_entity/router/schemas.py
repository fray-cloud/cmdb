from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateServiceRequest(BaseModel):
    name: str
    protocol: str = "tcp"
    ports: list[int] = []
    ip_addresses: list[UUID] = []
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateServiceRequest(BaseModel):
    name: str | None = None
    protocol: str | None = None
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateServiceItem(BaseModel):
    id: UUID
    name: str | None = None
    protocol: str | None = None
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ServiceResponse(BaseModel):
    id: UUID
    name: str
    protocol: str
    ports: list[int]
    ip_addresses: list[UUID]
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class ServiceListResponse(BaseModel):
    items: list[ServiceResponse]
    total: int
    offset: int
    limit: int
