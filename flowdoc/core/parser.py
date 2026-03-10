"""
HTML to Document model parser.

Converts sanitized DOM tree to internal model representation.
Pipeline: Step 4 (after sanitization and content selection)
See decisions.md sections 5-8 for parsing rules.
"""
import re
from typing import Literal

import trafilatura

# ExtractionMode controls which Trafilatura parameter set is used.
# "baseline" is and must remain the current production behavior.
ExtractionMode = Literal["baseline", "precision", "recall"]

from bs4 import BeautifulSoup, Tag, NavigableString

from flowdoc.core.model import (
    Document, Section, Heading, Block, Inline,
    Paragraph, ListBlock, ListItem, Quote, Preformatted, Image,
    Text, Emphasis, Strong, Code, Link, LineBreak
)
from flowdoc.core.sanitizer import sanitize
from flowdoc.core.content_selector import select_main_content
from flowdoc.core.degradation import (
    degrade_table, degrade_image, degrade_form, degrade_hr
)


class ValidationError(Exception):
    """Raised when input HTML lacks required semantic structure."""
    pass


def harvest_captions(html: str) -> dict[str, str]:
    """
    Scan raw HTML before Trafilatura runs, build a map of
    img src URL -> figcaption plain text.

    Rules:
    - Only considers <figure> elements containing exactly one <img>
      with an http/https src and a non-empty <figcaption>.
    - Ambiguous figures (multiple images, no image, data URIs) are skipped.
    - Safe to call on any HTML. No exceptions, no side effects.
    """
    from urllib.parse import urlparse
    soup = BeautifulSoup(html, "lxml")
    result: dict[str, str] = {}
    for figure in soup.find_all("figure"):
        figcaption = figure.find("figcaption")
        if not figcaption:
            continue
        caption_text = figcaption.get_text(separator=" ", strip=True)
        if not caption_text:
            continue
        imgs = figure.find_all("img")
        http_imgs = [
            img for img in imgs
            if img.get("src", "").strip()
            and urlparse(img["src"].strip()).scheme in ("http", "https")
        ]
        if len(http_imgs) != 1:
            continue
        result[http_imgs[0]["src"].strip()] = caption_text
    return result


# ---------------------------------------------------------------------------
# Tail boilerplate trim (end-anchored)
# ---------------------------------------------------------------------------
# CMS sites sometimes append footer/social paragraphs after legitimate article
# content that Trafilatura does not strip (e.g. Cleveland Clinic: "Follow
# Cleveland Clinic", "Blog, News & Apps", "Site Information & Policies").
#
# Heuristic: scan the last _TAIL_SCAN_LIMIT blocks of the final section.
# When an anchor pattern is found, remove that block AND everything after it.
# End-anchored by construction: blocks before the anchor are never touched.

_TAIL_BOILERPLATE_ANCHORS = frozenset([
    "Follow Cleveland Clinic",
])

_TAIL_SCAN_LIMIT = 10  # never scan further than this from the end


def _inline_to_text(inline: "Inline") -> str:
    """Recursively extract plain text from a single Inline for pattern matching."""
    if isinstance(inline, Text):
        return inline.text
    if isinstance(inline, (Emphasis, Strong)):
        return "".join(_inline_to_text(c) for c in inline.children)
    if isinstance(inline, Code):
        return inline.text
    if isinstance(inline, Link):
        return "".join(_inline_to_text(c) for c in inline.children)
    return ""  # LineBreak and unknowns contribute no text


def _paragraph_plain_text(para: Paragraph) -> str:
    """Return the plain-text content of a Paragraph for boilerplate matching."""
    return "".join(_inline_to_text(il) for il in para.inlines).strip()


