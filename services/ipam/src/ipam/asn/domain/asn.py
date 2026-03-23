"""ASN aggregate root — Autonomous System Number domain entity."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot

from ipam.asn.domain.events import ASNCreated, ASNDeleted, ASNUpdated
from ipam.asn.domain.value_objects import ASNumber


class ASN(AggregateRoot):
    """Autonomous System Number aggregate managing ASN lifecycle via event sourcing."""

    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.asn: ASNumber | None = None
        self.rir_id: UUID | None = None
        self.tenant_id: UUID | None = None
        self.description: str = ""
        self.custom_fields: dict = {}
        self.tags: list[UUID] = []
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        asn: int,
        rir_id: UUID | None = None,
        tenant_id: UUID | None = None,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> ASN:
        """Create a new ASN aggregate and emit an ASNCreated event."""
        asn_vo = ASNumber(asn=asn)
        aggregate = cls()
        aggregate.apply_event(
            ASNCreated(
                aggregate_id=aggregate.id,
                version=aggregate._next_version(),
                asn=asn_vo.asn,
                rir_id=rir_id,
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
        """Update mutable ASN fields and emit an ASNUpdated event."""
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted ASN")
        self.apply_event(
            ASNUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                description=description,
                tenant_id=tenant_id,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def delete(self) -> None:
        """Soft-delete the ASN and emit an ASNDeleted event."""
        if self._deleted:
            raise BusinessRuleViolationError("ASN is already deleted")
        self.apply_event(
            ASNDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    # --- Event Handlers ---

    def _apply_ASNCreated(self, event: ASNCreated) -> None:  # noqa: N802
        self.asn = ASNumber(asn=event.asn)
        self.rir_id = event.rir_id
        self.tenant_id = event.tenant_id
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_ASNUpdated(self, event: ASNUpdated) -> None:  # noqa: N802
        if event.description is not None:
            self.description = event.description
        if event.tenant_id is not None:
            self.tenant_id = event.tenant_id
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_ASNDeleted(self, event: ASNDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "asn": self.asn.asn if self.asn else None,
            "rir_id": str(self.rir_id) if self.rir_id else None,
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
        aggregate.asn = ASNumber(asn=state["asn"]) if state.get("asn") is not None else None
        aggregate.rir_id = UUID(state["rir_id"]) if state.get("rir_id") else None
        aggregate.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        aggregate.description = state.get("description", "")
        aggregate.custom_fields = state.get("custom_fields", {})
        aggregate.tags = [UUID(t) for t in state.get("tags", [])]
        aggregate._deleted = state.get("deleted", False)
        return aggregate
