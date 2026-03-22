"""create ipam tables

Revision ID: 001
Revises:
Create Date: 2026-03-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Event Store Tables ---

    # domain_events
    op.create_table(
        "domain_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_events_aggregate_id", "domain_events", ["aggregate_id"])
    op.create_index(
        "ix_domain_events_agg_version",
        "domain_events",
        ["aggregate_id", "version"],
        unique=True,
    )

    # aggregate_snapshots
    op.create_table(
        "aggregate_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("aggregate_type", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_aggregate_snapshots_aggregate_id", "aggregate_snapshots", ["aggregate_id"])
    op.create_index(
        "ix_snapshots_agg_version",
        "aggregate_snapshots",
        ["aggregate_id", "version"],
        unique=True,
    )

    # --- Read Model Tables ---

    # prefixes_read
    op.create_table(
        "prefixes_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("vrf_id", sa.Uuid(), nullable=True),
        sa.Column("vlan_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prefixes_read_network", "prefixes_read", ["network"])

    # ip_addresses_read
    op.create_table(
        "ip_addresses_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("address", sa.String(50), nullable=False),
        sa.Column("vrf_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("dns_name", sa.String(255), server_default="", nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ip_addresses_read_address", "ip_addresses_read", ["address"])

    # vrfs_read
    op.create_table(
        "vrfs_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rd", sa.String(50), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vrfs_read_name", "vrfs_read", ["name"])

    # vlans_read
    op.create_table(
        "vlans_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vid", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vlans_read_vid", "vlans_read", ["vid"])

    # ip_ranges_read
    op.create_table(
        "ip_ranges_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("start_address", sa.String(50), nullable=False),
        sa.Column("end_address", sa.String(50), nullable=False),
        sa.Column("vrf_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ip_ranges_read_start_address", "ip_ranges_read", ["start_address"])

    # rirs_read
    op.create_table(
        "rirs_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_private", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rirs_read_name", "rirs_read", ["name"])

    # asns_read
    op.create_table(
        "asns_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asn", sa.Integer(), nullable=False),
        sa.Column("rir_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asns_read_asn", "asns_read", ["asn"])

    # fhrp_groups_read
    op.create_table(
        "fhrp_groups_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("protocol", sa.String(20), nullable=False),
        sa.Column("group_id_value", sa.Integer(), nullable=False),
        sa.Column("auth_type", sa.String(20), nullable=False),
        sa.Column("auth_key", sa.String(255), server_default="", nullable=False),
        sa.Column("name", sa.String(255), server_default="", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("fhrp_groups_read")
    op.drop_table("asns_read")
    op.drop_table("rirs_read")
    op.drop_table("ip_ranges_read")
    op.drop_table("vlans_read")
    op.drop_table("vrfs_read")
    op.drop_table("ip_addresses_read")
    op.drop_table("prefixes_read")
    op.drop_table("aggregate_snapshots")
    op.drop_table("domain_events")
