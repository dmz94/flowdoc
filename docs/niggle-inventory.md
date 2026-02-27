# Niggle Inventory - Phase 2C (Classified)

Corpus: 10 user-study fixtures (`tests/fixtures/user-study/`).
Pipeline: baseline extraction mode → parse → render.
Date: 2026-02-27.

Classes:
- A) Boundary — start/end trimming issue
- B) Structural artifact — empty elements, duplicate sections, orphan lists, broken structure
- C) Sanitization / normalization — placeholder tokens, duplicated media blocks, minor markup noise
- D) Extraction failure — article body missing or fundamentally wrong extraction

---

## Recurring Patterns

### Pattern: Consecutive [Form omitted] cluster
Class: C
Fixtures:
- aeon — leading position, elements [6]–[11] (×6 consecutive)
- aeon — tail, last 4 elements (×4 consecutive)
- eater — elements [49]–[50] and [57]–[58] (×2 pairs)
- propublica — elements [2]–[6] (×5 consecutive)

Description:
Multiple consecutive `[Form omitted]` paragraphs grouped together, from newsletter
sign-up, share, save, or subscription form widgets embedded in the CMS template.
Individual `[Form omitted]` tokens are correct per decisions.md §7; the artifact is
the dense clustering that produces visual noise in the output.

---

### Pattern: [-] hr-placeholder density
Class: C
Fixtures:
- eater — ×3 distributed, including at final element
- propublica — ×10 distributed throughout article body

Description:
Multiple `<p>[-]</p>` paragraphs from `<hr>` elements in the source. Per decisions.md
§7, `[-]` is the correct placeholder for `<hr>`; however high density (3+ instances)
produces noise and, in propublica, originates from section-divider `<hr>`s in
non-article sections that should not have been extracted.

---

### Pattern: Trailing non-article section
Class: A
Fixtures:
- aeon — tail (×4 `[Form omitted]` subscription forms; no section heading; last 4 elements)
- eater — `"More in "` section with 25 image/link blocks (second-to-last section, elements [64]–[84])
- pbs — `"Educate your inbox"` section with subscription pitch, form placeholder, sponsor logo list (last 4 elements)
- propublica — `"Contributors"` section with author bios, social share link lists, repeated bio text, form placeholder (last ~10 elements)

Description:
A named or unnamed section at the end of the document containing only non-article
content — newsletter subscription widgets, related-article carousels, author bio
social links. Not stripped by Trafilatura or the current post-processing pipeline.

---

### Pattern: Leading metadata paragraphs
Class: A
Fixtures:
- aeon — author byline (`"by Graham Shields + BIO"`), image credit, truncated bio sentence, editor credit (`"Edited by Richard Fisher"`) — elements [2]–[5], immediately after title
- pbs — photographer credit (`"Stan Choe, Associated Press Stan Choe, Associated Press"`) — element [4]

Description:
Author byline, image credits, editor credits, or photographer credits rendered as
body paragraphs in the leading position, between the document title and the first
sentence of article prose. Extracted by Trafilatura as content paragraphs.

---

### Pattern: Extraction failure — no article body
Class: D
Fixtures:
- guardian — 21 elements, all navigation/related-links; main article prose absent entirely
- theringer — 4 elements, all navigation stub; main article prose absent entirely

Description:
Trafilatura extracts navigation, sidebar, or related-content structure instead of
the article body. The main article prose is entirely absent from the output. Both
fixtures currently pass validation (headings and paragraphs are technically present)
but produce no usable article content.

---

## Fixture-Specific Issues

### aeon

- Artifact: Inverted heading order at document start
  - Class: B
  - Description: The document opens with `<h2>The snowball effect</h2>` followed by `<h1>Our planet was once...`. The h2 precedes the h1, producing a reversed semantic hierarchy. Aeon uses the h2 as a section label above the h1 title.
  - Snippet: `<h2>The snowball effect</h2>` immediately before `<h1>Our planet was once a harsh, alien, icy world...`
  - Position: Elements [0]–[1], document start.

