"""create collections and collection_items tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-06

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "collection_items",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("collection_id", sa.Integer(), sa.ForeignKey("collections.id"), nullable=False),
        sa.Column("abs_item_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("collection_id", "abs_item_id"),
    )


def downgrade() -> None:
    op.drop_table("collection_items")
    op.drop_table("collections")
