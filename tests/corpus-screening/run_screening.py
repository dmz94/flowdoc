"""
Corpus screening tool for Decant.

Compares source HTML fixtures against their converted output and generates
side-by-side review pages with flagged items for human review. Pure
programmatic comparison -- no AI involved.

Usage:
    python tests/corpus-screening/run_screening.py
    python tests/corpus-screening/run_screening.py --select-fixture nhs-dyslexia
    python tests/corpus-screening/run_screening.py --select-category health
"""
import argparse
import html as html_module
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from decant.core.content_selector import detect_mode
from decant.core.parser import parse, extract_with_trafilatura
from decant.core.renderer import render
from decant.core.model import (
    Document, Paragraph, ListBlock, Quote, Preformatted,
    Table, Image, Text, Emphasis, Strong, Code, Link,
)
from decant.core.degradation import _is_simple_table


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCREENING_DIR = Path(__file__).resolve().parent
AUDIT_DIR = SCREENING_DIR.parent / "pipeline-audit"
FIXTURE_DIR = AUDIT_DIR / "test-pages"
REVIEW_DIR = SCREENING_DIR / "review"


# ---------------------------------------------------------------------------
# Boilerplate heading patterns (normalized, lowercase)
# ---------------------------------------------------------------------------

BOILERPLATE_HEADINGS_EXACT = {
    "related articles", "related stories", "related", "more stories",
    "read more", "recommended", "trending", "popular", "comments",
    "join the discussion", "leave a comment", "subscribe",
    "newsletter", "get more", "sign up", "follow us", "follow",
    "connect", "share", "share this", "share this story", "tags",
    "categories", "topics", "advertisement", "sponsored", "ad",
    "about us", "contact", "privacy policy", "terms", "cookie",
    "cookies", "advertise", "for musicians", "for members",
    "more access", "install", "previous", "next", "previous / next",
    "quick links", "resources", "is this page useful",
    "thank you", "thank you for your feedback",
    "sorry something went wrong", "fuel", "donate", "support",
    "go ad free", "premium", "welcome", "notification", "portals",
    "join", "view sources", "references", "more in", "also in",
    "next article", "comment on", "use your social network",
    "discover more", "find even more", "prepare for your trip",
    "help us improve", "get more of a good thing", "blogchains",
    "meta", "sections", "for ieee members", "ieee spectrum",
    "follow ieee spectrum", "support ieee spectrum",
    "more from", "more esp", "join the conversation",
    "subscriber only", "subscriber-only content",
    "ready for more", "discussion about this post",
    "latest in", "you might also like",
    "we care about your privacy", "from mayo clinic",
    "better health starts here", "care at", "experts you can trust",
    "fuel groundbreaking", "associated procedures",
    "mayo clinic press", "more serious eats recipes",
    "healthier families", "be active for your mental health",
    "listen to the", "about this classroom resource",
}

BOILERPLATE_HEADINGS_PREFIX = [
    "more from", "more esp", "more in", "also in", "enjoy more",
    "saving articles", "the institute", "downloading",
    "access to", "following topics", "adding your response",
    "create an account", "join the world", "select your free",
    "we and our partners", "discover more", "find even more",
]

BOILERPLATE_HEADINGS_CONTAINS = [
    "subscribe", "newsletter", "sign up", "cookie",
    "privacy", "account", "log in", "members", "membership",
    "exclusive for", "requires an", "create an account",
]


def _is_boilerplate_heading(normalized: str) -> bool:
    """Check if a normalized heading matches known boilerplate patterns."""
    if not normalized:
        return True
    if normalized in BOILERPLATE_HEADINGS_EXACT:
        return True
    for prefix in BOILERPLATE_HEADINGS_PREFIX:
        if normalized.startswith(prefix):
            return True
    for phrase in BOILERPLATE_HEADINGS_CONTAINS:
        if phrase in normalized:
            return True
    return False


