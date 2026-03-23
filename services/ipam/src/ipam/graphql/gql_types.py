"""GraphQL Strawberry type definitions for all IPAM entities."""

import uuid
from datetime import datetime

import strawberry


@strawberry.type
class PrefixType:
    id: uuid.UUID
    network: str
    vrf_id: uuid.UUID | None
    vlan_id: uuid.UUID | None
    status: str
    role: str | None
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class IPAddressType:
    id: uuid.UUID
    address: str
    vrf_id: uuid.UUID | None
    status: str
    dns_name: str
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class VRFType:
    id: uuid.UUID
    name: str
    rd: str | None
    import_targets: list[uuid.UUID]
    export_targets: list[uuid.UUID]
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class VLANType:
    id: uuid.UUID
    vid: int
    name: str
    group_id: uuid.UUID | None
    status: str
    role: str | None
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class IPRangeType:
    id: uuid.UUID
    start_address: str
    end_address: str
    vrf_id: uuid.UUID | None
    status: str
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class RIRType:
    id: uuid.UUID
    name: str
    is_private: bool
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ASNType:
    id: uuid.UUID
    asn: int
    rir_id: uuid.UUID | None
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class FHRPGroupType:
    id: uuid.UUID
    protocol: str
    group_id_value: int
    auth_type: str
    name: str
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class RouteTargetType:
    id: uuid.UUID
    name: str
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class VLANGroupType:
    id: uuid.UUID
    name: str
    slug: str
    min_vid: int
    max_vid: int
    tenant_id: uuid.UUID | None
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ServiceType:
    id: uuid.UUID
    name: str
    protocol: str
    ports: list[int]
    ip_addresses: list[uuid.UUID]
    description: str
    custom_fields: strawberry.scalars.JSON
    tags: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
