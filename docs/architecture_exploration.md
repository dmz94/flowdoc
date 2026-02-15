# Flowdoc - Architectural Brainstorming

**Status:** Revised  
**Last Updated:** February 13, 2026  

This document captures some architectural brainstorming around Flowdoc's runtime, CLI philosophy, integration strategy, parsing approach, and longer-term considerations. The purpose is to retain the thinking behind early technical exploration without presenting it as finalized decisions.

---

## Runtime And Tech Stack

Will this tool be a Linux or Windows CLI? What is the tech stack? What are the realistic implementation options, what are the pros and cons of each, and why should one be chosen over the others?

First, make an explicit product decision: Flowdoc should be cross-platform from day one (Windows + macOS + Linux). A CLI is inherently portable if the right runtime and packaging approach are selected. Selecting a single OS would unintentionally constrain adoption and downstream integrations. The real decision is the distribution model and runtime.

Tech stack options that fit the v1 scope (semantic HTML -> internal model -> self-contained HTML):

### Option A: Python CLI + Python Library (Recommended For V1)

**Pros**

- Best-in-class HTML parsing and sanitization ecosystem (BeautifulSoup/lxml, html5lib, bleach, etc.).
- Fast iteration speed; easy to prototype transformation rules and typography output.
- Straightforward test tooling, fixtures, and golden-file tests.
- Natural path to a library-first architecture (importable by other tools).

**Cons**

- Packaging can be inconvenient if users must install Python.
- `pip install` works well for developers but is less ideal for non-technical users.

**Mitigation**

- Publish both: a pip package for developers and standalone binaries (via PyInstaller or similar) for non-developers.

### Option B: Node.js CLI + Library

**Pros**

- Common in toolchains; good CLI distribution via npm.
- Solid HTML parsing options (parse5, jsdom, cheerio) and sanitizers.
- Straightforward path to a future Electron wrapper if needed.

**Cons**

- Sanitization correctness and browser-like parsing behavior can become subtle.
- Dependency trees can grow large.
- Producing a true single binary is more difficult without shipping the Node runtime.

### Option C: Go CLI (With Optional Library)

**Pros**

- Excellent single-binary distribution across operating systems.
- Fast and predictable deployment; aligns well with a "Linux command" philosophy.

**Cons**

- HTML parsing and sanitization ecosystem is thinner than Python or Node for this use case.
- Slower iteration while transformation rules are still evolving.
- Rapid changes to typography or layout rules create a heavier development loop.

### Option D: Rust CLI

**Pros**

- Strong performance and safety characteristics; long-term engine credibility.
- Potentially well-suited for embedding as a library later.

**Cons**

- Highest development friction early on.
- HTML parsing and web-like behavior require more effort.
- Overkill for the v1 scope.

### Why Python Is The Recommended Choice For V1

- The differentiator is not parsing; it is the transformation rules, readable HTML output, and validation with dyslexic readers.
- Python minimizes time-to-correctness for sanitization and DOM traversal, and keeps the internal model work inexpensive to evolve.
- A "Linux-command-feeling" tool can still be shipped by distributing a single executable per OS, even if implemented in Python.

### Concrete Recommendation

- Architecture: core engine as a library + thin CLI wrapper.
- Implementation: Python 3.12+.
- Distribution: pip for developers; standalone binaries for Windows/macOS/Linux.
- CLI interface: stable, scriptable, deterministic exit codes, predictable output naming.

---

## Linux Command Philosophy

Do one thing well, and compose with other commands.

What this means in practice:

- The CLI should be a pure transformer: input -> output, with no interactive state, no hidden caches, and no "project" concept.
- It should be easy to use in pipes and automation: predictable exit codes, deterministic output, stable flags.
- Concerns should remain separated: parsing/selection, transformation, rendering, packaging.

How this expresses itself in the CLI:

- Default support for stdin/stdout (even when file arguments are accepted):

  `flowdoc convert < input.html > output.html`

- File I/O remains optional and explicit:

  `flowdoc convert input.html -o output.html`

- Composition-friendly commands rather than a single mega-command:

  - `flowdoc convert` (main transformation)
  - `flowdoc validate` (checks semantic HTML and explains rejection)
  - `flowdoc info` (prints detected title/sections, element counts, degradation summary)

This aligns with a Unix mental model: inspect -> validate -> convert.

Determinism and trust (critical for composability):

- Same input + same version + same flags -> same output (byte-stable if feasible).
- No silent dropping: degraded elements either receive placeholders and/or are reported via a machine-readable report (`--report json`).

This matters for future integrations. If the CLI behaves as a reliable pure function, other tools can invoke it safely. If the engine is separated as a library, direct embedding remains viable.

Minimal rule of thumb:

