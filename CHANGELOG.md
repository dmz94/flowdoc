# Changelog

All notable changes to Flowdoc are recorded here.

---

## [Unreleased] - 2026-02-25

### Changed
- Broadened project vision from dyslexia-only to general accessibility tool.
  Initial focus remains dyslexia; same pipeline extends to ADHD, Irlen Syndrome,
  low vision, and color blindness with minimal additional effort.
- Replaced deterministic content selector (main -> article -> body fallback) with
  Trafilatura as the primary content extraction strategy. Deterministic fallback
  retained for clean semantic HTML inputs. This fixes the main real-world failure
  mode discovered during first fixture validation run.

### Why
First real-world validation against 10 HTML fixtures (Wikipedia, NHS, BBC Good Food,
WikiHow, MDN, Gutenberg, Cleveland Clinic, and others) revealed that the original
content selector failed on pages without main or article tags, pulling in navigation,
language links, and site chrome alongside article content. Trafilatura solves this
with best-in-class extraction (F1 0.958) and is Apache 2.0 licensed.

### Added
- Trafilatura dependency (v1.8.0+, Apache 2.0)

### Architecture docs updated
- README.md, SCOPE.md, ARCHITECTURE.md, decisions.md
