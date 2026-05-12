"""Unit tests for services/notify.py."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notify import _parse_release_date, build_digest, send


# ---------------------------------------------------------------------------
# _parse_release_date
# ---------------------------------------------------------------------------


def test_parse_none():
    assert _parse_release_date(None) is None


def test_parse_empty_string():
    assert _parse_release_date("") is None


def test_parse_year_only():
    assert _parse_release_date("2024") == datetime.date(2024, 1, 1)


def test_parse_year_month():
    assert _parse_release_date("2024-06") == datetime.date(2024, 6, 1)


def test_parse_full_date():
    assert _parse_release_date("2024-06-15") == datetime.date(2024, 6, 15)


def test_parse_invalid_returns_none():
    assert _parse_release_date("not-a-date") is None


def test_parse_partial_garbage():
    assert _parse_release_date("2024-99") is None


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------


def _mock_release(title: str, author: str, release_date: str | None = None) -> MagicMock:
    r = MagicMock()
    r.title = title
    r.author.name = author
    r.release_date = release_date
    return r


def test_build_digest_plural():
    releases = [
        _mock_release("Book A", "Author A", "2024-06-01"),
        _mock_release("Book B", "Author B", "2024-06-05"),
    ]
    subject, body = build_digest(releases, 7)
    assert "2 upcoming releases" in subject
    assert "Book A" in body
    assert "Author A" in body
    assert "2024-06-01" in body


def test_build_digest_singular():
    releases = [_mock_release("Only Book", "Only Author", "2024-06-01")]
    subject, body = build_digest(releases, 1)
    assert "1 upcoming release" in subject
    assert "1 day" in body
    assert "Only Book" in body


def test_build_digest_no_release_date():
    releases = [_mock_release("Undated", "Author", None)]
    _, body = build_digest(releases, 7)
    assert "Undated" in body
    assert "None" not in body


# ---------------------------------------------------------------------------
# send
# ---------------------------------------------------------------------------


async def test_send_success():
    mock_instance = MagicMock()
    mock_instance.add.return_value = True
    mock_instance.async_notify = AsyncMock(return_value=True)

    with patch("app.services.notify._apprise_lib") as mock_lib:
        mock_lib.Apprise.return_value = mock_instance
        await send("ntfy://server/topic", "Title", "Body")

    mock_instance.add.assert_called_once_with("ntfy://server/topic")
    mock_instance.async_notify.assert_called_once_with(title="Title", body="Body")


async def test_send_bad_url_raises():
    mock_instance = MagicMock()
    mock_instance.add.return_value = False

    with patch("app.services.notify._apprise_lib") as mock_lib:
        mock_lib.Apprise.return_value = mock_instance
        with pytest.raises(ValueError, match="rejected"):
            await send("invalid://url", "T", "B")


async def test_send_delivery_failure_raises():
    mock_instance = MagicMock()
    mock_instance.add.return_value = True
    mock_instance.async_notify = AsyncMock(return_value=False)

    with patch("app.services.notify._apprise_lib") as mock_lib:
        mock_lib.Apprise.return_value = mock_instance
        with pytest.raises(RuntimeError, match="failed"):
            await send("ntfy://server/topic", "T", "B")