def trim_trailing_boilerplate(sections: list[Section]) -> list[Section]:
    """
    Remove trailing CMS footer paragraphs from the last section.

    Scans up to _TAIL_SCAN_LIMIT blocks from the end of the final section.
    When an anchor pattern is found, that block and all blocks after it are
    removed.  Blocks before the anchor are preserved intact.

    End-anchored: never removes content from the middle of a document.
    Called after build_sections(), before render.
    """
    if not sections:
        return sections

    last = sections[-1]
    blocks = last.blocks
    if not blocks:
        return sections

    tail_start = max(0, len(blocks) - _TAIL_SCAN_LIMIT)
    cut_at = None

    for i in range(len(blocks) - 1, tail_start - 1, -1):
        block = blocks[i]
        if isinstance(block, Paragraph):
            text = _paragraph_plain_text(block)
            for pattern in _TAIL_BOILERPLATE_ANCHORS:
                if pattern in text:
                    cut_at = i
                    break

    if cut_at is not None:
        sections = list(sections)  # do not mutate the input list
        sections[-1] = Section(heading=last.heading, blocks=list(blocks[:cut_at]))

    return sections


def drop_trailing_orphan_section(sections: list[Section]) -> list[Section]:
    """
    Drop the final section if it meets either of two end-anchored conditions:

    1. Zero content blocks (bare heading stub — existing behaviour).
    2. All blocks are placeholder tokens: every block is a Paragraph whose
       sole inline is a bracketed placeholder text such as '[Form omitted]',
       '[Image omitted]', or '[Image: ...]'.  These sections contain no
       article prose and are unambiguously CMS template artefacts.

    End-anchored: only ever inspects the last section, so legitimate content
    earlier in the document is never affected.  Structural check only — no
    site-specific strings.

    Called after trim_trailing_boilerplate() (which may itself empty the last
    section's block list), before render.
    """
    if not sections:
        return sections
    last = sections[-1]
    if len(last.blocks) == 0:
        return sections[:-1]
    if last.blocks and all(_is_placeholder_paragraph(b) for b in last.blocks):
        return sections[:-1]
    return sections


def _normalize_str(s: str) -> str:
    """Collapse whitespace, strip, and lowercase a plain text string."""
    return re.sub(r'\s+', ' ', s).strip().lower()


def _normalize_heading_text(heading) -> str:
    """
    Return normalized heading text: strip, collapse internal whitespace,
    lowercase.  Used for consecutive duplicate detection.
    """
    raw = "".join(_inline_to_text(il) for il in heading.inlines)
    return _normalize_str(raw)


def drop_duplicate_consecutive_sections(sections: list[Section]) -> list[Section]:
    """
    Drop any section whose normalized heading text is identical to the
    immediately preceding section's normalized heading text.

    Only adjacent (consecutive) duplicates are removed.  Non-consecutive
    duplicate headings are left untouched.  Structural only — no
    site-specific strings.

    Called after collapse_consecutive_placeholder_blocks(), before render.
    """
    if not sections:
        return sections
    result = [sections[0]]
    for section in sections[1:]:
        if _normalize_heading_text(section.heading) != _normalize_heading_text(result[-1].heading):
            result.append(section)
    return result


def drop_empty_sections(sections: list[Section]) -> list[Section]:
    """
    Remove any section with zero content blocks.

    A heading with no paragraphs, lists, images, or other
    blocks beneath it is structural noise — either a
    title-duplicate artifact (section 0 matching <title>)
    or a source heading whose content was lost in extraction.

    Applied globally, not just end-anchored. Safe because
    empty sections by definition contain no prose or media.
    """
    return [s for s in sections if len(s.blocks) > 0]


def _is_placeholder_paragraph(block) -> bool:
    """
    Return True if block is a single-inline Paragraph whose text is a known
    placeholder token: [Form omitted], [Image not included], or [Image: <alt>].

    These are generated by degradation.py and are structurally inert when
    they appear in consecutive runs.
    """
    from flowdoc.core.model import Paragraph, Text as TextInline
    if not isinstance(block, Paragraph):
        return False
    if len(block.inlines) != 1:
        return False
    inline = block.inlines[0]
    if not isinstance(inline, TextInline):
        return False
    t = inline.text
    return t.startswith("[") and t.endswith("]")


