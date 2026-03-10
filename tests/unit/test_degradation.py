"""
Tests for HTML element degradation rules.

Validates placeholder generation for unsupported elements
and image preservation for images with external URLs.
"""
from bs4 import BeautifulSoup
from flowdoc.core.degradation import degrade_table, degrade_image, degrade_form, degrade_hr, _is_simple_table
from flowdoc.core.model import Image, Paragraph, Text, Table, TableRow, TableCell


def test_table_counts_rows_and_columns():
    """Simple 2x2 table returns Table model (not placeholder)."""
    html = "<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)

    assert isinstance(result, Table)
    assert len(result.rows) == 2
    assert len(result.rows[0].cells) == 2


def test_table_handles_uneven_columns():
    """Simple table with uneven columns returns Table model."""
    html = "<table><tr><td>A</td></tr><tr><td>B</td><td>C</td><td>D</td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)

    assert isinstance(result, Table)
    assert len(result.rows) == 2


# --- Simple table rendering tests ---

def test_simple_table_returns_table_model():
    """Simple 2x2 table with headers returns Table, not placeholder."""
    html = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Table)
    assert len(result.rows) == 2
    assert result.rows[0].cells[0].is_header is True
    assert result.rows[1].cells[0].is_header is False


def test_simple_table_preserves_cell_text():
    """Cell inline content is parsed correctly."""
    html = "<table><tr><td>Hello</td><td>World</td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Table)
    assert result.rows[0].cells[0].inlines[0].text == "Hello"


def test_complex_table_colspan_returns_placeholder():
    """Table with colspan degrades to placeholder."""
    html = '<table><tr><td colspan="2">Wide</td></tr><tr><td>A</td><td>B</td></tr></table>'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Paragraph)


def test_complex_table_rowspan_returns_placeholder():
    """Table with rowspan degrades to placeholder."""
    html = '<table><tr><td rowspan="2">Tall</td><td>A</td></tr><tr><td>B</td></tr></table>'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Paragraph)


def test_complex_table_nested_returns_placeholder():
    """Nested table degrades to placeholder."""
    html = "<table><tr><td><table><tr><td>Inner</td></tr></table></td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Paragraph)


def test_complex_table_too_many_rows_returns_placeholder():
    """Table with 11 rows degrades to placeholder."""
    rows = "".join(f"<tr><td>{i}</td></tr>" for i in range(11))
    html = f"<table>{rows}</table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Paragraph)


def test_boundary_table_10_rows_returns_table():
    """Table with exactly 10 rows is simple."""
    rows = "".join(f"<tr><td>{i}</td><td>x</td></tr>" for i in range(10))
    html = f"<table>{rows}</table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Table)
    assert len(result.rows) == 10


def test_single_cell_table_returns_placeholder():
    """Table with only 1 cell is not a real table."""
    html = "<table><tr><td>Only</td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    assert isinstance(result, Paragraph)


def test_is_simple_table_empty_returns_false():
    """Empty table is not simple."""
    html = "<table></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    assert _is_simple_table(element) is False


# --- Image preservation (http/https src) ---

def test_image_with_https_src_preserved():
    """Image with https src returns Image model object."""
    html = '<img src="https://example.com/photo.jpg" alt="A sunset">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert isinstance(result, Image)
    assert result.src == "https://example.com/photo.jpg"
    assert result.alt == "A sunset"


def test_image_with_http_src_preserved():
    """Image with http src returns Image model object."""
    html = '<img src="http://example.com/photo.jpg" alt="A photo">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert isinstance(result, Image)
    assert result.src == "http://example.com/photo.jpg"
    assert result.alt == "A photo"


def test_image_with_https_src_no_alt():
    """Image with https src but no alt preserves with empty alt."""
    html = '<img src="https://example.com/photo.jpg">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert isinstance(result, Image)
    assert result.src == "https://example.com/photo.jpg"
    assert result.alt == ""


# --- Image placeholder fallback ---

def test_image_with_alt_no_src_placeholder():
    """Image with alt but no src returns placeholder Text."""
    html = '<img alt="A beautiful sunset">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert isinstance(result, Text)
    assert result.text == "[Image: A beautiful sunset]"


def test_image_without_alt_or_src():
    """Image without alt or src uses generic placeholder."""
    html = '<img>'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert isinstance(result, Text)
    assert result.text == "[Image not included]"


def test_image_with_empty_alt_no_src():
    """Image with empty alt and no src is treated as missing."""
    html = '<img alt="">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert result.text == "[Image not included]"


def test_image_with_data_src_placeholder():
    """Image with data: src degrades to placeholder."""
    html = '<img src="data:image/png;base64,abc123" alt="Logo">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert isinstance(result, Text)
    assert result.text == "[Image: Logo]"


def test_image_with_relative_src_placeholder():
    """Image with relative src (no scheme) degrades to placeholder."""
    html = '<img src="/images/photo.jpg" alt="Photo">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)

    assert isinstance(result, Text)
    assert result.text == "[Image: Photo]"


# --- Form and HR (unchanged) ---

def test_form_returns_placeholder():
    """Form elements get static placeholder."""
    html = '<form><input type="text"></form>'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("form")
    result = degrade_form(element)

    assert isinstance(result, Paragraph)
    assert result.inlines[0].text == "[Form omitted]"


def test_hr_returns_separator():
    """HR becomes visual separator token."""
    result = degrade_hr()

    assert isinstance(result, Paragraph)
    assert result.inlines[0].text == "[-]"
