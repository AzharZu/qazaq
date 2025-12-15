from pathlib import Path

from gtts import gTTS

AUDIO_DIR = Path(__file__).resolve().parents[1] / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def generate_tts(filename: str, text: str, lang: str = "kk") -> Path:
    """Generate TTS audio and return the file path."""
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)
    return filepath


__all__ = ["generate_tts", "AUDIO_DIR"]
