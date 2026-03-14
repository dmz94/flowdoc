"""
Tests for parser inline element parsing.

Part 4 of parser tests - validates inline element conversion and nesting.
"""
from decant.core.parser import parse
from decant.core.model import Text, Emphasis, Strong, Code, Link


def test_parses_plain_text():
    """Plain text becomes Text objects."""
    html = "<body><h1>Simple heading</h1><p>Text</p></body>"
    doc = parse(html)
    heading = doc.sections[0].heading
    assert len(heading.inlines) == 1
    assert isinstance(heading.inlines[0], Text)
    assert heading.inlines[0].text == "Simple heading"


def test_parses_emphasis():
    """Em and i tags become Emphasis."""
    html = "<body><h1>Title</h1><p>Text with <em>emphasis</em> and <i>italic</i></p></body>"
    doc = parse(html)
    para = doc.sections[0].blocks[0]
    # Should have: Text, Emphasis, Text, Emphasis
    assert len(para.inlines) == 4
    assert isinstance(para.inlines[1], Emphasis)
    assert isinstance(para.inlines[3], Emphasis)


def test_parses_strong():
    """Strong and b tags become Strong."""
    html = "<body><h1>Title</h1><p>Text with <strong>strong</strong> and <b>bold</b></p></body>"
    doc = parse(html)
    para = doc.sections[0].blocks[0]
    assert isinstance(para.inlines[1], Strong)
    assert isinstance(para.inlines[3], Strong)


def test_parses_inline_code():
    """Code tags become Code."""
    html = "<body><h1>Title</h1><p>Use <code>print()</code> function</p></body>"
    doc = parse(html)
    para = doc.sections[0].blocks[0]
    assert isinstance(para.inlines[1], Code)
    assert para.inlines[1].text == "print()"


def test_parses_links():
    """A tags become Link objects."""
    html = '<body><h1>Title</h1><p>Visit <a href="https://example.com">our site</a> for more information about this topic and other details</p></body>'
    doc = parse(html)
    para = doc.sections[0].blocks[0]
    link = para.inlines[1]
    assert isinstance(link, Link)
    assert link.href == "https://example.com"
    assert len(link.children) == 1
    assert link.children[0].text == "our site"


def test_parses_nested_inlines():
    """Handles nested inline elements."""
    html = "<body><h1>Title</h1><p><strong>Bold with <em>nested emphasis</em></strong></p></body>"
    doc = parse(html)
    para = doc.sections[0].blocks[0]
    strong = para.inlines[0]
    assert isinstance(strong, Strong)
    assert len(strong.children) == 2
    assert isinstance(strong.children[0], Text)
    assert isinstance(strong.children[1], Emphasis)


def test_degrades_inline_image():
    """Inline images become Text placeholders."""
    html = '<body><h1>Title</h1><p>Text <img alt="photo"> more text</p></body>'
    doc = parse(html)
    para = doc.sections[0].blocks[0]
    # Should have: Text, Text (image placeholder), Text
    assert len(para.inlines) == 3
    assert "[Image: photo]" in para.inlines[1].text


def test_br_tag_becomes_linebreak():
    """BR tags produce a LineBreak inline object."""
    from decant.core.model import LineBreak
    html = "<body><h1>Title</h1><p>Step 1.<br/>Step 2.</p></body>"
    doc = parse(html)
    para = doc.sections[0].blocks[0]
    assert any(isinstance(i, LineBreak) for i in para.inlines)