# ---------------------------------------------------------------------------
# Manifest parsing (duplicated from run_metrics.py to avoid cross-dir imports)
# ---------------------------------------------------------------------------

def parse_manifest(manifest_path: Path) -> list[dict]:
    """Parse manifest.md table into a list of fixture records."""
    text = manifest_path.read_text(encoding="utf-8")
    rows = []
    in_table = False
    col_idx = {}

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            in_table = False
            continue

        raw_cells = [c.strip() for c in line.split("|")]
        if raw_cells and raw_cells[0] == "":
            raw_cells = raw_cells[1:]
        if raw_cells and raw_cells[-1] == "":
            raw_cells = raw_cells[:-1]

        if not in_table:
            in_table = True
            for i, cell in enumerate(raw_cells):
                col_idx[cell.strip().lower()] = i
            for required in ("filename", "scope"):
                if required not in col_idx:
                    raise ValueError(
                        f"Manifest {manifest_path} missing required column: {required}"
                    )
            continue

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
        category_idx = col_idx.get("category")

        rows.append({
            "num": int(num_str),
            "filename": raw_cells[filename_idx].strip(),
            "source_url": raw_cells[source_url_idx].strip() if source_url_idx is not None and source_url_idx < len(raw_cells) else "",
            "scope": raw_cells[scope_idx].strip(),
            "notes": raw_cells[notes_idx].strip() if notes_idx is not None and notes_idx < len(raw_cells) else "",
            "category": raw_cells[category_idx].strip() if category_idx is not None and category_idx < len(raw_cells) else "",
        })

    return rows


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(fixture_path: Path):
    """Run the Decant pipeline. Returns (doc, rendered_html, source_html)."""
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
# Inline text extraction (same pattern as run_metrics.py)
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


def _count_words(inlines):
    text = "".join(_inline_text(il) for il in inlines)
    return len(text.split())


def _is_placeholder(inlines: list) -> bool:
    if len(inlines) != 1:
        return False
    inline = inlines[0]
    if not isinstance(inline, Text):
        return False
    return inline.text.startswith("[") and inline.text.endswith("]")


# ---------------------------------------------------------------------------
# Source analysis
# ---------------------------------------------------------------------------

def analyze_source(source_html: str) -> dict:
    """Analyze source HTML for images, tables, and headings."""
    soup = BeautifulSoup(source_html, "lxml")

    # Images
    images = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "")
        # Check if inside figure with figcaption
        parent_figure = img.find_parent("figure")
        has_figcaption = False
        figcaption_text = ""
        if parent_figure:
            fc = parent_figure.find("figcaption")
            if fc:
                has_figcaption = True
                figcaption_text = fc.get_text(strip=True)
        images.append({
            "src": src,
            "alt": alt,
            "has_figcaption": has_figcaption,
            "figcaption_text": figcaption_text,
        })

    # Tables
    tables = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        row_count = len(rows)
        col_count = 0
        for row in rows:
            cells = row.find_all(["td", "th"])
            col_count = max(col_count, len(cells))
        is_simple = _is_simple_table(table)
        tables.append({
            "row_count": row_count,
            "col_count": col_count,
            "is_simple": is_simple,
        })

    # Headings (skip nav, header, footer, aside)
    skip_parents = {"nav", "header", "footer", "aside"}
    headings = []
    for level in range(1, 7):
        for h in soup.find_all(f"h{level}"):
            # Check if inside a skip-parent
            in_skip = False
            for parent in h.parents:
                if parent.name in skip_parents:
                    in_skip = True
                    break
            if not in_skip:
                headings.append({
                    "level": level,
                    "text": h.get_text(strip=True),
                })

    return {
        "images": images,
        "tables": tables,
        "headings": headings,
    }


# ---------------------------------------------------------------------------
# Output analysis
# ---------------------------------------------------------------------------