- Artifact: Audio player widget remnants
  - Class: B
  - Description: Two paragraphs from Aeon's audio player widget — `"Listen to this essay"` and `"23 minute listen"` — rendered as body text between the leading form cluster and the article content.
  - Snippet: `<p>Listen to this essay</p>` / `<p>23 minute listen</p>`
  - Position: Elements [12]–[13].

---

### cdc

- Artifact: Trailing whitespace artifact in cross-reference paragraph
  - Class: C
  - Description: Final paragraph ends with `"West Nile Virus Disease ."` — a space before the period marks the link element boundary after whitespace collapsing. Minor normalization artifact; the paragraph content is a legitimate cross-reference.
  - Snippet: `<p>Healthcare providers, see Treatment and Prevention of West Nile Virus Disease .</p>`
  - Position: Last element.

---

### eater

- Artifact: Empty `<ul>` with two empty `<li>` elements
  - Class: B
  - Description: A list with two empty list items appears as the third element. No visible content; produces an empty list block in the output.
  - Snippet: `<ul><li></li><li></li></ul>`
  - Position: Element [2], immediately after title and intro paragraph.

- Artifact: Duplicate consecutive image placeholders (×7 pairs)
  - Class: C
  - Description: Image placeholder paragraphs appear in consecutive identical pairs — each image produces two `[Image: alt]` paragraphs back-to-back. Affects 7 distinct images.
  - Snippet: `<p>[Image: shutterstock_2313618733 edit]</p><p>[Image: shutterstock_2313618733 edit]</p>` (×7 pairs)
  - Position: Elements [3]–[4]; also [66]–[67], [69]–[70], [72]–[73], [75]–[76], [78]–[79], [81]–[82].

---

### guardian

*(Primary artifact is the "Extraction failure" recurring pattern above. The following are secondary structural artifacts present within the failed extraction.)*

- Artifact: Duplicate `"More on this story"` heading
  - Class: B
  - Description: `<h2>More on this story</h2>` appears twice in the document — once at element [0] and again at element [3], each with its own pair of `[Form omitted]` blocks.
  - Snippet: `<h2>More on this story</h2>` at elements [0] and [3].
  - Position: Elements [0] and [3].

- Artifact: Duplicate `"Most viewed"` heading
  - Class: B
  - Description: `<h2>Most viewed</h2>` appears twice consecutively at the document end.
  - Snippet: `<h2>Most viewed</h2><h2>Most viewed</h2>`
  - Position: Elements [18]–[19].

- Artifact: Two empty `<ol>` elements
  - Class: B
  - Description: Two ordered list elements with no list items rendered.
  - Snippet: `<ol></ol>`
  - Position: Elements [7] and [20].

---

### nhs

- Artifact: Trailing CMS review date metadata
  - Class: A
  - Description: Final paragraph is a page review date stamp from the NHS CMS template, not article content.
  - Snippet: `<p>Page last reviewed: 07 March 2022 Next review due: 07 March 2025</p>`
  - Position: Last element.

---

### pbs

- Artifact: Related-article list at document start
  - Class: A
  - Description: A `<ul>` containing related article titles, bylines, and publication dates appears immediately after the title paragraph. A "Related stories" widget, not article content.
  - Snippet: `<ul><li>What went wrong at the Astroworld Festival... By Lisa Desjardins...</li><li>Astroworld concert victims...</li>...</ul>`
  - Position: Element [2], after title.

- Artifact: Tag list rendered as `<ul>` at document start
  - Class: A
  - Description: A `<ul>` of article tags (canvas, concert, crowd, travis scott) with href links appears immediately after the related-article list.
  - Snippet: `<ul><li><a href="...">canvas</a></li><li><a href="...">concert</a></li><li><a href="...">crowd</a></li><li><a href="...">travis scott</a></li></ul>`
  - Position: Element [3].

- Artifact: Duplicate related-article list mid-document
  - Class: B
  - Description: The same related-article `<ul>` from element [2] reappears under a `"Go Deeper"` heading mid-document.
  - Snippet: Same `<ul>` content as element [2], under `<h2>Go Deeper</h2>`.
  - Position: Mid-document.

---

### propublica

