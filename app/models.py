"""Pydantic models describing the shape of quiz content.

These are not decoration. They are the contract for what a valid question is,
and they are enforced at startup: if `data/questions.json` is malformed, the
app refuses to start. A deploy of broken content fails loudly at boot instead
of quietly serving a quiz where question 4 has no right answer.

Pydantic is doing three jobs here:
  1. parsing   — JSON text into Python objects
  2. validating — types AND our own rules (see the model_validators)
  3. serialising — Python objects back into the JSON the browser receives
"""

from pydantic import StringConstraints, BaseModel, ConfigDict, Field, model_validator
from typing import Annotated
from enum import StrEnum

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Category(StrEnum):
    SAMHALLE = "samhalle"
    KULTUR = "kultur"
    GEOGRAFI = "geografi"


class Question(BaseModel):
    # populate_by_name lets us build a Question with EITHER `correct_index`
    # (Python style) or `correctIndex` (the JSON key). See the alias note below.
    model_config = ConfigDict(populate_by_name=True)

    id: NonEmptyStr

    category: Category

    question: NonEmptyStr
    explanation: NonEmptyStr
    options: list[NonEmptyStr] = Field(min_length=2)   # 2+ options, none blank

    # Two naming conventions meet at this boundary: JavaScript says camelCase,
    # Python says snake_case. The alias lets each side keep its own idiom —
    # the field is `correct_index` in Python and `correctIndex` in JSON, and
    # FastAPI serialises using the alias, so the frontend never sees the
    # difference. This is the standard fix for that clash.
    correct_index: int = Field(alias="correctIndex", ge=0)


    @model_validator(mode="after")
    def correct_index_must_point_at_a_real_option(self):
        """Type-checking alone would happily accept correctIndex: 99.

        `mode="after"` means this runs once the individual fields are already
        parsed, so we can compare them against each other.
        """
        if self.correct_index >= len(self.options):
            raise ValueError(
                f"question {self.id!r}: correctIndex is {self.correct_index}, "
                f"but there are only {len(self.options)} options"
            )
        return self

    @model_validator(mode="after")
    def answers_must_be_unique(self):
        if len(self.options) != len(set(self.options)):
            raise ValueError(
                f"Answers to question {self.id!r} are not unique!"
            )
        return self

class QuestionSet(BaseModel):
    """The whole file: a version plus the questions.

    This mirrors the shape of questions.json on purpose. Wrapping the list in
    an object is what lets us add metadata later without breaking any client —
    the same reasoning as when we chose the file format.
    """

    version: int
    questions: list[Question] = Field(min_length=1)

    @model_validator(mode="after")
    def ids_must_be_unique(self):
        seen = set()
        for q in self.questions:
            if q.id in seen:
                raise ValueError(f"duplicate question id: {q.id!r}")
            seen.add(q.id)
        return self


# TODO (phase 2): add `source` (where the fact came from) and `verified: bool`
# so unreviewed LLM-drafted questions can be kept out of the served set.
