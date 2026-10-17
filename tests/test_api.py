"""Tests for the quiz API.

Run them with:

    .venv\\Scripts\\python.exe -m pytest -v

TestClient sends real requests through the real app, but in-process — no
server to start, no port, no network. It is as fast as calling a function
while still exercising routing, serialisation and status codes.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import QUESTION_SET, SERVED_SET, app

client = TestClient(app)


# --------------------------------------------------------------------------
# The API behaves
# --------------------------------------------------------------------------

def test_health_reports_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


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


# --------------------------------------------------------------------------
# Only verified content is served
# --------------------------------------------------------------------------

def test_api_serves_exactly_the_verified_questions():
    """Everything in the file is validated; only verified questions ship."""
    expected = [q for q in QUESTION_SET.questions if q.verified]
    served = client.get("/api/questions").json()["questions"]

    assert len(served) == len(expected)
    assert {q["id"] for q in served} == {q.id for q in expected}


def test_nothing_unverified_is_served():
    for q in SERVED_SET.questions:
        assert q.verified, f"{q.id} is served but not verified"
        assert q.source is not None, f"{q.id} is served without a source"


def test_served_set_is_not_empty():
    """Guards against quietly shipping a quiz with no questions.

    select_served() already refuses to start in that case, so this test fails
    at collection rather than here — but it states the requirement explicitly.
    """
    assert len(SERVED_SET.questions) > 0


def test_health_reports_both_counts():
    body = client.get("/api/health").json()
    assert body["questions"] == len(QUESTION_SET.questions)
    assert body["served"] == len(SERVED_SET.questions)


def _normalise(text: str) -> str:
    """Lowercased, with runs of whitespace collapsed.

    Enough to catch copy-paste and reformatting, not clever enough to catch
    rephrasing. See the note in PLAN.md.
    """
    return " ".join(text.lower().split())


def test_question_texts_are_unique():
    """Duplicate ids are caught by the model; duplicate *questions* are not.

    Asking the same thing twice is a content bug rather than a broken app, so
    it fails the build here instead of refusing to boot. It matters most when
    drafting in batches from overlapping sections, where the same fact is easy
    to turn into the same question twice.
    """
    seen: dict[str, str] = {}
    for q in QUESTION_SET.questions:
        key = _normalise(q.question)
        assert key not in seen, f"{q.id} asks the same question as {seen[key]}"
        seen[key] = q.id



def test_the_note_is_not_shipped_to_the_browser():
    """`note` carries questions.json's header comment, because JSON has no
    comment syntax. It is declared on the model so that forbidding unknown
    keys does not reject the file — but it is editor-facing commentary, not
    content, and declaring a field is enough to start serialising it.
    """
    body = client.get("/api/questions").json()
    assert "note" not in body
