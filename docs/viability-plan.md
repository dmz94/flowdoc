# Flowdoc Viability Plan

Purpose:
Decide whether Flowdoc "has legs" and should be continued, using a timeboxed, testable evaluation. Avoid endless edge-case chasing.

Timebox:
2-4 weeks. If gates are not trending positive by the end of the timebox, pause or narrow scope.

Non-goals:
- No buyer validation interviews in this plan.
- No new input formats (PDF/DOCX).
- No JS/SPA rendering.
- No site-specific extractor registry.
- No ML extraction.

---

## V0 - Rules of Engagement

- Keep a fixed evaluation set. Do not change scoring criteria mid-run.
- No "one-off" fixes unless they improve >=2 pages in the evaluation set.
- Prefer end-anchored and structural heuristics.
- Tests-first for any behavior change.
- Determinism must remain intact.

---

## V1 - Build the Evaluation Set (20 pages)

Composition:
- 10 existing user-study fixtures (already in repo).
- Add 10 new HTML snapshots:
  - 6 "likely in-scope" semantic prose articles from diverse sources.
  - 2 "hard but plausible" CMS-heavy prose pages.
  - 2 "out of scope" pages (tables/reference/interactive) to verify clean failure.

Snapshot rules:
- Store as raw HTML files (no network fetch at runtime).
- Record source URL and capture date in a small manifest file.
- Do not add huge corpora. Keep each snapshot reasonable size and count.

Deliverables:
- tests/fixtures/eval20/ (20 HTML files)
- tests/fixtures/eval20/manifest.md (URL, date, notes, expected in-scope/out-of-scope)

---

## V2 - Define the "Clean Output" Rubric

Score each page output on a 0/1 checklist:

1) Title present
2) Intro preserved (first 1-2 paragraphs)
3) No trailing boilerplate
4) No obvious structural artifacts (e.g., "FORM removed", stray placeholders)
5) Reads as a coherent article on skim

Clean threshold:
- Clean = 4/5 or 5/5
- Acceptable failure = explicit reject with clear reason (for out-of-scope pages)

Deliverables:
- docs/eval20-scorecard.md (blank scoring sheet template)
- A first pass filled scorecard (can live outside repo if preferred)

---

## V3 - Baseline Run and Score (No Code Changes)

Process:
- Run Flowdoc on all 20 pages using production default (baseline mode).
- Produce a deterministic summary table: chars, paragraphs, ACCEPT/REJECT, reason.
- Manually score outputs using the rubric.

Deliverables:
- eval20 summary output (kept out of git if large; summarize results in docs/viability-notes.md)

---

## V4 - High-Leverage Fixes Only

Selection rule:
Implement a fix only if it improves >=2 pages in eval20, or fixes a systemic failure mode.

Allowed fix types:
- Tail trimming (end-anchored)
- Orphan section cleanup (structural)
- Intro/title recovery (generic)
- Generic boilerplate termination patterns (not domain-specific)

Not allowed:
- Per-site selectors, per-domain rules, custom extractor registry
- Broad scoring systems that require tuning per site

Process:
- One failure mode at a time.
- Add failing test(s) using minimal fixtures.
- Implement smallest change.
- Re-run eval20 and re-score only impacted pages.

Deliverables:
- Small number of stable passes/modules (avoid a new file per niggle unless clearly justified)

---

## V5 - Differentiation Check vs Browser Reader Mode

Choose 5 pages from eval20 where Reader Mode tends to struggle (images, consent blocks, republish blocks, broken structure).

For each:
- Compare Flowdoc output vs Reader Mode output.
- Record a short qualitative judgment: "Flowdoc better / Reader Mode better / tie" and why.

Success signal:
- Flowdoc is clearly better on >=3 of the 5.

---

## V6 - Lightweight User Preference Test (5-10 people)

Goal:
Determine whether real readers prefer Flowdoc output over Reader Mode in practice.

Test design:
- 15 minutes per person.
- 3 pages per person (pre-selected).
- For each page: show Reader Mode and Flowdoc output (order randomized if possible).
- Ask:
  1) Which was easier to read?
  2) Which was less tiring?
  3) Any distracting artifacts?

Success signal:
- >=60% preference for Flowdoc overall, OR a clear subgroup signal (e.g., dyslexic readers strongly prefer Flowdoc).

Notes:
Distribution/hosting can be simple (static HTML). No product build required.

---

## V7 - Decision

Continue (green):
- Eval20 clean+acceptable failure rate is strong (>=80% clean/in-scope + clean fails out-of-scope)
- Differentiation check passes
- User preference test is positive or trending positive

Continue but narrow (yellow):
- Reliability improving but not there; user signal unclear
- Narrow scope to a smaller in-scope profile and stop adding heuristics

Pause / pivot (red):
- Reliability stalls or requires site-specific rules
- Differentiation is weak
- Users do not prefer output

Document the decision in docs/viability-notes.md.
