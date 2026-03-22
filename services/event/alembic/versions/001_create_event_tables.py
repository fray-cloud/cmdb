"""create event tables

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
    # Stored Events
    op.create_table(
        "stored_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("aggregate_type", sa.String(255), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aggregate_id", "version", name="uq_event_aggregate_version"),
    )
    op.create_index("ix_stored_events_aggregate_id", "stored_events", ["aggregate_id"])
    op.create_index("ix_stored_events_aggregate_type", "stored_events", ["aggregate_type"])
    op.create_index("ix_stored_events_timestamp", "stored_events", ["timestamp"])

    # Change Logs
    op.create_table(
        "change_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("aggregate_type", sa.String(255), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("correlation_id", sa.String(255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_change_logs_aggregate_id", "change_logs", ["aggregate_id"])
    op.create_index("ix_change_logs_aggregate_type", "change_logs", ["aggregate_type"])
    op.create_index("ix_change_logs_user_id", "change_logs", ["user_id"])
    op.create_index("ix_change_logs_tenant_id", "change_logs", ["tenant_id"])
    op.create_index("ix_change_logs_timestamp", "change_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("change_logs")
    op.drop_table("stored_events")
