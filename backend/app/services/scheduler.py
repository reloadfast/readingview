import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_JOB_ID = "release_refresh"
_scheduler: AsyncIOScheduler | None = None


def _parse_cron(expr: str) -> CronTrigger:
    parts = expr.strip().split()
    if len(parts) != 5:  # noqa: PLR2004
        raise ValueError(f"Invalid cron expression: {expr!r}")
    minute, hour, day, month, day_of_week = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


async def _refresh_job() -> None:
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    from ..db import _AsyncSession
    from ..models.settings import Settings
    from ..services import release_tracker as rt_svc

    async with _AsyncSession() as db:
        await db.execute(
            sqlite_insert(Settings).values(id=1).on_conflict_do_nothing(index_elements=["id"])
        )
        row = await db.get(Settings, 1)
        notifications_enabled = row.notifications_enabled if row else False
        apprise_url_enc = row.apprise_url if row else None

    async with _AsyncSession() as db:
        result = await rt_svc.run_refresh(db)

    logger.info(
        "Scheduled release refresh: added=%d skipped=%d failed=%d",
        result.added,
        result.skipped,
        result.failed,
    )

    if result.added > 0 and notifications_enabled and apprise_url_enc:
        await _dispatch_notification(apprise_url_enc, result.added)


async def _dispatch_notification(apprise_url_enc: str, added: int) -> None:
    from ..crypto import decrypt

    try:
        import apprise

        url = decrypt(apprise_url_enc)
        a = apprise.Apprise()
        a.add(url)
        title = "New releases found"
        body = f"{added} new release{'s' if added != 1 else ''} added by tracked authors."
        await a.async_notify(title=title, body=body)
        logger.info("Notification dispatched for %d new release(s)", added)
    except Exception:
        logger.exception("Failed to dispatch release notification")


def reschedule_refresh(cron: str) -> None:
    if _scheduler is None:
        return
    try:
        trigger = _parse_cron(cron)
        if _scheduler.get_job(_JOB_ID):
            _scheduler.reschedule_job(_JOB_ID, trigger=trigger)
        else:
            _scheduler.add_job(_refresh_job, trigger=trigger, id=_JOB_ID)
        logger.info("Release refresh rescheduled: %s", cron)
    except Exception:
        logger.exception("Failed to reschedule release refresh")


async def start(cron: str) -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    try:
        trigger = _parse_cron(cron)
        _scheduler.add_job(_refresh_job, trigger=trigger, id=_JOB_ID)
    except Exception:
        logger.exception("Invalid releases_refresh_cron %r — scheduler not started", cron)
        _scheduler = None
        return
    _scheduler.start()
    logger.info("Release refresh scheduler started (cron: %s)", cron)


def stop() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Release refresh scheduler stopped")
