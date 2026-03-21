# Comparison Results Summary

Scratch file for controller thread. Updated after corpus
finalization (2026-03-20).

## Corpus State

105 in-scope fixtures, 15 out-of-scope.
Manifest: tests/pipeline-audit/test-pages/manifest.md

Baseline status:
- PASS: 102
- MARGINAL: 2 (copyright-gov-faq, netflix-help)
- FAIL: 1 (scholastic-reading -- parser produces 0 sections)

## Comparison Classification (118 fixtures, pre-cull)

These counts are from the Readability.js comparison run
across the full corpus before culling.

- Clean: 23
- Good: 29
- Decant Wins: 16
- Moderate Gap: 28
- Severe Gap: 11
- Near Total Loss: 8
- Errors: 2 (both resolved)

## Cull Executed

14 fixtures marked out-of-scope:
- 5 academic papers (plos-one-open-access, elife-editorial,
  frontiers-metrics, nature-comms, arxiv-html)
- 4 recipes (bbcgoodfood-victoria, giallozafferano-tiramisu,
  minimalistbaker-cake, damndelicious-pasta)
- 3 encyclopedia (wikipedia-dyslexia, worldhistory-rome,
  simple-wiki-photosynthesis)
- 1 bad fixture (instructables-elwire, empty JS shell)
- 1 geo-redirect (history-constitution, pre-existing)

Parked categories (not v1): academic papers, recipes,
encyclopedia/Wikipedia.

## Fixture Added

bda-about-history.html (row 123, cat 10). BDA org history
page, SEN-relevant. Replaces the BDA about page which was
a JS-loaded hub (see Known Scope Boundaries in
docs/corpus-design.md).

## Engine Patterns Found (11)

Priority order for engine fixes:

1. LISTICLE_TRUNCATION -- Body content dropped on long
   multi-item pages. timeout-london (5.5%),
   roughguides-barcelona, tomsguide-espresso,
   outdoorgearlab-boots (1 heading of 54). Priority #1.
2. CALLOUT_CONTENT_LOSS -- Embedded pedagogical elements
   stripped (teacher notes, practice questions).
   openstax-photosynthesis. Priority #1.
3. IMAGE_LOSS -- 0% image survival on most fixtures.
4. CONTENT_BEFORE_FIRST_HEADING -- Parser drops pre-heading
   content by design.
5. EMPTY_SECTIONS -- Headings survive, 0 words beneath.
6. BRACKETED_LINK_REFERENCES -- Inline promo links as text.
7. STRUCTURED_CONTENT_LOSS -- Stat cards, pros/cons stripped.
8. BOILERPLATE_LEAK -- CTA, subscribe blocks surviving.
   stanford-epistemology extreme case (431 extra paragraphs).
9. CAPTION_LOSS -- figcaptions not matching after extraction.
10. ITALICIZED_CONTENT_DROPPED -- em/i tags lost.
11. HEADING_STRUCTURE_LOSS -- Sub-section headings flattened.

Engine fix priority order:
1. Core text fidelity (titles, headings, body content)
2. Images and captions
3. Tables and charts
4. Pre-heading content (taglines, decks, author info)

## Notable Fixture Decisions

- stanford-epistemology: KEEP as boilerplate leak test case
- playerstribune-green: KEEP, 0% is comparison artifact
- copyright-gov-faq: KEEP, accordion FAQ scope boundary
- scholastic-reading: KEEP, engine fix needed (parser fails)
- nami-bipolar: DECANT_WINS (Readability failed entirely)
- mind-depression: DECANT_WINS (Decant got more content)
- readingrockets-dyslexia: DECANT_WINS

## Known Scope Boundaries

JS-loaded accordion/hub pages: content fetched dynamically
on click, not in static HTML. BDA about page is the
confirmed example. Documented in docs/corpus-design.md.

CSS-hidden accordions (e.g. copyright-gov-faq): content IS
in the HTML but collapsed. Potential engine fix, not
architecture change.

## Comparison Scripts

Decision: KEEP in repo permanently. They are the QA loop
for engine fixes -- re-run after fixing LISTICLE_TRUNCATION
to prove the fix worked on timeout-london, etc.

Scripts (tracked):
- scripts/readability-extract.js
- scripts/compare-extractions.py
- scripts/run-comparison-batch.py
- scripts/package.json

Output (gitignored):
- scripts/output/ (full-results.json, summaries, manifests)
- tests/corpus-screening/review/compare-*.html

## Corpus Status

Corpus is closed for the viability call. 105 in-scope
fixtures, all baselined. Engine patterns documented.
Fix priorities established.