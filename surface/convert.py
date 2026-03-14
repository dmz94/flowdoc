"""
Pipeline wrapper for the Decant surface.

Connects URL fetching and file upload to the decant engine pipeline.
"""
from bs4 import BeautifulSoup

from decant.core.content_selector import detect_mode
from decant.core.parser import (
    parse, extract_with_trafilatura, ValidationError, harvest_captions,
)
from decant.core.renderer import render

from fetch import fetch_url


class ConvertError(Exception):
    """Engine-level conversion failure."""

    def __init__(self, message: str, user_message: str | None = None):
        super().__init__(message)
        self._user_message = user_message or message

    @property
    def user_message(self) -> str:
        return self._user_message


def _run_engine(raw_html: str, source_url: str = "") -> str:
    """
    Run the decant engine pipeline on raw HTML.

    Matches the logic in cli/main.py.

    Args:
        raw_html: The HTML to convert.
        source_url: Optional source URL for placeholder links.

    Returns:
        Converted HTML string.

    Raises:
        ConvertError: On engine failure.
    """
    try:
        mode = detect_mode(raw_html)

        if mode == "extract":
            original_soup = BeautifulSoup(raw_html, "lxml")
            original_title = original_soup.find("title")
            caption_map = harvest_captions(raw_html)
            html_to_parse = extract_with_trafilatura(raw_html)
        else:
            original_title = None
            caption_map = None
            html_to_parse = raw_html

        doc = parse(
            html_to_parse,
            original_title=original_title,
            require_article_body=(mode == "extract"),
            caption_map=caption_map,
            source_url=source_url,
        )
        return render(doc, use_opendyslexic=True)

    except (ValidationError, ValueError):
        raise ConvertError(
            "Validation failed",
            user_message=(
                "Couldn't find an article on this page. "
                "Decant works best with articles and blog posts."
            ),
        )
    except ConvertError:
        raise
    except Exception as e:
        raise ConvertError(
            str(e),
            user_message="Something went wrong during conversion. Try again in a moment.",
        )


def convert_url(url: str) -> tuple[str, str]:
    """
    Fetch a URL and convert its HTML.

    Args:
        url: The URL to fetch and convert.

    Returns:
        Tuple of (converted_html, source_url).
    """
    raw_html = fetch_url(url)
    output = _run_engine(raw_html, source_url=url)
    return output, url


def convert_file(html_bytes: bytes) -> tuple[str, str]:
    """
    Convert uploaded HTML file bytes.

    Args:
        html_bytes: Raw bytes of the uploaded file.

    Returns:
        Tuple of (converted_html, "").
    """
    raw_html = html_bytes.decode("utf-8", errors="replace")
    output = _run_engine(raw_html)
    return output, ""
