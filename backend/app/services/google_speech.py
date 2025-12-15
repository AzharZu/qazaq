import asyncio
import base64
import io
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import wave
import aifc
import audioop
from typing import Optional, Tuple


class GoogleSpeechError(Exception):
    pass


class GoogleSpeechClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        language_code: str = "kk-KZ",
        encoding: str = "LINEAR16",
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("GOOGLE_SPEECH_API_KEY")
        self.language_code = language_code
        self.encoding = encoding
        self.timeout = timeout

    async def transcribe_audio(self, file_bytes: bytes) -> str:
        if not self.api_key:
            raise GoogleSpeechError("GOOGLE_SPEECH_API_KEY is not configured")
        linear_bytes = await asyncio.to_thread(self._ensure_linear16, file_bytes)
        payload = {
            "config": {
                "languageCode": self.language_code,
                "encoding": self.encoding,
                "sampleRateHertz": 16000,
            },
            "audio": {"content": base64.b64encode(linear_bytes).decode("utf-8")},
        }
        try:
            data = await asyncio.to_thread(self._send_request, payload)
            results = data.get("results") or []
            if not results:
                raise GoogleSpeechError("No transcription results returned")
            alternatives = results[0].get("alternatives") or []
            if not alternatives:
                raise GoogleSpeechError("No alternatives in transcription response")
            transcript = alternatives[0].get("transcript") or ""
            if not transcript.strip():
                raise GoogleSpeechError("Transcription returned empty text")
            print(f"[autochecker] Google STT transcript: {transcript}")
            return transcript.strip()
        except GoogleSpeechError:
            raise
        except Exception as exc:  # pragma: no cover - external dependency
            raise GoogleSpeechError(f"Google Speech failed: {exc}") from exc

    def _ensure_linear16(self, file_bytes: bytes) -> bytes:
        """
        Convert arbitrary audio bytes to 16kHz mono PCM (LINEAR16).
        Tries ffmpeg first, then falls back to stdlib wave/aifc+audioop.
        """
        if shutil.which("ffmpeg"):
            try:
                return self._convert_with_ffmpeg(file_bytes)
            except Exception:
                pass  # fall back
        try:
            return self._convert_with_stdlib(file_bytes)
        except Exception as exc:
            raise GoogleSpeechError(f"Audio conversion failed: {exc}") from exc

    def _convert_with_ffmpeg(self, file_bytes: bytes) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as src:
            src.write(file_bytes)
            src.flush()
            src_path = src.name
        dst_fd, dst_path = tempfile.mkstemp(suffix=".wav")
        os.close(dst_fd)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            src_path,
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            "-acodec",
            "pcm_s16le",
            dst_path,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with open(dst_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.remove(src_path)
            except OSError:
                pass
            try:
                os.remove(dst_path)
            except OSError:
                pass

    def _convert_with_stdlib(self, file_bytes: bytes) -> bytes:
        stream = io.BytesIO(file_bytes)
        reader = None
        close_reader = False
        try:
            try:
                reader = wave.open(stream, "rb")
                comptype = "NONE"
            except wave.Error:
                stream.seek(0)
                reader = aifc.open(stream, "rb")
                comptype = reader.getcomptype().upper()
            n_channels = reader.getnchannels()
            sampwidth = reader.getsampwidth()
            framerate = reader.getframerate()
            frames = reader.readframes(reader.getnframes())
            close_reader = True
        finally:
            if close_reader and reader:
                reader.close()

        # Handle simple compressed AIFF (u-law/a-law) if present.
        if comptype in {"ULAW", "U-LAW", "ULAW1"}:
            frames = audioop.ulaw2lin(frames, 2)
            sampwidth = 2
        elif comptype in {"ALAW", "A-LAW"}:
            frames = audioop.alaw2lin(frames, 2)
            sampwidth = 2
        elif comptype not in {"NONE", "", None}:
            raise GoogleSpeechError(
                f"Unsupported AIFF compression '{comptype}'. "
                "Provide PCM/ULAW/ALAW audio or install ffmpeg for broader support."
            )

        target_rate = 16000
        target_width = 2
        target_channels = 1

        audio = frames
        if sampwidth != target_width:
            audio = audioop.lin2lin(audio, sampwidth, target_width)
        if n_channels != target_channels:
            audio = audioop.tomono(audio, target_width, 1, 1)
        if framerate != target_rate:
            audio, _ = audioop.ratecv(audio, target_width, target_channels, framerate, target_rate, None)

        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(target_channels)
            wf.setsampwidth(target_width)
            wf.setframerate(target_rate)
            wf.writeframes(audio)
        return out.getvalue()

    def _send_request(self, payload: dict) -> dict:
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"
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
            raise GoogleSpeechError(f"Google Speech failed: HTTP {exc.code} {message}") from exc
