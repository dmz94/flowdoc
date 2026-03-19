# Decant v1 - Locked Architecture and Tech Stack

**Status:** Locked for v1
**Last Updated:** February 16, 2026

This document locks the v1 implementation choices (runtime, libraries, module layout, pipeline, and testing approach).
These are decisions, not options. Do not re-decide them during implementation.

Authoritative behavior contracts (validation rules, model schema, element handling, CSS invariants, CLI contract) live in [decisions.md](decisions.md).
This document answers "what stack do we use and how is the codebase shaped".

---

## Runtime and distribution (locked)

Runtime:
- Python 3.12+ (floor)

Distribution:
- pip package: `pip install decant-cli`
- Hosted web surface at decant.cc

Rationale (short):
- v1 differentiator is transformation quality and iteration speed, not raw performance.
- Python has the strongest HTML parsing ecosystem for tolerant real-world input.

---

## Selected libraries (locked)

Parser:
- BeautifulSoup4 with the lxml backend

Why:
- Tolerant parsing of imperfect HTML.
- Stable and simple traversal API for DOM-to-model extraction.

Alternatives rejected for v1:
- html5lib backend: more browser-faithful but significantly slower (pure Python).
- lxml-only parsing: faster, but higher friction and less forgiving.

Content extractor:
- Trafilatura (Apache 2.0 license, v1.8.0+)

Why:
- Best-in-class main content extraction (F1 0.958 in independent benchmarks).
- Uses readability-lxml and jusText internally as fallbacks.
- Apache 2.0 license - no commercial use restrictions.
- Pure Python, no external dependencies beyond lxml.
- Outputs HTML, preserving structure for downstream parsing.

Sanitizer:
- nh3 (Rust-backed, allowlist-based HTML sanitizer)

Why:
- Allowlist-based security model.
- Actively maintained and fast (Rust ammonia backend).
- Clear configuration for tags, attributes, and URL schemes.

Alternatives rejected for v1:
- bleach: deprecated for this use case; avoid depending on html5lib-based sanitization stack.
- lxml.html.clean: blocklist-style and historically problematic for security-sensitive sanitization.

Testing:
- pytest

Why:
- Strong fixtures and parametrization for golden tests.
- Snapshot/plugin ecosystem for model-level tests.

---

## Module structure (locked)

Target layout:

```
decant/
+-- __init__.py              # Public library API
+-- core/
|   +-- constants.py         # Typography values, colors, spacing
|   +-- model.py             # Internal Document Model classes
|   +-- sanitizer.py         # nh3 wrapper with Decant rules
|   +-- content_selector.py  # Trafilatura extraction with deterministic fallback
|   +-- parser.py            # DOM -> Internal Model transformation
|   +-- degradation.py       # Table/image/form placeholder rules
|   +-- renderer.py          # Model -> HTML + CSS generation
+-- cli/
|   +-- main.py              # CLI wrapper (arg parsing + I/O + exit codes)
+-- io/
    +-- reader.py            # File/stdin reading
    +-- writer.py            # File/stdout writing

tests/
+-- unit/
|   +-- test_*.py
+-- integration/
|   +-- test_*.py
+-- fixtures/               # Shared test fixtures
+-- pipeline-audit/         # Eval harness (metrics + baselines)
|   +-- run_metrics.py
|   +-- audit_config.py
|   +-- expected-results/
|   +-- test-pages/
+-- benchmark-scrapinghub/  # ScrapingHub benchmark runner
+-- benchmark-wceb/         # WCEB benchmark runner
+-- benchmark-structural/   # Structural audit runner
```

Notes:
- `core/` must be pure: no file I/O, no network, no timestamps.
- CLI must be thin: argument parsing, I/O, error formatting, and exit codes only.

---

## Data flow (locked, with specific libraries)

Pipeline order is mandatory (security and correctness):

```
HTML string (user input)
  -> trafilatura.extract()          [core/content_selector.py]
  -> nh3.clean()                    [core/sanitizer.py]
  -> BeautifulSoup(..., "lxml")     [core/parser.py]
  -> validate structure             [core/parser.py]
  -> parse to internal model        [core/parser.py + core/degradation.py]
  -> render self-contained HTML     [core/renderer.py + core/constants.py]
  -> HTML string (output)
```

Important:
- Trafilatura extracts main content before sanitization.
- Sanitization occurs before BeautifulSoup parsing.
- The sanitizer allowlist must include `main`, `article`, and `body`, otherwise content selection can break.

---

## Testing strategy (locked)

Required test layers:

1) Unit and integration tests (pytest)
- Parser, renderer, sanitizer, model, and CLI tests
- Parametrized fixtures for element handling rules

2) Pipeline audit eval harness (separate from pytest)
- 38 real-world HTML fixtures with human-reviewed baselines
- 16 metrics computed per fixture (word counts, structure,
  placeholder density, link-to-prose ratio)
- Threshold-based regression detection
- Status codes: PASS, MARGINAL, REGRESSION, FAIL, NEW
- See docs/eval-harness.md for full reference

3) Determinism test
- run conversion twice with identical input/version/flags
- outputs must be byte-identical

Fixture corpus:
- 38 fixtures from real-world sites (NHS, BDA, Wikipedia,
  news, science journalism, educational content)
- All human-reviewed via interactive baseline process

---

## Deferred to v2 (explicit)

Out of scope for v1 (do not implement in v1):

- Additional CLI commands:
  - `validate`
  - `info`
  - `--report json`
- Additional fonts beyond OpenDyslexic
- Native PDF generation (v1 uses browser print-to-PDF)
- Additional input formats (PDF, DOCX, Markdown)

---

## Engineering Context

(Preserved from docs/technical-companion.md)

### Open Source Systems Reviewed

Reference implementations and extraction baselines studied
during development:

- Mozilla Readability (content extraction algorithm)
- Chromium DOM Distiller
- WebKit Reader Mode
- Trafilatura (current extraction engine)
- Mercury Parser
- jusText / Boilerpipe
- Wallabag (end-to-end extraction + storage pipeline)

### Architectural Seams

Boundaries maintained across all development:

- Extraction layer isolated from transformation logic
- Sanitization as a hard security boundary
- Explicit internal representation (IR) model
- Renderer consumes IR only
- Deterministic transformation passes
- Explicit failure modes (no silent guessing)

### Extraction Dependency Notes

Decant depends on external extraction behavior (Trafilatura).
Constraints:

- Version-pin dependencies
- Document extraction regressions
- Treat extraction changes as explicit events
- Add regression fixtures when behavior changes

### License Awareness

Before incorporating external logic:

- Confirm compatible license
- Avoid copying GPL-locked code into incompatible distribution
- Prefer algorithmic inspiration over direct reuse
- Document attribution where required
