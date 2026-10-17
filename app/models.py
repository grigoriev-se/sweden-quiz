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
    """Which chapter of UHR's official study book teaches this question.

    The chapters are the test's subject areas, so one field covers both
    "where is this taught" and "what is it about". Inledning is framing, not
    examinable content, so it has no member.
    """

    LANDET = "landet"
    DEMOKRATI = "demokrati"
    STYRE = "styre"
    VAL_OCH_PARTIER = "val_och_partier"
    LAG_OCH_RATT = "lag_och_ratt"
    MEDIA = "media"
    MANSKLIGA_RATTIGHETER = "manskliga_rattigheter"
    ARBETSMARKNAD_OCH_PRIVATEKONOMI = "arbetsmarknad_och_privatekonomi"
    VALFARDSSAMHALLET = "valfardssamhallet"
    HISTORIA = "historia"
    OMVARLDEN = "omvarlden"
    SEKULAR_STAT = "sekular_stat"
    TRADITIONER = "traditioner"


class Source(BaseModel):
    """Where in UHR's book this question's fact is taught.

    The chapter is already recorded in `Question.category`, so this holds only
    what is more specific. Storing the chapter twice would let the two copies
    disagree.

    The book's edition belongs once on QuestionSet, not on every question.
    """

    # See the note on Question.model_config: a misspelled key is a mistake,
    # not an extension point.
    model_config = ConfigDict(extra="forbid")

    section: NonEmptyStr          # e.g. "Nordiskt och europeiskt samarbete"
    page: int = Field(ge=1)


class Question(BaseModel):
    # populate_by_name lets us build a Question with EITHER `correct_index`
    # (Python style) or `correctIndex` (the JSON key). See the alias note below.
    #
    # extra="forbid" is the important half. Pydantic's default is to ignore
    # keys it does not recognise, which makes a typo silent: `"verfied": true`
    # would parse cleanly, leave `verified` at its False default, and the
    # question would validate, load, and never be served -- with nothing
    # printed anywhere. That is the one way bad content can reach production
    # quietly, which is exactly what startup validation exists to prevent.
    # Forbidding extras turns every misspelled key into a boot failure that
    # names the offending field.
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

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

    # Has a human checked this question against the source?
    #
    # Default False on purpose: a question where the field was forgotten is
    # treated as unchecked and is not served. The careless path is the safe
    # one. Only verified questions reach users; unverified drafts still live
    # in the repo and are still fully validated.
    verified: bool = False

    # Optional, because a draft can exist before anyone has cited it.
    # `verified_question_must_cite_source` below stops it staying that way:
    # a question can be uncited, or verified, but not both.
    source: Source | None = None

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

    @model_validator(mode="after")
    def verified_question_must_cite_source(self):
        if self.verified and self.source is None:
            raise ValueError(
                f"question {self.id!r} is verified but does not cite a source!"
            )
        return self


class QuestionSet(BaseModel):
    """The whole file: a version plus the questions.

    This mirrors the shape of questions.json on purpose. Wrapping the list in
    an object is what lets us add metadata later without breaking any client —
    the same reasoning as when we chose the file format.
    """

    model_config = ConfigDict(extra="forbid")

    version: int

    # JSON has no comment syntax, so questions.json carries its header comment
    # in a key. Declared rather than tolerated: with extra="forbid" an
    # undeclared key is now an error, and the alternative -- allowing extras
    # here -- would also let `"book_editon"` through silently, leaving every
    # page number without the edition it is meaningless without.
    #
    # exclude=True keeps it off the wire. It is a comment addressed to whoever
    # edits the file, not content, and declaring it without this would start
    # shipping it to every browser on every load -- which ignoring it as an
    # unknown key never did.
    note: str | None = Field(default=None, exclude=True)

    # Which edition of UHR's book the page numbers in `Source` refer to.
    # Recorded once here rather than on every question: a page number means
    # nothing without it, and UHR has already issued a corrected version that
    # changed content on a page we cite.
    book_edition: str | None = None

    questions: list[Question] = Field(min_length=1)

    @model_validator(mode="after")
    def ids_must_be_unique(self):
        seen = set()
        for q in self.questions:
            if q.id in seen:
                raise ValueError(f"duplicate question id: {q.id!r}")
            seen.add(q.id)
        return self

