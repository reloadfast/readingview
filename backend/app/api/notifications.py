import logging

from fastapi import APIRouter, Depends
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..schemas.notifications import DigestPreview, DigestReleaseItem, NotificationResult
from ..services import notify as notify_svc

router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_settings(db: AsyncSession) -> Settings | None:
    async with db.begin():
        await db.execute(
            sqlite_insert(Settings).values(id=1).on_conflict_do_nothing(index_elements=["id"])
        )
        return await db.get(Settings, 1)


@router.post("/notifications/test", response_model=NotificationResult)
async def test_notification(db: AsyncSession = Depends(get_db)) -> NotificationResult:
    row = await _get_settings(db)
    if not row or not row.apprise_url:
        return NotificationResult(ok=False, error="Apprise URL not configured")
    try:
        url = decrypt(row.apprise_url)
        await notify_svc.send(
            url, "ReadingView test", "Your notification configuration is working."
        )
        return NotificationResult(ok=True)
    except Exception as exc:
        logger.warning("Test notification failed: %s", exc)
        return NotificationResult(ok=False, error=str(exc))


@router.post("/notifications/digest/preview", response_model=DigestPreview)
async def preview_digest(db: AsyncSession = Depends(get_db)) -> DigestPreview:
    row = await _get_settings(db)
    days_before = row.notify_days_before if row else 7
    releases = await notify_svc.upcoming_releases(db, days_before)
    if releases:
        subject, body = notify_svc.build_digest(releases, days_before)
    else:
        subject = "ReadingView: no upcoming releases"
        body = f"No releases in the next {days_before} day{'s' if days_before != 1 else ''}."
    return DigestPreview(
        subject=subject,
        body=body,
        count=len(releases),
        releases=[
            DigestReleaseItem(
                title=r.title,
                author_name=r.author.name,
                release_date=r.release_date,
            )
            for r in releases
        ],
    )


@router.post("/notifications/digest/send", response_model=NotificationResult)
async def send_digest(db: AsyncSession = Depends(get_db)) -> NotificationResult:
    row = await _get_settings(db)
    if not row or not row.apprise_url:
        return NotificationResult(ok=False, error="Apprise URL not configured")
    days_before = row.notify_days_before
    releases = await notify_svc.upcoming_releases(db, days_before)
    if releases:
        subject, body = notify_svc.build_digest(releases, days_before)
    else:
        subject = "ReadingView: no upcoming releases"
        body = f"No releases in the next {days_before} day{'s' if days_before != 1 else ''}."
    try:
        url = decrypt(row.apprise_url)
        await notify_svc.send(url, subject, body)
        return NotificationResult(ok=True)
    except Exception as exc:
        logger.warning("Digest send failed: %s", exc)
        return NotificationResult(ok=False, error=str(exc))
