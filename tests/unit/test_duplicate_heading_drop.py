"""
Tests for duplicate consecutive heading deduplication (burn-down item 4).

If two consecutive sections have identical normalized heading text, the later
section is dropped entirely.  Non-consecutive duplicates are left untouched.

Normalization: strip leading/trailing whitespace, collapse internal whitespace
to a single space, lowercase.
"""
from decant.core.model import Heading, Paragraph, Text, Section
from decant.core.parser import (
    drop_duplicate_consecutive_sections,
    _normalize_heading_text,
)


def _make_section(text: str, n_blocks: int = 1) -> Section:
    """Helper: create a Section with a simple text heading and n_blocks paragraphs."""
    heading = Heading(level=2, inlines=[Text(text=text)])
    blocks = [Paragraph(inlines=[Text(text=f"block {i}")]) for i in range(n_blocks)]
    return Section(heading=heading, blocks=blocks)


# ---------------------------------------------------------------------------
# Unit tests for _normalize_heading_text
# ---------------------------------------------------------------------------

def test_normalize_strips_and_lowercases():
    h = Heading(level=2, inlines=[Text(text="  More On This Story  ")])
    assert _normalize_heading_text(h) == "more on this story"


def test_normalize_collapses_internal_whitespace():
    h = Heading(level=2, inlines=[Text(text="Most   Viewed")])
    assert _normalize_heading_text(h) == "most viewed"


# ---------------------------------------------------------------------------
# Unit tests for drop_duplicate_consecutive_sections
# ---------------------------------------------------------------------------

def test_consecutive_duplicate_dropped():
    """Two consecutive identical-heading sections: later one is dropped."""
    a = _make_section("More on this story", n_blocks=1)
    b = _make_section("More on this story", n_blocks=2)
    result = drop_duplicate_consecutive_sections([a, b])
    assert len(result) == 1
    assert result[0] is a


def test_non_consecutive_duplicates_kept():
    """Duplicate headings with a different section in between are both kept."""
    a = _make_section("Introduction")
    mid = _make_section("Body")
    b = _make_section("Introduction")
    result = drop_duplicate_consecutive_sections([a, mid, b])
    assert len(result) == 3


def test_no_duplicates_unchanged():
    """No consecutive duplicates — list is returned unchanged."""
    sections = [_make_section("A"), _make_section("B"), _make_section("C")]
    result = drop_duplicate_consecutive_sections(sections)
    assert len(result) == 3


def test_empty_list():
    assert drop_duplicate_consecutive_sections([]) == []


def test_single_section():
    s = _make_section("Only")
    result = drop_duplicate_consecutive_sections([s])
    assert result == [s]


def test_case_insensitive_match():
    """Normalization is case-insensitive."""
    a = _make_section("More On This Story")
    b = _make_section("more on this story")
    result = drop_duplicate_consecutive_sections([a, b])
    assert len(result) == 1