def analyze_output(doc: Document) -> dict:
    """Walk the Document model to extract images, tables, headings, placeholders, sections."""
    images = []
    rendered_tables = 0
    placeholdered_tables = []
    headings = []
    placeholders = []
    sections = []

    for section in doc.sections:
        heading_text = "".join(
            _inline_text(il) for il in section.heading.inlines
        ).strip()
        heading_level = section.heading.level
        headings.append({"level": heading_level, "text": heading_text})

        section_words = 0

        for block in section.blocks:
            if isinstance(block, Image):
                images.append({
                    "src": block.src,
                    "has_caption": bool(block.caption),
                })
            elif isinstance(block, Table):
                rendered_tables += 1
            elif isinstance(block, Paragraph):
                if _is_placeholder(block.inlines):
                    ph_text = block.inlines[0].text
                    placeholders.append({
                        "text": ph_text,
                        "section": heading_text,
                    })
                    if ph_text.startswith("[Table"):
                        placeholdered_tables.append({
                            "text": ph_text,
                            "section": heading_text,
                        })
                else:
                    section_words += _count_words(block.inlines)
            elif isinstance(block, ListBlock):
                section_words += _count_list_words(block)
            elif isinstance(block, Quote):
                section_words += _count_block_words(block.blocks)
            elif isinstance(block, Preformatted):
                section_words += len(block.text.split())

        sections.append({
            "heading": heading_text,
            "word_count": section_words,
        })

    return {
        "images": images,
        "rendered_tables": rendered_tables,
        "placeholdered_tables": placeholdered_tables,
        "headings": headings,
        "placeholders": placeholders,
        "sections": sections,
    }


def _count_list_words(list_block: ListBlock) -> int:
    total = 0
    for item in list_block.items:
        total += _count_words(item.inlines)
        for child in item.children:
            total += _count_list_words(child)
    return total


def _count_block_words(blocks) -> int:
    total = 0
    for block in blocks:
        if isinstance(block, Paragraph):
            if not _is_placeholder(block.inlines):
                total += _count_words(block.inlines)
        elif isinstance(block, ListBlock):
            total += _count_list_words(block)
        elif isinstance(block, Quote):
            total += _count_block_words(block.blocks)
        elif isinstance(block, Preformatted):
            total += len(block.text.split())
    return total


# ---------------------------------------------------------------------------
# Comparison / flag generation
# ---------------------------------------------------------------------------

