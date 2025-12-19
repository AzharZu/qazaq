import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure `app` package is discoverable when running tests from repo root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.main import app  # noqa: E402
from app.api import deps  # noqa: E402
from app.api.routes import autochecker  # noqa: E402


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[deps.require_user] = lambda: object()
    yield
    app.dependency_overrides.pop(deps.require_user, None)


@pytest.fixture
def client():
    return TestClient(app)


def _dummy_summary():
    return {"grammar": 8, "lexicon": 7, "spelling": 9, "punctuation": 8}


def _issues(count: int):
    return [
        {
            "type": "grammar",
            "severity": "medium",
            "bad_excerpt": f"қате {i}",
            "fix": f"дұрыс {i}",
            "why": "қысқа түсіндірме",
        }
        for i in range(count)
    ]


def test_kazakh_input_returns_kazakh(monkeypatch, client):
    prompts: list[str] = []

    def fake_generate_json(prompt: str, *args, **kwargs):
        prompts.append(prompt)
        return {
            "language": "kk",
            "level": "A1",
            "score": 88,
            "summary": _dummy_summary(),
            "issues": _issues(2),
            "corrected_text": "Сәлем, бұл тест.",
        }

    monkeypatch.setattr(autochecker.llm_client, "generate_json", fake_generate_json)
    monkeypatch.setattr(autochecker.llm_client, "is_configured", lambda: True)

    resp = client.post("/api/autochecker/text-check", json={"text": "Сәлем, бұл тест.", "language": "kk", "level": "A1"})
    data = resp.json()

    assert resp.status_code == 200
    assert data["language"] == "kk"
    assert "Привет" not in data["corrected_text"]
    assert prompts and "NEVER TRANSLATE" in prompts[0]


def test_ru_language_overrides_to_kazakh(monkeypatch, client):
    prompts: list[str] = []

    def fake_generate_json(prompt: str, *args, **kwargs):
        prompts.append(prompt)
        return {
            "language": "kk",
            "level": "A1",
            "score": 75,
            "summary": _dummy_summary(),
            "issues": _issues(1),
            "corrected_text": "Мен қазақ тілінде жазамын.",
        }

    monkeypatch.setattr(autochecker.llm_client, "generate_json", fake_generate_json)
    monkeypatch.setattr(autochecker.llm_client, "is_configured", lambda: True)

    resp = client.post("/api/autochecker/text-check", json={"text": "Мен қазақ тілінде жазамын.", "language": "ru", "level": "A1"})
    data = resp.json()

    assert resp.status_code == 200
    assert data["language"] == "kk"
    assert data.get("warning")
    assert prompts and "Kazakh (kk)" in prompts[0]


def test_level_controls_issue_cap(monkeypatch, client):
    prompts: list[str] = []
    payloads = [
        {
            "language": "kk",
            "level": "A1",
            "score": 60,
            "summary": _dummy_summary(),
            "issues": _issues(12),
            "corrected_text": "Сәлем, мәтін.",
        },
        {
            "language": "kk",
            "level": "B1",
            "score": 82,
            "summary": _dummy_summary(),
            "issues": _issues(12),
            "corrected_text": "Сәлем, мәтін.",
        },
    ]

    def fake_generate_json(prompt: str, *args, **kwargs):
        prompts.append(prompt)
        return payloads.pop(0)

    monkeypatch.setattr(autochecker.llm_client, "generate_json", fake_generate_json)
    monkeypatch.setattr(autochecker.llm_client, "is_configured", lambda: True)

    resp_a1 = client.post("/api/autochecker/text-check", json={"text": "Сәлем, мәтін.", "language": "kk", "level": "A1"})
    resp_b1 = client.post("/api/autochecker/text-check", json={"text": "Сәлем, мәтін.", "language": "kk", "level": "B1"})

    data_a1 = resp_a1.json()
    data_b1 = resp_b1.json()

    assert len(data_a1["issues"]) == 7  # capped for A1
    assert len(data_b1["issues"]) == 12  # B1 keeps more detail
    assert "Level: A1" in prompts[0] and "Level: B1" in prompts[1]
