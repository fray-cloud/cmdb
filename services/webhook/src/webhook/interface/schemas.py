from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateWebhookRequest(BaseModel):
    name: str
    url: str
    secret: str
    event_types: list[str]
    tenant_id: UUID | None = None
    description: str = ""


class UpdateWebhookRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None
    description: str | None = None


class WebhookResponse(BaseModel):
    id: UUID
    name: str
    url: str
    event_types: list[str]
    is_active: bool
    tenant_id: UUID | None
    description: str
    created_at: datetime
    updated_at: datetime
    # Note: secret intentionally excluded from response


class WebhookListResponse(BaseModel):
    items: list[WebhookResponse]
    total: int
    offset: int
    limit: int


class WebhookLogResponse(BaseModel):
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


class WebhookLogListResponse(BaseModel):
    items: list[WebhookLogResponse]
    total: int
    offset: int
    limit: int