def _normalize_heading(text: str) -> str:
    """Normalize heading text for fuzzy comparison.

    Lowercase, strip, collapse whitespace, remove hyphens/colons/em dashes,
    strip emoji and non-alphanumeric symbols.
    """
    t = text.lower().strip()
    # Replace common separators with space
    t = re.sub(r'[\-\u2013\u2014:]+', ' ', t)
    # Remove non-breaking spaces and other unicode whitespace
    t = re.sub(r'[\u00a0\u200b]+', ' ', t)
    # Strip emoji and symbols: keep only alphanumeric, spaces, and basic punctuation
    t = re.sub(r'[^\w\s.,;:!?\'\-]', '', t, flags=re.UNICODE)
    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def generate_flags(source: dict, output: dict) -> dict:
    """Compare source and output analyses, return categorized flags."""
    flags = {
        "images": [],
        "tables": [],
        "headings": [],
        "sections": [],
        "placeholders": [],
    }
    # Track boilerplate suppression count for display
    flags["_boilerplate_suppressed"] = 0

    # --- Images ---
    src_img_count = len(source["images"])
    out_img_count = len(output["images"])
    image_placeholders = [p for p in output["placeholders"] if p["text"].startswith("[Image")]

    survived = out_img_count
    placeholdered = len(image_placeholders)

    if src_img_count > 0:
        flags["images"].append(
            f"{survived} of {src_img_count} source images survived"
            + (f", {placeholdered} placeholder" if placeholdered else "")
        )

    for ph in image_placeholders:
        flags["images"].append(
            f'Lost: {ph["text"]} near "{ph["section"]}"'
        )

    # Check for figcaption loss: source images with figcaption that survived
    # but output image has no caption
    for src_img in source["images"]:
        if src_img["has_figcaption"]:
            # See if any output image matches and lacks caption
            # Simple heuristic: if fewer output images have captions than
            # source images have figcaptions, flag it
            pass  # Hard to match 1:1 without URL matching; flag summary instead

    src_with_figcaption = sum(1 for img in source["images"] if img["has_figcaption"])
    out_with_caption = sum(1 for img in output["images"] if img["has_caption"])
    if src_with_figcaption > out_with_caption and out_img_count > 0:
        flags["images"].append(
            f"Caption loss: {src_with_figcaption} source images had figcaption, "
            f"only {out_with_caption} output images have caption"
        )

    # --- Tables ---
    src_table_count = len(source["tables"])
    out_rendered = output["rendered_tables"]
    out_placeholdered_tables = output["placeholdered_tables"]

    if src_table_count > 0:
        flags["tables"].append(
            f"{out_rendered} of {src_table_count} source tables rendered, "
            f"{len(out_placeholdered_tables)} placeholdered"
        )

    for i, ph in enumerate(out_placeholdered_tables):
        detail = ph["text"]
        section = ph["section"]
        # Check if corresponding source table was simple
        simple_note = ""
        if i < len(source["tables"]):
            if source["tables"][i]["is_simple"]:
                simple_note = " (source table was simple -- could have been rendered)"
        flags["tables"].append(
            f'{detail} in "{section}"{simple_note}'
        )

    # --- Headings ---
    src_headings_norm = [(h["text"], _normalize_heading(h["text"])) for h in source["headings"]]
    out_headings_norm = [(h["text"], _normalize_heading(h["text"])) for h in output["headings"]]

    out_norm_set = {norm for _, norm in out_headings_norm}
    src_norm_set = {norm for _, norm in src_headings_norm}

    boilerplate_suppressed = 0
    missing = []
    for raw, norm in src_headings_norm:
        if norm in out_norm_set:
            continue
        if any(norm in on or on in norm for on in out_norm_set if norm and on):
            continue
        # Check boilerplate before flagging as missing
        if _is_boilerplate_heading(norm):
            boilerplate_suppressed += 1
            continue
        missing.append(raw)

    extra = []
    for raw, norm in out_headings_norm:
        if norm in src_norm_set:
            continue
        if any(norm in sn or sn in norm for sn in src_norm_set if norm and sn):
            continue
        extra.append(raw)

    flags["_boilerplate_suppressed"] = boilerplate_suppressed

    if missing:
        for h in missing:
            flags["headings"].append(f'Missing: "{h}"')
    if extra:
        for h in extra:
            flags["headings"].append(f'Extra (possible boilerplate): "{h}"')

    # --- Sections ---
    for sec in output["sections"]:
        if sec["word_count"] < 20:
            flags["sections"].append(
                f'Short section: "{sec["heading"]}" has only {sec["word_count"]} words'
            )

    # --- Placeholders (exclude image placeholders, already in IMAGES) ---
    for ph in output["placeholders"]:
        if not ph["text"].startswith("[Image"):
            flags["placeholders"].append(
                f'{ph["text"]} in "{ph["section"]}"'
            )

    return flags


def count_flags(flags: dict) -> int:
    """Count total flags across all categories."""
    return sum(len(v) for k, v in flags.items() if not k.startswith("_"))


# ---------------------------------------------------------------------------
# Terminal output
# ---------------------------------------------------------------------------

