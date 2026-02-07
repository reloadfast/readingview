"""
Lightweight notification scheduler using APScheduler.
Sends release digests on a configurable schedule (daily/weekly).
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_scheduler = None


def _send_digest_job():
    """Job function: build and send a release digest notification."""
    from config.config import config
    from database.db import ReleaseTrackerDB
    from utils.notifications import get_releases_due_soon, build_release_digest, send_notification

    if not config.APPRISE_API_URL or not config.APPRISE_NOTIFICATION_KEY:
        logger.debug("Scheduler: Apprise not configured, skipping digest.")
        return

    try:
        db = ReleaseTrackerDB(db_path=Path(config.DB_PATH))
        days = int(db.get_notification_setting("days_before_release") or "7")
        releases = get_releases_due_soon(db, days_ahead=days)
        body = build_release_digest(releases)
        if not body:
            logger.debug("Scheduler: No upcoming releases, skipping digest.")
            return

        ok, msg = send_notification(
            config.APPRISE_API_URL,
            config.APPRISE_NOTIFICATION_KEY,
            title=f"ReadingView: {len(releases)} Upcoming Release(s)",
            body=body,
        )
        if ok:
            logger.info("Scheduler: Digest sent with %d release(s).", len(releases))
        else:
            logger.warning("Scheduler: Failed to send digest: %s", msg)
    except Exception:
        logger.exception("Scheduler: Error sending digest.")


def start_scheduler(frequency: str = "daily") -> bool:
    """
    Start the background scheduler if not already running.

    Args:
        frequency: "daily" or "weekly"

    Returns:
        True if scheduler was started or is already running, False on error.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return True

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler not installed. Scheduled digests unavailable.")
        return False

    try:
        _scheduler = BackgroundScheduler(daemon=True)

        if frequency == "weekly":
            trigger = CronTrigger(day_of_week="mon", hour=9, minute=0)
        else:
            trigger = CronTrigger(hour=9, minute=0)

        _scheduler.add_job(
            _send_digest_job,
            trigger=trigger,
            id="release_digest",
            replace_existing=True,
            name=f"Release digest ({frequency})",
        )

        _scheduler.start()
        logger.info("Scheduler started: frequency=%s", frequency)
        return True
    except Exception:
        logger.exception("Failed to start scheduler.")
        return False


def stop_scheduler():
    """Stop the background scheduler if running."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
    _scheduler = None


def is_scheduler_running() -> bool:
    """Check if the scheduler is currently running."""
    return _scheduler is not None and _scheduler.running


def get_next_run_time() -> str | None:
    """Get the next scheduled run time as a string."""
    if _scheduler is None or not _scheduler.running:
        return None
    job = _scheduler.get_job("release_digest")
    if job and job.next_run_time:
        return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
    return None
