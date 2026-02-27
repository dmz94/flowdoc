# Flowdoc Phase 2 Plan

Purpose:
Phase 2 focuses on extraction reliability and deterministic post-processing. No scope expansion beyond program-board.md.

---

## Phase 2A – Extraction Configuration Experiments (Complete)

Status: Complete

- Baseline vs precision vs recall tested.
- Measurement runner implemented.
- Guardrail tests added.
- Baseline remains production default.

No further work unless new fixture evidence justifies it.

---

## Phase 2B – Deterministic Cleanup Heuristics (In Progress)

### 2B.1 Tail Boilerplate Trim
Goal: Remove trailing CMS boilerplate without affecting mid-document content.
Constraint: End-anchored only. Pattern-based. Tests-first.

### 2B.2 Orphan Trailing Section Dropper
Goal: Remove final heading-only sections (0 content blocks).
Constraint: Structural only. No site-specific strings.

Completion Gate:
- No trailing boilerplate in fixture corpus.
- No orphan trailing sections.
- No regression on clean fixtures.
- Determinism preserved.

---

## Phase 2C – Niggle Inventory Session (In Progress)

Goal:
Capture all remaining structural artifacts across the fixture corpus in one consolidated pass.

Process:
- Run full fixture set.
- Record every artifact.
- Classify into:
  A) Boundary (start/end)
  B) Structural artifact
  C) Sanitization / normalization
- Produce prioritized burn-down list.

Exit:
All recorded artifacts either fixed or explicitly accepted as known limitations.

### Progress / Pause (2026-02-27)

Completed burn-down items 1–5:
1. Drop empty list blocks (eater, guardian)
2. Drop empty heading elements (theringer)
3. Collapse consecutive identical placeholder blocks (aeon, propublica, eater)
4. Drop duplicate consecutive headings (guardian)
5. Extend trailing section drop to all-placeholder sections (structural extension)

Pausing before items 6+.
Items 6+ (end-anchored single-paragraph tail patterns, leading metadata trim,
mid-document section blocklist, duplicate list deduplication) either rely on
site-specific strings or involve start-anchored / content-scoring heuristics
with higher blast radius.  These are not structurally safe to implement without
broader fixture evidence or explicit scope approval.

Resume criteria:
- Any new rule must be structural (no site-specific strings).
- Must be bounded: end-anchored, or first-N-blocks with a conservative
  stop condition (e.g. stop at first block with ≥20 words of prose).
- Must be supported by evidence across at least 2 fixtures.
- If those criteria cannot be met, treat as a known limitation for Phase 2.

---

## Phase 2D – Intro/Title Recovery Improvements

Goal:
Improve preservation of titles and opening paragraphs where extraction misses early content.

Constraint:
No site-specific rules.
No fallback cascade changes.

Completion Gate:
- Titles present when available in source.
- Opening paragraphs preserved.
- No new leading junk introduced.

---

## Phase 2E – Lightweight Preview Runner

Goal:
Enable simple qualitative user testing on 5 curated pages.

Scope:
- Local viewer only.
- No SaaS.
- No browser extension.

Completion Gate:
Usable for real-user feedback sessions.

---

## Phase 2 Exit Criteria

- ≥90% clean extraction across fixture corpus.
- No structural artifacts.
- Determinism preserved.
- Niggle inventory exhausted.
- Ready for controlled qualitative user testing.
