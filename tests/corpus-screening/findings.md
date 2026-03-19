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