def collapse_consecutive_placeholder_blocks(sections: list[Section]) -> list[Section]:
    """
    Collapse runs of N>=2 consecutive identical placeholder Paragraphs within
    each section's block list to a single instance.

    'Identical' means the full placeholder text matches (e.g. all six
    consecutive '[Form omitted]' blocks become one).  Non-placeholder blocks
    and runs of length 1 are left untouched.

    Called after drop_trailing_orphan_section(), before render.
    """
    result = []
    for section in sections:
        collapsed: list = []
        for block in section.blocks:
            if (
                _is_placeholder_paragraph(block)
                and collapsed
                and _is_placeholder_paragraph(collapsed[-1])
                and collapsed[-1].inlines[0].text == block.inlines[0].text
            ):
                # Same placeholder as previous — skip (deduplicate)
                continue
            collapsed.append(block)
        result.append(Section(heading=section.heading, blocks=collapsed))
    return result


_ARTICLE_BODY_MIN_WORDS = 20


def _has_article_body(sections: list[Section]) -> bool:
    """
    Return True if the document contains at least one non-placeholder
    Paragraph with >= _ARTICLE_BODY_MIN_WORDS words of prose text.

    Placeholder paragraphs (bracketed tokens like '[Form omitted]',
    '[Image omitted]', etc.) are excluded from the count.  Headings and
    list blocks are not counted.

    Used to detect extraction failure where Trafilatura captured navigation
    or boilerplate instead of article content.
    """
    from flowdoc.core.model import Paragraph as ParagraphModel
    for section in sections:
        for block in section.blocks:
            if not isinstance(block, ParagraphModel):
                continue
            if _is_placeholder_paragraph(block):
                continue
            text = "".join(_inline_to_text(il) for il in block.inlines)
            if len(text.split()) >= _ARTICLE_BODY_MIN_WORDS:
                return True
    return False


# Minimum prose characters (after stripping tags) to accept a headingless
# Trafilatura extraction instead of falling back to the full original HTML.
# Both guardian (32 K) and theringer (18 K) clear this by a wide margin;
# a genuine empty/navigation-only extraction is well below it.
_MIN_PROSE_CHARS = 2000


def _extract_title_string(html: str) -> str:
    """
    Extract and normalise the text content of the <title> tag from a raw
    HTML string.  Returns an empty string if no <title> is found.

    Used to supply a synthetic heading when Trafilatura produces headingless
    prose output (see extract_with_trafilatura).
    """
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return re.sub(r'\s+', ' ', m.group(1)).strip()


def _strip_title_branding(title: str | None) -> str | None:
    """
    Strip site-branding suffix from a page title string.

    Tries delimiters in priority order: ' | ', ' - ', ' -- '.
    For the first delimiter found, splits on its last (rightmost) occurrence
    and returns the left part, whitespace-stripped.
    Returns None for None/empty input; returns the original stripped string
    if no delimiter matches.
    """
    if not title:
        return None
    for delim in (" | ", " - ", " -- "):
        if delim in title:
            return title.rsplit(delim, 1)[0].strip()
    return title.strip()


def _first_heading_text(html_string: str) -> str | None:
    """
    Return the plain text of the first h1-h6 element in an HTML string, or
    None if no heading is found or the text is empty/whitespace-only.

    Used by the H1-injection guard to compare the candidate synthetic title
    against the first real heading already present in Trafilatura output.
    """
    m = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html_string, re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return text if text else None


