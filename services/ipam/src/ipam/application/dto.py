from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PrefixDTO(BaseModel):
    id: UUID
    network: str
    vrf_id: UUID | None
    vlan_id: UUID | None
    status: str
    role: str | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class IPAddressDTO(BaseModel):
    id: UUID
    address: str
    vrf_id: UUID | None
    status: str
    dns_name: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class VRFDTO(BaseModel):
    id: UUID
    name: str
    rd: str | None
    import_targets: list[UUID]
    export_targets: list[UUID]
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class VLANDTO(BaseModel):
    id: UUID
    vid: int
    name: str
    group_id: UUID | None
    status: str
    role: str | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class IPRangeDTO(BaseModel):
    id: UUID
    start_address: str
    end_address: str
    vrf_id: UUID | None
    status: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class RIRDTO(BaseModel):
    id: UUID
    name: str
    is_private: bool
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class ASNDTO(BaseModel):
    id: UUID
    asn: int
    rir_id: UUID | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class FHRPGroupDTO(BaseModel):
    id: UUID
    protocol: str
    group_id_value: int
    auth_type: str
    name: str
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class RouteTargetDTO(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class VLANGroupDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    min_vid: int
    max_vid: int
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class ServiceDTO(BaseModel):
    id: UUID
    name: str
    protocol: str
    ports: list[int]
    ip_addresses: list[UUID]
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
