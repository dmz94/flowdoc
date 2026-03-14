"""
Main content selection from sanitized DOM.

Implements deterministic content selection: main -> article -> body.
Also provides mode detection for routing between transform and extract pipelines.
See decisions.md section 4 for selection rules.
"""
from bs4 import BeautifulSoup, Tag


def detect_mode(html: str) -> str:
    """
    Detect whether input HTML needs extraction (boilerplate removal) or
    can go straight to transform (fidelity-first parsing).

    Routing rules (in order):
    1. Force extract if scripts >= 10
    2. Force extract if nav/aside/footer/header elements >= 5
    3. Default to transform

    These thresholds were derived from analysis of the fixture corpus.
    simple_article.html (clean developer HTML) scores: scripts=0, nav=0
    Real-world pages (Wikipedia, NHS, BBC etc) score well above thresholds.

    Args:
        html: Raw HTML string

        Returns:
        "transform" or "extract"
    """
    soup = BeautifulSoup(html, "lxml")

    scripts = len(soup.find_all(["script", "iframe"]))
    nav_elements = len(soup.find_all(["nav", "aside", "footer", "header"]))

    if scripts >= 10:
        return "extract"

    if nav_elements >= 5:
        return "extract"

    return "transform"


def select_main_content(soup: BeautifulSoup) -> Tag:
    """
    Select main content area from DOM tree.

    Selection order (deterministic):
    1. First <main> element
    2. First <article> element
    3. <body> element

    Navigation, headers, footers, and sidebars are excluded by selection.

    Args:
        soup: BeautifulSoup parsed DOM tree

    Returns:
        Tag object representing the main content subtree

    Raises:
        ValueError: If no body element exists (malformed HTML)
    """
    main = soup.find("main")
    if main:
        return main

    article = soup.find("article")
    if article:
        return article

    body = soup.find("body")
    if body:
        return body

    raise ValueError("No body element found in HTML")
