"""create reading_goals table

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reading_goals",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("target_books", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("year"),
    )


def downgrade() -> None:
    op.drop_table("reading_goals")
