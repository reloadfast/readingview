import io
import os
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.engine import make_url

from ..config import settings

router = APIRouter()

_ALLOWED_FILENAMES = {"readingview.db"}


def _db_path() -> Path:
    database = make_url(settings.DATABASE_URL).database or ""
    return Path(database).resolve()


def _check_backup_token(authorization: str | None = Header(default=None)) -> None:
    token = settings.BACKUP_TOKEN
    if not token:
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/backup")
async def download_backup(_: None = Depends(_check_backup_token)) -> StreamingResponse:
    db = _db_path()
    if not db.exists():
        raise HTTPException(status_code=404, detail="Database file not found")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"readingview_backup_{timestamp}.tar.gz"

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(str(db), arcname=db.name)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore", status_code=200)
async def restore_backup(
    file: UploadFile,
    _: None = Depends(_check_backup_token),
) -> dict:
    max_bytes = settings.BACKUP_MAX_RESTORE_BYTES
    upload_fd, upload_path = tempfile.mkstemp(suffix=".tar.gz")
    try:
        written = 0
        with os.fdopen(upload_fd, "wb") as out:
            while True:
                chunk = await file.read(65536)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(status_code=413, detail="Upload exceeds size limit")
                out.write(chunk)

        try:
            with tarfile.open(upload_path, mode="r:gz") as tar:
                members = tar.getmembers()
                for m in members:
                    if m.name not in _ALLOWED_FILENAMES:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Unexpected file in archive: {m.name}",
                        )

                if not members:
                    raise HTTPException(status_code=400, detail="Archive is empty")

                db_member = next((m for m in members if m.name == "readingview.db"), members[0])
                f = tar.extractfile(db_member)
                if f is None:
                    raise HTTPException(status_code=400, detail="Cannot read DB from archive")

                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
                try:
                    with os.fdopen(tmp_fd, "wb") as db_out:
                        shutil.copyfileobj(f, db_out)

                    conn = sqlite3.connect(tmp_path)
                    try:
                        cur = conn.execute("PRAGMA integrity_check")
                        result = cur.fetchone()
                        if not result or result[0] != "ok":
                            msg = result[0] if result else "unknown"
                            raise HTTPException(
                                status_code=400,
                                detail=f"SQLite integrity check failed: {msg}",
                            )
                    finally:
                        conn.close()

                    target = _db_path()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(tmp_path, str(target))
                except HTTPException:
                    raise
                except Exception as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                finally:
                    try:
                        os.unlink(tmp_path)
                    except FileNotFoundError:
                        pass

        except HTTPException:
            raise
        except tarfile.TarError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid tar.gz file: {exc}") from exc

    finally:
        try:
            os.unlink(upload_path)
        except FileNotFoundError:
            pass

    from ..db import engine

    await engine.dispose()

    return {"status": "restored"}
