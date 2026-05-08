"""Tests for /api/backup and /api/restore endpoints."""

import io
import sqlite3
import tarfile
from unittest.mock import patch

import app.api.backup as backup_mod


async def test_backup_404_when_db_file_missing(client):
    # DATABASE_URL in tests points to :memory: which is not a real file path
    r = await client.get("/api/backup")
    assert r.status_code == 404


async def test_backup_streams_tar_gz(client, tmp_path):
    # Create a real SQLite file so the backup can stream it
    db_file = tmp_path / "readingview.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    with patch("app.api.backup._db_path", return_value=db_file):
        r = await client.get("/api/backup")

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/gzip"
    assert "readingview_backup_" in r.headers["content-disposition"]

    # Verify the response is a valid tar.gz
    buf = io.BytesIO(r.content)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        names = tar.getnames()
    assert "readingview.db" in names


async def test_restore_rejects_non_tar(client):
    payload = b"this is not a tar.gz"
    r = await client.post(
        "/api/restore",
        files={"file": ("backup.tar.gz", payload, "application/gzip")},
    )
    assert r.status_code in (400, 422)


async def test_restore_rejects_tar_without_db_file(client):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        data = b"not a sqlite db"
        info = tarfile.TarInfo(name="other.txt")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    buf.seek(0)

    r = await client.post(
        "/api/restore",
        files={"file": ("backup.tar.gz", buf.read(), "application/gzip")},
    )
    assert r.status_code in (400, 422)


async def test_backup_requires_token_when_configured(client, monkeypatch):
    monkeypatch.setattr(backup_mod.settings, "BACKUP_TOKEN", "secret")
    r = await client.get("/api/backup")
    assert r.status_code == 401


async def test_backup_passes_with_correct_token(client, monkeypatch, tmp_path):
    monkeypatch.setattr(backup_mod.settings, "BACKUP_TOKEN", "secret")
    db_file = tmp_path / "readingview.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    with patch("app.api.backup._db_path", return_value=db_file):
        r = await client.get("/api/backup", headers={"Authorization": "Bearer secret"})

    assert r.status_code == 200


async def test_restore_requires_token_when_configured(client, monkeypatch):
    monkeypatch.setattr(backup_mod.settings, "BACKUP_TOKEN", "secret")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz"):
        pass
    buf.seek(0)
    r = await client.post(
        "/api/restore",
        files={"file": ("backup.tar.gz", buf.read(), "application/gzip")},
    )
    assert r.status_code == 401


async def test_restore_rejects_oversized_upload(client, monkeypatch):
    monkeypatch.setattr(backup_mod.settings, "BACKUP_MAX_RESTORE_BYTES", 10)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        data = b"x" * 512
        info = tarfile.TarInfo(name="readingview.db")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    buf.seek(0)
    r = await client.post(
        "/api/restore",
        files={"file": ("backup.tar.gz", buf.read(), "application/gzip")},
    )
    assert r.status_code == 413


async def test_db_path_uses_make_url():
    from pathlib import Path

    with patch.object(backup_mod.settings, "DATABASE_URL", "sqlite+aiosqlite:////data/readingview.db"):
        p = backup_mod._db_path()
    assert p == Path("/data/readingview.db")
