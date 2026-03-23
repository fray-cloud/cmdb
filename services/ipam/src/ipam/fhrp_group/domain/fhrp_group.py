"""FHRP Group aggregate root — First Hop Redundancy Protocol group domain entity."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot

from ipam.fhrp_group.domain.events import FHRPGroupCreated, FHRPGroupDeleted, FHRPGroupUpdated
from ipam.fhrp_group.domain.value_objects import FHRPAuthType, FHRPProtocol


class FHRPGroup(AggregateRoot):
    """FHRP Group aggregate managing redundancy protocol group lifecycle via event sourcing."""

    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.protocol: FHRPProtocol | None = None
        self.group_id_value: int = 0
        self.auth_type: FHRPAuthType = FHRPAuthType.PLAINTEXT
        self.auth_key: str = ""
        self.name: str = ""
        self.description: str = ""
        self.custom_fields: dict = {}
        self.tags: list[UUID] = []
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        protocol: FHRPProtocol,
        group_id_value: int,
        auth_type: FHRPAuthType = FHRPAuthType.PLAINTEXT,
        auth_key: str = "",
        name: str = "",
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> FHRPGroup:
        """Create a new FHRP Group aggregate and emit a FHRPGroupCreated event."""
        group = cls()
        group.apply_event(
            FHRPGroupCreated(
                aggregate_id=group.id,
                version=group._next_version(),
                protocol=protocol.value,
                group_id_value=group_id_value,
                auth_type=auth_type.value,
                auth_key=auth_key,
                name=name,
                description=description,
                custom_fields=custom_fields or {},
                tags=tags or [],
            )
        )
        return group

    def update(
        self,
        *,
        name: str | None = None,
        auth_type: str | None = None,
        auth_key: str | None = None,
        description: str | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        """Update mutable FHRP Group fields and emit a FHRPGroupUpdated event."""
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted FHRP group")
        self.apply_event(
            FHRPGroupUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                name=name,
                auth_type=auth_type,
                auth_key=auth_key,
                description=description,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def delete(self) -> None:
        """Soft-delete the FHRP Group and emit a FHRPGroupDeleted event."""
        if self._deleted:
            raise BusinessRuleViolationError("FHRP group is already deleted")
        self.apply_event(
            FHRPGroupDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_FHRPGroupCreated(self, event: FHRPGroupCreated) -> None:  # noqa: N802
        self.protocol = FHRPProtocol(event.protocol)
        self.group_id_value = event.group_id_value
        self.auth_type = FHRPAuthType(event.auth_type)
        self.auth_key = event.auth_key
        self.name = event.name
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_FHRPGroupUpdated(self, event: FHRPGroupUpdated) -> None:  # noqa: N802
        if event.name is not None:
            self.name = event.name
        if event.auth_type is not None:
            self.auth_type = FHRPAuthType(event.auth_type)
        if event.auth_key is not None:
            self.auth_key = event.auth_key
        if event.description is not None:
            self.description = event.description
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_FHRPGroupDeleted(self, event: FHRPGroupDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol.value if self.protocol else None,
            "group_id_value": self.group_id_value,
            "auth_type": self.auth_type.value,
            "auth_key": self.auth_key,
            "name": self.name,
            "description": self.description,
            "custom_fields": self.custom_fields,
            "tags": [str(t) for t in self.tags],
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        group = cls(aggregate_id=aggregate_id)
        group.version = version
        group.protocol = FHRPProtocol(state["protocol"]) if state.get("protocol") else None
        group.group_id_value = state.get("group_id_value", 0)
        group.auth_type = FHRPAuthType(state["auth_type"]) if state.get("auth_type") else FHRPAuthType.PLAINTEXT
        group.auth_key = state.get("auth_key", "")
        group.name = state.get("name", "")
        group.description = state.get("description", "")
        group.custom_fields = state.get("custom_fields", {})
        group.tags = [UUID(t) for t in state.get("tags", [])]
        group._deleted = state.get("deleted", False)
        return group
