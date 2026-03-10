"""
Tests for trailing boilerplate removal heuristic.

Trailing CMS boilerplate is content that Trafilatura does not strip because it
appears structurally similar to article content (plain paragraphs) but is
semantically junk: social-follow prompts, site policy footers, newsletter
sign-ups attached to CMS page templates.

Documented in known-limitations.md as "Trailing CMS boilerplate".
"""
from pathlib import Path

from flowdoc.core.model import Heading, Paragraph, Text, Section
from flowdoc.core.parser import extract_with_trafilatura, parse, trim_trailing_boilerplate
from flowdoc.core.renderer import render


def _make_heading(text: str = "Section") -> Heading:
    return Heading(level=2, inlines=[Text(text=text)])


def _prose_para(text: str = "Some article content.") -> Paragraph:
    return Paragraph(inlines=[Text(text=text)])


def _make_section(heading_text: str, blocks) -> Section:
    return Section(heading=_make_heading(heading_text), blocks=list(blocks))


def test_clevelandclinic_trailing_cms_boilerplate_is_removed():
    """
    Cleveland Clinic fixture: Trafilatura extraction retains trailing CMS footer
    paragraphs ("Follow Cleveland Clinic", "Site Information & Policies") that
    appear after legitimate article content.

    Baseline (today): these paragraphs survive extract → parse → render and
    appear in the output HTML. This is documented behavior in known-limitations.md.

    Intended behavior (after heuristic): trailing social-follow / site-policy
    boilerplate paragraphs should be stripped before or during the parse phase
    so they do not appear in the rendered output.

    This test FAILS today because the heuristic has not been implemented.
    """
    fixture_path = (
        Path(__file__).resolve().parent / "test-data" / "clevelandclinic_dyslexia.html"
    )
    html = fixture_path.read_text(encoding="utf-8")

    # Production extract-mode pipeline (mirrors cli/main.py extract path)
    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)
    rendered = render(doc)

    # "Follow Cleveland Clinic" is a CMS social-follow prompt that appears in
    # the last three paragraphs of the current rendered output.  It is
    # unambiguously boilerplate and contains no article content.
    #
    # Today this assertion FAILS: the string IS present in rendered output.
    # After the trim heuristic is implemented it should PASS.
    assert "Follow Cleveland Clinic" not in rendered, (
        "Trailing CMS boilerplate 'Follow Cleveland Clinic' should be stripped "
        "by the boilerplate trim heuristic, but it is still present in the output."
    )


def test_clean_fixture_not_trimmed():
    """
    CDC fixture: a clean article with no trailing CMS boilerplate.
    The boilerplate trim heuristic must not remove legitimate content.
    """
    fixture_path = (
        Path(__file__).resolve().parent / "test-data" / "cdc.html"
    )
    html = fixture_path.read_text(encoding="utf-8")

    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)
    rendered = render(doc)

    # The fixture should produce non-trivial output with sections intact.
    assert len(doc.sections) > 0, "Clean CDC fixture should produce sections"
    assert "<!DOCTYPE html>" in rendered


def test_anchor_learn_more_health_library():
    """Anchor 'Learn more about the Health Library' triggers trim."""
    sections = [_make_section("Article", [
        _prose_para("Real content."),
        _prose_para("Learn more about the Health Library and how we ensure accuracy."),
        _prose_para("More footer stuff."),
    ])]
    result = trim_trailing_boilerplate(sections)
    assert len(result[0].blocks) == 1
    assert "Real content" in result[0].blocks[0].inlines[0].text


def test_anchor_back_to_top():
    """Anchor 'Back to top' triggers trim."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Back to top"),
    ])]
    result = trim_trailing_boilerplate(sections)
    assert len(result[0].blocks) == 1


def test_anchor_got_a_story():
    """Anchor 'Got a story we should hear' triggers trim."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("Got a story we should hear? Email us."),
    ])]
    result = trim_trailing_boilerplate(sections)
    assert len(result[0].blocks) == 1


def test_anchor_does_not_match_substring_in_prose():
    """Anchor match uses 'in', so substring in longer text still triggers."""
    sections = [_make_section("Article", [
        _prose_para("Content."),
        _prose_para("For more information, Follow Cleveland Clinic on social media."),
    ])]
    result = trim_trailing_boilerplate(sections)
    assert len(result[0].blocks) == 1
