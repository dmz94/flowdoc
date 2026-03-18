"""
Flask application for the Decant hosted surface.

Routes:
    GET  /healthz   — Health check (no auth).
    POST /feedback  — Log user feedback as JSON (no auth).
    GET  /login     — Login form.
    POST /login     — Authenticate and set session.
    GET  /          — Serve the index page (session required).
    POST /convert   — Accept URL or file, return converted HTML as JSON.
"""
import json
import logging
import os
import time
from datetime import timedelta

import requests as http_requests
from flask import (
    Flask, request, jsonify, render_template, make_response,
    session, redirect, url_for,
)

import config
from convert import convert_url, convert_file, ConvertError
from fetch import FetchError
from rate_limit import (
    check_rate_limit, acquire_fetch_slot, release_fetch_slot, RateLimitError,
)

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.permanent_session_lifetime = timedelta(days=30)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("decant")


# ---------------------------------------------------------------------------
# Login / Session Auth
# ---------------------------------------------------------------------------

_LOGIN_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decant — Log in</title>
<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32.png">
<style>
body {{
  font-family: system-ui, -apple-system, sans-serif;
  background: #fafaf7;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
}}
.card {{
  max-width: 360px;
  width: 100%;
  padding: 2rem;
}}
.logo {{
  height: 36px;
  width: auto;
  margin-bottom: 1.5rem;
}}
p {{
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 1.25rem;
}}
.error {{
  color: #cc3333;
  font-size: 13px;
  margin: 0 0 1rem;
}}
form {{
  text-align: left;
}}
label {{
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin: 0 0 4px;
}}
input[type="text"],
input[type="password"] {{
  width: 100%;
  padding: 0.6rem 0.75rem;
  font-size: 15px;
  border: 1px solid rgba(0,0,0,0.25);
  border-radius: 4px;
  margin-bottom: 0.75rem;
  box-sizing: border-box;
  background: #fff;
}}
input:focus {{
  outline: none;
  border-color: rgb(91,91,102);
}}
button {{
  width: 100%;
  padding: 0.7rem;
  font-size: 15px;
  font-weight: 500;
  background: rgb(91,91,102);
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.25rem;
}}
button:hover {{
  opacity: 0.85;
}}
.contact {{
  margin-top: 1.5rem;
  font-size: 13px;
  text-align: center;
}}
a {{ color: #1856a8; }}
</style>
</head>
<body>
<div class="card">
  <svg class="logo" viewBox="0 0 68 17" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(-95.779913,-118.25255)">
      <g transform="matrix(0.25568162,0,0,0.25568162,73.405452,90.167546)">
        <path fill="#555" opacity="0.99" d="m 111.79603,118.25255 q 7.83168,0 13.68779,3.03389 5.92667,2.96334 9.10167,8.60779 3.24556,5.57389 3.24556,13.05278 0,7.4789 -3.24556,12.98223 -3.175,5.50334 -9.10167,8.46668 -5.85611,2.89278 -13.68779,2.89278 H 95.779913 v -49.03615 z m 0,42.47448 q 8.60779,0 13.1939,-4.65667 4.58612,-4.65667 4.58612,-13.12335 0,-8.53722 -4.58612,-13.33501 -4.58611,-4.79778 -13.1939,-4.79778 h -7.97278 v 35.91281 z"/>
        <path fill="#555" opacity="0.99" d="m 181.64605,146.89813 q 0,2.18722 -0.28222,3.95111 h -29.70391 q 0.35278,4.65667 3.45723,7.47889 3.10444,2.82223 7.62,2.82223 6.49112,0 9.17223,-5.43278 h 8.67834 q -1.76389,5.36222 -6.42056,8.81945 -4.58611,3.38667 -11.43001,3.38667 -5.57389,0 -10.01889,-2.46945 -4.37445,-2.54 -6.91445,-7.05556 -2.46945,-4.58611 -2.46945,-10.58334 0,-5.99723 2.39889,-10.51278 2.46945,-4.58612 6.8439,-7.05557 4.445,-2.46944 10.16,-2.46944 5.50334,0 9.80723,2.39889 4.30389,2.39889 6.70278,6.77334 2.39889,4.30389 2.39889,9.94834 z m -8.39611,-2.54 q -0.0706,-4.44501 -3.17501,-7.12612 -3.10444,-2.68111 -7.69056,-2.68111 -4.16278,0 -7.12611,2.68111 -2.96334,2.61056 -3.52778,7.12612 z"/>
        <path fill="#555" opacity="0.99" d="m 187.07888,147.81535 q 0,-5.99723 2.39889,-10.51278 2.46945,-4.58612 6.77334,-7.05557 4.30389,-2.46944 9.87778,-2.46944 7.05556,0 11.64168,3.38667 4.65667,3.31611 6.27945,9.525 h -8.67834 q -1.05834,-2.89278 -3.38667,-4.51555 -2.32834,-1.62278 -5.85612,-1.62278 -4.93889,0 -7.90223,3.52778 -2.89278,3.45722 -2.89278,9.73667 0,6.27945 2.89278,9.80723 2.96334,3.52778 7.90223,3.52778 6.98501,0 9.24279,-6.13834 h 8.67834 q -1.69334,5.92667 -6.35001,9.45445 -4.65667,3.45723 -11.57112,3.45723 -5.57389,0 -9.87778,-2.46945 -4.30389,-2.54 -6.77334,-7.05556 -2.39889,-4.58611 -2.39889,-10.58334 z"/>
        <path fill="#555" opacity="0.99" d="m 229.62393,147.67424 q 0,-5.85612 2.39889,-10.37167 2.46945,-4.51556 6.63223,-6.98501 4.23333,-2.54 9.31334,-2.54 4.58611,0 7.97278,1.83444 3.45723,1.76389 5.50334,4.44501 v -5.64445 h 8.11389 v 38.87614 h -8.11389 v -5.78556 q -2.04611,2.75167 -5.57389,4.58611 -3.52778,1.83445 -8.04334,1.83445 -5.00945,0 -9.17223,-2.54 -4.16278,-2.61056 -6.63223,-7.19668 -2.39889,-4.65667 -2.39889,-10.51278 z m 31.82058,0.14111 q 0,-4.02167 -1.69334,-6.985 -1.62278,-2.96334 -4.30389,-4.51556 -2.68111,-1.55223 -5.78556,-1.55223 -3.10444,0 -5.78556,1.55223 -2.68111,1.48166 -4.37444,4.445 -1.62278,2.89278 -1.62278,6.91445 0,4.02167 1.62278,7.05556 1.69333,3.03389 4.37444,4.65667 2.75167,1.55222 5.78556,1.55222 3.10445,0 5.78556,-1.55222 2.68111,-1.55222 4.30389,-4.51556 1.69334,-3.03389 1.69334,-7.05556 z"/>
        <path fill="#555" opacity="0.99" d="m 299.96783,127.77756 q 4.58611,0 8.18445,1.905 3.66889,1.905 5.715,5.64445 2.04611,3.73945 2.04611,9.03112 v 22.93057 h -7.97278 v -21.73113 q 0,-5.22111 -2.61056,-7.97278 -2.61056,-2.82223 -7.12611,-2.82223 -4.51556,0 -7.19668,2.82223 -2.61055,2.75167 -2.61055,7.97278 v 21.73113 h -8.04334 v -38.87614 h 8.04334 v 4.445 q 1.97555,-2.39889 5.00945,-3.73944 3.10444,-1.34056 6.56167,-1.34056 z"/>
        <path fill="#555" opacity="0.99" d="m 335.73954,134.97423 v 21.51946 q 0,2.18722 0.98778,3.175 1.05833,0.91722 3.52778,0.91722 h 4.93889 v 6.70279 h -6.35001 q -5.43278,0 -8.32556,-2.54001 -2.89278,-2.54 -2.89278,-8.255 v -21.51946 h -4.58611 v -6.56167 h 4.58611 v -9.66612 h 8.1139 v 9.66612 h 9.45445 v 6.56167 z"/>
        <path fill="#b01030" opacity="0.99" d="m 103.82312,144.69298 v 16.03416 h 7.97316 c 5.73852,0 10.1361,-1.55212 13.19351,-4.65656 2.73447,-2.77654 4.24629,-6.56931 4.53512,-11.3776 -12.23324,4.09727 -19.62597,2.78456 -25.70179,0 z"/>
      </g>
    </g>
  </svg>
  <p>Decant is in early testing. If you have been invited, check your invite message for the username and password.</p>
  {error}
  <form method="post">
    <label for="username">Username</label>
    <input type="text" id="username" name="username" autocomplete="username" required value="{username}">
    <label for="password">Password</label>
    <input type="password" id="password" name="password" autocomplete="current-password" required>
    <button type="submit">Log in</button>
  </form>
  <p class="contact">If you need help, contact <a href="mailto:feedback@decant.cc">feedback@decant.cc</a></p>
</div>
</body>
</html>
"""


@app.before_request
def _require_login():
    if not config.BASIC_AUTH_ENABLED:
        return None
    # Routes that don't require auth
    open_paths = ("/login", "/healthz", "/static/")
    path = request.path
    if any(path == p or path.startswith(p) for p in open_paths):
        return None
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    error_html = ""
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if (username == config.BASIC_AUTH_USERNAME
                and password == config.BASIC_AUTH_PASSWORD):
            session.permanent = True
            session["logged_in"] = True
            return redirect(url_for("index"))
        error_html = '<p class="error">Incorrect username or password.</p>'
    return make_response(_LOGIN_PAGE_HTML.format(error=error_html, username=username))


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


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON."}), 400

    rating = data.get("rating", "")
    source = data.get("source", "")
    interaction_id = data.get("interaction_id", "")

    if rating not in ("up", "down", "broken", "error_report"):
        return jsonify({"status": "error", "message": "Rating must be 'up', 'down', or 'broken'."}), 400
    if not source:
        return jsonify({"status": "error", "message": "Source is required."}), 400
    if not interaction_id:
        return jsonify({"status": "error", "message": "Interaction ID is required."}), 400

    payload = {
        "event": "feedback",
        "interaction_id": interaction_id,
        "source": source,
        "source_domain": data.get("source_domain", ""),
        "rating": rating,
        "text": data.get("text", ""),
        "viewport": data.get("viewport", ""),
        "theme": data.get("theme", ""),
        "timestamp": data.get("timestamp", ""),
    }
    print(json.dumps(payload), flush=True)

    if config.AIRTABLE_API_TOKEN and config.AIRTABLE_BASE_ID:
        client_ip = get_client_ip(request)
        now = data.get("updated_at", data.get("timestamp", ""))
        fields = {
            "interaction_id": interaction_id,
            "timestamp": payload["timestamp"],
            "source": payload["source"],
            "source_domain": payload["source_domain"],
            "rating": payload["rating"],
            "text": payload["text"],
            "viewport": payload["viewport"],
            "theme": payload["theme"],
            "attempted_url": data.get("attempted_url", ""),
            "error_type": data.get("error_type", ""),
            "ip": client_ip,
            "updated_at": now,
        }
        # Only set created_at on first submission
        created_at = data.get("created_at", "")
        if created_at:
            fields["created_at"] = created_at

        try:
            http_requests.patch(
                "https://api.airtable.com/v0/{}/{}".format(
                    config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME,
                ),
                headers={
                    "Authorization": "Bearer {}".format(config.AIRTABLE_API_TOKEN),
                    "Content-Type": "application/json",
                },
                json={
                    "performUpsert": {
                        "fieldsToMergeOn": ["interaction_id"]
                    },
                    "records": [{
                        "fields": fields
                    }]
                },
                timeout=5,
            )
            log.info("Feedback upserted to Airtable")
        except Exception as e:
            log.warning("Airtable upsert failed: %s", str(e))

    return jsonify({"status": "ok"})


@app.route("/test-page")
def test_page():
    path = os.path.join(app.static_folder, "demo", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("<head>", '<head>\n<base href="/static/demo/">', 1)
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


@app.route("/")
def index():
    prefilled_url = request.args.get("url", "")
    return render_template("index.html", prefilled_url=prefilled_url)


@app.route("/what-works")
def what_works():
    return render_template("what-works.html")


@app.route("/convert", methods=["POST"])
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
                    "error_type": "invalid_file_type",
                }), 422

            # Validate file size
            html_bytes = uploaded.read()
            if len(html_bytes) > config.MAX_FILE_UPLOAD_SIZE:
                return jsonify({
                    "status": "error",
                    "message": "That file is too large to convert.",
                    "error_type": "file_too_large",
                }), 422

            source = "file_upload"
            converted_html, source_url = convert_file(html_bytes)
        else:
            url = request.form.get("url", "").strip()
            if not url:
                return jsonify({
                    "status": "error",
                    "message": "Please provide a URL or upload a file.",
                    "error_type": "missing_input",
                }), 422

            # Self-URL detection: read from disk instead of fetching
            _self_url_hit = False

            # Vanity routes that map to static files
            _VANITY_ROUTES = {
                "/test-page": "demo/index.html",
            }
            for _origin in ("https://decant.cc", "https://www.decant.cc"):
                for _vanity, _static_rel in _VANITY_ROUTES.items():
                    if url.rstrip("/") == _origin + _vanity:
                        local_path = os.path.realpath(
                            os.path.join(app.static_folder, *_static_rel.split("/"))
                        )
                        if local_path.startswith(os.path.realpath(app.static_folder) + os.sep) \
                                and os.path.isfile(local_path):
                            with open(local_path, "rb") as f:
                                html_bytes = f.read()
                            source = url
                            converted_html, source_url = convert_file(html_bytes)
                            _self_url_hit = True
                        break
                if _self_url_hit:
                    break

            # Static file URLs (e.g. /static/demo/index.html)
            if not _self_url_hit:
                for _prefix in ("https://decant.cc/static/", "https://www.decant.cc/static/"):
                    if url.startswith(_prefix):
                        rel_path = url[len(_prefix):]
                        local_path = os.path.realpath(
                            os.path.join(app.static_folder, *rel_path.split("/"))
                        )
                        # Guard against path traversal
                        if local_path.startswith(os.path.realpath(app.static_folder) + os.sep) \
                                and os.path.isfile(local_path):
                            with open(local_path, "rb") as f:
                                html_bytes = f.read()
                            source = url
                            converted_html, source_url = convert_file(html_bytes)
                            _self_url_hit = True
                        break

            if not _self_url_hit:
                # Acquire fetch slot
                if not acquire_fetch_slot():
                    return jsonify({
                        "status": "error",
                        "message": "The service is busy. Please try again in a moment.",
                        "error_type": "service_busy",
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
            "error_type": e.error_type,
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
            "error_type": getattr(e, "error_type", "fetch_error"),
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
            "error_type": e.error_type,
            "hint": "See what kinds of pages work well.",
            "hint_url": "/what-works",
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
            "error_type": "server_error",
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
