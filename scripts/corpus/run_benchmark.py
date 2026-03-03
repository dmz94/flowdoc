"""
Run the ScrapingHub Article Extraction Benchmark against Flowdoc.

Iterates over 181 gzip-compressed HTML files from the benchmark repo,
runs the full Flowdoc pipeline on each, and reports pass/fail rates.

Usage (from project root):
    python scripts/corpus/run_benchmark.py

Requires the benchmark repo cloned as a sibling directory:
    git clone https://github.com/scrapinghub/article-extraction-benchmark.git ../article-extraction-benchmark

Writes detailed results to eval/reports/benchmark/results.json.
"""

import gzip
import json
import re
import sys
import traceback
from pathlib import Path

from bs4 import BeautifulSoup

from flowdoc.core.content_selector import detect_mode
from flowdoc.core.parser import parse, extract_with_trafilatura, ValidationError
from flowdoc.core.renderer import render
from flowdoc.core.model import (
    Document, Paragraph, ListBlock, Quote, Preformatted,
    Text, Emphasis, Strong, Code, Link,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_DIR = PROJECT_ROOT.parent / "article-extraction-benchmark"
HTML_DIR = BENCHMARK_DIR / "html"
GROUND_TRUTH_PATH = BENCHMARK_DIR / "ground-truth.json"
REPORT_DIR = PROJECT_ROOT / "eval" / "reports" / "benchmark"


# ---------------------------------------------------------------------------
# Word counting (from run_metrics.py, kept minimal)
# ---------------------------------------------------------------------------

def _inline_text(inline) -> str:
    if isinstance(inline, Text):
        return inline.text
    if isinstance(inline, (Emphasis, Strong)):
        return "".join(_inline_text(c) for c in inline.children)
    if isinstance(inline, Code):
        return inline.text
    if isinstance(inline, Link):
        return "".join(_inline_text(c) for c in inline.children)
    return ""


def count_output_words(doc: Document) -> int:
    """Count prose words in the Document model."""
    total = 0

    def _count_inlines(inlines):
        text = "".join(_inline_text(il) for il in inlines)
        return len(text.split())

    def _walk_blocks(blocks):
        nonlocal total
        for block in blocks:
            if isinstance(block, Paragraph):
                total += _count_inlines(block.inlines)
            elif isinstance(block, ListBlock):
                _walk_list(block)
            elif isinstance(block, Quote):
                _walk_blocks(block.blocks)
            elif isinstance(block, Preformatted):
                total += len(block.text.split())

    def _walk_list(lb):
        nonlocal total
        for item in lb.items:
            total += _count_inlines(item.inlines)
            for child in item.children:
                _walk_list(child)

    for section in doc.sections:
        _walk_blocks(section.blocks)

    return total


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_one(html: str) -> dict:
    """Run Flowdoc pipeline on a single HTML string. Returns result dict."""
    try:
        mode = detect_mode(html)
        original_title = None
        html_to_parse = html

        if mode == "extract":
            soup = BeautifulSoup(html, "lxml")
            original_title = soup.find("title")
            html_to_parse = extract_with_trafilatura(html)

        doc = parse(
            html_to_parse,
            original_title=original_title,
            require_article_body=(mode == "extract"),
        )
        rendered = render(doc)

        return {
            "status": "PASS",
            "mode": mode,
            "section_count": len(doc.sections),
            "output_word_count": count_output_words(doc),
            "error": None,
            "error_type": None,
        }

    except ValidationError as e:
        msg = str(e)
        if "Out of scope" in msg:
            status = "SCOPE_ERROR"
        elif "No article body" in msg:
            status = "EXTRACTION_FAIL"
        else:
            status = "VALIDATION_ERROR"
        return {
            "status": status,
            "mode": detect_mode(html),
            "section_count": 0,
            "output_word_count": 0,
            "error": msg,
            "error_type": "ValidationError",
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "mode": None,
            "section_count": 0,
            "output_word_count": 0,
            "error": str(e),
            "error_type": type(e).__name__,
        }


# ---------------------------------------------------------------------------
# Ground truth comparison
# ---------------------------------------------------------------------------

def compute_word_overlap(output_words: str, truth_words: str) -> float:
    """Compute word overlap ratio: |intersection| / |truth words|."""
    out_set = set(output_words.lower().split())
    truth_set = set(truth_words.lower().split())
    if not truth_set:
        return 0.0
    return len(out_set & truth_set) / len(truth_set)


def extract_plain_text(doc: Document) -> str:
    """Extract all plain text from a Document model."""
    parts = []

    def _collect_inlines(inlines):
        for il in inlines:
            parts.append(_inline_text(il))

    def _walk_blocks(blocks):
        for block in blocks:
            if isinstance(block, Paragraph):
                _collect_inlines(block.inlines)
            elif isinstance(block, ListBlock):
                _walk_list(block)
            elif isinstance(block, Quote):
                _walk_blocks(block.blocks)
            elif isinstance(block, Preformatted):
                parts.append(block.text)

    def _walk_list(lb):
        for item in lb.items:
            _collect_inlines(item.inlines)
            for child in item.children:
                _walk_list(child)

    for section in doc.sections:
        _collect_inlines(section.heading.inlines)
        _walk_blocks(section.blocks)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not HTML_DIR.exists():
        print(
            f"ERROR: Benchmark HTML directory not found: {HTML_DIR}\n"
            f"Clone the repo first:\n"
            f"  git clone https://github.com/scrapinghub/article-extraction-benchmark.git "
            f"../article-extraction-benchmark",
            file=sys.stderr,
        )
        sys.exit(1)

    gz_files = sorted(HTML_DIR.glob("*.html.gz"))
    total = len(gz_files)
    print(f"ScrapingHub Article Extraction Benchmark")
    print(f"Files: {total}")
    print()

    # Load ground truth
    ground_truth = {}
    if GROUND_TRUTH_PATH.exists():
        ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))

    results = {}
    counters = {
        "PASS": 0,
        "VALIDATION_ERROR": 0,
        "SCOPE_ERROR": 0,
        "EXTRACTION_FAIL": 0,
        "ERROR": 0,
    }
    mode_counters = {"extract": 0, "transform": 0}

    for i, gz_path in enumerate(gz_files, 1):
        file_hash = gz_path.name.removesuffix(".html.gz")

        # Decompress
        with gzip.open(gz_path, "rb") as f:
            html = f.read().decode("utf-8", errors="replace")

        # Run pipeline
        result = run_one(html)
        result["file"] = gz_path.name
        result["url"] = ground_truth.get(file_hash, {}).get("url", "")

        # Count
        status = result["status"]
        counters[status] += 1
        if result["mode"]:
            mode_counters[result["mode"]] += 1

        # Progress
        marker = "OK" if status == "PASS" else status
        print(f"  [{i:3d}/{total}]  {marker:<20s}  {file_hash[:16]}...")

        results[file_hash] = result

    # Summary
    pass_count = counters["PASS"]
    val_err = counters["VALIDATION_ERROR"]
    scope_err = counters["SCOPE_ERROR"]
    extract_fail = counters["EXTRACTION_FAIL"]
    error_count = counters["ERROR"]
    all_validation = val_err + scope_err + extract_fail

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total files:          {total}")
    print(f"  PASS:                 {pass_count:3d}  ({100*pass_count/total:.1f}%)")
    print(f"  VALIDATION_ERROR:     {all_validation:3d}  ({100*all_validation/total:.1f}%)")
    print(f"    - SCOPE_ERROR:      {scope_err:3d}")
    print(f"    - EXTRACTION_FAIL:  {extract_fail:3d}")
    print(f"    - Other:            {val_err:3d}")
    print(f"  ERROR:                {error_count:3d}  ({100*error_count/total:.1f}%)")
    print()
    print(f"  Mode breakdown:")
    print(f"    extract:            {mode_counters['extract']:3d}")
    print(f"    transform:          {mode_counters['transform']:3d}")
    print()

    # PASS stats
    pass_results = [r for r in results.values() if r["status"] == "PASS"]
    if pass_results:
        word_counts = [r["output_word_count"] for r in pass_results]
        section_counts = [r["section_count"] for r in pass_results]
        print(f"  PASS output stats:")
        print(f"    Avg word count:     {sum(word_counts)/len(word_counts):.0f}")
        print(f"    Median word count:  {sorted(word_counts)[len(word_counts)//2]}")
        print(f"    Avg sections:       {sum(section_counts)/len(section_counts):.1f}")
    print()

    # Failure analysis
    print("=" * 60)
    print("FAILURE ANALYSIS")
    print("=" * 60)

    # Group by error message
    error_groups = {}
    for file_hash, r in results.items():
        if r["status"] != "PASS":
            msg = r["error"] or "unknown"
            # Normalize long messages
            short_msg = msg[:120]
            if short_msg not in error_groups:
                error_groups[short_msg] = []
            error_groups[short_msg].append(file_hash)

    # Sort by frequency
    sorted_errors = sorted(error_groups.items(), key=lambda x: -len(x[1]))
    for msg, hashes in sorted_errors[:10]:
        print(f"\n  [{len(hashes)}x] {msg}")
        for h in hashes[:3]:
            url = results[h].get("url", "")
            print(f"       {h[:16]}...  {url[:60]}")

    # Ground truth overlap for PASS results
    print()
    print("=" * 60)
    print("GROUND TRUTH OVERLAP (PASS results only)")
    print("=" * 60)

    overlaps = []
    for file_hash, r in results.items():
        if r["status"] != "PASS":
            continue
        truth_entry = ground_truth.get(file_hash)
        if not truth_entry or not truth_entry.get("articleBody"):
            continue

        # Re-run pipeline to get Document for text extraction
        gz_path = HTML_DIR / f"{file_hash}.html.gz"
        with gzip.open(gz_path, "rb") as f:
            html = f.read().decode("utf-8", errors="replace")

        try:
            mode = detect_mode(html)
            original_title = None
            html_to_parse = html
            if mode == "extract":
                soup = BeautifulSoup(html, "lxml")
                original_title = soup.find("title")
                html_to_parse = extract_with_trafilatura(html)
            doc = parse(
                html_to_parse,
                original_title=original_title,
                require_article_body=(mode == "extract"),
            )
            plain = extract_plain_text(doc)
            overlap = compute_word_overlap(plain, truth_entry["articleBody"])
            overlaps.append((file_hash, overlap))
        except Exception:
            continue

    if overlaps:
        scores = [o[1] for o in overlaps]
        scores_sorted = sorted(scores)
        mean = sum(scores) / len(scores)
        median = scores_sorted[len(scores_sorted) // 2]
        bottom5 = sorted(overlaps, key=lambda x: x[1])[:5]

        print(f"  Files with ground truth: {len(overlaps)}")
        print(f"  Mean overlap:           {mean:.3f}")
        print(f"  Median overlap:         {median:.3f}")
        print()
        print(f"  Bottom 5 overlap scores:")
        for h, score in bottom5:
            url = results[h].get("url", "")
            print(f"    {score:.3f}  {h[:16]}...  {url[:50]}")
    else:
        print("  No overlap data available.")

    print()

    # Save results
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "results.json"
    report = {
        "total": total,
        "summary": {
            "PASS": pass_count,
            "VALIDATION_ERROR": val_err,
            "SCOPE_ERROR": scope_err,
            "EXTRACTION_FAIL": extract_fail,
            "ERROR": error_count,
        },
        "mode_breakdown": mode_counters,
        "results": results,
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Results saved to: {report_path}")


if __name__ == "__main__":
    main()
