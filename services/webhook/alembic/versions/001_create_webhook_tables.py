"""create webhook tables

Revision ID: 001
Revises:
Create Date: 2026-03-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhooks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("event_types", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhooks_name", "webhooks", ["name"])
    op.create_index("ix_webhooks_is_active", "webhooks", ["is_active"])
    op.create_index("ix_webhooks_tenant_id", "webhooks", ["tenant_id"])

    op.create_table(
        "webhook_event_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("webhook_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("request_url", sa.Text(), nullable=False),
        sa.Column("request_body", sa.Text(), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt", sa.Integer(), server_default="1", nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_event_logs_webhook_id", "webhook_event_logs", ["webhook_id"])
    op.create_index("ix_webhook_event_logs_event_type", "webhook_event_logs", ["event_type"])
    op.create_index("ix_webhook_event_logs_event_id", "webhook_event_logs", ["event_id"])
    op.create_index("ix_webhook_event_logs_created_at", "webhook_event_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("webhook_event_logs")
    op.drop_table("webhooks")
