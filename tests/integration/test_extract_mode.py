"""
Tests for extract mode pipeline.

Validates extract mode behavior including known limitations.
Extract mode uses Trafilatura for boilerplate removal - formatting
preservation is best-effort, not guaranteed.

Known documented limitations in extract mode:
- <pre> code blocks are converted to <blockquote>
- Some inline spacing may be lost around inline elements
"""
import pytest
import trafilatura as _trafilatura
from pathlib import Path
from flowdoc.core.parser import parse, extract_with_trafilatura, ExtractionMode
from flowdoc.core.renderer import render


def test_extract_with_trafilatura_returns_string():
    """extract_with_trafilatura returns a non-empty string."""
    html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    result = extract_with_trafilatura(html)
    assert isinstance(result, str)
    assert len(result) > 0


def test_extract_with_trafilatura_falls_back_on_no_headings():
    """Falls back to original HTML if Trafilatura strips all headings."""
    html = "<html><body><p>No headings here at all</p></body></html>"
    result = extract_with_trafilatura(html)
    assert result == html


def test_extract_mode_preserves_headings():
    """Extract mode preserves heading structure."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "input" / "simple_article.html"
    html = fixture_path.read_text(encoding='utf-8')
    extracted = extract_with_trafilatura(html)
    assert "<h1" in extracted
    assert "<h2" in extracted


def test_extract_mode_pre_becomes_blockquote():
    """
    Known limitation: <pre> blocks are converted to <blockquote> by Trafilatura.

    This is documented extract mode behavior, not a bug.
    Content is preserved, block type changes.
    In transform mode, <pre> is preserved correctly.
    """
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "input" / "simple_article.html"
    html = fixture_path.read_text(encoding='utf-8')
    extracted = extract_with_trafilatura(html)
    # <pre> is converted - content should still be present
    assert "Hello, World" in extracted
    # <pre> tag is not preserved in extract mode
    assert "<pre>" not in extracted


def test_transform_mode_preserves_pre():
    """Transform mode preserves <pre> blocks exactly."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "input" / "simple_article.html"
    html = fixture_path.read_text(encoding='utf-8')
    # Direct parse() call = transform mode (no Trafilatura)
    doc = parse(html)
    output = render(doc)
    assert "<pre>" in output


def test_transform_mode_preserves_strong():
    """Transform mode preserves <strong> inline formatting."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "input" / "simple_article.html"
    html = fixture_path.read_text(encoding='utf-8')
    doc = parse(html)
    output = render(doc)
    assert "<strong>efficient high-level data structures</strong>" in output


def test_transform_mode_preserves_links():
    """Transform mode preserves links."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "input" / "simple_article.html"
    html = fixture_path.read_text(encoding='utf-8')
    doc = parse(html)
    output = render(doc)
    assert 'href="https://python.org"' in output


def test_baseline_extraction_mode_matches_default():
    """
    ExtractionMode "baseline" produces byte-identical output to the implicit default.

    This guards against accidental changes to baseline behavior when the
    extraction_mode parameter is added. The default must equal "baseline".
    """
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "input" / "simple_article.html"
    html = fixture_path.read_text(encoding='utf-8')
    default_result = extract_with_trafilatura(html)
    baseline_result = extract_with_trafilatura(html, extraction_mode="baseline")
    assert default_result == baseline_result


def test_extraction_mode_default_parameter_is_baseline():
    """
    The extraction_mode parameter default is "baseline" at the function signature level.

    Guards against a refactor silently changing the default to "recall" or "precision".
    Checked via inspect so the assertion is independent of call-site behavior.
    """
    import inspect
    sig = inspect.signature(extract_with_trafilatura)
    default = sig.parameters["extraction_mode"].default
    assert default == "baseline", f"Expected 'baseline', got {default!r}"


def test_recall_mode_differs_from_baseline_on_real_fixture():
    """
    "recall" produces different output from "baseline" on at least one real fixture.

    Guards against the mode switch being accidentally collapsed (i.e., all modes
    producing identical output, which would defeat the purpose of the switch).
    Uses cdc fixture where Phase 2A measurements showed chars 4656 vs 5073.
    """
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "user-study" / "cdc.html"
    html = fixture_path.read_text(encoding="utf-8")
    baseline_result = extract_with_trafilatura(html, extraction_mode="baseline")
    recall_result = extract_with_trafilatura(html, extraction_mode="recall")
    assert baseline_result != recall_result, (
        "baseline and recall produced identical output on cdc fixture; "
        "mode kwargs may have been collapsed"
    )


