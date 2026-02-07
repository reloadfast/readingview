"""
SQLite database for tracking upcoming book releases.
"""

import sqlite3
from pathlib import Path
from typing import Any, Optional


DB_PATH = Path("/app/data/release_tracker.db")


class ReleaseTrackerDB:
    """SQLite-backed storage for tracked authors, series, and releases."""

    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS tracked_authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_name TEXT NOT NULL,
                external_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tracked_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_name TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                external_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES tracked_authors(id)
            );

            CREATE TABLE IF NOT EXISTS notification_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_title TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                series_id INTEGER,
                release_date TEXT,
                release_date_confirmed INTEGER DEFAULT 0,
                book_number TEXT,
                link_url TEXT,
                goodreads_url TEXT,
                amazon_url TEXT,
                notes TEXT,
                source TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES tracked_authors(id),
                FOREIGN KEY (series_id) REFERENCES tracked_series(id)
            );

            CREATE TABLE IF NOT EXISTS book_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_item_id TEXT NOT NULL UNIQUE,
                note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS collection_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                library_item_id TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collection_id) REFERENCES collections(id),
                UNIQUE(collection_id, library_item_id)
            );
        """)
        # Migration: add link_url if missing (existing DBs)
        try:
            self.conn.execute("ALTER TABLE releases ADD COLUMN link_url TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
        self.conn.commit()

    # --- Authors ---

    def get_tracked_authors(self) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, author_name, external_id FROM tracked_authors WHERE is_active = 1 ORDER BY author_name"
        )
        return [dict(row) for row in cur.fetchall()]

    def add_tracked_author(self, author_name: str, external_id: Optional[str] = None) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO tracked_authors (author_name, external_id) VALUES (?, ?)",
            (author_name, external_id),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def remove_tracked_author(self, author_id: int):
        cur = self.conn.cursor()
        cur.execute("UPDATE tracked_authors SET is_active = 0 WHERE id = ?", (author_id,))
        cur.execute("UPDATE tracked_series SET is_active = 0 WHERE author_id = ?", (author_id,))
        cur.execute("UPDATE releases SET is_active = 0 WHERE author_id = ?", (author_id,))
        self.conn.commit()

    # --- Series ---

    def get_tracked_series(self, author_id: int) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, series_name, external_id FROM tracked_series WHERE author_id = ? AND is_active = 1 ORDER BY series_name",
            (author_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def add_tracked_series(self, series_name: str, author_id: int, external_id: Optional[str] = None) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO tracked_series (series_name, author_id, external_id) VALUES (?, ?, ?)",
            (series_name, author_id, external_id),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    # --- Releases ---

    def get_upcoming_releases(
        self,
        author_id: Optional[int] = None,
        sort_by: str = "release_date",
    ) -> list[dict[str, Any]]:
        query = """
            SELECT r.id, r.book_title, a.author_name, s.series_name,
                   r.book_number, r.release_date, r.release_date_confirmed,
                   r.link_url, r.goodreads_url, r.amazon_url, r.notes, r.source
            FROM releases r
            JOIN tracked_authors a ON r.author_id = a.id
            LEFT JOIN tracked_series s ON r.series_id = s.id
            WHERE r.is_active = 1
        """
        params: list[Any] = []

        if author_id is not None:
            query += " AND r.author_id = ?"
            params.append(author_id)

        sort_column = {
            "release_date": "r.release_date",
            "author_name": "a.author_name",
            "book_title": "r.book_title",
        }.get(sort_by, "r.release_date")

        query += f" ORDER BY {sort_column} ASC NULLS LAST"

        cur = self.conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def get_next_releases(self, limit: int = 3) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT r.id, r.book_title, a.author_name, s.series_name,
                   r.book_number, r.release_date, r.release_date_confirmed,
                   r.link_url, r.goodreads_url, r.amazon_url, r.notes
            FROM releases r
            JOIN tracked_authors a ON r.author_id = a.id
            LEFT JOIN tracked_series s ON r.series_id = s.id
            WHERE r.is_active = 1 AND r.release_date >= date('now')
            ORDER BY r.release_date ASC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]

    def add_release(
        self,
        book_title: str,
        author_id: int,
        series_id: Optional[int] = None,
        release_date: Optional[str] = None,
        release_date_confirmed: bool = False,
        book_number: Optional[str] = None,
        link_url: Optional[str] = None,
        goodreads_url: Optional[str] = None,
        amazon_url: Optional[str] = None,
        notes: Optional[str] = None,
        source: Optional[str] = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO releases
                (book_title, author_id, series_id, release_date, release_date_confirmed,
                 book_number, link_url, goodreads_url, amazon_url, notes, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book_title, author_id, series_id, release_date,
                int(release_date_confirmed), book_number, link_url,
                goodreads_url, amazon_url, notes, source,
            ),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def update_release(self, release_id: int, **fields: Any):
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [release_id]
        cur = self.conn.cursor()
        cur.execute(f"UPDATE releases SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def delete_release(self, release_id: int):
        cur = self.conn.cursor()
        cur.execute("UPDATE releases SET is_active = 0 WHERE id = ?", (release_id,))
        self.conn.commit()

    # --- Notification Config ---

    _NOTIFICATION_DEFAULTS: dict[str, str] = {
        "frequency": "daily",          # daily | weekly | per-event
        "days_before_release": "7",
        "notify_new_books": "true",
    }

    def get_notification_setting(self, key: str) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM notification_config WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return row["value"]
        return self._NOTIFICATION_DEFAULTS.get(key, "")

    def set_notification_setting(self, key: str, value: str):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO notification_config (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def get_all_notification_settings(self) -> dict[str, str]:
        settings = dict(self._NOTIFICATION_DEFAULTS)
        cur = self.conn.cursor()
        cur.execute("SELECT key, value FROM notification_config")
        for row in cur.fetchall():
            settings[row["key"]] = row["value"]
        return settings

    # --- Book Notes ---

    def get_book_note(self, library_item_id: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT note FROM book_notes WHERE library_item_id = ?",
            (library_item_id,),
        )
        row = cur.fetchone()
        return row["note"] if row else None

    def set_book_note(self, library_item_id: str, note: str):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO book_notes (library_item_id, note, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(library_item_id) DO UPDATE SET note = excluded.note, updated_at = CURRENT_TIMESTAMP",
            (library_item_id, note),
        )
        self.conn.commit()

    def delete_book_note(self, library_item_id: str):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM book_notes WHERE library_item_id = ?", (library_item_id,))
        self.conn.commit()

    def get_all_book_notes(self) -> dict[str, str]:
        cur = self.conn.cursor()
        cur.execute("SELECT library_item_id, note FROM book_notes")
        return {row["library_item_id"]: row["note"] for row in cur.fetchall()}

    def search_book_notes(self, query: str) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT library_item_id, note FROM book_notes WHERE note LIKE ?",
            (f"%{query}%",),
        )
        return [dict(row) for row in cur.fetchall()]

    # --- Collections ---

    def get_collections(self) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT c.id, c.name, c.description, c.created_at, "
            "COUNT(ci.id) AS item_count "
            "FROM collections c LEFT JOIN collection_items ci ON c.id = ci.collection_id "
            "GROUP BY c.id ORDER BY c.name"
        )
        return [dict(row) for row in cur.fetchall()]

    def create_collection(self, name: str, description: str = "") -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO collections (name, description) VALUES (?, ?)",
            (name, description),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def delete_collection(self, collection_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM collection_items WHERE collection_id = ?", (collection_id,))
        cur.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        self.conn.commit()

    def rename_collection(self, collection_id: int, name: str, description: str = ""):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE collections SET name = ?, description = ? WHERE id = ?",
            (name, description, collection_id),
        )
        self.conn.commit()

    def get_collection_items(self, collection_id: int) -> list[str]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT library_item_id FROM collection_items WHERE collection_id = ? ORDER BY added_at",
            (collection_id,),
        )
        return [row["library_item_id"] for row in cur.fetchall()]

    def add_to_collection(self, collection_id: int, library_item_id: str):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO collection_items (collection_id, library_item_id) VALUES (?, ?)",
            (collection_id, library_item_id),
        )
        self.conn.commit()

    def remove_from_collection(self, collection_id: int, library_item_id: str):
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM collection_items WHERE collection_id = ? AND library_item_id = ?",
            (collection_id, library_item_id),
        )
        self.conn.commit()

    def get_item_collections(self, library_item_id: str) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT c.id, c.name FROM collections c "
            "JOIN collection_items ci ON c.id = ci.collection_id "
            "WHERE ci.library_item_id = ? ORDER BY c.name",
            (library_item_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    # --- Database Integrity ---

    def check_integrity(self) -> tuple[bool, str]:
        """Run PRAGMA integrity_check. Returns (ok, message)."""
        cur = self.conn.cursor()
        cur.execute("PRAGMA integrity_check")
        result = cur.fetchone()
        msg = result[0] if result else "unknown"
        return msg == "ok", msg
