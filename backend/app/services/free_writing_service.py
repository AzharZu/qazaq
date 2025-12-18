import asyncio
import logging
import textwrap
import uuid
from dataclasses import dataclass
from typing import Any

from .llm_client import LLMClient, LLMClientError

logger = logging.getLogger(__name__)

FREE_WRITING_SYSTEM_PROMPT = """
You are a concise writing evaluator for learners.

- Language can be Kazakh (kk), Russian (ru), or English (en); respond in the requested language.
- Be encouraging but direct.
- Keep feedback short (max 3 sentences).
- Return ONLY valid JSON with this schema and no markdown:
{
  "score": 0-100,
  "level": "excellent" | "good" | "ok" | "weak",
  "feedback": "short feedback in target language",
  "corrections": ["short correction hints or examples"]
}
"""


@dataclass
class FreeWritingResult:
    ok: bool
    score: int | None = None
    level: str | None = None
    feedback: str | None = None
    corrections: list[str] | None = None
    model: str | None = None
    error: str | None = None
    details: str | None = None


def _clamp_score(value: Any) -> int:
    try:
        return int(max(0, min(100, round(float(value)))))
    except Exception:
        return 0


def _normalize_level(level: str | None, score: int) -> str:
    allowed = {"excellent", "good", "ok", "weak"}
    if level:
        normalized = str(level).strip().lower()
        if normalized in allowed:
            return normalized
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 50:
        return "ok"
    return "weak"


def _trim_text(text: str | None, limit: int) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


class FreeWritingService:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient(timeout_seconds=60)

    def _build_prompt(self, prompt: str, answer: str, rubric: str | None, language: str) -> str:
        lang_hint = language if language in {"kk", "ru", "en"} else "kk"
        rubric_section = f"Rubric/criteria:\n{rubric}\n\n" if rubric else ""
        return textwrap.dedent(
            f"""
            Evaluate the student's free writing response.
            Task:\n{prompt}\n
            {rubric_section}Student answer:\n{answer}\n
            Respond in {lang_hint}. Return ONLY JSON per the schema.
            """
        ).strip()

    def _normalize(self, payload: dict, model: str | None) -> FreeWritingResult:
        score = _clamp_score(payload.get("score"))
        level = _normalize_level(payload.get("level"), score)
        feedback = str(payload.get("feedback") or "").strip()
        corrections_raw = payload.get("corrections") or []
        corrections: list[str] = []
        if isinstance(corrections_raw, (list, tuple)):
            for item in corrections_raw:
                text = str(item or "").strip()
                if text:
                    corrections.append(text)
        elif corrections_raw:
            text = str(corrections_raw).strip()
            if text:
                corrections.append(text)
        return FreeWritingResult(
            ok=True,
            score=score,
            level=level,
            feedback=feedback,
            corrections=corrections,
            model=model or "llm",
        )

    async def check(self, *, prompt: str, student_answer: str, rubric: str | None, language: str, request_id: str | None = None) -> FreeWritingResult:
        if not self.client.is_configured():
            raise LLMClientError("LLM_API_KEY is not configured")
        req_id = request_id or uuid.uuid4().hex
        safe_prompt = _trim_text(prompt, 1500)
        safe_answer = _trim_text(student_answer, 3500)
        safe_rubric = _trim_text(rubric, 1200) if rubric else None

        logger.info(
            "[free-writing] req=%s model=%s prompt_len=%s answer_len=%s rubric_len=%s",
            req_id,
            getattr(self.client, "model", None),
            len(safe_prompt),
            len(safe_answer),
            len(safe_rubric or ""),
        )
        full_prompt = self._build_prompt(safe_prompt, safe_answer, safe_rubric, language)
        try:
            response = await asyncio.to_thread(
                self.client.generate_json,
                f"{FREE_WRITING_SYSTEM_PROMPT}\n\n{full_prompt}",
                max_retries=2,
            )
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning("[free-writing] req=%s LLM error: %s", req_id, exc)
            raise LLMClientError(str(exc)) from exc

        data = response or {}
        logger.info(
            "[free-writing] req=%s model=%s raw_len=%s",
            req_id,
            getattr(self.client, "model", None),
            len(str(data)),
        )
        if not isinstance(data, dict) or "score" not in data:
            raise LLMClientError("LLM returned incomplete payload")
        return self._normalize(data, getattr(self.client, "model", None))


__all__ = ["FreeWritingService", "FreeWritingResult"]
