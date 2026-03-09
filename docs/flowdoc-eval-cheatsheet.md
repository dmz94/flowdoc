# Flowdoc Eval -- Cheat Sheet

## What This System Does

The eval runner measures pipeline output quality automatically.
It answers the question: "Is Flowdoc still producing good output
from these articles?"

It does NOT replace human judgment for new fixtures.
It DOES replace human judgment for routine regression checking.

---

## Daily Commands

### Check everything is still working (30 seconds)
  python tests/pipeline-audit/run_metrics.py --select-corpus main

Run this after any pipeline change. If you see only PASS and MARGINAL,
nothing has regressed. If you see REGRESSION or FAIL, investigate
before committing.

### Full report with JSON output
  python tests/pipeline-audit/run_metrics.py --select-corpus main --quality-json-report

Writes to eval/reports/{timestamp}/report.json. Use when you want
a permanent record, e.g. before a release or after a significant change.

### Check one fixture
  python tests/pipeline-audit/run_metrics.py --select-corpus main --select-fixture nhs-dyslexia

Use when you're debugging a specific article or investigating an anomaly.

### Add baselines for new fixtures
  python tests/pipeline-audit/run_metrics.py --select-corpus main --interactive-baseline

Only presents fixtures that don't have a baseline yet. Existing
baselines are skipped. See "Adding New Fixtures" below.

---

## Status Codes

PASS        Pipeline working well. All metrics within thresholds.
            Matches baseline. No action needed.

MARGINAL    Known-imperfect fixture, approved by a human.
            The source article itself is limited (short, image-heavy,
            navigation-heavy). Pipeline is working correctly.
            Stable MARGINAL is not a problem -- ignore it.

REGRESSION  Something got worse. Either:
            (a) a metric crossed a threshold that was previously OK, or
            (b) section count or word count dropped significantly.
            Always investigate a REGRESSION before committing.

FAIL        Pipeline threw an error. The article could not be processed.
            Check the error message in the output.

NEW         No baseline exists yet. Run --interactive-baseline to review and save.

---

## Thresholds (tests/pipeline-audit/audit_config.py)

These define what counts as an anomaly:

  WORD_COUNT_RATIO_MIN      0.30    Output must be at least 30% of
                                    source word count. Below this
                                    suggests extraction failure.

  AVG_PARAGRAPH_WORDS_MIN   8.0     Average paragraph must be at
                                    least 8 words. Below this
                                    suggests fragmentation.

  PLACEHOLDER_DENSITY_MAX   0.20    Placeholders (images, forms,
                                    tables) must be less than 20%
                                    of paragraph count. Above this
                                    suggests content-poor source.

  LINK_TO_PROSE_RATIO_MAX   0.50    Link words must be less than 50%
                                    of prose words. Above this
                                    suggests navigation-heavy page,
                                    not article prose.

To adjust sensitivity, edit the values in tests/pipeline-audit/audit_config.py and
re-run --interactive-baseline to regenerate baselines.

---

## Metrics Explained

The runner computes these for each fixture:

  section_count             Number of headings/sections in output
  output_word_count         Words of real prose in output
                            (excludes placeholders, headings)
  source_plain_word_count   Words in raw source HTML (after tag strip)
  word_count_ratio          output / source -- key quality signal
  paragraph_count           Non-placeholder paragraphs
  avg_paragraph_words       Mean words per paragraph
  shortest_paragraph_words  3 shortest paragraph word counts
  placeholder_count         Total [Image], [Form], [Table] tokens
  placeholder_types         Breakdown by type
  placeholder_density       Placeholders per paragraph
  link_word_count           Words inside hyperlinks
  link_to_prose_ratio       Link words / prose words
  empty_sections            Headings with no content blocks
  stub_sections             Headings with only a placeholder block

---

## When Human Review Is Required

### Always required: new fixtures
Every new article added to the corpus must be reviewed by a human
before its baseline is committed. The --interactive-baseline interactive mode
walks you through this. You must:

  1. Look at the metrics presented
  2. Optionally open the converted output in a browser to verify
     it looks like a real article (not navigation junk)
  3. Decide: PASS, MARGINAL, or skip

You cannot automate this judgment. The metrics tell you numbers;
only you can tell if the content makes sense.

### Always required: REGRESSION investigation
When the runner shows a REGRESSION, a human must decide:
  - Is this a real pipeline problem? Fix it.
  - Is the source article just worse than it used to be? Re-baseline.
  - Is the threshold too tight? Adjust thresholds.py and re-baseline.
