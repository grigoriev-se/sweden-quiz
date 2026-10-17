"""Tests for the content model itself, independent of the question data.

Imports only `app.models`, never `app.main`. `app.main` loads and validates
data/questions.json at import, so if the data is broken, every test in a file
importing it errors before running. These tests still run in that case, which
tells you which layer failed: the model, or the data.
"""

import pytest

from pydantic import ValidationError

from app.models import Category, Question

@pytest.mark.parametrize("member", list(Category), ids=lambda c: c.name)
def test_category_value_is_lowercased_ascii_name(member):
    assert member.value == member.name.lower()
    assert member.value.isascii()

@pytest.fixture
def valid_question_base():
    """ a fixture supplying the fields of a valid question """
    return {
        "id":"q1",
        "category":"omvarlden",
        "question":"Vilket år blev Sverige medlem i Europeiska unionen (EU)?",
        "options":["1975", "1985", "1995", "2005"],
        "correctIndex":2,
        "explanation":"Sverige gick med i EU den 1 januari 1995, efter en folkomröstning 1994.",
    }

def test_verified_question_without_source_is_rejected(valid_question_base):
    with pytest.raises(ValidationError):
        Question(
            **valid_question_base,
            verified=True,
            source=None
        )

def test_verified_question_with_a_valid_source_is_accepted(valid_question_base):
    Question(
        **valid_question_base,
        verified=True,
        source={"section":"Nordiskt och europeiskt samarbete", "page":29}
    )
