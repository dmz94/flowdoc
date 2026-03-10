"""
Tests for trim_trailing_noise() — end-anchored removal of trailing
noise paragraphs (photo credits, license text, date stamps, trivial noise).
"""
from flowdoc.core.model import Heading, Paragraph, Text, Section, ListBlock, ListItem
from flowdoc.core.parser import trim_trailing_noise


def _make_heading(text: str = "Section") -> Heading:
    return Heading(level=2, inlines=[Text(text=text)])


def _prose_para(text: str = "Some article content.") -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


def _make_section(heading_text: str, blocks) -> Section:
    return Section(heading=_make_heading(heading_text), blocks=list(blocks))


# ---------------------------------------------------------------------------
# Photo/image/visual/credit prefix
# ---------------------------------------------------------------------------

def test_photo_credit_removed():
    """Trailing photo credit is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Photo: Jane Smith / Reuters"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_image_credit_removed():
    """Trailing image credit is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Image: \u00a9 Rawpixel | GettyImages"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_visual_credit_removed():
    """Trailing visual credit is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Visual: Nora Belblidia for Undark"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_copyright_symbol_removed():
    """Trailing copyright symbol line is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("\u00a9 Shutterstock"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_copyright_c_removed():
    """Trailing (c) line is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("(c) 2025 Associated Press"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


# ---------------------------------------------------------------------------
# License boilerplate
# ---------------------------------------------------------------------------

def test_creative_commons_removed():
    """Trailing Creative Commons line is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("This article is published under Creative Commons BY-SA 4.0"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_cc_by_removed():
    """Trailing CC BY line is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("CC BY-SA 4.0"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


# ---------------------------------------------------------------------------
# Trivial noise
# ---------------------------------------------------------------------------

def test_trivial_period_removed():
    """Trailing single period is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("."),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_trivial_dash_removed():
    """Trailing single dash is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("-"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


# ---------------------------------------------------------------------------
# Bare date stamps
# ---------------------------------------------------------------------------

def test_bare_date_stamp_removed():
    """Trailing bare date stamp is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Aug. 06, 2022"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_bare_iso_date_removed():
    """Trailing ISO date is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("2025-01-15"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_bare_slash_date_removed():
    """Trailing slash date is removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("01/15/2025"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_date_with_prose_NOT_removed():
    """Date embedded in prose is not removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Published on Aug. 06, 2022 by the editorial team."),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 2


# ---------------------------------------------------------------------------
# Multiple trailing noise / end-anchor behavior
# ---------------------------------------------------------------------------

def test_multiple_trailing_noise_paragraphs():
    """Multiple consecutive trailing noise paragraphs are all removed."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Visual: Staff"),
        _prose_para("\u00a9 2025 Reuters"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1


def test_noise_scan_stops_at_non_matching_paragraph():
    """Scan stops at non-matching paragraph (end-anchored)."""
    sections = [_make_section("Article", [
        _prose_para("Visual: Staff"),
        _prose_para("Some legitimate prose here."),
        _prose_para("\u00a9 Reuters"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 2
    assert "Visual: Staff" in result[0].blocks[0].inlines[0].text


def test_noise_scan_stops_at_non_paragraph_block():
    """Scan stops at non-Paragraph block (ListBlock)."""
    sections = [_make_section("Article", [
        ListBlock(ordered=False, items=[ListItem(inlines=[Text(text="Item")], children=[])]),
        _prose_para("\u00a9 Reuters"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1
    assert isinstance(result[0].blocks[0], ListBlock)


def test_no_sections_returns_empty():
    """Empty input returns empty."""
    assert trim_trailing_noise([]) == []


def test_section_with_no_noise_unchanged():
    """Normal prose sections are unchanged."""
    sections = [_make_section("Article", [
        _prose_para("First paragraph."),
        _prose_para("Second paragraph."),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 2


def test_credit_case_insensitive():
    """Credit detection is case-insensitive."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("PHOTO: Staff photographer"),
    ])]
    result = trim_trailing_noise(sections)
    assert len(result[0].blocks) == 1
