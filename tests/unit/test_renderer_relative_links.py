"""
Tests for relative link stripping in rendered output.

Relative links have no base URL to resolve against in converted
documents, so they render as plain text instead of anchor tags.
"""
from decant.core.model import (
    Document, Section, Heading, Paragraph, Text, Link, Strong,
)
from decant.core.renderer import render


def _make_doc(inlines):
    return Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Paragraph(inlines=inlines)],
            )
        ],
    )


def test_absolute_http_link_preserved():
    doc = _make_doc([Link(href="http://example.com", children=[Text(text="click")])])
    html = render(doc)
    assert '<a href="http://example.com">click</a>' in html


def test_absolute_https_link_preserved():
    doc = _make_doc([Link(href="https://example.com", children=[Text(text="click")])])
    html = render(doc)
    assert '<a href="https://example.com">click</a>' in html


def test_fragment_link_preserved():
    doc = _make_doc([Link(href="#section-2", children=[Text(text="jump")])])
    html = render(doc)
    assert '<a href="#section-2">jump</a>' in html


def test_relative_slash_link_stripped():
    doc = _make_doc([Link(href="/wiki/Dyslexia", children=[Text(text="Dyslexia")])])
    html = render(doc)
    assert "<a" not in html
    assert "Dyslexia" in html


def test_relative_path_link_stripped():
    doc = _make_doc([Link(href="page2.html", children=[Text(text="next page")])])
    html = render(doc)
    assert "<a" not in html
    assert "next page" in html


def test_relative_dotdot_link_stripped():
    doc = _make_doc([Link(href="../other/page.html", children=[Text(text="other")])])
    html = render(doc)
    assert "<a" not in html
    assert "other" in html


def test_empty_href_stripped():
    doc = _make_doc([Link(href="", children=[Text(text="nowhere")])])
    html = render(doc)
    assert "<a" not in html
    assert "nowhere" in html


def test_relative_link_preserves_inline_formatting():
    doc = _make_doc([
        Link(href="/wiki/Test", children=[
            Text(text="bold "),
            Strong(children=[Text(text="word")]),
        ])
    ])
    html = render(doc)
    assert "<a" not in html
    assert "bold " in html
    assert "<strong>word</strong>" in html
