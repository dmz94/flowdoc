"""
End-to-end integration tests.

Tests complete pipeline with real HTML fixtures.
"""
from pathlib import Path

from bs4 import BeautifulSoup

from flowdoc.core.content_selector import detect_mode
from flowdoc.core.model import Image
from flowdoc.core.parser import parse, extract_with_trafilatura
from flowdoc.core.renderer import render

FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "pipeline-audit" / "test-pages"
UNIT_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "unit" / "test-data"


def test_simple_article_conversion():
    """Converts simple article HTML end-to-end."""
    # Read fixture
    fixture_path = UNIT_FIXTURE_DIR / "simple_article.html"
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
    fixture_path = UNIT_FIXTURE_DIR / "simple_article.html"
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


def _run_full_pipeline(fixture_path: Path) -> tuple:
    """Run detect_mode → extract → parse → render on a fixture. Returns (doc, html)."""
    html = fixture_path.read_text(encoding="utf-8")
    mode = detect_mode(html)
    original_title = None
    html_to_parse = html
    if mode == "extract":
        original_soup = BeautifulSoup(html, "lxml")
        original_title = original_soup.find("title")
        html_to_parse = extract_with_trafilatura(html)
    doc = parse(html_to_parse, original_title=original_title)
    rendered = render(doc)
    return doc, rendered


def test_deterministic_output():
    """Same input produces byte-identical output across two runs (decisions.md §12)."""
    fixture_path = FIXTURE_DIR / "nhs-dyslexia.html"
    _, output_a = _run_full_pipeline(fixture_path)
    _, output_b = _run_full_pipeline(fixture_path)
    assert output_a == output_b


def test_nhs_dyslexia_end_to_end():
    """NHS dyslexia fixture converts cleanly end-to-end."""
    fixture_path = FIXTURE_DIR / "nhs-dyslexia.html"
    doc, rendered = _run_full_pipeline(fixture_path)
    assert "<!DOCTYPE html>" in rendered
    assert "<style>" in rendered
    assert len(doc.sections) > 0
    assert "dyslexia" in rendered.lower()
    assert "[Form omitted]" not in rendered


def test_smithsonian_end_to_end():
    """Smithsonian fixture converts with multiple sections."""
    fixture_path = FIXTURE_DIR / "smithsonian-homo-sapiens.html"
    doc, rendered = _run_full_pipeline(fixture_path)
    assert "<!DOCTYPE html>" in rendered
    assert len(doc.sections) >= 5
    assert "Homo sapiens" in rendered


def test_pbs_with_images_end_to_end():
    """PBS fixture preserves images through the pipeline."""
    fixture_path = FIXTURE_DIR / "pbs-crowd-surges.html"
    _, rendered = _run_full_pipeline(fixture_path)
    assert "<!DOCTYPE html>" in rendered
    assert "<img " in rendered


def test_image_preservation_end_to_end():
    """PBS fixture produces Image blocks in the document model."""
    fixture_path = FIXTURE_DIR / "pbs-crowd-surges.html"
    doc, rendered = _run_full_pipeline(fixture_path)
    all_blocks = [b for s in doc.sections for b in s.blocks]
    image_blocks = [b for b in all_blocks if isinstance(b, Image)]
    assert len(image_blocks) >= 1, "Expected at least one Image block in PBS fixture"
    assert '<img src="http' in rendered