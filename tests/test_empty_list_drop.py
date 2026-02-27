"""
Tests for empty list block filtering (burn-down item 1).

Empty list blocks are structural artifacts from Trafilatura extraction where
<ul>/<ol> elements have either zero <li> items or all-empty <li> items.
Both cases produce invisible output and are unambiguously extraction artifacts.

Affected fixtures:
- eater: <ul><li></li><li></li></ul> near document start (all-empty items)
- guardian: <ol></ol> twice (zero items)
"""
from pathlib import Path

from flowdoc.core.model import ListBlock
from flowdoc.core.parser import extract_with_trafilatura, parse


def _all_listblocks(doc) -> list[ListBlock]:
    """Collect every ListBlock at the top level of every section."""
    blocks = []
    for section in doc.sections:
        for block in section.blocks:
            if isinstance(block, ListBlock):
                blocks.append(block)
    return blocks


def test_eater_no_all_empty_list_items():
    """
    Eater fixture: a <ul> with two empty <li> elements appears near the start
    of the document after extraction.  Every list item has no inline content
    and no nested children.

    Before fix: the ListBlock is present in the model with 2 items, all empty.
    After fix: no ListBlock in the document has all-empty items.

    Sanity check: at least one legitimate ListBlock with real content remains.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "user-study" / "eater.html"
    html = fixture_path.read_text(encoding="utf-8")
    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)

    list_blocks = _all_listblocks(doc)

    # Sanity: legitimate lists must survive (eater has many real list blocks)
    assert list_blocks, "No ListBlocks found at all — fixture or pipeline changed"

    # Target: no ListBlock may have all-empty items
    all_empty = [
        lb for lb in list_blocks
        if lb.items and all(not item.inlines and not item.children for item in lb.items)
    ]
    assert all_empty == [], (
        f"Found {len(all_empty)} ListBlock(s) with all-empty items; "
        "empty list filtering is not working."
    )


def test_guardian_no_zero_item_lists():
    """
    Guardian fixture: two <ol></ol> elements with zero <li> items appear in
    the extracted output (elements [7] and [20]).

    Before fix: ListBlocks with items=[] are present in the model.
    After fix: no ListBlock in the document has zero items.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "user-study" / "guardian.html"
    html = fixture_path.read_text(encoding="utf-8")
    extracted = extract_with_trafilatura(html)
    doc = parse(extracted)

    list_blocks = _all_listblocks(doc)

    zero_item = [lb for lb in list_blocks if not lb.items]
    assert zero_item == [], (
        f"Found {len(zero_item)} ListBlock(s) with zero items; "
        "empty list filtering is not working."
    )