def print_screening(name: str, source: dict, output: dict, flags: dict):
    """Print screening results to terminal."""
    total = count_flags(flags)

    print("=" * 61)
    print(f"SCREENING: {name}")
    print("=" * 61)
    print()

    # Images
    src_img_count = len(source["images"])
    out_img_count = len(output["images"])
    image_phs = len([p for p in output["placeholders"] if p["text"].startswith("[Image")])
    print("IMAGES")
    print(f"  Source: {src_img_count} | Output: {out_img_count} survived, {image_phs} placeholder")
    for f in flags["images"]:
        if f.startswith(str(out_img_count)):
            continue  # Skip the summary line, already printed above
        print(f"  >> {f}")
    print()

    # Tables
    src_tbl_count = len(source["tables"])
    out_rendered = output["rendered_tables"]
    out_ph_tbl = len(output["placeholdered_tables"])
    print("TABLES")
    print(f"  Source: {src_tbl_count} | Output: {out_rendered} rendered, {out_ph_tbl} placeholder")
    for f in flags["tables"]:
        if f.startswith(str(out_rendered)):
            continue  # Skip the summary line
        print(f"  >> {f}")
    print()

    # Headings
    src_h_count = len(source["headings"])
    out_h_count = len(output["headings"])
    boilerplate_count = flags.get("_boilerplate_suppressed", 0)
    print("HEADINGS")
    print(f"  Source: {src_h_count} | Output: {out_h_count}")
    if boilerplate_count > 0:
        print(f"  ({boilerplate_count} boilerplate headings suppressed)")
    for f in flags["headings"]:
        print(f"  >> {f}")
    print()

    # Sections
    print("SECTIONS")
    if flags["sections"]:
        for f in flags["sections"]:
            print(f"  >> {f}")
    else:
        print("  All sections have >= 20 words")
    print()

    # Placeholders (image placeholders excluded)
    print("PLACEHOLDERS")
    if flags["placeholders"]:
        for i, f in enumerate(flags["placeholders"], 1):
            print(f"  {i}. {f}")
    else:
        print("  None (image placeholders listed above)")
    print()

    print(f"FLAGS: {total} items to review")
    print("=" * 61)
    print()


# ---------------------------------------------------------------------------
# HTML review page generation
# ---------------------------------------------------------------------------

def generate_review_page(
    name: str,
    source_url: str,
    source_html: str,
    rendered_html: str,
    flags: dict,
    prev_name: str | None,
    next_name: str | None,
) -> str:
    """Generate a single fixture review HTML page."""
    total = count_flags(flags)
    boilerplate_count = flags.get("_boilerplate_suppressed", 0)

    # Build flags panel HTML
    flags_html_parts = []
    for category, items in flags.items():
        if category.startswith("_"):
            continue
        if not items and category != "headings":
            continue
        cat_label = category.upper()
        flags_html_parts.append(f'<h3>{cat_label}</h3>')
        if category == "headings" and boilerplate_count > 0:
            flags_html_parts.append(
                f'<p class="boilerplate-note">{boilerplate_count} boilerplate headings suppressed</p>'
            )
        for item in items:
            escaped = html_module.escape(item)
            flags_html_parts.append(
                f'<label class="flag-item">'
                f'<input type="checkbox"> {escaped}'
                f'</label>'
            )
    flags_panel = "\n".join(flags_html_parts) if flags_html_parts else "<p>No flags.</p>"

    # Navigation links
    nav_parts = []
    if prev_name:
        nav_parts.append(f'<a href="{prev_name}.html">&larr; Previous</a>')
    else:
        nav_parts.append('<span class="nav-disabled">&larr; Previous</span>')
    nav_parts.append('<a href="index.html">Index</a>')
    if next_name:
        nav_parts.append(f'<a href="{next_name}.html">Next &rarr;</a>')
    else:
        nav_parts.append('<span class="nav-disabled">Next &rarr;</span>')
    nav_html = " | ".join(nav_parts)

    # Escape both HTML strings for srcdoc
    source_srcdoc_escaped = html_module.escape(source_html)
    output_srcdoc_escaped = html_module.escape(rendered_html)

    source_link = ""
    escaped_url = ""
    if source_url:
        escaped_url = html_module.escape(source_url)
        source_link = f'<a href="{escaped_url}" target="_blank" rel="noopener">{escaped_url}</a>'

    # Live page link for left panel footer
    live_link = ""
    if source_url:
        live_link = f'<a href="{escaped_url}" target="_blank" rel="noopener">Open live page in new tab</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Screening: {html_module.escape(name)}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: system-ui, -apple-system, sans-serif; font-size: 14px; color: #333; }}

