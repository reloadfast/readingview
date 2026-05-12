"""Integration tests for POST /api/notifications/* endpoints."""

from unittest.mock import AsyncMock, patch


async def test_test_notification_no_apprise_url(client):
    r = await client.post("/api/notifications/test")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert data["error"] is not None
    assert "not configured" in data["error"].lower()


async def test_test_notification_success(client):
    await client.patch("/api/settings", json={"apprise_url": "ntfy://server/topic"})

    with patch("app.api.notifications.notify_svc.send", new_callable=AsyncMock) as mock_send:
        r = await client.post("/api/notifications/test")

    assert r.status_code == 200
    assert r.json()["ok"] is True
    mock_send.assert_called_once()
    _, kwargs = mock_send.call_args
    assert kwargs.get("title") or mock_send.call_args[0][1]


async def test_test_notification_delivery_failure(client):
    await client.patch("/api/settings", json={"apprise_url": "ntfy://server/topic"})

    with patch("app.api.notifications.notify_svc.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = RuntimeError("server unreachable")
        r = await client.post("/api/notifications/test")

    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert "server unreachable" in data["error"]


async def test_digest_preview_empty(client):
    r = await client.post("/api/notifications/digest/preview")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 0
    assert isinstance(data["releases"], list)
    assert "subject" in data
    assert "body" in data
    assert "no upcoming" in data["subject"].lower()


async def test_digest_send_no_apprise_url(client):
    r = await client.post("/api/notifications/digest/send")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert "not configured" in data["error"].lower()


async def test_digest_send_success_no_releases(client):
    await client.patch("/api/settings", json={"apprise_url": "ntfy://server/topic"})

    with patch("app.api.notifications.notify_svc.send", new_callable=AsyncMock) as mock_send:
        r = await client.post("/api/notifications/digest/send")

    assert r.status_code == 200
    assert r.json()["ok"] is True
    mock_send.assert_called_once()


async def test_digest_send_delivery_failure(client):
    await client.patch("/api/settings", json={"apprise_url": "ntfy://server/topic"})

    with patch("app.api.notifications.notify_svc.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = RuntimeError("timeout")
        r = await client.post("/api/notifications/digest/send")

    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert "timeout" in data["error"]