- Artifact: `"Republish This Story for Free"` section
  - Class: A
  - Description: A full section headed `<h2>Republish This Story for Free</h2>` containing Creative Commons license terms, republication conditions, and form placeholders, appearing before the article body.
  - Snippet: `<h2>Republish This Story for Free</h2>` / `<p>Creative Commons License (CC BY-NC-ND 3.0)</p>` / `<p>[-]</p>` / `<p>Thank you for your interest in republishing...</p>` / `<ul>You have to credit ProPublica...</ul>` / `<p>[Form omitted]</p>` × 2
  - Position: Elements [7]–[13], before article body.

---

### skysports

- Artifact: Trailing poll call-to-action
  - Class: A
  - Description: Final paragraph is a call-to-action referencing an interactive poll widget not present in the output.
  - Snippet: `<p>Have your say on the biggest reason in our poll.</p>`
  - Position: Last element.

---

### smithsonian

- Artifact: Split paragraph — sentence fragments separated from context
  - Class: B
  - Description: A sentence or caption rendered as two consecutive standalone paragraphs: `"Homo sapiens while a European branch leads to"` and `"Homo neanderthalensis and the Denisovans."` These are fragments of a single inline text or image caption broken at a `<p>` boundary by the extraction process.
  - Snippet: `<p>Homo sapiens while a European branch leads to</p>` / `<p>Homo neanderthalensis and the Denisovans.</p>`
  - Position: Elements [5]–[6].

---

### theringer

*(Primary artifact is the "Extraction failure" recurring pattern above. The following is a secondary structural artifact within the failed extraction.)*

- Artifact: Two consecutive empty `<h1>` headings
  - Class: B
  - Description: The document opens with two `<h1>` elements containing no text — structural shells with no content.
  - Snippet: `<h1></h1><h1></h1>`
  - Position: Elements [0]–[1], document start.

---

## Summary

Total distinct artifact entries: 21
(5 recurring patterns + 16 fixture-specific issues)

Class A (Boundary — start/end trimming): 7
- Recurring: trailing non-article section (4 fixtures), leading metadata paragraphs (2 fixtures)
- Fixture-specific: nhs trailing review date, pbs related-article list at start, pbs tag list at start, propublica republish section, skysports poll CTA

Class B (Structural artifact): 9
- Fixture-specific: aeon inverted heading order, aeon audio widget remnants, eater empty ul, guardian duplicate "More on this story", guardian duplicate "Most viewed", guardian empty ol ×2, pbs duplicate related-article list mid-doc, smithsonian split paragraph, theringer empty h1 ×2

Class C (Sanitization / normalization): 4
- Recurring: consecutive [Form omitted] clusters (3 fixtures), [-] hr-placeholder density (2 fixtures)
- Fixture-specific: cdc trailing whitespace artifact, eater duplicate consecutive image placeholders

Class D (Extraction failure): 1
- Recurring: no article body extracted (guardian, theringer)

Fixtures with no artifacts observed: smithsonian (1 minor B only), nhs (1 minor A only).
Fixtures with complete extraction failure: guardian, theringer.
Fixtures with heaviest artifact load: aeon (6 entries), propublica (4 entries), pbs (4 entries), eater (4 entries).

---

## Burn-Down Order – Phase 2C

Ordering principles: deterministic-structural first; end-anchored preferred; no site-specific strings; lowest blast radius earliest; Class D last.

---

### 1. Drop empty list blocks
Class: B
Scope: Filter ListBlock nodes with zero items from section blocks during parse.
Affected fixtures: eater (element [2]: `<ul><li></li><li></li></ul>`), guardian (elements [7], [20]: `<ol></ol>`)
Rationale: A list with no items renders nothing and is unambiguously an artifact. Purely structural, no content heuristic required. No blast radius — legitimate lists always have at least one item.
Expected blast radius: Low

---

### 2. Drop empty heading elements
Class: B
Scope: Filter Section nodes whose heading contains no inline text (all inlines empty or whitespace-only) from the section list during build_sections.
Affected fixtures: theringer (elements [0]–[1]: two empty `<h1>`)
Rationale: A heading with no text content is structurally inert. Purely structural check on inline content. No blast radius — legitimate headings always have text.
Expected blast radius: Low

