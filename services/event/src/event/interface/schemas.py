from datetime import datetime
from typing import Literal
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


# --- Journal Entry ---


class CreateJournalEntryRequest(BaseModel):
    object_type: str
    object_id: UUID
    entry_type: Literal["info", "success", "warning", "danger"]
    comment: str


class JournalEntryResponse(BaseModel):
    id: UUID
    object_type: str
    object_id: UUID
    entry_type: str
    comment: str
    user_id: UUID | None
    tenant_id: UUID | None
    created_at: datetime


class JournalEntryListResponse(BaseModel):
    items: list[JournalEntryResponse]
    total: int
    offset: int
    limit: int
