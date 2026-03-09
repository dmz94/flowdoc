"""
Tests for trailing boilerplate removal heuristic.

Trailing CMS boilerplate is content that Trafilatura does not strip because it
appears structurally similar to article content (plain paragraphs) but is
semantically junk: social-follow prompts, site policy footers, newsletter
sign-ups attached to CMS page templates.

Documented in known-limitations.md as "Trailing CMS boilerplate".
"""
from pathlib import Path

from flowdoc.core.parser import extract_with_trafilatura, parse
from flowdoc.core.renderer import render


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
