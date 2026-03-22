from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# --- Shared ---


class ChangeStatusRequest(BaseModel):
    status: str


class BulkCreateResponse(BaseModel):
    ids: list[UUID]
    count: int


class BulkDeleteRequest(BaseModel):
    ids: list[UUID]


class BulkUpdateResponse(BaseModel):
    updated: int


class BulkDeleteResponse(BaseModel):
    deleted: int


# --- Prefix ---


class CreatePrefixRequest(BaseModel):
    network: str
    vrf_id: UUID | None = None
    vlan_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdatePrefixRequest(BaseModel):
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdatePrefixItem(BaseModel):
    id: UUID
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class PrefixResponse(BaseModel):
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


class PrefixListResponse(BaseModel):
    items: list[PrefixResponse]
    total: int
    offset: int
    limit: int


# --- IPAddress ---


class CreateIPAddressRequest(BaseModel):
    address: str
    vrf_id: UUID | None = None
    status: str = "active"
    dns_name: str = ""
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateIPAddressRequest(BaseModel):
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateIPAddressItem(BaseModel):
    id: UUID
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class IPAddressResponse(BaseModel):
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


class IPAddressListResponse(BaseModel):
    items: list[IPAddressResponse]
    total: int
    offset: int
    limit: int


# --- VRF ---


class CreateVRFRequest(BaseModel):
    name: str
    rd: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateVRFRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVRFItem(BaseModel):
    id: UUID
    name: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VRFResponse(BaseModel):
    id: UUID
    name: str
    rd: str | None
    tenant_id: UUID | None
    description: str
    import_targets: list[UUID]
    export_targets: list[UUID]
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class VRFListResponse(BaseModel):
    items: list[VRFResponse]
    total: int
    offset: int
    limit: int


# --- VLAN ---


class CreateVLANRequest(BaseModel):
    vid: int
    name: str
    group_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateVLANRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVLANItem(BaseModel):
    id: UUID
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VLANResponse(BaseModel):
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


class VLANListResponse(BaseModel):
    items: list[VLANResponse]
    total: int
    offset: int
    limit: int


# --- IPRange ---


class CreateIPRangeRequest(BaseModel):
    start_address: str
    end_address: str
    vrf_id: UUID | None = None
    status: str = "active"
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateIPRangeRequest(BaseModel):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateIPRangeItem(BaseModel):
    id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class IPRangeResponse(BaseModel):
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


class IPRangeListResponse(BaseModel):
    items: list[IPRangeResponse]
    total: int
    offset: int
    limit: int


# --- RIR ---


class CreateRIRRequest(BaseModel):
    name: str
    is_private: bool = False
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateRIRRequest(BaseModel):
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateRIRItem(BaseModel):
    id: UUID
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class RIRResponse(BaseModel):
    id: UUID
    name: str
    is_private: bool
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class RIRListResponse(BaseModel):
    items: list[RIRResponse]
    total: int
    offset: int
    limit: int


# --- ASN ---


class CreateASNRequest(BaseModel):
    asn: int
    rir_id: UUID | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateASNRequest(BaseModel):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateASNItem(BaseModel):
    id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ASNResponse(BaseModel):
    id: UUID
    asn: int
    rir_id: UUID | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class ASNListResponse(BaseModel):
    items: list[ASNResponse]
    total: int
    offset: int
    limit: int


# --- FHRPGroup ---


class CreateFHRPGroupRequest(BaseModel):
    protocol: str
    group_id_value: int
    auth_type: str = "plaintext"
    auth_key: str = ""
    name: str = ""
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class UpdateFHRPGroupRequest(BaseModel):
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateFHRPGroupItem(BaseModel):
    id: UUID
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class FHRPGroupResponse(BaseModel):
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


class FHRPGroupListResponse(BaseModel):
    items: list[FHRPGroupResponse]
    total: int
    offset: int
    limit: int


# --- RouteTarget ---


class CreateRouteTargetRequest(BaseModel):
    name: str
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateRouteTargetRequest(BaseModel):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateRouteTargetItem(BaseModel):
    id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class RouteTargetResponse(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime


class RouteTargetListResponse(BaseModel):
    items: list[RouteTargetResponse]
    total: int
    offset: int
    limit: int


# --- VLANGroup ---


class CreateVLANGroupRequest(BaseModel):
    name: str
    slug: str
    min_vid: int = 1
    max_vid: int = 4094
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateVLANGroupRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    min_vid: int | None = None
    max_vid: int | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVLANGroupItem(BaseModel):
    id: UUID
    name: str | None = None
    description: str | None = None
    min_vid: int | None = None
    max_vid: int | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VLANGroupResponse(BaseModel):
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


class VLANGroupListResponse(BaseModel):
    items: list[VLANGroupResponse]
    total: int
    offset: int
    limit: int


# --- Service ---


class CreateServiceRequest(BaseModel):
    name: str
    protocol: str = "tcp"
    ports: list[int] = []
    ip_addresses: list[UUID] = []
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateServiceRequest(BaseModel):
    name: str | None = None
    protocol: str | None = None
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateServiceItem(BaseModel):
    id: UUID
    name: str | None = None
    protocol: str | None = None
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ServiceResponse(BaseModel):
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


class ServiceListResponse(BaseModel):
    items: list[ServiceResponse]
    total: int
    offset: int
    limit: int


# --- Saved Filter ---


class CreateSavedFilterRequest(BaseModel):
    name: str
    entity_type: str
    filter_config: dict = {}
    is_default: bool = False


class UpdateSavedFilterRequest(BaseModel):
    name: str | None = None
    filter_config: dict | None = None
    is_default: bool | None = None


class SavedFilterResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    entity_type: str
    filter_config: dict
    is_default: bool
    created_at: datetime
    updated_at: datetime


class SavedFilterListResponse(BaseModel):
    items: list[SavedFilterResponse]


# --- Global Search ---


class SearchResultResponse(BaseModel):
    entity_type: str
    entity_id: UUID
    display_text: str
    description: str
    relevance: float


class GlobalSearchResponse(BaseModel):
    results: list[SearchResultResponse]
    total: int
