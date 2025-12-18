import asyncio

from fastapi import APIRouter, status
from fastapi.responses import ORJSONResponse

from ...services.llm_client import LLMClient, LLMClientError

router = APIRouter(prefix="/api/llm", tags=["llm"])

llm_client = LLMClient(timeout_seconds=30)


@router.get("/health")
async def llm_health():
    try:
        text = await asyncio.to_thread(llm_client.generate_text, "Say just: OK")
        if not text:
            raise LLMClientError("Empty response")
        return {"ok": True, "model": llm_client.model, "base_url": llm_client.base_url}
    except Exception as exc:
        return ORJSONResponse(
            {"ok": False, "model": llm_client.model, "base_url": llm_client.base_url, "error": str(exc)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
