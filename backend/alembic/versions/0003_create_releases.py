"""create release_tracked_authors and releases tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-06

"""

import sqlite3
import time
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_DB_PATHS = [
    Path("/app/data/release_tracker.db"),
    Path("database/release_tracker.db"),
]


def upgrade() -> None:
    op.create_table(
        "release_tracked_authors",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ol_key", sa.String(), nullable=True),
        sa.Column("added_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ol_key"),
    )
    op.create_index("ix_release_tracked_authors_name", "release_tracked_authors", ["name"])

    op.create_table(
        "releases",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column(
            "author_id", sa.Integer(), sa.ForeignKey("release_tracked_authors.id"), nullable=False
        ),
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
    op.create_index("ix_releases_ol_key", "releases", ["ol_key"])

    # Migrate data from old SQLite DB if present
    old_db = next((p for p in _OLD_DB_PATHS if p.exists()), None)
    if old_db is None:
        return

    conn = op.get_bind()
    old = sqlite3.connect(str(old_db))
    old.row_factory = sqlite3.Row

    # Map old author id → new author id
    author_id_map: dict[int, int] = {}
    now_ms = int(time.time() * 1000)

    for row in old.execute(
        "SELECT id, author_name, external_id FROM tracked_authors WHERE is_active = 1"
    ):
        result = conn.execute(
            sa.text(
                "INSERT INTO release_tracked_authors (name, ol_key, added_at)"
                " VALUES (:name, :ol_key, :added_at)"
            ),
            {"name": row["author_name"], "ol_key": row["external_id"], "added_at": now_ms},
        )
        author_id_map[row["id"]] = result.lastrowid  # type: ignore[assignment]

    for row in old.execute(
        "SELECT book_title, author_id, release_date, release_date_confirmed, "
        "book_number, link_url, goodreads_url, notes, source "
        "FROM releases WHERE is_active = 1"
    ):
        new_author_id = author_id_map.get(row["author_id"])
        if new_author_id is None:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO releases (author_id, title, release_date, release_date_confirmed, "
                "book_number, link_url, notes, source, is_active) "
                "VALUES (:author_id, :title, :release_date, :confirmed,"
                " :book_number, :link_url, :notes, :source, 1)"
            ),
            {
                "author_id": new_author_id,
                "title": row["book_title"],
                "release_date": row["release_date"],
                "confirmed": bool(row["release_date_confirmed"]),
                "book_number": row["book_number"],
                "link_url": row["link_url"],
                "notes": row["notes"],
                "source": row["source"],
            },
        )

    old.close()


def downgrade() -> None:
    op.drop_index("ix_releases_ol_key", "releases")
    op.drop_table("releases")
    op.drop_index("ix_release_tracked_authors_name", "release_tracked_authors")
    op.drop_table("release_tracked_authors")
