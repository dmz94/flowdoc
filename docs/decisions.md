# Decant - Technical Decisions (Authoritative Spec)

**Status:** Locked for v1 implementation
**Last updated:** 2026-03-14

This document is the single source of truth for v1 implementation and tests. If another document disagrees with this one, this one wins.

References:
- Scope boundaries and success criteria: See README.md
- Typography evidence and citations: [research-typography-guidelines.md](research-typography-guidelines.md)

---

## 1) v1 contract (inputs/outputs)

Input (v1): HTML only.

Output (v1): self-contained readable HTML:
- one HTML file
- CSS in a single inline `<style>` block
- no external scripts, CSS, or fonts
- images use original source URLs (see section 7)
- OpenDyslexic embedded only when enabled via `--font opendyslexic`

Non-goals for v1 include: PDF input, GUI, native PDF output.

The engine is file-in/file-out only. It does not fetch URLs.
A user-facing surface (web page, browser extension, or other form)
is a separate v1 deliverable. The engine alone is not a product.

---

## 2) Processing pipeline (order is mandatory)

Given input HTML string:

1. **Extract main content** (Trafilatura; falls back to deterministic selector if Trafilatura returns nothing)
2. **Sanitize** (strip active content, strip attributes, enforce URL policies)
3. **Parse DOM** (tolerant HTML parser)
4. **Parse to internal model** (apply degradation rules; model is safe and HTML-free)
5. **Render from model only** (renderer never touches DOM)

---

## 3) Input validation and rejection (testable rules)

Decant rejects input as "non-semantic" when any of the following are true in the selected main content subtree (after extraction and sanitization):

A. No headings usable for structure:
- There is **no** `<h1>`, `<h2>`, or `<h3>` in the selected main content subtree.

B. No body content elements:
- There is **no** `<p>`, `<ul>`, or `<ol>` in the selected main content subtree.

Notes:
- `<h4>`-`<h6>` may exist, but do not satisfy the "at least one h1-h3" requirement.
- Heading level sequencing is **not** validated (h1->h3 is allowed).
- Content before the first heading is treated as preamble/junk and is dropped (see sectioning rules).

Error message (exact):
`Input HTML lacks semantic structure (requires at least one h1-h3 and body content in p/ul/ol).`

Exit code: 1.

---

## 4) Main content selection

Primary strategy: Trafilatura (`trafilatura.extract(html, output_format="html")`).

Trafilatura is called first on the raw HTML string before sanitization. It returns a clean HTML fragment containing the main content, stripping navigation, headers, footers, sidebars, and boilerplate.

Fallback (if Trafilatura returns None or empty string):
1. If `<main>` exists, select the **first** `<main>` element.
2. Else if `<article>` exists, select the **first** `<article>` element.
3. Else select `<body>`.

If `<body>` is missing and Trafilatura also fails, treat as parse/validation error (exit code 1).

The fallback exists for inputs where Trafilatura cannot identify a main content region (e.g. hand-crafted semantic HTML with no boilerplate to strip). In practice the fallback handles simple_article.html and similar clean inputs correctly.

---

## 5) Sectioning and headings

Title extraction:
- If the document has a `<title>`, use its text as `Document.title`.
- Else, if the first `<h1>` exists within the selected content, use its text as `Document.title`.
- Else, `Document.title` is empty string.

Section construction (content under headings only):
- Drop all content before the first heading (h1-h6) in the selected subtree.
- The first heading encountered begins Section 1.
- A section continues until the next heading of **any** level.

Special rule for multiple `<h1>`:
- The **first** `<h1>` is treated as title when no `<title>` exists (above).
- **Subsequent** `<h1>` headings create **top-level sections** like any other heading.

Heading levels:
- Levels are preserved (1-6) for rendering hierarchy.
- No validation of "skipped levels."

---

## 6) Internal document model (v1)

Model must be explicit and HTML-free.

```
Document
  - title: str
  - sections: list[Section]

Section
  - heading: Heading
  - blocks: list[Block]

Heading
  - level: int  # 1..6
  - inlines: list[Inline]  # headings may include inline emphasis/strong/code/link as plain inlines

Block (one of)
  - Paragraph(inlines: list[Inline])
  - ListBlock(ordered: bool, items: list[ListItem])
  - Quote(blocks: list[Block])  # blockquote content parsed into blocks
  - Preformatted(text: str)     # from <pre>

ListItem
  - inlines: list[Inline]
  - children: list[ListBlock]   # nested lists are preserved; do not flatten

Inline (one of)
  - Text(text: str)
  - Emphasis(children: list[Inline])
  - Strong(children: list[Inline])
  - Code(text: str)
  - Link(href: str, children: list[Inline])
```

