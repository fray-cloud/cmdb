from uuid import UUID

from shared.event.domain_event import DomainEvent


class PrefixCreated(DomainEvent):
    network: str
    vrf_id: UUID | None = None
    vlan_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class PrefixUpdated(DomainEvent):
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class PrefixDeleted(DomainEvent):
    pass


class PrefixStatusChanged(DomainEvent):
    old_status: str
    new_status: str
