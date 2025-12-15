import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "models/gemini-pro"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_SAFETY = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


class GeminiClientError(Exception):
    """Raised when Gemini cannot fulfill a request."""


@dataclass
class GeminiJSONResponse:
    raw_text: str
    data: Dict[str, Any]


def _extract_text(response: Any) -> str:
    if hasattr(response, "text") and response.text:
        return response.text
    for cand in getattr(response, "candidates", []) or []:
        parts = getattr(getattr(cand, "content", None), "parts", []) or []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                return text
    return ""


def _parse_json(raw_text: str) -> Dict[str, Any]:
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    for delimiter in ("```",):
        if delimiter in raw_text:
            try:
                return json.loads(raw_text.split(delimiter)[1])
            except Exception:
                continue
    try:
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        return json.loads(cleaned[start:end])
    except Exception as exc:
        raise GeminiClientError("Gemini returned non-JSON payload") from exc


class GeminiClient:
    """Thin wrapper around google-generativeai with retries and timeouts."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self._models: dict[str, Any] = {}

    def _get_model(self, system_instruction: Optional[str] = None):
        key = system_instruction or "__default__"
        if key in self._models:
            return self._models[key]
        if not self.api_key:
            raise GeminiClientError("GEMINI_API_KEY is not configured")
        genai.configure(
            api_key=self.api_key,
            client_options={"api_endpoint": "https://generativelanguage.googleapis.com"},
        )
        self._models[key] = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction,
        )
        return self._models[key]

    async def generate_json(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        max_retries: int = 2,
    ) -> GeminiJSONResponse:
        if not prompt or not prompt.strip():
            raise GeminiClientError("Prompt is empty")

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                model = self._get_model(system_instruction)
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        model.generate_content,
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "temperature": 0.35,
                            "max_output_tokens": 1024,
                        },
                        safety_settings=DEFAULT_SAFETY,
                    ),
                    timeout=self.timeout_seconds,
                )
                raw_text = _extract_text(response)
                if not raw_text:
                    raise GeminiClientError("Gemini returned an empty response")
                data = _parse_json(raw_text)
                return GeminiJSONResponse(raw_text=raw_text, data=data)
            except Exception as exc:  # pragma: no cover - network/SDK errors
                last_error = exc
                logger.warning("Gemini attempt %s failed: %s", attempt + 1, exc)
                if attempt < max_retries:
                    await asyncio.sleep(0.6 * (attempt + 1))
        raise GeminiClientError("Gemini request failed") from last_error
