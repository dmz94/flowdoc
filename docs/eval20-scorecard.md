# Eval20 Scorecard

Scoring rubric — 0/1 per criterion:

1. **title** — Title is present in output
2. **intro** — First 1–2 paragraphs of article prose are preserved
3. **no_boilerplate** — No trailing nav/footer/form boilerplate in output
4. **no_artifacts** — No obvious structural artifacts (stray placeholders, broken markup, etc.)
5. **coherent** — Reads as a coherent article on skim

**Clean threshold:** 4/5 or 5/5

Out-of-scope fixtures: mark rubric fields N/A. `accept/reject` = "accept" if Flowdoc rejects cleanly with a clear reason; "reject" if it fails to reject correctly.

Proposed clean-rate: 15/18 in-scope (auto-scored; requires human review).

---

| index | fixture | expected_scope | title | intro | no_boilerplate | no_artifacts | coherent | total | clean? | accept/reject | reason | chars | paragraphs | notes |
|-------|---------|----------------|-------|-------|----------------|--------------|----------|-------|--------|---------------|--------|------:|-----------:|-------|
| 01 | aeon.html | in-scope | 1 | 0 | 1 | 1 | 1 | 4 | Y | accept | OK | 26445 | 65 | intro: audio widget labels ("Listen to this essay") precede article lede |
| 02 | cdc.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 6357 | 39 | |
| 03 | eater.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 21661 | 91 | |
| 04 | guardian.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 33886 | 75 | |
| 05 | nhs.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 6854 | 48 | |
| 06 | pbs.html | in-scope | 1 | 1 | 0 | 0 | 1 | 3 | N | accept | OK | 9581 | 51 | trailing Subscribe form + [Form omitted] + related-article nav in body |
| 07 | propublica.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 55301 | 124 | [Form omitted] run present but collapsed by dedup code |
| 08 | skysports.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 6988 | 43 | |
| 09 | smithsonian.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 19304 | 60 | |
| 10 | theringer.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 20115 | 65 | |
| 11 | wikipedia-gdp-table.html | out-of-scope | N/A | N/A | N/A | N/A | N/A | N/A | N/A | accept | Out of scope: navigation/reference page. | 42 | 0 | Expected reject (out-of-scope). |
| 12 | w3c-validator-tool.html | out-of-scope | N/A | N/A | N/A | N/A | N/A | N/A | N/A | accept | Out of scope: tool/form page. | 37 | 0 | Expected reject (out-of-scope). |
| 13 | article-13-theconversation.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 11068 | 38 | |
| 14 | article-14-sciencedaily.html | in-scope | 1 | 1 | 0 | 0 | 1 | 3 | N | accept | OK | 12036 | 68 | "Explore More" nav links at tail; RELATED TOPICS/TERMS labels in body |
| 15 | article-15-quantamagazine.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 24032 | 75 | |
| 16 | article-16-e360yale.html | in-scope | 1 | 1 | 1 | 0 | 1 | 4 | Y | accept | OK | 15283 | 20 | 4 empty blockquotes from sanitized pull-quotes |
| 17 | article-17-hakaimagazine.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 31282 | 82 | |
| 18 | article-18-undark.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 33354 | 122 | |
| 19 | article-19-insideclimate.html | in-scope | 1 | 1 | 0 | 0 | 1 | 3 | N | accept | OK | 7366 | 39 | "About This Story" fundraising section at tail with Donate Now CTA |
| 20 | article-20-sciencefriday.html | in-scope | 1 | 1 | 1 | 1 | 1 | 5 | Y | accept | OK | 2616 | 23 | Short article (2 body paras); coherent news lede |
