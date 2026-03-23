"""Domain events emitted by the VLAN aggregate."""

from uuid import UUID

from shared.event.domain_event import DomainEvent


class VLANCreated(DomainEvent):
    vid: int
    name: str
    group_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class VLANUpdated(DomainEvent):
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VLANDeleted(DomainEvent):
    pass


class VLANStatusChanged(DomainEvent):
    old_status: str
    new_status: str
