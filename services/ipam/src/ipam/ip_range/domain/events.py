"""Domain events emitted by the IPRange aggregate."""

from uuid import UUID

from shared.event.domain_event import DomainEvent


class IPRangeCreated(DomainEvent):
    start_address: str
    end_address: str
    vrf_id: UUID | None = None
    status: str = "active"
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class IPRangeUpdated(DomainEvent):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class IPRangeDeleted(DomainEvent):
    pass


class IPRangeStatusChanged(DomainEvent):
    old_status: str
    new_status: str
