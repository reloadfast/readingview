"""Tests for release refresh scheduler."""

import pytest

import app.services.scheduler as sched_mod
from app.services.scheduler import _parse_cron, reschedule_refresh, start, stop


def test_parse_cron_default() -> None:
    trigger = _parse_cron("0 6 * * *")
    assert trigger is not None


def test_parse_cron_custom() -> None:
    trigger = _parse_cron("30 8 * * 1")
    assert trigger is not None


def test_parse_cron_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Invalid cron expression"):
        _parse_cron("not a cron")


def test_parse_cron_too_few_parts() -> None:
    with pytest.raises(ValueError, match="Invalid cron expression"):
        _parse_cron("0 6 * *")


def test_parse_cron_too_many_parts() -> None:
    with pytest.raises(ValueError, match="Invalid cron expression"):
        _parse_cron("0 6 * * * *")


async def test_start_creates_scheduler() -> None:
    await start("0 6 * * *")
    assert sched_mod._scheduler is not None
    assert sched_mod._scheduler.running
    stop()
    assert sched_mod._scheduler is None


async def test_stop_noop_when_not_running() -> None:
    sched_mod._scheduler = None
    stop()  # must not raise


async def test_start_invalid_cron_leaves_scheduler_none() -> None:
    await start("invalid cron expr here now!")
    assert sched_mod._scheduler is None


async def test_reschedule_noop_when_no_scheduler() -> None:
    sched_mod._scheduler = None
    reschedule_refresh("0 8 * * *")  # must not raise


async def test_reschedule_updates_existing_job() -> None:
    await start("0 6 * * *")
    reschedule_refresh("0 8 * * *")
    job = sched_mod._scheduler.get_job("release_refresh")  # type: ignore[union-attr]
    assert job is not None
    stop()
