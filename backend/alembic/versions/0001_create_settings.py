"""create settings table

Revision ID: 0001
Revises:
Create Date: 2026-05-05

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("abs_url", sa.String(), nullable=True),
        sa.Column("abs_token", sa.String(), nullable=True),
        sa.Column("recommender_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "recommender_vector_backend", sa.String(), nullable=False, server_default="python"
        ),
        sa.Column(
            "recommender_embed_model",
            sa.String(),
            nullable=False,
            server_default="nomic-embed-text",
        ),
        sa.Column("recommender_top_k", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("recommender_min_similarity", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("llm_type", sa.String(), nullable=False, server_default="ollama"),
        sa.Column("llm_endpoint", sa.String(), nullable=True),
        sa.Column("llm_model", sa.String(), nullable=True),
        sa.Column("llm_api_key_enc", sa.String(), nullable=True),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("apprise_url", sa.String(), nullable=True),
        sa.Column("notify_days_before", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("notify_time", sa.String(), nullable=False, server_default="09:00"),
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO settings (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("settings")
