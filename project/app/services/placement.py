import math


def compute_level(score: int, total_questions: int = 20) -> str:
    """Return CEFR-like level for a normalized 0-20 score."""
    normalized = score
    if total_questions and total_questions != 20:
        normalized = math.ceil(score * 20 / total_questions)
    if normalized >= 18:
        return "B2"
    if normalized >= 14:
        return "B1"
    if normalized >= 10:
        return "A2"
    if normalized >= 6:
        return "A1"
    return "A0"
