from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class IPAMBase(DeclarativeBase):
    pass


class PrefixReadModel(IPAMBase):
    __tablename__ = "prefixes_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    network: Mapped[str] = mapped_column(String(50), index=True)
    vrf_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    vlan_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IPAddressReadModel(IPAMBase):
    __tablename__ = "ip_addresses_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    address: Mapped[str] = mapped_column(String(50), index=True)
    vrf_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    dns_name: Mapped[str] = mapped_column(String(255), default="")
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VRFReadModel(IPAMBase):
    __tablename__ = "vrfs_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    rd: Mapped[str | None] = mapped_column(String(50), nullable=True)
    import_targets: Mapped[list] = mapped_column(JSONB, default=list)
    export_targets: Mapped[list] = mapped_column(JSONB, default=list)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VLANReadModel(IPAMBase):
    __tablename__ = "vlans_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    vid: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    group_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IPRangeReadModel(IPAMBase):
    __tablename__ = "ip_ranges_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    start_address: Mapped[str] = mapped_column(String(50), index=True)
    end_address: Mapped[str] = mapped_column(String(50))
    vrf_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RIRReadModel(IPAMBase):
    __tablename__ = "rirs_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ASNReadModel(IPAMBase):
    __tablename__ = "asns_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    asn: Mapped[int] = mapped_column(Integer, index=True)
    rir_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FHRPGroupReadModel(IPAMBase):
    __tablename__ = "fhrp_groups_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    protocol: Mapped[str] = mapped_column(String(20))
    group_id_value: Mapped[int] = mapped_column(Integer)
    auth_type: Mapped[str] = mapped_column(String(20))
    auth_key: Mapped[str] = mapped_column(String(255), default="")
    name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RouteTargetReadModel(IPAMBase):
    __tablename__ = "route_targets_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VLANGroupReadModel(IPAMBase):
    __tablename__ = "vlan_groups_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    min_vid: Mapped[int] = mapped_column(Integer)
    max_vid: Mapped[int] = mapped_column(Integer)
    tenant_id: Mapped[UUID | None] = mapped_column(SAUUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ServiceReadModel(IPAMBase):
    __tablename__ = "services_read"

    id: Mapped[UUID] = mapped_column(SAUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    protocol: Mapped[str] = mapped_column(String(10))
    ports: Mapped[list] = mapped_column(JSONB, default=list)
    ip_addresses: Mapped[list] = mapped_column(JSONB, default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
