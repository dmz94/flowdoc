"""
Tests for HTML element degradation rules.

Validates placeholder generation for unsupported elements.
"""
from bs4 import BeautifulSoup
from flowdoc.core.degradation import degrade_table, degrade_image, degrade_form, degrade_hr
from flowdoc.core.model import Paragraph, Text


def test_table_counts_rows_and_columns():
    """Table placeholder includes correct dimensions."""
    html = "<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    
    assert isinstance(result, Paragraph)
    assert len(result.inlines) == 1
    assert result.inlines[0].text == "[Table omitted - 2 rows, 2 columns]"


def test_table_handles_uneven_columns():
    """Table uses max column count across rows."""
    html = "<table><tr><td>A</td></tr><tr><td>B</td><td>C</td><td>D</td></tr></table>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("table")
    result = degrade_table(element)
    
    assert result.inlines[0].text == "[Table omitted - 2 rows, 3 columns]"


def test_image_with_alt_text():
    """Image with alt text includes description."""
    html = '<img alt="A beautiful sunset">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)
    
    assert isinstance(result, Text)
    assert result.text == "[Image: A beautiful sunset]"


def test_image_without_alt():
    """Image without alt attribute uses generic placeholder."""
    html = '<img src="photo.jpg">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)
    
    assert isinstance(result, Text)
    assert result.text == "[Image omitted]"


def test_image_with_empty_alt():
    """Image with empty alt is treated as missing."""
    html = '<img alt="">'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("img")
    result = degrade_image(element)
    
    assert result.text == "[Image omitted]"


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