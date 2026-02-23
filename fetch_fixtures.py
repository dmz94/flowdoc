"""
fetch_fixtures.py - Download HTML test fixtures for Flowdoc.

Run from your project root with venv activated:
    python fetch_fixtures.py

Files are saved to tests/fixtures/input/
Requires: pip install requests
"""

import time
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

OUTPUT_DIR = Path("tests/fixtures/input")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FIXTURES = [
    {
        "filename": "wikipedia_dyslexia.html",
        "url": "https://en.wikipedia.org/api/rest_v1/page/html/Dyslexia",
        "description": "Wikipedia - Dyslexia (encyclopedia article)",
    },
    {
        "filename": "wikipedia_photosynthesis.html",
        "url": "https://en.wikipedia.org/wiki/Photosynthesis",
        "description": "Wikipedia - Photosynthesis (science article)",
    },
    {
        "filename": "mdn_html_elements.html",
        "url": "https://developer.mozilla.org/en-US/docs/Web/HTML/Element",
        "description": "MDN - HTML elements (technical documentation)",
    },
    {
        "filename": "nhs_dyslexia.html",
        "url": "https://www.nhs.uk/conditions/dyslexia/",
        "description": "NHS - Dyslexia (health/medical page)",
    },
    {
        "filename": "bbcgoodfood_carbonara.html",
        "url": "https://www.bbcgoodfood.com/recipes/spaghetti-carbonara",
        "description": "BBC Good Food - Spaghetti Carbonara (recipe)",
    },
    {
        "filename": "wikihow_ride_a_bike.html",
        "url": "https://www.wikihow.com/Ride-a-Bike",
        "description": "WikiHow - How to Ride a Bike (how-to guide)",
    },
    {
        "filename": "cdc_dyslexia.html",
        "url": "https://www.cdc.gov/ncbddd/dyslexia/facts.html",
        "description": "CDC - Dyslexia facts (government/health page)",
    },
    {
        "filename": "gutenberg_pride_prejudice.html",
        "url": "https://www.gutenberg.org/files/1342/1342-h/1342-h.htm",
        "description": "Project Gutenberg - Pride and Prejudice (long-form book)",
    },
    {
        "filename": "paulgraham_identity.html",
        "url": "https://paulgraham.com/identity.html",
        "description": "Paul Graham - Keep Your Identity Small (blog/essay)",
    },
    {
        "filename": "readability_001_tech_blog.html",
        "url": "https://raw.githubusercontent.com/mozilla/readability/main/test/test-pages/001/source.html",
        "description": "Mozilla Readability test 001 (tech blog article)",
    },
]


def fetch_fixture(fixture, session):
    filename = fixture["filename"]
    url = fixture["url"]
    description = fixture["description"]
    output_path = OUTPUT_DIR / filename

    print(f"Fetching: {description}")
    print(f"  URL: {url}")

    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        size_kb = len(response.content) / 1024
        print(f"  OK - saved to {output_path} ({size_kb:.1f} KB)")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"  FAILED - HTTP error: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  FAILED - connection error (site may be blocking requests)")
        return False
    except requests.exceptions.Timeout:
        print(f"  FAILED - request timed out")
        return False
    except Exception as e:
        print(f"  FAILED - {e}")
        return False


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving fixtures to: {OUTPUT_DIR.resolve()}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    results = []
    for i, fixture in enumerate(FIXTURES):
        success = fetch_fixture(fixture, session)
        results.append((fixture["filename"], success))
        if i < len(FIXTURES) - 1:
            time.sleep(1)  # be polite - 1 second between requests

    print("\n--- Summary ---")
    passed = 0
    failed = 0
    for filename, success in results:
        status = "OK" if success else "FAILED"
        print(f"  {status}: {filename}")
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed} succeeded, {failed} failed.")
    if failed > 0:
        print("For failed files, save them manually by opening the URL in your browser")
        print("and using File > Save As > Web Page, HTML Only.")


if __name__ == "__main__":
    main()
