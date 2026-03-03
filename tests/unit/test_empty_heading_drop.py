"""
Tests for empty heading section filtering (burn-down item 2).

Empty heading elements (<h1></h1> etc.) are structural artifacts where
Trafilatura extracts a heading DOM node that contains no text content.
The resulting Section is structurally inert and is dropped during build_sections.

Affected fixture:
- theringer: two consecutive empty <h1> elements at document start
"""
from pathlib import Path

from flowdoc.core.model import Heading, Text
from flowdoc.core.parser import extract_with_trafilatura, parse, _heading_has_text


def test_heading_has_text_returns_false_for_empty():
    """_heading_has_text returns False when heading has no inlines."""
    empty = Heading(level=1, inlines=[])
    assert _heading_has_text(empty) is False


def test_heading_has_text_returns_true_for_non_empty():
    """_heading_has_text returns True for a heading with text content."""
    heading = Heading(level=1, inlines=[Text(text="Introduction")])
    assert _heading_has_text(heading) is True


def test_theringer_no_empty_heading_sections():
    """
    Theringer fixture: two empty <h1></h1> elements at the document start
    produce Section nodes with headings that have no inline text.

    Before fix: two empty-heading sections appear at the start of the document.
    After fix: no section in the document has a heading with empty text.

    Sanity check: at least one section with non-empty heading survives
    (the 'Keep Exploring' section, which has 1 paragraph).
    """
    fixture_path = (
        Path(__file__).resolve().parent.parent / "fixtures" / "user-study" / "theringer.html"
    )
    html = fixture_path.read_text(encoding="utf-8")
    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)

    # Sanity: at least one section must exist after filtering
    assert doc.sections, "All sections were dropped — filtering is too aggressive"

    # Target: every remaining section must have a non-empty heading
    empty_heading_sections = [
        s for s in doc.sections
        if not _heading_has_text(s.heading)
    ]
    assert empty_heading_sections == [], (
        f"Found {len(empty_heading_sections)} section(s) with empty headings; "
        "empty heading filtering is not working."
    )
