import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Default key from instructions; override with GEMINI_API_KEY env var in production.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAX10gyWcu-651JEgIswMoEMvY4dzSWmSU")
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

SYSTEM_PROMPT = """
Ты — AutoChecker, инструмент, который анализирует текст на казахском и русском языках.
Задача:
1) Проверить грамматику текста.
2) Проверить лексику.
3) Найти конкретные ошибки (по фрагментам текста).
4) Дать рекомендации, как улучшить текст.
5) Предложить улучшенную версию текста, сохраняя стиль автора.
6) Сформировать HTML-разметку с подсветкой ошибок.

Формат ответа строго в JSON:
{
  "grammar_score": число от 0 до 10,
  "vocabulary_score": число от 0 до 10,
  "errors": [
    {
      "fragment": "ошибочный фрагмент",
      "explanation": "краткое объяснение ошибки",
      "suggestion": "как правильно"
    }
  ],
  "recommendations": ["совет 1", "совет 2"],
  "improved_text": "улучшенный текст целиком",
  "annotated_html": "оригинальный текст, но с тегами <mark> вокруг проблемных мест"
}

Никакого лишнего текста, только JSON.
annotated_html должен быть безопасным простым HTML без стилей: только <p>, <br>, <mark>, <b>, <i>.
""".strip()


class AutoCheckerError(Exception):
    """Raised when AI analysis cannot be completed."""


def _build_model():
    if not GEMINI_API_KEY:
        raise AutoCheckerError("Gemini API key is not configured.")
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )


_model = _build_model()


def _sanitize_html(html: str) -> str:
    if not html:
        return ""
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\\1>", "", html)
    allowed = r"(?:p|br|mark|b|i)"
    cleaned = re.sub(rf"</?(?!{allowed}\\b)[^>]+>", "", html)
    return cleaned


def _parse_json(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    def _load(candidate: str) -> Dict[str, Any]:
        return json.loads(candidate)

    data: Dict[str, Any] | None = None
    try:
        data = _load(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            try:
                data = _load(match.group(0))
            except json.JSONDecodeError:
                data = None
    if data is None:
        logger.error("AutoChecker JSON parse failed. Raw: %s", raw_text[:500], exc_info=True)
        raise AutoCheckerError("Анализ недоступен. Попробуйте позже.")

    def _as_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [value]
        return [str(value)]

    def _as_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _as_errors(value: Any) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        if isinstance(value, dict):
            value = [value]
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    continue
                items.append(
                    {
                        "fragment": str(item.get("fragment") or "").strip(),
                        "explanation": str(item.get("explanation") or "").strip(),
                        "suggestion": str(item.get("suggestion") or "").strip(),
                    }
                )
        return [i for i in items if any(i.values())]

    annotated_html = _sanitize_html(str(data.get("annotated_html") or ""))

    return {
        "grammar_score": _as_int(data.get("grammar_score")),
        "vocabulary_score": _as_int(data.get("vocabulary_score")),
        "errors": _as_errors(data.get("errors")),
        "recommendations": _as_list(data.get("recommendations")),
        "improved_text": str(data.get("improved_text") or "").strip(),
        "annotated_html": annotated_html,
    }


def _normalize_level(level: str | None) -> str:
    lvl = (level or "A2").upper()
    return lvl if lvl in {"A1", "A2", "B1", "B2"} else "A2"


def _analyze_sync(user_text: str, level: str) -> Dict[str, Any]:
    prompt = (
        "Проанализируй текст и верни JSON по инструкции. "
        f"Учитывай, что этот текст от ученика уровня {level}: для A1/A2 объясняй проще и мягче, "
        "для B1/B2 можно быть строже и подробнее.\n"
        f"Текст:\n{user_text}"
    )
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 2048,
        "response_mime_type": "application/json",
    }
    response = _model.generate_content(
        prompt,
        generation_config=generation_config,
        safety_settings=SAFETY_SETTINGS,
    )

    raw_text = None
    try:
        raw_text = response.text
    except Exception:
        raw_text = None
    if not raw_text and getattr(response, "candidates", None):
        for cand in response.candidates:
            parts = getattr(getattr(cand, "content", None), "parts", []) or []
            for part in parts:
                candidate_text = getattr(part, "text", None)
                if candidate_text:
                    raw_text = candidate_text
                    break
            if raw_text:
                break
    if not raw_text and getattr(response, "prompt_feedback", None):
        raise AutoCheckerError("Модель отклонила запрос. Попробуйте другой текст или уменьшите чувствительный контент.")
    if not raw_text:
        raise AutoCheckerError("Не удалось получить ответ от ИИ.")

    return _parse_json(raw_text)


async def analyze_text(user_text: str, level: str = "A2") -> Dict[str, Any]:
    """Analyze text with Gemini and return structured feedback."""
    if not user_text or not user_text.strip():
        raise AutoCheckerError("Введите текст для проверки.")

    lvl = _normalize_level(level)

    try:
        return await asyncio.to_thread(_analyze_sync, user_text.strip(), lvl)
    except AutoCheckerError:
        raise
    except Exception as exc:  # pragma: no cover - network/SDK errors
        logger.exception("AutoChecker request failed")
        raise AutoCheckerError("Не удалось получить ответ от ИИ.") from exc