- Fewer flags, sharper contracts.
- Flags are added only when they change output meaningfully and predictably.

---

## Embedding In Other Tools

There is a goal of allowing other developers to incorporate Flowdoc (e.g., a recipe manager offering "Save as Flowdoc").

This is primarily an architecture and packaging concern. The objective is to be embed-friendly from day one.

What downstream developers typically require:

- A callable library API (preferred).
- Alternatively, a stable CLI they can shell out to.
- Deterministic output and predictable failure modes.
- Machine-readable diagnostics.

Concrete enabling steps:

### A) Library-First Core

Expose a small, stable API such as:

- `convert(html: str, options) -> (output_html: str, report)`
- `validate(html: str) -> report`
- `extract_main(html: str) -> (html_fragment, report)` (optional)

The core should remain pure: no filesystem requirement, no global state.

### B) Stable CLI Contract

- Exit codes: 0 success; non-zero for validation failure, parse error, or internal error.
- `--report json` option producing structured diagnostics.
- `--stdout` mode for piping.

### C) Versioning Strategy

Downstream tools are sensitive to unexpected visual diffs.

- Semantic versioning.
- Clear documentation of what changes in MINOR versus MAJOR.
- Formatting rule changes that alter appearance should be treated as potentially breaking.

### D) Licensing And Embedding

MIT licensing supports adoption.  
OpenDyslexic license handling should remain explicit.

### E) Integration Documentation

A concise `docs/integration.md` describing:

- Library usage.
- CLI usage.
- Exit codes.
- Report schema.
- Example calls.

A commercial tool is more likely to embed a library dependency than require users to install an external CLI. The architectural implication is clear: separate the core conversion engine cleanly from the CLI layer.

---

## HTML Parsing And Library Reuse

HTML parsing is a solved problem and should rely on mature libraries. Parsing and sanitizing HTML is not the differentiator; transformation rules and readable output are.

Key principle:

- Do not implement a custom HTML parser.
- Do not implement a custom sanitizer.
- Treat those as infrastructure.

Required capabilities from parsing:

- Correct handling of real-world, imperfect HTML.
- Reliable DOM traversal.
- HTML5-compliant parsing behavior.
- Safe sanitization (scripts, event handlers, external resources removed).

Ownership boundaries:

**Owned**

- DOM -> Internal Model mapping.
- Degradation rules (tables, images, etc.).
- Main content extraction policy (main -> article -> body).
- Typography and layout generation.
- Deterministic rendering rules.

**Not Owned**

- Low-level tokenization.
- HTML specification edge-case handling.
- XSS protection logic.
- URL normalization.

Architectural flow:

HTML input  
-> Parser (library)  
-> Sanitizer (library)  
-> DOM tree  
-> Internal Document model  
-> Readability transformation rules  
-> Deterministic HTML renderer  

Scraping-style heuristic extraction would shift the product into a different problem space. For v1, focus remains on well-structured semantic HTML.

Reuse aggressively. Time and complexity should be invested in the internal model and transformation layer.

---

## Additional Strategic Considerations

### Testing Strategy

Golden file tests (input -> exact expected output).  
Regression tests for typography and layout rules.  
A real-world fixture corpus (recipes, articles, technical documentation).

Formatting engines drift without golden tests.


### Change Control Over Formatting Rules

Typography tweaks may appear minor but can be visually breaking.

Key questions:

- Are formatting rule changes treated as MAJOR version bumps?
- Are visual shifts permitted in MINOR versions?


### Output Stability Vs Readability Evolution

If spacing or font sizing improves based on research or feedback:

- Should existing output automatically adopt the new behavior?
- Or should versioned "format profiles" exist?


### Main-Content Extraction Boundary

Current policy: deterministic selection (main -> article -> body).

Introducing heuristic readability extraction (similar to Readability.js) would shift the product into scraping territory and significantly increase maintenance complexity.


### Internationalization

Areas not yet addressed:

- Non-English languages.
- Right-to-left scripts.
- CJK typography.
- Hyphenation rules.

A decision may be required on whether v1 is intentionally English-focused.


### Accessibility Positioning

Clarify whether the goal is:

- Informal accessibility improvement, or
- Explicit alignment with WCAG standards.

This distinction affects long-term positioning and potential institutional adoption.


### Feedback And Iteration Model

Validation with dyslexic readers implies a structured feedback loop.

Questions to consider:

- How will feedback be collected?
- Will typography rules evolve in response?
- How will changes be communicated?


### Governance Model

If open source:

- Who approves typography or formatting changes?
- How are disputes resolved?
- Are external pull requests accepted for formatting rules?


### Long-Term Positioning

Determine whether Flowdoc remains dyslexia-specific or evolves into a broader readability engine with dyslexia as a primary focus.