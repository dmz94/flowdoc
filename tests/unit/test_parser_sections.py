"""
Tests for parser sectioning logic.

Part 2 of parser tests - validates section creation from headings.
"""
from decant.core.parser import parse, ValidationError


def test_creates_sections_from_headings():
    """Each heading creates a new section."""
    html = "<body><h1>First</h1><p>Text</p><h2>Second</h2><p>More</p></body>"
    doc = parse(html)
    assert len(doc.sections) == 2
    assert doc.sections[0].heading.level == 1
    assert doc.sections[1].heading.level == 2


def test_drops_content_before_first_heading():
    """Content before first heading is dropped."""
    html = "<body><p>Skip this</p><h1>Start here</h1><p>Keep this</p></body>"
    doc = parse(html)
    assert len(doc.sections) == 1
    assert doc.sections[0].heading.level == 1


def test_preserves_heading_levels():
    """Heading levels (1-6) are preserved."""
    html = "<body><h1>L1</h1><p>Text</p><h3>L3</h3><p>Text</p><h6>L6</h6><p>Text</p></body>"
    doc = parse(html)
    assert len(doc.sections) == 3
    assert doc.sections[0].heading.level == 1
    assert doc.sections[1].heading.level == 3
    assert doc.sections[2].heading.level == 6


def test_empty_sections_when_no_headings():
    """No headings raises ValidationError."""
    import pytest
    html = "<body><p>No headings here</p></body>"
    with pytest.raises(ValidationError):
        parse(html)