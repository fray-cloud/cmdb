from typing import Any
from uuid import UUID

from pydantic import Field

from shared.domain.entity import Entity
from shared.event.domain_event import DomainEvent


class Group(Entity):
    name: str
    tenant_id: UUID
    role_ids: list[UUID] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        object.__setattr__(self, "_pending_events", [])

    def collect_events(self) -> list[DomainEvent]:
        events: list[DomainEvent] = list(self._pending_events)
        self._pending_events.clear()
        return events

    @classmethod
    def create(
        cls,
        *,
        name: str,
        tenant_id: UUID,
        role_ids: list[UUID] | None = None,
    ) -> "Group":
        return cls(name=name, tenant_id=tenant_id, role_ids=role_ids or [])
