from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.aggregate import AggregateRoot

from ipam.domain.events import ServiceCreated, ServiceDeleted, ServiceUpdated
from ipam.domain.value_objects import ServiceProtocol


class Service(AggregateRoot):
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        super().__init__(aggregate_id)
        self.name: str = ""
        self.protocol: ServiceProtocol = ServiceProtocol.TCP
        self.ports: list[int] = []
        self.ip_addresses: list[UUID] = []
        self.description: str = ""
        self.custom_fields: dict = {}
        self.tags: list[UUID] = []
        self._deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        name: str,
        protocol: ServiceProtocol,
        ports: list[int],
        ip_addresses: list[UUID] | None = None,
        description: str = "",
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> Service:
        cls._validate_ports(ports)
        aggregate = cls()
        aggregate.apply_event(
            ServiceCreated(
                aggregate_id=aggregate.id,
                version=aggregate._next_version(),
                name=name,
                protocol=protocol.value,
                ports=ports,
                ip_addresses=ip_addresses or [],
                description=description,
                custom_fields=custom_fields or {},
                tags=tags or [],
            )
        )
        return aggregate

    def update(
        self,
        *,
        name: str | None = None,
        protocol: str | None = None,
        ports: list[int] | None = None,
        ip_addresses: list[UUID] | None = None,
        description: str | None = None,
        custom_fields: dict | None = None,
        tags: list[UUID] | None = None,
    ) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Cannot update a deleted Service")
        if ports is not None:
            self._validate_ports(ports)
        self.apply_event(
            ServiceUpdated(
                aggregate_id=self.id,
                version=self._next_version(),
                name=name,
                protocol=protocol,
                ports=ports,
                ip_addresses=ip_addresses,
                description=description,
                custom_fields=custom_fields,
                tags=tags,
            )
        )

    def delete(self) -> None:
        if self._deleted:
            raise BusinessRuleViolationError("Service is already deleted")
        self.apply_event(
            ServiceDeleted(
                aggregate_id=self.id,
                version=self._next_version(),
            )
        )

    @staticmethod
    def _validate_ports(ports: list[int]) -> None:
        if not ports:
            raise BusinessRuleViolationError("Service must have at least one port")
        for port in ports:
            if not 1 <= port <= 65535:
                raise BusinessRuleViolationError(f"Port must be between 1 and 65535, got {port}")

    # --- Event Handlers ---

    def _apply_ServiceCreated(self, event: ServiceCreated) -> None:  # noqa: N802
        self.name = event.name
        self.protocol = ServiceProtocol(event.protocol)
        self.ports = list(event.ports)
        self.ip_addresses = list(event.ip_addresses)
        self.description = event.description
        self.custom_fields = event.custom_fields
        self.tags = list(event.tags)

    def _apply_ServiceUpdated(self, event: ServiceUpdated) -> None:  # noqa: N802
        if event.name is not None:
            self.name = event.name
        if event.protocol is not None:
            self.protocol = ServiceProtocol(event.protocol)
        if event.ports is not None:
            self.ports = list(event.ports)
        if event.ip_addresses is not None:
            self.ip_addresses = list(event.ip_addresses)
        if event.description is not None:
            self.description = event.description
        if event.custom_fields is not None:
            self.custom_fields = event.custom_fields
        if event.tags is not None:
            self.tags = list(event.tags)

    def _apply_ServiceDeleted(self, event: ServiceDeleted) -> None:  # noqa: N802
        self._deleted = True

    # --- Snapshot ---

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "protocol": self.protocol.value,
            "ports": self.ports,
            "ip_addresses": [str(ip) for ip in self.ip_addresses],
            "description": self.description,
            "custom_fields": self.custom_fields,
            "tags": [str(t) for t in self.tags],
            "deleted": self._deleted,
        }

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        aggregate = cls(aggregate_id=aggregate_id)
        aggregate.version = version
        aggregate.name = state.get("name", "")
        aggregate.protocol = ServiceProtocol(state.get("protocol", "tcp"))
        aggregate.ports = state.get("ports", [])
        aggregate.ip_addresses = [UUID(ip) for ip in state.get("ip_addresses", [])]
        aggregate.description = state.get("description", "")
        aggregate.custom_fields = state.get("custom_fields", {})
        aggregate.tags = [UUID(t) for t in state.get("tags", [])]
        aggregate._deleted = state.get("deleted", False)
        return aggregate
