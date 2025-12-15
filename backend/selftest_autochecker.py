"""
Self-test for the autochecker pipeline.

Usage:
  python selftest_autochecker.py --server http://127.0.0.1:8000 \
    --email admin@example.com --password admin123 --phrase "Сәлем" \
    [--file /path/to/audio.wav]

If --file is omitted, a synthetic 16kHz sine wave is generated (may not be
recognizable speech; STT could return empty). Provide a real spoken WAV/AIFF
for a meaningful end-to-end check.
"""

import argparse
import asyncio
import io
import os
import math
import sys
import wave
from pathlib import Path

import requests

from app.services.google_speech import GoogleSpeechClient, GoogleSpeechError

# Simple .env loader (comment-aware) to ease local testing
def load_env_if_needed():
    if os.getenv("GEMINI_API_KEY") and os.getenv("GOOGLE_SPEECH_API_KEY"):
        return
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        # try repo root /backend/.env if run from root
        env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        with env_path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
        print(f"[selftest] Loaded env from {env_path}")
    else:
        print("[selftest] No .env file found; relying on existing environment variables.")


def generate_sine_wav(duration_sec: float = 1.2, freq: float = 440.0, rate: int = 16000) -> bytes:
    samples = int(duration_sec * rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        frames = bytearray()
        for i in range(samples):
            val = int(0.3 * 32767 * math.sin(2 * math.pi * freq * (i / rate)))
            frames += val.to_bytes(2, byteorder="little", signed=True)
        wf.writeframes(frames)
    return buf.getvalue()


async def run_stt(file_bytes: bytes) -> str:
    client = GoogleSpeechClient()
    return await client.transcribe_audio(file_bytes)


def login(session: requests.Session, server: str, email: str, password: str):
    resp = session.post(
        f"{server}/api/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def call_autochecker(session: requests.Session, server: str, phrase: str, file_bytes: bytes):
    files = {"audio": ("test.wav", file_bytes, "audio/wav")}
    data = {"phrase": phrase}
    resp = session.post(f"{server}/api/autochecker/eval", files=files, data=data, timeout=60)
    return resp


async def main():
    load_env_if_needed()
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default="admin@example.com")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--phrase", default="Сәлем")
    parser.add_argument("--file", help="Path to WAV/AIFF/other audio. If omitted, synthetic tone is used.")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "rb") as f:
            file_bytes = f.read()
    else:
        file_bytes = generate_sine_wav()
        print("[selftest] Using synthetic sine wave; STT may not produce speech text.")

    try:
        transcript = await run_stt(file_bytes)
        print(f"[selftest] STT transcript: {transcript}")
    except GoogleSpeechError as exc:
        print(f"[selftest] STT FAILED: {exc}")
        sys.exit(1)

    session = requests.Session()
    try:
        user = login(session, args.server, args.email, args.password)
        print(f"[selftest] Logged in as: {user.get('email')}")
    except Exception as exc:
        print(f"[selftest] LOGIN FAILED: {exc}")
        sys.exit(1)

    try:
        resp = call_autochecker(session, args.server, args.phrase, file_bytes)
        print(f"[selftest] Autochecker status: {resp.status_code}")
        print(f"[selftest] Response: {resp.text}")
        if resp.status_code != 200:
            sys.exit(1)
    except Exception as exc:
        print(f"[selftest] AUTOCHECKER FAILED: {exc}")
        sys.exit(1)

    print("[selftest] PASS")


if __name__ == "__main__":
    asyncio.run(main())
