from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from ipam.domain.events import RouteTargetCreated, RouteTargetDeleted, RouteTargetUpdated
from ipam.domain.value_objects import RouteDistinguisher
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot


class RouteTarget(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.name: RouteDistinguisher | None = None
        self.tenant_id: UUID | None = None
        self.description: str = ""
        self.custom_fields: dict = {}
        self.tags: list[UUID] = []
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        name: str,
        tenant_id: UUID | None = None,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> RouteTarget:
        name_vo = RouteDistinguisher(rd=name)
        aggregate = cls()
        aggregate.apply_event(
            RouteTargetCreated(
                aggregate_id=aggregate.id,
                version=aggregate._next_version(),
                name=name_vo.rd,
                tenant_id=tenant_id,
                description=description,
                custom_fields=custom_fields or {},
                tags=tags or [],
            )
        )
        return aggregate

    def update(
        self,
        *,
        description: str | None = None,
        tenant_id: UUID | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted RouteTarget")
        self.apply_event(
            RouteTargetUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                description=description,
                tenant_id=tenant_id,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("RouteTarget is already deleted")
        self.apply_event(
            RouteTargetDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_RouteTargetCreated(self, event: RouteTargetCreated) -> None:  # noqa: N802
        self.name = RouteDistinguisher(rd=event.name)
        self.tenant_id = event.tenant_id
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_RouteTargetUpdated(self, event: RouteTargetUpdated) -> None:  # noqa: N802
        if event.description is not None:
            self.description = event.description
        if event.tenant_id is not None:
            self.tenant_id = event.tenant_id
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_RouteTargetDeleted(self, event: RouteTargetDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name.rd if self.name else None,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "description": self.description,
            "custom_fields": self.custom_fields,
            "tags": [str(t) for t in self.tags],
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        aggregate = cls(aggregate_id=aggregate_id)
        aggregate.version = version
        aggregate.name = RouteDistinguisher(rd=state["name"]) if state.get("name") else None
        aggregate.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        aggregate.description = state.get("description", "")
        aggregate.custom_fields = state.get("custom_fields", {})
        aggregate.tags = [UUID(t) for t in state.get("tags", [])]
        aggregate._deleted = state.get("deleted", False)
        return aggregate
