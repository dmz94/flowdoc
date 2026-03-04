# FLOWDOC V1 SUCCESS CONTRACT (v1.0)

## 1) Purpose (Product-Level)

Flowdoc v1 exists to turn a saved HTML file into a clean, readable, printable document that can be shared, filed, emailed, or handed to someone.

It preserves the prose content and structure of the original. Visual and interactive content that cannot be preserved is flagged clearly and linked back to the original source. Obvious clutter is removed.

It does not need to work on every page on the internet.
It must be trustworthy. When it cannot meet its quality standard, it must warn clearly or fail explicitly. It must never silently degrade meaning.

The quality bar: would you hand this printed document to a student, a colleague, or a parent without apology?

## 2) Audiences and Operator Model

Beneficiary:
Anyone who needs a clearer, more readable version of a web article. Initial validation focuses on readers with dyslexia because that is where the research base, typography evidence, and personal connection are strongest. The same output benefits readers with ADHD, low vision, cognitive load issues, or anyone reading in a second language.

Audiences (overall mission scope):
- People converting articles for their own use
- Parents, teachers, SENCOs preparing materials for students
- Developers building accessibility tools on the engine
- Institutions and organizations producing accessible content

Operator model (v1 reality):
v1 ships as a CLI tool. v1 also requires a user-facing surface (see Section 10) for product validation and non-technical access.

## 3) Two-Layer Architecture (v1)

**Engine:**
The core conversion pipeline. HTML file in, accessible HTML document out.
Deterministic, security-bounded, model-driven. File-in/file-out only.
The engine does not fetch URLs.

**Surface:**
A user-facing layer that accepts a URL or uploaded HTML file, passes content to the engine, and returns the converted document. Required for product validation and non-technical user access. Form factor TBD (web page, browser extension, or other).

Both layers are v1 deliverables. The engine alone is not a product.

## 4) Output Artifact (v1)

Primary output:
- A single HTML file
- Designed to print cleanly
- Designed to open in any browser
- BDA-aligned typography defaults

Images:
- Preserved using original source URLs when available
- Render when online and in print (the primary use case)
- If source URL is unavailable, fall back to WARN placeholder

Provenance (visible in the document):
- Source URL (if available, supplied by surface or CLI parameter)
- Conversion date
- Flowdoc version

Provenance is excluded from the determinism contract.
Content is byte-identical across runs; provenance metadata may vary.

## 5) Content Quality Standard (v1)

An output is acceptable when:

1. All main article prose is present and correctly ordered.
2. Title and section headings are preserved well enough for navigation.
3. Layout is readable without manual adjustment.
4. Obvious clutter (navigation, ads, site chrome) is removed.
5. Images are preserved when source URL is available.
6. Captions are preserved.
7. Content that cannot be preserved is explicitly flagged with a link to the original source.
8. No silent structural corruption occurs.

Silent structural corruption means:
- Missing sections that are not flagged.
- Meaning loss that appears clean but is incomplete.
- Structural breakage not disclosed to the user.

## 6) PASS / WARN / FAIL Model (v1)

PASS:
- Core prose content complete and correct.
- Readable layout.
- Clutter removed.
- Images preserved or not materially required.

WARN:
Core prose content is complete and readable, but quality issues exist that do not destroy meaning.

WARN triggers include:
- Image could not be rendered -> placeholder + link to original.
- Table could not be rendered -> placeholder + link to original.
- Headings imperfect but still navigable.

Requirements:
- WARN must be visible in the HTML artifact (inline placeholders).
- WARN must be visible in console summary.

FAIL:
- Main text extraction incomplete (missing sections).
- Output unreadable or structurally broken.
- Silent corruption detected.

On FAIL:
- Exit non-zero with specific, documented error code.
- Do not output a Flowdoc artifact.
- Engine provides structured error detail for surface consumption.
- Surface translates error codes into user-friendly explanations.
- Error code catalog to be defined when surface is built.

## 7) WARN Behavior (User-Facing)

If one or more items trigger WARN:

Page-level summary (rendered at top of document, only if WARN exists):

> Notice: Some visual or structured content in this document could not be fully rendered. See inline notes below for details. [View original source](<source URL>)

Inline placeholders:

Missing image:
> [Image not included. View original](<source URL>)

Missing table:
> [Table not included. View original](<source URL>)

Linking rules:
- Always link to original page URL when available.
- If source URL is not available, omit the link (placeholder text only).
- Fragment anchors appended when available (optional, best-effort).

