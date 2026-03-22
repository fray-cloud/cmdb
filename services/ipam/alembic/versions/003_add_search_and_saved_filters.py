"""add search vectors and saved filters

Revision ID: 003
Revises: 002
Create Date: 2026-03-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

SEARCH_VECTOR_CONFIGS = [
    (
        "prefixes_read",
        "to_tsvector('simple', coalesce(network, '') || ' ' || coalesce(description, '') || ' ' || coalesce(role, ''))",
    ),
    (
        "ip_addresses_read",
        "to_tsvector('simple', coalesce(address, '') || ' ' || coalesce(dns_name, '')"
        " || ' ' || coalesce(description, ''))",
    ),
    (
        "vrfs_read",
        "to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(rd, '') || ' ' || coalesce(description, ''))",
    ),
    (
        "vlans_read",
        "to_tsvector('simple', coalesce(name, '') || ' ' || vid::text || ' ' || coalesce(description, ''))",
    ),
    (
        "ip_ranges_read",
        "to_tsvector('simple', coalesce(start_address, '') || ' ' || coalesce(end_address, '')"
        " || ' ' || coalesce(description, ''))",
    ),
    (
        "rirs_read",
        "to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(description, ''))",
    ),
    (
        "asns_read",
        "to_tsvector('simple', asn::text || ' ' || coalesce(description, ''))",
    ),
    (
        "fhrp_groups_read",
        "to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(protocol, '')"
        " || ' ' || coalesce(description, ''))",
    ),
    (
        "route_targets_read",
        "to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(description, ''))",
    ),
    (
        "vlan_groups_read",
        "to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(slug, '') || ' ' || coalesce(description, ''))",
    ),
    (
        "services_read",
        "to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(protocol, '')"
        " || ' ' || coalesce(description, ''))",
    ),
]


def upgrade() -> None:
    # Add search_vector generated columns and GIN indexes
    for table_name, expression in SEARCH_VECTOR_CONFIGS:
        op.add_column(
            table_name,
            sa.Column(
                "search_vector",
                postgresql.TSVECTOR(),
                sa.Computed(expression, persisted=True),
                nullable=True,
            ),
        )
        op.create_index(
            f"ix_{table_name}_search",
            table_name,
            ["search_vector"],
            postgresql_using="gin",
        )

    # Create saved_filters table
    op.create_table(
        "saved_filters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("filter_config", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_filters_user_id", "saved_filters", ["user_id"])
    op.create_index("ix_saved_filters_user_entity", "saved_filters", ["user_id", "entity_type"])


def downgrade() -> None:
    op.drop_table("saved_filters")
    for table_name, _ in SEARCH_VECTOR_CONFIGS:
        op.drop_index(f"ix_{table_name}_search", table_name)
        op.drop_column(table_name, "search_vector")
