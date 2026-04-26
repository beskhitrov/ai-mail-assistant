"""Create email and analysis tables.

Revision ID: 0001_create_email_tables
Revises:
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_create_email_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create tables for emails and their analysis results."""
    op.create_table(
        "emails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_emails_id"), "emails", ["id"], unique=False)

    op.create_table(
        "email_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("tasks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("entities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("draft_reply", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_id"),
    )
    op.create_index(
        op.f("ix_email_analyses_email_id"),
        "email_analyses",
        ["email_id"],
        unique=False,
    )
    op.create_index(op.f("ix_email_analyses_id"), "email_analyses", ["id"], unique=False)


def downgrade() -> None:
    """Drop email analysis and email tables."""
    op.drop_index(op.f("ix_email_analyses_id"), table_name="email_analyses")
    op.drop_index(op.f("ix_email_analyses_email_id"), table_name="email_analyses")
    op.drop_table("email_analyses")
    op.drop_index(op.f("ix_emails_id"), table_name="emails")
    op.drop_table("emails")
