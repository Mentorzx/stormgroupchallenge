"""create breaches table

Revision ID: 20260610_0001
Revises:
Create Date: 2026-06-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260610_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "breaches",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("breach_date", sa.Date(), nullable=True),
        sa.Column("added_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("modified_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pwn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_path", sa.Text(), nullable=True),
        sa.Column(
            "data_classes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"
        ),
        sa.Column(
            "data_classes_normalized",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_fabricated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_retired", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_spam_list", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_malware", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_index("ix_breaches_lower_domain", "breaches", [sa.text("lower(domain)")])
    op.create_index("ix_breaches_breach_date", "breaches", ["breach_date"])
    op.create_index("ix_breaches_added_date", "breaches", ["added_date"])
    op.create_index("ix_breaches_pwn_count", "breaches", ["pwn_count"])
    op.create_index("ix_breaches_is_verified", "breaches", ["is_verified"])
    op.create_index("ix_breaches_is_sensitive", "breaches", ["is_sensitive"])
    op.create_index("ix_breaches_is_spam_list", "breaches", ["is_spam_list"])
    op.create_index(
        "ix_breaches_data_classes_normalized_gin",
        "breaches",
        ["data_classes_normalized"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_breaches_data_classes_normalized_gin", table_name="breaches")
    op.drop_index("ix_breaches_is_spam_list", table_name="breaches")
    op.drop_index("ix_breaches_is_sensitive", table_name="breaches")
    op.drop_index("ix_breaches_is_verified", table_name="breaches")
    op.drop_index("ix_breaches_pwn_count", table_name="breaches")
    op.drop_index("ix_breaches_added_date", table_name="breaches")
    op.drop_index("ix_breaches_breach_date", table_name="breaches")
    op.drop_index("ix_breaches_lower_domain", table_name="breaches")
    op.drop_table("breaches")
