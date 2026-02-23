"""
Tests for parser block-level element parsing.

Part 3 of parser tests - validates block element conversion.
"""
from flowdoc.core.parser import parse
from flowdoc.core.model import Paragraph, ListBlock, Quote, Preformatted


def test_parses_paragraph():
    """Paragraphs become Paragraph objects."""
    html = "<body><h1>Title</h1><p>Text content</p></body>"
    doc = parse(html)
    assert len(doc.sections[0].blocks) == 1
    assert isinstance(doc.sections[0].blocks[0], Paragraph)


def test_parses_unordered_list():
    """Unordered lists become ListBlock with ordered=False."""
    html = "<body><h1>Title</h1><ul><li>Item 1</li><li>Item 2</li></ul></body>"
    doc = parse(html)
    block = doc.sections[0].blocks[0]
    assert isinstance(block, ListBlock)
    assert block.ordered is False
    assert len(block.items) == 2


def test_parses_ordered_list():
    """Ordered lists become ListBlock with ordered=True."""
    html = "<body><h1>Title</h1><ol><li>First</li><li>Second</li></ol></body>"
    doc = parse(html)
    block = doc.sections[0].blocks[0]
    assert isinstance(block, ListBlock)
    assert block.ordered is True
    assert len(block.items) == 2


def test_parses_nested_lists():
    """Nested lists are preserved in ListItem.children."""
    html = "<body><h1>Title</h1><ul><li>Parent<ul><li>Child</li></ul></li></ul></body>"
    doc = parse(html)
    block = doc.sections[0].blocks[0]
    assert isinstance(block, ListBlock)
    assert len(block.items) == 1
    assert len(block.items[0].children) == 1
    assert isinstance(block.items[0].children[0], ListBlock)


def test_parses_blockquote():
    """Blockquotes become Quote objects."""
    html = "<body><h1>Title</h1><blockquote><p>Quoted text</p></blockquote></body>"
    doc = parse(html)
    block = doc.sections[0].blocks[0]
    assert isinstance(block, Quote)
    assert len(block.blocks) == 1
    assert isinstance(block.blocks[0], Paragraph)


def test_parses_preformatted():
    """Pre elements become Preformatted objects."""
    html = "<body><h1>Title</h1><pre>Code here\n  indented</pre><p>Text</p></body>"
    doc = parse(html)
    block = doc.sections[0].blocks[0]
    assert isinstance(block, Preformatted)
    assert "Code here" in block.text


def test_degrades_table():
    """Tables become placeholder paragraphs."""
    html = "<body><h1>Title</h1><table><tr><td>A</td></tr></table><p>Text</p></body>"
    doc = parse(html)
    block = doc.sections[0].blocks[0]
    assert isinstance(block, Paragraph)
    assert "Table omitted" in block.inlines[0].text