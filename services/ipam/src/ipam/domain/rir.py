from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from ipam.domain.events import RIRCreated, RIRDeleted, RIRUpdated
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot


class RIR(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.name: str = ""
        self.is_private: bool = False
        self.description: str = ""
        self.custom_fields: dict = {}
        self.tags: list[UUID] = []
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        name: str,
        is_private: bool = False,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> RIR:
        rir = cls()
        rir.apply_event(
            RIRCreated(
                aggregate_id=rir.id,
                version=rir._next_version(),
                name=name,
                is_private=is_private,
                description=description,
                custom_fields=custom_fields or {},
                tags=tags or [],
            )
        )
        return rir

    def update(
        self,
        *,
        description: str | None = None,
        is_private: bool | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted RIR")
        self.apply_event(
            RIRUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                description=description,
                is_private=is_private,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("RIR is already deleted")
        self.apply_event(
            RIRDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_RIRCreated(self, event: RIRCreated) -> None:  # noqa: N802
        self.name = event.name
        self.is_private = event.is_private
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_RIRUpdated(self, event: RIRUpdated) -> None:  # noqa: N802
        if event.description is not None:
            self.description = event.description
        if event.is_private is not None:
            self.is_private = event.is_private
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_RIRDeleted(self, event: RIRDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "is_private": self.is_private,
            "description": self.description,
            "custom_fields": self.custom_fields,
            "tags": [str(t) for t in self.tags],
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        rir = cls(aggregate_id=aggregate_id)
        rir.version = version
        rir.name = state["name"]
        rir.is_private = state.get("is_private", False)
        rir.description = state.get("description", "")
        rir.custom_fields = state.get("custom_fields", {})
        rir.tags = [UUID(t) for t in state.get("tags", [])]
        rir._deleted = state.get("deleted", False)
        return rir
