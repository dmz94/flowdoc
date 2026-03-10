# Flowdoc Program Board

## Identity (Revised per v1 success contract)

Flowdoc is a free, open-source CLI tool that converts semantic prose HTML
into accessible, self-contained, printable HTML for anyone who needs
a clearer, more readable version of a web article. Initial validation
focuses on readers with dyslexia because that is where the research base,
typography evidence, and personal connection are strongest. For parents,
teachers, SEN coordinators, and accessibility practitioners.

## v1 Success Definition

Absolute requirement:
- 0% silent structural corruption. Output must never silently drop
  content or corrupt meaning without flagging it.

Quality bar:
- Would you hand this printed document to a student, colleague, or
  parent without apology?

Release gate percentage:
- Deferred until test corpus is defined. Cannot be evaluated until
  corpus categories, composition, and user-facing surface exist.

Release gate (set 2026-03-04):
- Non-negotiable: 0 REGRESSION, 0 FAIL
- Minimum thresholds: PASS >= 60%, MARGINAL <= 40%
- Current state: 46 fixtures, 28 PASS (61%), 18 MARGINAL (39%),
  0 REGRESSION, 0 FAIL
- Thresholds will be revisited after tasks 2a-7 to determine if
  pipeline improvements have raised PASS rates above the minimum.

Engine + surface:
- Both are required for v1 ship. The engine alone is not a product.

## Primary User Hypothesis

Target users are parents, teachers, SEN coordinators, and accessibility
practitioners who currently reformat documents manually. No institutional
buyer dependency. Validation through direct community feedback.

## Primary Beneficiary

Anyone who needs a clearer, more readable version of a web article.
Initial validation focuses on readers with dyslexia or similar
reading-comprehension friction who benefit from controlled typography
and structured prose. The same output benefits readers with ADHD, low
vision, cognitive load issues, or anyone reading in a second language.

## Current Milestone

Corpus expansion -- v1 definition deferred until corpus results are in.

## Phase 2 Exit Criteria

- Guardian and Ringer either (a) fail explicitly and cleanly or (b) extract correct article body.
- No trailing boilerplate (Related, Share, Republish, navigation blocks) in any fixture.
- No structural artifacts (e.g., stray "FORM removed", "[-]" in inappropriate places).
- Titles and opening paragraphs are preserved when present in source.
- No orphan trailing sections.
- Determinism preserved across extraction mode flag.
- No regression on currently clean fixtures.
- Niggle inventory is exhausted for the v1 fixture set (all recorded artifacts are either fixed or explicitly accepted as known limitations).

## Phase 2 Status

Complete. All exit criteria met. Identity10 evaluation: 8 PASS, 1 MARGINAL, 2 FAIL.

## Phase 3 — Ship v1

**Step 1 -- Corpus expansion session** *(next dedicated session)*
Expand test fixtures beyond Identity10 and Eval20. More document types, styles,
and sources. Diagnose Wikipedia failure -- fixable or architectural boundary.
Results determine v1 definition.

**Step 2 -- Print validation** *(needs dedicated planning)*
Requires thought before execution. Questions to resolve:
- Which document types represent real use cases?
- What are we evaluating -- typography, layout, readability, page breaks?
- Who is assessing -- owner alone, or a dyslexic reader?
- What is pass/fail criteria?

Primary reviewer candidate: owner's son. Selection of documents and evaluation
criteria to be agreed before printing anything.

**Step 3 -- Define "done" for the engine**
Explicit, measurable, agreed criteria before corpus results come in. Without this
the engine work has no natural stopping point.

**Step 4 -- Define v1**
Based on corpus results, print validation, and "done" definition. Rewrite
program-board.md Phase 3 tasks against real data.

**Step 5 -- OpenDyslexic embedding**
Contained, spec'd work. Implement before any public release. Not a current
priority.

**Step 6 -- Hosted reference surface (v1 deliverable)**
Required for v1 ship. The engine alone is not a product. Build after
engine is stable and v1 is defined. Accepts a URL or uploaded HTML
file, passes content to the engine, returns the converted document.
Temporary domain (aglet.club) for early testing only -- not the
permanent home. URL input required. Basic typography controls included.

**Step 7 -- PyPI package**
Clean API, well-documented. Enables community surfaces. Architecture and code
review by human contacts before release.

**Step 8 -- Tester recruitment**
Warm introductions via NSPCC network and personal connections. After hosted
surface exists -- nothing to test before then.

## Top Backlog (Ranked)

1. Image preservation pipeline (implementation pending).
   decisions.md sections 7 and 9 specify image URL preservation.
   Code (sanitizer.py, degradation.py, parser.py, model.py,
   renderer.py) still degrades images to placeholder text.
   Completion Criteria: img src preserved through sanitizer;
   model represents preserved images; renderer emits <img> tags
   with original source URLs; WARN placeholder used only when
   src unavailable; tests updated.
   Sequencing: after corpus exercise results determine priority.

2. Trafilatura configuration experiments (baseline vs precision vs fast).
   Completion Criteria: Extraction modes implemented; summary runner compares all 10 fixtures; no default behavior change.

3. Niggle inventory + burn-down plan.
   Completion Criteria: Single consolidated artifact list created; issues classified (boundary / model / sanitization); prioritized remediation plan agreed.

4. ~~Deterministic tail boilerplate trimming.~~ **COMPLETE.**
   Three end-anchored heuristics: anchor-string matching, trailing noise
   pattern removal (credits/copyright/dates/trivial), boilerplate heading
   detection. Covered by regression tests.

5. Intro/title recovery improvements (top-section extraction refinement).
   Completion Criteria: Titles and opening paragraphs preserved where present; no new leading junk introduced; covered by regression tests.

6. Orphan trailing section detector + structural artifact cleanup.
   Completion Criteria: No empty or heading-only trailing sections; placeholders used only where intentional; no regressions.

7. Lightweight preview runner for real-user testing.
   Completion Criteria: Simple local viewer for 5 curated demo pages; usable for qualitative feedback sessions.

## Explicitly Out of Scope (v1)

- JS execution / SPA rendering
- Browser extension
- Hosted SaaS
- PDF/DOCX input
- Site-specific extractor registry
- ML-based extraction
- Visual rendering engine
- Fully offline image rendering (images use external source URLs in v1)
- Self-contained image embedding (self-contained constraint relaxed for images)
