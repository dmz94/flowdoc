"""
Tests for trailing orphan section removal heuristic.

A trailing orphan section is a final section whose heading has no meaningful
body content (zero blocks or only trivially-empty blocks after the full
parse pipeline).  These are CMS "related content" / navigation rails that
Trafilatura captures as heading-only fragments:

    <h2>The Latest</h2>
    (no paragraphs, no lists)

They produce a heading in the rendered output with nothing beneath it —
visual noise that is unambiguously not article content.

Documented in known-limitations.md as "Orphan trailing section".
"""
from pathlib import Path

from decant.core.model import Heading, Paragraph, Text, Section
from decant.core.parser import (
    drop_trailing_orphan_section,
    extract_with_trafilatura,
    parse,
)
from decant.core.renderer import render


def _make_heading(text: str, level: int = 2) -> Heading:
    return Heading(level=level, inlines=[Text(text=text)])


def _prose_para(text: str = "Some article content.") -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


def _make_section(heading_text: str, blocks=None) -> Section:
    return Section(heading=_make_heading(heading_text), blocks=list(blocks or []))


def test_eater_trailing_orphan_section_is_removed():
    """
    Eater fixture: Trafilatura extraction retains a trailing heading-only
    section ('The Latest') with zero body blocks.  It is the very last
    section in the document after the full parse pipeline and is
    unambiguously a CMS navigation stub, not article content.

    Baseline (today): 'The Latest' heading survives extract → parse → render
    and appears in the output HTML.

    Intended behavior (after heuristic): the trailing orphan section should
    be dropped so 'The Latest' does not appear in the rendered output.
    Legitimate article content ('Pastel de Nata', from the real lead section
    with 46 blocks) must be preserved.

    This test FAILS today because the heuristic has not been implemented.
    """
    fixture_path = (
        Path(__file__).resolve().parent / "test-data" / "eater.html"
    )
    html = fixture_path.read_text(encoding="utf-8")

    # Production extract-mode pipeline (mirrors cli/main.py extract path)
    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)
    rendered = render(doc)

    # Sanity: real article content from the lead section (46 blocks) must
    # remain.  If this fails the fixture or pipeline has changed fundamentally.
    assert "Pastel de Nata" in rendered, (
        "Lead article content 'Pastel de Nata' missing — fixture or pipeline "
        "has changed unexpectedly."
    )

    # Target: the orphan trailing section heading must NOT appear.
    # Today this assertion FAILS: 'The Latest' IS present in rendered output.
    # After the orphan-drop heuristic is implemented it should PASS.
    assert "The Latest" not in rendered, (
        "Trailing orphan section 'The Latest' (0 blocks) should be dropped "
        "by the orphan section heuristic, but it is still present in the output."
    )


def test_section_with_content_not_dropped():
    """
    A section with real body content must NOT be dropped, even if it is the
    last section in the document.
    """
    fixture_path = (
        Path(__file__).resolve().parent / "test-data" / "cdc.html"
    )
    html = fixture_path.read_text(encoding="utf-8")

    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)

    # Every section should have blocks — none should be orphaned away
    # if they contain real content.
    last_section = doc.sections[-1]
    assert len(last_section.blocks) > 0, (
        "Last section of a clean fixture has content and must not be dropped"
    )


# ---------------------------------------------------------------------------
# Mechanism C: Boilerplate heading detection
# ---------------------------------------------------------------------------

def test_boilerplate_heading_newsletter_dropped():
    """Last section heading is 'Newsletter' — dropped."""
    sections = [
        _make_section("Article", [_prose_para("Content.")]),
        _make_section("Newsletter", [_prose_para("Sign up for updates.")]),
    ]
    result = drop_trailing_orphan_section(sections)
    assert len(result) == 1
    assert result[0].heading.inlines[0].text == "Article"


def test_boilerplate_heading_subscribe_dropped():
    """Last section heading is 'Subscribe' — dropped."""
    sections = [
        _make_section("Article", [_prose_para("Content.")]),
        _make_section("Subscribe", [_prose_para("Get our emails.")]),
    ]
    result = drop_trailing_orphan_section(sections)
    assert len(result) == 1


def test_boilerplate_heading_case_insensitive():
    """Heading match is case-insensitive."""
    sections = [
        _make_section("Article", [_prose_para("Content.")]),
        _make_section("RELATED ARTICLES", [_prose_para("More reading.")]),
    ]
    result = drop_trailing_orphan_section(sections)
    assert len(result) == 1


def test_boilerplate_heading_with_whitespace():
    """Extra whitespace in heading is normalized before matching."""
    sections = [
        _make_section("Article", [_prose_para("Content.")]),
        _make_section("  Related   Stories  ", [_prose_para("More.")]),
    ]
    result = drop_trailing_orphan_section(sections)
    assert len(result) == 1


def test_legitimate_heading_not_dropped():
    """A section with a non-boilerplate heading is kept."""
    sections = [
        _make_section("Introduction", [_prose_para("First part.")]),
        _make_section("Conclusion", [_prose_para("Final thoughts.")]),
    ]
    result = drop_trailing_orphan_section(sections)
    assert len(result) == 2


def test_non_trailing_boilerplate_heading_kept():
    """A boilerplate heading that is NOT the last section is kept."""
    sections = [
        _make_section("Newsletter", [_prose_para("Sign up.")]),
        _make_section("Article", [_prose_para("Content.")]),
    ]
    result = drop_trailing_orphan_section(sections)
    assert len(result) == 2
