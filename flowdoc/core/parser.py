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
    Paragraph, ListBlock, ListItem, Quote, Preformatted,
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


def _normalize_heading_text(heading) -> str:
    """
    Return normalized heading text: strip, collapse internal whitespace,
    lowercase.  Used for consecutive duplicate detection.
    """
    raw = "".join(_inline_to_text(il) for il in heading.inlines)
    return re.sub(r'\s+', ' ', raw).strip().lower()


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


def _is_placeholder_paragraph(block) -> bool:
    """
    Return True if block is a single-inline Paragraph whose text is a known
    placeholder token: [Form omitted], [Image omitted], or [Image: <alt>].

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


def extract_with_trafilatura(html: str, extraction_mode: ExtractionMode = "baseline") -> str:
    """
    Extract main content from HTML using Trafilatura.

    Used in extract mode (real-world pages with boilerplate).
    Returns extracted HTML if Trafilatura succeeds and preserves heading
    structure. Falls back to original HTML if extraction fails or strips
    all headings.

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

    Returns:
        Extracted HTML string, or original HTML if extraction failed
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
        include_comments=False,
        include_tables=False,
        **traf_kwargs,
    )
    has_headings = extracted and any(f"<h{i}" in extracted for i in range(1, 7))
    if has_headings:
        cleaned = re.sub(r'<p>\s*Advertisement\s*</p>', '', extracted)
        return cleaned
    return html


def parse(html: str, original_title=None) -> Document:
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
    Returns:
        Document model with title and sections
    """
    # Step 1: Sanitize
    clean_html = sanitize(html)

    # Step 2: Parse DOM
    soup = BeautifulSoup(clean_html, "lxml")

    # Step 3: Select main content
    content = select_main_content(soup)

    # Step 4: Validate structure
    validate_structure(content)

    # Step 5: Build sections
    sections = build_sections(content)

    # Step 5.5: Trim trailing CMS boilerplate paragraphs (end-anchored)
    sections = trim_trailing_boilerplate(sections)

    # Step 5.6: Drop final orphan section (heading with zero content blocks)
    sections = drop_trailing_orphan_section(sections)

    # Step 5.7: Collapse consecutive identical placeholder blocks
    sections = collapse_consecutive_placeholder_blocks(sections)

    # Step 5.8: Drop consecutive duplicate-heading sections
    sections = drop_duplicate_consecutive_sections(sections)

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


def build_sections(content: Tag) -> list[Section]:
    """
    Build sections from headings in content.

    Per decisions.md section 5:
    - Drop all content before first heading
    - Each heading starts a new section
    - Section continues until next heading (any level)

    v2 consideration: Could preserve pre-heading content as preamble with warning.

    Args:
        content: Selected content subtree

    Returns:
        List of Section objects
    """
    # Find all headings (h1-h6)
    headings = content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    if not headings:
        # No headings found - will fail validation later
        return []

    sections = []

    for i, heading_elem in enumerate(headings):
        # Parse the heading
        heading = parse_heading(heading_elem)

        # Collect blocks until next heading
        blocks = []
        current = heading_elem.next_sibling

        # Find next heading element (or None if last section)
        next_heading = headings[i + 1] if i + 1 < len(headings) else None

        while current:
            # Stop if we hit the next heading
            if next_heading and current == next_heading:
                break

            if isinstance(current, Tag):
                block = parse_block(current)
                if block:
                    blocks.append(block)

            current = current.next_sibling

        # Drop sections whose heading has no text content — structural artifact.
        # Legitimate headings always have text; an empty heading is an
        # extraction stub (e.g. <h1></h1>) with no renderable content.
        if _heading_has_text(heading):
            sections.append(Section(heading=heading, blocks=blocks))

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


def parse_block(element: Tag) -> Block | None:
    """
    Parse block-level element to Block model.

    Returns None for unrecognized elements (silently skipped in v1).
    v2: Add warning logging for skipped elements.

    Args:
        element: BeautifulSoup Tag for block element

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
    elif tag_name == "img":
        # Image returns Text (inline), wrap in Paragraph
        return Paragraph(inlines=[degrade_image(element)])
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
    elif tag_name == "img":
        return degrade_image(element)
    else:
        # Unknown inline element - extract text
        text = element.get_text().strip()
        if text:
            return Text(text=text)
        return None
