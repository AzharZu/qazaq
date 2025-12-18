import sys
from pathlib import Path

import pytest

# Ensure `app` package is discoverable when running tests from repo root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.services.free_writing_service import FreeWritingService  # noqa: E402
from app.services.llm_client import LLMClientError  # noqa: E402


class DummyLLMClient:
    def __init__(self, payload: dict):
        self.payload = payload
        self.model = "models/test"

    def is_configured(self) -> bool:
        return True

    async def generate_json(self, *args, **kwargs):
        return self.payload


@pytest.mark.asyncio
async def test_free_writing_normalizes_result():
    client = DummyLLMClient({"score": 92, "level": "good", "feedback": "Nice job", "corrections": ["Try shorter sentences"]})
    service = FreeWritingService(client=client)

    result = await service.check(prompt="Q", student_answer="A", rubric=None, language="en", request_id="t1")

    assert result.ok is True
    assert result.score == 92
    assert result.level == "good"
    assert result.feedback == "Nice job"
    assert result.corrections == ["Try shorter sentences"]
    assert result.model == "models/test"


@pytest.mark.asyncio
async def test_free_writing_requires_score_in_payload():
    client = DummyLLMClient({})
    service = FreeWritingService(client=client)

    with pytest.raises(LLMClientError):
        await service.check(prompt="Q", student_answer="A", rubric=None, language="en", request_id="t2")
