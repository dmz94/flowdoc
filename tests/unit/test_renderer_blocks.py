"""
Tests for renderer block-level element rendering.

Part 2 of renderer tests - validates block element HTML generation.
"""
from flowdoc.core.model import Document, Section, Heading, Paragraph, ListBlock, ListItem, Quote, Preformatted, Text
from flowdoc.core.renderer import render


def test_renders_paragraph():
    """Paragraphs render as <p> tags."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Paragraph(inlines=[Text(text="Content")])]
            )
        ]
    )
    html = render(doc)
    assert "<p>" in html
    assert "</p>" in html


def test_renders_unordered_list():
    """Unordered lists render as <ul>."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    ListBlock(
                        ordered=False,
                        items=[ListItem(inlines=[Text(text="Item")], children=[])]
                    )
                ]
            )
        ]
    )
    html = render(doc)
    assert "<ul>" in html
    assert "<li>" in html
    assert "</ul>" in html


def test_renders_ordered_list():
    """Ordered lists render as <ol>."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    ListBlock(
                        ordered=True,
                        items=[ListItem(inlines=[Text(text="First")], children=[])]
                    )
                ]
            )
        ]
    )
    html = render(doc)
    assert "<ol>" in html
    assert "</ol>" in html


def test_renders_nested_lists():
    """Nested lists render with proper structure."""
    nested_list = ListBlock(
        ordered=False,
        items=[ListItem(inlines=[Text(text="Nested")], children=[])]
    )
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    ListBlock(
                        ordered=False,
                        items=[
                            ListItem(inlines=[Text(text="Parent")], children=[nested_list])
                        ]
                    )
                ]
            )
        ]
    )
    html = render(doc)
    # Should have two <ul> tags (parent and nested)
    assert html.count("<ul>") == 2
    assert html.count("</ul>") == 2


def test_renders_blockquote():
    """Blockquotes render as <blockquote>."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Quote(blocks=[Paragraph(inlines=[Text(text="Quoted")])])
                ]
            )
        ]
    )
    html = render(doc)
    assert "<blockquote>" in html
    assert "</blockquote>" in html


def test_renders_preformatted():
    """Preformatted text renders as <pre> with escaping."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Preformatted(text="<code>example</code>")]
            )
        ]
    )
    html = render(doc)
    assert "<pre>" in html
    assert "&lt;code&gt;" in html  # Should be escaped