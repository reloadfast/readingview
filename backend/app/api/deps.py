"""abs_client dependency — shared across back-end API modules.

Each route that talks to Audiobookshelf gets the client via
``Depends(abs_client)``.  When ABS is not configured the dependency
raises ``HTTPException(status_code=503)`` before the handler even runs.
The client is closed after the request completes.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..services.audiobookshelf import AudiobookshelfClient


async def abs_client(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AudiobookshelfClient, None]:
    row = await db.get(Settings, 1)
    if not row or not row.abs_url or not row.abs_token:
        raise HTTPException(status_code=503, detail="ABS connection not configured")
    client = AudiobookshelfClient(row.abs_url, decrypt(row.abs_token))
    try:
        yield client
    finally:
        await client.aclose()
