"""
Comprehensive structural audit of ScrapingHub and WCEB benchmark corpora.

Phase 1: Raw HTML scan (pre-pipeline) — element counts and patterns.
Phase 2: Pipeline analysis — Document model inspection after Decant processing.

Usage:
    python tests/benchmark-structural/run_structural_audit.py
"""

import gzip
import statistics
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Decant imports for Phase 2
from decant.core.content_selector import detect_mode
from decant.core.parser import (
    parse,
    extract_with_trafilatura,
    harvest_captions,
    ValidationError,
)
from decant.core.renderer import render
from decant.core.model import (
    Document, Section, Paragraph, ListBlock, Quote, Preformatted, Image,
    Text, Emphasis, Strong, Code, Link, LineBreak,
)

# ---------------------------------------------------------------------------
# Corpus locations
# ---------------------------------------------------------------------------

BASE = Path(__file__).resolve().parent.parent.parent.parent
SCRAPINGHUB_DIR = BASE / "article-extraction-benchmark" / "html"
WCEB_DIR = BASE / "web-content-extraction-benchmark" / "datasets" / "combined" / "html"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def progress(phase, i, total, start_time):
    elapsed = time.time() - start_time
    pct = (i / total * 100) if total else 0
    print(
        f"  [{phase}] {i}/{total} ({pct:.0f}%) - {elapsed:.0f}s elapsed",
        file=sys.stderr,
        flush=True,
    )


def collect_files():
    """Return list of (path, is_gzip, corpus_name) tuples."""
    files = []
    if SCRAPINGHUB_DIR.exists():
        for p in sorted(SCRAPINGHUB_DIR.glob("*.html.gz")):
            files.append((p, True, "scrapinghub"))
    if WCEB_DIR.exists():
        for p in sorted(WCEB_DIR.rglob("*.html")):
            files.append((p, False, "wceb"))
    return files