Constraints:
- Nested lists are represented via `ListItem.children` (0..n).
- Renderer consumes only the model. No DOM references or raw HTML strings are allowed in the model.

---

## 7) HTML element handling (deterministic)

Supported block elements (first-class):
- headings: h1-h6 (sectioning)
- p -> Paragraph
- ul/ol -> ListBlock
- blockquote -> Quote (parse contents into blocks)
- pre -> Preformatted (verbatim text content)
- code inside pre is treated as part of preformatted text

Supported inline elements:
- em, i -> Emphasis
- strong, b -> Strong
- code (inline) -> Code
- a[href] -> Link (href retained subject to URL policy)

Degraded with placeholders (deterministic):
- table -> simple tables (<=10 rows, no colspan, no rowspan, no
  nesting, >1 cell) are rendered as styled HTML tables. Complex
  tables degrade to a Paragraph WARN placeholder:
    `[Table omitted - N rows, M columns]`
  Always link to original source when source URL is available.
- img -> preserved as inline image when src URL is available:
  - if src is http/https: render as `<img src="{src}" alt="{alt}">`
  - if src is unavailable or not http/https: WARN placeholder:
    `[Image not included. View original](<source URL if known>)`
  Note: self-contained offline constraint is relaxed for images in v1.
  Print quality takes precedence.
  Implementation pending -- code changes tracked separately.
- form/input/textarea/select/button -> Paragraph: `[Form omitted]`
- Source URL linking: when `--source-url` is provided on the CLI,
  each placeholder paragraph gets a "View original" link to the
  source page. A notice banner at the top of the document summarizes
  omitted tables/images/forms with a link to the original page.
  Without `--source-url`, placeholders render without links and
  the banner omits the link (but still lists omitted content types).
- figure/figcaption:
  - In transform mode: <figure> is parsed directly.
    If it contains an image, the image is preserved with
    figcaption text as a visible caption.
    If it contains no image, figcaption text is preserved
    as Paragraph(s).
  - In extract mode: captions are harvested from the raw
    HTML before Trafilatura extraction. Captions are matched
    to images by exact src URL. When a match is found, the
    caption is rendered below the image in a <figcaption>.
  - Images without captions render as bare <img> (unchanged).

Dropped (removed from consideration entirely):
- nav, header, footer, aside
- scripts, styles, iframes, object, embed
- advertisements / decorative containers (implicitly dropped by selection + unsupported handling)

Footnotes/endnotes:
- v1 does not preserve footnote structure.
- Any footnote blocks encountered are treated as normal paragraphs in place; markers/links are dropped.

Horizontal rules:
- hr becomes a Paragraph with a visual separator token: `[-]` (renderer styles this as a divider).

Definition lists:
- dl -> degraded to an unordered list where each item is `term - definition`.

---

## 8) Inline whitespace and nesting rules

Whitespace:
- Apply standard HTML whitespace collapsing rules across inline boundaries.
- Ensure `word<strong>next</strong>` renders as `word next` (insert a space when the boundary would otherwise concatenate tokens).

Nesting:
- Inline elements may nest arbitrarily in source HTML.
- Parser supports nesting by representing children as `list[Inline]`.
- Renderer must render nesting without leaking raw tags.

Links:
- Preserve link text as inline children.
- Preserve href subject to URL policy (below).

---

## 9) Sanitization (security boundary)

Sanitization happens after Trafilatura extraction and before DOM parsing.

Policy:
- Allowlist tags required for v1 parsing/selection.
- Allowlist attributes required for links only.
- Strip everything else.

URL policy:
- Drop `javascript:` entirely.
- Drop `data:` entirely.
- Preserve `http:` and `https:`.
- Preserve fragment identifiers (`#...`) for internal navigation.

nh3 configuration (required for v1):
- allowed tags include: html, head, body, main, article, h1-h6, p, ul, ol, li, blockquote, pre, code, em, i, strong, b, a, table, tr, td, th, img, figure, figcaption, dl, dt, dd, hr, form, input, textarea, select, option, button
  - (tables/images/forms are allowed so they can be degraded deterministically; they are not rendered as-is)
- allowed attributes: `href` on `a`, `alt` and `src` on `img`
  Note: src URL scheme filtering (http/https only) already applies
  via the existing allowed schemes rule.
  Implementation pending -- code changes tracked separately.
- allowed schemes: http, https
- strip comments: yes

---

## 10) Rendering invariants (CSS + HTML)

