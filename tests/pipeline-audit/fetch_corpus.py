"""
Fetch HTML fixture files for Flowdoc test corpora.

Downloads pages from their source URLs and saves them as HTML fixtures.
Supports multiple corpora via the --corpus argument.

Usage (from project root with venv active):
    python tests/pipeline-audit/fetch_corpus.py                  # fetch all corpora
    python tests/pipeline-audit/fetch_corpus.py --corpus input   # fetch one corpus
    python tests/pipeline-audit/fetch_corpus.py --corpus candidates  # fetch candidate URLs

Requires: pip install requests
"""

import argparse
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_DIR = Path(__file__).resolve().parent

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

CANDIDATES_MD = AUDIT_DIR / "candidates.md"
STAGING_DIR = AUDIT_DIR / "staging"
FETCH_RESULTS_PATH = AUDIT_DIR / "fetch-results.txt"

MIN_SIZE = 10 * 1024  # 10 KB


def parse_candidates_md(path=CANDIDATES_MD):
    """Parse candidates.md and return list of (url, filename, id) tuples."""
    text = path.read_text(encoding="utf-8")
    candidates = []
    # Match table rows: | C## | slug | URL | ... |
    row_re = re.compile(
        r"^\|\s*(C\d+)\s*\|\s*(\S+)\s*\|\s*(https?://\S+?)\s*\|",
        re.MULTILINE,
    )
    for match in row_re.finditer(text):
        cid = match.group(1)
        slug = match.group(2)
        url = match.group(3)
        filename = slug + ".html"
        candidates.append((url, filename, cid))
    return candidates


def fetch_candidates(session):
    """Fetch all candidate URLs from candidates.md into staging dir.

    Returns list of result dicts for summary table.
    """
    if not CANDIDATES_MD.exists():
        print(f"ERROR: candidates.md not found: {CANDIDATES_MD}", file=sys.stderr)
        sys.exit(1)

    candidates = parse_candidates_md()
    total = len(candidates)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Corpus: candidates")
    print(f"  Source: {CANDIDATES_MD}")
    print(f"  Output: {STAGING_DIR}")
    print(f"  Candidates: {total}")
    print()

    results = []

    for i, (url, filename, cid) in enumerate(candidates, 1):
        slug = filename.removesuffix(".html")
        print(f"  [{i}/{total}] Fetching {slug}...")
        output_path = STAGING_DIR / filename

        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()

            content = response.content
            size = len(content)
            size_kb = size / 1024

            output_path.write_bytes(content)

            if size < MIN_SIZE:
                print(f"  [{i}/{total}] SMALL - {size_kb:.0f} KB")
                results.append({
                    "id": cid, "slug": slug, "size_kb": size_kb,
                    "status": "SMALL", "reason": f"<10KB ({size_kb:.0f} KB)",
                })
            else:
                print(f"  [{i}/{total}] OK - {size_kb:.0f} KB")
                results.append({
                    "id": cid, "slug": slug, "size_kb": size_kb,
                    "status": "OK", "reason": "",
                })

        except requests.exceptions.HTTPError as e:
            reason = f"HTTP {e.response.status_code}" if e.response else str(e)
            print(f"  [{i}/{total}] FAILED - {reason}")
            results.append({
                "id": cid, "slug": slug, "size_kb": 0,
                "status": "FAILED", "reason": reason,
            })
        except requests.exceptions.ConnectionError:
            print(f"  [{i}/{total}] FAILED - connection error")
            results.append({
                "id": cid, "slug": slug, "size_kb": 0,
                "status": "FAILED", "reason": "connection error",
            })
        except requests.exceptions.Timeout:
            print(f"  [{i}/{total}] FAILED - timeout")
            results.append({
                "id": cid, "slug": slug, "size_kb": 0,
                "status": "FAILED", "reason": "timeout",
            })
        except Exception as e:
            print(f"  [{i}/{total}] FAILED - {e}")
            results.append({
                "id": cid, "slug": slug, "size_kb": 0,
                "status": "FAILED", "reason": str(e),
            })

        # Polite delay between requests
        if i < total:
            time.sleep(1.5)

    # Print summary table
    ok_count = sum(1 for r in results if r["status"] == "OK")
    small_count = sum(1 for r in results if r["status"] == "SMALL")
    fail_count = sum(1 for r in results if r["status"] == "FAILED")

    print()
    print("=" * 78)
    print("FETCH SUMMARY")
    print("=" * 78)
    header = f"  {'ID':<5s} {'Slug':<35s} {'Size':>7s}  {'Status':<8s} {'Notes'}"
    sep = f"  {'---':<5s} {'---':<35s} {'---':>7s}  {'---':<8s} {'---'}"
    print(header)
    print(sep)
    for r in results:
        size_str = f"{r['size_kb']:.0f} KB" if r["size_kb"] > 0 else "-"
        notes = r["reason"] if r["status"] == "FAILED" else ""
        print(f"  {r['id']:<5s} {r['slug']:<35s} {size_str:>7s}  {r['status']:<8s} {notes}")

    print()
    print(f"  OK: {ok_count}  SMALL: {small_count}  FAILED: {fail_count}  Total: {total}")

    # Save results to file
    lines = []
    lines.append("Corpus Expansion Fetch Results")
    lines.append(f"Date: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append(f"{'ID':<5s} {'Slug':<35s} {'Size':>7s}  {'Status':<8s} {'Notes'}")
    lines.append(f"{'---':<5s} {'---':<35s} {'---':>7s}  {'---':<8s} {'---'}")
    for r in results:
        size_str = f"{r['size_kb']:.0f} KB" if r["size_kb"] > 0 else "-"
        notes = r["reason"] if r["status"] == "FAILED" else ""
        lines.append(f"{r['id']:<5s} {r['slug']:<35s} {size_str:>7s}  {r['status']:<8s} {notes}")
    lines.append("")
    lines.append(f"OK: {ok_count}  SMALL: {small_count}  FAILED: {fail_count}  Total: {total}")
    lines.append("")

    FETCH_RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n  Results saved to: {FETCH_RESULTS_PATH}")

    return ok_count, fail_count + small_count


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
    all_choices = list(CORPORA.keys()) + ["candidates"]
    parser = argparse.ArgumentParser(description="Fetch HTML fixtures for Flowdoc test corpora")
    parser.add_argument(
        "--corpus",
        default=None,
        choices=all_choices,
        help="Which corpus to fetch (default: all except candidates)",
    )
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update(HEADERS)

    # "candidates" corpus is handled separately
    if args.corpus == "candidates":
        fetch_candidates(session)
        return

    if args.corpus:
        targets = {args.corpus: CORPORA[args.corpus]}
    else:
        targets = CORPORA

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
