from uuid import UUID

from shared.event.domain_event import DomainEvent

# Prefix Events


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


# IPAddress Events


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


# VRF Events


class VRFCreated(DomainEvent):
    name: str
    rd: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class VRFUpdated(DomainEvent):
    name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


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


# IPRange Events


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


# RIR Events


class RIRCreated(DomainEvent):
    name: str
    is_private: bool = False
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class RIRUpdated(DomainEvent):
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class RIRDeleted(DomainEvent):
    pass


# ASN Events


class ASNCreated(DomainEvent):
    asn: int
    rir_id: UUID | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class ASNUpdated(DomainEvent):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ASNDeleted(DomainEvent):
    pass


# FHRPGroup Events


class FHRPGroupCreated(DomainEvent):
    protocol: str
    group_id_value: int
    auth_type: str = "plaintext"
    auth_key: str = ""
    name: str = ""
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class FHRPGroupUpdated(DomainEvent):
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class FHRPGroupDeleted(DomainEvent):
    pass
