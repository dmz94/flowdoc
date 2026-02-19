"""
Degradation rules for unsupported HTML elements.

Converts tables, images, forms, and other unsupported elements into
placeholder model objects. See decisions.md section 7 for rules.
"""
from bs4 import Tag
from flowdoc.core.model import Paragraph, Text


def degrade_table(element: Tag) -> Paragraph:
    """
    Convert table to placeholder text with dimensions.
    
    v2 consideration: Simple tables could be rendered with readable styling.
    
    Args:
        element: BeautifulSoup Tag for <table>
        
    Returns:
        Paragraph with placeholder text showing row/column count
    """
    rows = element.find_all("tr")
    row_count = len(rows)
    
    # Find max columns across all rows
    col_count = 0
    for row in rows:
        cells = row.find_all(["td", "th"])
        col_count = max(col_count, len(cells))
    
    text = f"[Table omitted - {row_count} rows, {col_count} columns]"
    return Paragraph(inlines=[Text(text=text)])


def degrade_image(element: Tag) -> Text:
    """
    Convert image to placeholder text with alt description.
    
    v2 consideration: Images could be included with proper sizing and alt text.
    Base64 embedding would bloat file size and break self-contained goal.
    
    Args:
        element: BeautifulSoup Tag for <img>
        
    Returns:
        Text with alt description or generic placeholder
    """
    alt = element.get("alt", "").strip()
    
    if alt:
        text = f"[Image: {alt}]"
    else:
        text = "[Image omitted]"
    
    return Text(text=text)


def degrade_form(element: Tag) -> Paragraph:
    """
    Convert form to placeholder.
    
    Forms are interactive and incompatible with static readable output.
    Will not be supported in future versions.
    
    Args:
        element: BeautifulSoup Tag for form element
        
    Returns:
        Paragraph with static placeholder
    """
    return Paragraph(inlines=[Text(text="[Form omitted]")])


def degrade_hr() -> Paragraph:
    """
    Convert horizontal rule to visual separator.
    
    v2 consideration: Could render as actual CSS border for visual clarity.
    
    Returns:
        Paragraph with separator token
    """
    return Paragraph(inlines=[Text(text="[-]")])