---

### 3. Collapse consecutive identical placeholder blocks
Class: C
Scope: After build_sections, deduplicate runs of consecutive identical Paragraph blocks where the full text matches a known placeholder token (`[Form omitted]`, `[Image omitted]`, or any `[Image: ...]`). Collapse N≥2 consecutive identical blocks to 1.
Affected fixtures: aeon (×6 leading, ×4 tail), eater (×2 pairs [Form omitted]; ×7 pairs image placeholders), propublica (×5 leading)
Rationale: Consecutive identical placeholder blocks are always an extraction/HTML duplicate artifact — the same widget or image appears twice in the source DOM. Deduplication is purely structural (same block type, same text, consecutive). Does not affect non-placeholder paragraphs. Does not remove all forms, only duplicates.
Expected blast radius: Low

---

### 4. Drop duplicate consecutive headings
Class: B
Scope: After build_sections, remove a Section if its heading text (plain text, normalized) is identical to the immediately preceding Section's heading text.
Affected fixtures: guardian (duplicate `"More on this story"` sections [0] and [3]; duplicate `"Most viewed"` headings [18]–[19])
Rationale: Two consecutive sections with the same heading text is always an extraction artifact. Structural check on adjacent section heading content. No legitimate document has the same heading twice in a row.
Expected blast radius: Low

---

### 5. Extend trailing section drop to all-placeholder sections
Class: A
Scope: Extend `drop_trailing_orphan_section` to also drop the final section if all its blocks consist exclusively of placeholder tokens (`[Form omitted]`, `[Image omitted]`, `[Image: ...]`, `[-]`). Structural check on block content only. Still end-anchored.
Affected fixtures: aeon (tail: 4 `[Form omitted]` blocks, no heading — currently not caught because aeon tail has no section heading), pbs (`"Educate your inbox"`: 3 blocks — all placeholder/sponsor-image), propublica (`"Contributors"`: last section mixes bio text with social links and form — evaluate whether all-placeholder criterion fits; may require per-block content scoring)
Rationale: Extends the existing orphan-drop mechanism with one additional structural predicate. End-anchored, still no site-specific strings. Covers cases where Trafilatura extracted a trailing section that contains real-looking structure but only placeholder content.
Expected blast radius: Low–Medium (the all-placeholder check must not fire on legitimate image-heavy sections mid-document; end-anchoring constrains it)

---

### 6. End-anchored single-paragraph tail pattern anchors
Class: A
Scope: Add to `_TAIL_BOILERPLATE_ANCHORS` in the existing `trim_trailing_boilerplate` mechanism:
- `"Page last reviewed:"` (nhs review date stamp)
- `"Have your say"` (skysports poll CTA)
These are end-anchored, single-paragraph patterns analogous to the existing `"Follow Cleveland Clinic"` anchor.
Affected fixtures: nhs (trailing review date), skysports (trailing poll CTA)
Rationale: Both are single trailing paragraphs with no article content. The anchor strings are not site-specific in the narrow sense — any NHS-family or interactive-widget site could produce the same patterns — and the existing infrastructure already handles this class of fix with low risk.
Expected blast radius: Low (end-anchored; pattern only fires on the last _TAIL_SCAN_LIMIT blocks)

---

### 7. Leading metadata block trim
Class: A
Scope: After build_sections, scan the first N blocks (N ≤ 5) of the first section. Drop blocks whose full text matches structural metadata patterns: lines beginning with `"by "`, lines consisting entirely of a credit/attribution phrase (image credit, editor credit, photographer credit patterns). Anchor: stop scanning at the first block that contains ≥ 20 words of non-metadata prose.
Affected fixtures: aeon (byline, image credit, bio fragment, editor credit — elements [2]–[5]), pbs (photographer credit — element [4])
Rationale: Author bylines and credits are consistently short (< 15 words), appear in the leading position, and follow recognizable patterns (`"by "` prefix, `"Associated Press"` suffix, `"Edited by"` prefix, image credit phrasing). Start-anchored analogue of the tail boilerplate trimmer. Moderate risk because the pattern heuristic must not fire on legitimate short opening paragraphs.
Expected blast radius: Medium

