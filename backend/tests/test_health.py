from unittest.mock import AsyncMock, MagicMock

async def test_health_ok(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


async def test_health_db_failure(client, monkeypatch):
    import app.api.health as health_module

    mock_engine = MagicMock()
    mock_engine.connect.return_value.__aenter__ = AsyncMock(
        side_effect=Exception("DB connection failed")
    )
    mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(health_module, "engine", mock_engine)

    r = await client.get("/api/health")
    assert r.status_code == 503
    data = r.json()
    assert data["status"] == "unhealthy"
    assert "DB connection failed" in data["detail"]
