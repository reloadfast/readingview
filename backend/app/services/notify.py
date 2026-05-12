import datetime
import logging

import apprise as _apprise_lib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


def _parse_release_date(s: str | None) -> datetime.date | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


async def upcoming_releases(db: AsyncSession, days_before: int) -> list:
    from ..models.releases import Release

    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days_before)
    async with db.begin():
        rows = (
            await db.execute(
                select(Release)
                .options(selectinload(Release.author))
                .where(Release.is_active.is_(True))
            )
        ).scalars().all()
    return sorted(
        [
            r
            for r in rows
            if (d := _parse_release_date(r.release_date)) is not None and today <= d <= cutoff
        ],
        key=lambda r: r.release_date or "",
    )


def build_digest(releases: list, days_before: int) -> tuple[str, str]:
    n = len(releases)
    subject = f"ReadingView: {n} upcoming release{'s' if n != 1 else ''}"
    lines = [f"Upcoming releases in the next {days_before} day{'s' if days_before != 1 else ''}:\n"]
    for r in releases:
        line = f"• {r.title} — {r.author.name}"
        if r.release_date:
            line += f" ({r.release_date})"
        lines.append(line)
    return subject, "\n".join(lines)


async def send(url: str, title: str, body: str) -> None:
    """Send a notification to a plaintext Apprise URL. Raises on failure."""
    a = _apprise_lib.Apprise()
    if not a.add(url):
        raise ValueError("Apprise rejected the notification URL")
    ok = await a.async_notify(title=title, body=body)
    if not ok:
        raise RuntimeError("Apprise notification delivery failed")
    logger.info("Notification sent: %s", title)
