"""
Tests for internal document model classes.

Verifies dataclass creation and nested structures.
"""
from decant.core.model import (
    Text, Emphasis, Strong, Code, Link,
    Paragraph, ListItem, ListBlock, Quote, Preformatted,
    Heading, Section, Document
)


def test_text_creation():
    """Text holds a string."""
    t = Text(text="Hello")
    assert t.text == "Hello"


def test_emphasis_nesting():
    """Emphasis can contain other inlines."""
    em = Emphasis(children=[
        Text(text="Hello "),
        Strong(children=[Text(text="world")])
    ])
    assert len(em.children) == 2
    assert em.children[0].text == "Hello "


def test_link_creation():
    """Link holds href and inline children."""
    link = Link(
        href="https://example.com",
        children=[Text(text="Click here")]
    )
    assert link.href == "https://example.com"
    assert len(link.children) == 1

def test_paragraph_creation():
    """Paragraph contains inline elements."""
    p = Paragraph(inlines=[
        Text(text="Hello "),
        Emphasis(children=[Text(text="world")])
    ])
    assert len(p.inlines) == 2


def test_list_creation():
    """ListBlock contains ListItems."""
    lst = ListBlock(
        ordered=True,
        items=[
            ListItem(inlines=[Text(text="First")], children=[]),
            ListItem(inlines=[Text(text="Second")], children=[])
        ]
    )
    assert lst.ordered is True
    assert len(lst.items) == 2
    assert lst.items[0].inlines[0].text == "First"

def test_nested_list():
    """ListItem can contain nested lists."""
    nested = ListBlock(
        ordered=False,
        items=[ListItem(inlines=[Text(text="Nested item")], children=[])]
    )
    parent = ListItem(
        inlines=[Text(text="Parent item")],
        children=[nested]
    )
    assert len(parent.children) == 1
    assert parent.children[0].items[0].inlines[0].text == "Nested item"


def test_complete_document():
    """Document contains sections with headings and blocks."""
    doc = Document(
        title="Test Document",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Introduction")]),
                blocks=[
                    Paragraph(inlines=[Text(text="First paragraph.")]),
                    ListBlock(
                        ordered=False,
                        items=[ListItem(inlines=[Text(text="Item one")], children=[])]
                    )
                ]
            )
        ]
    )
    assert doc.title == "Test Document"
    assert len(doc.sections) == 1
    assert doc.sections[0].heading.level == 1
    assert len(doc.sections[0].blocks) == 2