import asyncio
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form, Request, status

from ...api import deps
from ...services.autochecker_service import AutoCheckerService, AutoCheckerError
from ...services.gemini_client import GeminiClient, GeminiClientError

router = APIRouter(prefix="/api/autochecker", tags=["autochecker"])

service = AutoCheckerService()
gemini_client = GeminiClient(api_key=service.settings.gemini_api_key, timeout_seconds=10)

GEMINI_SYSTEM_PROMPT = """
You are an AI mentor checking Kazakh language writing.

Return ONLY valid JSON in the following format:
{
  "overall_score": 0-100,
  "categories": {
    "grammar": 0-100,
    "vocabulary": 0-100,
    "spelling": 0-100,
    "style": 0-100
  },
  "mistakes": [
    {
      "type": "grammar|spelling|vocabulary|style",
      "original": "<original fragment>",
      "explanation": "<short explanation>",
      "suggestion": "<corrected version>"
    }
  ],
  "recommendations": [
    "<short actionable recommendation>"
  ],
  "improved_version": "<slightly improved version in Kazakh>"
}

Do not include markdown.
Do not include explanations outside JSON.
"""


@router.post(
    "",
    summary="Lightweight text-based pronunciation scoring",
)
def autochecker_text(payload: dict, user=Depends(deps.require_user)):
    phrase = payload.get("phrase") or payload.get("target") or ""
    transcript = payload.get("text") or payload.get("transcript") or ""
    if not phrase or not transcript:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="phrase and text are required")
    def _normalize(s: str) -> str:
        return "".join(ch.lower() for ch in s if ch.isalnum())
    norm_phrase = _normalize(phrase)
    norm_spoken = _normalize(transcript)
    if not norm_phrase or not norm_spoken:
        return {"score": 0, "expected": phrase, "transcript": transcript, "tips": []}
    overlap = sum(1 for a, b in zip(norm_phrase, norm_spoken) if a == b)
    score = int((overlap / max(len(norm_phrase), len(norm_spoken))) * 100)
    return {
        "score": score,
        "expected": phrase,
        "transcript": transcript,
        "tips": ["Сравните ударения", "Повторите медленнее"],
    }


def _clamp_score(value: Any) -> int:
    try:
        num = float(value)
    except Exception:
        num = 0
    return int(max(0, min(100, round(num))))


def _normalize_categories(raw: Any) -> dict:
    raw = raw or {}
    return {
        "grammar": _clamp_score(raw.get("grammar", 0)),
        "vocabulary": _clamp_score(raw.get("vocabulary", 0)),
        "word_order": _clamp_score(raw.get("word_order", 0)),
        "clarity": _clamp_score(raw.get("clarity", 0)),
    }


def _normalize_mistakes(raw: Any) -> list[dict]:
    if not isinstance(raw, (list, tuple)):
        return []
    normalized = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "fragment": str(item.get("fragment") or "").strip(),
                "issue": str(item.get("issue") or "").strip(),
                "explanation": str(item.get("explanation") or "").strip(),
                "suggestion": str(item.get("suggestion") or "").strip(),
            }
        )
    return normalized


def _normalize_recommendations(raw: Any) -> list[str]:
    if not raw:
        return []
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    cleaned = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _normalize_schema(data: dict, model_name: str | None) -> dict | None:
    try:
        overall = _clamp_score(data.get("overall_score", 0))
        categories = _normalize_categories(data.get("categories") or {})
        mistakes = _normalize_mistakes(data.get("mistakes"))
        mentor_feedback = str(data.get("mentor_feedback") or "").strip()
        improved_version = str(data.get("improved_version") or "").strip()
        recommendations = _normalize_recommendations(data.get("recommendations"))
    except Exception:
        return None

    if overall == 0:
        total = sum(categories.values())
        if total > 0:
            overall = _clamp_score(total / 4)

    return {
        "ai_used": True,
        "model": model_name or "gemini-pro",
        "overall_score": overall,
        "categories": categories,
        "mistakes": mistakes,
        "mentor_feedback": mentor_feedback,
        "improved_version": improved_version,
        "recommendations": recommendations,
    }


def _failure_response(message: str = "AI model unavailable") -> dict:
    return {
        "ai_used": False,
        "model": None,
        "overall_score": 0,
        "categories": {"grammar": 0, "vocabulary": 0, "word_order": 0, "clarity": 0},
        "mistakes": [],
        "mentor_feedback": "",
        "improved_version": "",
        "recommendations": [],
        "error": message,
    }


