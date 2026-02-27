# Technical Companion (Engineering Context)

Status: Active
Supports: docs/strategy.md

This document preserves architectural intent and open-source leverage
considerations that support the Flowdoc compiler model.

It is not positioning.
It is engineering context.

---

## 1. Open Source Systems to Review and Learn From

These systems are reference implementations or extraction baselines:

- Mozilla Readability (content extraction algorithm)
- Chromium DOM Distiller
- WebKit Reader Mode
- Trafilatura (current extraction engine)
- Mercury Parser
- jusText / Boilerpipe
- Wallabag (end-to-end extraction + storage pipeline)

Purpose:
- Understand extraction heuristics
- Compare degradation behavior
- Study distillability signals
- Identify architectural separation patterns

Flowdoc may reuse ideas.
It must not copy incompatible licensed code.

---

## 2. Architectural Seams to Preserve

Even in v1, maintain these boundaries:

- Extraction layer isolated from transformation logic
- Sanitization as a hard security boundary
- Explicit internal representation (IR) model
- Renderer consumes IR only
- Deterministic transformation passes
- Explicit failure modes (no silent guessing)

Future compiler passes may include:

- Paragraph repair
- Boilerplate trimming
- Fragment merging
- Nested list normalization
- Structural repair for imperfect semantic HTML

Expansion deepens quality before widening scope.

---

## 3. Extraction Dependency Notes

Flowdoc currently depends on external extraction behavior.

Constraints:
- Version-pin dependencies
- Document extraction regressions
- Treat extraction changes as explicit events
- Add regression fixtures when behavior changes

If extraction quality proves insufficient,
Flowdoc may introduce additional structural normalization passes
without violating IR and determinism constraints.

---

## 4. License Awareness

Before incorporating external logic:

- Confirm compatible license
- Avoid copying GPL-locked code into incompatible distribution
- Prefer algorithmic inspiration over direct reuse
- Document attribution where required

---

End of document.