.top-bar {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: #f5f5f5; border-bottom: 1px solid #ddd;
  padding: 12px 20px;
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}}
.top-bar h1 {{ font-size: 16px; font-weight: 700; }}
.top-bar .source-url {{ font-size: 12px; color: #666; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 400px; }}
.top-bar .source-url a {{ color: #1856a8; text-decoration: none; }}
.top-bar .source-url a:hover {{ text-decoration: underline; }}
.badge {{ background: #e65100; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; }}
.badge.zero {{ background: #4caf50; }}
.nav {{ margin-left: auto; font-size: 13px; }}
.nav a {{ color: #1856a8; text-decoration: none; }}
.nav a:hover {{ text-decoration: underline; }}
.nav-disabled {{ color: #aaa; }}

.flags-panel {{
  position: fixed; top: 52px; left: 0; right: 0; z-index: 90;
  background: #fff8e1; border-bottom: 1px solid #e0d6a8;
  padding: 12px 20px;
  max-height: 40vh; overflow-y: auto;
}}
.flags-panel h3 {{ font-size: 13px; font-weight: 700; margin: 10px 0 4px; text-transform: uppercase; color: #6d5e00; }}
.flags-panel h3:first-child {{ margin-top: 0; }}
.flag-item {{ display: block; font-size: 13px; padding: 3px 0; cursor: pointer; }}
.flag-item input {{ margin-right: 6px; }}
.boilerplate-note {{ font-size: 12px; color: #888; font-style: italic; margin: 2px 0 4px; }}
.toggle-btn {{
  position: fixed; z-index: 95; right: 20px;
  background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px;
  padding: 4px 10px; font-size: 12px; cursor: pointer;
}}

.main-area {{
  display: flex; height: 100vh;
}}
.panel {{
  flex: 1; display: flex; flex-direction: column;
  overflow: hidden; border-right: 1px solid #ddd;
}}
.panel:last-child {{ border-right: none; }}
.panel iframe {{
  flex: 1; width: 100%; border: none;
}}
.panel-header {{
  padding: 6px 12px;
  background: #f0f0f0; border-bottom: 1px solid #ddd;
  font-size: 12px; font-weight: 600; color: #555;
  text-transform: uppercase; letter-spacing: 0.03em;
}}
.panel-footer {{
  padding: 4px 12px;
  background: #f9f9f9; border-top: 1px solid #eee;
  font-size: 11px; color: #888;
}}
.panel-footer a {{ color: #1856a8; text-decoration: none; }}
.panel-footer a:hover {{ text-decoration: underline; }}

@media (max-width: 768px) {{
  .main-area {{ flex-direction: column; }}
  .panel {{ flex: none; height: 50vh; }}
}}
</style>
</head>
<body>

<div class="top-bar">
  <h1>{html_module.escape(name)}</h1>
  <div class="source-url">{source_link}</div>
  <span class="badge{' zero' if total == 0 else ''}">{total} flag{"s" if total != 1 else ""}</span>
  <div class="nav">{nav_html}</div>
</div>

<div class="flags-panel" id="flags-panel">
{flags_panel}
</div>

<div class="main-area" id="main-area">
  <div class="panel">
    <div class="panel-header">Source HTML</div>
    <iframe srcdoc="{source_srcdoc_escaped}"></iframe>
    <div class="panel-footer">{live_link}</div>
  </div>
  <div class="panel">
    <div class="panel-header">Decant Output</div>
    <iframe srcdoc="{output_srcdoc_escaped}"></iframe>
  </div>
</div>

<button class="toggle-btn" id="toggle-flags" style="top: 56px;">Hide flags</button>

<script>
(function() {{
  var panel = document.getElementById("flags-panel");
  var btn = document.getElementById("toggle-flags");
  var main = document.getElementById("main-area");
  btn.addEventListener("click", function() {{
    if (panel.style.display === "none") {{
      panel.style.display = "";
      btn.textContent = "Hide flags";
    }} else {{
      panel.style.display = "none";
      btn.textContent = "Show flags";
    }}
  }});
}})();
</script>

</body>
</html>"""


def generate_error_review_page(
    name: str,
    source_url: str,
    error: str,
    prev_name: str | None,
    next_name: str | None,
) -> str:
    """Generate a review page for a fixture that errored during pipeline."""
    nav_parts = []
    if prev_name:
        nav_parts.append(f'<a href="{prev_name}.html">&larr; Previous</a>')
    else:
        nav_parts.append('<span style="color:#aaa">&larr; Previous</span>')
    nav_parts.append('<a href="index.html">Index</a>')
    if next_name:
        nav_parts.append(f'<a href="{next_name}.html">Next &rarr;</a>')
    else:
        nav_parts.append('<span style="color:#aaa">Next &rarr;</span>')
    nav_html = " | ".join(nav_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Screening: {html_module.escape(name)} (ERROR)</title>
<style>
body {{ font-family: system-ui, sans-serif; padding: 2rem; color: #333; }}
h1 {{ font-size: 1.2rem; margin-bottom: 1rem; }}
.error {{ background: #fce4ec; border: 1px solid #e57373; padding: 1rem; border-radius: 4px; margin: 1rem 0; }}
.nav {{ margin-top: 1rem; font-size: 13px; }}
.nav a {{ color: #1856a8; text-decoration: none; }}
</style>
</head>
<body>
<h1>Screening: {html_module.escape(name)}</h1>
<div class="error"><strong>Pipeline error:</strong> {html_module.escape(error)}</div>
<div class="nav">{nav_html}</div>
</body>
</html>"""


def generate_index_page(results: list[dict]) -> str:
    """Generate the index.html listing all screened fixtures."""
    # Sort by flag count descending
    sorted_results = sorted(results, key=lambda r: r["flag_count"], reverse=True)

    rows = []
    for r in sorted_results:
        name = r["name"]
        flag_count = r["flag_count"]
        source_url = r.get("source_url", "")
        error = r.get("error")
        status = "ERROR" if error else "OK"

        escaped_url = html_module.escape(source_url)
        url_display = escaped_url[:80] + "..." if len(source_url) > 80 else escaped_url

        rows.append(
            f'<tr>'
            f'<td><a href="{name}.html">{html_module.escape(name)}</a></td>'
            f'<td class="flag-count">{flag_count}</td>'
            f'<td>{status}</td>'
            f'<td class="url-cell"><a href="{escaped_url}" target="_blank" rel="noopener">{url_display}</a></td>'
            f'</tr>'
        )

    rows_html = "\n".join(rows)
    total_flags = sum(r["flag_count"] for r in results)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corpus Screening Index</title>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; background: #f5f5f5; color: #333; margin: 0; padding: 2rem 1rem; }}
.card {{ max-width: 1000px; margin: 0 auto; background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); padding: 2rem; }}
h1 {{ font-size: 1.3rem; margin: 0 0 0.5rem; }}
.summary {{ font-size: 0.9rem; color: #666; margin-bottom: 1.5rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f9f9f9; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #555; }}
.flag-count {{ text-align: center; font-weight: 600; }}
.url-cell {{ font-size: 0.75rem; word-break: break-all; color: #555; }}
a {{ color: #1856a8; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div class="card">
<h1>Corpus Screening Index</h1>
<p class="summary">{len(results)} fixtures screened. {total_flags} total flags. Sorted by flag count (most first).</p>
<table>
<tr><th>Fixture</th><th>Flags</th><th>Status</th><th>Source URL</th></tr>
{rows_html}
</table>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Decant corpus screening tool")
    parser.add_argument(
        "--select-fixture",
        default=None,
        dest="select_fixture",
        help="Screen a single fixture (name without .html)",
    )
    parser.add_argument(
        "--select-category",
        default=None,
        dest="select_category",
        help="Filter by category column in manifest",
    )
    args = parser.parse_args()

    # Ensure stdout can handle Unicode on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    manifest_path = AUDIT_DIR / "manifest.md"
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    fixtures = parse_manifest(manifest_path)
    fixtures = [f for f in fixtures if f["scope"] == "in-scope"]

    # Filter by fixture name
    if args.select_fixture:
        fixtures = [f for f in fixtures if f["filename"] == f"{args.select_fixture}.html"]
        if not fixtures:
            print(f"ERROR: fixture '{args.select_fixture}' not found in manifest", file=sys.stderr)
            sys.exit(1)

    # Filter by category
    if args.select_category:
        has_category = any(f.get("category") for f in fixtures)
        if not has_category:
            print("WARNING: manifest has no 'category' column; --select-category ignored", file=sys.stderr)
        else:
            fixtures = [f for f in fixtures if f.get("category", "").lower() == args.select_category.lower()]
            if not fixtures:
                print(f"ERROR: no fixtures match category '{args.select_category}'", file=sys.stderr)
                sys.exit(1)

    if not fixtures:
        print("No fixtures to screen.", file=sys.stderr)
        sys.exit(1)

    # Ensure review directory exists
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # Process fixtures
    results = []  # For index generation
    fixture_names = [f["filename"].removesuffix(".html") for f in fixtures]
    total_flags = 0

    for i, f in enumerate(fixtures):
        name = f["filename"].removesuffix(".html")
        source_url = f["source_url"]
        fixture_path = FIXTURE_DIR / f["filename"]

        prev_name = fixture_names[i - 1] if i > 0 else None
        next_name = fixture_names[i + 1] if i < len(fixtures) - 1 else None

        if not fixture_path.exists():
            print(f"  {name:<40}  MISSING (file not found)")
            results.append({
                "name": name,
                "source_url": source_url,
                "flag_count": 0,
                "error": "fixture file not found",
            })
            page = generate_error_review_page(name, source_url, "Fixture file not found", prev_name, next_name)
            (REVIEW_DIR / f"{name}.html").write_text(page, encoding="utf-8")
            continue

        try:
            doc, rendered, source_html = run_pipeline(fixture_path)
            source_analysis = analyze_source(source_html)
            output_analysis = analyze_output(doc)
            flags = generate_flags(source_analysis, output_analysis)
            flag_count = count_flags(flags)
            total_flags += flag_count

            print_screening(name, source_analysis, output_analysis, flags)

            page = generate_review_page(name, source_url, source_html, rendered, flags, prev_name, next_name)
            (REVIEW_DIR / f"{name}.html").write_text(page, encoding="utf-8")

            results.append({
                "name": name,
                "source_url": source_url,
                "flag_count": flag_count,
                "error": None,
            })

        except Exception as e:
            print(f"  {name:<40}  ERROR: {e}")
            results.append({
                "name": name,
                "source_url": source_url,
                "flag_count": 0,
                "error": str(e),
            })
            page = generate_error_review_page(name, source_url, str(e), prev_name, next_name)
            (REVIEW_DIR / f"{name}.html").write_text(page, encoding="utf-8")

    # Generate index
    index_page = generate_index_page(results)
    (REVIEW_DIR / "index.html").write_text(index_page, encoding="utf-8")

    print()
    print(f"Screened {len(results)} fixtures. Total flags: {total_flags}.")
    print(f"Review pages: tests/corpus-screening/review/index.html")


if __name__ == "__main__":
    main()
