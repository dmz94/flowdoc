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

from flowdoc.core.parser import extract_with_trafilatura, parse
from flowdoc.core.renderer import render


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
