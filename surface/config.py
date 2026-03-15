"""
Configuration constants for the Decant hosted surface.
"""
import ipaddress
import os

# Airtable integration (feedback logging)
AIRTABLE_API_TOKEN = os.environ.get("AIRTABLE_API_TOKEN", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE_NAME = "Feedback"

# Login credentials (development defaults — override via env vars in production)
BASIC_AUTH_ENABLED = True
BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME", "decant")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD", "preview")

# Flask session
FLASK_SECRET_KEY = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-insecure-change-me-a7f3b9c1e2d4",
)

# URL fetching
REQUEST_TIMEOUT = 20  # seconds
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_URL_LENGTH = 2048

# SSRF protection: block all private/reserved IP ranges
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
]

ALLOWED_SCHEMES = ("http", "https")
ALLOWED_CONTENT_TYPES = ("text/html",)

# Rate limiting
RATE_LIMIT_MAX_REQUESTS = 60  # per IP per window
RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour
MAX_CONCURRENT_FETCHES = 10
MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
