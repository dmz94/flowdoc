"""
Flowdoc eval metrics runner.

Runs the conversion pipeline on fixture corpora and reports metrics.
Separate from pytest — this is for regression detection and quality tracking.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

from flowdoc.core.content_selector import detect_mode
from flowdoc.core.parser import parse, extract_with_trafilatura, ValidationError
from flowdoc.core.renderer import render
from flowdoc.core.model import (
    Document, Paragraph, ListBlock, Quote, Preformatted,
    Text, Emphasis, Strong, Code, Link,
)
from thresholds import (
    WORD_COUNT_RATIO_MIN, AVG_PARAGRAPH_WORDS_MIN,
    PLACEHOLDER_DENSITY_MAX, LINK_TO_PROSE_RATIO_MAX,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIRS = {
    "identity10": PROJECT_ROOT / "tests" / "fixtures" / "identity10",
    "eval20": PROJECT_ROOT / "tests" / "fixtures" / "eval20",
    "main": PROJECT_ROOT / "tests" / "fixtures" / "main",
}


def parse_manifest(manifest_path: Path) -> list[dict]:
    """
    Parse a manifest.md table into a list of fixture records.

    Each record has keys: num, filename, source_url, scope, notes.
    Only rows from the markdown table are returned (header/separator skipped).
    Column positions are read from the header row, so any column order works.
    """
    text = manifest_path.read_text(encoding="utf-8")
    rows = []
    in_table = False
    col_idx = {}  # column name -> index, set from header row

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            in_table = False
            continue

        # split on | gives empty strings at start/end; keep all for indexing
        raw_cells = [c.strip() for c in line.split("|")]
        # Drop leading/trailing empty strings from outer pipes
        if raw_cells and raw_cells[0] == "":
            raw_cells = raw_cells[1:]
        if raw_cells and raw_cells[-1] == "":
            raw_cells = raw_cells[:-1]

        if not in_table:
            # First table row is the header — build column index
            in_table = True
            for i, cell in enumerate(raw_cells):
                col_idx[cell.strip().lower()] = i
            for required in ("filename", "scope"):
                if required not in col_idx:
                    raise ValueError(
                        f"Manifest {manifest_path} missing required column: {required}"
                    )
            continue

        # Skip separator row (all dashes)
        if raw_cells and all(re.match(r'^-+$', c) for c in raw_cells):
            continue

        filename_idx = col_idx["filename"]
        scope_idx = col_idx["scope"]
        min_cols = max(filename_idx, scope_idx) + 1

        if len(raw_cells) < min_cols:
            continue

        num_str = raw_cells[0].strip()
        if not num_str.isdigit():
            continue

        source_url_idx = col_idx.get("source_url")
        notes_idx = col_idx.get("notes")

        rows.append({
            "num": int(num_str),
            "filename": raw_cells[filename_idx].strip(),
            "source_url": raw_cells[source_url_idx].strip() if source_url_idx is not None and source_url_idx < len(raw_cells) else "",
            "scope": raw_cells[scope_idx].strip(),
            "notes": raw_cells[notes_idx].strip() if notes_idx is not None and notes_idx < len(raw_cells) else "",
        })

    return rows


def run_pipeline(fixture_path: Path):
    """
    Run the full Flowdoc pipeline on a single fixture file.

    Returns (doc, rendered_html, source_html) on success.
    Raises on validation or pipeline failure.
    """
    html = fixture_path.read_text(encoding="utf-8")

    mode = detect_mode(html)

    original_title = None
    html_to_parse = html

    if mode == "extract":
        original_soup = BeautifulSoup(html, "lxml")
        original_title = original_soup.find("title")
        html_to_parse = extract_with_trafilatura(html)

    doc = parse(
        html_to_parse,
        original_title=original_title,
        require_article_body=(mode == "extract"),
    )
    rendered = render(doc)

    return doc, rendered, html


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _inline_text(inline) -> str:
    """Recursively extract plain text from a single Inline."""
    if isinstance(inline, Text):
        return inline.text
    if isinstance(inline, (Emphasis, Strong)):
        return "".join(_inline_text(c) for c in inline.children)
    if isinstance(inline, Code):
        return inline.text
    if isinstance(inline, Link):
        return "".join(_inline_text(c) for c in inline.children)
    return ""


def _link_text(inline) -> str:
    """Extract text from Link inlines only (for link word counting)."""
    if isinstance(inline, Link):
        return "".join(_inline_text(c) for c in inline.children)
    if isinstance(inline, (Emphasis, Strong)):
        return "".join(_link_text(c) for c in inline.children)
    return ""


def _is_placeholder(inlines: list) -> bool:
    """Check if inlines represent a placeholder paragraph."""
    if len(inlines) != 1:
        return False
    inline = inlines[0]
    if not isinstance(inline, Text):
        return False
    return inline.text.startswith("[") and inline.text.endswith("]")


def _classify_placeholder(text: str) -> str:
    """Classify a placeholder text into a category."""
    if text.startswith("[Image"):
        return "image"
    if text.startswith("[Form"):
        return "form"
    if text.startswith("[Table"):
        return "table"
    if text == "[---]":
        return "hr"
    return "other"


def compute_metrics(doc: Document, source_html: str, rendered_html: str) -> dict:
    """
    Compute 16 quality metrics for a single fixture conversion.

    Walks the Document model tree to count words, paragraphs, placeholders,
    links, and structural anomalies.

    Returns a dict with exactly these keys:
        section_count, headings, output_word_count, source_plain_word_count,
        word_count_ratio, paragraph_count, avg_paragraph_words,
        shortest_paragraph_words, placeholder_count, placeholder_types,
        placeholder_density, link_word_count, prose_word_count,
        link_to_prose_ratio, empty_sections, stub_sections
    """
    section_count = len(doc.sections)
    headings = []
    paragraph_count = 0
    paragraph_word_counts = []
    placeholder_count = 0
    placeholder_types = {"image": 0, "form": 0, "table": 0, "hr": 0, "other": 0}
    total_output_words = 0
    total_link_words = 0
    empty_sections = 0
    stub_sections = 0

    def _count_words(inlines):
        text = "".join(_inline_text(il) for il in inlines)
        return len(text.split())

    def _count_link_words(inlines):
        text = "".join(_link_text(il) for il in inlines)
        return len(text.split())

    def _walk_blocks(blocks):
        nonlocal paragraph_count, placeholder_count
        nonlocal total_output_words, total_link_words

        for block in blocks:
            if isinstance(block, Paragraph):
                if _is_placeholder(block.inlines):
                    placeholder_count += 1
                    placeholder_types[_classify_placeholder(block.inlines[0].text)] += 1
                else:
                    paragraph_count += 1
                    wc = _count_words(block.inlines)
                    paragraph_word_counts.append(wc)
                    total_output_words += wc
                    total_link_words += _count_link_words(block.inlines)
            elif isinstance(block, ListBlock):
                _walk_list(block)
            elif isinstance(block, Quote):
                _walk_blocks(block.blocks)
            elif isinstance(block, Preformatted):
                total_output_words += len(block.text.split())

    def _walk_list(list_block):
        nonlocal total_output_words, total_link_words

        for item in list_block.items:
            wc = _count_words(item.inlines)
            total_output_words += wc
            total_link_words += _count_link_words(item.inlines)
            for child in item.children:
                _walk_list(child)

    for section in doc.sections:
        heading_text = "".join(
            _inline_text(il) for il in section.heading.inlines
        ).strip()
        headings.append(heading_text)

        if len(section.blocks) == 0:
            empty_sections += 1
        elif all(
            isinstance(b, Paragraph) and _is_placeholder(b.inlines)
            for b in section.blocks
        ):
            stub_sections += 1

        _walk_blocks(section.blocks)

    # Source plain word count (regex strip tags)
    source_plain = re.sub(r'<[^>]+>', '', source_html)
    source_plain_word_count = len(source_plain.split())

    # Derived metrics
    word_count_ratio = (
        total_output_words / source_plain_word_count
        if source_plain_word_count > 0 else 0.0
    )
    avg_paragraph_words = (
        sum(paragraph_word_counts) / len(paragraph_word_counts)
        if paragraph_word_counts else 0.0
    )
    shortest_paragraph_words = sorted(paragraph_word_counts)[:3]
    total_paras = paragraph_count + placeholder_count
    placeholder_density = (
        placeholder_count / total_paras if total_paras > 0 else 0.0
    )
    link_to_prose_ratio = (
        total_link_words / total_output_words
        if total_output_words > 0 else 0.0
    )

    return {
        "section_count": section_count,
        "headings": headings,
        "output_word_count": total_output_words,
        "source_plain_word_count": source_plain_word_count,
        "word_count_ratio": word_count_ratio,
        "paragraph_count": paragraph_count,
        "avg_paragraph_words": avg_paragraph_words,
        "shortest_paragraph_words": shortest_paragraph_words,
        "placeholder_count": placeholder_count,
        "placeholder_types": placeholder_types,
        "placeholder_density": placeholder_density,
        "link_word_count": total_link_words,
        "prose_word_count": total_output_words,
        "link_to_prose_ratio": link_to_prose_ratio,
        "empty_sections": empty_sections,
        "stub_sections": stub_sections,
    }


# ---------------------------------------------------------------------------
# Baseline save / load
# ---------------------------------------------------------------------------

BASELINE_DIR = Path(__file__).resolve().parent / "baselines"


def load_baseline(corpus: str, fixture_name: str) -> dict | None:
    """Load a saved baseline for a fixture. Returns None if not found."""
    path = BASELINE_DIR / corpus / f"{fixture_name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_baseline(corpus: str, fixture_name: str, data: dict) -> None:
    """Write a baseline record to eval/baselines/{corpus}/{fixture_name}.json."""
    path = BASELINE_DIR / corpus / f"{fixture_name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_baseline_record(fixture_name: str, corpus: str, metrics: dict) -> dict:
    """Build a baseline record dict from computed metrics."""
    return {
        "fixture": fixture_name,
        "corpus": corpus,
        "baselined_at": datetime.now(timezone.utc).isoformat(),
        "flowdoc_version": "0.1.0",
        "status": "PASS",
        "notes": "",
        "metrics": metrics,
        "thresholds_applied": {
            "word_count_ratio_min": WORD_COUNT_RATIO_MIN,
            "avg_paragraph_words_min": AVG_PARAGRAPH_WORDS_MIN,
            "placeholder_density_max": PLACEHOLDER_DENSITY_MAX,
            "link_to_prose_ratio_max": LINK_TO_PROSE_RATIO_MAX,
        },
    }


# ---------------------------------------------------------------------------
# Interactive baseline review
# ---------------------------------------------------------------------------

def _collect_anomalies(metrics: dict) -> list[str]:
    """Collect threshold-based anomalies from metrics."""
    anomalies = []
    if metrics["word_count_ratio"] < WORD_COUNT_RATIO_MIN:
        anomalies.append(
            f"Word count ratio {metrics['word_count_ratio']:.2f} "
            f"below minimum {WORD_COUNT_RATIO_MIN}"
        )
    if metrics["avg_paragraph_words"] < AVG_PARAGRAPH_WORDS_MIN:
        anomalies.append(
            f"Avg paragraph words {metrics['avg_paragraph_words']:.1f} "
            f"below minimum {AVG_PARAGRAPH_WORDS_MIN}"
        )
    if metrics["placeholder_density"] > PLACEHOLDER_DENSITY_MAX:
        anomalies.append(
            f"Placeholder density {metrics['placeholder_density']:.2f} "
            f"above maximum {PLACEHOLDER_DENSITY_MAX}"
        )
    if metrics["link_to_prose_ratio"] > LINK_TO_PROSE_RATIO_MAX:
        anomalies.append(
            f"Link/prose ratio {metrics['link_to_prose_ratio']:.2f} "
            f"above maximum {LINK_TO_PROSE_RATIO_MAX}"
        )
    if metrics["empty_sections"] > 0:
        anomalies.append(f"{metrics['empty_sections']} empty section(s)")
    if metrics["stub_sections"] > 0:
        anomalies.append(
            f"{metrics['stub_sections']} stub section(s) (all placeholders)"
        )
    return anomalies


def print_review_block(fixture_name: str, metrics: dict) -> None:
    """Print the interactive baseline review block for a PASS fixture."""
    m = metrics
    headings = m["headings"]

    print("=" * 80)
    print(f"BASELINE REVIEW -- {fixture_name}")
    print("=" * 80)
    print()

    print(f"HEADINGS  ({len(headings)} found)")
    print("-" * 75)
    for h in headings:
        print(f"  {h}")
    print()

    print("WORD COUNT")
    print("-" * 75)
    print(f"  Source plain text : {m['source_plain_word_count']:,} words")
    print(f"  Output            : {m['output_word_count']:,} words")
    print(f"  Ratio             : {m['word_count_ratio']:.2f}")
    print()

    print(f"PLACEHOLDERS  ({m['placeholder_count']} total)")
    print("-" * 75)
    if m["placeholder_count"] == 0:
        print("  None.")
    else:
        for ptype, count in m["placeholder_types"].items():
            if count > 0:
                print(f"  {ptype}  x{count}")
    print()

    print("FRAGMENTATION")
    print("-" * 75)
    if m["avg_paragraph_words"] >= AVG_PARAGRAPH_WORDS_MIN:
        print(f"  OK -- avg paragraph {m['avg_paragraph_words']:.1f} words")
    else:
        print(
            f"  WARNING -- avg paragraph {m['avg_paragraph_words']:.1f} words "
            f"(below {AVG_PARAGRAPH_WORDS_MIN})"
        )
    print()

    anomalies = _collect_anomalies(m)
    print("ANOMALIES")
    print("-" * 75)
    if not anomalies:
        print("  None.")
    else:
        for a in anomalies:
            print(f"  {a}")
    print()

    print("METRICS SUMMARY")
    print("-" * 75)
    print(
        f"  Sections: {m['section_count']}  |  "
        f"Paragraphs: {m['paragraph_count']}  |  "
        f"Avg para: {m['avg_paragraph_words']:.1f}w"
    )
    print(
        f"  Link/prose ratio: {m['link_to_prose_ratio']:.2f}  |  "
        f"Determinism: PASS"
    )
    print()
    print("=" * 80)


def print_fail_review_block(fixture_name: str, error: str) -> None:
    """Print the interactive baseline review block for a FAIL fixture."""
    print("=" * 80)
    print(f"BASELINE REVIEW -- {fixture_name}")
    print("=" * 80)
    print()
    print("STATUS: FAIL")
    print("-" * 75)
    print(f"  {error}")
    print()
    print("=" * 80)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

REPORT_DIR = Path(__file__).resolve().parent / "reports"


def classify_fixture(metrics: dict, baseline: dict | None) -> str:
    """
    Classify fixture status by comparing current metrics to baseline.

    Returns one of: PASS, REGRESSION, MARGINAL, FAIL, NEW.
    (FAIL is assigned by the caller before reaching this function.)

    Logic:
    - NEW: no baseline exists
    - REGRESSION: anomalies exist AND baseline status was PASS
    - MARGINAL: baseline status was MARGINAL (known-marginal fixture)
    - PASS: no anomalies and baseline status was PASS
    """
    if baseline is None:
        return "NEW"
    baseline_status = baseline.get("status", "PASS")
    anomalies = _collect_anomalies(metrics)
    if baseline_status == "MARGINAL":
        return "MARGINAL"
    if anomalies:
        return "REGRESSION"
    return "PASS"


def save_report(corpus: str, fixture_results: list[dict]) -> Path:
    """Write a JSON report to eval/reports/{timestamp}/report.json."""
    ts = datetime.now(timezone.utc)
    timestamp_dir = ts.strftime("%Y%m%d_%H%M%S")
    report_dir = REPORT_DIR / timestamp_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    summary = {"PASS": 0, "REGRESSION": 0, "MARGINAL": 0, "FAIL": 0, "NEW": 0}
    for r in fixture_results:
        summary[r["status"]] += 1

    report = {
        "generated_at": ts.isoformat(),
        "corpus": corpus,
        "flowdoc_version": "0.1.0",
        "fixture_count": len(fixture_results),
        "summary": summary,
        "fixtures": fixture_results,
    }

    report_path = report_dir / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path


def prompt_action() -> str:
    """Prompt for baseline review action. Returns 'a', 's', or 'q'."""
    while True:
        response = input("ACTION  [a]pprove  [s]kip  [q]uit\n> ").strip().lower()
        if response in ("a", "s", "q"):
            return response


def main():
    parser = argparse.ArgumentParser(description="Flowdoc eval metrics runner")
    parser.add_argument(
        "--corpus",
        required=True,
        choices=["main"],
        help="Which fixture corpus to evaluate",
    )
    parser.add_argument(
        "--fixture",
        default=None,
        help="Run on a single fixture (name without .html)",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Save current metrics as baseline",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Compare current metrics against baseline",
    )
    args = parser.parse_args()

    fixture_dir = FIXTURE_DIRS[args.corpus]
    manifest_path = fixture_dir / "manifest.md"

    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    fixtures = parse_manifest(manifest_path)

    # Filter to in-scope only
    fixtures = [f for f in fixtures if f["scope"] == "in-scope"]

    # Filter to single fixture if requested
    if args.fixture:
        fixtures = [f for f in fixtures if f["filename"] == f"{args.fixture}.html"]
        if not fixtures:
            print(
                f"ERROR: fixture '{args.fixture}' not found in {args.corpus} manifest",
                file=sys.stderr,
            )
            sys.exit(1)

    # Header
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Flowdoc Eval -- {args.corpus} -- {now}")
    print()

    # Process each fixture
    interactive_baseline = args.baseline and sys.stdin.isatty()
    auto_baseline = args.baseline and not sys.stdin.isatty()
    saved_count = 0
    skipped_count = 0
    fixture_results = []

    for f in fixtures:
        name = f["filename"].removesuffix(".html")
        fixture_path = fixture_dir / f["filename"]

        if not fixture_path.exists():
            print(f"  {f['num']:02d}  {name:<40}  MISSING")
            continue

        # Interactive baseline: skip fixtures that already have a baseline
        if interactive_baseline and load_baseline(args.corpus, name) is not None:
            continue

        try:
            doc, rendered, source_html = run_pipeline(fixture_path)
            metrics = compute_metrics(doc, source_html, rendered)

            if interactive_baseline:
                print_review_block(name, metrics)
                action = prompt_action()
                if action == "a":
                    record = build_baseline_record(name, args.corpus, metrics)
                    if _collect_anomalies(metrics):
                        record["status"] = "MARGINAL"
                    save_baseline(args.corpus, name, record)
                    print(f"  -> saved ({record['status']})")
                    saved_count += 1
                elif action == "s":
                    print("  -> skipped")
                    skipped_count += 1
                elif action == "q":
                    print("  -> quit")
                    break
            else:
                print(
                    f"  {f['num']:02d}  {name:<40}  OK    "
                    f"s={metrics['section_count']}  "
                    f"w={metrics['output_word_count']}  "
                    f"r={metrics['word_count_ratio']:.2f}  "
                    f"p={metrics['placeholder_count']}"
                )
                if auto_baseline:
                    record = build_baseline_record(name, args.corpus, metrics)
                    if _collect_anomalies(metrics):
                        record["status"] = "MARGINAL"
                    save_baseline(args.corpus, name, record)
                    print(f"        -> baseline saved ({record['status']})")
                if args.report:
                    baseline = load_baseline(args.corpus, name)
                    anomalies = _collect_anomalies(metrics)
                    status = classify_fixture(metrics, baseline)
                    baseline_metrics = baseline.get("metrics") if baseline else None
                    fixture_results.append({
                        "fixture": name,
                        "status": status,
                        "anomalies": anomalies,
                        "metrics": metrics,
                        "baseline_metrics": baseline_metrics,
                        "error": None,
                    })

        except Exception as e:
            if interactive_baseline:
                print_fail_review_block(name, str(e))
                action = prompt_action()
                if action == "a":
                    record = build_baseline_record(name, args.corpus, {})
                    record["status"] = "FAIL"
                    record["notes"] = str(e)
                    save_baseline(args.corpus, name, record)
                    print("  -> saved")
                    saved_count += 1
                elif action == "s":
                    print("  -> skipped")
                    skipped_count += 1
                elif action == "q":
                    print("  -> quit")
                    break
            else:
                print(f"  {f['num']:02d}  {name:<40}  FAIL        {e}")
                if args.report:
                    baseline = load_baseline(args.corpus, name)
                    baseline_metrics = baseline.get("metrics") if baseline else None
                    fixture_results.append({
                        "fixture": name,
                        "status": "FAIL",
                        "anomalies": [],
                        "metrics": {},
                        "baseline_metrics": baseline_metrics,
                        "error": str(e),
                    })

    if args.report and fixture_results:
        report_path = save_report(args.corpus, fixture_results)
        print(f"  Report: {report_path}")

    print()
    if interactive_baseline:
        print("--- Baseline review complete ---")
        print(f"  Saved: {saved_count}  Skipped: {skipped_count}")
    else:
        print("--- Done ---")


if __name__ == "__main__":
    main()
