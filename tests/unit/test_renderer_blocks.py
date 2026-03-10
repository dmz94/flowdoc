"""
Tests for renderer block-level element rendering.

Part 2 of renderer tests - validates block element HTML generation.
"""
from flowdoc.core.model import Document, Section, Heading, Paragraph, ListBlock, ListItem, Quote, Preformatted, Image, Table, TableRow, TableCell, Text
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


def test_renders_image():
    """Image renders as <img> with src and alt."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Image(src="https://example.com/photo.jpg", alt="A photo")]
            )
        ]
    )
    html = render(doc)
    assert '<img src="https://example.com/photo.jpg" alt="A photo">' in html


def test_renders_image_escapes_attributes():
    """Image src and alt are HTML-escaped."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Image(src="https://example.com/a&b.jpg", alt='Photo "1"')]
            )
        ]
    )
    html = render(doc)
    assert "https://example.com/a&amp;b.jpg" in html
    assert "Photo &quot;1&quot;" in html


def test_render_complete_document():
    """render() produces a complete HTML5 document with all structural elements."""
    doc = Document(
        title="My Document",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="My Document")]),
                blocks=[Paragraph(inlines=[Text(text="Hello world.")])]
            )
        ]
    )
    html = render(doc)
    assert "<!DOCTYPE html>" in html
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8">' in html
    assert "<title>My Document</title>" in html
    assert "<style>" in html
    assert '<div class="container">' in html
    assert "Hello world." in html
    assert "</html>" in html


def _minimal_doc():
    """Helper: minimal Document for CSS-focused tests."""
    return Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Paragraph(inlines=[Text(text="Content")])]
            )
        ]
    )


def test_opendyslexic_bold_font_face():
    """OpenDyslexic mode embeds two @font-face blocks including bold."""
    html = render(_minimal_doc(), use_opendyslexic=True)
    assert html.count("@font-face") == 2
    assert "font-weight: bold" in html


def test_opendyslexic_em_restyled():
    """OpenDyslexic mode restyles em as bold, not italic."""
    html = render(_minimal_doc(), use_opendyslexic=True)
    assert "font-style: normal" in html
    assert "font-weight: bold" in html


def test_default_em_not_restyled():
    """Default rendering does not restyle em to bold."""
    html = render(_minimal_doc(), use_opendyslexic=False)
    assert "em {" not in html


def test_renders_simple_table():
    """Simple table renders as HTML table with correct structure."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Table(rows=[
                        TableRow(cells=[
                            TableCell(inlines=[Text(text="Name")], is_header=True),
                            TableCell(inlines=[Text(text="Value")], is_header=True),
                        ]),
                        TableRow(cells=[
                            TableCell(inlines=[Text(text="A")]),
                            TableCell(inlines=[Text(text="1")]),
                        ]),
                    ])
                ]
            )
        ]
    )
    html = render(doc)
    assert '<table class="flowdoc-table">' in html
    assert "<th>Name</th>" in html
    assert "<td>A</td>" in html


def test_renders_table_escapes_content():
    """Table cell content is HTML-escaped."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Table(rows=[
                        TableRow(cells=[
                            TableCell(inlines=[Text(text="<script>")]),
                            TableCell(inlines=[Text(text="A&B")]),
                        ]),
                    ])
                ]
            )
        ]
    )
    html = render(doc)
    assert "&lt;script&gt;" in html
    assert "A&amp;B" in html


def test_table_css_present():
    """Rendered output includes table CSS."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Table(rows=[
                        TableRow(cells=[
                            TableCell(inlines=[Text(text="A")]),
                            TableCell(inlines=[Text(text="B")]),
                        ]),
                    ])
                ]
            )
        ]
    )
    html = render(doc)
    assert ".flowdoc-table" in html
    assert "border-collapse" in html