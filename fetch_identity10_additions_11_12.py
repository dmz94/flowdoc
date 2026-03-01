"""
fetch_identity10_additions_11_12.py - Fetch additive fixtures 11 and 12 for Identity10.

Run from project root with venv activated:
    python fetch_identity10_additions_11_12.py

Options:
    --dry-run     Print what would be fetched without downloading anything.
    --overwrite   Re-fetch and overwrite files that already exist on disk.

Outputs:
    tests/fixtures/identity10/11_yale_what_is_dyslexia.html
    tests/fixtures/identity10/12_understood_what_is_dyslexia.html
    tests/fixtures/identity10/fetch_log_additions_11_12.json

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
LOG_PATH = OUTPUT_DIR / "fetch_log_additions_11_12.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CONNECT_TIMEOUT = 10  # seconds
READ_TIMEOUT = 20     # seconds

FIXTURES = [
    {
        "idx": "11",
        "filename": "11_yale_what_is_dyslexia.html",
        "url": "https://dyslexia.yale.edu/dyslexia/what-is-dyslexia/",
    },
    {
        "idx": "12",
        "filename": "12_understood_what_is_dyslexia.html",
        "url": "https://www.understood.org/en/articles/what-is-dyslexia",
    },
]


def fetch_fixture(fixture, session, overwrite=False):
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
    ap = argparse.ArgumentParser(description="Fetch Identity10 additive fixtures 11 and 12.")
    ap.add_argument("--dry-run", action="store_true", help="Print plan without downloading.")
    ap.add_argument("--overwrite", action="store_true", help="Re-fetch files that already exist.")
    args = ap.parse_args()

    if args.dry_run:
        dry_run()
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving fixtures to: {OUTPUT_DIR.resolve()}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    results = []
    for i, fixture in enumerate(FIXTURES):
        result = fetch_fixture(fixture, session, overwrite=args.overwrite)
        results.append(result)
        if i < len(FIXTURES) - 1:
            time.sleep(1)  # be polite — 1 second between requests

    LOG_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nLog written to: {LOG_PATH}")

    print("\n--- Summary ---")
    ok_count = sum(1 for r in results if r["ok"] and not (r["error"] or "").startswith("skipped"))
    skip_count = sum(1 for r in results if (r["error"] or "").startswith("skipped"))
    fail_count = sum(1 for r in results if not r["ok"])
    print(f"  {'#':>2}  {'status':>6}  {'KB':>7}  filename")
    print(f"  {'--':>2}  {'------':>6}  {'------':>7}  --------")
    for r in results:
        if (r["error"] or "").startswith("skipped"):
            label = "SKIP"
        elif r["ok"]:
            label = "OK"
        else:
            label = "FAIL"
        kb = f"{r['bytes'] / 1024:.1f}" if r["bytes"] else "-"
        print(f"  {r['idx']:>2}  {label:>6}  {kb:>7}  {r['filename']}")
    print(f"\n{ok_count} succeeded, {skip_count} skipped, {fail_count} failed.")
    if fail_count > 0:
        print("For failed items, save manually: open URL in browser > File > Save As > Web Page, HTML Only.")


if __name__ == "__main__":
    main()
