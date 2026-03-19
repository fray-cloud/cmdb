from uuid import UUID

from shared.event.domain_event import DomainEvent

# Prefix Events


class PrefixCreated(DomainEvent):
    network: str
    vrf_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""


class PrefixUpdated(DomainEvent):
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None


class PrefixDeleted(DomainEvent):
    pass


class PrefixStatusChanged(DomainEvent):
    old_status: str
    new_status: str


# IPAddress Events


class IPAddressCreated(DomainEvent):
    address: str
    vrf_id: UUID | None = None
    status: str = "active"
    dns_name: str = ""
    tenant_id: UUID | None = None
    description: str = ""


class IPAddressUpdated(DomainEvent):
    dns_name: str | None = None
    description: str | None = None


class IPAddressDeleted(DomainEvent):
    pass


class IPAddressStatusChanged(DomainEvent):
    old_status: str
    new_status: str


# VRF Events


class VRFCreated(DomainEvent):
    name: str
    rd: str | None = None
    tenant_id: UUID | None = None
    description: str = ""


class VRFUpdated(DomainEvent):
    name: str | None = None
    description: str | None = None


class VRFDeleted(DomainEvent):
    pass


# VLAN Events


class VLANCreated(DomainEvent):
    vid: int
    name: str
    group_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""


class VLANUpdated(DomainEvent):
    name: str | None = None
    role: str | None = None
    description: str | None = None


class VLANDeleted(DomainEvent):
    pass


class VLANStatusChanged(DomainEvent):
    old_status: str
    new_status: str
