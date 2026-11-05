"""CLI compatibility checks against the shared Goodreads service."""

import json
from unittest.mock import AsyncMock

import pytest

from app.services import goodreads, goodreads_probe

URL = "https://www.goodreads.com/book/show/257149406-bog-standard-isekai"


@pytest.mark.parametrize(
    ("html", "exit_code"),
    [
        ('<script type="application/ld+json">{"@type":"Book","name":"Sample"}</script>', 0),
        ("In order to continue, we need to verify that you're not a robot.", 1),
        ("<html>No metadata</html>", 1),
    ],
)
def test_saved_html_matches_service_output(tmp_path, monkeypatch, capsys, html, exit_code):
    saved = tmp_path / "book.html"
    saved.write_text(html)
    monkeypatch.setattr("sys.argv", ["goodreads_probe", URL, "--html", str(saved)])
    assert goodreads_probe.main() == exit_code
    assert json.loads(capsys.readouterr().out) == goodreads.parse_page(html, URL)


@pytest.mark.parametrize("status", ["ok", "partial", "blocked", "network_error", "too_large"])
def test_live_lookup_preserves_report_and_exit_code(monkeypatch, capsys, status):
    report = {"status": status, "url": goodreads.canonical_url(URL)}
    lookup = AsyncMock(return_value=report)
    monkeypatch.setattr(goodreads_probe, "probe", lookup)
    monkeypatch.setattr("sys.argv", ["goodreads_probe", URL])
    assert goodreads_probe.main() == (0 if status in {"ok", "partial"} else 1)
    assert json.loads(capsys.readouterr().out) == report
    lookup.assert_awaited_once_with(goodreads.canonical_url(URL))


def test_invalid_url_is_rejected_without_fetching_or_exposing_credentials(monkeypatch, capsys):
    lookup = AsyncMock()
    monkeypatch.setattr(goodreads_probe, "probe", lookup)
    monkeypatch.setattr(
        "sys.argv", ["goodreads_probe", "https://user:secret@www.goodreads.com/book/show/123"]
    )
    with pytest.raises(SystemExit) as exc:
        goodreads_probe.main()
    assert exc.value.code == 2
    assert "secret" not in capsys.readouterr().err
    lookup.assert_not_awaited()


def test_saved_html_size_limit(tmp_path, monkeypatch, capsys):
    saved = tmp_path / "large.html"
    saved.write_bytes(b"x" * (goodreads.MAX_BYTES + 1))
    monkeypatch.setattr("sys.argv", ["goodreads_probe", URL, "--html", str(saved)])
    with pytest.raises(SystemExit) as exc:
        goodreads_probe.main()
    assert exc.value.code == 2
    assert "5 MiB" in capsys.readouterr().err
