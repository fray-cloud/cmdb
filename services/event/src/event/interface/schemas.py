from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StoredEventResponse(BaseModel):
    id: int
    aggregate_id: UUID
    aggregate_type: str
    event_type: str
    version: int
    payload: dict
    timestamp: datetime


class EventListResponse(BaseModel):
    items: list[StoredEventResponse]
    total: int
    offset: int
    limit: int


class ChangeLogResponse(BaseModel):
    id: int
    aggregate_id: UUID
    aggregate_type: str
    action: str
    event_type: str
    user_id: UUID | None
    tenant_id: UUID | None
    correlation_id: str | None
    timestamp: datetime


class ChangeLogListResponse(BaseModel):
    items: list[ChangeLogResponse]
    total: int
    offset: int
    limit: int
