import asyncio
import logging
import uuid
from string import Template
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form, Request, status
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field, ValidationError

from ...api import deps
from ...services.autochecker_service import AutoCheckerService, AutoCheckerError
from ...services.free_writing_service import FreeWritingService, FreeWritingResult
from ...services.llm_client import LLMClient, LLMClientError

router = APIRouter(prefix="/api/autochecker", tags=["autochecker"])

service = AutoCheckerService()
llm_client = LLMClient(timeout_seconds=60)
free_writing_service = FreeWritingService(client=llm_client)
logger = logging.getLogger(__name__)

LLM_SYSTEM_PROMPT = """
YТы — профессиональный преподаватель казахского языка (Qazaq tili),
лингвист и методист. Ты проверяешь письменные тексты учеников.

ВАЖНО:
— Отвечай СТРОГО на языке текста пользователя:
  • если текст на казахском → отвечай ТОЛЬКО на казахском
  • если текст на русском → отвечай ТОЛЬКО на русском
— НИКОГДА не используй английский язык
— Не сокращай объяснения
— Не «угадывай» слова, если не уверен — объясни сомнение
— Казахский язык приоритетен

ТВОЯ ЗАДАЧА:
Проанализировать текст ученика и вернуть СТРОГО валидный JSON
БЕЗ markdown, БЕЗ комментариев, БЕЗ лишнего текста.

АНАЛИЗ ВКЛЮЧАЕТ:
1. Орфография (әріптер: ә, ғ, қ, ң, ө, ұ, ү, һ)
2. Грамматика (септік жалғаулары, жіктік, тәуелдік)
3. Пунктуация
4. Лексика (дұрыс сөз таңдау)
5. Синтаксис и порядок слов
6. Общая понятность текста

ФОРМАТ ОТВЕТА (СТРОГО):

{
  "language": "kk | ru",
  "scores": {
    "grammar": 0-100,
    "vocabulary": 0-100,
    "punctuation": 0-100,
    "word_order": 0-100,
    "clarity": 0-100,
    "overall": 0-100
  },
  "before": "<исходный текст без изменений>",
  "after": "<исправленный текст, литературная норма>",
  "errors": [
    {
      "type": "Орфография | Грамматика | Пунктуация | Лексика | Синтаксис",
      "fragment": "<ошибочный фрагмент>",
      "explanation": "<подробное, учебное объяснение ПОЧЕМУ это ошибка>",
      "suggestion": "<правильный вариант>"
    }
  ],
  "recommendations": [
    "<конкретный совет по улучшению казахского языка>",
    "<ещё один совет>"
  ],
  "suggested_text": "<улучшенный вариант текста, естественный и живой>"
}

ПРАВИЛА:
— explanation ДОЛЖНО объяснять ПРАВИЛО (не одно слово!)
— suggested_text может быть улучшенной версией, но без изменения смысла
— если ошибок нет, массив errors должен быть пустым []
— оценки должны быть честными (не завышай)
— не придумывай ошибок
— не используй слова вроде «возможно», если правило чёткое

Ты — не чат-бот, ты — строгий, но доброжелательный учитель.
"""

