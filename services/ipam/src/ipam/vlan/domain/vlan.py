"""VLAN aggregate root for virtual LAN management."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot

from ipam.vlan.domain.events import VLANCreated, VLANDeleted, VLANStatusChanged, VLANUpdated
from ipam.vlan.domain.value_objects import VLANId, VLANStatus


class VLAN(AggregateRoot):
    """Aggregate root representing a virtual LAN within an optional VLAN group."""

    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.vid: VLANId | None = None
        self.name: str = ""
        self.group_id: UUID | None = None
        self.status: VLANStatus = VLANStatus.ACTIVE
        self.role: str | None = None
        self.tenant_id: UUID | None = None
        self.description: str = ""
        self.custom_fields: dict = {}
        self.tags: list[UUID] = []
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        vid: int,
        name: str,
        group_id: UUID | None = None,
        status: VLANStatus = VLANStatus.ACTIVE,
        role: str | None = None,
        tenant_id: UUID | None = None,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> VLAN:
        """Create a new VLAN aggregate with a validated VLAN ID."""
        vlan = cls()
        vlan.apply_event(
            VLANCreated(
                aggregate_id=vlan.id,
                version=vlan._next_version(),
                vid=VLANId(vid=vid).vid,
                name=name,
                group_id=group_id,
                status=status.value,
                role=role,
                tenant_id=tenant_id,
                description=description,
                custom_fields=custom_fields or {},
                tags=tags or [],
            )
        )
        return vlan

    def update(
        self,
        *,
        name: str | None = None,
        role: str | None = None,
        description: str | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        """Update mutable fields of the VLAN."""
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted VLAN")
        self.apply_event(
            VLANUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                name=name,
                role=role,
                description=description,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def change_status(self, new_status: VLANStatus) -> None:
        """Transition the VLAN to a new lifecycle status."""
        if self._deleted:
            raise BusinessRuleViolationError("Cannot change status of a deleted VLAN")
        if self.status == new_status:
            raise BusinessRuleViolationError(f"VLAN is already {new_status.value}")
        self.apply_event(
            VLANStatusChanged(
                aggregate_id=self.id,
                version=self._next_version(),
                old_status=self.status.value,
                new_status=new_status.value,
            )
        )

    def delete(self) -> None:
        """Soft-delete the VLAN by emitting a VLANDeleted event."""
        if self._deleted:
            raise BusinessRuleViolationError("VLAN is already deleted")
        self.apply_event(
            VLANDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_VLANCreated(self, event: VLANCreated) -> None:  # noqa: N802
        self.vid = VLANId(vid=event.vid)
        self.name = event.name
        self.group_id = event.group_id
        self.status = VLANStatus(event.status)
        self.role = event.role
        self.tenant_id = event.tenant_id
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_VLANUpdated(self, event: VLANUpdated) -> None:  # noqa: N802
        if event.name is not None:
            self.name = event.name
        if event.role is not None:
            self.role = event.role
        if event.description is not None:
            self.description = event.description
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_VLANStatusChanged(self, event: VLANStatusChanged) -> None:  # noqa: N802
        self.status = VLANStatus(event.new_status)

    def _apply_VLANDeleted(self, event: VLANDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "vid": self.vid.vid if self.vid else None,
            "name": self.name,
            "group_id": str(self.group_id) if self.group_id else None,
            "status": self.status.value,
            "role": self.role,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "description": self.description,
            "custom_fields": self.custom_fields,
            "tags": [str(t) for t in self.tags],
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        vlan = cls(aggregate_id=aggregate_id)
        vlan.version = version
        vlan.vid = VLANId(vid=state["vid"]) if state.get("vid") is not None else None
        vlan.name = state.get("name", "")
        vlan.group_id = UUID(state["group_id"]) if state.get("group_id") else None
        vlan.status = VLANStatus(state["status"])
        vlan.role = state.get("role")
        vlan.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        vlan.description = state.get("description", "")
        vlan.custom_fields = state.get("custom_fields", {})
        vlan.tags = [UUID(t) for t in state.get("tags", [])]
        vlan._deleted = state.get("deleted", False)
        return vlan
