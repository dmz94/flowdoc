# Comparison Tool Results Summary

Generated: 2026-03-20
Tool: scripts/run-comparison-batch.py --all
Baseline: Readability.js + jsdom vs Decant pipeline
Status: TRIAGE COMPLETE. Keep/cull decisions made. Execution pending.

## Classification Counts

| Classification | Count |
|---|---|
| Clean (90%+) | 23 |
| Good (80-90%) | 29 |
| Decant Wins | 16 |
| Moderate Gap (50-80%) | 28 |
| Severe Gap (15-50%) | 12 |
| Near Total Loss (<15%) | 8 |
| Errors | 2 |
| **Total** | **118** |

68 fixtures (58%) need no engine work (Clean + Good + Decant Wins).

## Cull List (14 fixtures)

| Fixture | Reason |
|---|---|
| plos-one-open-access | Academic paper (parked) |
| nature-comms | Academic paper (parked) |
| pmc-open-access | Academic paper (parked) |
| elife-editorial | Academic paper (parked) |
| frontiers-metrics | Academic paper (parked) |
| arxiv-html | Academic paper (parked) |
| minimalistbaker-cake | Recipe (parked) |
| damndelicious-pasta | Recipe (parked) |
| bbcgoodfood-victoria | Recipe (parked) |
| giallozafferano-tiramisu | Recipe (parked) |
| wikipedia-dyslexia | Encyclopedia (parked) |
| simple-wiki-photosynthesis | Encyclopedia (parked) |
| worldhistory-rome | Encyclopedia (parked) |
| instructables-elwire | Bad fixture (empty JS shell) |

After cull: ~104 in-scope fixtures.

## Engine Fix Priority Order

1. Core text fidelity (titles, headings, body content)
2. Images and captions
3. Tables and charts
4. Pre-heading content (taglines, decks, author info)

## Engine Patterns Found

| # | Pattern | Priority | Examples |
|---|---|---|---|
| 1 | Image loss (0% survival on most fixtures) | #2 | Most moderate+ fixtures |
| 2 | Content before first heading dropped | #4 | yale360-baboons, atavist-castles |
| 3 | Listicle truncation (NEW) | #1 | timeout-london (5.5%), outdoorgearlab-boots (1/54 headings) |
| 4 | Empty sections | #1 | tomsguide-espresso |
| 5 | Bracketed link references | Low | foxsports-nfl |
| 6 | Structured content loss | Medium | foxsports-nfl, outdoorgearlab-boots |
| 7 | Boilerplate leak | Under investigation | stanford-epistemology (431 extra paras) |
| 8 | Caption loss | #2 | All fixtures with figcaptions |
| 9 | Italicized content dropped | #1 | allaboutjazz-genesis |
| 10 | Callout content loss (NEW) | #1 | openstax-photosynthesis |
| 11 | Heading structure loss | #1 | github-2fa (1 heading vs 7) |

## Parked Categories (not v1)

- Academic papers
- Recipes
- Wikipedia/encyclopedia

## Architecture Issue: Accordion/JS-Hidden Content

Two fixtures (copyright-gov-faq, BDA about page) use
accordion/collapsed content that requests.get() never
sees. Content MAY be in static HTML hidden by CSS/JS.
If so, engine fix. If not, architecture change needed.
BDA is a target-audience site -- this matters.

## New Fixture to Add

BDA about page: https://www.bdadyslexia.org.uk/about
Accordion FAQ on target-audience site. Fetch and add
during corpus finalization.

## Notable Fixture Decisions

- stanford-epistemology: KEEP as boilerplate leak test case
- playerstribune-green: KEEP, 0% is comparison artifact
- copyright-gov-faq: KEEP, accordion FAQ scope boundary
- scholastic-reading: KEEP, engine fix needed (parser fails)
- nami-bipolar: DECANT_WINS (Readability failed entirely)
- mind-depression: DECANT_WINS (Decant got more content)
- readingrockets-dyslexia: DECANT_WINS

## Comparison Tool Location

Scripts (tracked):
- scripts/readability-extract.js
- scripts/compare-extractions.py
- scripts/run-comparison-batch.py
- package.json

Output (gitignored):
- scripts/output/full-results.json (complete data)
- scripts/output/full-summary.txt (text summary)
- scripts/output/triage-needed.txt
- scripts/output/decant-wins.txt
- scripts/output/cleanup-manifest.txt

Decision pending: keep scripts in repo permanently or
remove after investigation completes.

## Next Steps

1. Execute cull (mark 14 fixtures out-of-scope in manifest)
2. Add BDA about page fixture
3. Auto-baseline survivors
4. Update docs with final counts
5. Report to controller for viability call