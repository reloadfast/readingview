import httpx
from fastapi import APIRouter

from ..schemas.settings import ABSTestRequest, LLMTestRequest, TestConnectionResponse

router = APIRouter()

_TIMEOUT = 10.0


@router.post("/llm/test-connection", response_model=TestConnectionResponse)
async def test_llm_connection(req: LLMTestRequest) -> TestConnectionResponse:
    headers: dict[str, str] = {}
    if req.api_key:
        headers["Authorization"] = f"Bearer {req.api_key}"

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
async def test_abs_connection(req: ABSTestRequest) -> TestConnectionResponse:
    headers = {"Authorization": f"Bearer {req.token}"}
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
