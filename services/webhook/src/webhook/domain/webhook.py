from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Webhook(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    url: str
    secret: str
    event_types: list[str]  # ["*"] or ["ipam.domain.events.PrefixCreated", ...]
    is_active: bool = True
    tenant_id: UUID | None = None
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def matches_event(self, event_type: str) -> bool:
        if not self.is_active:
            return False
        return "*" in self.event_types or event_type in self.event_types

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now()
