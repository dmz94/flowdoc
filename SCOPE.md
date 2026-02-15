# Flowdoc - Scope Document

**Version:** 1.0  
**Status:** Frozen for v1 development

---

## What is Flowdoc?

Flowdoc is a general-purpose document converter that transforms structured documents into dyslexia-friendly, readable formats.

**v1 is optimized for text-flow documents** - content with headings, paragraphs, and lists - rather than complex layout replication or visual design preservation.

The tool accepts documents with semantic structure and produces optimized output with:
- Dyslexia-friendly typography (defaults informed by research and tuned via reader feedback)
- Proper spacing and layout
- Single-column, flowed presentation
- Cross-platform compatibility (modern browsers, mobile devices, print)

---

## Design Principle: Readability Over Fidelity

**Flowdoc intentionally does not preserve original layout, branding, or page geometry.**

The goal is readable content for dyslexic readers, not visual reproduction of the source document. Output may look completely different from the original - this is by design, not a limitation.

---

## Use Cases

Flowdoc works on text-based structured content:

- Recipes
- Articles and blog posts
- Educational materials
- Technical documentation
- Instructional content (how-tos, manuals)
- Work documents
- Any document with headings, paragraphs, and lists

---

## v1 Scope

### Input Format

**HTML only** (Tier-1 input)

**Requirements:**
- Must contain semantic structure: headings (h1-h6), paragraphs (p), lists (ul, ol)
- "Semantic HTML" means proper use of semantic tags, not div-based layouts ("div soup")
- Content must have text-flow structure (headings, paragraphs, lists)

**Flowdoc will reject non-semantic HTML with a clear error message.**

Rejection criteria (operational definition):
* Input lacks at least one h1-h3 heading
* Input lacks p, ul, or ol elements for body content
* Input is div-only layout structure with no semantic tags
* Missing heading hierarchy triggers error

Error message: "Input HTML lacks semantic structure (no headings, paragraphs, or lists found). Flowdoc requires semantic HTML elements (h1-h6, p, ul, ol)."

### Output Format

**Readable HTML** (canonical output)

**Self-contained HTML definition:**
- No external dependencies (no external CSS, fonts, scripts, or images)
- All CSS inlined in a single `<style>` block
- Fonts are NOT embedded by default (system font stack used)
- Fonts ARE embedded only when OpenDyslexic toggle is used (see below)
- Output is a single HTML file that works offline

**Compatibility:**
- Modern browsers (recent versions of Chrome, Edge, Safari, Firefox)
- Mobile devices (iOS, Android)
- Print (via browser print-to-PDF)

### HTML Element Handling

**Supported (v1 first-class):**
- Headings (h1-h6)
- Paragraphs (p)
- Ordered lists (ol)
- Unordered lists (ul)
- Blockquotes (blockquote)
- Code blocks (pre, code)
- Inline emphasis (em, strong)
- Links (a with href)
- Inline code (code within paragraphs)

**Degrades with placeholders (v1):**
- Tables -> `[Table omitted - X rows, Y columns]`
- Images -> `[Image: alt text]` or `[Image omitted]` if alt missing
- Figures/captions -> Caption text preserved, image handled per image policy
- Footnotes/endnotes -> Converted to regular paragraphs at point of reference

**Dropped (v1):**
- Navigation (nav)
- Sidebars (aside)
- Headers/footers (header, footer)
- Advertisements
- Decorative containers
- Scripts, event handlers, active content (security)

### OpenDyslexic Font Toggle

**In scope for v1:**
- Optional OpenDyslexic font toggle (accessed via `--font opendyslexic` CLI flag)
- NOT the default font
- Provided as a preference toggle; no claim of universal improvement
- OpenDyslexic is embedded only when selected; otherwise system font stack (Arial, Verdana) is used and no fonts are embedded
- Note: Enabling OpenDyslexic embeds font files and increases output file size significantly.

**Out of scope for v1:**
- Multiple font toggles (Lexend, Dyslexie, Atkinson Hyperlegible, etc.)
- v1 supports exactly two font options: system fonts OR OpenDyslexic

### Core Features
- Parse HTML semantic structure
- Apply dyslexia-friendly typography
- Optimize spacing, line height, margins
- Single-column layout
- Command-line interface
- Deterministic content selection (main -> article -> body)
- HTML sanitization:
  * Remove all script tags and content
  * Strip inline event handlers (onclick, onload, etc.)
  * Remove external resource URLs
  * Drop iframe, object, embed elements
  * Drop all active content

---

## Non-Goals (Out of Scope for v1)

