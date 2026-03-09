"""
Tests for empty section removal (sections with zero content blocks).

Empty sections are headings with no paragraphs, lists, images, or other
blocks beneath them. They are structural noise — either title-duplicate
artifacts (section 0 matching <title>) or source headings whose content
was lost in extraction.
"""
from pathlib import Path

from flowdoc.core.model import Heading, Paragraph, Text, Section
from flowdoc.core.parser import (
    drop_empty_sections,
    extract_with_trafilatura,
    parse,
)

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "pipeline-audit" / "test-pages"


def _make_heading(text: str = "Section") -> Heading:
    return Heading(level=2, inlines=[Text(text=text)])


def _prose_para(text: str = "Some article content.") -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


def _make_section(heading_text: str, blocks) -> Section:
    return Section(heading=_make_heading(heading_text), blocks=list(blocks))


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_empty_section_dropped():
    """A section with zero blocks is removed."""
    kept = _make_section("Article", [_prose_para()])
    empty = _make_section("Empty", [])
    result = drop_empty_sections([kept, empty])
    assert len(result) == 1
    assert result[0] is kept


def test_multiple_empty_sections_dropped():
    """Multiple empty sections are removed; sections with content survive."""
    sections = [
        _make_section("Empty1", []),
        _make_section("Article", [_prose_para()]),
        _make_section("Empty2", []),
        _make_section("Conclusion", [_prose_para("Final thoughts.")]),
        _make_section("Empty3", []),
    ]
    result = drop_empty_sections(sections)
    assert len(result) == 2
    assert all(len(s.blocks) > 0 for s in result)


def test_all_sections_have_content_unchanged():
    """Sections with content are not affected."""
    sections = [
        _make_section("Intro", [_prose_para()]),
        _make_section("Body", [_prose_para("More content.")]),
    ]
    result = drop_empty_sections(sections)
    assert len(result) == 2


def test_all_sections_empty_returns_empty_list():
    """All-empty input returns an empty list."""
    sections = [
        _make_section("Empty1", []),
        _make_section("Empty2", []),
    ]
    result = drop_empty_sections(sections)
    assert result == []


def test_section_with_placeholder_not_dropped():
    """A section with placeholder blocks is NOT empty — it has blocks."""
    placeholder = Paragraph(inlines=[Text(text="[Form omitted]")])
    section = _make_section("Subscribe", [placeholder])
    result = drop_empty_sections([section])
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Integration tests: real fixtures
# ---------------------------------------------------------------------------

def test_cdc_west_nile_no_empty_sections():
    """CDC West Nile fixture has no empty sections after pipeline."""
    fixture_path = FIXTURE_DIR / "cdc-west-nile.html"
    html = fixture_path.read_text(encoding="utf-8")
    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)
    assert all(len(s.blocks) > 0 for s in doc.sections)


def test_mayoclinic_dyslexia_no_empty_sections():
    """Mayo Clinic dyslexia fixture has no empty sections after pipeline."""
    fixture_path = FIXTURE_DIR / "mayoclinic-dyslexia.html"
    html = fixture_path.read_text(encoding="utf-8")
    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)
    assert all(len(s.blocks) > 0 for s in doc.sections)
