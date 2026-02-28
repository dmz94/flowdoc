# Viability V3 - Baseline eval20 run (no code changes)

Run date: 2026-02-28. Flowdoc production default (baseline extraction mode).
17 of 20 fixtures ACCEPT; 3 REJECT. 1 in-scope reject (e360yale); 2 expected out-of-scope rejects.
Guardian and theringer now ACCEPT via headingless-prose extraction fix (added post-baseline).

| # | fixture | expected_scope | status | reason | chars | paragraphs |
|---|---------|---------------|--------|--------|------:|----------:|
| 01 | aeon | in-scope | ACCEPT | OK | 26445 | 65 |
| 02 | cdc | in-scope | ACCEPT | OK | 6357 | 39 |
| 03 | eater | in-scope | ACCEPT | OK | 21661 | 91 |
| 04 | guardian | in-scope | ACCEPT | OK | 33886 | 75 |
| 05 | nhs | in-scope | ACCEPT | OK | 6854 | 48 |
| 06 | pbs | in-scope | ACCEPT | OK | 9581 | 51 |
| 07 | propublica | in-scope | ACCEPT | OK | 55301 | 124 |
| 08 | skysports | in-scope | ACCEPT | OK | 6988 | 43 |
| 09 | smithsonian | in-scope | ACCEPT | OK | 19304 | 60 |
| 10 | theringer | in-scope | ACCEPT | OK | 20115 | 65 |
| 11 | wikipedia-gdp-table | out-of-scope | REJECT | Out of scope: navigation/reference page. | 42 | 0 |
| 12 | w3c-validator-tool | out-of-scope | REJECT | Out of scope: tool/form page. | 37 | 0 |
| 13 | article-13-theconversation | in-scope | ACCEPT | OK | 11068 | 38 |
| 14 | article-14-sciencedaily | in-scope | ACCEPT | OK | 12036 | 68 |
| 15 | article-15-quantamagazine | in-scope | ACCEPT | OK | 24032 | 75 |
| 16 | article-16-e360yale | in-scope | REJECT | Lacks semantic structure (no h1–h3 + body content) | 95 | 0 |
| 17 | article-17-hakaimagazine | in-scope | ACCEPT | OK | 31282 | 82 |
| 18 | article-18-undark | in-scope | ACCEPT | OK | 33354 | 122 |
| 19 | article-19-insideclimate | in-scope | ACCEPT | OK | 7366 | 39 |
| 20 | article-20-sciencefriday | in-scope | ACCEPT | OK | 2616 | 23 |

## Reject details (full error text)

**11 wikipedia-gdp-table:**
> Out of scope: navigation/reference page.

**12 w3c-validator-tool:**
> Out of scope: tool/form page.

**16 article-16-e360yale:**
> Input HTML lacks semantic structure (requires at least one h1-h3 and body content in p/ul/ol).

## Before / After ACCEPT/REJECT count

| run | ACCEPT | REJECT | notes |
|-----|-------:|-------:|-------|
| V3 baseline (no preflight, no headingless fix) | 17 | 3 | out-of-scope false-ACCEPT; guardian+theringer false-REJECT |
| V3 + preflight scope check | 15 | 5 | out-of-scope REJECT cleanly; guardian+theringer still REJECT |
| V3 + preflight + headingless-prose fix | 17 | 3 | guardian+theringer now ACCEPT; out-of-scope REJECT correctly |
