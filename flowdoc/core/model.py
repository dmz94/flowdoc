"""
Internal document model classes.

Represents parsed HTML as a tree of Python objects.
Parser builds these from DOM. Renderer consumes them to generate HTML.
No HTML strings or DOM references allowed in the model.
"""
from __future__ import annotations
from dataclasses import dataclass


# === Inline elements ===

@dataclass
class Text:
    """Plain text content."""
    text: str
    
@dataclass
class Emphasis:
    """Emphasized text (italic). Can contain nested inlines."""
    children: list[Inline]    

@dataclass
class Strong:
    """Strong emphasis (bold). Can contain nested inlines."""
    children: list[Inline]

@dataclass
class Code:
    """Inline code. Plain text only (no nesting)."""
    text: str

@dataclass
class Link:
    """Hyperlink with href and inline children."""
    href: str
    children: list[Inline]

class LineBreak:
    """Line break (br tag). No fields - marker type only."""
    pass 


# Type alias for any inline element
Inline = Text | Emphasis | Strong | Code | Link | LineBreak


# === Block elements ===

@dataclass
class Paragraph:
    """Paragraph containing inline elements."""
    inlines: list[Inline]


@dataclass
class ListItem:
    """
    Single item in a list.
    
    Can contain nested lists via children field.
    """
    inlines: list[Inline]
    children: list[ListBlock]  # Nested lists (0..n)


@dataclass
class ListBlock:
    """Ordered or unordered list."""
    ordered: bool
    items: list[ListItem]


@dataclass
class Quote:
    """Blockquote containing block elements (recursive)."""
    blocks: list[Block]


@dataclass
class Preformatted:
    """Preformatted text from <pre>. Verbatim content."""
    text: str


@dataclass
class Image:
    """Preserved image with external URL. No raw HTML."""
    src: str
    alt: str
    caption: str = ""


# Type alias for any block element
Block = Paragraph | ListBlock | Quote | Preformatted | Image


# === Document structure ===

@dataclass
class Heading:
    """Section heading with level and inline content."""
    level: int  # 1..6
    inlines: list[Inline]


@dataclass
class Section:
    """Document section with heading and blocks."""
    heading: Heading
    blocks: list[Block]


@dataclass
class Document:
    """Top-level document structure."""
    title: str
    sections: list[Section]