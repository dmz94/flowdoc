# Flowdoc Program Board

## Identity (Frozen)

Flowdoc is a deterministic CLI-based accessibility document compiler that converts semantic prose HTML into structured, readability-optimized, self-contained HTML, with dyslexia-informed typography as the initial focus profile.

## v1 Success Definition

- >=90% of the 10-fixture corpus produces clean article content (no leading junk, no trailing boilerplate, no structural artifacts).
- Output is byte-identical across repeated runs and across supported extraction modes.
- On at least 3 representative complex pages, Flowdoc output is qualitatively preferred over browser Reader Mode.

## Primary Buyer Hypothesis

No validated buyer yet. Phase 2 focuses on technical proof and extraction reliability before committing to a specific B2B segment.

## Primary Beneficiary

Readers with dyslexia or similar reading-comprehension friction who benefit from controlled typography and structured prose.

## Current Milestone

Phase 2 - Extraction reliability and deterministic post-processing.

## Phase 2 Exit Criteria

- Guardian and Ringer either (a) fail explicitly and cleanly or (b) extract correct article body.
- No trailing boilerplate (Related, Share, Republish, navigation blocks) in any fixture.
- No structural artifacts (e.g., stray "FORM removed", "[-]" in inappropriate places).
- Titles and opening paragraphs are preserved when present in source.
- No orphan trailing sections.
- Determinism preserved across extraction mode flag.
- No regression on currently clean fixtures.
- Niggle inventory is exhausted for the v1 fixture set (all recorded artifacts are either fixed or explicitly accepted as known limitations).

## Top Backlog (Ranked)

1. Trafilatura configuration experiments (baseline vs precision vs fast).
   Completion Criteria: Extraction modes implemented; summary runner compares all 10 fixtures; no default behavior change.

2. Niggle inventory + burn-down plan.
   Completion Criteria: Single consolidated artifact list created; issues classified (boundary / model / sanitization); prioritized remediation plan agreed.

3. Deterministic tail boilerplate trimming.
   Completion Criteria: Trailing CMS artifacts removed without breaking clean fixtures; covered by regression tests.

4. Intro/title recovery improvements (top-section extraction refinement).
   Completion Criteria: Titles and opening paragraphs preserved where present; no new leading junk introduced; covered by regression tests.

5. Orphan trailing section detector + structural artifact cleanup.
   Completion Criteria: No empty or heading-only trailing sections; placeholders used only where intentional; no regressions.

6. Lightweight preview runner for real-user testing.
   Completion Criteria: Simple local viewer for 5 curated demo pages; usable for qualitative feedback sessions.

## Explicitly Out of Scope (v1)

- JS execution / SPA rendering
- Browser extension
- Hosted SaaS
- PDF/DOCX input
- Site-specific extractor registry
- ML-based extraction
- Visual rendering engine
