import pytest
from fastapi.responses import FileResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import get_db
from app.main import app


async def test_api_unmatched_returns_404_json(client):
    r = await client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert r.json()["detail"] == "Not Found"


@pytest.fixture
async def spa_client(engine, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>SPA</html>")
    index = str(dist / "index.html")

    async def _serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(index)

    app.add_api_route(
        "/{full_path:path}",
        _serve_spa,
        include_in_schema=False,
        name="_test_spa_route",
    )

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    app.router.routes = [
        r for r in app.router.routes if getattr(r, "name", None) != "_test_spa_route"
    ]


async def test_spa_serves_index_html(spa_client):
    r = await spa_client.get("/some-route")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
