"""
Tests for input validation.

Validates that non-semantic HTML is rejected with the correct error
message and that valid HTML passes through without error.
See decisions.md section 3 for validation rules.
"""
import pytest
from flowdoc.core.parser import parse, ValidationError


VALID_HTML = "<html><body><h1>Title</h1><p>Content</p></body></html>"

ERROR_MESSAGE = (
    "Input HTML lacks semantic structure "
    "(requires at least one h1-h3 and body content in p/ul/ol)."
)


def test_valid_html_passes():
    """Valid semantic HTML does not raise ValidationError."""
    doc = parse(VALID_HTML)
    assert doc is not None


def test_no_headings_raises():
    """HTML with no headings raises ValidationError."""
    html = "<html><body><p>No headings here</p></body></html>"
    with pytest.raises(ValidationError):
        parse(html)


def test_no_body_content_raises():
    """HTML with headings but no p/ul/ol raises ValidationError."""
    html = "<html><body><h1>Title only</h1></body></html>"
    with pytest.raises(ValidationError):
        parse(html)


def test_h4_only_raises():
    """HTML with only h4-h6 headings raises ValidationError."""
    html = "<html><body><h4>Too deep</h4><p>Content</p></body></html>"
    with pytest.raises(ValidationError):
        parse(html)


def test_h2_satisfies_heading_requirement():
    """h2 satisfies the heading requirement."""
    html = "<html><body><h2>Section</h2><p>Content</p></body></html>"
    doc = parse(html)
    assert doc is not None


def test_h3_satisfies_heading_requirement():
    """h3 satisfies the heading requirement."""
    html = "<html><body><h3>Section</h3><p>Content</p></body></html>"
    doc = parse(html)
    assert doc is not None


def test_ul_satisfies_body_content_requirement():
    """ul satisfies the body content requirement."""
    html = "<html><body><h1>Title</h1><ul><li>Item</li></ul></body></html>"
    doc = parse(html)
    assert doc is not None


def test_ol_satisfies_body_content_requirement():
    """ol satisfies the body content requirement."""
    html = "<html><body><h1>Title</h1><ol><li>Item</li></ol></body></html>"
    doc = parse(html)
    assert doc is not None


def test_exact_error_message():
    """ValidationError message matches spec exactly."""
    html = "<html><body><p>No headings</p></body></html>"
    with pytest.raises(ValidationError) as exc_info:
        parse(html)
    assert str(exc_info.value) == ERROR_MESSAGE