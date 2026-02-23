"""
HTML to Document model parser.

Converts sanitized DOM tree to internal model representation.
Pipeline: Step 4 (after sanitization and content selection)
See decisions.md sections 5-8 for parsing rules.
"""
from bs4 import BeautifulSoup, Tag, NavigableString

from flowdoc.core.model import (
    Document, Section, Heading, Block, Inline,
    Paragraph, ListBlock, ListItem, Quote, Preformatted,
    Text, Emphasis, Strong, Code, Link
)
from flowdoc.core.sanitizer import sanitize
from flowdoc.core.content_selector import select_main_content
from flowdoc.core.degradation import (
    degrade_table, degrade_image, degrade_form, degrade_hr
)


def parse(html: str) -> Document:
    """
    Parse HTML string to Document model.
    
    Full pipeline: sanitize -> parse DOM -> select content -> build model.
    
    Args:
        html: Raw HTML string
        
    Returns:
        Document model with title and sections
    """
    # Step 1: Sanitize
    clean_html = sanitize(html)
    
    # Step 2: Parse DOM
    soup = BeautifulSoup(clean_html, "lxml")
    
    # Step 3: Select main content
    content = select_main_content(soup)
    
    # Step 4: Build sections
    sections = build_sections(content)
    
    # Step 5: Extract title
    title = extract_title(soup, content)
    
    return Document(title=title, sections=sections)


def extract_title(soup: BeautifulSoup, content: Tag) -> str:
    """
    Extract document title from <title> tag or first <h1>.
    
    Per decisions.md section 5:
    - If <title> exists, use its text
    - Else if first <h1> in content exists, use its text
    - Else empty string
    
    Args:
        soup: Full DOM tree (for <title> access)
        content: Selected content subtree
        
    Returns:
        Title string (may be empty)
    """
    # Try <title> tag first
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text().strip()
    
    # Fall back to first <h1> in content
    h1 = content.find("h1")
    if h1:
        return h1.get_text().strip()
    
    return ""

def build_sections(content: Tag) -> list[Section]:
    """
    Build sections from headings in content.
    
    Per decisions.md section 5:
    - Drop all content before first heading
    - Each heading starts a new section
    - Section continues until next heading (any level)
    
    v2 consideration: Could preserve pre-heading content as preamble with warning.
    
    Args:
        content: Selected content subtree
        
    Returns:
        List of Section objects
    """
    # Find all headings (h1-h6)
    headings = content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    
    if not headings:
        # No headings found - will fail validation later
        return []
    
    sections = []
    
    for i, heading_elem in enumerate(headings):
        # Parse the heading
        heading = parse_heading(heading_elem)
        
        # Collect blocks until next heading
        blocks = []
        current = heading_elem.next_sibling
        
        # Find next heading element (or None if last section)
        next_heading = headings[i + 1] if i + 1 < len(headings) else None
        
        while current:
            # Stop if we hit the next heading
            if next_heading and current == next_heading:
                break
            
            # Parse blocks (TODO: implement parse_block next)
            if isinstance(current, Tag):
                block = parse_block(current)
                if block:
                    blocks.append(block)
            
            current = current.next_sibling
        
        sections.append(Section(heading=heading, blocks=blocks))
    
    return sections


def parse_heading(element: Tag) -> Heading:
    """
    Parse heading element to Heading model.
    
    Args:
        element: BeautifulSoup Tag for h1-h6
        
    Returns:
        Heading with level and inline content
    """
    # Extract level from tag name (h1 -> 1, h2 -> 2, etc.)
    level = int(element.name[1])
    
    # Parse inline content (TODO: implement parse_inlines next)
    inlines = parse_inlines(element)
    
    return Heading(level=level, inlines=inlines)


def parse_block(element: Tag) -> Block | None:
    """
    Parse block-level element to Block model.
    
    Returns None for unrecognized elements (silently skipped in v1).
    v2: Add warning logging for skipped elements.
    
    Args:
        element: BeautifulSoup Tag for block element
        
    Returns:
        Block model object or None if unsupported
    """
    tag_name = element.name
    
    if tag_name == "p":
        return parse_paragraph(element)
    elif tag_name in ("ul", "ol"):
        return parse_list(element)
    elif tag_name == "blockquote":
        return parse_quote(element)
    elif tag_name == "pre":
        return parse_preformatted(element)
    elif tag_name == "table":
        return degrade_table(element)
    elif tag_name == "img":
        # Image returns Text (inline), wrap in Paragraph
        return Paragraph(inlines=[degrade_image(element)])
    elif tag_name in ("form", "input", "textarea", "select", "button"):
        return degrade_form(element)
    elif tag_name == "hr":
        return degrade_hr()
    else:
        # Unknown block - skip silently in v1
        return None


