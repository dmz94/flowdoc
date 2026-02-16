# Flowdoc v1 Plan

**Status:** Execution checklist (v1)
**Note:** This plan intentionally links to the frozen scope and to the authoritative implementation spec in `decisions.md` rather than restating contracts.

Key references:
- Scope boundaries: [SCOPE.md](../SCOPE.md)
- Implementation/test contracts: [decisions.md](decisions.md)
- Locked v1 architecture/stack: [ARCHITECTURE.md](ARCHITECTURE.md)
- Typography research reference: [research_typography_guidelines.md](research_typography_guidelines.md)

---

## Step 1 - Confirm scope is frozen

- Ensure [SCOPE.md](../SCOPE.md) reflects v1 boundaries and success criteria.
- Do not expand formats (PDF/DOCX/Markdown) or features (GUI, heuristic extraction) in v1.

## Step 2 - Repository hygiene

- Repo layout, licensing, samples, and tests directories.
- Minimal README with links to docs.
- Add [ABOUT.md](ABOUT.md) for origin story (keep README factual).

## Step 3 - Lock the implementation spec

- [decisions.md](decisions.md) is the single source of truth for:
  - input validation rules
  - content selection and sectioning rules
  - internal model (including nested lists)
  - sanitization allowlist config
  - deterministic element degradation policies
  - renderer invariants + CSS constants
  - CLI contract and exit codes
  - determinism and test contracts

Do not start coding parser/renderer until [decisions.md](decisions.md) is stable.

## Step 3.5 - Lock architecture and tech stack

- [ARCHITECTURE.md](ARCHITECTURE.md) locks:
  - runtime and distribution (Python 3.12+, pip + PyInstaller)
  - selected libraries (BeautifulSoup4 + lxml, nh3, pytest)
  - module structure (core/, cli/, io/)
  - pipeline order with specific library usage
  - locked testing approach (golden files, model snapshots, determinism)

Do not start Step 4 until [ARCHITECTURE.md](ARCHITECTURE.md) is locked. Renderer requirements may expose parser/selection edge cases; locking architecture first prevents rework.

## Step 4 - Build the core pipeline (library-first)

Implement the pure core pipeline described in [decisions.md](decisions.md):

1. sanitize HTML string
2. parse DOM (tolerant parser)
3. select main content (main -> article -> body)
4. parse to internal model (apply degradation rules)
5. render model to self-contained HTML

Core must be pure: no filesystem, no network, no timestamps.

## Step 5 - Implement renderer + CSS invariants

- Emit a stable HTML template.
- Inline CSS (single `<style>`).
- Embed OpenDyslexic only when flag is set.
- Verify print styles preserve readability.

## Step 6 - Implement CLI wrapper (v1 only: convert)

- One command: `flowdoc convert`
- Support file input/output and stdin/stdout per [decisions.md](decisions.md).
- Exit codes and error formatting per [decisions.md](decisions.md).

Explicitly out of v1: `validate`, `info`, `--report json`.

## Step 7 - Test suite

- Fixture corpus (real-world HTML) per [decisions.md](decisions.md).
- Golden output tests and model snapshot tests.
- Determinism test (same input/version/flags -> byte-identical output).

## Step 8 - Reader validation

- Test outputs with dyslexic readers on:
  - phone/tablet/desktop
  - print
  - system font vs OpenDyslexic toggle

Collect structured feedback and decide whether v1 meets success criteria.

## Step 9 - Plan v2 (only after v1 validation)

If v1 validates, consider:
- additional inputs (Markdown, DOCX)
- native PDF output
- additional font toggles
- content transformation (TTS/readability improvements)

Do not implement v2 work during v1.
