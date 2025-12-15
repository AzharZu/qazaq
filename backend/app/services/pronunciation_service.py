import random
from pathlib import Path
from typing import Tuple


async def evaluate_pronunciation(audio_path: str, target_word: str) -> float:
    """
    Return a match score between 0 and 1 for the given audio and target word.

    Stub implementation: mixes audio file length and a random factor to produce
    a deterministic-ish score suitable for MVP/testing. Replace with a real
    model (e.g., embeddings cosine similarity) when available.
    """
    path = Path(audio_path)
    size_factor = min(max(path.stat().st_size / 1_000_000, 0.1), 1.0) if path.exists() else 0.1
    randomness = random.uniform(0.4, 1.0)
    word_factor = (len(target_word.strip()) % 5) / 10  # slight variance by word
    score = max(0.0, min(1.0, (size_factor * 0.4) + (randomness * 0.5) + word_factor * 0.1))
    return round(score, 3)


def score_to_status(score: float) -> str:
    if score > 0.75:
        return "excellent"
    if score > 0.5:
        return "ok"
    return "bad"


def feedback_for_score(score: float) -> str:
    if score > 0.75:
        return "Отлично! Произнесено уверенно."
    if score > 0.5:
        return "Хорошо, но обратите внимание на окончания и ударение."
    return "Попробуйте еще раз: говорите медленнее и четче."
