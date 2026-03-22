from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WebhookDTO(BaseModel):
    id: UUID
    name: str
    url: str
    secret: str
    event_types: list[str]
    is_active: bool
    tenant_id: UUID | None
    description: str
    created_at: datetime
    updated_at: datetime


class WebhookLogDTO(BaseModel):
    id: UUID
    webhook_id: UUID
    event_type: str
    event_id: str
    request_url: str
    response_status: int | None
    error_message: str | None
    attempt: int
    duration_ms: int | None
    success: bool
    created_at: datetime
