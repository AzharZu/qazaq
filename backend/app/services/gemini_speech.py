import asyncio
import base64
import json
import os
import urllib.error
import urllib.request
from difflib import SequenceMatcher


class GeminiSpeechError(Exception):
    pass


class GeminiSpeechClient:
    def __init__(
        self,
        model_name: str = "models/gemini-pro",
        api_key: str | None = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.timeout = timeout

    def _request(self, payload: dict) -> dict:
        if not self.api_key:
            raise GeminiSpeechError("Gemini not configured")
        url = f"https://generativelanguage.googleapis.com/v1/{self.model_name}:generateContent?key={self.api_key}"
        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
            return json.loads(body)
        except urllib.error.HTTPError as exc:  # pragma: no cover - external dependency
            message = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
            raise GeminiSpeechError(f"Gemini failed: HTTP {exc.code} {message}") from exc
        except Exception as exc:  # pragma: no cover - external dependency
            raise GeminiSpeechError(f"Gemini failed: {exc}") from exc

    async def transcribe_audio(self, file_bytes: bytes, mime_type: str | None = None) -> str:
        """
        Fallback transcription via Gemini (kept for compatibility, primary STT is Google).
        """
        mime = mime_type or self._guess_mime_type(file_bytes)
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Transcribe the following audio and return plaintext only."},
                        {
                            "inline_data": {
                                "mime_type": mime,
                                "data": base64.b64encode(file_bytes).decode("utf-8"),
                            }
                        },
                    ]
                }
            ]
        }
        data = await asyncio.to_thread(self._request, payload)
        text = self._extract_text(data)
        if not text:
            raise GeminiSpeechError("Transcription returned empty result")
        print(f"[autochecker] Gemini transcript (fallback): {text}")
        return text.strip()

    def evaluate_pronunciation(self, reference_text: str, recognized_text: str) -> float:
        ref = (reference_text or "").strip().lower()
        rec = (recognized_text or "").strip().lower()
        if not ref or not rec:
            return 0.0
        ratio = SequenceMatcher(None, ref, rec).ratio()
        return round(ratio, 3)

    async def generate_feedback(self, reference_text: str, recognized_text: str, score: float) -> str:
        """
        Generate feedback via Gemini. Falls back to rule-based text on failure.
        """
        try:
            prompt = (
                "You are a concise pronunciation coach for Kazakh learners.\n"
                f"Expected phrase: {reference_text}\n"
                f"Recognized phrase: {recognized_text}\n"
                f"Score (0-100): {round(score, 1)}\n"
                "Provide 1-2 short sentences of feedback in Russian, focusing on pronunciation fixes."
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
            }
            data = await asyncio.to_thread(self._request, payload)
            feedback = self._extract_text(data)
            if feedback:
                print(f"[autochecker] Gemini feedback: {feedback}")
                return feedback.strip()
        except Exception as exc:  # pragma: no cover - defensive/fallback
            print(f"[autochecker] Gemini feedback fallback due to error: {exc}")

        # Fallback rule-based feedback
        if score >= 90:
            return "Отлично! Произношение почти идеальное."
        if score >= 75:
            return "Хорошо, но есть небольшие неточности. Повторите фразу ещё раз."
        if score >= 50:
            return "Есть заметные расхождения. Попробуйте проговорить чётче, внимание на ударение."
        return "Текст сильно отличается от ожидаемого. Послушайте образец и повторите медленнее."

    def _guess_mime_type(self, file_bytes: bytes) -> str:
        header = file_bytes[:12]
        if header.startswith(b"RIFF") and b"WAVE" in header:
            return "audio/wav"
        if header.startswith(b"OggS"):
            return "audio/ogg"
        if header.startswith(b"fLaC"):
            return "audio/flac"
        if header.startswith(b"ID3") or (len(header) > 0 and header[0] == 0xFF):
            return "audio/mpeg"
        return "audio/webm"

    def _extract_text(self, data: dict) -> str:
        candidates = data.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            for part in parts:
                if "text" in part:
                    return part["text"]
        return ""
