"""SQLite database for book recommender metadata and embeddings."""

import hashlib
import json
import sqlite3
import struct
from pathlib import Path
from typing import Any, Optional


class RecommenderDB:
    """SQLite-backed storage for book metadata and embeddings."""

    def __init__(self, db_path: str):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                description TEXT,
                subjects TEXT,
                isbns TEXT,
                cover_id INTEGER,
                work_key TEXT,
                content_hash TEXT
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                book_id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                model_name TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS index_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_rebuild_hash TEXT
            );
        """)
        self.conn.commit()

    @staticmethod
    def compute_content_hash(description: str, subjects: list[str]) -> str:
        """SHA256 hash of description + subjects for change detection."""
        content = (description or "") + "|" + json.dumps(sorted(subjects or []))
        return hashlib.sha256(content.encode()).hexdigest()

    # --- Books ---

    def upsert_book(
        self,
        book_id: str,
        title: str,
        authors: list[str],
        description: Optional[str] = None,
        subjects: Optional[list[str]] = None,
        isbns: Optional[list[str]] = None,
        cover_id: Optional[int] = None,
        work_key: Optional[str] = None,
    ) -> None:
        content_hash = self.compute_content_hash(description or "", subjects or [])
        self.conn.execute(
            """INSERT INTO books (id, title, authors, description, subjects, isbns, cover_id, work_key, content_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   title=excluded.title, authors=excluded.authors,
                   description=excluded.description, subjects=excluded.subjects,
                   isbns=excluded.isbns, cover_id=excluded.cover_id,
                   work_key=excluded.work_key, content_hash=excluded.content_hash""",
            (
                book_id,
                title,
                json.dumps(authors),
                description,
                json.dumps(subjects or []),
                json.dumps(isbns or []),
                cover_id,
                work_key,
                content_hash,
            ),
        )
        self.conn.commit()

    def get_book(self, book_id: str) -> Optional[dict[str, Any]]:
        cur = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._deserialize_book(row)

    def get_all_books(self) -> list[dict[str, Any]]:
        cur = self.conn.execute("SELECT * FROM books ORDER BY title")
        return [self._deserialize_book(row) for row in cur.fetchall()]

    @staticmethod
    def _deserialize_book(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        for field in ("authors", "subjects", "isbns"):
            if d.get(field):
                d[field] = json.loads(d[field])
            else:
                d[field] = []
        return d

    # --- Embeddings ---

    def upsert_embedding(
        self,
        book_id: str,
        embedding: list[float],
        model_name: str,
        content_hash: str,
    ) -> None:
        blob = struct.pack(f"{len(embedding)}f", *embedding)
        self.conn.execute(
            """INSERT INTO embeddings (book_id, embedding, model_name, content_hash)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(book_id) DO UPDATE SET
                   embedding=excluded.embedding, model_name=excluded.model_name,
                   content_hash=excluded.content_hash""",
            (book_id, blob, model_name, content_hash),
        )
        self.conn.commit()

    def get_embedding(self, book_id: str) -> Optional[list[float]]:
        cur = self.conn.execute(
            "SELECT embedding FROM embeddings WHERE book_id = ?", (book_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._deserialize_embedding(row["embedding"])

    def get_all_embeddings(self) -> list[tuple[str, list[float]]]:
        """Return list of (book_id, embedding) for all embedded books."""
        cur = self.conn.execute("SELECT book_id, embedding FROM embeddings ORDER BY book_id")
        return [
            (row["book_id"], self._deserialize_embedding(row["embedding"]))
            for row in cur.fetchall()
        ]

    @staticmethod
    def _deserialize_embedding(blob: bytes) -> list[float]:
        count = len(blob) // 4
        return list(struct.unpack(f"{count}f", blob))

    def get_stale_books(self, model_name: str) -> list[dict[str, Any]]:
        """Find books that need (re-)embedding: no embedding, wrong model, or content changed."""
        cur = self.conn.execute(
            """SELECT b.* FROM books b
               LEFT JOIN embeddings e ON b.id = e.book_id
               WHERE e.book_id IS NULL
                  OR e.model_name != ?
                  OR e.content_hash != b.content_hash""",
            (model_name,),
        )
        return [self._deserialize_book(row) for row in cur.fetchall()]

    # --- Index State ---

    def get_index_state(self) -> Optional[str]:
        cur = self.conn.execute("SELECT last_rebuild_hash FROM index_state WHERE id = 1")
        row = cur.fetchone()
        return row["last_rebuild_hash"] if row else None

    def set_index_state(self, rebuild_hash: str) -> None:
        self.conn.execute(
            """INSERT INTO index_state (id, last_rebuild_hash) VALUES (1, ?)
               ON CONFLICT(id) DO UPDATE SET last_rebuild_hash=excluded.last_rebuild_hash""",
            (rebuild_hash,),
        )
        self.conn.commit()

    def compute_embeddings_hash(self) -> str:
        """Hash of all embedding content_hashes — detects when index needs rebuild."""
        cur = self.conn.execute(
            "SELECT content_hash FROM embeddings ORDER BY book_id"
        )
        combined = "|".join(row["content_hash"] for row in cur.fetchall())
        return hashlib.sha256(combined.encode()).hexdigest()
