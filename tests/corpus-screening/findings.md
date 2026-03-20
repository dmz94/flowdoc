# Corpus Screening: Findings and Coordination

Status of the corpus expansion from 38 to 100 fixtures.
Updated after each screening run or engine fix.

## Current State

- Corpus: 38 in-scope fixtures, all PASS (manifest is source
  of truth: tests/pipeline-audit/test-pages/manifest.md)
- Screening tool: tests/corpus-screening/run_screening.py
  (working; heading noise suppression and emoji normalization
  done; minor heading noise remains, fix as it surfaces)
- Candidate URLs: 97 candidates merged from four research
  runs into tests/pipeline-audit/candidates.md
- Corpus design: docs/corpus-design.md (16 categories,
  coverage targets defined, 60 new fixtures needed)

## Sequencing

1. ~~Fix screening tool (heading noise, emoji normalization)~~ Done
2. Fix engine issues surfaced by screening (deferred --
   log during expansion, batch-fix after pattern triage)
3. ~~Merge and finalize candidate URL lists~~ Done (97 candidates)
4. Fetch candidates to staging -- IN PROGRESS
5. Review fetch results, cull failures
6. Move survivors to test-pages, add to manifest
7. Run metrics with --interactive-baseline on new fixtures
8. Run screening tool on new fixtures
9. Human review via side-by-side review pages
10. Cull failed fixtures
11. Pattern triage on engine issues logged during expansion
12. Commit corpus, update docs

## Fetch Results (2026-03-19)

First fetch pass: 97 candidates attempted.

- OK: 73 (saved to staging/)
- SMALL: 2 (C53 usgs-yellowstone 2KB, C69 mozilla-sync 3KB)
- FAILED: 22

Dead (12 rows deleted from candidates.md):
- C05 reuters-nuclear: 401, article too short
- C06 axios-iran-fuel: 403, article too short
- C09 longreads-best-2025: site down (connection error on
  both automated fetch and manual retry)
- C28 openlearn-teachers: course landing page, not content
- C32 allrecipes-lasagna: 402 paywall
- C38 marthastewart-cheesecake: 402 paywall
- C47 uscis-disability: 404 URL gone
- C53 usgs-yellowstone: 404 page not found
- C64 wiktionary-dyslexia: dictionary entry, not readable
- C65 wikisource-magna-carta: hub page, not readable
- C77 rogerebert-shadows: 404 page not found
- C83 atlasobscura-medieval: 404 page not found

Manual browser saves completed (9 files added to staging/):
- C19 drugs-metformin
- C22 mind-depression
- C23 nami-bipolar
- C43 ssa-disability (edge case -- thin gov hub)
- C62 simple-wiki-photosynthesis
- C69 mozilla-sync
- C85 unesco-heritage
- C92 pmc-open-access
- C93 elife-editorial

Retried (connection errors from first pass):
- C10 atavist-castles: manual browser save OK
- C11 restofworld-tiger: manual browser save OK
- C44 canada-ai-guidance: manual browser save OK

Culled after screening (pipeline correctly rejected):
- C43 ssa-disability: out of scope (navigation/reference)
- C48 travel-state-passports: out of scope (tool/form page)
- C51 nasa-globalwarming: out of scope (navigation/reference)
- C96 cochrane-evidence: out of scope (navigation/reference)

## Screening Tool Improvements Needed

These must be fixed before screening 60+ new fixtures.

**Heading noise suppression.** "Missing" heading flags are
dominated by CMS boilerplate that Trafilatura correctly
stripped: "Related Articles", "Comments", "Subscribe",
"More Stories", newsletter signups, etc. First run across
38 fixtures produced 455 flags, most of them false
positives. Add a boilerplate heading dictionary to suppress
known patterns.

