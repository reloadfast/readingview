from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..services.audiobookshelf import AudiobookshelfClient


async def abs_client(db: AsyncSession = Depends(get_db)) -> AudiobookshelfClient:
    row = await db.get(Settings, 1)
    if not row or not row.abs_url or not row.abs_token:
        raise HTTPException(status_code=503, detail="ABS connection not configured")
    return AudiobookshelfClient(row.abs_url, decrypt(row.abs_token))
