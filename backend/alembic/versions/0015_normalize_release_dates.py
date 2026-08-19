"""normalize release date separators

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE releases SET release_date = REPLACE(release_date, '/', '-') "
        "WHERE release_date GLOB '????/??/??'"
    )
    op.execute(
        "UPDATE manual_releases SET release_date = REPLACE(release_date, '/', '-') "
        "WHERE release_date GLOB '????/??/??'"
    )


def downgrade() -> None:
    # The ISO date representation is canonical and does not need reverting.
    pass
