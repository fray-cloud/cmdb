from uuid import UUID

from shared.cqrs.command import Command

# --- Prefix ---


class CreatePrefixCommand(Command):
    network: str
    vrf_id: UUID | None = None
    vlan_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdatePrefixCommand(Command):
    prefix_id: UUID
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangePrefixStatusCommand(Command):
    prefix_id: UUID
    status: str


class DeletePrefixCommand(Command):
    prefix_id: UUID


# --- IPAddress ---


class CreateIPAddressCommand(Command):
    address: str
    vrf_id: UUID | None = None
    status: str = "active"
    dns_name: str = ""
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateIPAddressCommand(Command):
    ip_id: UUID
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangeIPAddressStatusCommand(Command):
    ip_id: UUID
    status: str


class DeleteIPAddressCommand(Command):
    ip_id: UUID


# --- VRF ---


class CreateVRFCommand(Command):
    name: str
    rd: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateVRFCommand(Command):
    vrf_id: UUID
    name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteVRFCommand(Command):
    vrf_id: UUID


# --- VLAN ---


class CreateVLANCommand(Command):
    vid: int
    name: str
    group_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateVLANCommand(Command):
    vlan_id: UUID
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangeVLANStatusCommand(Command):
    vlan_id: UUID
    status: str


class DeleteVLANCommand(Command):
    vlan_id: UUID


# --- IPRange ---


class CreateIPRangeCommand(Command):
    start_address: str
    end_address: str
    vrf_id: UUID | None = None
    status: str = "active"
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateIPRangeCommand(Command):
    range_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangeIPRangeStatusCommand(Command):
    range_id: UUID
    status: str


class DeleteIPRangeCommand(Command):
    range_id: UUID


# --- RIR ---


class CreateRIRCommand(Command):
    name: str
    is_private: bool = False
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateRIRCommand(Command):
    rir_id: UUID
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteRIRCommand(Command):
    rir_id: UUID


# --- ASN ---


class CreateASNCommand(Command):
    asn: int
    rir_id: UUID | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateASNCommand(Command):
    asn_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteASNCommand(Command):
    asn_id: UUID


# --- FHRPGroup ---


class CreateFHRPGroupCommand(Command):
    protocol: str
    group_id_value: int
    auth_type: str = "plaintext"
    auth_key: str = ""
    name: str = ""
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateFHRPGroupCommand(Command):
    fhrp_group_id: UUID
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteFHRPGroupCommand(Command):
    fhrp_group_id: UUID
