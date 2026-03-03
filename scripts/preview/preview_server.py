"""
Flowdoc drag-drop preview server (dev tool only).

Runs the Flowdoc pipeline on uploaded HTML files and returns
converted output for visual inspection in a browser.

Usage (from project root):
    python scripts/preview/preview_server.py
Then open http://localhost:5000 in a browser.
"""
from flask import Flask, request
import os
from bs4 import BeautifulSoup

from flowdoc.core.content_selector import detect_mode
from flowdoc.core.parser import parse, extract_with_trafilatura
from flowdoc.core.renderer import render

app = Flask(__name__)

PREVIEW_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview.html")


@app.route("/")
def index():
    """Serve the drag-drop preview page."""
    with open(PREVIEW_HTML, "r", encoding="utf-8") as f:
        return f.read()


@app.route("/convert", methods=["POST"])
def convert():
    """
    Accept uploaded HTML, run Flowdoc pipeline, return converted HTML.

    Form fields:
        file - HTML file to convert (required)
        font - optional; pass 'opendyslexic' to enable font toggle
        mode - optional; 'transform', 'extract', or 'auto' (default: auto)
    """
    f = request.files.get("file")
    if not f:
        return "No file received", 400

    raw_html = f.read().decode("utf-8", errors="replace")
    font = request.form.get("font", None)
    requested_mode = request.form.get("mode", "auto")

    try:
        # Determine mode
        if requested_mode == "auto":
            mode = detect_mode(raw_html)
        else:
            mode = requested_mode

        # Route to appropriate pipeline
        original_title = None
        html_to_parse = raw_html

        if mode == "extract":
            # Capture title before Trafilatura strips <head>
            original_soup = BeautifulSoup(raw_html, "lxml")
            original_title = original_soup.find("title")
            html_to_parse = extract_with_trafilatura(raw_html)

        doc = parse(html_to_parse, original_title=original_title)
        use_opendyslexic = (font == "opendyslexic")
        output = render(doc, use_opendyslexic=use_opendyslexic)

        # Add mode info as HTML comment for debugging
        output = output.replace(
            "<!DOCTYPE html>",
            f"<!DOCTYPE html>\n<!-- flowdoc mode: {mode} -->"
        )

        return output, 200, {"Content-Type": "text/html; charset=utf-8"}

    except ValueError as e:
        return f"<pre>Validation error: {e}</pre>", 422
    except Exception as e:
        return f"<pre>Error: {e}</pre>", 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
