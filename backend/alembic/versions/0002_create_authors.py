"""create tracked_authors table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tracked_authors",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ol_key", sa.String(), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("birth_date", sa.String(), nullable=True),
        sa.Column("death_date", sa.String(), nullable=True),
        sa.Column("followed_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ol_key"),
    )
    op.create_index("ix_tracked_authors_name", "tracked_authors", ["name"])


def downgrade() -> None:
    op.drop_index("ix_tracked_authors_name", "tracked_authors")
    op.drop_table("tracked_authors")
