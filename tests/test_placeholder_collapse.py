"""
Tests for consecutive identical placeholder block collapsing (burn-down item 3).

Consecutive identical placeholder Paragraphs (e.g. [Form omitted], [Image omitted],
[Image: ...]) that appear in a run of N>=2 are collapsed to a single instance.

Affected fixtures:
- aeon: leading cluster of x6 [Form omitted] collapses to x1;
        tail cluster of x4 [Form omitted] collapses to x1
- propublica: cluster of x5 [Form omitted] collapses to x1
- eater: at least one pair of consecutive [Image: ...] placeholders collapses to x1
"""
from pathlib import Path

from flowdoc.core.model import Paragraph, Text
from flowdoc.core.parser import (
    extract_with_trafilatura,
    parse,
    _is_placeholder_paragraph,
)

FIXTURES = Path(__file__).parent / "fixtures" / "user-study"


def _all_blocks(doc):
    """Flatten all top-level blocks across all sections."""
    for section in doc.sections:
        yield from section.blocks


def _identical_placeholder_runs(blocks):
    """
    Return list of run lengths where consecutive IDENTICAL placeholder blocks
    appear and run length >= 2.  Two placeholder blocks are 'identical' when
    their single inline text is the same string.
    """
    runs = []
    count = 1
    for i in range(1, len(blocks)):
        prev, curr = blocks[i - 1], blocks[i]
        if (
            _is_placeholder_paragraph(prev)
            and _is_placeholder_paragraph(curr)
            and prev.inlines[0].text == curr.inlines[0].text
        ):
            count += 1
        else:
            if count >= 2:
                runs.append(count)
            count = 1
    if count >= 2:
        runs.append(count)
    return runs


# ---------------------------------------------------------------------------
# Unit tests for _is_placeholder_paragraph
# ---------------------------------------------------------------------------

def test_is_placeholder_form_omitted():
    p = Paragraph(inlines=[Text(text="[Form omitted]")])
    assert _is_placeholder_paragraph(p) is True


def test_is_placeholder_image_omitted():
    p = Paragraph(inlines=[Text(text="[Image omitted]")])
    assert _is_placeholder_paragraph(p) is True


def test_is_placeholder_image_with_alt():
    p = Paragraph(inlines=[Text(text="[Image: some alt text]")])
    assert _is_placeholder_paragraph(p) is True


def test_is_not_placeholder_normal_paragraph():
    p = Paragraph(inlines=[Text(text="This is a normal paragraph.")])
    assert _is_placeholder_paragraph(p) is False


def test_is_not_placeholder_empty_paragraph():
    p = Paragraph(inlines=[])
    assert _is_placeholder_paragraph(p) is False


def test_is_not_placeholder_multi_inline():
    p = Paragraph(inlines=[Text(text="[Form omitted]"), Text(text=" extra")])
    assert _is_placeholder_paragraph(p) is False


# ---------------------------------------------------------------------------
# Fixture integration tests
# ---------------------------------------------------------------------------

def test_aeon_no_consecutive_placeholder_runs():
    """
    Aeon fixture: a leading cluster of 6 and a tail cluster of 4 [Form omitted]
    blocks appear after extraction.

    Before fix: runs of length 6 and 4 are present.
    After fix: no run of 2+ consecutive identical placeholder blocks remains.
    """
    html = (FIXTURES / "aeon.html").read_text(encoding="utf-8")
    doc = parse(extract_with_trafilatura(html))

    blocks = list(_all_blocks(doc))
    runs = _identical_placeholder_runs(blocks)
    assert runs == [], (
        f"Found consecutive identical placeholder runs of lengths {runs}; "
        "placeholder collapsing is not working."
    )


def test_propublica_no_consecutive_placeholder_runs():
    """
    Propublica fixture: a cluster of 5 [Form omitted] blocks appears.

    Before fix: run of length 5 present.
    After fix: no run of 2+ consecutive identical placeholder blocks remains.
    """
    html = (FIXTURES / "propublica.html").read_text(encoding="utf-8")
    doc = parse(extract_with_trafilatura(html))

    blocks = list(_all_blocks(doc))
    runs = _identical_placeholder_runs(blocks)
    assert runs == [], (
        f"Found consecutive identical placeholder runs of lengths {runs}; "
        "placeholder collapsing is not working."
    )


def test_eater_no_consecutive_placeholder_runs():
    """
    Eater fixture: at least one pair of consecutive [Image: ...] placeholder
    blocks appears after extraction.

    Before fix: run of length >= 2 present.
    After fix: no run of 2+ consecutive identical placeholder blocks remains.
    """
    html = (FIXTURES / "eater.html").read_text(encoding="utf-8")
    doc = parse(extract_with_trafilatura(html))

    blocks = list(_all_blocks(doc))
    runs = _identical_placeholder_runs(blocks)
    assert runs == [], (
        f"Found consecutive identical placeholder runs of lengths {runs}; "
        "placeholder collapsing is not working."
    )