**Emoji spacing in heading comparison.** The
ghost-accessibility-blog fixture produces false positives
from space-before-emoji differences (e.g., "Publishing
from iPad🔗" vs "Publishing from iPad 🔗"). Normalize
or strip emoji during heading comparison.

## Engine Issues Surfaced by Screening

These should be investigated and fixed before baselining
new fixtures, otherwise defects get locked in as expected
behavior.

### Image caption matching (high priority)

Caption matching fails on every fixture tested. Source
pages with figcaptions produce 0 captions in output.
Affected fixtures: quanta-smell (9 lost),
seriouseats-brisket (28 lost), golf-greenside-bunker
(9 lost), texasmonthly-bbq-history (5 lost),
wikipedia-dyslexia (3 lost).

The caption harvester extracts captions before Trafilatura
runs, then matches by exact src URL after extraction. If
Trafilatura modifies the src or drops the image, the match
fails. Investigate whether the matching logic has a bug or
a wrong assumption.

### Image survival through extraction (high priority)

Many article images are stripped during Trafilatura
extraction. Examples: ribbonfarm (199 source, 0 output),
clevelandclinic (19 source, 0 output), natarchives (20
source, 0 output), mayoclinic (15 source, 0 output),
plos-one (30 source, 0 output).

Some loss is correct (decorative, navigation, ad images).
But 100% loss on multiple fixtures suggests article images
are being lost too. Investigate which images are dropped
and why. Compare extract mode vs transform mode on the
same fixtures.

### Severe content loss on specific fixtures (high priority)

clevelandclinic-dyslexia: 27 source headings reduced to 1
output heading. Nearly all article structure lost. This is
a SEN-relevant health page.

plos-one-open-access: 7 sections with 0 prose words
(Abstract, Introduction, Results, Discussion). Article
structure survived but content did not.

Investigate whether these are engine problems worth fixing
or bad fixtures that should be re-evaluated.

### Table rendering (medium priority)

Only 3 fixtures contain tables. All tables became
placeholders: wikipedia-dyslexia (8 tables, 0 rendered),
seriouseats-brisket (3 tables, 0 rendered), ribbonfarm
(1 table, 0 rendered). Investigate whether tables fail
the simple-table test in source HTML or whether
Trafilatura modifies table structure before it reaches
the degradation logic.

### berthub image placeholders (medium priority)

berthub-long-term-software: 7 source images, 0 survived,
6 placeholders. All images show "[Image not included]".
Likely a relative src issue -- images have no http/https
scheme so they degrade to placeholder. Investigate
whether detect_mode chose the wrong mode or whether base
URL resolution could recover these.

## Corpus Expansion Workflow

Once tool and engine fixes are complete:

1. Merge Claude and GPT candidate lists. Deduplicate.
   Favor verified over high-confidence. Favor structural
   diversity within each category. Target ~75 candidates.
2. Manual browser check on high-confidence URLs (open
   each, confirm prose loads, no paywall/JS-only). Kill
   failures.
3. Fetch HTML fixtures (fetch_corpus.py for automated,
   manual save-as for blocked domains).
4. Run screening tool on all new fixtures.
5. Human review with side-by-side review pages and
   screening flags. Approve, marginal, or skip.
6. Pattern triage: group flagged items across fixtures,
   identify low-hanging engine fixes vs known limitations.
7. Baseline and commit approved fixtures.

## Visual Review Results (2026-03-20)

### Review Process

11 of 119 fixtures reviewed manually using four inputs
per fixture: (1) screening tool review page, (2) original
webpage screenshot, (3) Firefox Reader Mode screenshot as
extraction benchmark, (4) tool diagnostic text.

Reader Mode comparison proved decisive: it settles "engine
problem vs scope problem" immediately. Every fixture tested
extracts cleanly in Reader Mode, meaning all content losses
are engine issues, not exotic HTML.

Manual review does not scale. 10-15 minutes of mechanical
work per fixture (screenshotting, copying, pasting) before
AI analysis begins. Tooling needed to automate baseline
comparison. See tooling investigation notes below.

### Fixture Calls

KEEP (10):
1. foxsports-nfl (cat 15, marginal)
2. arxiv-html (cat 16, marginal, needs image/table fixes)
3. outdoorgearlab-boots (cat 13, poor conversion, proven extractable)
4. timeout-london (cat 14, FAIL-level total content loss, proven extractable)
5. tomsguide-espresso (cat 13, partial, empty sections bug)
6. insideclimate-2025 (cat 1, good conversion, images lost)
7. nature-patcid (cat 16, marginal, title/authors dropped)
8. atavist-castles (cat 2, excellent prose, subscription boilerplate leaks)
9. bleacherreport-bracket (cat 15, clean conversion, best result in batch)
10. yale360-baboons (cat 9, existing PASS but opening lede dropped)

CULL (1):
11. history-constitution (geo-redirect homepage, not an article)

### Engine Patterns

1. IMAGE SURVIVAL: 0% on most fixtures. Partial on
   tomsguide (53/154) and bleacherreport (4/30). Reader
   Mode extracts images on every page tested. Engine
   problem, not source problem.

2. CONTENT BEFORE FIRST HEADING DROPPED (high priority):
   Fixtures: nature-patcid, yale360-baboons. Title, authors,
   and opening content above first h2/h3 discarded. Affects
   academic papers and feature articles. Most important
   content on the page is often above the first heading.

3. STRUCTURED LISTICLE WIPEOUT (high priority):
   Fixture: timeout-london. All 50 list items missing. Only
   intro preamble survives. Repeating card/div structure
   stripped entirely. Reader Mode pulls all 50 items.

4. EMPTY SECTIONS (medium priority):
   Fixture: tomsguide-espresso. Headings survive but 0 words
   beneath them. Prose exists but doesn't land in sections.

5. BRACKETED LINK REFERENCES (low priority):
   Fixture: foxsports-nfl. Inline promotional links render
   as bracketed text in output.

6. STRUCTURED CONTENT LOSS (medium priority):
   Fixtures: foxsports-nfl (stat cards), outdoorgearlab-boots
   (pros/cons). Non-widget structured content stripped.

7. SUBSCRIPTION/PAYWALL CTA SURVIVING EXTRACTION:
   Fixture: atavist-castles. Subscribe block and form
   placeholder appear at top of output.

8. HUB/HOMEPAGE PAGES PASSING SCOPE VALIDATION:
   history-constitution (geo-redirect), espn.com,
   espn.com/nfl. Card-grid homepages pass prose word-count
   threshold. Reader Mode refuses all three.

9. CAPTION LOSS (known, reinforced):
   Every fixture with figcaptions in source has 0 captions
   in output.

10. ITALICIZED INLINE CONTENT DROPPED:
    Fixture: allaboutjazz-genesis (existing PASS). Album
    titles in em/i tags missing throughout. Article
    unreadable without them. Metrics did not catch it.

### Existing Fixture Issues

Two fixtures baselined as PASS have undetected content loss:

1. allaboutjazz-genesis: Album titles (em/i content) dropped.
   Discography walkthrough unreadable without them. Word
   counts barely change so metrics missed it.

2. yale360-baboons: Opening lede dropped. First ~3 paragraphs
   (Kataza kitchen-raid anecdote) missing. Content before
   first heading pattern.

### Tool Fixes

Applied:
- Heading whitespace normalization: strip all spaces in
  _normalize_heading() before comparison. Reduced false
  flags by 60-70 per affected fixture. (2026-03-20)

Needed:
- Boilerplate heading dictionary gaps: yale360-baboons
  missing headings are mostly navigation/footer ("Related
  Articles", "Solutions", "Biodiversity", "Energy", etc.)
  that should be suppressed.

### Side Observations

1. CATEGORY GAP: No entertainment review fixtures (music,
   film, TV). Different CMS templates, embedded media
   players, tracklists, star ratings. Consider adding 1-2.

2. READER MODE AS BENCHMARK: Reader Mode consistently
   extracts more content than Decant. Gap is: (a) images
   surviving, (b) pull quotes and breakout elements
   preserved, (c) opening content before first heading
   preserved. North-star benchmark for extraction quality.

3. PASS FIXTURES WITH HIDDEN CONTENT LOSS: The
   allaboutjazz finding proves metrics-only baselining
   misses qualitative problems. Consider targeted re-review
   of all 38 existing fixtures after expansion.

### Tooling Investigation

Manual review does not scale for remaining 108 fixtures.
Proposed: use Readability.js (Mozilla's Reader Mode engine)
as automated baseline comparator. Run it programmatically
against each fixture, diff against Decant output, flag
differences. Reduces human review from 10-15 min/fixture
to seconds per fixture. Investigation in progress.
