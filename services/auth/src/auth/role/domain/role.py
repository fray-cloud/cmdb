from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from shared.domain.entity import Entity
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.domain_event import DomainEvent

from auth.shared.domain.permission import Permission


class Role(Entity):
    name: str
    tenant_id: UUID
    description: str | None = None
    permissions: list[Permission] = Field(default_factory=list)
    is_system: bool = False

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
        description: str | None = None,
        permissions: list[Permission] | None = None,
    ) -> "Role":
        return cls(
            name=name,
            tenant_id=tenant_id,
            description=description,
            permissions=permissions or [],
        )

    def add_permission(self, permission: Permission) -> None:
        for p in self.permissions:
            if p.object_type == permission.object_type:
                raise BusinessRuleViolationError(
                    f"Permission for object_type '{permission.object_type}' already exists"
                )
        self.permissions.append(permission)
        self.updated_at = datetime.now()

    def remove_permission(self, object_type: str) -> None:
        original_len = len(self.permissions)
        self.permissions = [p for p in self.permissions if p.object_type != object_type]
        if len(self.permissions) == original_len:
            raise BusinessRuleViolationError(f"No permission found for object_type '{object_type}'")
        self.updated_at = datetime.now()
