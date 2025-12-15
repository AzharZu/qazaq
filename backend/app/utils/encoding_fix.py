def _looks_mojibake(text: str) -> bool:
    """Heuristic: mojibake often contains many 'Ð', 'Ñ', 'Ò', 'Ó' characters."""
    if not text or not isinstance(text, str):
        return False
    suspect_chars = sum(1 for ch in text if ch in "ÐÑÒÓðñº�")
    return len(text) > 0 and suspect_chars / len(text) > 0.1


def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return text
    cleaned = text
    if _looks_mojibake(text):
        try:
            decoded = text.encode("latin1").decode("utf-8")
            cleaned = decoded
        except Exception:
            cleaned = text
    return cleaned


def clean_encoding(value):
    """Recursively fix encoding issues across nested payloads."""
    if isinstance(value, str):
        return fix_mojibake(value)
    if isinstance(value, list):
        return [clean_encoding(item) for item in value]
    if isinstance(value, dict):
        return {key: clean_encoding(val) for key, val in value.items()}
    return value
