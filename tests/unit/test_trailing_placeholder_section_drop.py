"""
Tests for all-placeholder trailing section drop (burn-down item 5).

Extends the existing orphan-section dropper (Phase 2B.2) with a second
end-anchored condition: drop the final section when every block in it is a
placeholder Paragraph ([Form omitted], [Image not included], [Image: ...]).

These sections contain no article prose and are CMS template artefacts.
The check is end-anchored — only the final section is inspected.
"""
from pathlib import Path

from flowdoc.core.model import Heading, Paragraph, Text, Section, ListBlock, ListItem
from flowdoc.core.parser import (
    extract_with_trafilatura,
    parse,
    drop_trailing_orphan_section,
    _is_placeholder_paragraph,
)

FIXTURES = Path(__file__).resolve().parent / "test-data"


def _make_heading(text: str = "Section") -> Heading:
    return Heading(level=2, inlines=[Text(text=text)])


def _placeholder_para(token: str = "[Form omitted]") -> Paragraph:
    return Paragraph(inlines=[Text(text=token)])


def _prose_para(text: str = "Some article content.") -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


def _make_section(heading_text: str, blocks) -> Section:
    return Section(heading=_make_heading(heading_text), blocks=list(blocks))


# ---------------------------------------------------------------------------
# Unit tests: zero-block condition (existing behaviour preserved)
# ---------------------------------------------------------------------------

def test_zero_block_trailing_section_still_dropped():
    """Existing behaviour: zero-block final section is dropped."""
    anchor = _make_section("Article", [_prose_para()])
    orphan = _make_section("Related", [])
    result = drop_trailing_orphan_section([anchor, orphan])
    assert len(result) == 1
    assert result[0] is anchor


# ---------------------------------------------------------------------------
# Unit tests: all-placeholder condition (new behaviour)
# ---------------------------------------------------------------------------

def test_all_placeholder_trailing_section_dropped():
    """New: final section whose only block is a placeholder is dropped."""
    anchor = _make_section("Article", [_prose_para()])
    tail = _make_section("Subscribe", [_placeholder_para("[Form omitted]")])
    result = drop_trailing_orphan_section([anchor, tail])
    assert len(result) == 1
    assert result[0] is anchor


def test_all_placeholder_multi_block_trailing_section_dropped():
    """New: final section with multiple all-placeholder blocks is dropped."""
    anchor = _make_section("Article", [_prose_para()])
    tail = _make_section("Newsletter", [
        _placeholder_para("[Form omitted]"),
        _placeholder_para("[Image not included]"),
    ])
    result = drop_trailing_orphan_section([anchor, tail])
    assert len(result) == 1
    assert result[0] is anchor


def test_all_placeholder_image_with_alt_dropped():
    """New: [Image: alt] placeholder token qualifies."""
    anchor = _make_section("Article", [_prose_para()])
    tail = _make_section("Promo", [_placeholder_para("[Image: promo banner]")])
    result = drop_trailing_orphan_section([anchor, tail])
    assert len(result) == 1


def test_single_all_placeholder_section_dropped():
    """Edge case: document with only one all-placeholder section is dropped entirely."""
    only = _make_section("Subscribe", [_placeholder_para("[Form omitted]")])
    result = drop_trailing_orphan_section([only])
    assert result == []


# ---------------------------------------------------------------------------
# Unit tests: prose content prevents drop
# ---------------------------------------------------------------------------

def test_section_with_prose_not_dropped():
    """A final section containing at least one prose paragraph is kept."""
    anchor = _make_section("Article", [_prose_para()])
    kept = _make_section("Related", [_prose_para("Read more here.")])
    result = drop_trailing_orphan_section([anchor, kept])
    assert len(result) == 2


def test_section_with_mixed_content_not_dropped():
    """Final section with prose mixed among placeholders is NOT dropped."""
    anchor = _make_section("Article", [_prose_para()])
    mixed = _make_section("Further Reading", [
        _placeholder_para("[Form omitted]"),
        _prose_para("Subscribe for updates."),
    ])
    result = drop_trailing_orphan_section([anchor, mixed])
    assert len(result) == 2


def test_section_with_listblock_not_dropped():
    """Final section containing a ListBlock (non-Paragraph) is NOT dropped."""
    anchor = _make_section("Article", [_prose_para()])
    with_list = _make_section("Links", [
        ListBlock(ordered=False, items=[ListItem(inlines=[Text(text="Item 1")], children=[])])
    ])
    result = drop_trailing_orphan_section([anchor, with_list])
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Integration test: aeon fixture — prose-containing final section is preserved
# ---------------------------------------------------------------------------

def test_aeon_final_section_not_erroneously_dropped():
    """
    Aeon fixture regression guard: the final section is the main article with
    substantial prose.  The all-placeholder extension must NOT drop it.

    Sanity: at least one section remains and the final section has at least
    one non-placeholder block.
    """
    html = (FIXTURES / "aeon.html").read_text(encoding="utf-8")
    doc = parse(extract_with_trafilatura(html))

    assert doc.sections, "All sections were dropped — pipeline too aggressive"

    last = doc.sections[-1]
    non_placeholder = [b for b in last.blocks if not _is_placeholder_paragraph(b)]
    assert non_placeholder, (
        "Final aeon section has no non-placeholder blocks; "
        "the all-placeholder extension is over-firing."
    )
