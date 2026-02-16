# Flowdoc - Technical Decisions (Authoritative Spec)

**Status:** Locked for v1 implementation
**Last updated:** 2026-02-15

This document is the single source of truth for v1 implementation and tests. If another document disagrees with this one, this one wins.

References:
- Scope boundaries and success criteria: [SCOPE.md](../SCOPE.md)
- Typography evidence and citations: [research_typography_guidelines.md](research_typography_guidelines.md)

---

## 1) v1 contract (inputs/outputs)

Input (v1): HTML only.

Output (v1): self-contained readable HTML:
- one HTML file
- CSS in a single inline `<style>` block
- no external scripts, CSS, images, or fonts
- OpenDyslexic embedded only when enabled via `--font opendyslexic`

Non-goals for v1 include: PDF input, heuristic scraping of div soup, GUI, native PDF output.

---

## 2) Processing pipeline (order is mandatory)

Given input HTML string:

1. **Sanitize** (strip active content, strip attributes, enforce URL policies)
2. **Parse DOM** (tolerant HTML parser)
3. **Select main content** (deterministic: main -> article -> body)
4. **Parse to internal model** (apply degradation rules; model is safe and HTML-free)
5. **Render from model only** (renderer never touches DOM)

---

## 3) Input validation and rejection (testable rules)

Flowdoc rejects input as "non-semantic" when any of the following are true after sanitization:

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

## 4) Main content selection (deterministic)

Selection is applied on the sanitized DOM:

1. If `<main>` exists, select the **first** `<main>` element.
2. Else if `<article>` exists, select the **first** `<article>` element.
3. Else select `<body>`.

If `<body>` is missing, treat as parse/validation error (exit code 1).

After selection, navigation/sidebars/headers/footers are not separately processed; they are simply excluded by selection.

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
- table -> a single Paragraph: `[Table omitted - X rows, Y columns]`
  - rows = count of `<tr>`
  - cols = max count of immediate `<td>`/`<th>` per row
  - ignore rowspan/colspan for counting
- img -> a single Inline Text inside a Paragraph:
  - if alt exists and non-empty: `[Image: {alt}]`
  - else: `[Image omitted]`
- form/input/textarea/select/button -> Paragraph: `[Form omitted]`
- figure/figcaption:
  - figcaption text is preserved as Paragraph(s)
  - embedded images handled by img rule

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

Sanitization happens before DOM parsing and content selection.

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
- allowed attributes: `href` on `a`, `alt` on `img`
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

`flowdoc convert [INPUT] [-o OUTPUT] [--font opendyslexic]`

Input:
- If INPUT path is provided, read file.
- If INPUT missing and stdin is not a TTY, read stdin.
- If INPUT missing and stdin is a TTY, error with exit code 3.

Output:
- Default output filename: `<basename>.flowdoc.html` alongside input file.
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

Explicitly out of v1:
- `validate` command
- `info` command
- `--report json`

(They may be discussed only in [architecture_exploration.md](architecture_exploration.md).)

---

## 12) Determinism contract

Contract:
Same input HTML + same Flowdoc version + same flags -> byte-identical output.

Enforcement requirements:
- No timestamps, random values, environment-dependent paths, or non-deterministic iteration.
- Stable ordering when iterating attributes/collections during rendering.
- Normalize output formatting (consistent indentation/newlines) in renderer.

Tests must include:
- determinism test: run conversion twice and compare bytes.
- golden output tests: fixtures -> expected HTML.
- model snapshot tests: fixtures -> model JSON snapshot.

Dependency control:
- Development may use compatible ranges.
- Releases must be cut from exact dependency pins; updating dependencies requires intentional regeneration of golden files.