---

### 8. Mid-document non-article section: propublica "Republish This Story for Free"
Class: A
Scope: Drop a section whose heading text exactly matches a known non-article section name. Seed list: `"Republish This Story for Free"`. Not end-anchored; requires a heading-text blocklist.
Affected fixtures: propublica (elements [7]–[13])
Rationale: This section appears consistently on every ProPublica article and is unambiguously non-article content. However, a heading-text blocklist introduces site-specific strings and is not structural. Should be considered only after structural alternatives are exhausted. Acceptable as a known-limitation deferral if blocklist approach is rejected.
Expected blast radius: Medium (blocklist approach; any change to heading matching could affect legitimate sections)

---

### 9. PBS duplicate related-article list mid-document
Class: B
Scope: After build_sections, detect and drop duplicate ListBlock nodes within a section where the list content (normalized text) is identical to a ListBlock appearing earlier in the same document.
Affected fixtures: pbs (related-article `<ul>` at element [2] reappears under `"Go Deeper"`)
Rationale: Content-level deduplication is more complex than structural deduplication (item 3) because it requires comparing block text across sections, not just consecutive identical placeholders. Risk of false positives on legitimate repeated lists.
Expected blast radius: Medium

---

### 10. Aeon audio player widget remnants
Class: B
Scope: Drop leading paragraphs whose full text matches audio widget UI strings (`"Listen to this essay"`, `"[N] minute listen"`).
Affected fixtures: aeon (elements [12]–[13])
Rationale: Text-specific match for one fixture's widget. No structural generalisation available. Candidate for "accept as known limitation" if the leading metadata trim (item 7) does not subsume it. Low priority — only affects aeon; content is obviously non-article but requires a pattern string.
Expected blast radius: Low (single fixture, narrow pattern)

---

### 11. Aeon inverted heading order
Class: B
Scope: Detect and correct h2-before-h1 inversion at document start. Swap heading levels when the first heading is h2 and the second heading is h1 and they are in the same or adjacent sections.
Affected fixtures: aeon (h2 `"The snowball effect"` before h1 title)
Rationale: The inverted order is a source-HTML authoring choice (Aeon places a category label above the article title using h2). Correcting it requires semantic inference about which heading is the title. High risk of incorrect behaviour on other fixtures with legitimate h2-first structures. Candidate for "accept as known limitation."
Expected blast radius: Medium–High

---

### 12. Smithsonian split paragraph fragments
Class: B
Scope: Detect and merge consecutive paragraphs where the first ends without terminal punctuation and the second begins with a capital proper noun or continuation phrase.
Affected fixtures: smithsonian (elements [5]–[6]: `"Homo sapiens while a European branch leads to"` / `"Homo neanderthalensis and the Denisovans."`)
Rationale: The split originates from an inline image or figure element in the source breaking a sentence across two `<p>` tags during Trafilatura extraction. Merging requires heuristic punctuation detection. High risk of false positives merging legitimate consecutive short paragraphs. Candidate for "accept as known limitation."
Expected blast radius: High

---

### 13. Guardian and Theringer: extraction failure
Class: D
Scope: Investigate alternative extraction strategies (e.g., alternate CSS selectors, precision/recall mode switch, or structured fallback selector targeting `<article>` body) for these two fixtures specifically.
Affected fixtures: guardian (article body entirely absent), theringer (article body entirely absent)
Rationale: Trafilatura selects navigation/sidebar structure on both pages. The fix requires understanding why extraction fails — possibly paywalled content, JavaScript-rendered body, or unusual DOM structure — and adjusting the fallback selector or extraction parameters. High risk of regressions on other fixtures. Must be evaluated with the full corpus. Per Phase 2A findings, `precision` mode makes no difference on this corpus; `recall` mode performs worse. Correct approach requires fixture-specific investigation before any pipeline change.
Expected blast radius: High

---

## Known Limitations – Phase 2C (Accepted Deferrals)

The following burn-down items (6–13) are deferred and accepted as known
limitations for Phase 2 exit.  Each fails at least one of the Phase 2C
resume criteria: structural-only, bounded, and supported by ≥2 fixtures.

