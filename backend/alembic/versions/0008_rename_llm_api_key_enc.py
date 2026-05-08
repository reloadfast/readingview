"""rename llm_api_key_enc to llm_api_key for naming consistency

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-08

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("settings") as batch_op:
        batch_op.alter_column("llm_api_key_enc", new_column_name="llm_api_key")


def downgrade() -> None:
    with op.batch_alter_table("settings") as batch_op:
        batch_op.alter_column("llm_api_key", new_column_name="llm_api_key_enc")