def extract_with_trafilatura(
    html: str,
    extraction_mode: ExtractionMode = "baseline",
    original_title: str | None = None,
) -> str:
    """
    Extract main content from HTML using Trafilatura.

    Used in extract mode (real-world pages with boilerplate).
    Returns extracted HTML if Trafilatura succeeds.  Falls back to original
    HTML only when extraction genuinely fails (None or near-empty output).

    Acceptance rules (in order):
    1. Extracted content contains headings → use as-is (existing behaviour).
    2. Extracted content is prose-sufficient (>= _MIN_PROSE_CHARS chars after
       stripping tags) but headingless → inject a synthetic <h1> from the page
       title so that validate_structure() and build_sections() can process the
       content normally.  Catches prose articles whose headings are CSS- or
       JS-rendered and therefore absent from Trafilatura's HTML output
       (e.g. Guardian long-reads, The Ringer feature articles).
    3. Otherwise → fall back to original HTML (genuine extraction failure).

    The synthetic heading is sourced from:
    - ``original_title`` argument if supplied by the caller, else
    - the raw ``<title>`` element parsed from ``html``, else
    - the literal string "Article".

    Known limitations in extract mode:
    - <pre> code blocks are converted to <blockquote>
    - Some inline spacing may be lost around inline elements
    These are documented limitations, not bugs.

    Args:
        html: Raw HTML string
        extraction_mode: Controls Trafilatura parameter set (default "baseline").
            "baseline"  - current production behavior: favor_precision=True, with fallback.
            "precision" - stricter: favor_precision=True, no_fallback=True.
                          Skips fallback extraction algorithms; more inputs fall
                          through to original HTML. Fewer false positives.
            "recall"    - inclusive: favor_recall=True. Less filtering, more
                          content retained. More boilerplate may leak through.
        original_title: Optional page title string; used as the synthetic <h1>
                          text when the extraction is headingless.  Callers may
                          omit this; the function will extract it from ``html``.

    Returns:
        Extracted HTML string (possibly with injected <h1>), or original HTML
        if extraction failed.
    """
    # Trafilatura kwargs per extraction mode.
    # "baseline" is the unchanged production behavior; existing callers are unaffected.
    if extraction_mode == "precision":
        # no_fallback=True: skip secondary extraction methods on failure.
        # Trafilatura>=1.8.0 supports this parameter.
        traf_kwargs: dict = dict(favor_precision=True, no_fallback=True)
    elif extraction_mode == "recall":
        # favor_recall=True: more inclusive extraction, keeps more content at cost of
        # more boilerplate leakage. Named for what it does, not for speed.
        traf_kwargs = dict(favor_precision=False, favor_recall=True, no_fallback=False)
    else:  # "baseline" — must stay byte-identical to the previous hardcoded call
        traf_kwargs = dict(favor_precision=True, no_fallback=False)

    extracted = trafilatura.extract(
        html,
        output_format="html",
        include_formatting=True,
        include_links=True,
        include_images=True,
        include_comments=False,
        include_tables=False,
        **traf_kwargs,
    )

    has_h1 = extracted and "<h1" in extracted
    has_any_heading = extracted and any(f"<h{i}" in extracted for i in range(1, 7))

    if has_any_heading:
        cleaned = re.sub(r'<p>\s*Advertisement\s*</p>', '', extracted)
        if not has_h1:
            title = _strip_title_branding(original_title or _extract_title_string(html))
            h1 = f"<h1>{title}</h1>\n" if title else "<h1>Article</h1>\n"
            # Guard: skip injection if the title duplicates the first real heading.
            # Uses the same normalization as drop_duplicate_consecutive_sections().
            first_h = _first_heading_text(cleaned)
            if first_h is not None and title:
                if _normalize_str(title) == _normalize_str(first_h):
                    return cleaned
            return h1 + cleaned
        return cleaned

    # Headingless extraction: accept if prose-sufficient, inject synthetic heading.
    if extracted:
        prose_chars = len(re.sub(r'<[^>]+>', '', extracted).strip())
        if prose_chars >= _MIN_PROSE_CHARS:
            cleaned = re.sub(r'<p>\s*Advertisement\s*</p>', '', extracted)
            title = _strip_title_branding(original_title or _extract_title_string(html))
            h1 = f"<h1>{title}</h1>\n" if title else "<h1>Article</h1>\n"
            return h1 + cleaned

    return html


