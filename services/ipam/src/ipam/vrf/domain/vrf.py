"""VRF aggregate root for Virtual Routing and Forwarding instance management."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot

from ipam.shared.value_objects import RouteDistinguisher
from ipam.vrf.domain.events import VRFCreated, VRFDeleted, VRFUpdated


class VRF(AggregateRoot):
    """Aggregate root representing a Virtual Routing and Forwarding instance."""

    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.name: str = ""
        self.rd: RouteDistinguisher | None = None
        self.import_targets: list[UUID] = []
        self.export_targets: list[UUID] = []
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
        rd: str | None = None,
        import_targets: list[UUID] | None = None,
        export_targets: list[UUID] | None = None,
        tenant_id: UUID | None = None,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> VRF:
        """Create a new VRF aggregate with a validated route distinguisher."""
        vrf = cls()
        vrf.apply_event(
            VRFCreated(
                aggregate_id=vrf.id,
                version=vrf._next_version(),
                name=name,
                rd=RouteDistinguisher(rd=rd).rd if rd else None,
                import_targets=import_targets or [],
                export_targets=export_targets or [],
                tenant_id=tenant_id,
                description=description,
                custom_fields=custom_fields or {},
                tags=tags or [],
            )
        )
        return vrf

    def update(
        self,
        *,
        name: str | None = None,
        import_targets: list[UUID] | None = None,
        export_targets: list[UUID] | None = None,
        description: str | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        """Update mutable fields of the VRF."""
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted VRF")
        self.apply_event(
            VRFUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                name=name,
                import_targets=import_targets,
                export_targets=export_targets,
                description=description,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def delete(self) -> None:
        """Soft-delete the VRF by emitting a VRFDeleted event."""
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
        self.import_targets = list(event.import_targets)
        self.export_targets = list(event.export_targets)
        self.tenant_id = event.tenant_id
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_VRFUpdated(self, event: VRFUpdated) -> None:  # noqa: N802
        if event.name is not None:
            self.name = event.name
        if event.import_targets is not None:
            self.import_targets = list(event.import_targets)
        if event.export_targets is not None:
            self.export_targets = list(event.export_targets)
        if event.description is not None:
            self.description = event.description
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_VRFDeleted(self, event: VRFDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rd": self.rd.rd if self.rd else None,
            "import_targets": [str(t) for t in self.import_targets],
            "export_targets": [str(t) for t in self.export_targets],
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "description": self.description,
            "custom_fields": self.custom_fields,
            "tags": [str(t) for t in self.tags],
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        vrf = cls(aggregate_id=aggregate_id)
        vrf.version = version
        vrf.name = state.get("name", "")
        vrf.rd = RouteDistinguisher(rd=state["rd"]) if state.get("rd") else None
        vrf.import_targets = [UUID(t) for t in state.get("import_targets", [])]
        vrf.export_targets = [UUID(t) for t in state.get("export_targets", [])]
        vrf.tenant_id = UUID(state["tenant_id"]) if state.get("tenant_id") else None
        vrf.description = state.get("description", "")
        vrf.custom_fields = state.get("custom_fields", {})
        vrf.tags = [UUID(t) for t in state.get("tags", [])]
        vrf._deleted = state.get("deleted", False)
        return vrf
