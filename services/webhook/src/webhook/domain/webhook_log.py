from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WebhookEventLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    webhook_id: UUID
    event_type: str
    event_id: str
    request_url: str
    request_body: str
    response_status: int | None = None
    response_body: str | None = None
    error_message: str | None = None
    attempt: int = 1
    duration_ms: int | None = None
    success: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
