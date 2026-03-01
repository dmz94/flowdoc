"""
fetch_identity10_fixtures.py - Download HTML fixtures for Identity10 review.

Run from project root with venv activated:
    python fetch_identity10_fixtures.py

Options:
    --dry-run     Print what would be fetched without downloading anything.
    --overwrite   Re-fetch and overwrite files that already exist on disk.

Outputs:
    tests/fixtures/identity10/<filename>.html  (one per fixture)
    tests/fixtures/identity10/fetch_log.json   (machine-readable results)

Requires: pip install requests
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

OUTPUT_DIR = Path("tests/fixtures/identity10")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CONNECT_TIMEOUT = 10   # seconds
READ_TIMEOUT = 20      # seconds

FIXTURES = [
    {
        "idx": "01",
        "filename": "01_nhs_dyslexia.html",
        "url": "https://www.nhs.uk/conditions/dyslexia/",
    },
    {
        "idx": "02",
        "filename": "02_nhs_adhd_symptoms.html",
        "url": "https://www.nhs.uk/conditions/attention-deficit-hyperactivity-disorder-adhd/symptoms/",
    },
    {
        "idx": "03",
        "filename": "03_cdc_milestones.html",
        "url": "https://www.cdc.gov/child-development/milestones/",
    },
    {
        "idx": "04",
        "filename": "04_bbc_bitesize_znm2kmn.html",
        "url": "https://www.bbc.co.uk/bitesize/articles/znm2kmn",
    },
    {
        "idx": "05",
        "filename": "05_wikipedia_photosynthesis.html",
        "url": "https://en.wikipedia.org/wiki/Photosynthesis",
    },
    {
        "idx": "06",
        "filename": "06_guardian_ultra_processed_food_brazil_monteiro.html",
        "url": "https://www.theguardian.com/food/2020/feb/13/how-ultra-processed-food-took-over-your-shopping-basket-brazil-carlos-monteiro",
    },
    {
        "idx": "07",
        "filename": "07_understood_what_is_dyslexia.html",
        "url": "https://www.understood.org/en/articles/what-is-dyslexia",
    },
    {
        "idx": "08",
        "filename": "08_bdadyslexia_support_my_child.html",
        "url": "https://www.bdadyslexia.org.uk/advice/children/how-can-i-support-my-child",
    },
    {
        "idx": "09",
        "filename": "09_dyslexiaida_dyslexia_basics.html",
        "url": "https://dyslexiaida.org/dyslexia-basics/",
    },
    {
        "idx": "10",
        "filename": "10_wikipedia_world_war_i.html",
        "url": "https://en.wikipedia.org/wiki/World_War_I",
    },
]


def fetch_fixture(fixture, session, overwrite=False):
    """
    Attempt to download one fixture.

    Returns a result dict with keys:
        idx, url, final_url, status_code, ok, error, filename, bytes
    """
    idx = fixture["idx"]
    filename = fixture["filename"]
    url = fixture["url"]
    output_path = OUTPUT_DIR / filename

    result = {
        "idx": idx,
        "url": url,
        "final_url": None,
        "status_code": None,
        "ok": False,
        "error": None,
        "filename": filename,
        "bytes": 0,
    }

    if output_path.exists() and not overwrite:
        size = output_path.stat().st_size
        print(f"  SKIP [{idx}] {filename} — already exists ({size} bytes). Use --overwrite to re-fetch.")
        result["ok"] = True
        result["error"] = "skipped: file exists"
        result["bytes"] = size
        return result

    print(f"  Fetching [{idx}] {url}")
    try:
        response = session.get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        result["final_url"] = response.url
        result["status_code"] = response.status_code

        response.raise_for_status()

        output_path.write_bytes(response.content)
        size = len(response.content)
        result["ok"] = True
        result["bytes"] = size
        print(f"    OK — {filename} ({size / 1024:.1f} KB, status {response.status_code})")

    except requests.exceptions.HTTPError as e:
        result["error"] = f"HTTP error: {e}"
        print(f"    FAILED — HTTP error: {e}")
    except requests.exceptions.ConnectionError:
        result["error"] = "connection error (site may be blocking requests)"
        print(f"    FAILED — connection error (site may be blocking requests)")
    except requests.exceptions.Timeout:
        result["error"] = "request timed out"
        print(f"    FAILED — request timed out")
    except Exception as e:
        result["error"] = str(e)
        print(f"    FAILED — {e}")

    return result


def dry_run():
    print(f"DRY RUN — would fetch {len(FIXTURES)} fixture(s) into {OUTPUT_DIR.resolve()}\n")
    for f in FIXTURES:
        output_path = OUTPUT_DIR / f["filename"]
        exists = "EXISTS" if output_path.exists() else "missing"
        print(f"  [{f['idx']}] {f['filename']}  ({exists})")
        print(f"       {f['url']}")
    print()


def main():
    ap = argparse.ArgumentParser(description="Fetch Identity10 HTML fixtures.")
    ap.add_argument("--dry-run", action="store_true", help="Print plan without downloading.")
    ap.add_argument("--overwrite", action="store_true", help="Re-fetch files that already exist.")
    args = ap.parse_args()

    if args.dry_run:
        dry_run()
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_DIR / "fetch_log.json"
    print(f"Saving fixtures to: {OUTPUT_DIR.resolve()}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    results = []
    for i, fixture in enumerate(FIXTURES):
        result = fetch_fixture(fixture, session, overwrite=args.overwrite)
        results.append(result)
        if i < len(FIXTURES) - 1:
            time.sleep(1)  # be polite — 1 second between requests

    # Write machine-readable log
    log_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nLog written to: {log_path}")

    # Summary table
    print("\n--- Summary ---")
    ok_count = 0
    fail_count = 0
    skip_count = 0
    print(f"  {'#':>2}  {'status':>6}  {'KB':>7}  filename")
    print(f"  {'--':>2}  {'------':>6}  {'------':>7}  --------")
    for r in results:
        if r["error"] and r["error"].startswith("skipped"):
            label = "SKIP"
            skip_count += 1
        elif r["ok"]:
            label = "OK"
            ok_count += 1
        else:
            label = "FAIL"
            fail_count += 1
        kb = f"{r['bytes'] / 1024:.1f}" if r["bytes"] else "-"
        print(f"  {r['idx']:>2}  {label:>6}  {kb:>7}  {r['filename']}")

    print(f"\n{ok_count} succeeded, {skip_count} skipped, {fail_count} failed.")
    if fail_count > 0:
        print("For failed items, save manually: open URL in browser > File > Save As > Web Page, HTML Only.")


if __name__ == "__main__":
    main()
