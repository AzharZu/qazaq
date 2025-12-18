import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.api.routes.autochecker import _normalize_text_response, TextCheckIssue  # noqa: E402


def test_normalize_builds_highlight():
    raw = {
        "level": "b2",
        "scores": {"grammar": 7, "lexicon": 8, "spelling": 6, "punctuation": 5, "overall": 75},
        "before_text": "Hello world",
        "after_text": "Hello, world!",
        "issues": [
            {
                "id": "e1",
                "type": "grammar",
                "title": "Comma",
                "explanation": "Need comma",
                "before": "Hello world",
                "after": "Hello, world",
                "start": 5,
                "end": 11,
                "severity": "low",
            }
        ],
        "recommendations": ["Use comma"],
        "suggested_text": "Hello, world!",
    }
    resp = _normalize_text_response(raw, req_id="r1", language="ru")
    assert resp is not None
    assert resp.ok is True
    assert resp.level == "B2"
    assert "<mark" in resp.highlighted_html
    assert 'data-error-id="e1"' in resp.highlighted_html


def test_normalize_invalid_returns_none():
    resp = _normalize_text_response({}, req_id="r2", language="kk")
    assert resp is None
