from uuid import UUID

from shared.event.domain_event import DomainEvent


class IPAddressCreated(DomainEvent):
    address: str
    vrf_id: UUID | None = None
    status: str = "active"
    dns_name: str = ""
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class IPAddressUpdated(DomainEvent):
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class IPAddressDeleted(DomainEvent):
    pass


class IPAddressStatusChanged(DomainEvent):
    old_status: str
    new_status: str
