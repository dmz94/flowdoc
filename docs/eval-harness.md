# Decant Eval Harness -- Reference

**Status:** Current as of 2026-03-03
**Source of truth:** tests/pipeline-audit/run_metrics.py, tests/pipeline-audit/audit_config.py

This document describes the eval harness: what it does, how it works,
and how to use it. For quick-reference commands, see
docs/eval-cheatsheet.md.

---

## Purpose

The eval harness measures the quality of Decant's conversion pipeline
by computing metrics on a corpus of real-world HTML fixtures and
comparing them against human-reviewed baselines.

It answers one question: "Is the pipeline still producing good output
from these articles?"

The harness is separate from pytest. pytest validates correctness
(parsing rules, rendering invariants, model structure). The eval
harness validates quality (is the extracted content complete? is the
output well-structured? has anything regressed?).

---

## File Locations

  tests/pipeline-audit/run_metrics.py               Main runner script
  tests/pipeline-audit/audit_config.py                Anomaly threshold constants
  tests/pipeline-audit/expected-results/*.json        Human-reviewed baseline records
  eval/reports/                     Ephemeral run reports (gitignored)
  tests/pipeline-audit/README.md                    Short usage reference
  tests/pipeline-audit/test-pages/*.html        Source HTML fixture files
  tests/pipeline-audit/test-pages/manifest.md   Corpus manifest (defines fixture list)
  docs/eval-cheatsheet.md   Quick-reference cheat sheet

---

## How It Works

The harness runs three stages for each fixture:

### Stage 1: Pipeline

Runs the full Decant conversion pipeline on the fixture HTML:

1. detect_mode() determines extract vs transform mode
2. In extract mode: Trafilatura extracts main content
3. parse() builds the internal Document model
4. render() produces the output HTML

If the pipeline throws an exception, the fixture is marked FAIL.

### Stage 2: Metrics

Walks the Document model tree and computes 16 metrics. These are
computed from the model, not from rendered HTML. The metrics capture
word counts, structural properties, placeholder density, and
link-to-prose ratios.

### Stage 3: Comparison

Compares current metrics against the saved baseline for each fixture.
Applies threshold rules to detect anomalies. Classifies the fixture
as PASS, MARGINAL, REGRESSION, FAIL, or NEW.

---

## Metrics

The runner computes these for each fixture:

  section_count             Number of sections (one per heading)
  headings                  List of heading text strings
  output_word_count         Words in prose paragraphs, lists, quotes,
                            and preformatted blocks (excludes
                            placeholders and headings)
  source_plain_word_count   Words in raw source HTML after tag stripping
  word_count_ratio          output_word_count / source_plain_word_count
                            Key quality signal -- how much content
                            survived extraction
  paragraph_count           Non-placeholder paragraphs
  avg_paragraph_words       Mean words per paragraph
  shortest_paragraph_words  3 shortest paragraph word counts
                            (fragmentation indicator)
  placeholder_count         Total placeholder tokens ([Image], [Form],
                            [Table], [-])
  placeholder_types         Breakdown: image, form, table, hr, other
  placeholder_density       placeholder_count / (paragraph_count +
                            placeholder_count)
  link_word_count           Words inside hyperlinks
  prose_word_count          Same as output_word_count (total prose)
  link_to_prose_ratio       link_word_count / prose_word_count
  empty_sections            Sections with no content blocks at all
  stub_sections             Sections with only placeholder blocks

---

## Thresholds

Defined in tests/pipeline-audit/audit_config.py. These determine what counts as an
anomaly:

  WORD_COUNT_RATIO_MIN      0.30
    Output must be at least 30% of source word count.
    Below this suggests extraction failure.

  AVG_PARAGRAPH_WORDS_MIN   8.0
    Average paragraph must be at least 8 words.
    Below this suggests fragmentation.

  PLACEHOLDER_DENSITY_MAX   0.20
    Placeholders must be less than 20% of total paragraph count.
    Above this suggests content-poor source.

  LINK_TO_PROSE_RATIO_MAX   0.50
    Link words must be less than 50% of prose words.
    Above this suggests navigation-heavy page, not article prose.

Additional anomaly checks (not threshold-configurable):
- empty_sections > 0
- stub_sections > 0

To adjust sensitivity, edit audit_config.py and re-run --interactive-baseline to
regenerate baselines.

---

## Status Codes

PASS        All metrics within thresholds. Matches baseline.
            No action needed.

MARGINAL    Human-approved baseline with known imperfections.
            The source article itself is limited (short, image-heavy,
            navigation-heavy). The pipeline is working correctly.
            Stable MARGINAL is not a problem.

REGRESSION  A metric crossed a threshold that was previously OK,
            or baseline status was PASS but anomalies now exist.
            Always investigate before committing.

FAIL        Pipeline threw an exception. The fixture could not be
            processed.

NEW         No baseline exists yet. Run --interactive-baseline to review and save.

### Classification Logic

  if no baseline exists:           -> NEW
  if baseline status is MARGINAL:  -> MARGINAL (preserved)
  if anomalies exist:              -> REGRESSION
  otherwise:                       -> PASS

FAIL is assigned by the runner when the pipeline raises an exception,
before classification runs.

---

## Commands

### Run all fixtures (routine check)
  python tests/pipeline-audit/run_metrics.py --select-corpus main

### Run a single fixture
  python tests/pipeline-audit/run_metrics.py --select-corpus main --select-fixture nhs-dyslexia

### Generate a JSON report
  python tests/pipeline-audit/run_metrics.py --select-corpus main --quality-json-report

Writes to eval/reports/{timestamp}/report.json.

### Interactive baseline review
  python tests/pipeline-audit/run_metrics.py --select-corpus main --interactive-baseline

Requires an interactive terminal (TTY). Presents each fixture without
a baseline and prompts for a decision:

  [a] Approve as PASS
  [m] Approve as MARGINAL
  [s] Skip (do not save baseline)
  [q] Quit review session

Fixtures that already have a baseline are skipped automatically.
The review block shows a [N of total] counter in the header.

---

## When Human Review Is Required

### Always: new fixtures
Every new fixture must be reviewed by a human via --interactive-baseline before
its baseline is committed. Metrics tell you numbers; only a human can
tell if the content makes sense.

### Always: REGRESSION
A human must decide: pipeline bug (fix it), source article changed
(re-fetch and re-baseline), threshold too tight (adjust and
re-baseline), or acceptable degradation (re-baseline as MARGINAL).

### Always: FAIL
Check the error message. Either the source HTML changed enough to
break extraction, or there is a pipeline bug.

### Not required: stable PASS and MARGINAL
If everything is PASS or MARGINAL and nothing changed, no review
needed.

### Periodically: visual spot-check
Metrics catch regressions in quantity but not quality. Before a
release or every few months, open 3-5 converted articles in a browser
and read them.

---

## Corpus

### Naming Convention

Filename convention: {site}-{slug}.html -- lowercase, hyphens only,
no numeric prefixes.

Examples:
  nhs-dyslexia.html
  wikipedia-photosynthesis.html
  propublica-3m-pfas.html

### Current State (17 fixtures, all human-reviewed)

PASS (11):
  nhs-dyslexia, nhs-adhd, wwf-ways-to-help, pbs-crowd-surges,
  propublica-3m-pfas, smithsonian-homo-sapiens, theringer-chase-budinger,
  theconversation-ai-innovation, quanta-smell, yale360-baboons,
  undark-brain-organoids

MARGINAL (6):
  cdc-west-nile, dyslexiaida-dyslexia-basics, sciencedaily-memory,
  wikipedia-photosynthesis, wikipedia-world-war-i, hakai-caviar-sturgeon

All 17 baselines were human-reviewed and approved during the Phase 3
baseline review session.

### Manifest

The corpus is defined in tests/pipeline-audit/test-pages/manifest.md. Each row
specifies a fixture number, filename, source URL, scope (in-scope or
out-of-scope), and notes. Only in-scope fixtures are evaluated by the
runner.

---

## Known Limitations

The eval harness measures extraction completeness and structural
quality. It does not measure:

- **Rendering quality** -- typography, spacing, and visual layout are
  not evaluated. Use visual spot-checks for this.

- **Semantic accuracy** -- the harness cannot tell if extracted content
  is correct or garbled, only that word counts and ratios are stable.

- **ScienceDaily and similar aggregators** -- detect_mode() routes
  these to transform mode, bypassing Trafilatura boilerplate removal.
  CMS chrome leaks into output. Known scope boundary, not a bug.

- **Wikipedia lead section fragmentation** -- dense link-heavy
  paragraphs fragment into single-phrase paragraphs during extraction.
  Deferred to v2.

- **Trafilatura extraction variance** -- Trafilatura updates can change
  extraction behavior, invalidating baselines. Pin Trafilatura to a
  specific version for releases.

See docs/known-limitations.md for the full list of v1 pipeline
limitations.
