"""unify followed and release-tracked authors

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    release_authors = (
        conn.execute(sa.text("SELECT id, name, ol_key, added_at FROM release_tracked_authors"))
        .mappings()
        .all()
    )
    author_ids: dict[int, int] = {}

    for release_author in release_authors:
        ol_key = release_author["ol_key"]
        if ol_key:
            followed = (
                conn.execute(
                    sa.text("SELECT id, ol_key FROM tracked_authors WHERE ol_key = :ol_key"),
                    {"ol_key": ol_key},
                )
                .mappings()
                .first()
            )
        else:
            followed = None
        if followed is None:
            followed = (
                conn.execute(
                    sa.text(
                        "SELECT id, ol_key FROM tracked_authors WHERE lower(name) = lower(:name)"
                    ),
                    {"name": release_author["name"]},
                )
                .mappings()
                .first()
            )

        if followed is None:
            result = conn.execute(
                sa.text(
                    "INSERT INTO tracked_authors "
                    "(name, ol_key, photo_url, bio, birth_date, death_date, followed_at) "
                    "VALUES (:name, :ol_key, NULL, NULL, NULL, NULL, :followed_at)"
                ),
                {
                    "name": release_author["name"],
                    "ol_key": ol_key,
                    "followed_at": release_author["added_at"],
                },
            )
            author_ids[release_author["id"]] = result.lastrowid  # type: ignore[assignment]
            continue

        author_ids[release_author["id"]] = followed["id"]
        if ol_key and followed["ol_key"] is None:
            conn.execute(
                sa.text("UPDATE tracked_authors SET ol_key = :ol_key WHERE id = :id"),
                {"ol_key": ol_key, "id": followed["id"]},
            )

    op.create_table(
        "releases_unified_authors",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("tracked_authors.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("release_date", sa.String(), nullable=True),
        sa.Column("release_date_confirmed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("book_number", sa.String(), nullable=True),
        sa.Column("ol_key", sa.String(), nullable=True),
        sa.Column("link_url", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_releases_unified_authors_ol_key", "releases_unified_authors", ["ol_key"])

    releases = conn.execute(sa.text("SELECT * FROM releases")).mappings()
    for release in releases:
        conn.execute(
            sa.text(
                "INSERT INTO releases_unified_authors "
                "(id, author_id, title, release_date, release_date_confirmed, book_number, "
                "ol_key, link_url, notes, source, is_active) "
                "VALUES (:id, :author_id, :title, :release_date, :release_date_confirmed, "
                ":book_number, :ol_key, :link_url, :notes, :source, :is_active)"
            ),
            {**dict(release), "author_id": author_ids[release["author_id"]]},
        )

    op.drop_table("releases")
    op.drop_index("ix_release_tracked_authors_name", table_name="release_tracked_authors")
    op.drop_table("release_tracked_authors")
    op.rename_table("releases_unified_authors", "releases")
    op.drop_index("ix_releases_unified_authors_ol_key", table_name="releases")
    op.create_index("ix_releases_ol_key", "releases", ["ol_key"])


def downgrade() -> None:
    # Restoring two independent author lists would require choosing how to split records.
    raise NotImplementedError("This data-consolidating migration cannot be downgraded safely")
