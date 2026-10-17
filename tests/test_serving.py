"""Tests for the gate between "validated" and "visible to users".

`select_served` is the whole of that gate, and tests/test_api.py cannot
defend it: every question in data/questions.json is currently verified, so
there `expected` is just "everything" and a filter that filtered nothing
would pass. Replacing the filter body with `list(question_set.questions)` --
i.e. deleting the feature -- kept the whole suite green.

So these tests build their own sets, with a mix of verified and unverified
questions, giving the filter something it can actually get wrong. They import
`select_served` as a function rather than going through the API, because the
interesting cases include one where the app refuses to start and no API
exists to call.
"""

import pytest

from app.main import select_served
from app.models import Question, QuestionSet

SOURCE = {"section": "Landet styrs på olika nivåer", "page": 12}


def question(qid: str, *, verified: bool) -> Question:
    """A valid question that differs from its neighbours only where it matters."""
    return Question(
        id=qid,
        category="styre",
        question=f"Fråga {qid}?",
        options=["Alternativ A", "Alternativ B"],
        correctIndex=0,
        explanation="Därför.",
        verified=verified,
        # Only a verified question is required to cite a source, but giving
        # both one keeps `verified` the single variable under test.
        source=SOURCE,
    )


def question_set(*questions: Question) -> QuestionSet:
    return QuestionSet(
        version=1,
        book_edition="1:a upplagan, korrigerad version 2026-08-10",
        questions=list(questions),
    )


def test_unverified_questions_are_not_served():
    """The point of the whole mechanism."""
    served = select_served(
        question_set(
            question("q1", verified=True),
            question("q2", verified=False),
            question("q3", verified=True),
        )
    )
    assert [q.id for q in served.questions] == ["q1", "q3"]


def test_a_set_where_nothing_is_verified_refuses_to_start():
    """An empty quiz is a worse outcome than a failed deploy, so this raises
    at import time and the app never boots. The check is explicit in
    select_served precisely so the message says why."""
    with pytest.raises(RuntimeError, match="No verified questions"):
        select_served(
            question_set(
                question("q1", verified=False),
                question("q2", verified=False),
            )
        )


def test_the_error_names_how_many_questions_were_loaded():
    """"2 question(s) loaded, none verified" is the difference between "I
    forgot the flag" and "the file did not load at all"."""
    with pytest.raises(RuntimeError, match=r"2 question\(s\)"):
        select_served(
            question_set(
                question("q1", verified=False),
                question("q2", verified=False),
            )
        )


def test_an_all_verified_set_is_served_whole():
    """The boundary the other way: filtering must not drop anything it should
    keep. This is the case data/questions.json is in today, which is why it
    cannot be the only one tested."""
    served = select_served(
        question_set(question("q1", verified=True), question("q2", verified=True))
    )
    assert [q.id for q in served.questions] == ["q1", "q2"]


def test_filtering_keeps_the_set_metadata():
    """Serving is a filtered *view*, not a new set. `book_edition` is what
    makes every cited page number meaningful, so losing it in the copy would
    quietly strip the provenance the whole `source` field exists to carry."""
    original = question_set(question("q1", verified=True), question("q2", verified=False))
    served = select_served(original)

    assert served.book_edition == original.book_edition
    assert served.version == original.version


def test_the_original_set_is_left_alone():
    """Unverified drafts must survive in QUESTION_SET: /api/health reports the
    full count, and they are still validated at startup. Filtering into a copy
    is what keeps both true."""
    original = question_set(question("q1", verified=True), question("q2", verified=False))
    select_served(original)

    assert len(original.questions) == 2
