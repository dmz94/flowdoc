"""
Flask application for the Decant hosted surface.

Routes:
    GET  /healthz — Health check (no auth).
    GET  /        — Serve the index page.
    POST /convert — Accept URL or file, return converted HTML as JSON.
"""
import logging
import os
import time
from functools import wraps

from flask import Flask, request, jsonify, render_template

import config
from convert import convert_url, convert_file, ConvertError
from fetch import FetchError
from rate_limit import (
    check_rate_limit, acquire_fetch_slot, release_fetch_slot, RateLimitError,
)

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("decant")


# ---------------------------------------------------------------------------
# HTTP Basic Auth
# ---------------------------------------------------------------------------

def _check_auth(username: str, password: str) -> bool:
    return (
        username == config.BASIC_AUTH_USERNAME
        and password == config.BASIC_AUTH_PASSWORD
    )


def _auth_required_response():
    return (
        jsonify({"status": "error", "message": "Authentication required."}),
        401,
        {"WWW-Authenticate": 'Basic realm="Decant"'},
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not config.BASIC_AUTH_ENABLED:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or not _check_auth(auth.username, auth.password):
            return _auth_required_response()
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_client_ip(req) -> str:
    """Get client IP, checking X-Forwarded-For first for proxy setups."""
    forwarded = req.headers.get("X-Forwarded-For", "")
    if forwarded:
        # Take the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()
    return req.remote_addr or "unknown"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/healthz")
def healthz():
    return "ok", 200


@app.route("/")
@requires_auth
def index():
    prefilled_url = request.args.get("url", "")
    return render_template("index.html", prefilled_url=prefilled_url)


@app.route("/convert", methods=["POST"])
@requires_auth
def convert():
    start = time.monotonic()
    source = None

    try:
        # Rate limit check
        client_ip = get_client_ip(request)
        if not check_rate_limit(client_ip):
            raise RateLimitError()

        # File upload takes precedence
        uploaded = request.files.get("file")
        if uploaded and uploaded.filename:
            # Validate file extension
            filename = uploaded.filename.lower()
            if not filename.endswith((".html", ".htm")):
                return jsonify({
                    "status": "error",
                    "message": "Please upload an HTML file (.html or .htm).",
                }), 422

            # Validate file size
            html_bytes = uploaded.read()
            if len(html_bytes) > config.MAX_FILE_UPLOAD_SIZE:
                return jsonify({
                    "status": "error",
                    "message": "That file is too large to convert.",
                }), 422

            source = "file_upload"
            converted_html, source_url = convert_file(html_bytes)
        else:
            url = request.form.get("url", "").strip()
            if not url:
                return jsonify({
                    "status": "error",
                    "message": "Please provide a URL or upload a file.",
                }), 422

            # Acquire fetch slot
            if not acquire_fetch_slot():
                return jsonify({
                    "status": "error",
                    "message": "The service is busy. Please try again in a moment.",
                }), 503

            try:
                source = url
                converted_html, source_url = convert_url(url)
            finally:
                release_fetch_slot()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.info("convert OK source=%s elapsed=%dms", source, elapsed_ms)

        return jsonify({
            "status": "ok",
            "html": converted_html,
        })

    except RateLimitError as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.warning(
            "convert RATE_LIMITED ip=%s elapsed=%dms",
            get_client_ip(request), elapsed_ms,
        )
        return jsonify({
            "status": "error",
            "message": e.user_message,
        }), 429

    except FetchError as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.warning(
            "convert FETCH_ERROR source=%s error=%s elapsed=%dms",
            source, e, elapsed_ms,
        )
        return jsonify({
            "status": "error",
            "message": e.user_message,
        }), 422

    except ConvertError as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.warning(
            "convert CONVERT_ERROR source=%s error=%s elapsed=%dms",
            source, e, elapsed_ms,
        )
        return jsonify({
            "status": "error",
            "message": e.user_message,
        }), 422

    except Exception:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.exception(
            "convert UNEXPECTED_ERROR source=%s elapsed=%dms",
            source, elapsed_ms,
        )
        return jsonify({
            "status": "error",
            "message": "Something went wrong on our end. Try again in a moment.",
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