---

- **Item 6: End-anchored single-paragraph tail patterns (nhs, skysports)**
  Class: A
  Fixtures: nhs (`"Page last reviewed:…"`), skysports (`"Have your say…"`)
  Deferred because: site-specific strings.  Both anchor strings are CMS- or
  widget-specific text that is not structurally derivable without hard-coding
  the phrase.
  Accept for Phase 2 exit?: Yes — both are minor trailing metadata fragments
  that do not block qualitative usability testing.

---

- **Item 7: Leading metadata block trim (aeon, pbs)**
  Class: A
  Fixtures: aeon (byline, image credit, bio fragment, editor credit),
  pbs (photographer credit)
  Deferred because: start-anchored risk.  The `"by "` / attribution heuristic
  has meaningful false-positive risk on legitimate short opening sentences.
  Only 2 fixtures affected; the stop-condition design is not yet validated.
  Accept for Phase 2 exit?: No — aeon and pbs start with metadata clutter
  that would degrade a user-study session.  Flag as high-priority for Phase 2D
  if title/opening-paragraph recovery work is in scope.

---

- **Item 8: Mid-document non-article section — propublica "Republish This Story for Free"**
  Class: A
  Fixtures: propublica only
  Deferred because: site-specific string.  Requires a heading-text blocklist;
  no structural predicate can identify this section without pattern-matching
  the heading text.  Single-fixture evidence.
  Accept for Phase 2 exit?: Yes — the section is self-contained and does not
  corrupt the article body.  One known fixture; not a blocker for user testing.

---

- **Item 9: PBS duplicate related-article list mid-document**
  Class: B
  Fixtures: pbs only
  Deferred because: high false-positive risk.  Cross-document ListBlock
  deduplication by content comparison risks removing legitimate repeated
  enumerations.  Single-fixture evidence.
  Accept for Phase 2 exit?: Yes — minor visual duplication; does not block
  comprehension of the article.

---

- **Item 10: Aeon audio player widget remnants**
  Class: B
  Fixtures: aeon only
  Deferred because: site-specific string.  `"Listen to this essay"` and
  `"[N] minute listen"` are widget-specific UI strings; no structural
  generalisation exists.  Single-fixture evidence.
  Accept for Phase 2 exit?: Yes — two short non-article paragraphs in one
  fixture; minor noise, not a comprehension blocker.

---

- **Item 11: Aeon inverted heading order (h2 before h1)**
  Class: B
  Fixtures: aeon only
  Deferred because: high false-positive risk.  Correcting the h2→h1 inversion
  requires semantic inference about which heading is the article title.
  Legitimate h2-first structures exist and could be misidentified.
  Single-fixture evidence.
  Accept for Phase 2 exit?: Yes — heading level is cosmetic in the rendered
  output; article content is intact.

---

- **Item 12: Smithsonian split paragraph fragments**
  Class: B
  Fixtures: smithsonian only
  Deferred because: high false-positive risk.  Merging consecutive paragraphs
  using punctuation heuristics risks incorrectly joining intentionally separate
  short paragraphs.  Root cause is a Trafilatura extraction split at an inline
  figure element; not fixable at the parser layer without semantic
  sentence-boundary detection.  Single-fixture evidence.
  Accept for Phase 2 exit?: Yes — two sentence fragments; does not block
  comprehension of the surrounding content.

---

- **Item 13: Guardian and Theringer extraction failure**
  Class: D
  Fixtures: guardian, theringer
  Deferred because: extraction root cause unknown.  Trafilatura selects
  navigation / sidebar structure instead of article body on both fixtures.
  Root cause may be paywalled content, JavaScript-rendered body, or unusual
  DOM structure.  Per Phase 2A findings, precision and recall modes do not
  help.  Any fix requires fixture-specific investigation with full-corpus
  regression coverage.
  Accept for Phase 2 exit?: No — both fixtures produce no usable article
  content.  The program-board.md Phase 2 exit criterion explicitly requires
  guardian and theringer to either fail cleanly or extract correctly.
  Remain open; target Phase 2D or a dedicated extraction investigation spike.