def parse(html: str, original_title=None, require_article_body: bool = False,
          caption_map: dict[str, str] | None = None) -> Document:
    """
    Parse HTML string to Document model.

    Full pipeline: sanitize -> parse DOM -> select content -> build model.

    In transform mode, call parse() directly with raw HTML.
    In extract mode, call extract_with_trafilatura() first, then parse()
    with the original_title captured before extraction.

    Args:
        html: Raw HTML string (pre-extracted if in extract mode)
        original_title: Optional BeautifulSoup Tag for <title>, captured
                        before Trafilatura strips <head>. Passed by main.py
                        in extract mode to preserve document title.
        require_article_body: If True, raise ValidationError when no paragraph
                        with >= 20 words of non-placeholder prose is found.
                        Set to True in extract mode to detect extraction failure.
                        Default False to preserve backward compatibility.

    Returns:
        Document model with title and sections
    """
    # Step 1: Sanitize
    clean_html = sanitize(html)

    # Step 1.5: Convert trafilatura <graphic> to <img> before lxml parsing.
    # lxml doesn't recognise <graphic> as void, so it nests subsequent
    # content inside it.  <img> is a known void element.
    clean_html = re.sub(
        r'<graphic\b([^>]*)(?:/>|>\s*</graphic>|>)',
        r'<img\1>',
        clean_html,
    )

    # Step 2: Parse DOM
    soup = BeautifulSoup(clean_html, "lxml")

    # Step 3: Select main content
    content = select_main_content(soup)

    # Step 4: Validate structure
    validate_structure(content)

    # Step 4.5: Preflight scope check — reject table/form/reference-dominant pages
    preflight_scope_check(content)

    # Step 5: Build sections
    sections = build_sections(content, caption_map=caption_map)

    # Step 5.5: Trim trailing CMS boilerplate paragraphs (end-anchored)
    sections = trim_trailing_boilerplate(sections)

    # Step 5.6: Drop final orphan section (heading with zero content blocks)
    sections = drop_trailing_orphan_section(sections)

    # Step 5.7: Collapse consecutive identical placeholder blocks
    sections = collapse_consecutive_placeholder_blocks(sections)

    # Step 5.8: Drop consecutive duplicate-heading sections
    sections = drop_duplicate_consecutive_sections(sections)

    # Step 5.85: Drop all empty sections (heading-only, no content blocks)
    sections = drop_empty_sections(sections)

    # Step 5.9: Guard against extraction failure — no article body (extract mode only)
    if require_article_body and not _has_article_body(sections):
        raise ValidationError(
            "No article body detected: document contains no paragraph with "
            "20 or more words of prose text.  Extraction may have captured "
            "navigation or boilerplate instead of article content."
        )

    # Step 6: Extract title
    title = extract_title(soup, content, original_title=original_title)

    return Document(title=title, sections=sections)


def extract_title(soup: BeautifulSoup, content: Tag, original_title=None) -> str:
    """
    Extract document title from <title> tag or first <h1>.

    Per decisions.md section 5:
    - If <title> exists, use its text
    - Else if first <h1> in content exists, use its text
    - Else empty string

    Args:
        soup: Full DOM tree (for <title> access)
        content: Selected content subtree
        original_title: Optional BeautifulSoup Tag captured before
                        Trafilatura stripped <head>

    Returns:
        Title string (may be empty)
    """
    # Use original title if provided (extract mode - Trafilatura strips <head>)
    title_tag = original_title or soup.find("title")
    if title_tag:
        return re.sub(r'\s+', ' ', title_tag.get_text()).strip()

    # Fall back to first <h1> in content
    h1 = content.find("h1")
    if h1:
        return re.sub(r'\s+', ' ', h1.get_text()).strip()

    return ""


