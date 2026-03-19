from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from ipam.domain.events import (
    IPAddressCreated,
    IPAddressDeleted,
    IPAddressStatusChanged,
    IPAddressUpdated,
)
from ipam.domain.value_objects import IPAddressStatus, IPAddressValue
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot


class IPAddress(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.address: IPAddressValue | None = None
        self.vrf_id: UUID | None = None
        self.status: IPAddressStatus = IPAddressStatus.ACTIVE
        self.dns_name: str = ""
        self.tenant_id: UUID | None = None
        self.description: str = ""
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        address: str,
        vrf_id: UUID | None = None,
        status: IPAddressStatus = IPAddressStatus.ACTIVE,
        dns_name: str = "",
        tenant_id: UUID | None = None,
        description: str = "",
    ) -> IPAddress:
        ip = cls()
        ip.apply_event(
            IPAddressCreated(
                aggregate_id=ip.id,
                version=ip._next_version(),
                address=str(IPAddressValue(address=address).address),
                vrf_id=vrf_id,
                status=status.value,
                dns_name=dns_name,
                tenant_id=tenant_id,
                description=description,
            )
        )
        return ip

    def update(
        self,
        *,
        dns_name: str | None = None,
        description: str | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted IP address")
        self.apply_event(
            IPAddressUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                dns_name=dns_name,
                description=description,
            )
        )

    def change_status(self, new_status: IPAddressStatus) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot change status of a deleted IP address")
        if self.status == new_status:
            raise BusinessRuleViolationError(f"IP address is already {new_status.value}")
        self.apply_event(
            IPAddressStatusChanged(
                aggregate_id=self.id,
                version=self._next_version(),
                old_status=self.status.value,
                new_status=new_status.value,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("IP address is already deleted")
        self.apply_event(
            IPAddressDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_IPAddressCreated(self, event: IPAddressCreated) -> None:  # noqa: N802
        self.address = IPAddressValue(address=event.address)
        self.vrf_id = event.vrf_id
        self.status = IPAddressStatus(event.status)
        self.dns_name = event.dns_name
        self.tenant_id = event.tenant_id
        self.description = event.description

    def _apply_IPAddressUpdated(self, event: IPAddressUpdated) -> None:  # noqa: N802
        if event.dns_name is not None:
            self.dns_name = event.dns_name
        if event.description is not None:
            self.description = event.description

    def _apply_IPAddressStatusChanged(self, event: IPAddressStatusChanged) -> None:  # noqa: N802
        self.status = IPAddressStatus(event.new_status)

    def _apply_IPAddressDeleted(self, event: IPAddressDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "address": self.address.address if self.address else None,
            "vrf_id": str(self.vrf_id) if self.vrf_id else None,
            "status": self.status.value,
            "dns_name": self.dns_name,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "description": self.description,
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        ip = cls(aggregate_id=aggregate_id)
        ip.version = version
        ip.address = IPAddressValue(address=state["address"]) if state.get("address") else None
        ip.vrf_id = UUID(state["vrf_id"]) if state.get("vrf_id") else None
        ip.status = IPAddressStatus(state["status"])
        ip.dns_name = state.get("dns_name", "")
        ip.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        ip.description = state.get("description", "")
        ip._deleted = state.get("deleted", False)
        return ip
