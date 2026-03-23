from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot

from ipam.ip_range.domain.events import IPRangeCreated, IPRangeDeleted, IPRangeStatusChanged, IPRangeUpdated
from ipam.ip_range.domain.value_objects import IPRangeStatus
from ipam.shared.value_objects import IPAddressValue


class IPRange(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.start_address: IPAddressValue | None = None
        self.end_address: IPAddressValue | None = None
        self.vrf_id: UUID | None = None
        self.status: IPRangeStatus = IPRangeStatus.ACTIVE
        self.tenant_id: UUID | None = None
        self.description: str = ""
        self.custom_fields: dict = {}
        self.tags: list[UUID] = []
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        start_address: str,
        end_address: str,
        vrf_id: UUID | None = None,
        status: IPRangeStatus = IPRangeStatus.ACTIVE,
        tenant_id: UUID | None = None,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> IPRange:
        start = IPAddressValue(address=start_address)
        end = IPAddressValue(address=end_address)
        if start.version != end.version:
            raise BusinessRuleViolationError("Start and end addresses must be the same IP version")
        if start.ip_address >= end.ip_address:
            raise BusinessRuleViolationError("Start address must be less than end address")
        ip_range = cls()
        ip_range.apply_event(
            IPRangeCreated(
                aggregate_id=ip_range.id,
                version=ip_range._next_version(),
                start_address=start.address,
                end_address=end.address,
                vrf_id=vrf_id,
                status=status.value,
                tenant_id=tenant_id,
                description=description,
                custom_fields=custom_fields or {},
                tags=tags or [],
            )
        )
        return ip_range

    def update(
        self,
        *,
        description: str | None = None,
        tenant_id: UUID | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted IP range")
        self.apply_event(
            IPRangeUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                description=description,
                tenant_id=tenant_id,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def change_status(self, new_status: IPRangeStatus) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot change status of a deleted IP range")
        if self.status == new_status:
            raise BusinessRuleViolationError(f"IP range is already {new_status.value}")
        self.apply_event(
            IPRangeStatusChanged(
                aggregate_id=self.id,
                version=self._next_version(),
                old_status=self.status.value,
                new_status=new_status.value,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("IP range is already deleted")
        self.apply_event(
            IPRangeDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_IPRangeCreated(self, event: IPRangeCreated) -> None:  # noqa: N802
        self.start_address = IPAddressValue(address=event.start_address)
        self.end_address = IPAddressValue(address=event.end_address)
        self.vrf_id = event.vrf_id
        self.status = IPRangeStatus(event.status)
        self.tenant_id = event.tenant_id
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_IPRangeUpdated(self, event: IPRangeUpdated) -> None:  # noqa: N802
        if event.description is not None:
            self.description = event.description
        if event.tenant_id is not None:
            self.tenant_id = event.tenant_id
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_IPRangeStatusChanged(self, event: IPRangeStatusChanged) -> None:  # noqa: N802
        self.status = IPRangeStatus(event.new_status)

    def _apply_IPRangeDeleted(self, event: IPRangeDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "start_address": self.start_address.address if self.start_address else None,
            "end_address": self.end_address.address if self.end_address else None,
            "vrf_id": str(self.vrf_id) if self.vrf_id else None,
            "status": self.status.value,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "description": self.description,
            "custom_fields": self.custom_fields,
            "tags": [str(t) for t in self.tags],
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        ip_range = cls(aggregate_id=aggregate_id)
        ip_range.version = version
        ip_range.start_address = IPAddressValue(address=state["start_address"]) if state.get("start_address") else None
        ip_range.end_address = IPAddressValue(address=state["end_address"]) if state.get("end_address") else None
        ip_range.vrf_id = UUID(state["vrf_id"]) if state.get("vrf_id") else None
        ip_range.status = IPRangeStatus(state["status"])
        ip_range.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        ip_range.description = state.get("description", "")
        ip_range.custom_fields = state.get("custom_fields", {})
        ip_range.tags = [UUID(t) for t in state.get("tags", [])]
        ip_range._deleted = state.get("deleted", False)
        return ip_range