def validate_structure(content: Tag) -> None:
    """
    Validate that content has minimum semantic structure.

    Per decisions.md section 3:
    - Must have at least one h1, h2, or h3
    - Must have at least one p, ul, or ol

    Args:
        content: Selected content subtree

    Raises:
        ValidationError: If structure requirements are not met
    """
    has_heading = bool(content.find(["h1", "h2", "h3"]))
    has_body_content = bool(content.find(["p", "ul", "ol"]))

    if not has_heading or not has_body_content:
        raise ValidationError(
            "Input HTML lacks semantic structure "
            "(requires at least one h1-h3 and body content in p/ul/ol)."
        )


def preflight_scope_check(content: Tag) -> None:
    """
    Preflight: reject table/form/reference-dominant pages before model build.

    Checks three structural signatures that indicate out-of-scope content:
    1. Form/tool pages: form elements present + sparse prose (<250 words).
    2. Table/reference pages: multiple tables + sparse prose (<250 words).
    3. Navigation/reference pages: link-word ratio > 0.5 with sparse prose
       (<500 words).  Catches pages whose paragraph text is mostly navigation
       links rather than article prose (e.g. GDP reference lists).

    Thresholds are calibrated against the eval20 corpus:
    - Lowest in-scope ACCEPT p_text_words: 241 (cdc)
    - Highest in-scope ACCEPT link/p ratio:  0.18 (theconversation)
    Both values leave a safe margin below these rejection thresholds.

    Called unconditionally after validate_structure() so that it applies in
    both transform and extract mode.
    """
    table_count = len(content.find_all("table"))
    form_count = len(content.find_all("form"))

    p_text_words = sum(
        len(p.get_text().split())
        for p in content.find_all("p")
    )
    link_words = sum(
        len(a.get_text().split())
        for a in content.find_all("a")
    )

    if form_count >= 1 and p_text_words < 250:
        raise ValidationError("Out of scope: tool/form page.")

    if table_count >= 2 and p_text_words < 250:
        raise ValidationError("Out of scope: table/reference page.")

    if p_text_words > 0 and p_text_words < 500 and (link_words / p_text_words) > 0.5:
        raise ValidationError("Out of scope: navigation/reference page.")


def build_sections(content: Tag, caption_map: dict[str, str] | None = None) -> list[Section]:
    """
    Build sections from headings in content.

    Per decisions.md section 5:
    - Drop all content before first heading
    - Each heading starts a new section
    - Section continues until next heading (any level)

    Uses a flatten-then-assign approach: all headings and block-level
    elements are collected in document order, then each block is assigned
    to the most recent heading.  This avoids content duplication when
    headings are nested at different DOM depths (e.g. h2 → div → h3).

    Args:
        content: Selected content subtree

    Returns:
        List of Section objects
    """
    # Find all headings (h1-h6)
    heading_tags = set(["h1", "h2", "h3", "h4", "h5", "h6"])
    headings = content.find_all(heading_tags)

    if not headings:
        # No headings found - will fail validation later
        return []

    heading_set = set(id(h) for h in headings)

    # Flatten: walk content descendants in document order, collecting
    # headings and parseable block elements.  Skip any element whose
    # ancestor is already a collected block (prevents duplication).
    ordered: list[tuple[str, Tag]] = []  # ("heading"|"block", element)
    collected_ids: set[int] = set()

    for elem in content.descendants:
        if not isinstance(elem, Tag):
            continue

        # Skip elements inside an already-collected block
        if any(id(p) in collected_ids for p in elem.parents):
            continue

        if id(elem) in heading_set:
            ordered.append(("heading", elem))
            collected_ids.add(id(elem))
        elif elem.name not in heading_tags:
            block = parse_block(elem, caption_map=caption_map)
            if block:
                ordered.append(("block", elem))
                collected_ids.add(id(elem))

    # Assign: each block goes to the most recent heading.
    sections: list[Section] = []
    current_heading: Heading | None = None
    current_blocks: list[Block] = []

    for kind, elem in ordered:
        if kind == "heading":
            # Flush previous section
            if current_heading is not None and _heading_has_text(current_heading):
                sections.append(Section(heading=current_heading, blocks=current_blocks))
            current_heading = parse_heading(elem)
            current_blocks = []
        else:
            if current_heading is not None:
                block = parse_block(elem, caption_map=caption_map)
                if block:
                    current_blocks.append(block)

    # Flush last section
    if current_heading is not None and _heading_has_text(current_heading):
        sections.append(Section(heading=current_heading, blocks=current_blocks))

    return sections


