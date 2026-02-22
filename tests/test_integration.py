"""
End-to-end integration tests.

Tests complete pipeline with real HTML fixtures.
"""
from pathlib import Path
from flowdoc.core.parser import parse
from flowdoc.core.renderer import render


def test_simple_article_conversion():
    """Converts simple article HTML end-to-end."""
    # Read fixture
    fixture_path = Path(__file__).parent / "fixtures" / "input" / "simple_article.html"
    html_input = fixture_path.read_text(encoding='utf-8')
    
    # Parse
    document = parse(html_input)
    
    # Verify document structure
    assert document.title == "Simple Article Example"
    assert len(document.sections) == 3  # h1 + 2 h2s
    
    # Verify sections have content
    assert document.sections[0].heading.level == 1
    assert document.sections[1].heading.level == 2
    assert document.sections[2].heading.level == 2
    
    # Render
    html_output = render(document)
    
    # Verify output structure
    assert "<!DOCTYPE html>" in html_output
    assert '<meta charset="utf-8">' in html_output
    assert "<style>" in html_output
    assert "</style>" in html_output
    
    # Verify content preserved
    assert "Getting Started with Python" in html_output
    assert "Why Choose Python?" in html_output
    assert "<strong>efficient high-level data structures</strong>" in html_output
    assert "<em>read</em>" in html_output
    
    # Verify nested list preserved
    assert html_output.count("<ul>") == 2  # Parent and nested
    assert "Active forums" in html_output
    
    # Verify link preserved
    assert 'href="https://python.org"' in html_output
    assert "python.org" in html_output
    
    # Verify blockquote preserved
    assert "<blockquote>" in html_output
    assert "freedom programmers need" in html_output
    
  # Verify preformatted code preserved
    assert "<pre>" in html_output
    assert "print" in html_output
    assert "Hello, World" in html_output
    
    # Verify CSS applied
    assert "font-family:" in html_output
    assert "line-height:" in html_output
    assert "background-color:" in html_output


def test_renders_valid_html():
    """Output is valid HTML5."""
    fixture_path = Path(__file__).parent / "fixtures" / "input" / "simple_article.html"
    html_input = fixture_path.read_text(encoding='utf-8')
    
    document = parse(html_input)
    html_output = render(document)
    
    # Basic HTML5 validation
    assert html_output.startswith("<!DOCTYPE html>")
    assert "<html" in html_output
    assert "</html>" in html_output
    assert "<head>" in html_output
    assert "</head>" in html_output
    assert "<body>" in html_output
    assert "</body>" in html_output
    
    # No unclosed tags (rough check)
    assert html_output.count("<p>") == html_output.count("</p>")
    assert html_output.count("<ul>") == html_output.count("</ul>")