Renderer output:
- HTML5 document with `<meta charset="utf-8">`
- single `<style>` block (inline)
- content in a single, single-column container
- stable heading hierarchy and list formatting
- link styling remains identifiable in screen and print

Typography defaults (v1):
- font: system sans-serif stack (Arial/Verdana) unless OpenDyslexic toggle
- body font size: 18px
- line-height: 1.5
- letter-spacing: 0.02em (starting point)
- word-spacing: 0.16em (starting point)
- These are starting-point values for empirical tuning; the BDA-recommended spacing targets are referenced in docs/research-typography-guidelines.md.
- max line length: 60-70 characters (implemented via container max-width)
- left-aligned, ragged-right (no full justification)
- background: off-white/cream; text dark gray/black
- meet WCAG AA contrast minimum

Print:
- do not shrink below 12pt
- preserve link affordance
- avoid broken headings/list items where feasible

OpenDyslexic embedding:
- only when `--font opendyslexic`
- embed as base64 in CSS so output remains self-contained
- otherwise embed no fonts

---

## 11) CLI contract (v1)

v1 ships one command only:

`decant convert [INPUT] [-o OUTPUT] [--font opendyslexic]`

Input:
- If INPUT path is provided, read file.
- If INPUT missing and stdin is not a TTY, read stdin.
- If INPUT missing and stdin is a TTY, error with exit code 3.

Output:
- Default output filename: `<basename>.decant.html` alongside input file.
- `-o/--output` overrides output path.
- In stdin mode, write to stdout unless `-o` is provided.

stdout/stderr:
- stdout contains only output HTML in stdout mode.
- stderr contains errors only.

Exit codes:
- 0 success
- 1 validation/parse error (non-semantic, missing body, etc.)
- 2 render error
- 3 I/O error

Engine error codes:
Specific error codes for structured FAIL states are deferred to the
surface design session. The surface is responsible for translating
engine exit codes and error messages into user-friendly explanations.

Explicitly out of v1:
- `validate` command
- `info` command
- `--report json`

(They may be discussed only in docs/architecture.md.)

---

## 12) Determinism contract

Contract:
Same input HTML + same Decant version + same flags -> byte-identical output.

Enforcement requirements:
- No timestamps, random values, environment-dependent paths, or non-deterministic iteration.
  Provenance metadata (source URL, conversion date, Decant version)
  is excluded from byte-comparison. See section 13.
- Stable ordering when iterating attributes/collections during rendering.
- Normalize output formatting (consistent indentation/newlines) in renderer.

Tests must include:
- determinism test: run conversion twice and compare bytes.
- golden output tests: fixtures -> expected HTML.
- model snapshot tests: fixtures -> model JSON snapshot.

Dependency control:
- Development may use compatible ranges.
- Releases must be cut from exact dependency pins; updating dependencies requires intentional regeneration of golden files.
- Trafilatura updates require particular care: extraction behaviour can change between versions, invalidating golden files. Pin to a specific version for releases.

---

## Phase 2A measurement note (2026-02-27)

**Context:** Trafilatura 2.0.0. Corpus: 10 user-study fixtures (`tests/fixtures/user-study/`).

Three extraction modes were measured: `baseline` (favor_precision=True, no_fallback=False), `precision` (favor_precision=True, no_fallback=True), `recall` (favor_recall=True, no_fallback=False).

**Results:**
- `precision` == `baseline` on all 10 fixtures (zero char/paragraph delta). The fallback path is not triggered by any user-study fixture; `no_fallback=True` has no observable effect on this corpus.
- `recall` diverged significantly on 3 fixtures (worse, not better):
  - eater: −338,460 chars (354,950 → 16,490), −40 paragraphs
  - propublica: −318,458 chars (366,581 → 48,123), −103 paragraphs
  - pbs: −274,066 chars (280,423 → 6,357), −4 paragraphs
- No status changes: all 10 fixtures ACCEPT under all 3 modes.

**Decision:** Keep `baseline` as the default and only production mode. The mode switch (`ExtractionMode`) exists for experimentation only and must not be exposed in the v1 CLI. `recall` must not become the default; it performs worse on this corpus because `favor_recall=True` activates a different internal Trafilatura algorithm that extracts less content from these specific site structures.

---

## 13) Provenance (v1)

Every output document includes visible provenance metadata:
- Source URL (if supplied by surface or CLI parameter)
- Conversion date
- Decant version

Provenance is rendered at the bottom of the output document.
Provenance is excluded from the determinism byte-comparison contract.
Content is byte-identical across runs; provenance metadata may vary.

CLI parameter: `--source-url <url>` (optional, no default)
If not supplied, source URL is omitted from provenance block.