def read_html(path, is_gzip):
    if is_gzip:
        with gzip.open(path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")
    return path.read_text(encoding="utf-8", errors="replace")


def _has_caption_class(tag):
    """Return True if tag has a class containing 'caption'."""
    classes = tag.get("class", [])
    return any("caption" in c.lower() for c in classes)


# ---------------------------------------------------------------------------
# Phase 1: Raw HTML scan
# ---------------------------------------------------------------------------

def empty_phase1_stats():
    return {
        "total_files": 0,
        "files_scanned": 0,
        "read_errors": 0,
        # Images
        "img_total": 0,
        "img_http_src": 0,
        "img_data_src": 0,
        "img_relative_src": 0,
        "img_no_src": 0,
        "img_has_alt": 0,
        "img_no_alt": 0,
        # Figures
        "figure_with_figcaption": 0,
        "figure_harvestable": 0,
        "caption_class_adjacent": 0,
        # Headings
        "files_with_headings": 0,
        "heading_level_counts": {i: 0 for i in range(1, 7)},
        "files_with_skipped_levels": 0,
        "files_with_multiple_h1": 0,
        # Lists
        "ul_total": 0,
        "ol_total": 0,
        "max_nesting_depths": [],  # per-file max depth
        "files_nesting_gt3": 0,
        # Definition lists
        "dl_total": 0,
        "files_with_dl": 0,
        "dl_dt_counts": [],  # dt count per dl
        "dl_dd_counts": [],  # dd count per dl
        # Blockquotes
        "blockquote_total": 0,
        "nested_blockquotes": 0,
    }


def merge_phase1(a, b):
    merged = {}
    for key in a:
        if key == "heading_level_counts":
            merged[key] = {i: a[key][i] + b[key][i] for i in range(1, 7)}
        elif isinstance(a[key], list):
            merged[key] = a[key] + b[key]
        else:
            merged[key] = a[key] + b[key]
    return merged


def scan_phase1_file(soup, stats):
    """Scan a single parsed file and update stats in place."""
    stats["files_scanned"] += 1

    # --- Images ---
    imgs = soup.find_all("img")
    stats["img_total"] += len(imgs)
    for img in imgs:
        src = img.get("src", "")
        alt = img.get("alt", "")
        if not src:
            stats["img_no_src"] += 1
        elif src.startswith(("http://", "https://")):
            stats["img_http_src"] += 1
        elif src.startswith("data:"):
            stats["img_data_src"] += 1
        else:
            stats["img_relative_src"] += 1

        if alt and alt.strip():
            stats["img_has_alt"] += 1
        else:
            stats["img_no_alt"] += 1

    # --- Figures ---
    for figure in soup.find_all("figure"):
        fc = figure.find("figcaption")
        if fc:
            stats["figure_with_figcaption"] += 1
            # Check harvestable: has http/https img + non-empty figcaption
            fig_img = figure.find("img")
            if fig_img:
                fig_src = fig_img.get("src", "")
                fc_text = fc.get_text(strip=True)
                if fig_src.startswith(("http://", "https://")) and fc_text:
                    stats["figure_harvestable"] += 1

    # --- Non-standard caption patterns ---
    for img in imgs:
        for sib in [img.next_sibling, img.previous_sibling]:
            if sib and hasattr(sib, "name") and sib.name in ("div", "span"):
                if _has_caption_class(sib):
                    stats["caption_class_adjacent"] += 1
                    break
        # Also check parent's next 2 siblings
        parent = img.parent
        if parent:
            count = 0
            sib = parent.next_sibling
            while sib and count < 2:
                if hasattr(sib, "name") and sib.name in ("div", "span"):
                    if _has_caption_class(sib):
                        stats["caption_class_adjacent"] += 1
                        break
                if hasattr(sib, "name"):
                    count += 1
                sib = sib.next_sibling if sib else None

    # --- Headings ---
    levels_found = set()
    for level in range(1, 7):
        tags = soup.find_all(f"h{level}")
        count = len(tags)
        stats["heading_level_counts"][level] += count
        if count > 0:
            levels_found.add(level)

    if levels_found:
        stats["files_with_headings"] += 1
        # Check for skipped levels
        sorted_levels = sorted(levels_found)
        skipped = False
        for i in range(len(sorted_levels) - 1):
            if sorted_levels[i + 1] - sorted_levels[i] > 1:
                skipped = True
                break
        if skipped:
            stats["files_with_skipped_levels"] += 1

    h1_count = len(soup.find_all("h1"))
    if h1_count > 1:
        stats["files_with_multiple_h1"] += 1

    # --- Lists ---
    uls = soup.find_all("ul")
    ols = soup.find_all("ol")
    stats["ul_total"] += len(uls)
    stats["ol_total"] += len(ols)

    # Max nesting depth
    max_depth = 0
    for lst in uls + ols:
        depth = 1
        parent = lst.parent
        while parent:
            if parent.name in ("ul", "ol"):
                depth += 1
            parent = parent.parent
        max_depth = max(max_depth, depth)
    stats["max_nesting_depths"].append(max_depth)
    if max_depth > 3:
        stats["files_nesting_gt3"] += 1

    # --- Definition lists ---
    dls = soup.find_all("dl")
    stats["dl_total"] += len(dls)
    if dls:
        stats["files_with_dl"] += 1
    for dl in dls:
        stats["dl_dt_counts"].append(len(dl.find_all("dt", recursive=False)))
        stats["dl_dd_counts"].append(len(dl.find_all("dd", recursive=False)))

    # --- Blockquotes ---
    bqs = soup.find_all("blockquote")
    stats["blockquote_total"] += len(bqs)
    for bq in bqs:
        if bq.find("blockquote"):
            stats["nested_blockquotes"] += 1


# ---------------------------------------------------------------------------
# Phase 2: Pipeline analysis
# ---------------------------------------------------------------------------

def empty_phase2_stats():
    return {
        "total_files": 0,
        "success": 0,
        "validation_errors": 0,
        "extraction_fails": 0,
        "other_errors": 0,
        # Images
        "image_objects": 0,
        "image_placeholders": 0,
        # Placeholders
        "table_placeholders": 0,
        "form_placeholders": 0,
        "hr_placeholders": 0,
        "other_placeholders": 0,
        # Paragraphs
        "total_paragraphs": 0,
        "total_placeholders_all": 0,
        "paragraph_counts": [],  # per-document
        "words_per_paragraph": [],  # per-paragraph
        "short_paragraphs": 0,  # < 5 words
        # Headings
        "output_heading_levels": {i: 0 for i in range(1, 7)},
        # Sections
        "section_counts": [],  # per-document
        "empty_sections": 0,
        # Lists
        "list_blocks": 0,
        "max_list_depths": [],  # per-document
        # Quotes
        "quote_blocks": 0,
    }


def _count_list_depth(block, depth=1):
    """Return max nesting depth of a ListBlock."""
    max_d = depth
    for item in block.items:
        for child in item.children:
            max_d = max(max_d, _count_list_depth(child, depth + 1))
    return max_d


def _walk_blocks(blocks):
    """Yield all blocks including those nested inside quotes."""
    for block in blocks:
        yield block
        if isinstance(block, Quote):
            yield from _walk_blocks(block.blocks)


def _plain_text(paragraph):
    """Extract plain text from paragraph inlines."""
    parts = []
    for inline in paragraph.inlines:
        if isinstance(inline, Text):
            parts.append(inline.text)
        elif isinstance(inline, (Emphasis, Strong)):
            for child in inline.children:
                if isinstance(child, Text):
                    parts.append(child.text)
        elif isinstance(inline, Code):
            parts.append(inline.text)
        elif isinstance(inline, Link):
            for child in inline.children:
                if isinstance(child, Text):
                    parts.append(child.text)
    return " ".join(parts)


def _is_placeholder_text(text):
    """Return True if text looks like a placeholder."""
    return text.startswith("[") and text.endswith("]")


def analyze_document(doc, stats):
    """Analyze a Document model and update stats."""
    stats["success"] += 1
    stats["section_counts"].append(len(doc.sections))

    doc_para_count = 0
    doc_max_list_depth = 0

    for section in doc.sections:
        # Check for empty sections
        if not section.blocks:
            stats["empty_sections"] += 1

        # Heading level
        level = section.heading.level
        if 1 <= level <= 6:
            stats["output_heading_levels"][level] += 1

        for block in _walk_blocks(section.blocks):
            if isinstance(block, Paragraph):
                doc_para_count += 1
                text = _plain_text(block)
                words = text.split()
                word_count = len(words)
                stats["words_per_paragraph"].append(word_count)

                if word_count < 5:
                    stats["short_paragraphs"] += 1

                # Check for placeholder
                if len(block.inlines) == 1 and isinstance(block.inlines[0], Text):
                    t = block.inlines[0].text
                    if _is_placeholder_text(t):
                        stats["total_placeholders_all"] += 1
                        if t.startswith("[Table"):
                            stats["table_placeholders"] += 1
                        elif t.startswith("[Image"):
                            stats["image_placeholders"] += 1
                        elif t.startswith("[Form"):
                            stats["form_placeholders"] += 1
                        elif t == "[-]":
                            stats["hr_placeholders"] += 1
                        else:
                            stats["other_placeholders"] += 1

            elif isinstance(block, Image):
                stats["image_objects"] += 1

            elif isinstance(block, ListBlock):
                stats["list_blocks"] += 1
                depth = _count_list_depth(block)
                doc_max_list_depth = max(doc_max_list_depth, depth)

            elif isinstance(block, Quote):
                stats["quote_blocks"] += 1

    stats["total_paragraphs"] += doc_para_count
    stats["paragraph_counts"].append(doc_para_count)
    stats["max_list_depths"].append(doc_max_list_depth)


def run_pipeline(html):
    """Run the full Decant pipeline. Returns Document or raises."""
    mode = detect_mode(html)

    original_title = None
    caption_map = None
    html_to_parse = html

    if mode == "extract":
        soup = BeautifulSoup(html, "lxml")
        original_title = soup.find("title")
        caption_map = harvest_captions(html)
        html_to_parse = extract_with_trafilatura(html)

    doc = parse(
        html_to_parse,
        original_title=original_title,
        require_article_body=(mode == "extract"),
        caption_map=caption_map,
    )
    return doc


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_phase1(name, stats):
    total = stats["files_scanned"]
    print(f"\n  --- {name} ({total} files) ---")
    print(f"  Read errors: {stats['read_errors']}")

    print(f"\n  Images:")
    print(f"    Total <img>:                {stats['img_total']}")
    print(f"    http/https src:             {stats['img_http_src']}")
    print(f"    data: src:                  {stats['img_data_src']}")
    print(f"    Relative src:               {stats['img_relative_src']}")
    print(f"    No src:                     {stats['img_no_src']}")
    print(f"    Has alt text:               {stats['img_has_alt']}")
    print(f"    Empty/missing alt:          {stats['img_no_alt']}")

    print(f"\n  Figures & Captions:")
    print(f"    <figure> with <figcaption>: {stats['figure_with_figcaption']}")
    print(f"    Harvestable (http img+fc):  {stats['figure_harvestable']}")
    print(f"    Non-standard caption class: {stats['caption_class_adjacent']}")

    print(f"\n  Headings:")
    print(f"    Files with headings:        {stats['files_with_headings']}")
    for lvl in range(1, 7):
        print(f"    h{lvl} elements:              {stats['heading_level_counts'][lvl]}")
    print(f"    Files with skipped levels:  {stats['files_with_skipped_levels']}")
    print(f"    Files with multiple h1:     {stats['files_with_multiple_h1']}")

    print(f"\n  Lists:")
    print(f"    <ul> elements:              {stats['ul_total']}")
    print(f"    <ol> elements:              {stats['ol_total']}")
    depths = stats["max_nesting_depths"]
    if depths:
        print(f"    Max nesting depth (max):    {max(depths)}")
        print(f"    Mean nesting depth:         {statistics.mean(depths):.1f}")
    print(f"    Files with depth > 3:       {stats['files_nesting_gt3']}")

    print(f"\n  Definition Lists:")
    print(f"    <dl> elements:              {stats['dl_total']}")
    print(f"    Files with <dl>:            {stats['files_with_dl']}")
    if stats["dl_dt_counts"]:
        print(f"    Avg dt per dl:              {statistics.mean(stats['dl_dt_counts']):.1f}")
        print(f"    Avg dd per dl:              {statistics.mean(stats['dl_dd_counts']):.1f}")

    print(f"\n  Blockquotes:")
    print(f"    Total <blockquote>:         {stats['blockquote_total']}")
    print(f"    Nested blockquotes:         {stats['nested_blockquotes']}")


def print_phase2(stats):
    total = stats["total_files"]
    ok = stats["success"]
    print(f"\n  Files processed:              {total}")
    print(f"  Successful:                   {ok}")
    print(f"  Validation errors:            {stats['validation_errors']}")
    print(f"  Extraction failures:          {stats['extraction_fails']}")
    print(f"  Other errors:                 {stats['other_errors']}")

    print(f"\n  Image Preservation:")
    img_obj = stats["image_objects"]
    img_ph = stats["image_placeholders"]
    img_total = img_obj + img_ph
    rate = (img_obj / img_total * 100) if img_total else 0
    print(f"    Image objects (preserved):  {img_obj}")
    print(f"    Image placeholders:         {img_ph}")
    print(f"    Preservation rate:          {rate:.1f}%")

    print(f"\n  Placeholders:")
    print(f"    Table:                      {stats['table_placeholders']}")
    print(f"    Image:                      {stats['image_placeholders']}")
    print(f"    Form:                       {stats['form_placeholders']}")
    print(f"    HR [-]:                     {stats['hr_placeholders']}")
    print(f"    Other:                      {stats['other_placeholders']}")
    tp = stats["total_paragraphs"]
    ph = stats["total_placeholders_all"]
    density = (ph / (tp + ph) * 100) if (tp + ph) else 0
    print(f"    Total placeholders:         {ph}")
    print(f"    Placeholder density:        {density:.1f}%")

    print(f"\n  Paragraphs:")
    print(f"    Total:                      {tp}")
    pc = stats["paragraph_counts"]
    if pc:
        print(f"    Per doc (mean):             {statistics.mean(pc):.1f}")
        print(f"    Per doc (median):           {statistics.median(pc):.0f}")
        sorted_pc = sorted(pc)
        p90_idx = int(len(sorted_pc) * 0.9)
        print(f"    Per doc (p90):              {sorted_pc[p90_idx] if sorted_pc else 0}")
    wpp = stats["words_per_paragraph"]
    if wpp:
        print(f"    Avg words per para:         {statistics.mean(wpp):.1f}")
    sp = stats["short_paragraphs"]
    sp_pct = (sp / tp * 100) if tp else 0
    print(f"    Short paras (< 5 words):    {sp} ({sp_pct:.1f}%)")

    print(f"\n  Headings (output model):")
    for lvl in range(1, 7):
        print(f"    h{lvl}:                       {stats['output_heading_levels'][lvl]}")

    print(f"\n  Sections:")
    sc = stats["section_counts"]
    if sc:
        print(f"    Per doc (mean):             {statistics.mean(sc):.1f}")
        print(f"    Per doc (median):           {statistics.median(sc):.0f}")
    print(f"    Empty sections:             {stats['empty_sections']}")

    print(f"\n  Lists:")
    print(f"    ListBlock objects:          {stats['list_blocks']}")
    mld = stats["max_list_depths"]
    if mld:
        nonzero = [d for d in mld if d > 0]
        if nonzero:
            print(f"    Max nesting depth:          {max(nonzero)}")

    print(f"\n  Quotes:")
    print(f"    Quote blocks:               {stats['quote_blocks']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    all_files = collect_files()
    total = len(all_files)
    print(f"Collected {total} files.", file=sys.stderr, flush=True)

    sh_files = [(p, gz, c) for p, gz, c in all_files if c == "scrapinghub"]
    wceb_files = [(p, gz, c) for p, gz, c in all_files if c == "wceb"]
    print(f"  ScrapingHub: {len(sh_files)}", file=sys.stderr, flush=True)
    print(f"  WCEB: {len(wceb_files)}", file=sys.stderr, flush=True)

    # ===================================================================
    # Phase 1
    # ===================================================================
    print(
        "\n=== PHASE 1: Raw HTML Scan ===",
        file=sys.stderr, flush=True,
    )
    start = time.time()

    sh_stats = empty_phase1_stats()
    sh_stats["total_files"] = len(sh_files)
    wceb_stats = empty_phase1_stats()
    wceb_stats["total_files"] = len(wceb_files)

    for i, (path, is_gzip, corpus) in enumerate(all_files, 1):
        if i % 100 == 0:
            progress("Phase 1", i, total, start)

        try:
            html = read_html(path, is_gzip)
        except Exception:
            if corpus == "scrapinghub":
                sh_stats["read_errors"] += 1
            else:
                wceb_stats["read_errors"] += 1
            continue

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            continue

        if corpus == "scrapinghub":
            scan_phase1_file(soup, sh_stats)
        else:
            scan_phase1_file(soup, wceb_stats)

    combined_p1 = merge_phase1(sh_stats, wceb_stats)

    print("\n" + "=" * 60)
    print("  RAW HTML SCAN")
    print("=" * 60)
    print_phase1("ScrapingHub", sh_stats)
    print_phase1("WCEB", wceb_stats)
    print_phase1("COMBINED", combined_p1)

    # ===================================================================
    # Phase 2
    # ===================================================================
    print(
        "\n=== PHASE 2: Pipeline Analysis ===",
        file=sys.stderr, flush=True,
    )
    start2 = time.time()

    p2 = empty_phase2_stats()
    p2["total_files"] = total

    for i, (path, is_gzip, corpus) in enumerate(all_files, 1):
        if i % 100 == 0:
            progress("Phase 2", i, total, start2)

        try:
            html = read_html(path, is_gzip)
        except Exception:
            p2["other_errors"] += 1
            continue

        try:
            doc = run_pipeline(html)
            analyze_document(doc, p2)
        except ValidationError as e:
            msg = str(e)
            if "No article body" in msg:
                p2["extraction_fails"] += 1
            else:
                p2["validation_errors"] += 1
        except Exception:
            p2["other_errors"] += 1

    print("\n" + "=" * 60)
    print("  PIPELINE ANALYSIS")
    print("=" * 60)
    print_phase2(p2)

    # ===================================================================
    # Image preservation comparison
    # ===================================================================
    print("\n" + "=" * 60)
    print("  IMAGE PRESERVATION")
    print("=" * 60)
    raw_imgs = combined_p1["img_total"]
    raw_http = combined_p1["img_http_src"]
    preserved = p2["image_objects"]
    ph_img = p2["image_placeholders"]
    print(f"  Raw <img> in source HTML:     {raw_imgs}")
    print(f"  Raw http/https src:           {raw_http}")
    print(f"  Preserved Image objects:      {preserved}")
    print(f"  Image placeholders:           {ph_img}")
    if raw_http:
        print(f"  Yield (preserved/raw http):   {preserved / raw_http * 100:.1f}%")

    # ===================================================================
    # Heading comparison
    # ===================================================================
    print("\n" + "=" * 60)
    print("  HEADING ANALYSIS")
    print("=" * 60)
    print(f"  {'Level':<8} {'Raw HTML':>10} {'Output Model':>14}")
    for lvl in range(1, 7):
        raw = combined_p1["heading_level_counts"][lvl]
        out = p2["output_heading_levels"][lvl]
        print(f"  h{lvl:<7} {raw:>10} {out:>14}")

    # ===================================================================
    # Key findings
    # ===================================================================
    print("\n" + "=" * 60)
    print("  KEY FINDINGS")
    print("=" * 60)

    # Image preservation
    if raw_http and preserved:
        yield_pct = preserved / raw_http * 100
        print(f"  - Image preservation yield: {yield_pct:.1f}% of http/https images survive pipeline")

    # Placeholder density
    tp = p2["total_paragraphs"]
    ph_all = p2["total_placeholders_all"]
    if tp + ph_all:
        density = ph_all / (tp + ph_all) * 100
        if density > 5:
            print(f"  - Placeholder density {density:.1f}% exceeds 5% threshold")
        else:
            print(f"  - Placeholder density {density:.1f}% is within acceptable range")

    # Short paragraphs
    if tp:
        sp_pct = p2["short_paragraphs"] / tp * 100
        if sp_pct > 5:
            print(f"  - Short paragraphs (<5 words): {sp_pct:.1f}% — may indicate fragmentation")

    # Heading level shift
    for lvl in range(1, 7):
        raw = combined_p1["heading_level_counts"][lvl]
        out = p2["output_heading_levels"][lvl]
        if raw > 0 and out > 0:
            ratio = out / raw
            if ratio < 0.5 or ratio > 2.0:
                print(f"  - h{lvl}: significant shift (raw {raw} -> output {out})")

    # Definition lists
    if combined_p1["dl_total"] > 0:
        print(f"  - {combined_p1['dl_total']} definition lists in source — currently unsupported")

    # Non-standard captions
    if combined_p1["caption_class_adjacent"] > 0:
        print(f"  - {combined_p1['caption_class_adjacent']} non-standard caption patterns (class-based) — harvester misses these")

    # Empty sections
    if p2["empty_sections"] > 0:
        print(f"  - {p2['empty_sections']} empty sections in output — should be 0 after pipeline")
    else:
        print(f"  - 0 empty sections in output (pipeline cleanup working)")

    # Pipeline success rate
    if total:
        success_pct = p2["success"] / total * 100
        print(f"  - Pipeline success rate: {success_pct:.1f}% ({p2['success']}/{total})")

    elapsed_total = time.time() - start
    print(
        f"\nDone. Total elapsed: {elapsed_total:.0f}s",
        file=sys.stderr, flush=True,
    )


if __name__ == "__main__":
    main()
