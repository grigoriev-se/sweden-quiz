"""Tests for the content model itself, independent of the question data.

Imports only `app.models`, never `app.main`. `app.main` loads and validates
data/questions.json at import, so if the data is broken, every test in a file
importing it errors before running. These tests still run in that case, which
tells you which layer failed: the model, or the data.
"""

import pytest

from pydantic import ValidationError

from app.models import Category, Question, QuestionSet

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


# --------------------------------------------------------------------------
# Unknown fields
#
# The regression tests for the only way bad content used to reach production
# silently. Pydantic's default is to ignore keys it does not recognise, so
# `"verfied": true` parsed fine, left `verified` at False, and the question
# vanished from the quiz with nothing printed anywhere. Everything else in
# this file fails loudly already; these two are about failing *at all*.
# --------------------------------------------------------------------------

def test_misspelled_field_is_rejected(valid_question_base):
    """`verfied` must not quietly become "unverified"."""
    with pytest.raises(ValidationError, match="verfied"):
        Question(**valid_question_base, verfied=True)


def test_misspelled_source_field_is_rejected(valid_question_base):
    with pytest.raises(ValidationError, match="pge"):
        Question(
            **valid_question_base,
            verified=True,
            source={"section": "Nordiskt och europeiskt samarbete", "pge": 29},
        )


# --------------------------------------------------------------------------
# correctIndex points at a real option
# --------------------------------------------------------------------------

def test_correct_index_past_the_last_option_is_rejected(valid_question_base):
    """Four options means the only valid indexes are 0-3. Plain type checking
    would accept 4, or 99, and the frontend would mark every answer wrong."""
    with pytest.raises(ValidationError):
        Question(**{**valid_question_base, "correctIndex": 4})


def test_negative_correct_index_is_rejected(valid_question_base):
    """-1 is a real risk, not a theoretical one: it is what a 1-based habit
    produces, and in JavaScript it would silently index nothing."""
    with pytest.raises(ValidationError):
        Question(**{**valid_question_base, "correctIndex": -1})


def test_last_option_is_a_valid_answer(valid_question_base):
    """The boundary the other direction: index 3 of 4 options must be fine,
    so the check above cannot be tightened into an off-by-one."""
    q = Question(**{**valid_question_base, "correctIndex": 3})
    assert q.correct_index == 3


# --------------------------------------------------------------------------
# Options
# --------------------------------------------------------------------------

def test_duplicate_options_are_rejected(valid_question_base):
    """Two identical options means one of them is right and unmarkable."""
    with pytest.raises(ValidationError):
        Question(**{**valid_question_base, "options": ["1995", "1995", "2005"]})


def test_a_single_option_is_rejected(valid_question_base):
    """A question with one answer is not a question."""
    with pytest.raises(ValidationError):
        Question(**{**valid_question_base, "options": ["1995"]})


def test_blank_option_is_rejected(valid_question_base):
    """NonEmptyStr strips first, so whitespace-only is empty. An invisible
    button is worse than a missing one."""
    with pytest.raises(ValidationError):
        Question(**{**valid_question_base, "options": ["1995", "   "]})


@pytest.mark.parametrize("field", ["id", "question", "explanation"])
def test_blank_text_fields_are_rejected(valid_question_base, field):
    with pytest.raises(ValidationError):
        Question(**{**valid_question_base, field: "  "})


def test_surrounding_whitespace_is_stripped(valid_question_base):
    """Content is hand-edited JSON, so stray spaces arrive. They must not
    reach the duplicate checks, where " 1995" and "1995" would look like two
    different options."""
    q = Question(**{**valid_question_base, "options": [" 1975 ", "1985", " 1995", "2005"]})
    assert q.options == ["1975", "1985", "1995", "2005"]


# --------------------------------------------------------------------------
# Category
# --------------------------------------------------------------------------

def test_unknown_category_is_rejected(valid_question_base):
    """The enum is what stops a typo inventing a fourteenth chapter, which
    would then be missing from any per-category filtering or statistics."""
    with pytest.raises(ValidationError):
        Question(**{**valid_question_base, "category": "omvarlde"})


# --------------------------------------------------------------------------
# Source
# --------------------------------------------------------------------------

def test_page_zero_is_rejected(valid_question_base):
    """Pages are 1-based. 0 is the shape a missing value takes."""
    with pytest.raises(ValidationError):
        Question(
            **valid_question_base,
            verified=True,
            source={"section": "Nordiskt och europeiskt samarbete", "page": 0},
        )


def test_blank_section_is_rejected(valid_question_base):
    """A page number with no section does not survive a new edition."""
    with pytest.raises(ValidationError):
        Question(
            **valid_question_base,
            verified=True,
            source={"section": "  ", "page": 29},
        )


# --------------------------------------------------------------------------
# The set as a whole
# --------------------------------------------------------------------------

def _question_set(*questions, **extra):
    return QuestionSet(version=1, questions=list(questions), **extra)


def test_duplicate_ids_are_rejected(valid_question_base):
    """Ids are permanent and will key attempt logging from phase 3, so two
    questions sharing one is a data bug, not a content bug: it fails in the
    model rather than in a test."""
    a = Question(**valid_question_base)
    b = Question(**{**valid_question_base, "question": "En annan fråga?"})
    assert a.id == b.id
    with pytest.raises(ValidationError, match="duplicate question id"):
        _question_set(a, b)


def test_an_empty_set_is_rejected():
    with pytest.raises(ValidationError):
        _question_set()


def test_misspelled_set_field_is_rejected(valid_question_base):
    """`book_editon` would leave every page number without the edition it is
    meaningless without."""
    with pytest.raises(ValidationError, match="book_editon"):
        _question_set(Question(**valid_question_base), book_editon="1:a upplagan")


def test_the_note_key_is_accepted(valid_question_base):
    """questions.json carries its header comment in a `note` key, because JSON
    has no comments. It is declared, so forbidding extras does not break it."""
    s = _question_set(Question(**valid_question_base), note="Hand-written content.")
    assert s.note == "Hand-written content."
