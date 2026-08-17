"""create manual releases

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "manual_releases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("series", sa.String(), nullable=True),
        sa.Column("release_date", sa.String(), nullable=True),
        sa.Column("media", sa.String(), nullable=True),
        sa.Column("cover_url", sa.String(), nullable=True),
        sa.Column("cover_filename", sa.String(), nullable=True),
        sa.Column("link_url", sa.String(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("last_checked_at", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="watching"),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dedupe_key", sa.String(length=64), nullable=False, unique=True),
    )


def downgrade() -> None:
    op.drop_table("manual_releases")