Never ignore a REGRESSION. Never re-baseline without looking at why.

### Always required: FAIL investigation
A FAIL means the pipeline threw an error. Check the error message.
Either the source HTML changed enough to break extraction, or there
is a bug. Fix before committing.

### Not required: stable PASS and MARGINAL
If everything is PASS or MARGINAL and nothing changed, no review
needed. This is the normal state. The system is working.

### Periodically: visual spot-check
Metrics catch regressions in quantity (word count, section count)
but not quality (does the output read well?). Every few months,
or before a release, open 3-5 converted articles in a browser and
read them. The metrics cannot tell you if the typography is right
or if a paragraph reads oddly after extraction.

---

## Adding New Fixtures

### Step 1: Find a good article
Target sources: NHS, BDA, educational sites, science journalism,
longform essays. The article should be:
  - Prose-dominant (not a reference table, not a form)
  - At least 500-800 words
  - From a site the target audience (parents, teachers, SEN
    coordinators) would actually use
  - Not already in the corpus (check manifest.md)

Avoid:
  - Short listicles or news briefs
  - Image-heavy pages with little prose
  - Sites that heavily JS-render their content
  - Duplicate sources already well-represented in the corpus

### Step 2: Save the HTML
Open the article in a browser.
File > Save As > Web Page, HTML Only.
Save to: tests/pipeline-audit/test-pages/{site}-{slug}.html

Filename convention: {site}-{slug}.html -- lowercase, hyphens only, no numeric prefixes.
  bda-style-guide-overview.html
  understood-dyscalculia-basics.html
  nhs-irlen-syndrome.html

### Step 3: Add to manifest
Open tests/pipeline-audit/test-pages/manifest.md.
Add a row at the bottom:

  | 18 | bda-style-guide-overview.html | https://... | in-scope | |

Column format: # | filename | source_url | scope | notes
scope must be "in-scope" (add out-of-scope only for boundary test cases)

### Step 4: Run baseline review
  python tests/pipeline-audit/run_metrics.py --select-corpus main --interactive-baseline

The runner presents only the new fixture(s). For each:

  - Review the metrics block
  - If word_count_ratio >= 0.30 and no anomalies: press [a] to approve PASS
  - If anomalies exist but output looks reasonable: press [m] for MARGINAL
  - If output looks like junk (navigation, boilerplate): press [s] to skip
    and go fix the fixture or choose a different article

### Step 5: Commit
  git add tests/pipeline-audit/test-pages/ tests/pipeline-audit/expected-results/
  git commit -m "Add fixture: bda-style-guide-overview"

---

## Removing or Replacing Fixtures

When a fixture is consistently MARGINAL due to poor source quality
(not pipeline problems), replace it with a better article.

1. Delete the HTML file from tests/pipeline-audit/test-pages/
2. Delete the baseline JSON from tests/pipeline-audit/expected-results/
3. Remove the manifest row
4. Add replacement following "Adding New Fixtures" above
5. Commit both the removal and the addition together

Do not remove fixtures just because they are MARGINAL. Only remove
them if the source article is a poor representative of the use case.

---

## Regression Investigation Checklist

When you see a REGRESSION in the output:

1. Run the single fixture to see full anomaly detail:
   python tests/pipeline-audit/run_metrics.py --select-corpus main --select-fixture {name}

2. Check what changed. Did you recently:
   - Update Trafilatura?
   - Change parser.py or content_selector.py?
   - Change thresholds.py?

3. Open the converted output visually:
   python tests/pipeline-audit/visual-review/convert_fixtures.py
   Open tests/pipeline-audit/test-pages/{name}.flowdoc.html in a browser

4. Decide:
   - Pipeline problem: fix the code, re-run, confirm PASS
   - Source article changed (site updated): re-fetch HTML, re-baseline
   - Threshold too tight: adjust thresholds.py, re-baseline all
   - Acceptable degradation: re-baseline with MARGINAL

5. Never commit a known REGRESSION without a resolution decision.

---

## File Locations

  tests/pipeline-audit/run_metrics.py               Main runner script
  tests/pipeline-audit/audit_config.py                Anomaly threshold constants
  tests/pipeline-audit/expected-results/*.json        Committed baseline records
  eval/reports/                     Ephemeral run reports (gitignored)
  tests/pipeline-audit/README.md                    Short usage reference
  tests/pipeline-audit/test-pages/*.html        Source HTML files
  tests/pipeline-audit/test-pages/manifest.md   Corpus manifest
