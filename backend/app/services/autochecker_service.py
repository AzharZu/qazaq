import logging

from fastapi import status

from ..core.config import get_settings
from .gemini_speech import GeminiSpeechClient, GeminiSpeechError
from .google_speech import GoogleSpeechClient, GoogleSpeechError
from .llm_client import LLMClient


class AutoCheckerError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(message)
        self.status_code = status_code


class AutoCheckerService:
    def __init__(
        self,
        speech_client: GoogleSpeechClient | None = None,
        feedback_client: GeminiSpeechClient | None = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.speech_client = speech_client or GoogleSpeechClient(api_key=self.settings.google_speech_api_key)
        llm_client = LLMClient()
        self.feedback_client = feedback_client or GeminiSpeechClient(
            llm_client=llm_client,
        )
        # Keep a direct flag for configuration checks (GeminiSpeechClient keeps LLM client inside).
        self.feedback_client.api_key = getattr(self.feedback_client.llm_client, "api_key", None)

    async def process_audio(self, user, audio_bytes: bytes, phrase: str, mime_type: str | None = None) -> dict:
        if not self.speech_client.api_key:
            raise AutoCheckerError("Google Speech is not configured", status.HTTP_503_SERVICE_UNAVAILABLE)
        if not self.feedback_client.llm_client.is_configured():
            raise AutoCheckerError("LLM is not configured", status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            transcript = await self.speech_client.transcribe_audio(audio_bytes)
            score_ratio = self.feedback_client.evaluate_pronunciation(phrase, transcript)
            score = round(score_ratio * 100, 1)
            feedback = await self.feedback_client.generate_feedback(phrase, transcript, score)
            transcript_preview = (transcript or "")[:200]
            feedback_preview = (feedback or "")[:200]
            self.logger.info("[autochecker] transcript_preview='%s', score=%s", transcript_preview, score)
            self.logger.info("[autochecker] feedback_preview='%s'", feedback_preview)
            return {
                "score": score,
                "feedback": feedback,
                "expected": phrase,
                "transcript": transcript,
            }
        except GoogleSpeechError as exc:
            raise AutoCheckerError(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
        except GeminiSpeechError as exc:
            raise AutoCheckerError(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
