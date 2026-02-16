# Flowdoc - v1 Scope

**Version:** 1.0
**Status:** Frozen for v1 development

Flowdoc is a general-purpose document converter that transforms structured documents into dyslexia-friendly, readable formats.

v1 is intentionally narrow: it validates core value with dyslexic readers before any scope expansion.

## Design principle

Readability over fidelity.

Flowdoc does not preserve original layout, branding, or page geometry. Output may look completely different from the source. This is by design.

## v1 inputs

HTML only.

Operational requirement: input must be **semantic HTML** (text-flow structure), not div-based layouts.

At a minimum, v1 expects:
- at least one heading in **h1-h3**
- body content expressed via **p and/or ul/ol**
- semantic structure usable without heuristics

Flowdoc rejects non-semantic HTML with a clear error. Exact validation rules are defined in [docs/decisions.md](docs/decisions.md).

## v1 output

Readable HTML (canonical output).

Self-contained means:
- a single HTML file
- no external CSS, fonts, scripts, or images
- CSS inlined in one `<style>` block
- fonts embedded only when OpenDyslexic toggle is enabled

PDF output is out of scope for v1. Use browser print-to-PDF.

## In-scope functionality (v1)

- Deterministic main content selection (main -> article -> body)
- Parse headings, paragraphs, lists, blockquotes, and code blocks
- Preserve inline emphasis, strong, inline code, and links
- Deterministic degradation for unsupported elements (e.g., tables/images)
- Strict sanitization to remove active content
- Simple CLI conversion workflow
- Validate usefulness with dyslexic readers before expanding scope

Exact handling rules live in [docs/decisions.md](docs/decisions.md).

## Out of scope (v1)

Inputs:
- PDF
- DOCX
- Markdown
- OCR / image-based documents
- Heuristic scraping / "readability extraction" for div soup

Outputs:
- native PDF generation
- DOCX output
- layout fidelity / visual preservation

Features:
- GUI or web service
- recipe-specific parsing or enrichment
- document editing (conversion only)
- batch processing features beyond basic CLI usage

## Font support (v1)

- Default: system sans-serif stack (Arial/Verdana)
- Optional toggle: OpenDyslexic via `--font opendyslexic`

OpenDyslexic is provided as a preference toggle; Flowdoc makes no universal efficacy claim.

## Success criteria (v1)

1. Accepts semantic HTML inputs within scope.
2. Produces a self-contained readable HTML output.
3. Output is measurably better for dyslexic readers versus the original formatting, using a simple comparison protocol (fewer re-reads / fewer line-loss incidents / lower fatigue scores).
4. Works on modern browsers, mobile devices, and print.
5. Failure modes are predictable and explained clearly.
6. Inline elements (links/emphasis/code) render correctly.
7. Unsupported elements degrade deterministically (no silent dropping).
8. Sanitization prevents active-content and injection issues.

If v1 meets these criteria, scope expansion is justified; otherwise it is premature.
