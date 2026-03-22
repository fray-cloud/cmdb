from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot

from ipam.domain.events import VLANGroupCreated, VLANGroupDeleted, VLANGroupUpdated


class VLANGroup(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.name: str = ""
        self.slug: str = ""
        self.min_vid: int = 1
        self.max_vid: int = 4094
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
        slug: str,
        min_vid: int = 1,
        max_vid: int = 4094,
        tenant_id: UUID | None = None,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> VLANGroup:
        cls._validate_vid_range(min_vid, max_vid)
        aggregate = cls()
        aggregate.apply_event(
            VLANGroupCreated(
                aggregate_id=aggregate.id,
                version=aggregate._next_version(),
                name=name,
                slug=slug,
                min_vid=min_vid,
                max_vid=max_vid,
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
        name: str | None = None,
        description: str | None = None,
        min_vid: int | None = None,
        max_vid: int | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted VLANGroup")
        new_min = min_vid if min_vid is not None else self.min_vid
        new_max = max_vid if max_vid is not None else self.max_vid
        if min_vid is not None or max_vid is not None:
            self._validate_vid_range(new_min, new_max)
        self.apply_event(
            VLANGroupUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                name=name,
                description=description,
                min_vid=min_vid,
                max_vid=max_vid,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("VLANGroup is already deleted")
        self.apply_event(
            VLANGroupDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    @staticmethod
    def _validate_vid_range(min_vid: int, max_vid: int) -> None:
        if not 1 <= min_vid <= 4094:
            raise BusinessRuleViolationError(f"min_vid must be between 1 and 4094, got {min_vid}")
        if not 1 <= max_vid <= 4094:
            raise BusinessRuleViolationError(f"max_vid must be between 1 and 4094, got {max_vid}")
        if min_vid > max_vid:
            raise BusinessRuleViolationError(f"min_vid ({min_vid}) must be <= max_vid ({max_vid})")

    # --- Event Handlers ---

    def _apply_VLANGroupCreated(self, event: VLANGroupCreated) -> None:  # noqa: N802
        self.name = event.name
        self.slug = event.slug
        self.min_vid = event.min_vid
        self.max_vid = event.max_vid
        self.tenant_id = event.tenant_id
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_VLANGroupUpdated(self, event: VLANGroupUpdated) -> None:  # noqa: N802
        if event.name is not None:
            self.name = event.name
        if event.description is not None:
            self.description = event.description
        if event.min_vid is not None:
            self.min_vid = event.min_vid
        if event.max_vid is not None:
            self.max_vid = event.max_vid
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_VLANGroupDeleted(self, event: VLANGroupDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "slug": self.slug,
            "min_vid": self.min_vid,
            "max_vid": self.max_vid,
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
        aggregate.name = state.get("name", "")
        aggregate.slug = state.get("slug", "")
        aggregate.min_vid = state.get("min_vid", 1)
        aggregate.max_vid = state.get("max_vid", 4094)
        aggregate.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        aggregate.description = state.get("description", "")
        aggregate.custom_fields = state.get("custom_fields", {})
        aggregate.tags = [UUID(t) for t in state.get("tags", [])]
        aggregate._deleted = state.get("deleted", False)
        return aggregate
