"""
Run the Webis Web Content Extraction Benchmark (WCEB) against Decant.

Iterates over 3985 HTML files across 8 datasets and reports pass/fail
rates per dataset and overall.

Usage (from project root):
    python tests/benchmark-wceb/run_wceb.py --benchmark-dir ../web-content-extraction-benchmark/datasets/combined

Writes detailed results to eval/reports/benchmark/wceb_results.json (ephemeral).
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

from decant.core.content_selector import detect_mode
from decant.core.parser import parse, extract_with_trafilatura, ValidationError
from decant.core.renderer import render
from decant.core.model import (
    Document, Paragraph, ListBlock, Quote, Preformatted,
    Text, Emphasis, Strong, Code, Link,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = PROJECT_ROOT / "eval" / "reports" / "benchmark"


# ---------------------------------------------------------------------------
# Word counting (same as run_benchmark.py)
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

        try:
            mode = detect_mode(html)
        except Exception:
            mode = None

        return {
            "status": status,
            "mode": mode,
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
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run Webis WCEB against Decant"
    )
    parser.add_argument(
        "--benchmark-dir",
        required=True,
        help="Path to the combined dataset directory",
    )
    args = parser.parse_args()

    benchmark_dir = Path(args.benchmark_dir).resolve()
    html_dir = benchmark_dir / "html"

    if not html_dir.exists():
        print(f"ERROR: HTML directory not found: {html_dir}", file=sys.stderr)
        sys.exit(1)

    # Discover datasets and files
    datasets = sorted([d.name for d in html_dir.iterdir() if d.is_dir()])
    all_files = []
    for ds in datasets:
        ds_dir = html_dir / ds
        for f in sorted(ds_dir.glob("*.html")):
            all_files.append((ds, f))

    total = len(all_files)
    print(f"Webis Web Content Extraction Benchmark")
    print(f"Datasets: {len(datasets)} ({', '.join(datasets)})")
    print(f"Total files: {total}")
    print()

    # Per-dataset counters
    ds_counters = defaultdict(lambda: {
        "PASS": 0, "VALIDATION_ERROR": 0, "SCOPE_ERROR": 0,
        "EXTRACTION_FAIL": 0, "ERROR": 0, "total": 0,
        "extract": 0, "transform": 0,
        "word_counts": [], "section_counts": [],
    })
    overall = {
        "PASS": 0, "VALIDATION_ERROR": 0, "SCOPE_ERROR": 0,
        "EXTRACTION_FAIL": 0, "ERROR": 0,
        "extract": 0, "transform": 0,
    }

    results = {}
    error_groups = defaultdict(list)
    start_time = time.time()

    for i, (ds, filepath) in enumerate(all_files, 1):
        page_id = filepath.stem

        try:
            html = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            result = {
                "status": "ERROR",
                "mode": None,
                "section_count": 0,
                "output_word_count": 0,
                "error": f"Read error: {e}",
                "error_type": "IOError",
            }
            html = None

        if html is not None:
            result = run_one(html)

        result["file"] = filepath.name
        result["dataset"] = ds

        status = result["status"]
        overall[status] += 1
        ds_counters[ds][status] += 1
        ds_counters[ds]["total"] += 1

        if result["mode"]:
            overall[result["mode"]] += 1
            ds_counters[ds][result["mode"]] += 1

        if status == "PASS":
            ds_counters[ds]["word_counts"].append(result["output_word_count"])
            ds_counters[ds]["section_counts"].append(result["section_count"])

        if status != "PASS":
            short_msg = (result["error"] or "unknown")[:120]
            error_groups[short_msg].append((ds, page_id))

        results[f"{ds}/{page_id}"] = result

        # Progress every 100 files
        if i % 100 == 0 or i == total:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            print(f"  [{i:4d}/{total}]  {rate:.1f} files/sec  "
                  f"PASS={overall['PASS']}  FAIL={total - i + (i - overall['PASS'])}")

    elapsed = time.time() - start_time

    # Summary
    pass_count = overall["PASS"]
    val_err = overall["VALIDATION_ERROR"]
    scope_err = overall["SCOPE_ERROR"]
    extract_fail = overall["EXTRACTION_FAIL"]
    error_count = overall["ERROR"]
    all_validation = val_err + scope_err + extract_fail

    print()
    print("=" * 72)
    print("OVERALL SUMMARY")
    print("=" * 72)
    print(f"  Total files:          {total}")
    print(f"  PASS:                 {pass_count:4d}  ({100*pass_count/total:.1f}%)")
    print(f"  VALIDATION_ERROR:     {all_validation:4d}  ({100*all_validation/total:.1f}%)")
    print(f"    - SCOPE_ERROR:      {scope_err:4d}")
    print(f"    - EXTRACTION_FAIL:  {extract_fail:4d}")
    print(f"    - Other:            {val_err:4d}")
    print(f"  ERROR:                {error_count:4d}  ({100*error_count/total:.1f}%)")
    print(f"  Time:                 {elapsed:.1f}s ({total/elapsed:.1f} files/sec)")
    print()
    print(f"  Mode breakdown:")
    print(f"    extract:            {overall['extract']:4d}")
    print(f"    transform:          {overall['transform']:4d}")

    # PASS stats
    all_wc = []
    all_sc = []
    for ds in datasets:
        all_wc.extend(ds_counters[ds]["word_counts"])
        all_sc.extend(ds_counters[ds]["section_counts"])
    if all_wc:
        print()
        print(f"  PASS output stats:")
        print(f"    Mean word count:    {sum(all_wc)/len(all_wc):.0f}")
        print(f"    Median word count:  {sorted(all_wc)[len(all_wc)//2]}")
        print(f"    Mean sections:      {sum(all_sc)/len(all_sc):.1f}")
        print(f"    Median sections:    {sorted(all_sc)[len(all_sc)//2]}")

    # Per-dataset table
    print()
    print("=" * 72)
    print("PER-DATASET BREAKDOWN")
    print("=" * 72)
    print(f"  {'Dataset':<22s} {'Total':>5s} {'PASS':>5s} {'Rate':>6s} "
          f"{'Scope':>5s} {'ExtFl':>5s} {'ValEr':>5s} {'Error':>5s}")
    print(f"  {'-'*22} {'-'*5} {'-'*5} {'-'*6} {'-'*5} {'-'*5} {'-'*5} {'-'*5}")
    for ds in datasets:
        c = ds_counters[ds]
        t = c["total"]
        p = c["PASS"]
        rate = f"{100*p/t:.1f}%" if t > 0 else "N/A"
        print(f"  {ds:<22s} {t:5d} {p:5d} {rate:>6s} "
              f"{c['SCOPE_ERROR']:5d} {c['EXTRACTION_FAIL']:5d} "
              f"{c['VALIDATION_ERROR']:5d} {c['ERROR']:5d}")

    # Per-dataset mode breakdown
    print()
    print(f"  {'Dataset':<22s} {'Extract':>7s} {'Transform':>9s}")
    print(f"  {'-'*22} {'-'*7} {'-'*9}")
    for ds in datasets:
        c = ds_counters[ds]
        print(f"  {ds:<22s} {c['extract']:7d} {c['transform']:9d}")

    # Failure analysis
    print()
    print("=" * 72)
    print("TOP FAILURE PATTERNS")
    print("=" * 72)
    sorted_errors = sorted(error_groups.items(), key=lambda x: -len(x[1]))
    for msg, entries in sorted_errors[:10]:
        ds_breakdown = defaultdict(int)
        for ds, _ in entries:
            ds_breakdown[ds] += 1
        ds_str = ", ".join(f"{d}:{n}" for d, n in sorted(ds_breakdown.items(), key=lambda x: -x[1]))
        print(f"\n  [{len(entries)}x] {msg}")
        print(f"       datasets: {ds_str}")
        for ds, pid in entries[:3]:
            print(f"       {ds}/{pid[:16]}...")

    # Save results
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "wceb_results.json"

    # Strip word_counts/section_counts from serializable counters
    ds_summary = {}
    for ds in datasets:
        c = ds_counters[ds]
        ds_summary[ds] = {
            "total": c["total"],
            "PASS": c["PASS"],
            "VALIDATION_ERROR": c["VALIDATION_ERROR"],
            "SCOPE_ERROR": c["SCOPE_ERROR"],
            "EXTRACTION_FAIL": c["EXTRACTION_FAIL"],
            "ERROR": c["ERROR"],
            "extract": c["extract"],
            "transform": c["transform"],
        }

    report = {
        "total": total,
        "elapsed_seconds": round(elapsed, 1),
        "overall": {
            "PASS": pass_count,
            "VALIDATION_ERROR": val_err,
            "SCOPE_ERROR": scope_err,
            "EXTRACTION_FAIL": extract_fail,
            "ERROR": error_count,
        },
        "mode_breakdown": {
            "extract": overall["extract"],
            "transform": overall["transform"],
        },
        "per_dataset": ds_summary,
        "results": results,
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nResults saved to: {report_path}")


if __name__ == "__main__":
    main()
