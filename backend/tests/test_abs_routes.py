"""ABS-dependent route tests: 503 without config, happy path with mocked client."""
from unittest.mock import AsyncMock, patch


def _mock_abs(items=None, progress=None, stats=None, sessions=None, libraries=None):
    mock = AsyncMock()
    mock.get_all_library_items.return_value = items or []
    mock.get_media_progress_map.return_value = progress or {}
    mock.get_user_listening_stats.return_value = stats or {"totalTime": 0, "items": {}}
    mock.get_user_listening_sessions.return_value = sessions or []
    mock.get_libraries.return_value = libraries or []
    mock.cover_url.side_effect = lambda item_id: f"http://abs.test/api/items/{item_id}/cover"
    return mock


async def _configure_abs(client):
    await client.patch("/api/settings", json={"abs_url": "http://abs.test", "abs_token": "t"})


# --- 503 without ABS config ---

async def test_library_503_without_config(client):
    r = await client.get("/api/library")
    assert r.status_code == 503


async def test_library_in_progress_503_without_config(client):
    r = await client.get("/api/library/in-progress")
    assert r.status_code == 503


async def test_library_item_503_without_config(client):
    r = await client.get("/api/library/some-id")
    assert r.status_code == 503


async def test_statistics_503_without_config(client):
    r = await client.get("/api/statistics")
    assert r.status_code == 503


async def test_statistics_yearly_503_without_config(client):
    r = await client.get("/api/statistics/yearly")
    assert r.status_code == 503


async def test_statistics_recap_503_without_config(client):
    r = await client.get("/api/statistics/recap")
    assert r.status_code == 503


async def test_series_list_503_without_config(client):
    r = await client.get("/api/series")
    assert r.status_code == 503


async def test_series_detail_503_without_config(client):
    r = await client.get("/api/series/The%20Expanse")
    assert r.status_code == 503


async def test_narrators_503_without_config(client):
    r = await client.get("/api/narrators")
    assert r.status_code == 503


async def test_narrator_detail_503_without_config(client):
    r = await client.get("/api/narrators/Alice%20Reader")
    assert r.status_code == 503


# --- happy path with mocked ABS ---

async def test_statistics_returns_overall_stats(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.statistics.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/statistics")
    assert r.status_code == 200
    data = r.json()
    assert "books_completed" in data
    assert "hours_listened" in data


async def test_statistics_yearly_returns_data(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.statistics.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/statistics/yearly?year=2024")
    assert r.status_code == 200
    assert r.json()["year"] == "2024"


async def test_statistics_recap_returns_data(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.statistics.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/statistics/recap?year=2024")
    assert r.status_code == 200
    assert r.json()["year"] == "2024"


async def test_narrators_list_returns_empty(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.narrators.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/narrators")
    assert r.status_code == 200
    assert r.json() == []


async def test_narrator_detail_not_found(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.narrators.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/narrators/Nobody")
    assert r.status_code == 404


async def test_series_list_returns_empty(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.series.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/series")
    assert r.status_code == 200
    assert r.json() == []


async def test_series_detail_not_found(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.series.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/series/Unknown%20Series")
    assert r.status_code == 404


async def test_library_list_returns_empty(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.library.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/library")
    assert r.status_code == 200
    assert r.json() == []


async def test_library_in_progress_returns_empty(client):
    await _configure_abs(client)
    mock = _mock_abs()
    with patch("app.api.library.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/library/in-progress")
    assert r.status_code == 200
    assert r.json() == []


async def test_library_item_not_found(client):
    await _configure_abs(client)
    mock = _mock_abs()
    mock.get_item = AsyncMock(return_value=None)
    with patch("app.api.library.AudiobookshelfClient", return_value=mock):
        r = await client.get("/api/library/no-such-id")
    assert r.status_code == 404
