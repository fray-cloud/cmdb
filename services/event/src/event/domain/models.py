from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StoredEvent(BaseModel):
    id: int | None = None
    aggregate_id: UUID
    aggregate_type: str
    event_type: str
    version: int
    payload: dict
    timestamp: datetime


class ChangeLogEntry(BaseModel):
    id: int | None = None
    aggregate_id: UUID
    aggregate_type: str
    action: str
    event_type: str
    user_id: UUID | None = None
    tenant_id: UUID | None = None
    correlation_id: str | None = None
    timestamp: datetime
