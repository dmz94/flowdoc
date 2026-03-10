"""
HTML sanitization using nh3 library.

Security boundary: strips active content, dangerous attributes, and unsafe URLs
before DOM parsing. See decisions.md section 9 for allowlist specification.
"""
import nh3


# Allowed HTML tags (from decisions.md section 9)
ALLOWED_TAGS = {
    # Structure
    "html", "head", "title", "body", "main", "article",
    # Headings
    "h1", "h2", "h3", "h4", "h5", "h6",
    # Block elements
    "p", "ul", "ol", "li", "blockquote", "pre", "code",
    # Inline elements
    "em", "i", "strong", "b", "a", "br",
    # Elements for degradation (kept so parser can create placeholders)
    "table", "tr", "td", "th", "img", "figure", "figcaption",
    "dl", "dt", "dd", "hr", "form", "input", "textarea", "select", "option", "button",
    "graphic",
}

# Allowed attributes per tag
ALLOWED_ATTRIBUTES = {
    "a": {"href"},
    "img": {"alt", "src"},
    "graphic": {"alt", "src"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}

# Allowed URL schemes (blocks javascript:, data:, etc.)
ALLOWED_URL_SCHEMES = {"http", "https"}


def sanitize(html: str) -> str:
    """
    Sanitize HTML using nh3 allowlist.
    
    Removes scripts, event handlers, dangerous attributes, and unsafe URLs.
    Keeps only tags/attributes needed for parsing and degradation.
    
    Args:
        html: Raw HTML string (untrusted input)
        
    Returns:
        Sanitized HTML string safe for parsing
    """
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        strip_comments=True,
    )