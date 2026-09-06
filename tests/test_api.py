"""Tests for the quiz API.

Run them with:

    .venv\\Scripts\\python.exe -m pytest -v

TestClient sends real requests through the real app, but in-process — no
server to start, no port, no network. It is as fast as calling a function
while still exercising routing, serialisation and status codes.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import QUESTION_SET, app

client = TestClient(app)


# --------------------------------------------------------------------------
# The API behaves
# --------------------------------------------------------------------------

def test_health_reports_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_questions_endpoint_returns_every_question():
    res = client.get("/api/questions")
    assert res.status_code == 200
    assert len(res.json()["questions"]) == len(QUESTION_SET.questions)


def test_api_speaks_camelcase_to_the_frontend():
    """The Python field is correct_index; the wire format must be correctIndex.

    Without this test, renaming a field in models.py would silently break the
    JavaScript — which would fail in the browser, far from any Python error.
    Contract tests belong wherever two languages meet.
    """
    first = client.get("/api/questions").json()["questions"][0]
    assert "correctIndex" in first
    assert "correct_index" not in first


def test_root_serves_the_frontend():
    res = client.get("/")
    assert res.status_code == 200
    assert "<title>" in res.text


# --------------------------------------------------------------------------
# The CONTENT is sane
#
# These do not test our code at all — they test the question data. That is the
# point: this suite is the safety net for the phase-2 content work, where the
# realistic mistake is a bad question, not a bad function.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("q", QUESTION_SET.questions, ids=lambda q: q.id)
def test_question_is_well_formed(q):
    """parametrize runs this once PER QUESTION, so a failure names the culprit
    ("test_question_is_well_formed[q4]") instead of just saying something,
    somewhere, is wrong."""
    assert q.question.strip(), "question text is empty"
    assert q.explanation.strip(), "explanation is empty"
    assert 0 <= q.correct_index < len(q.options)
    assert len(set(q.options)) == len(q.options), "duplicate options"


def test_question_ids_are_unique():
    ids = [q.id for q in QUESTION_SET.questions]
    assert len(ids) == len(set(ids))
