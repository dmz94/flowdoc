"""
Fetch HTML fixture files for Flowdoc test corpora.

Downloads pages from their source URLs and saves them as HTML fixtures.
Supports multiple corpora via the --corpus argument.

Usage (from project root with venv active):
    python scripts/corpus/fetch_corpus.py                  # fetch all corpora
    python scripts/corpus/fetch_corpus.py --corpus input   # fetch one corpus

Requires: pip install requests
"""

import argparse
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Each corpus: name -> (output_dir, fixtures list)
# Fixtures: (url, filename, description)
CORPORA = {
    "input": {
        "dir": PROJECT_ROOT / "tests" / "fixtures" / "input",
        "fixtures": [
            (
                "https://en.wikipedia.org/api/rest_v1/page/html/Dyslexia",
                "wikipedia_dyslexia.html",
                "Wikipedia - Dyslexia (encyclopedia article)",
            ),
            (
                "https://en.wikipedia.org/wiki/Photosynthesis",
                "wikipedia_photosynthesis.html",
                "Wikipedia - Photosynthesis (science article)",
            ),
            (
                "https://developer.mozilla.org/en-US/docs/Web/HTML/Element",
                "mdn_html_elements.html",
                "MDN - HTML elements (technical documentation)",
            ),
            (
                "https://www.nhs.uk/conditions/dyslexia/",
                "nhs_dyslexia.html",
                "NHS - Dyslexia (health/medical page)",
            ),
            (
                "https://www.bbcgoodfood.com/recipes/spaghetti-carbonara",
                "bbcgoodfood_carbonara.html",
                "BBC Good Food - Spaghetti Carbonara (recipe)",
            ),
            (
                "https://www.wikihow.com/Ride-a-Bike",
                "wikihow_ride_a_bike.html",
                "WikiHow - How to Ride a Bike (how-to guide)",
            ),
            (
                "https://www.cdc.gov/ncbddd/dyslexia/facts.html",
                "cdc_dyslexia.html",
                "CDC - Dyslexia facts (government/health page)",
            ),
            (
                "https://paulgraham.com/identity.html",
                "paulgraham_identity.html",
                "Paul Graham - Keep Your Identity Small (blog/essay)",
            ),
            (
                "https://raw.githubusercontent.com/mozilla/readability/main/test/test-pages/001/source.html",
                "readability_001_tech_blog.html",
                "Mozilla Readability test 001 (tech blog article)",
            ),
        ],
    },
    "user-study": {
        "dir": PROJECT_ROOT / "tests" / "fixtures" / "user-study",
        "fixtures": [
            (
                "https://www.skysports.com/football/news/11095/13511444/home-advantage-is-on-the-wane-in-the-premier-league-between-the-lines",
                "skysports.html",
                "Sky Sports - Home advantage (sports analysis)",
            ),
            (
                "https://www.theringer.com/2024/07/25/olympics/chase-budinger-paris-2024-olympics-beach-volleyball",
                "theringer.html",
                "The Ringer - Chase Budinger (sports profile)",
            ),
            (
                "https://www.smithsonianmag.com/science-nature/essential-timeline-understanding-evolution-homo-sapiens-180976807/",
                "smithsonian.html",
                "Smithsonian - Homo Sapiens evolution (science)",
            ),
            (
                "https://aeon.co/essays/how-the-harsh-icy-world-of-snowball-earth-shaped-life-today",
                "aeon.html",
                "Aeon - Snowball Earth (longform essay)",
            ),
            (
                "https://www.theguardian.com/food/2020/feb/13/how-ultra-processed-food-took-over-your-shopping-basket-brazil-carlos-monteiro",
                "guardian.html",
                "The Guardian - Ultra-processed food (longform)",
            ),
            (
                "https://www.eater.com/dining-out/919418/lisbon-pastel-de-nata-tourism-gentrification-portugal",
                "eater.html",
                "Eater - Lisbon pastel de nata (food/culture)",
            ),
            (
                "https://www.pbs.org/newshour/arts/explainer-here-is-why-crowd-surges-can-kill-people",
                "pbs.html",
                "PBS - Crowd surges (explainer)",
            ),
            (
                "https://www.propublica.org/article/3m-forever-chemicals-pfas-pfos-inside-story",
                "propublica.html",
                "ProPublica - 3M PFAS (investigative)",
            ),
            (
                "https://www.nhs.uk/conditions/dyslexia/",
                "nhs.html",
                "NHS - Dyslexia (health/medical page)",
            ),
            (
                "https://www.cdc.gov/west-nile-virus/symptoms-diagnosis-treatment/index.html",
                "cdc.html",
                "CDC - West Nile virus (government/health)",
            ),
        ],
    },
}

MIN_SIZE = 10 * 1024  # 10 KB


def fetch_corpus(name, corpus, session):
    """Fetch all fixtures for a single corpus. Returns (passed, failed)."""
    output_dir = corpus["dir"]
    fixtures = corpus["fixtures"]

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Corpus: {name}")
    print(f"  Output: {output_dir}")
    print(f"  Fixtures: {len(fixtures)}")
    print()

    passed = 0
    failed = 0

    for i, (url, filename, description) in enumerate(fixtures):
        output_path = output_dir / filename
        print(f"  Fetching: {description}")
        print(f"    URL: {url}")

        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()

            content = response.content
            size = len(content)

            if size < MIN_SIZE:
                print(f"    FAILED - only {size} bytes (below {MIN_SIZE // 1024} KB minimum)")
                failed += 1
            else:
                output_path.write_bytes(content)
                print(f"    OK - saved ({size // 1024} KB)")
                passed += 1

        except requests.exceptions.HTTPError as e:
            print(f"    FAILED - HTTP error: {e}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print(f"    FAILED - connection error")
            failed += 1
        except requests.exceptions.Timeout:
            print(f"    FAILED - request timed out")
            failed += 1
        except Exception as e:
            print(f"    FAILED - {e}")
            failed += 1

        # Polite delay between requests
        if i < len(fixtures) - 1:
            time.sleep(1)

    return passed, failed


def main():
    parser = argparse.ArgumentParser(description="Fetch HTML fixtures for Flowdoc test corpora")
    parser.add_argument(
        "--corpus",
        default=None,
        choices=list(CORPORA.keys()),
        help="Which corpus to fetch (default: all)",
    )
    args = parser.parse_args()

    if args.corpus:
        targets = {args.corpus: CORPORA[args.corpus]}
    else:
        targets = CORPORA

    session = requests.Session()
    session.headers.update(HEADERS)

    total_passed = 0
    total_failed = 0

    for name, corpus in targets.items():
        passed, failed = fetch_corpus(name, corpus, session)
        total_passed += passed
        total_failed += failed
        print()

    print("--- Summary ---")
    print(f"  {total_passed} succeeded, {total_failed} failed.")
    if total_failed > 0:
        print("  For failed files, save manually: open the URL in a browser,")
        print("  File > Save As > Web Page, HTML Only.")


if __name__ == "__main__":
    main()
