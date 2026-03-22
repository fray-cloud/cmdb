"""add new aggregates

Revision ID: 002
Revises: 001
Create Date: 2026-03-21
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- route_targets_read ---
    op.create_table(
        "route_targets_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_route_targets_read_name", "route_targets_read", ["name"])

    # --- vlan_groups_read ---
    op.create_table(
        "vlan_groups_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("min_vid", sa.Integer(), nullable=False),
        sa.Column("max_vid", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vlan_groups_read_name", "vlan_groups_read", ["name"])
    op.create_index("ix_vlan_groups_read_slug", "vlan_groups_read", ["slug"], unique=True)

    # --- services_read ---
    op.create_table(
        "services_read",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("protocol", sa.String(10), nullable=False),
        sa.Column("ports", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("ip_addresses", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_services_read_name", "services_read", ["name"])

    # --- Add import_targets / export_targets to vrfs_read ---
    op.add_column("vrfs_read", sa.Column("import_targets", postgresql.JSONB(), server_default="[]", nullable=False))
    op.add_column("vrfs_read", sa.Column("export_targets", postgresql.JSONB(), server_default="[]", nullable=False))


def downgrade() -> None:
    op.drop_column("vrfs_read", "export_targets")
    op.drop_column("vrfs_read", "import_targets")
    op.drop_table("services_read")
    op.drop_table("vlan_groups_read")
    op.drop_table("route_targets_read")
