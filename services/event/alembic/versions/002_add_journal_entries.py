"""add journal entries

Revision ID: 002
Revises: 001
Create Date: 2026-03-22
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "journal_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("object_type", sa.String(100), nullable=False),
        sa.Column("object_id", sa.Uuid(), nullable=False),
        sa.Column("entry_type", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_journal_object", "journal_entries", ["object_type", "object_id"])
    op.create_index("ix_journal_tenant", "journal_entries", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("journal_entries")
