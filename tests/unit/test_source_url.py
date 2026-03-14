"""
Tests for source URL threading and "View original" placeholder links.
"""
from decant.core.model import Document, Section, Heading, Paragraph, Text, Image
from decant.core.parser import parse
from decant.core.renderer import render, render_notice_banner


def _make_heading(text: str = "Section") -> Heading:
    return Heading(level=2, inlines=[Text(text=text)])


def _prose_para(text: str = "Some article content.") -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


def _placeholder_para(text: str = "[Table removed]") -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


def _make_section(heading_text: str, blocks) -> Section:
    return Section(heading=_make_heading(heading_text), blocks=list(blocks))


# ---------------------------------------------------------------------------
# a. Document model accepts source_url
# ---------------------------------------------------------------------------

def test_document_source_url_set():
    doc = Document(title="T", sections=[], source_url="https://example.com")
    assert doc.source_url == "https://example.com"


def test_document_source_url_default():
    doc = Document(title="T", sections=[])
    assert doc.source_url == ""


# ---------------------------------------------------------------------------
# b. parse() threads source_url to Document
# ---------------------------------------------------------------------------

def test_parse_threads_source_url():
    html = "<body><h1>T</h1><p>Content here.</p></body>"
    doc = parse(html, source_url="https://example.com")
    assert doc.source_url == "https://example.com"


def test_parse_source_url_default():
    html = "<body><h1>T</h1><p>Content here.</p></body>"
    doc = parse(html)
    assert doc.source_url == ""


# ---------------------------------------------------------------------------
# c. Placeholder paragraphs get "View original" link when source_url set
# ---------------------------------------------------------------------------

def test_placeholder_gets_view_original_link():
    doc = Document(
        title="T",
        sections=[_make_section("S", [
            _prose_para(),
            _placeholder_para("[Table removed]"),
        ])],
        source_url="https://example.com",
    )
    rendered = render(doc)
    assert "View original" in rendered
    assert 'href="https://example.com"' in rendered
    assert 'class="placeholder"' in rendered


# ---------------------------------------------------------------------------
# d. Placeholder paragraphs have NO link when source_url is empty
# ---------------------------------------------------------------------------

def test_placeholder_no_link_without_source_url():
    doc = Document(
        title="T",
        sections=[_make_section("S", [
            _prose_para(),
            _placeholder_para("[Table removed]"),
        ])],
    )
    rendered = render(doc)
    assert "View original" not in rendered


# ---------------------------------------------------------------------------
# e. Notice banner appears when placeholders exist
# ---------------------------------------------------------------------------

def test_notice_banner_with_placeholders():
    doc = Document(
        title="T",
        sections=[_make_section("S", [
            _prose_para(),
            _placeholder_para("[Table removed]"),
            _placeholder_para("[Table removed]"),
            _placeholder_para("[Image removed]"),
        ])],
        source_url="https://example.com",
    )
    rendered = render(doc)
    assert "2 tables and 1 image" in rendered
    assert "view the original page" in rendered
    assert 'href="https://example.com"' in rendered


# ---------------------------------------------------------------------------
# f. Notice banner absent when no placeholders
# ---------------------------------------------------------------------------

def test_no_banner_without_placeholders():
    doc = Document(
        title="T",
        sections=[_make_section("S", [_prose_para()])],
        source_url="https://example.com",
    )
    rendered = render(doc)
    assert '<div class="decant-notice">' not in rendered


# ---------------------------------------------------------------------------
# g. Notice banner with no source_url omits link
# ---------------------------------------------------------------------------

def test_banner_no_link_without_source_url():
    doc = Document(
        title="T",
        sections=[_make_section("S", [
            _prose_para(),
            _placeholder_para("[Table removed]"),
        ])],
    )
    rendered = render(doc)
    assert "1 table" in rendered
    assert "view the original page" not in rendered


# ---------------------------------------------------------------------------
# h. HR separators ([-]) do NOT count in banner
# ---------------------------------------------------------------------------

def test_hr_placeholders_not_in_banner():
    doc = Document(
        title="T",
        sections=[_make_section("S", [
            _prose_para(),
            _placeholder_para("[-]"),
        ])],
    )
    banner = render_notice_banner(doc)
    assert banner == ""


# ---------------------------------------------------------------------------
# i. Form placeholders counted in banner
# ---------------------------------------------------------------------------

def test_form_placeholder_in_banner():
    doc = Document(
        title="T",
        sections=[_make_section("S", [
            _prose_para(),
            _placeholder_para("[Form omitted]"),
        ])],
    )
    banner = render_notice_banner(doc)
    assert "1 form" in banner
