import base64
import logging
from functools import lru_cache
from typing import Optional
from urllib.request import urlopen, Request

from google.cloud import speech
from google.api_core.exceptions import GoogleAPICallError

from ..core.config import get_settings

logger = logging.getLogger(__name__)


def _cosine_similarity(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    from collections import Counter

    ca, cb = Counter(a), Counter(b)
    shared = set(ca) & set(cb)
    dot = sum(ca[w] * cb[w] for w in shared)
    norm_a = sum(v * v for v in ca.values()) ** 0.5
    norm_b = sum(v * v for v in cb.values()) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _tokenize(text: str) -> list[str]:
    return [t for t in (text or "").lower().split() if t.strip()]


@lru_cache()
def _speech_client() -> Optional[speech.SpeechClient]:
    try:
        return speech.SpeechClient()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Speech client unavailable: %s", exc)
        return None


def fetch_audio_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "QazaqMentor/1.0"})
    with urlopen(req) as resp:
        return resp.read()


def transcribe_audio(audio_bytes: bytes, language_code: str = "kk-KZ") -> str:
    client = _speech_client()
    if not client:
        return ""
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code=language_code,
        enable_automatic_punctuation=True,
    )
    try:
        response = client.recognize(config=config, audio=audio)
        transcripts = [alt.transcript for result in response.results for alt in result.alternatives]
        return transcripts[0] if transcripts else ""
    except GoogleAPICallError as exc:  # pragma: no cover - defensive
        logger.warning("Speech API error: %s", exc)
        return ""
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Speech transcription failed: %s", exc)
        return ""


def score_pronunciation(reference_audio: bytes | None, user_audio: bytes, expected_text: str | None = None) -> dict:
    settings = get_settings()
    lang = "kk-KZ"
    ref_text = ""
    if reference_audio:
        ref_text = transcribe_audio(reference_audio, language_code=lang)
    if not ref_text and expected_text:
        ref_text = expected_text
    user_text = transcribe_audio(user_audio, language_code=lang)

    sim = _cosine_similarity(_tokenize(ref_text), _tokenize(user_text)) if ref_text and user_text else 0.0
    score = int(round(sim * 100)) if ref_text and user_text else 0
    comment = "Произношение корректно" if score >= 70 else "Попробуйте ещё"
    return {
        "reference_text": ref_text,
        "user_text": user_text,
        "similarity": sim,
        "score": max(0, min(100, score)),
        "comment": comment,
    }


def decode_base64_audio(b64: str) -> bytes:
    return base64.b64decode(b64)
