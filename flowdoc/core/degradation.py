"""
Degradation rules for unsupported HTML elements.

Converts tables, images, forms, and other unsupported elements into
placeholder model objects. See decisions.md section 7 for rules.
"""
from urllib.parse import urlparse

from bs4 import Tag
from flowdoc.core.model import Image, Paragraph, Text, Table, TableRow, TableCell


def _is_simple_table(element: Tag) -> bool:
    """
    Check if a table meets the simple-table boundary.

    Simple: <= 10 rows, no colspan, no rowspan, no nested tables,
    more than 1 cell total.
    """
    # No nested tables
    if element.find("table"):
        return False

    rows = element.find_all("tr")
    if len(rows) == 0 or len(rows) > 10:
        return False

    total_cells = 0
    for row in rows:
        cells = row.find_all(["td", "th"])
        for cell in cells:
            if cell.get("colspan") or cell.get("rowspan"):
                return False
            total_cells += 1

    return total_cells > 1


def degrade_table(element: Tag) -> Paragraph | Table:
    """
    Convert table to Table model if simple, otherwise placeholder.

    Simple tables (<= 10 rows, no colspan/rowspan/nesting, > 1 cell)
    are rendered as styled HTML tables. Complex tables degrade to
    placeholder text with dimensions.

    Args:
        element: BeautifulSoup Tag for <table>

    Returns:
        Table for simple tables, Paragraph placeholder for complex
    """
    if _is_simple_table(element):
        return _parse_simple_table(element)

    rows = element.find_all("tr")
    row_count = len(rows)

    col_count = 0
    for row in rows:
        cells = row.find_all(["td", "th"])
        col_count = max(col_count, len(cells))

    text = f"[Table omitted - {row_count} rows, {col_count} columns]"
    return Paragraph(inlines=[Text(text=text)])


def _parse_simple_table(element: Tag) -> Table:
    """
    Parse a simple table element into a Table model.

    Walks rows and cells, parsing inline content from each cell.
    Cells are marked as headers if they are <th> elements.
    """
    from flowdoc.core.parser import parse_inlines

    model_rows: list[TableRow] = []
    for tr in element.find_all("tr"):
        cells: list[TableCell] = []
        for cell in tr.find_all(["td", "th"]):
            inlines = parse_inlines(cell)
            cells.append(TableCell(
                inlines=inlines,
                is_header=(cell.name == "th"),
            ))
        if cells:
            model_rows.append(TableRow(cells=cells))

    return Table(rows=model_rows)


def degrade_image(element: Tag) -> Image | Text:
    """
    Preserve image when src is http/https, otherwise placeholder.

    Per decisions.md section 7: images with external URLs are rendered
    as <img> tags. Images without valid src degrade to WARN placeholder.

    Args:
        element: BeautifulSoup Tag for <img>

    Returns:
        Image when src is http/https, Text placeholder otherwise
    """
    src = element.get("src", "").strip()
    alt = element.get("alt", "").strip()

    if src:
        scheme = urlparse(src).scheme.lower()
        if scheme in ("http", "https"):
            return Image(src=src, alt=alt)

    # Fallback: WARN placeholder
    if alt:
        text = f"[Image: {alt}]"
    else:
        text = "[Image not included]"

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