# New Grok-based text evaluation prompt template (language-specific).
# New Grok-based text evaluation prompt template (language-specific).
TEXT_CHECK_PROMPT = Template(
    """
You are a strict writing evaluator. Language: $lang_name ($lang_code). Respond ONLY in this language.

Return ONLY valid JSON (no markdown, no comments) with EXACTLY these keys:
{
  "ok": true,
  "request_id": "$request_id",
  "language": "$lang_code",
  "level": "A1|A2|B1|B2|C1|C2",
  "scores": {
    "grammar": 0-10,
    "lexicon": 0-10,
    "spelling": 0-10,
    "punctuation": 0-10,
    "overall": 0-100
  },
  "before_text": "<original text>",
  "after_text": "<improved text in same language>",
  "highlighted_html": "<safe HTML with <mark data-error-id='...'>...</mark>>",
  "issues": [
    {
      "id": "e1",
      "type": "grammar|lexicon|spelling|punctuation",
      "title": "<short title>",
      "explanation": "<why it's wrong>",
      "before": "<incorrect fragment>",
      "after": "<corrected fragment>",
      "start": 0,
      "end": 0,
      "severity": "low|medium|high"
    }
  ],
  "recommendations": ["...", "..."],
  "suggested_text": "<best final version>"
}

Rules:
- Use plain text, no markdown, no code fences.
- start/end are character indices inside before_text.
- highlighted_html must align with issues using <mark data-error-id='...'>.
- If language is Kazakh (kk), strictly handle ә, ғ, қ, ң, ө, ұ, ү, һ; check септіктер, орфография, пунктуация.
- If language is Russian (ru), focus on согласование, падежи, пунктуация.
- Do NOT add any keys or explanations outside the JSON. Return ONLY JSON.
"""
)



def _get_request_id(request: Request | None = None) -> str:
    return getattr(request.state, "request_id", None) if request else None or uuid.uuid4().hex


@router.get("/health")
async def autochecker_health(request: Request, user=Depends(deps.require_admin)):
    req_id = _get_request_id(request)
    key_present = llm_client.is_configured()
    if not key_present:
        logger.warning("[autochecker] health req=%s key missing", req_id)
        return ORJSONResponse(
            {"ok": False, "provider": "llm", "key_present": False, "request_id": req_id},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        await asyncio.to_thread(llm_client.generate_text, "Say just: OK")
        return {"ok": True, "provider": "llm", "key_present": True, "request_id": req_id, "model": llm_client.model, "base_url": llm_client.base_url}
    except Exception as exc:  # pragma: no cover - network errors
        logger.warning("[autochecker] health req=%s failed: %s", req_id, exc)
        return ORJSONResponse(
            {"ok": False, "provider": "llm", "key_present": True, "error": "LLM error", "details": str(exc), "request_id": req_id},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


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
        "model": model_name or "llm",
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


async def _call_llm(text: str) -> dict | None:
    model_name = getattr(llm_client, "model", None) or "llm-default"
    if not llm_client.is_configured():
        print("[autochecker] LLM skipped: LLM_API_KEY is not configured")
        return _failure_response("LLM_API_KEY is not configured")

    logger.info("[autochecker] LLM request start model=%s", model_name)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                llm_client.generate_json,
                f"{LLM_SYSTEM_PROMPT}\n\nText:\n{text}",
            ),
            timeout=60,
        )
        raw_preview = str(response)[:200]
        logger.info("[autochecker] LLM raw response model=%s preview=%r", model_name, raw_preview)
        data = response or {}
        has_required = (
            isinstance(data, dict)
            and "overall_score" in data
            and "categories" in data
            and "improved_version" in data
        )
        if not has_required:
            logger.warning("[autochecker] LLM analysis failed: incomplete payload keys=%s", list(data.keys()))
            return _failure_response("LLM returned incomplete payload")
        normalized = _normalize_schema(data, model_name=model_name)
        if not normalized:
            logger.warning("[autochecker] LLM analysis failed: normalization returned None")
            return _failure_response("LLM returned invalid payload")
        logger.info("[autochecker] LLM request succeeded model=%s", model_name)
        return normalized
    except asyncio.TimeoutError:
        logger.warning("[autochecker] LLM analysis failed: timeout for model=%s", model_name)
        return _failure_response("LLM timeout")
    except LLMClientError as exc:
        logger.warning("[autochecker] LLM analysis failed: %s", exc)
        return _failure_response(f"LLM error: {exc}")
    except Exception as exc:  # pragma: no cover - defensive/fallback
        logger.exception("[autochecker] LLM analysis failed: %s", exc)
        return _failure_response(f"LLM unexpected error: {exc}")


