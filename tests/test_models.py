"""Tests for the content model itself, independent of the question data.

Imports only `app.models`, never `app.main`. `app.main` loads and validates
data/questions.json at import, so if the data is broken, every test in a file
importing it errors before running. These tests still run in that case, which
tells you which layer failed: the model, or the data.
"""

import pytest

from app.models import Category

@pytest.mark.parametrize("member", list(Category), ids=lambda c: c.name)
def test_category_value_is_lowercased_ascii_name(member):
    assert member.value == member.name.lower()
    assert member.value.isascii()
