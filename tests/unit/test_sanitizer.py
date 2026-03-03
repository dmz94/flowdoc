"""
Tests for HTML sanitization.

Validates that dangerous content is removed while safe content is preserved.
"""
from flowdoc.core.sanitizer import sanitize


def test_allowed_tags_preserved():
    """Safe tags and content pass through."""
    html = "<p>Hello <strong>world</strong></p>"
    result = sanitize(html)
    assert "<p>" in result
    assert "<strong>" in result
    assert "Hello" in result


def test_script_tags_removed():
    """Script tags are stripped."""
    html = "<p>Safe</p><script>alert('xss')</script><p>More</p>"
    result = sanitize(html)
    assert "<script>" not in result
    assert "alert" not in result
    assert "<p>Safe</p>" in result


def test_event_handlers_removed():
    """Event handler attributes are stripped."""
    html = '<p onclick="alert(1)">Click me</p>'
    result = sanitize(html)
    assert "onclick" not in result
    assert "alert" not in result
    assert "Click me" in result


def test_javascript_urls_blocked():
    """javascript: URLs are removed from href."""
    html = '<a href="javascript:alert(1)">Bad link</a>'
    result = sanitize(html)
    assert "javascript:" not in result
    assert "Bad link" in result


def test_data_urls_blocked():
    """data: URLs are removed."""
    html = '<a href="data:text/html,<script>alert(1)</script>">Bad</a>'
    result = sanitize(html)
    assert "data:" not in result


def test_http_urls_allowed():
    """http and https URLs are preserved."""
    html = '<a href="https://example.com">Link</a>'
    result = sanitize(html)
    assert "https://example.com" in result
    assert "<a" in result


def test_comments_stripped():
    """HTML comments are removed."""
    html = "<p>Before</p><!-- secret comment --><p>After</p>"
    result = sanitize(html)
    assert "<!--" not in result
    assert "secret comment" not in result
    assert "Before" in result
    assert "After" in result


def test_allowed_attributes_preserved():
    """href and alt attributes are kept."""
    html = '<a href="http://example.com">Link</a><img alt="Description">'
    result = sanitize(html)
    assert 'href="http://example.com"' in result
    assert 'alt="Description"' in result
    

def test_br_tag_preserved():
    """BR tags survive sanitization."""
    html = "<p>Step 1.<br/>Step 2.</p>"
    result = sanitize(html)
    assert "<br" in result    