## 8) Console Summary (Always-On)

Every run (PASS / WARN / FAIL) outputs to stderr:
- Status (PASS / WARN / FAIL)
- Source (file path or URL if known)
- Output path
- Warning count (images, tables)
- Link to original source (if available)

## 9) Release Gate (v1)

Absolute requirement:
- 0% silent structural corruption.

Percentage gate (PASS + WARN threshold):
- To be set after test corpus is defined.
- FAIL is acceptable only if clearly signaled and explained.

Gate cannot be evaluated until:
- Test corpus is defined (categories and composition).
- User-facing surface exists for non-technical tester access.

## Release Gate

Non-negotiable:
- 0 REGRESSION
- 0 FAIL

Minimum thresholds:
- PASS >= 60%
- MARGINAL <= 40%

Current state (2026-03-04): 46 fixtures, 28 PASS (61%),
18 MARGINAL (39%), 0 REGRESSION, 0 FAIL.

These thresholds will be revisited after tasks 2a-7 to determine
if pipeline improvements have raised PASS rates above the minimum.

## 10) Test Surface (Pre-Release)

A disposable web page used to validate the product before v1 ships. Serves double duty as the prototype for the eventual production surface.

Part 1 -- Curated comparisons:
- Pre-selected articles across key content categories.
- Side-by-side or sequential: original vs Flowdoc output.
- Structured feedback form (readability, completeness, preference).
- Open-ended question: "If you could change one thing about how this looks, what would it be?"

Part 2 -- Sandbox:
- Paste a URL, get a Flowdoc document.
- Reveals what people actually want to convert.

Both parts use the same backend: URL in, engine processes HTML, document out.

The test surface is not the production surface. It is built fast, collects feedback, and informs the final surface form factor.

## 11) Tables (v1 and v2)

v1: Tables degrade to WARN placeholders with link to original source. No table rendering.

v2: Simple tables preserved structurally with readable styling. Complex tables remain WARN placeholders.

## 12) Typography and Customization

v1 defaults:
- BDA-aligned typography (font, spacing, contrast, line length).
- OpenDyslexic as an opt-in toggle.
- No user-configurable parameters beyond the font toggle.

Principle:
Defaults are opinionated and evidence-based. User customization is a surface-layer feature, not an engine concern. The engine produces good output without customization.

v2 direction (informed by tester feedback):
- Font choice, size, and spacing are likely customization targets.
- Specific controls to be determined by user feedback from the test surface, not by assumption.

## 13) Explicit v1 Non-Goals

Not required for v1:
- Perfect handling of complex interactive graphics.
- Full support for script-driven content or SPAs.
- Table rendering (v2).
- User accounts or personalization.
- Profile system or user-configurable typography parameters (beyond OpenDyslexic toggle).
- "Works on the entire web" claims.
- Fully offline image rendering (images use external URLs).

## 14) Honest Boundaries

Flowdoc v1 will not handle every content type. That is by design. The product is honest about its boundaries:

- Tables are flagged, not rendered. Table support is planned.
- Some content types (e.g. Wikipedia dense reference pages) may not convert well. These are known limitations, not defects.
- The tool works best on prose articles. When it encounters content outside its scope, it says so clearly.

Being explicit about what is coming next is part of the product, not an admission of failure.

## 15) Explicit TBD (Separate Sessions)

To be defined in focused follow-up sessions:

1. Corpus categories and composition.
   - Define the 7-10 content types that cover 80-90% of target use.
   - Assess current pipeline performance against each category.
   - Set corpus size, representative fixtures, and release gate percentage.

2. Print acceptance criteria.
   - A4 vs Letter, margins, page breaks.
   - What constitutes "prints cleanly."
   - Who evaluates and how.

3. Typography parameter lock.
   - Font size, line height, max width.
   - Current values vs final values.

4. Determinism formal definition.
   - Content byte-identical; provenance metadata excluded.
   - Document exact boundary.

5. Regression harness specification.
   - Automated checks for content quality.
   - Integration with corpus and release gate.

6. Surface form factor decision.
   - Informed by test surface feedback.
   - Web page, browser extension, or other.

7. Versioning and packaging strategy.
   - PyPI vs source-first.
   - Engine API surface.

8. Error code catalog.
   - Specific engine failure codes.
   - Defined when surface is built.

Each TBD must be resolved via:
- Defined experiment or investigation
- Measured output
- Locked decision
