"""
Batch runner: run Readability.js + Decant comparison on multiple fixtures.

Usage:
    python scripts/run-comparison-batch.py --all
    python scripts/run-comparison-batch.py yale360-baboons timeout-london

Outputs:
    scripts/output/full-results.json    (structured data for AI triage)
    scripts/output/full-summary.txt     (paste-friendly summary by classification)
    scripts/output/triage-needed.txt    (moderate/severe/loss fixtures for triage)
    scripts/output/cleanup-manifest.txt (inventory of all comparison tool files)
    tests/corpus-screening/review/compare-{name}.html (per fixture)
"""
import json
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to path so we can import compare-extractions
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

# Import comparison logic from compare-extractions
from importlib import import_module
compare_mod = import_module("compare-extractions")
run_comparison = compare_mod.run_comparison

FIXTURE_DIR = PROJECT_ROOT / "tests" / "pipeline-audit" / "test-pages"
MANIFEST_PATH = PROJECT_ROOT / "tests" / "pipeline-audit" / "manifest.md"
OUTPUT_DIR = SCRIPTS_DIR / "output"
READABILITY_SCRIPT = SCRIPTS_DIR / "readability-extract.js"
REVIEW_DIR = PROJECT_ROOT / "tests" / "corpus-screening" / "review"


# ---------------------------------------------------------------------------
# Manifest parsing
# ---------------------------------------------------------------------------

def parse_manifest():
    """Parse manifest.md and return list of {name, filename, source_url, scope}."""
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    fixtures = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")]
        # cols[0] is empty (before first |), cols[1] is #, etc.
        if len(cols) < 6:
            continue
        num, filename, source_url, scope = cols[1], cols[2], cols[3], cols[4]
        # Skip header and separator rows
        if num in ("#", "---", "") or filename in ("filename", "---", ""):
            continue
        if not filename.endswith(".html"):
            continue
        name = filename.replace(".html", "")
        fixtures.append({
            "name": name,
            "filename": filename,
            "source_url": source_url,
            "scope": scope,
        })
    return fixtures


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(result):
    """Classify a comparison result and return (classification, tags)."""
    sim = result["similarity"]
    p = result["paragraphs"]
    r_only_p = p["readability_only"]
    d_only_p = p["decant_only"]
    shared_p = p["shared"]
    direction = result.get("direction", "COMPARABLE")

    # Classification
    # DECANT_WINS: Decant has more content and Readability missed little
    if direction == "DECANT_AHEAD" and r_only_p <= 2:
        classification = "DECANT_WINS"
    elif sim >= 0.90 and r_only_p <= 2 and d_only_p <= 2:
        classification = "CLEAN"
    elif sim >= 0.80:
        classification = "GOOD"
    elif sim >= 0.50:
        classification = "MODERATE_GAP"
    elif sim >= 0.15:
        classification = "SEVERE_GAP"
    else:
        classification = "NEAR_TOTAL_LOSS"

    # Tags
    tags = []

    if direction == "DECANT_AHEAD" and r_only_p <= 2:
        tags.append("DECANT_WINS")

    r_hdg_count = len(result["headings"]["readability"])
    d_hdg_count = len(result["headings"]["decant"])
    if r_only_p > 0 and r_hdg_count < d_hdg_count:
        tags.append("PRE_HEADING_CONTENT")

    r_only_imgs = len(result["images"]["readability_only"])
    shared_imgs = len(result["images"]["shared"])
    total_r_imgs = r_only_imgs + shared_imgs
    if r_only_imgs > 0 and shared_imgs < total_r_imgs:
        tags.append("IMAGE_LOSS")

    d_only_imgs = len(result["images"]["decant_only"])
    if d_only_imgs > 0:
        tags.append("IMAGE_GAIN")

    if d_only_p > 3:
        tags.append("BOILERPLATE_LEAK")

    if d_only_p > 10:
        d_only_texts = result.get("decant_only_texts", [])
        if d_only_texts:
            lengths = [len(t) for t in d_only_texts]
            if statistics.median(lengths) < 100:
                tags.append("CONTENT_FRAGMENTATION")

    # Paragraph match failure: both extracted content but nothing matched
    if shared_p == 0 and r_only_p > 5 and d_only_p > 5:
        tags.append("PARAGRAPH_MATCH_FAILURE")

    return classification, tags