def _heading_has_text(heading: "Heading") -> bool:
    """Return True if the heading contains at least one non-whitespace character."""
    return bool("".join(_inline_to_text(il) for il in heading.inlines).strip())


def parse_heading(element: Tag) -> Heading:
    """
    Parse heading element to Heading model.

    Args:
        element: BeautifulSoup Tag for h1-h6

    Returns:
        Heading with level and inline content
    """
    level = int(element.name[1])
    inlines = parse_inlines(element)
    return Heading(level=level, inlines=inlines)


def _listblock_has_content(block: "ListBlock") -> bool:
    """Return True if the list has at least one item with non-empty content.

    Filters two structural artifact cases:
    - Zero items: <ol></ol> or <ul></ul> (no <li> elements at all)
    - All-empty items: every <li> has no inline text and no nested lists
      (e.g. <ul><li></li><li></li></ul>)
    Both are unambiguously extraction artifacts; legitimate lists always have
    at least one item with visible content.
    """
    return bool(block.items) and any(
        item.inlines or item.children for item in block.items
    )


def parse_figure(element: Tag, caption_map: dict[str, str] | None = None) -> Block | None:
    """
    Parse <figure> element to Block model.

    If the figure contains an image, preserves it with figcaption as caption.
    If no image but figcaption text exists, returns as Paragraph.
    """
    imgs = element.find_all(["img", "graphic"])
    figcaption = element.find("figcaption")
    caption_text = ""
    if figcaption:
        caption_text = figcaption.get_text(separator=" ", strip=True)

    if not imgs:
        if caption_text:
            return Paragraph(inlines=[Text(text=caption_text)])
        return None

    result = degrade_image(imgs[0])
    if isinstance(result, Image):
        if caption_text:
            result.caption = caption_text
        return result
    # Placeholder Text — wrap in Paragraph
    return Paragraph(inlines=[result])


def parse_block(element: Tag, caption_map: dict[str, str] | None = None) -> Block | None:
    """
    Parse block-level element to Block model.

    Returns None for unrecognized elements (silently skipped in v1).
    v2: Add warning logging for skipped elements.

    Args:
        element: BeautifulSoup Tag for block element
        caption_map: Optional map of img src -> caption text (extract mode)

    Returns:
        Block model object or None if unsupported
    """
    tag_name = element.name

    if tag_name == "p":
        block = parse_paragraph(element)
        return block if block.inlines else None
    elif tag_name in ("ul", "ol"):
        block = parse_list(element)
        return block if _listblock_has_content(block) else None
    elif tag_name == "blockquote":
        return parse_quote(element)
    elif tag_name == "pre":
        return parse_preformatted(element)
    elif tag_name == "table":
        return degrade_table(element)
    elif tag_name == "figure":
        return parse_figure(element, caption_map=caption_map)
    elif tag_name in ("img", "graphic"):
        result = degrade_image(element)
        if isinstance(result, Image):
            if caption_map and result.src in caption_map:
                result.caption = caption_map[result.src]
            return result
        # Placeholder Text — wrap in Paragraph
        return Paragraph(inlines=[result])
    elif tag_name in ("form", "input", "textarea", "select", "button"):
        return degrade_form(element)
    elif tag_name == "hr":
        return degrade_hr()
    else:
        # Unknown block - skip silently in v1
        return None


def parse_paragraph(element: Tag) -> Paragraph:
    """
    Parse paragraph to Paragraph model.

    Args:
        element: BeautifulSoup Tag for <p>

    Returns:
        Paragraph with inline content
    """
    inlines = parse_inlines(element)
    return Paragraph(inlines=inlines)