async def _call_gemini(text: str) -> dict | None:
    model_name = "models/gemini-1.5-flash-latest"
    if not (gemini_client.api_key or service.settings.gemini_api_key):
        print("[autochecker] Gemini skipped: GEMINI_API_KEY is not configured")
        return _failure_response("GEMINI_API_KEY is not configured")

    gemini_client.api_key = gemini_client.api_key or service.settings.gemini_api_key
    gemini_client.model_name = model_name

    print(f"[autochecker] Gemini request start model={model_name}")
    try:
        response = await asyncio.wait_for(
            gemini_client.generate_json(
                prompt=f"Text:\n{text}",
                system_instruction=GEMINI_SYSTEM_PROMPT,
            ),
            timeout=10,
        )
        print(f"[autochecker] Gemini raw response model={model_name}: {response.raw_text!r}")
        data = response.data or {}
        has_required = (
            isinstance(data, dict)
            and "overall_score" in data
            and "categories" in data
            and "improved_version" in data
        )
        if not has_required:
            print(f"[autochecker] Gemini analysis failed: incomplete payload keys={list(data.keys())}")
            return _failure_response("Gemini returned incomplete payload")
        normalized = _normalize_schema(data, model_name=model_name)
        if not normalized:
            print("[autochecker] Gemini analysis failed: normalization returned None")
            return _failure_response("Gemini returned invalid payload")
        print(f"[autochecker] Gemini request succeeded model={model_name}")
        return normalized
    except asyncio.TimeoutError:
        print(f"[autochecker] Gemini analysis failed: timeout for model={model_name}")
        return _failure_response("Gemini timeout")
    except GeminiClientError as exc:
        print(f"[autochecker] Gemini analysis failed: {exc}")
        return _failure_response(f"Gemini error: {exc}")
    except Exception as exc:  # pragma: no cover - defensive/fallback
        print(f"[autochecker] Gemini analysis failed: {exc}")
        return _failure_response(f"Gemini unexpected error: {exc}")


def _baseline_response(text: str) -> dict:
    """Offline fallback to keep the feature usable when Gemini is unavailable."""
    words = [w for w in text.replace("\n", " ").split(" ") if w.strip()]
    unique_words = len({w.lower().strip(".,!?;:") for w in words if w})
    length_score = _clamp_score(min(100, max(35, len(text) // 3)))
    vocabulary_score = _clamp_score(min(95, int((unique_words / max(1, len(words))) * 120)))
    grammar_score = _clamp_score(length_score - 5)
    clarity_score = _clamp_score(80 if len(text.split(".")) > 1 else 65)
    overall = _clamp_score((grammar_score + vocabulary_score + clarity_score) / 3)
    return {
        "ai_used": True,
        "model": "fallback-local",
        "overall_score": overall,
        "categories": {
            "grammar": grammar_score,
            "vocabulary": vocabulary_score,
            "word_order": grammar_score,
            "clarity": clarity_score,
        },
        "mistakes": [],
        "mentor_feedback": "",
        "improved_version": text.strip(),
        "recommendations": ["Попробуйте укоротить предложения для лучшей читаемости."] if len(text) > 200 else [],
    }


@router.post("/html")
async def autochecker_html(payload: dict, user=Depends(deps.require_user)):
    text = str(payload.get("text") or "").strip()
    language = str(payload.get("language") or "").strip()
    del user, language  # reserved for future use
    if not text:
        return _failure_response("AI model unavailable")
    gemini_result = await _call_gemini(text)
    if gemini_result:
        return gemini_result
    return _baseline_response(text)


@router.get("/ping")
def autochecker_ping():
    return {"status": "ok"}


@router.post(
    "/eval",
    summary="Evaluate pronunciation via Gemini",
    description="""
    curl -b cookies.txt -X POST http://127.0.0.1:8000/api/autochecker/eval \\
      -F "audio=@voice.webm" \\
      -F "phrase=Сәлем"
    """,
)
async def autochecker_eval(
    request: Request,
    phrase: str = Form(...),
    audio: UploadFile = File(...),
    user=Depends(deps.require_user),
):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty")
    try:
        result = await service.process_audio(user, audio_bytes, phrase, mime_type=audio.content_type)
        return result
    except AutoCheckerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