def _baseline_response(text: str) -> dict:
    """Offline fallback to keep the feature usable when the LLM is unavailable."""
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
    llm_result = await _call_llm(text)
    if llm_result:
        return llm_result
    return _baseline_response(text)


class FreeWritingPayload(BaseModel):
    prompt: str = Field(..., min_length=1)
    student_answer: str = Field(..., min_length=1)
    rubric: str | None = None
    language: str = "kk"


class TextCheckPayload(BaseModel):
    text: str = Field(..., min_length=1)
    language: str = Field(default="kk", pattern="^(kk|ru)$")
    mode: str = Field(default="full")


class TextCheckScores(BaseModel):
    grammar: int = Field(0, ge=0, le=10)
    lexicon: int = Field(0, ge=0, le=10)
    spelling: int = Field(0, ge=0, le=10)
    punctuation: int = Field(0, ge=0, le=10)
    overall: int = Field(0, ge=0, le=100)


class TextCheckIssue(BaseModel):
    id: str
    type: str
    title: str
    explanation: str
    before: str
    after: str
    start: int
    end: int
    severity: str


class TextCheckResponse(BaseModel):
    ok: bool = True
    request_id: str
    language: str
    level: str
    scores: TextCheckScores
    before_text: str
    after_text: str
    highlighted_html: str
    issues: list[TextCheckIssue]
    recommendations: list[str]
    suggested_text: str


def _free_writing_error(message: str, details: Any, status_code: int, request_id: str) -> ORJSONResponse:
    payload: dict[str, Any] = {"ok": False, "error": message, "request_id": request_id}
    if details:
        payload["details"] = details
    return ORJSONResponse(payload, status_code=status_code)


def _safe_highlight(before: str, issues: list[TextCheckIssue]) -> str:
    """Build highlighted HTML using <mark data-error-id='...'> spans."""
    if not before:
        return ""
    result = []
    cursor = 0
    for issue in sorted(issues, key=lambda i: i.start):
        start = max(0, min(len(before), issue.start))
        end = max(start, min(len(before), issue.end))
        if start > cursor:
            result.append(before[cursor:start])
        frag = before[start:end] or ""
        result.append(f"<mark data-error-id=\"{issue.id}\">{frag}</mark>")
        cursor = end
    if cursor < len(before):
        result.append(before[cursor:])
    return "".join(result)


def _normalize_text_response(raw: dict, req_id: str, language: str) -> TextCheckResponse | None:
    if not isinstance(raw, dict):
        return None

    def _score(val, *, overall: bool = False) -> int:
        try:
            num = float(val)
        except Exception:
            num = 0
        if overall:
            return int(max(0, min(100, round(num))))
        if num > 10:
            num = num / 10.0
        return int(max(0, min(10, round(num))))

    scores_raw = raw.get("scores") or {}
    scores = {
        "grammar": _score(scores_raw.get("grammar")),
        "lexicon": _score(scores_raw.get("lexicon")),
        "spelling": _score(scores_raw.get("spelling")),
        "punctuation": _score(scores_raw.get("punctuation")),
        "overall": _score(scores_raw.get("overall"), overall=True),
    }

    before_text = raw.get("before_text") or raw.get("before") or ""
    after_text = raw.get("after_text") or raw.get("after") or ""
    highlighted_html = raw.get("highlighted_html") or raw.get("highlighted") or ""

    issues_raw = raw.get("issues") or raw.get("errors") or []
    issues_list = []
    if isinstance(issues_raw, (list, tuple)):
        for idx, item in enumerate(issues_raw):
            if not isinstance(item, dict):
                continue
            issues_list.append({
                "id": item.get("id") or f"e{idx+1}",
                "type": item.get("type") or "grammar",
                "title": item.get("title") or item.get("explanation") or "",
                "explanation": item.get("explanation") or item.get("reason") or "",
                "before": item.get("before") or item.get("fragment") or "",
                "after": item.get("after") or item.get("suggestion") or "",
                "start": int(item.get("start") or 0),
                "end": int(item.get("end") or 0),
                "severity": item.get("severity") or "medium",
            })

    try:
        payload = TextCheckResponse(
            request_id=req_id,
            language=language,
            level=str(raw.get("level") or "A1").upper(),
            scores=scores,
            before_text=str(before_text),
            after_text=str(after_text),
            highlighted_html=str(highlighted_html),
            issues=issues_list,
            recommendations=[str(r) for r in raw.get("recommendations") or []],
            suggested_text=str(raw.get("suggested_text") or raw.get("suggested") or ""),
        )
    except Exception:
        return None

    if payload.level not in {"A1", "A2", "B1", "B2", "C1", "C2"}:
        payload.level = "A1"
    if (not payload.highlighted_html) and payload.issues:
        payload.highlighted_html = _safe_highlight(payload.before_text, payload.issues)
    return payload


