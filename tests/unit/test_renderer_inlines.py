"""
Tests for renderer inline element rendering.

Part 3 of renderer tests - validates inline element HTML generation.
"""
from decant.core.model import Document, Section, Heading, Paragraph, Text, Emphasis, Strong, Code, Link
from decant.core.renderer import render


def test_renders_plain_text():
    """Plain text is escaped."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Paragraph(inlines=[Text(text="Simple text")])]
            )
        ]
    )
    html = render(doc)
    assert "Simple text" in html


def test_escapes_html_in_text():
    """HTML characters in text are escaped."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Paragraph(inlines=[Text(text="<script>alert()</script>")])]
            )
        ]
    )
    html = render(doc)
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_renders_emphasis():
    """Emphasis renders as <em>."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Paragraph(inlines=[
                        Text(text="Normal "),
                        Emphasis(children=[Text(text="emphasized")])
                    ])
                ]
            )
        ]
    )
    html = render(doc)
    assert "<em>emphasized</em>" in html


def test_renders_strong():
    """Strong renders as <strong>."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Paragraph(inlines=[Strong(children=[Text(text="bold")])])
                ]
            )
        ]
    )
    html = render(doc)
    assert "<strong>bold</strong>" in html


def test_renders_code():
    """Code renders as <code> with escaping."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Paragraph(inlines=[Code(text="<html>")])]
            )
        ]
    )
    html = render(doc)
    assert "<code>&lt;html&gt;</code>" in html


def test_renders_link():
    """Links render as <a> with escaped href."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Paragraph(inlines=[
                        Link(href="https://example.com", children=[Text(text="click")])
                    ])
                ]
            )
        ]
    )
    html = render(doc)
    assert '<a href="https://example.com">click</a>' in html


def test_renders_nested_inlines():
    """Nested inline elements render correctly."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Paragraph(inlines=[
                        Strong(children=[
                            Text(text="Bold with "),
                            Emphasis(children=[Text(text="italic")])
                        ])
                    ])
                ]
            )
        ]
    )
    html = render(doc)
    assert "<strong>Bold with <em>italic</em></strong>" in html


def test_renders_linebreak():
    """LineBreak renders as br element."""
    from decant.core.model import LineBreak
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[
                    Paragraph(inlines=[
                        Text(text="Step 1."),
                        LineBreak(),
                        Text(text="Step 2.")
                    ])
                ]
            )
        ]
    )
    html = render(doc)
    assert "<br>" in html