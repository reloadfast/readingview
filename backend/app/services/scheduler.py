import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_JOB_ID = "release_refresh"
_DIGEST_JOB_ID = "daily_digest"
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


def _parse_notify_time(t: str, timezone: str) -> CronTrigger:
    parts = t.split(":")
    if len(parts) != 2:  # noqa: PLR2004
        raise ValueError(f"Invalid notify_time: {t!r}")
    return CronTrigger(hour=int(parts[0]), minute=int(parts[1]), timezone=timezone)


async def _refresh_job() -> None:
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    from ..db import _AsyncSession
    from ..models.settings import Settings
    from ..services import notify as notify_svc
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
        from ..crypto import decrypt

        try:
            url = decrypt(apprise_url_enc)
            n = result.added
            await notify_svc.send(
                url,
                "New releases found",
                f"{n} new release{'s' if n != 1 else ''} added by tracked authors.",
            )
        except Exception:
            logger.exception("Failed to dispatch release notification")


async def _digest_job() -> None:
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    from ..crypto import decrypt
    from ..db import _AsyncSession
    from ..models.settings import Settings
    from ..services import notify as notify_svc

    async with _AsyncSession() as db:
        await db.execute(
            sqlite_insert(Settings).values(id=1).on_conflict_do_nothing(index_elements=["id"])
        )
        row = await db.get(Settings, 1)
        if not row or not row.notifications_enabled or not row.apprise_url:
            return
        apprise_url_enc = row.apprise_url
        days_before = row.notify_days_before

    try:
        url = decrypt(apprise_url_enc)
    except Exception:
        logger.exception("Failed to decrypt Apprise URL for digest job")
        return

    async with _AsyncSession() as db:
        releases = await notify_svc.upcoming_releases(db, days_before)

    if not releases:
        logger.debug("Digest job: no upcoming releases within %d days, skipping", days_before)
        return

    subject, body = notify_svc.build_digest(releases, days_before)
    try:
        await notify_svc.send(url, subject, body)
        logger.info("Digest notification sent: %d upcoming release(s)", len(releases))
    except Exception:
        logger.exception("Failed to send digest notification")


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


def reschedule_digest(notify_time: str, timezone: str) -> None:
    if _scheduler is None:
        return
    try:
        trigger = _parse_notify_time(notify_time, timezone)
        if _scheduler.get_job(_DIGEST_JOB_ID):
            _scheduler.reschedule_job(_DIGEST_JOB_ID, trigger=trigger)
        else:
            _scheduler.add_job(_digest_job, trigger=trigger, id=_DIGEST_JOB_ID)
        logger.info("Digest scheduler set: %s (%s)", notify_time, timezone)
    except Exception:
        logger.exception("Failed to reschedule digest job")


async def start(
    refresh_cron: str, notify_time: str = "09:00", notify_timezone: str = "UTC"
) -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.start()
    reschedule_refresh(refresh_cron)
    reschedule_digest(notify_time, notify_timezone)
    logger.info(
        "Scheduler started (refresh: %s, digest: %s %s)", refresh_cron, notify_time, notify_timezone
    )


def stop() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Scheduler stopped")
