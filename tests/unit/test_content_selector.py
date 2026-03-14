"""
Tests for main content selection and mode detection.

Validates deterministic selection order: main -> article -> body.
Also validates auto mode detection routing logic.
"""
import pytest
from bs4 import BeautifulSoup
from decant.core.content_selector import select_main_content, detect_mode


def test_selects_main_when_present():
    """Returns <main> when it exists."""
    html = "<body><nav>Skip</nav><main>Content</main></body>"
    soup = BeautifulSoup(html, "lxml")
    result = select_main_content(soup)
    assert result.name == "main"
    assert "Content" in result.get_text()


def test_selects_article_when_no_main():
    """Falls back to <article> when no <main>."""
    html = "<body><nav>Skip</nav><article>Content</article></body>"
    soup = BeautifulSoup(html, "lxml")
    result = select_main_content(soup)
    assert result.name == "article"


def test_selects_body_when_no_main_or_article():
    """Falls back to <body> when neither <main> nor <article> exist."""
    html = "<body><p>Just body content</p></body>"
    soup = BeautifulSoup(html, "lxml")
    result = select_main_content(soup)
    assert result.name == "body"


def test_prefers_main_over_article():
    """Prefers <main> when both <main> and <article> exist."""
    html = "<body><article>Article</article><main>Main</main></body>"
    soup = BeautifulSoup(html, "lxml")
    result = select_main_content(soup)
    assert result.name == "main"
    assert "Main" in result.get_text()


# Note: We don't test the "no body" error case because HTML parsers (lxml)
# automatically add <body> tags during parsing, making this scenario impossible
# to trigger in practice. The ValueError in content_selector.py remains as
# defensive coding.


def test_detect_mode_returns_transform_for_clean_html():
    """Clean semantic HTML with no scripts or nav returns transform."""
    html = "<html><body><main><h1>Title</h1><p>Content</p></main></body></html>"
    assert detect_mode(html) == "transform"


def test_detect_mode_returns_extract_for_high_script_count():
    """HTML with 10 or more scripts returns extract."""
    scripts = "".join("<script>var x=1;</script>" for _ in range(10))
    html = f"<html><body>{scripts}<h1>Title</h1><p>Content</p></body></html>"
    assert detect_mode(html) == "extract"


def test_detect_mode_returns_extract_for_high_nav_count():
    """HTML with 5 or more nav/aside/footer/header elements returns extract."""
    nav_elements = (
        "<nav>Nav</nav>"
        "<nav>Nav</nav>"
        "<aside>Aside</aside>"
        "<footer>Footer</footer>"
        "<header>Header</header>"
    )
    html = f"<html><body>{nav_elements}<h1>Title</h1><p>Content</p></body></html>"
    assert detect_mode(html) == "extract"


def test_detect_mode_defaults_to_transform_when_ambiguous():
    """Ambiguous input (below both thresholds) defaults to transform."""
    html = (
        "<html><body>"
        "<nav>Nav</nav>"
        "<script>var x=1;</script>"
        "<h1>Title</h1><p>Content</p>"
        "</body></html>"
    )
    assert detect_mode(html) == "transform"


def test_detect_mode_simple_article_is_transform():
    """simple_article.html fixture is detected as transform mode."""
    from pathlib import Path
    fixture_path = Path(__file__).resolve().parent / "test-data" / "simple_article.html"
    html = fixture_path.read_text(encoding='utf-8')
    assert detect_mode(html) == "transform"


def test_detect_mode_wikipedia_is_extract():
    """Wikipedia fixture is detected as extract mode."""
    from pathlib import Path
    fixture_path = Path(__file__).resolve().parent / "test-data" / "wikipedia_dyslexia.html"
    html = fixture_path.read_text(encoding='utf-8')
    assert detect_mode(html) == "extract"