@router.post("/free-writing/check")

async def free_writing_check(payload: dict, request: Request, user=Depends(deps.require_user)):
    req_id = _get_request_id(request)
    try:
        data = FreeWritingPayload.model_validate(payload)
    except ValidationError as exc:
        return _free_writing_error("Invalid payload", exc.errors(), status.HTTP_400_BAD_REQUEST, req_id)

    logger.info(
        "[autochecker] free-writing req=%s user=%s prompt_len=%s answer_len=%s",
        req_id,
        getattr(user, "id", None),
        len(data.prompt or ""),
        len(data.student_answer or ""),
    )
    try:
        result: FreeWritingResult = await free_writing_service.check(
            prompt=data.prompt,
            student_answer=data.student_answer,
            rubric=data.rubric,
            language=data.language.lower() if isinstance(data.language, str) else "kk",
            request_id=req_id,
        )
    except LLMClientError as exc:
        return _free_writing_error("LLM error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE, req_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("[autochecker] free-writing req=%s unexpected error", req_id)
        return _free_writing_error("Unexpected error", str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR, req_id)

    return {
        "ok": True,
        "score": result.score,
        "level": result.level,
        "feedback": result.feedback,
        "corrections": result.corrections or [],
        "model": result.model,
        "request_id": req_id,
    }


@router.post("/text-check")
async def text_check(payload: dict, request: Request, user=Depends(deps.require_user)):
    req_id = _get_request_id(request)
    try:
        data = TextCheckPayload.model_validate(payload)
    except ValidationError as exc:
        return _free_writing_error("Invalid payload", exc.errors(), status.HTTP_400_BAD_REQUEST, req_id)

    text = (data.text or "").strip()
    if not text:
        return _free_writing_error("Text is empty", None, status.HTTP_400_BAD_REQUEST, req_id)

    # Guard length
    max_len = 4000
    if len(text) > max_len:
        text = text[:max_len]

    lang_name = "Kazakh" if data.language == "kk" else "Russian"
    prompt = TEXT_CHECK_PROMPT.safe_substitute(
        lang_code=data.language,
        lang_name=lang_name,
        request_id=req_id,
    ) + f"\n\nUser text:\n{text}"

    try:
        raw = await asyncio.to_thread(llm_client.generate_json, prompt, max_retries=2)
        normalized = _normalize_text_response(raw or {}, req_id=req_id, language=data.language)
        if not normalized:
            raise LLMClientError("LLM returned invalid payload")
        return normalized.model_dump()
    except LLMClientError as exc:
        return _free_writing_error("LLM error", str(exc), status.HTTP_502_BAD_GATEWAY, req_id)
    except Exception as exc:  # pragma: no cover
        logger.exception("[autochecker] text-check req=%s failed", req_id)
        return _free_writing_error("Unexpected error", str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR, req_id)


@router.get("/ping")
def autochecker_ping():
    return {"status": "ok"}


@router.post(
    "/eval",
    summary="Evaluate pronunciation via LLM feedback",
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