def parse_list(element: Tag) -> ListBlock:
    """
    Parse list to ListBlock model.

    Handles nested lists via ListItem.children.

    Args:
        element: BeautifulSoup Tag for <ul> or <ol>

    Returns:
        ListBlock with items
    """
    ordered = element.name == "ol"
    items = []

    for li in element.find_all("li", recursive=False):
        # Parse inlines, but exclude nested lists from inline parsing
        # (nested lists are handled separately via children)
        li_copy = li.__copy__()
        for nested in li_copy.find_all(["ul", "ol"], recursive=False):
            nested.decompose()
        inlines = parse_inlines(li_copy)

        # Find nested lists
        nested_lists = li.find_all(["ul", "ol"], recursive=False)
        children = [parse_list(nested) for nested in nested_lists]

        items.append(ListItem(inlines=inlines, children=children))

    return ListBlock(ordered=ordered, items=items)


def parse_quote(element: Tag) -> Quote:
    """
    Parse blockquote to Quote model (recursive).

    Args:
        element: BeautifulSoup Tag for <blockquote>

    Returns:
        Quote containing blocks
    """
    blocks = []
    for child in element.children:
        if isinstance(child, Tag):
            block = parse_block(child)
            if block:
                blocks.append(block)

    return Quote(blocks=blocks)


def parse_preformatted(element: Tag) -> Preformatted:
    """
    Parse <pre> to Preformatted model.

    Preserves whitespace exactly.

    Args:
        element: BeautifulSoup Tag for <pre>

    Returns:
        Preformatted with verbatim text
    """
    return Preformatted(text=element.get_text())


def collapse_whitespace(text: str) -> str:
    """
    Collapse runs of whitespace into a single space.

    Preserves leading/trailing space if the original had whitespace
    at those boundaries. This matches HTML whitespace collapsing rules
    (decisions.md section 8).
    """
    if not text:
        return ""
    leading = " " if text[0].isspace() else ""
    trailing = " " if text[-1].isspace() else ""
    collapsed = re.sub(r"\s+", " ", text.strip())
    if not collapsed:
        return ""
    return leading + collapsed + trailing


def parse_inlines(element: Tag) -> list[Inline]:
    """
    Parse inline content recursively.

    Handles nested inline elements and text nodes.
    Applies whitespace normalization.

    Args:
        element: BeautifulSoup Tag containing inline content

    Returns:
        List of Inline model objects
    """
    result = []

    for child in element.children:
        if isinstance(child, NavigableString):
            text = collapse_whitespace(str(child))
            if text:
                result.append(Text(text=text))
        elif isinstance(child, Tag):
            inline = parse_inline_element(child)
            if isinstance(inline, list):
                result.extend(inline)
            elif inline:
                result.append(inline)

    return result


def parse_inline_element(element: Tag) -> Inline | list[Inline] | None:
    """
    Parse single inline element.

    Returns Inline object, list of Inlines, or None for unknown elements.

    Args:
        element: BeautifulSoup Tag for inline element

    Returns:
        Inline model object(s) or None
    """
    tag_name = element.name

    if tag_name == "br":
        return LineBreak()
    elif tag_name in ("em", "i"):
        return Emphasis(children=parse_inlines(element))
    elif tag_name in ("strong", "b"):
        return Strong(children=parse_inlines(element))
    elif tag_name == "code":
        return Code(text=element.get_text())
    elif tag_name == "a":
        href = element.get("href", "")
        return Link(href=href, children=parse_inlines(element))
    elif tag_name in ("img", "graphic"):
        result = degrade_image(element)
        if isinstance(result, Image):
            # Image is block-level; in inline context, use alt text
            return Text(text=result.alt) if result.alt else None
        return result
    else:
        # Unknown inline element - extract text
        text = element.get_text().strip()
        if text:
            return Text(text=text)
        return None
