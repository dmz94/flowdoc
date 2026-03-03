"""
Tests for parser title extraction.

Part 1 of parser tests - validates title extraction logic.
"""
from flowdoc.core.parser import parse, ValidationError


def test_title_from_title_tag():
    """Uses <title> tag when present."""
    html = "<html><head><title>My Document</title></head><body><h1>Heading</h1><p>Text</p></body></html>"
    doc = parse(html)
    assert doc.title == "My Document"


def test_title_from_first_h1():
    """Falls back to first <h1> when no <title>."""
    html = "<body><h1>First Heading</h1><p>Text</p><h1>Second</h1></body>"
    doc = parse(html)
    assert doc.title == "First Heading"


def test_title_empty_when_neither():
    """No headings raises ValidationError."""
    import pytest
    html = "<body><p>Just a paragraph</p></body>"
    with pytest.raises(ValidationError):
        parse(html)


def test_title_prefers_title_over_h1():
    """<title> takes precedence over <h1>."""
    html = "<html><head><title>Title Tag</title></head><body><h1>H1 Tag</h1><p>Text</p></body></html>"
    doc = parse(html)
    assert doc.title == "Title Tag"