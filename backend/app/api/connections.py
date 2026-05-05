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
            r = await client.get(f"{req.llm_endpoint.rstrip('/')}/v1/models", headers=headers)
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

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(f"{req.url.rstrip('/')}/api/me", headers=headers)
            r.raise_for_status()
            return TestConnectionResponse(ok=True)
    except httpx.HTTPStatusError as exc:
        return TestConnectionResponse(ok=False, error=f"HTTP {exc.response.status_code}")
    except Exception as exc:
        return TestConnectionResponse(ok=False, error=str(exc))
