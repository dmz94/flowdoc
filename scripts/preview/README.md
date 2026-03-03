# scripts/preview/

Dev tools for visually inspecting Flowdoc conversion output.

## Scripts

**convert_fixtures.py** -- Batch convert all HTML fixtures in
tests/fixtures/input/ and write .flowdoc.html output alongside each.

    python scripts/preview/convert_fixtures.py

**preview_server.py** -- Flask drag-drop server. Upload an HTML file
and see the Flowdoc conversion in your browser.

    python scripts/preview/preview_server.py
    # Open http://localhost:5000

Requires preview.html in this directory (not yet created).
