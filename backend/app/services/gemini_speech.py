import asyncio
from difflib import SequenceMatcher

from .llm_client import LLMClient, LLMClientError


class GeminiSpeechError(Exception):
    pass


class GeminiSpeechClient:
    def __init__(
        self,
        model_name: str = "models/gemini-pro",  # kept for backward compatibility
        api_key: str | None = None,
        timeout: int = 30,
        llm_client: LLMClient | None = None,
    ):
        self.timeout = timeout
        self.llm_client = llm_client or LLMClient(api_key=api_key, model=model_name, timeout_seconds=timeout)

    async def transcribe_audio(self, file_bytes: bytes, mime_type: str | None = None) -> str:
        raise GeminiSpeechError("LLM audio transcription is not supported in this build")

    def evaluate_pronunciation(self, reference_text: str, recognized_text: str) -> float:
        ref = (reference_text or "").strip().lower()
        rec = (recognized_text or "").strip().lower()
        if not ref or not rec:
            return 0.0
        ratio = SequenceMatcher(None, ref, rec).ratio()
        return round(ratio, 3)

    async def generate_feedback(self, reference_text: str, recognized_text: str, score: float) -> str:
        try:
            prompt = (
                "You are a concise pronunciation coach for Kazakh learners.\n"
                f"Expected phrase: {reference_text}\n"
                f"Recognized phrase: {recognized_text}\n"
                f"Score (0-100): {round(score, 1)}\n"
                "Provide 1-2 short sentences of feedback in Russian, focusing on pronunciation fixes."
            )
            feedback = await asyncio.to_thread(self.llm_client.generate_text, prompt)
            if feedback:
                return feedback.strip()
        except (LLMClientError, Exception) as exc:  # pragma: no cover - defensive/fallback
            print(f"[autochecker] LLM feedback fallback due to error: {exc}")

        # Fallback rule-based feedback
        if score >= 90:
            return "Отлично! Произношение почти идеальное."
        if score >= 75:
            return "Хорошо, но есть небольшие неточности. Повторите фразу ещё раз."
        if score >= 50:
            return "Есть заметные расхождения. Попробуйте проговорить чётче, внимание на ударение."
        return "Текст сильно отличается от ожидаемого. Послушайте образец и повторите медленнее."