def parse_paragraph(element: Tag) -> Paragraph:
    """
    Parse paragraph to Paragraph model.
    
    Args:
        element: BeautifulSoup Tag for <p>
        
    Returns:
        Paragraph with inline content
    """
    # TODO: Implement parse_inlines (next part)
    inlines = parse_inlines(element)
    return Paragraph(inlines=inlines)


def parse_list(element: Tag) -> ListBlock:
    """
    Parse list to ListBlock model.
    
    Handles nested lists via ListItem.children.
    
    Args:
        element: BeautifulSoup Tag for <ul> or <ol>
        
    Returns:
        ListBlock with items
    """
    ordered = element.name == "ol"
    items = []
    
    for li in element.find_all("li", recursive=False):  # Direct children only
    # Parse inlines, but exclude nested lists from inline parsing
    # (nested lists are handled separately via children)
        li_copy = li.__copy__()
        for nested in li_copy.find_all(["ul", "ol"], recursive=False):
            nested.decompose()
        inlines = parse_inlines(li_copy)
        
        # Find nested lists
        nested_lists = li.find_all(["ul", "ol"], recursive=False)
        children = [parse_list(nested) for nested in nested_lists]
        
        items.append(ListItem(inlines=inlines, children=children))
    
    return ListBlock(ordered=ordered, items=items)


def parse_quote(element: Tag) -> Quote:
    """
    Parse blockquote to Quote model (recursive).
    
    Args:
        element: BeautifulSoup Tag for <blockquote>
        
    Returns:
        Quote containing blocks
    """
    blocks = []
    for child in element.children:
        if isinstance(child, Tag):
            block = parse_block(child)
            if block:
                blocks.append(block)
    
    return Quote(blocks=blocks)


def parse_preformatted(element: Tag) -> Preformatted:
    """
    Parse <pre> to Preformatted model.
    
    Preserves whitespace exactly.
    
    Args:
        element: BeautifulSoup Tag for <pre>
        
    Returns:
        Preformatted with verbatim text
    """
    return Preformatted(text=element.get_text())

def collapse_whitespace(text: str) -> str:
    """
    Collapse runs of whitespace into a single space.

    Preserves leading/trailing space if the original had whitespace
    at those boundaries. This matches HTML whitespace collapsing rules
    (decisions.md section 8).
    """
    import re
    if not text:
        return ""
    leading = " " if text[0].isspace() else ""
    trailing = " " if text[-1].isspace() else ""
    collapsed = re.sub(r"\s+", " ", text.strip())
    if not collapsed:
        return ""
    return leading + collapsed + trailing


def parse_inlines(element: Tag) -> list[Inline]:
    """
    Parse inline content recursively.
    
    Handles nested inline elements and text nodes.
    Applies whitespace normalization.
    
    Args:
        element: BeautifulSoup Tag containing inline content
        
    Returns:
        List of Inline model objects
    """
    result = []
    
    for child in element.children:
        if isinstance(child, NavigableString):
            # Text node
            text = collapse_whitespace(str(child))
            if text:  # Skip empty text nodes
                result.append(Text(text=text))
        elif isinstance(child, Tag):
            inline = parse_inline_element(child)
            if isinstance(inline, list):
                result.extend(inline)
            elif inline:
                result.append(inline)
    
    return result


def parse_inline_element(element: Tag) -> Inline | list[Inline] | None:
    """
    Parse single inline element.
    
    Returns Inline object, list of Inlines, or None for unknown elements.
    
    Args:
        element: BeautifulSoup Tag for inline element
        
    Returns:
        Inline model object(s) or None
    """
    tag_name = element.name
    
    if tag_name == "br":
        return Text(text=" ")
    elif tag_name in ("em", "i"):
        return Emphasis(children=parse_inlines(element))
    elif tag_name in ("strong", "b"):
        return Strong(children=parse_inlines(element))
    elif tag_name == "code":
        # Inline code - plain text only
        return Code(text=element.get_text())
    elif tag_name == "a":
        href = element.get("href", "")
        return Link(href=href, children=parse_inlines(element))
    elif tag_name == "img":
        # Image inside paragraph
        return degrade_image(element)
    else:
        # Unknown inline element - extract text
        text = element.get_text().strip()
        if text:
            return Text(text=text)
        return None