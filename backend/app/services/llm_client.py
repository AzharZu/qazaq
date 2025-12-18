import json
import logging
import os
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when the LLM request fails."""


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL") or "https://api.groq.com/openai/v1").rstrip("/")
        self.model = model or os.getenv("LLM_MODEL") or "llama-3.1-8b-instant"
        self.timeout_seconds = timeout_seconds

    def _request(self, prompt: str, extra_messages: list[dict] | None = None) -> Dict[str, Any]:
        if not self.api_key:
            raise LLMClientError("LLM_API_KEY is not configured")
        url = f"{self.base_url}/chat/completions"
        messages = [{"role": "user", "content": prompt}]
        if extra_messages:
            messages.extend(extra_messages)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        try:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise LLMClientError("LLM request timed out") from exc
        except Exception as exc:  # pragma: no cover - network errors
            raise LLMClientError(f"LLM request failed: {exc}") from exc
        if resp.status_code >= 400:
            message = ""
            try:
                body = resp.json()
                message = body.get("error", {}).get("message") or body.get("message") or resp.text
            except Exception:
                message = resp.text
            if resp.status_code in {401, 403}:
                raise LLMClientError(f"LLM authentication error ({resp.status_code}): {message}")
            if resp.status_code == 429:
                raise LLMClientError(f"LLM rate limit exceeded: {message}")
            raise LLMClientError(f"LLM HTTP {resp.status_code}: {message}")
        try:
            return resp.json()
        except Exception as exc:
            raise LLMClientError("LLM returned non-JSON payload") from exc

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
            return "".join(parts)
        return ""

    def generate_text(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise LLMClientError("Prompt is empty")
        data = self._request(prompt)
        text = self._extract_text(data)
        if not text:
            raise LLMClientError("LLM returned an empty response")
        return text.strip()

    def generate_json(self, prompt: str, *, max_retries: int = 2) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            raise LLMClientError("Prompt is empty")
        last_error: Exception | None = None
        attempts = max(1, max_retries + 1)
        for attempt in range(attempts):
            try:
                extra = None
                if attempt > 0:
                    extra = [{"role": "system", "content": "Return ONLY valid JSON, no markdown"}]
                data = self._request(prompt, extra_messages=extra)
                text = self._extract_text(data)
                if not text:
                    raise LLMClientError("LLM returned an empty response")
                return json.loads(text)
            except Exception as exc:  # pragma: no cover - network
                last_error = exc
                logger.warning("LLM attempt %s failed: %s", attempt + 1, exc)
                if attempt + 1 < attempts:
                    time.sleep(0.5 * (attempt + 1))
        raise LLMClientError(str(last_error) if last_error else "LLM request failed")

    def is_configured(self) -> bool:
        return bool(self.api_key)
