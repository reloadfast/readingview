"""add manual release series number

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("manual_releases", sa.Column("series_number", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("manual_releases", "series_number")
