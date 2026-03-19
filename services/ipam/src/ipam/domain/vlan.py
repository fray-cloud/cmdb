from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from ipam.domain.events import VLANCreated, VLANDeleted, VLANStatusChanged, VLANUpdated
from ipam.domain.value_objects import VLANId, VLANStatus
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot


class VLAN(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.vid: VLANId | None = None
        self.name: str = ""
        self.group_id: UUID | None = None
        self.status: VLANStatus = VLANStatus.ACTIVE
        self.role: str | None = None
        self.tenant_id: UUID | None = None
        self.description: str = ""
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
    ) -> VLAN:
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
            )
        )
        return vlan

    def update(
        self,
        *,
        name: str | None = None,
        role: str | None = None,
        description: str | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted VLAN")
        self.apply_event(
            VLANUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                name=name,
                role=role,
                description=description,
            )
        )

    def change_status(self, new_status: VLANStatus) -> None:
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

    def _apply_VLANUpdated(self, event: VLANUpdated) -> None:  # noqa: N802
        if event.name is not None:
            self.name = event.name
        if event.role is not None:
            self.role = event.role
        if event.description is not None:
            self.description = event.description

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
        vlan._deleted = state.get("deleted", False)
        return vlan
