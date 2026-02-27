"""
Tests for explicit extraction failure when no article body is detected (burn-down item 13).

If the document contains no paragraph block with >= 20 words of non-placeholder prose,
the pipeline raises ValidationError instead of emitting navigation/junk output.

Affected fixtures:
- guardian: extraction failure — all content is navigation/related-links
- theringer: extraction failure — all content is navigation stub

Clean fixture (regression guard):
- smithsonian: real article prose, must NOT fail
"""
import pytest
from pathlib import Path

from flowdoc.core.parser import (
    extract_with_trafilatura,
    parse,
    ValidationError,
    _has_article_body,
)
from flowdoc.core.model import Paragraph, Text, Section, Heading

FIXTURES = Path(__file__).parent / "fixtures" / "user-study"


def _make_section(blocks) -> Section:
    return Section(
        heading=Heading(level=2, inlines=[Text(text="H")]),
        blocks=list(blocks),
    )


def _para(text: str) -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


# ---------------------------------------------------------------------------
# Unit tests for _has_article_body
# ---------------------------------------------------------------------------

def test_has_article_body_true_for_long_prose():
    """A paragraph with >= 20 words qualifies as article body."""
    long_text = "word " * 20  # exactly 20 words
    sections = [_make_section([_para(long_text.strip())])]
    assert _has_article_body(sections) is True


def test_has_article_body_false_for_short_prose():
    """A paragraph with < 20 words does not qualify."""
    short_text = "word " * 19  # 19 words
    sections = [_make_section([_para(short_text.strip())])]
    assert _has_article_body(sections) is False


def test_has_article_body_excludes_placeholders():
    """Placeholder paragraphs ([...]) are excluded from the word count."""
    sections = [_make_section([_para("[Form omitted]"), _para("[Image omitted]")])]
    assert _has_article_body(sections) is False


def test_has_article_body_false_for_empty_sections():
    assert _has_article_body([]) is False


def test_has_article_body_true_when_one_qualifying_para_among_short():
    """One qualifying paragraph is sufficient even if others are short."""
    sections = [_make_section([
        _para("short text"),
        _para("word " * 20),
    ])]
    assert _has_article_body(sections) is True


def test_has_article_body_counts_across_sections():
    """The qualifying paragraph can be in any section."""
    s1 = _make_section([_para("too short")])
    s2 = _make_section([_para("word " * 25)])
    assert _has_article_body([s1, s2]) is True


# ---------------------------------------------------------------------------
# Fixture integration tests
# ---------------------------------------------------------------------------

def test_guardian_raises_validation_error():
    """
    Guardian fixture: Trafilatura extracts navigation/related-links instead
    of article body.  In extract mode (require_article_body=True), parse()
    must raise ValidationError, not return junk output.
    """
    html = (FIXTURES / "guardian.html").read_text(encoding="utf-8")
    with pytest.raises(ValidationError, match="No article body"):
        parse(extract_with_trafilatura(html), require_article_body=True)


def test_theringer_raises_validation_error():
    """
    Theringer fixture: Trafilatura extracts a navigation stub.
    In extract mode (require_article_body=True), parse() must raise
    ValidationError, not return junk output.
    """
    html = (FIXTURES / "theringer.html").read_text(encoding="utf-8")
    with pytest.raises(ValidationError, match="No article body"):
        parse(extract_with_trafilatura(html), require_article_body=True)


def test_smithsonian_does_not_fail():
    """
    Smithsonian fixture: clean article with substantial prose.
    Must NOT raise ValidationError even in extract mode.
    """
    html = (FIXTURES / "smithsonian.html").read_text(encoding="utf-8")
    doc = parse(extract_with_trafilatura(html), require_article_body=True)
    assert doc.sections, "Smithsonian must have sections"
