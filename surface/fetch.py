"""
URL fetching with SSRF protection.

Validates URLs, resolves DNS, checks against blocked IP ranges,
and fetches HTML content with size limits.
"""
import ipaddress
import socket
from urllib.parse import urlparse

import requests

import config


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class FetchError(Exception):
    """Base class for fetch errors."""
    error_type = "fetch_error"

    @property
    def user_message(self) -> str:
        return str(self)


class InvalidURLError(FetchError):
    """Bad format, scheme, or length."""
    error_type = "invalid_url"

    @property
    def user_message(self) -> str:
        return "That doesn't look like a valid URL. Check the address and try again."


class SSRFBlockedError(FetchError):
    """Private or reserved IP detected."""
    error_type = "ssrf_blocked"

    @property
    def user_message(self) -> str:
        return "That URL points to a private or reserved address and can't be fetched."


class FetchTimeoutError(FetchError):
    """Request timed out."""
    error_type = "fetch_timeout"

    @property
    def user_message(self) -> str:
        return "The page took too long to respond. Try again in a moment."


class ContentTypeError(FetchError):
    """Response is not text/html."""
    error_type = "content_type"

    @property
    def user_message(self) -> str:
        return "That URL doesn't serve an HTML page. Decant only works with web pages."


class ResponseTooLargeError(FetchError):
    """Response exceeds size limit."""
    error_type = "response_too_large"

    @property
    def user_message(self) -> str:
        return "That page is too large to process. Decant handles pages up to 10 MB."


class FetchConnectionError(FetchError):
    """DNS failure, connection refused, etc."""
    error_type = "fetch_connection"

    @property
    def user_message(self) -> str:
        return "Couldn't connect to that site. Check the URL and try again."


class BotProtectionError(FetchError):
    """Response appears to be a bot-protection challenge page."""
    error_type = "bot_protection"

    @property
    def user_message(self) -> str:
        return (
            "This site blocked our request. Try saving the page as HTML "
            "in your browser (File > Save As > HTML) and uploading the "
            "file instead."
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BOT_PROTECTION_SIGNATURES = [
    "Checking if the site connection is secure",
    "cf-browser-verification",
    "challenge-platform",
    "Just a moment...",
    "Attention Required",
]


def _check_bot_protection(html: str) -> None:
    """Raise BotProtectionError if HTML looks like a challenge page."""
    for sig in _BOT_PROTECTION_SIGNATURES:
        if sig in html:
            raise BotProtectionError(f"Bot protection detected: {sig!r}")
    # "Access denied" combined with "Cloudflare"
    if "Access denied" in html and "Cloudflare" in html:
        raise BotProtectionError("Bot protection detected: Access denied + Cloudflare")


def _is_blocked_ip(ip_str: str) -> bool:
    """Check if an IP address falls within any blocked range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable -> block
    return any(addr in network for network in config.BLOCKED_IP_RANGES)


def _resolve_and_check(hostname: str) -> None:
    """Resolve hostname and check all IPs against blocked ranges."""
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise FetchConnectionError(f"DNS resolution failed for {hostname}")

    if not results:
        raise FetchConnectionError(f"No DNS results for {hostname}")

    for family, _type, _proto, _canonname, sockaddr in results:
        ip = sockaddr[0]
        if _is_blocked_ip(ip):
            raise SSRFBlockedError(f"Blocked IP {ip} for {hostname}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_url(url: str) -> str:
    """
    Fetch HTML from a URL with SSRF protection and size limits.

    Args:
        url: The URL to fetch.

    Returns:
        The HTML content as a string.

    Raises:
        InvalidURLError: Bad URL format, scheme, or length.
        SSRFBlockedError: URL resolves to a private/reserved IP.
        FetchTimeoutError: Request timed out.
        ContentTypeError: Response is not text/html.
        ResponseTooLargeError: Response exceeds MAX_RESPONSE_SIZE.
        FetchConnectionError: DNS or connection failure.
    """
    # 1. Validate length
    if len(url) > config.MAX_URL_LENGTH:
        raise InvalidURLError(f"URL exceeds {config.MAX_URL_LENGTH} characters")

    # 2. Parse and validate scheme
    parsed = urlparse(url)
    if parsed.scheme not in config.ALLOWED_SCHEMES:
        raise InvalidURLError(f"Scheme '{parsed.scheme}' not allowed")
    if not parsed.hostname:
        raise InvalidURLError("No hostname in URL")

    # 3-4. Resolve DNS and check IP
    _resolve_and_check(parsed.hostname)

    # 5. Fetch with streaming
    try:
        response = requests.get(
            url,
            timeout=config.REQUEST_TIMEOUT,
            stream=True,
            headers={"User-Agent": "Decant/1.0 (+https://decant.cc)"},
            allow_redirects=True,
        )
    except requests.exceptions.Timeout:
        raise FetchTimeoutError(f"Timeout fetching {url}")
    except requests.exceptions.ConnectionError:
        raise FetchConnectionError(f"Connection failed for {url}")
    except requests.exceptions.RequestException as e:
        raise FetchConnectionError(f"Request failed: {e}")

    # Post-redirect SSRF check: verify final URL's IP
    final_url = response.url
    final_parsed = urlparse(final_url)
    if final_parsed.hostname and final_parsed.hostname != parsed.hostname:
        _resolve_and_check(final_parsed.hostname)

    # 6. Check content type
    content_type = response.headers.get("Content-Type", "")
    if not any(content_type.startswith(ct) for ct in config.ALLOWED_CONTENT_TYPES):
        raise ContentTypeError(f"Content-Type '{content_type}' is not HTML")

    # 7. Check Content-Length header if present
    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            if int(content_length) > config.MAX_RESPONSE_SIZE:
                raise ResponseTooLargeError(
                    f"Content-Length {content_length} exceeds limit"
                )
        except ValueError:
            pass  # malformed header, proceed to streaming check

    # 8. Read body with size limit
    chunks = []
    total_size = 0
    for chunk in response.iter_content(chunk_size=65536):
        total_size += len(chunk)
        if total_size > config.MAX_RESPONSE_SIZE:
            response.close()
            raise ResponseTooLargeError(
                f"Response body exceeds {config.MAX_RESPONSE_SIZE} bytes"
            )
        chunks.append(chunk)

    # 9. Decode
    body = b"".join(chunks)
    encoding = response.encoding or "utf-8"
    html = body.decode(encoding, errors="replace")

    # 10. Check for bot protection / challenge pages
    _check_bot_protection(html)

    return html