# ---------------------------------------------------------------------------
# Readability runner
# ---------------------------------------------------------------------------

def run_readability(fixture_path, output_path, source_url):
    """Run readability-extract.js via subprocess. Returns True on success."""
    cmd = [
        "node", str(READABILITY_SCRIPT),
        str(fixture_path), str(output_path),
        f"--source-url={source_url}",
    ]
    result = subprocess.run(
        cmd, capture_output=True, timeout=60,
        encoding="utf-8", errors="replace",
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        if "null" in stderr.lower() or "could not parse" in stderr.lower():
            return False, "Readability returned null (not article-like)"
        return False, stderr[:200] if stderr else "unknown error"
    return True, stdout


# ---------------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------------

def write_full_summary(results, errors):
    """Write full-summary.txt grouped by classification."""
    groups = {
        "CLEAN": [], "GOOD": [], "DECANT_WINS": [], "MODERATE_GAP": [],
        "SEVERE_GAP": [], "NEAR_TOTAL_LOSS": [],
    }
    for r in results:
        cls = r["classification"]
        if cls in groups:
            groups[cls].append(r)

    lines = [f"=== FULL COMPARISON: {len(results)} fixtures ===", ""]

    for cls_name in ("CLEAN", "GOOD", "DECANT_WINS", "MODERATE_GAP", "SEVERE_GAP", "NEAR_TOTAL_LOSS"):
        items = groups[cls_name]
        lines.append(f"--- {cls_name} ({len(items)} fixtures) ---")
        for r in sorted(items, key=lambda x: x["similarity"], reverse=True):
            tag_str = f" [{', '.join(r['tags'])}]" if r["tags"] else ""
            lines.append(f"{r['fixture']}: {r['similarity']:.1%}{tag_str}")
        lines.append("")

    if errors:
        lines.append(f"--- ERRORS ({len(errors)} fixtures) ---")
        for name, msg in errors:
            lines.append(f"{name}: {msg}")
        lines.append("")

    counts = {k: len(v) for k, v in groups.items()}
    lines.append("=== SUMMARY ===")
    lines.append(
        f"Total: {len(results) + len(errors)} fixtures"
    )
    lines.append(
        f"Clean: {counts['CLEAN']} | Good: {counts['GOOD']} | "
        f"Decant wins: {counts['DECANT_WINS']} | "
        f"Moderate: {counts['MODERATE_GAP']} | Severe: {counts['SEVERE_GAP']} | "
        f"Total loss: {counts['NEAR_TOTAL_LOSS']} | Errors: {len(errors)}"
    )
    lines.append("")
    lines.append("=== END ===")
    return "\n".join(lines)


def write_decant_wins(results):
    """Write decant-wins.txt for fixtures where Decant outperformed Readability."""
    wins = [r for r in results if r["classification"] == "DECANT_WINS"]
    wins.sort(key=lambda x: x["paragraphs"]["decant_only"], reverse=True)

    lines = [f"=== DECANT WINS: {len(wins)} fixtures ===", ""]
    lines.append("Fixtures where Decant extracted more content than Readability.")
    lines.append("These need human verification, not engine investigation.")
    lines.append("")

    for r in wins:
        p = r["paragraphs"]
        lines.append(f"--- {r['fixture']} ---")
        lines.append(f"Similarity: {r['similarity']:.1%}")
        lines.append(f"Direction: {r.get('direction', 'DECANT_AHEAD')}")
        tags = [t for t in r["tags"] if t != "DECANT_WINS"]
        if tags:
            lines.append(f"Tags: {', '.join(tags)}")
        lines.append(f"Shared: {p['shared']} paragraphs")
        lines.append(f"Readability-only: {p['readability_only']} paragraphs")
        lines.append(f"Decant-only: {p['decant_only']} paragraphs")

        d_texts = r.get("decant_only_texts", [])
        if d_texts:
            lines.append("Sample Decant-only content:")
            for t in d_texts[:3]:
                truncated = t[:120] + "..." if len(t) > 120 else t
                lines.append(f"  - {truncated}")

        lines.append("")

    lines.append("=== END DECANT WINS ===")
    return "\n".join(lines)


def write_triage_needed(results):
    """Write triage-needed.txt for moderate/severe/loss fixtures (excludes DECANT_WINS)."""
    triage = [
        r for r in results
        if r["classification"] in ("MODERATE_GAP", "SEVERE_GAP", "NEAR_TOTAL_LOSS")
    ]
    triage.sort(key=lambda x: x["similarity"])

    lines = [f"=== TRIAGE NEEDED: {len(triage)} fixtures ===", ""]

    for r in triage:
        p = r["paragraphs"]
        lines.append(f"--- {r['fixture']} ---")
        lines.append(f"Similarity: {r['similarity']:.1%}")
        lines.append(f"Classification: {r['classification']}")
        if r["tags"]:
            lines.append(f"Tags: {', '.join(r['tags'])}")
        lines.append(f"Readability-only: {p['readability_only']} paragraphs")
        lines.append(f"Decant-only: {p['decant_only']} paragraphs")

        # Sample readability-only paragraphs
        r_texts = r.get("readability_only_texts", [])
        if r_texts:
            lines.append("Sample Readability-only (Decant missed):")
            for t in r_texts[:3]:
                truncated = t[:120] + "..." if len(t) > 120 else t
                lines.append(f"  - {truncated}")

        # Sample decant-only paragraphs
        d_texts = r.get("decant_only_texts", [])
        if d_texts:
            lines.append("Sample Decant-only (possible boilerplate):")
            for t in d_texts[:3]:
                truncated = t[:120] + "..." if len(t) > 120 else t
                lines.append(f"  - {truncated}")

        lines.append("")

    lines.append("=== END TRIAGE ===")
    return "\n".join(lines)


def write_cleanup_manifest():
    """Write cleanup-manifest.txt listing all comparison tool files."""
    # Count compare HTML files
    compare_files = list(REVIEW_DIR.glob("compare-*.html"))

    lines = [
        "=== COMPARISON TOOL FILE INVENTORY ===",
        "",
        "=== scripts/ ===",
        "scripts/readability-extract.js (Readability.js extractor)",
        "scripts/compare-extractions.py (comparison + HTML report)",
        "scripts/run-comparison-batch.py (batch runner)",
        "scripts/output/ (directory)",
        "scripts/output/full-results.json",
        "scripts/output/full-summary.txt",
        "scripts/output/triage-needed.txt",
        "scripts/output/decant-wins.txt",
        "scripts/output/triage-fixtures.json (manual extract)",
        "scripts/output/batch-results.json (from earlier prototype run)",
        "scripts/output/batch-summary.txt (from earlier prototype run)",
        "scripts/output/cleanup-manifest.txt",
        "",
        "=== tests/corpus-screening/review/ ===",
        f"tests/corpus-screening/review/compare-*.html ({len(compare_files)} files)",
        "",
        "=== scripts/ (additional) ===",
        "scripts/node_modules/ (npm packages, gitignored)",
        "scripts/package.json (tracked)",
        "scripts/package-lock.json (gitignored)",
        "",
        "=== GITIGNORE STATUS ===",
        "GITIGNORED: node_modules/, package-lock.json, scripts/output/, tests/corpus-screening/review/",
        "TRACKED: package.json, scripts/readability-extract.js, scripts/compare-extractions.py, scripts/run-comparison-batch.py",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Readability vs Decant comparison")
    parser.add_argument("--all", action="store_true", help="Run all in-scope fixtures from manifest")
    parser.add_argument("fixtures", nargs="*", help="Fixture names (without .html)")
    args = parser.parse_args()

    if not args.all and not args.fixtures:
        parser.print_help()
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # Build fixture list
    if args.all:
        manifest = parse_manifest()
        fixture_list = [f for f in manifest if f["scope"] == "in-scope"]
    else:
        # For named fixtures, look them up in manifest for source_url
        manifest = parse_manifest()
        manifest_lookup = {f["name"]: f for f in manifest}
        fixture_list = []
        for name in args.fixtures:
            if name in manifest_lookup:
                fixture_list.append(manifest_lookup[name])
            else:
                fixture_list.append({
                    "name": name,
                    "filename": f"{name}.html",
                    "source_url": "https://example.com/placeholder",
                    "scope": "in-scope",
                })

    total = len(fixture_list)
    results = []
    errors = []

    for i, fixture_info in enumerate(fixture_list, 1):
        name = fixture_info["name"]
        source_url = fixture_info["source_url"]
        fixture_path = FIXTURE_DIR / fixture_info["filename"]

        print(f"Processing {i} of {total}: {name}...")

        if not fixture_path.exists():
            msg = f"fixture file not found"
            print(f"  ERROR: {msg}")
            errors.append((name, msg))
            continue

        with tempfile.TemporaryDirectory() as tmpdir:
            r_output = Path(tmpdir) / f"{name}.html"

            ok, detail = run_readability(fixture_path, r_output, source_url)
            if not ok:
                print(f"  ERROR: {detail}")
                errors.append((name, detail))
                continue

            # Load Readability output
            readability_html = r_output.read_text(encoding="utf-8")
            json_path = r_output.with_suffix(".json")
            readability_meta = {}
            if json_path.exists():
                readability_meta = json.loads(json_path.read_text(encoding="utf-8"))

            try:
                result = run_comparison(fixture_path, readability_html, readability_meta)
                classification, tags = classify(result)
                result["classification"] = classification
                result["tags"] = tags
                results.append(result)

                p = result["paragraphs"]
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                print(f"  {classification} {result['similarity']:.1%} "
                      f"(R-only: {p['readability_only']}p, D-only: {p['decant_only']}p){tag_str}")
            except Exception as e:
                msg = f"comparison error: {e}"
                print(f"  ERROR: {msg}")
                errors.append((name, msg))

    # Write outputs
    print(f"\n{'='*60}")
    print(f"Writing outputs...")

    # Full JSON results
    json_path = OUTPUT_DIR / "full-results.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  JSON: {json_path}")

    # Full summary
    summary_text = write_full_summary(results, errors)
    summary_path = OUTPUT_DIR / "full-summary.txt"
    summary_path.write_text(summary_text, encoding="utf-8")
    print(f"  Summary: {summary_path}")

    # Triage needed
    triage_text = write_triage_needed(results)
    triage_path = OUTPUT_DIR / "triage-needed.txt"
    triage_path.write_text(triage_text, encoding="utf-8")
    print(f"  Triage: {triage_path}")

    # Decant wins
    wins_text = write_decant_wins(results)
    wins_path = OUTPUT_DIR / "decant-wins.txt"
    wins_path.write_text(wins_text, encoding="utf-8")
    print(f"  Decant wins: {wins_path}")

    # Cleanup manifest
    cleanup_text = write_cleanup_manifest()
    cleanup_path = OUTPUT_DIR / "cleanup-manifest.txt"
    cleanup_path.write_text(cleanup_text, encoding="utf-8")
    print(f"  Cleanup manifest: {cleanup_path}")

    # Also write batch-results.json for backward compat
    batch_path = OUTPUT_DIR / "batch-results.json"
    batch_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*60}")
    print(summary_text)


if __name__ == "__main__":
    main()