def test_extract_mode_full_pipeline_wikipedia():
    """Extract mode processes Wikipedia fixture without crashing."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "input" / "wikipedia_dyslexia.html"
    html = fixture_path.read_text(encoding='utf-8')
    extracted = extract_with_trafilatura(html)
    # Capture title before extraction
    from bs4 import BeautifulSoup
    original_soup = BeautifulSoup(html, "lxml")
    original_title = original_soup.find("title")
    doc = parse(extracted, original_title=original_title)
    output = render(doc)
    assert "<!DOCTYPE html>" in output
    assert len(output) > 1000


# ---------------------------------------------------------------------------
# Synthetic <h1> brand-strip tests (A, B, C)
#
# These test the planned behaviour: when extract_with_trafilatura injects a
# synthetic <h1>, it should brand-strip the page title by splitting on the
# last occurrence of ' | ', ' - ', or ' -- ' and keeping the left side.
#
# Test A and C currently FAIL (correct: they describe unimplemented behaviour).
# Test B currently PASSES and must continue to pass after the change.
# ---------------------------------------------------------------------------


def _html_with_title(title: str) -> str:
    """Minimal page with the given <title>. Body is irrelevant; trafilatura is mocked."""
    return (
        f"<html><head><title>{title}</title></head>"
        "<body><p>Body content for testing.</p></body></html>"
    )


def test_h2_no_h1_injects_brand_stripped_h1(monkeypatch):
    """(A) Extracted HTML has h2 but no h1 -> inject synthetic <h1> with brand-stripped title.

    Currently FAILS: has_h1_h3 is True when h2 is present, so the current code
    returns the cleaned extraction without injecting anything.
    Will PASS after the 'any heading h1-h6 AND lacks h1' check is implemented.
    """
    extracted_html = "<h2>Section</h2><p>Body</p>"
    monkeypatch.setattr(_trafilatura, "extract", lambda *a, **kw: extracted_html)

    html = _html_with_title("Title - Site")
    result = extract_with_trafilatura(html)

    assert result.startswith("<h1>Title</h1>\n"), (
        f"Expected brand-stripped synthetic <h1>, got: {result[:80]!r}"
    )
    assert "<h2>Section</h2><p>Body</p>" in result


def test_h1_present_no_synthetic_injection(monkeypatch):
    """(B) Extracted HTML already has <h1> -> return as-is, no second heading injected.

    Currently PASSES and must continue to pass after the change.
    """
    extracted_html = "<h1>Real</h1><p>Body</p>"
    monkeypatch.setattr(_trafilatura, "extract", lambda *a, **kw: extracted_html)

    html = _html_with_title("Real - Site")
    result = extract_with_trafilatura(html)

    assert result.startswith("<h1>Real</h1>"), (
        f"Expected original <h1>, got: {result[:80]!r}"
    )
    assert result.count("<h1>") == 1


@pytest.mark.parametrize("raw_title,expected_clean", [
    ("Photosynthesis - Wikipedia", "Photosynthesis"),
    ("What is dyslexia? | Yale Dyslexia", "What is dyslexia?"),
    ("A -- B", "A"),
])
def test_brand_strip_on_synthetic_h1(monkeypatch, raw_title, expected_clean):
    """(C) Brand-strip splits on last ' | ', ' - ', or ' -- ' and keeps the left side.

    Uses the h2+no-h1 scenario. Currently FAILS on all three cases (no injection,
    no stripping). Will PASS after the parser change.
    """
    extracted_html = "<h2>Section</h2><p>Body content here.</p>"
    monkeypatch.setattr(_trafilatura, "extract", lambda *a, **kw: extracted_html)

    html = _html_with_title(raw_title)
    result = extract_with_trafilatura(html)

    expected_h1 = f"<h1>{expected_clean}</h1>\n"
    assert result.startswith(expected_h1), (
        f"title={raw_title!r}: expected {expected_h1!r}, got {result[:80]!r}"
    )
