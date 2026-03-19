from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from ipam.domain.events import VRFCreated, VRFDeleted, VRFUpdated
from ipam.domain.value_objects import RouteDistinguisher
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot


class VRF(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.name: str = ""
        self.rd: RouteDistinguisher | None = None
        self.tenant_id: UUID | None = None
        self.description: str = ""
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        name: str,
        rd: str | None = None,
        tenant_id: UUID | None = None,
        description: str = "",
    ) -> VRF:
        vrf = cls()
        vrf.apply_event(
            VRFCreated(
                aggregate_id=vrf.id,
                version=vrf._next_version(),
                name=name,
                rd=RouteDistinguisher(rd=rd).rd if rd else None,
                tenant_id=tenant_id,
                description=description,
            )
        )
        return vrf

    def update(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted VRF")
        self.apply_event(
            VRFUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                name=name,
                description=description,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("VRF is already deleted")
        self.apply_event(
            VRFDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_VRFCreated(self, event: VRFCreated) -> None:  # noqa: N802
        self.name = event.name
        self.rd = RouteDistinguisher(rd=event.rd) if event.rd else None
        self.tenant_id = event.tenant_id
        self.description = event.description

    def _apply_VRFUpdated(self, event: VRFUpdated) -> None:  # noqa: N802
        if event.name is not None:
            self.name = event.name
        if event.description is not None:
            self.description = event.description

    def _apply_VRFDeleted(self, event: VRFDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rd": self.rd.rd if self.rd else None,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "description": self.description,
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        vrf = cls(aggregate_id=aggregate_id)
        vrf.version = version
        vrf.name = state.get("name", "")
        vrf.rd = RouteDistinguisher(rd=state["rd"]) if state.get("rd") else None
        vrf.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        vrf.description = state.get("description", "")
        vrf._deleted = state.get("deleted", False)
        return vrf
