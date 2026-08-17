"""add library sort default setting

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "settings",
        sa.Column("library_sort_default", sa.String(), nullable=False, server_default="title"),
    )


def downgrade() -> None:
    op.drop_column("settings", "library_sort_default")
