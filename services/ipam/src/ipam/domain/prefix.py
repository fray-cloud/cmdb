from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from ipam.domain.events import PrefixCreated, PrefixDeleted, PrefixStatusChanged, PrefixUpdated
from ipam.domain.value_objects import PrefixNetwork, PrefixStatus
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot


class Prefix(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.network: PrefixNetwork | None = None
        self.vrf_id: UUID | None = None
        self.status: PrefixStatus = PrefixStatus.ACTIVE
        self.role: str | None = None
        self.tenant_id: UUID | None = None
        self.description: str = ""
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        network: str,
        vrf_id: UUID | None = None,
        status: PrefixStatus = PrefixStatus.ACTIVE,
        role: str | None = None,
        tenant_id: UUID | None = None,
        description: str = "",
    ) -> Prefix:
        prefix = cls()
        prefix.apply_event(
            PrefixCreated(
                aggregate_id=prefix.id,
                version=prefix._next_version(),
                network=str(PrefixNetwork(network=network).network),
                vrf_id=vrf_id,
                status=status.value,
                role=role,
                tenant_id=tenant_id,
                description=description,
            )
        )
        return prefix

    def update(
        self,
        *,
        description: str | None = None,
        role: str | None = None,
        tenant_id: UUID | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted prefix")
        self.apply_event(
            PrefixUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                description=description,
                role=role,
                tenant_id=tenant_id,
            )
        )

    def change_status(self, new_status: PrefixStatus) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot change status of a deleted prefix")
        if self.status == new_status:
            raise BusinessRuleViolationError(f"Prefix is already {new_status.value}")
        self.apply_event(
            PrefixStatusChanged(
                aggregate_id=self.id,
                version=self._next_version(),
                old_status=self.status.value,
                new_status=new_status.value,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Prefix is already deleted")
        self.apply_event(
            PrefixDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_PrefixCreated(self, event: PrefixCreated) -> None:  # noqa: N802
        self.network = PrefixNetwork(network=event.network)
        self.vrf_id = event.vrf_id
        self.status = PrefixStatus(event.status)
        self.role = event.role
        self.tenant_id = event.tenant_id
        self.description = event.description

    def _apply_PrefixUpdated(self, event: PrefixUpdated) -> None:  # noqa: N802
        if event.description is not None:
            self.description = event.description
        if event.role is not None:
            self.role = event.role
        if event.tenant_id is not None:
            self.tenant_id = event.tenant_id

    def _apply_PrefixStatusChanged(self, event: PrefixStatusChanged) -> None:  # noqa: N802
        self.status = PrefixStatus(event.new_status)

    def _apply_PrefixDeleted(self, event: PrefixDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "network": self.network.network if self.network else None,
            "vrf_id": str(self.vrf_id) if self.vrf_id else None,
            "status": self.status.value,
            "role": self.role,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "description": self.description,
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        prefix = cls(aggregate_id=aggregate_id)
        prefix.version = version
        prefix.network = PrefixNetwork(network=state["network"]) if state.get("network") else None
        prefix.vrf_id = UUID(state["vrf_id"]) if state.get("vrf_id") else None
        prefix.status = PrefixStatus(state["status"])
        prefix.role = state.get("role")
        prefix.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        prefix.description = state.get("description", "")
        prefix._deleted = state.get("deleted", False)
        return prefix
