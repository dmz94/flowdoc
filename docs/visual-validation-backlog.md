# Flowdoc Visual Validation Backlog

Generated: February 25, 2026
Source: First visual validation run of dual-pipeline (transform/extract) architecture
Fixtures tested: 9 of 11 (wikipedia_dyslexia skipped - same issues as photosynthesis)

---

## Priority 1 - Small Fixable Bugs

These are targeted code fixes, likely trivial.

### P1-1: Empty paragraphs in output
- Symptom: `<p></p>` appearing in output, visible as blank space
- Seen in: readability_001_tech_blog (after image placeholder), clevelandclinic
- Likely cause: Parser emitting empty paragraph blocks, renderer not filtering them
- Fix: Strip empty blocks in parser or renderer before output

### P1-2: Title whitespace
- Symptom: NHS title renders as "Dyslexia\n - NHS" with embedded newline
- Seen in: nhs_dyslexia
- Likely cause: Title tag contains whitespace/newlines, not stripped on capture
- Fix: Strip and normalize whitespace when capturing original_title in parser.py

### P1-3: "Advertisement" text surviving extraction
- Symptom: Paragraph containing just "Advertisement" appears inline in content
- Seen in: clevelandclinic (appears 3 times)
- Likely cause: Trafilatura keeping Cleveland Clinic's ad marker divs as text
- Fix: Post-extraction filter - strip paragraphs whose stripped text == "Advertisement"

### P1-4: Trailing boilerplate in Cleveland Clinic output
- Symptom: "Better health starts here", "Subscribe", "About Cleveland Clinic",
  "Experts You Can Trust", duplicate References section after main content
- Seen in: clevelandclinic
- Likely cause: Trafilatura not stripping CMS footer elements on this site
- Fix: Investigate - may need post-extraction truncation at first footer/aside heading

---

## Priority 2 - Trafilatura Limitations (Assess Fix vs Document)

These come from Trafilatura's behavior. May be fixable with post-processing,
or may need to be accepted as documented extract mode limitations.

### P2-1: Inline code becoming standalone pre blocks
- Symptom: `<code>Cow</code>` inside a sentence becomes a full `<pre>` block,
  breaking the paragraph into fragments ("let's reuse the silly" ... [pre block] ... "example")
- Seen in: readability_001_tech_blog
- Likely cause: Trafilatura promoting inline code to block level
- Options: (a) post-process to re-inline short pre blocks, (b) document as known limitation

### P2-2: Missing spaces around inline elements
- Symptom: "data-cover attribute" loses space -> "data-coverattribute",
  "must be" loses space -> "mustbe"
- Seen in: readability_001_tech_blog (list items)
- Likely cause: Trafilatura inline spacing issue
- Options: (a) post-process to add spaces around inline elements, (b) document

### P2-3: Duplicate list items from nested structures
- Symptom: Nested list item content appears as both a nested item AND a
  standalone top-level list item
- Seen in: wikihow_ride_a_bike
- Likely cause: Trafilatura flattening nested lists incorrectly
- Options: (a) deduplicate adjacent identical list items, (b) document

### P2-4: Wikipedia lead section fragmentation
- Symptom: Dense link paragraph breaks into dozens of single-phrase paragraphs,
  each containing one linked term ("biological processes by which", "autotrophic",
  "organisms, such as most")
- Seen in: wikipedia_photosynthesis, wikipedia_dyslexia (assumed)
- Likely cause: Trafilatura splitting on inline links in dense Wikipedia lead sections
- Options: (a) post-process to merge short adjacent paragraphs, (b) document as
  Wikipedia-specific limitation, (c) defer to v2

---

## Priority 3 - Accessibility Concern

### P3-1: Italic rendering harmful for dyslexic readers
- Symptom: Large sections rendered in italic (Gutenberg Preface is entirely italic)
- Seen in: gutenberg_pride_prejudice (Preface section)
- Root cause: Gutenberg wraps entire Preface in one long `<em>` block. We render
  `<em>` as `<em>` which browsers display as italic. Italic is harder for dyslexic readers
  per BDA guidelines.
- Options:
  (a) Strip `<em>` entirely - loses emphasis semantics
  (b) Render `<em>` as non-italic style (e.g. slight color change or underline)
  (c) CSS override: add `em { font-style: normal; font-weight: bold; }` to renderer
- Recommended: Option (c) - simplest, preserves semantics visually without italic
- Note: This is a genuine accessibility issue, not cosmetic

---

## Priority 4 - Scope Boundaries (Do Not Fix in v1)

These are documented as out of scope. Record here for v2 consideration.

### P4-1: MDN reference table pages
- Issue: MDN HTML elements page content lives entirely in tables. We strip tables.
  Output is nearly empty - just section headings and [Table omitted] placeholders.
- Decision: Wrong input type for Flowdoc. Flowdoc is for prose articles.
- Action: None for v1. Consider table rendering in v2.

### P4-2: BBC Good Food validation failure
- Issue: Trafilatura strips all heading structure from recipe pages.
  Validation fails because no h1-h3 survives extraction.
- Decision: Recipe sites with this structure are out of scope for v1.
- Action: None for v1.

### P4-3: Gutenberg page number artifacts
- Issue: {xvi}, {12}, {14} etc. appearing inline as linked anchors in Gutenberg HTML
- Decision: Gutenberg-specific markup. Low impact - reader can mentally ignore.
- Action: Could strip with simple regex post-processing but not worth it for v1.

---

## Suggested Work Order for Next Session

1. P3-1 (italic/em) - one-line CSS fix, high accessibility impact, do this first
2. P1-2 (title whitespace) - trivial string strip
3. P1-1 (empty paragraphs) - small filter in parser or renderer
4. P1-3 (advertisement text) - small post-extraction filter
5. P2-1 (inline code fragmentation) - assess complexity, fix or document
6. P2-2 (missing spaces) - assess complexity, fix or document
7. P1-4 (Cleveland Clinic trailing boilerplate) - investigate, may be complex
8. P2-3 (duplicate list items) - assess complexity, fix or document
9. P2-4 (Wikipedia fragmentation) - likely document as v2

After fixes: re-run convert_fixtures.py and visually verify improvements
before implementing golden file tests.
