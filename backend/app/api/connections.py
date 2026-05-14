import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..schemas.settings import ABSTestRequest, LLMTestRequest, TestConnectionResponse

router = APIRouter()

_TIMEOUT = 10.0


@router.post("/llm/test-connection", response_model=TestConnectionResponse)
async def test_llm_connection(
    req: LLMTestRequest,
    db: AsyncSession = Depends(get_db),
) -> TestConnectionResponse:
    headers: dict[str, str] = {}
    api_key = req.api_key or ""
    needs_key = req.llm_type in ("ollama_bearer", "openai")
    if needs_key and not api_key:
        # Token omitted (page-refresh scenario) — load and decrypt from DB.
        async with db.begin():
            row = await db.get(Settings, 1)
        if row and row.llm_api_key:
            try:
                api_key = decrypt(row.llm_api_key)
            except Exception:
                return TestConnectionResponse(ok=False, error="Stored API key is corrupted")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(f"{req.endpoint.rstrip('/')}/v1/models", headers=headers)
            r.raise_for_status()
            data = r.json()
            model_ids = [m["id"] for m in data.get("data", [])]
            return TestConnectionResponse(ok=True, models=model_ids)
    except httpx.HTTPStatusError as exc:
        return TestConnectionResponse(ok=False, error=f"HTTP {exc.response.status_code}")
    except Exception as exc:
        return TestConnectionResponse(ok=False, error=str(exc))


@router.post("/abs/test-connection", response_model=TestConnectionResponse)
async def test_abs_connection(
    req: ABSTestRequest,
    db: AsyncSession = Depends(get_db),
) -> TestConnectionResponse:
    token = req.token or ""
    if not token:
        # Token omitted (e.g. page-refresh scenario where the UI shows a masked
        # placeholder) — load and decrypt the stored token from the DB.
        async with db.begin():
            row = await db.get(Settings, 1)
        if not row or not row.abs_token:
            return TestConnectionResponse(ok=False, error="No API token configured")
        try:
            token = decrypt(row.abs_token)
        except Exception:
            return TestConnectionResponse(ok=False, error="Stored token is corrupted")

    headers = {"Authorization": f"Bearer {token}"}
    base = req.url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(f"{base}/api/me", headers=headers)
            r.raise_for_status()

            libs_r = await client.get(f"{base}/api/libraries", headers=headers)
            libs_r.raise_for_status()
            libraries = libs_r.json().get("libraries", [])

            metadata: dict = {}
            if libraries:
                first = libraries[0]
                metadata["library_name"] = first.get("name", "")
                metadata["library_count"] = len(libraries)
                stats = first.get("stats", {}) or {}
                if "totalItems" in stats:
                    metadata["book_count"] = stats["totalItems"]

            return TestConnectionResponse(ok=True, metadata=metadata or None)
    except httpx.HTTPStatusError as exc:
        return TestConnectionResponse(ok=False, error=f"HTTP {exc.response.status_code}")
    except Exception as exc:
        return TestConnectionResponse(ok=False, error=str(exc))
