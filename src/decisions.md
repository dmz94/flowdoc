# Technical Decisions and Rationale

This document captures key technical decisions for Flowdoc v1, including typography research, implementation choices, and the reasoning behind them.

---

## Project Origin

Flowdoc started with a simple request: convert a recipe PDF to make it easier for my dyslexic son to read.

I used PDF-XChange Editor to manually reformat the document with dyslexia-friendly typography, including the OpenDyslexic font. It worked, but the process was tedious and clunky. After finishing, I learned the recipe site could export to HTML.

That triggered a realization. At Oxford University Press, I managed the technology team for the dictionary division. We stored data in XML and JSON and built parsers to extract structured content from third-party dictionaries. If structured dictionaries could be parsed, so could structured recipes.

Recipe sites already contained semantic structure: headings, ingredients lists, instructions. The same pattern appeared in articles, documentation, and educational materials. The problem was broader than recipes.

The decision was to build a general-purpose tool, not a recipe manager. Start simple. Validate with real users. Expand only if it proves useful.

Flowdoc is that tool.

---

## Typography and Design Decisions

### Font Choices

Default: System font stack (Arial, Verdana)

Rationale:
- British Dyslexia Association recommends sans serif fonts such as Arial and Verdana
- Universally available
- No licensing concerns
- No embedding required
- Research shows standard sans serif fonts perform as well as specialized dyslexia fonts for speed and accuracy

v1 Font Toggle: OpenDyslexic (optional)

Implementation:
- Enabled via `--font opendyslexic`
- Embedded as base64 in CSS only when selected
- Not embedded by default

Research context:
- Most controlled studies show no reliable improvement over standard sans serif fonts
- Some preliminary evidence suggests possible comprehension benefits in longer texts for adults
- Individual preference varies significantly
- Provided as an option, not a recommendation

License: SIL Open Font License (OFL), embedding permitted

Deferred to v2:
- Lexend
- Atkinson Hyperlegible
- Dyslexie

See `1.5 Research_typography_guidelines.md` for full research summary.

---

## Spacing and Layout

Line Height  
Decision: 1.5 (150%)  
Rationale: Explicit BDA recommendation.

Letter Spacing  
Decision: ~0.02em starting point  
Rationale: Increased spacing can help readability, but excessive spacing reduces it. Conservative baseline validated via user testing.

Word Spacing  
Decision: ~0.16em (minimum 3.5× letter spacing)  
Rationale: Must scale proportionally with letter spacing to maintain word boundaries.

Line Length  
Decision: 6070 characters  
Rationale: Reduces eye-tracking fatigue and excessive line breaks.

Color and Contrast  
Decision:
- Background: Cream/off-white (#FEFCF4 or similar)
- Text: Dark gray/black (#333333 or darker)
- Contrast: WCAG AA minimum

Rationale: Pale backgrounds reduce glare and visual stress.

---

## Why HTML First?

Decision: v1 accepts HTML only.

Rationale:
- HTML already contains semantic structure
- Parsing is reliable
- Reduces ambiguity
- Focus remains on conversion quality

Deferred to v2: DOCX and Markdown input.

---

## Semantic HTML Requirement

Decision: Reject non-semantic HTML.

Rejection criteria:
- No h1h6 headings
- No p, ul, or ol elements
- Pure div-based layout

Error:
"Input HTML lacks semantic structure (no headings, paragraphs, or lists found). Flowdoc requires semantic HTML elements (h1-h6, p, ul, ol)."

Rationale: Dyslexia-friendly formatting depends on structure. Inferring structure from divs is unreliable.

---

## Main Content Selection

Deterministic rule:
1. Use `<main>` if present
2. Else `<article>`
3. Else `<body>`

If multiple article elements exist: Use the first article element. Additional article elements are ignored.

Drop entirely:
- nav
- header
- footer
- aside

Rationale: Predictable and testable behavior aligned with HTML5 semantics.

---

## HTML Element Handling

Supported:
- h1h6
- p
- ol, ul
- blockquote
- pre, code
- em, strong
- a (href only)

Tables:
- Replace with "[Table omitted - X rows, Y columns]"
- Count tr elements for rows
- Count maximum immediate td/th children for columns

Images:
- If alt exists: "[Image: alt text]"
- Else: "[Image omitted]"

Figures:
- Preserve figcaption text
- Handle embedded images per image policy

Footnotes:
- Convert to paragraphs at reference point
- Drop markers

Forms:
- Replace with "[Form omitted]"

Dropped:
- nav
- aside
- header
- footer
- advertisements
- decorative containers

---

## Inline Handling

Whitespace:
Preserve standard HTML whitespace collapsing rules.

Example:
`word<strong>next</strong>` renders as "word next".

Nested inline tags:
Support one level. Flatten deeper nesting while preserving innermost semantic meaning.

---

## HTML Sanitization

Drop entirely:
- script tags
- event handlers
- iframe
- object
- embed
- all active content

Keep:
- href (links only)

Drop attributes:
- style
- class
- id
- data-*
- event handlers

URL Handling:
* Strip javascript: protocol URLs entirely
* Preserve http: and https: URLs in href attributes
* Preserve fragment identifiers (hash links) for internal navigation
* Remove data: URLs

Rationale: Prevent script injection and layout leakage.

---

## PDF Strategy

Decision: v1 uses browser print-to-PDF.

Rationale:
- Preserves CSS exactly
- No heavy dependencies
- Cross-platform

Deferred:
Native PDF generation (e.g., headless browser) due to dependency size and complexity.

---

## Readability Over Fidelity

Flowdoc does not preserve original layout, branding, or geometry.

Rationale:
Dyslexia-friendly formatting requires specific typography and spacing. Layout preservation would undermine readability.

---

## CLI Failure Semantics

Exit codes:
- 0: Success
- 1: Parse error
- 2: Render error
- 3: I/O error

Errors:
- Written to stderr
- stdout contains only output HTML

Non-semantic input:
- Hard fail
- Exit code 1
- Clear error message
- No best-effort conversion

---

## CSS Invariants

Typography:
- Arial or Verdana (or OpenDyslexic if toggled)
- Font size: 18px body text (default; BDA baseline range is 16-19px, but 18px chosen for consistency and screen readability)
- Line height 1.5
- Letter spacing ~0.02em
- Word spacing ~0.16em

Layout:
- 6070 character line width
- Single column
- Generous margins
- Left-aligned

Spacing:
- Headings =20% larger than body
- =1em paragraph spacing
- =1.5em before headings
- Clear list indentation

Color:
- Cream background
- Dark text
- WCAG AA contrast

Links:
- Underlined or clearly distinct
- Remain identifiable in print

Print:
- Do not shrink below 12pt
- Adequate margins
- Maintain contrast in black-and-white

---

## Success Criteria for v1

1. Accepts semantic HTML
2. Produces self-contained readable HTML
3. Improves measurable readability for dyslexic readers
4. Works across browsers, mobile, and print
5. CLI is simple
6. Licensing documented
7. Predictable failure modes
8. Correct inline rendering
9. Graceful degradation for unsupported elements
10. Secure sanitization

---

## Research Sources

- British Dyslexia Association (2023). Dyslexia Friendly Style Guide
- Kuster et al. (2018). Annals of Dyslexia
- Marinus et al. (2016). Dyslexia
- Wery & Diliberto (2017). Annals of Dyslexia
- Rello & Baeza-Yates (2013). ACM SIGACCESS
- Zorzi et al. (2012). PNAS
- Franzen et al. (2019). Annals of Eye Science (conference abstract)

See `1.5 Research_typography_guidelines.md` for full research detail.