### Input
- PDF files (fixed layout, hard to parse reliably)
- DOCX files (defer to v2)
- Markdown files (defer to v2)
- Image-based documents (OCR out of scope)
- "Div soup" HTML without semantic structure

### Output
- Native PDF generation (v1 uses browser print-to-PDF)
- DOCX output
- Layout fidelity or visual preservation
- Preserving original branding or page geometry

### Features
- Graphical user interface (GUI)
- Cloud service or web app
- Recipe-specific features (ingredient parsing, nutrition facts, etc.)
- Image processing or optimization
- Real-time collaborative editing
- Document editing (conversion only, not an editor)
- Complex layout replication

### Domain Specificity
- Recipe manager functionality
- Domain-specific parsers (recipes, legal docs, etc.)
- Content management

---

## Print-to-PDF Workflow

**Print-to-PDF via browser is an acceptable v1 workflow; native PDF export is out of scope for v1.**

Browser print-to-PDF:
- Preserves CSS exactly as rendered
- Works on all modern browsers
- Sufficient for v1 needs
- No additional dependencies required

Native PDF generation deferred to v2.

---

## Scope Boundaries

**What Flowdoc IS:**
- A document converter
- A command-line tool
- General-purpose (works on any structured text with semantic HTML)
- Focused on dyslexia-friendly readability
- Optimized for text-flow documents (headings, paragraphs, lists)

**What Flowdoc IS NOT:**
- A recipe app
- A PDF repair tool
- A document editor
- A layout preservation tool
- A browser extension
- A cloud service
- A visual design replicator

---

## Why These Boundaries?

### HTML First
HTML already contains semantic structure. Parsing is straightforward and reliable. Other formats (DOCX, Markdown) can be added in v2 once core value is proven.

### No PDF Input
PDFs are fixed-layout formats. Extracting semantic structure is unreliable and error-prone. Starting with structured inputs (HTML) allows focus on the conversion quality, not parsing complexity.

### No Native PDF Output (v1)
Browser print-to-PDF works well and preserves CSS. Adding programmatic PDF generation (via headless Chrome) adds ~300MB dependency and significant complexity before validating core value.

### General-Purpose, Not Recipe-Specific
The trigger for this project was a recipe, but the problem is broader: any document can benefit from dyslexia-friendly formatting. Building a general tool maximizes utility and prevents over-fitting to one use case.

### Readability Over Fidelity
Preserving original layout defeats the purpose. Dyslexia-friendly formatting requires specific typography, spacing, and structure that are incompatible with arbitrary visual designs.

---

## Success Criteria for v1

1. Takes an HTML file with semantic structure
2. Produces a self-contained, readable HTML file
3. **Output is measurably better for dyslexic readers**
   * Validation framework:
      * Fewer self-reported re-read events during timed reading task
      * Lower fatigue score on 1-5 scale after 3-minute reading session
      * Fewer line-loss incidents counted during reading
   * Measured via comparison with original formatting using same content
   * Tested with dyslexic readers (minimum N=5 for v1 validation)
4. Works reliably on modern browsers, mobile devices, and print
5. Command-line interface is simple and functional
6. Font licensing is clear and documented (OpenDyslexic SIL-OFL)
7. Failure modes are predictable and consistent
8. Inline elements (links, emphasis, code) render correctly
9. Unsupported elements (tables, images) degrade gracefully per defined policy
10. HTML sanitization prevents security issues

If v1 meets these criteria, scope expansion is justified.  
If not, scope expansion is premature.

---

## Future Considerations (v2 and Beyond)

These are explicitly out of scope for v1 but may be considered after validation:

### Additional Input Formats
- DOCX input (via libraries like python-docx or mammoth)
- Markdown input (easy addition)

### Additional Output Formats
- Native PDF output (if browser print proves insufficient)

### Additional Font Options
- Lexend, Atkinson Hyperlegible, Dyslexie (beyond OpenDyslexic)

### Content Transformation
- Text-to-speech compatibility enhancements
- Readability scoring and improvement
- Sentence simplification
- Jargon expansion

### Other Enhancements
- Configurable themes beyond high-contrast
- Local web preview mode
- Batch conversion

**v1 must prove core value before expanding scope.**

---

## Summary

Flowdoc v1 is a focused tool:
- Converts semantic HTML to dyslexia-friendly HTML
- Prioritizes readability over visual fidelity
- Supports or degrades HTML elements deterministically
- Offers optional OpenDyslexic font toggle
- Uses browser print-to-PDF for PDF output
- Targets modern browsers and mobile devices
- Validates with dyslexic readers before expansion

Scope is intentionally narrow to ship a working, validated v1.
