# Technical Decisions and Rationale

**Status:** Revised  
**Last Updated:** February 13, 2026  

This document captures key technical decisions for Flowdoc v1, including typography research, implementation choices, and the reasoning behind them.

---

## Project Origin

Flowdoc started with a simple request: convert a recipe PDF to make it easier for my dyslexic son to read.

I used PDF-XChange Editor to manually reformat the document with dyslexia-friendly typography, including the OpenDyslexic font. It worked, but the process was tedious and clunky. After finishing, I learned the recipe site could export to HTML.

That triggered a realization. At Oxford University Press, I managed the technology team for the dictionary division. We stored data in XML and JSON and built parsers to extract structured content from third-party dictionaries. If structured dictionaries could be parsed, so could structured recipes.

Recipe sites already contained semantic structure: headings, ingredients lists, instructions. The same pattern appeared in articles, documentation, and educational materials. The problem was broader than recipes.

The decision was to build a general-purpose tool, not a recipe manager. Start simple. Validate with real users. Expand only if it proves useful.

Flowdoc is that tool.

---

## Typography and Design Decisions

### Font Choices

Default: System font stack (Arial, Verdana)

Rationale:
- British Dyslexia Association recommends sans serif fonts such as Arial and Verdana
- Universally available
- No licensing concerns
- No embedding required
- Research shows standard sans serif fonts perform as well as specialized dyslexia fonts for speed and accuracy

**Embedding rule: System fonts are never embedded in output HTML.**

v1 Font Toggle: OpenDyslexic (optional)

Implementation:
- Enabled via `--font opendyslexic`
- Embedded as base64 in CSS only when selected
- Not embedded by default
- **Font selection is binary: system fonts OR OpenDyslexic only**

Research context:
- Most controlled studies show no reliable improvement over standard sans serif fonts
- Some preliminary evidence suggests possible comprehension benefits in longer texts for adults
- Individual preference varies significantly
- Provided as an option, not a recommendation

License: SIL Open Font License (OFL), embedding permitted

Deferred to v2:
- Lexend
- Atkinson Hyperlegible
- Dyslexie

See [research_typography_guidelines.md](research_typography_guidelines.md) for full research summary.

---

## Internal Document Model

**Model structure (v1):**

```
Document
  - title
  - sections[]
    - heading
    - blocks[]
      - paragraph (contains inline elements)
      - ordered_list (items contain inline elements)
      - unordered_list (items contain inline elements)
      - preformatted (code/pre blocks)
      - quote (blockquote, contains inline elements)

Inline elements (explicitly modeled):
  - text
  - emphasis (em, i)
  - strong (strong, b)
  - code (inline code)
  - link (a with href and text)
```

**Critical constraint:**
Inline elements must be modeled explicitly in the internal representation.

**Rationale:**
Without explicit inline modeling, the parser must choose between:
- Dropping inline semantics (data loss) - breaks technical/work documents
- Leaking raw HTML into output (breaks rendering and trust)

Both outcomes are unacceptable for a general-purpose document converter.

**Block type additions:**
- `preformatted`: Protects code blocks and technical content from formatting interference
- `quote`: Explicit blockquote handling preserves semantic distinction from regular paragraphs

These prevent silent structure flattening and maintain semantic clarity required for technical and work documents.

**Intentional exclusions:**
The internal model is intentionally minimal. Unsupported structures (tables, images, forms, navigation elements, etc.) are not represented in the model and are handled via deterministic degradation rules defined in the HTML Element Handling section.

---

## Spacing and Layout

Line Height  
Decision: 1.5 (150%)  
Rationale: Explicit BDA recommendation.

Letter Spacing  
Decision: ~0.02em starting point  
Rationale: Increased spacing can help readability, but excessive spacing reduces it. Conservative baseline validated via user testing.

Word Spacing  
Decision: ~0.16em (minimum 3.5x letter spacing)  
Rationale: Must scale proportionally with letter spacing to maintain word boundaries.

Line Length  
Decision: 60-70 characters  
Rationale: Reduces eye-tracking fatigue and excessive line breaks.

Color and Contrast  
Decision:
- Background: Cream/off-white (#FEFCF4 or similar)
- Text: Dark gray/black (#333333 or darker)
- Contrast: WCAG AA minimum

Rationale: Pale backgrounds reduce glare and visual stress.

---

## Why HTML First?

Decision: v1 accepts HTML only.

Rationale:
- HTML already contains semantic structure
- Parsing is reliable
- Reduces ambiguity
- Focus remains on conversion quality

Deferred to v2: DOCX and Markdown input.

---

## Semantic HTML Requirement

Decision: Reject non-semantic HTML.

Rejection criteria:
- No h1-h6 headings
- No p, ul, or ol elements
- Pure div-based layout

Error:
"Input HTML lacks semantic structure (no headings, paragraphs, or lists found). Flowdoc requires semantic HTML elements (h1-h6, p, ul, ol)."

Rationale: Dyslexia-friendly formatting depends on structure. Inferring structure from divs is unreliable.

---

## Main Content Selection

Deterministic rule:
1. Use `<main>` if present
2. Else `<article>`
3. Else `<body>`

If multiple article elements exist: Use the first article element. Additional article elements are ignored.

Drop entirely:
- nav
- header
- footer
- aside

Rationale: Predictable and testable behavior aligned with HTML5 semantics.

---

## HTML Element Handling

Supported:
- h1-h6
- p
- ol, ul
- blockquote
- pre, code
- em, strong
- a (href only)

Tables:
- Replace with "[Table omitted - X rows, Y columns]"
- Count tr elements for rows
- Count maximum immediate td/th children for columns

Images:
- If alt exists: "[Image: alt text]"
- Else: "[Image omitted]"

Figures:
- Preserve figcaption text
- Handle embedded images per image policy

Footnotes:
- Convert to paragraphs at reference point
- Drop markers

Forms:
- Replace with "[Form omitted]"

Dropped:
- nav
- aside
- header
- footer
- advertisements
- decorative containers

---

## Inline Handling

Whitespace:
Preserve standard HTML whitespace collapsing rules.

Example:
`word<strong>next</strong>` renders as "word next".

Nested inline tags:
Support one level. Flatten deeper nesting while preserving innermost semantic meaning.

---

## HTML Sanitization

Drop entirely:
- script tags
- event handlers
- iframe
- object
- embed
- all active content

Keep:
- href (links only)

Drop attributes:
- style
- class
- id
- data-*
- event handlers

URL Handling:
* Strip javascript: protocol URLs entirely
* Preserve http: and https: URLs in href attributes
* Preserve fragment identifiers (hash links) for internal navigation
* Remove data: URLs

Rationale: Prevent script injection and layout leakage.

---

## PDF Strategy

Decision: v1 uses browser print-to-PDF.

Rationale:
- Preserves CSS exactly
- No heavy dependencies
- Cross-platform

Deferred:
Native PDF generation (e.g., headless browser) due to dependency size and complexity.

---

## Readability Over Fidelity

Flowdoc does not preserve original layout, branding, or geometry.

Rationale:
Dyslexia-friendly formatting requires specific typography and spacing. Layout preservation would undermine readability.

---

## CLI Failure Semantics

Exit codes:
- 0: Success
- 1: Parse error
- 2: Render error
- 3: I/O error

Errors:
- Written to stderr
- stdout contains only output HTML

Non-semantic input:
- Hard fail
- Exit code 1
- Clear error message
- No best-effort conversion

---

## CSS Invariants

Typography:
- Arial or Verdana (or OpenDyslexic if toggled)
- Font size: 18px body text (default; BDA baseline range is 16-19px, but 18px chosen for consistency and screen readability)
- Line height 1.5
- Letter spacing ~0.02em
- Word spacing ~0.16em

Layout:
- 60-70 character line width
- Single column
- Generous margins
- Left-aligned

Spacing:
- Headings >=20% larger than body
- >=1em paragraph spacing
- >=1.5em before headings
- Clear list indentation

Color:
- Cream background
- Dark text
- WCAG AA contrast

Links:
- Underlined or clearly distinct
- Remain identifiable in print

Print:
- Do not shrink below 12pt
- Adequate margins
- Maintain contrast in black-and-white

---

## Architecture Principles

**Determinism:**
The transformation engine must be deterministic. Identical input + identical version + identical flags -> identical output (model representation and rendered HTML).

**Note:** Formatting rules are subject to change during v1 validation based on dyslexic reader feedback.

**Parser constraints:**
The parser layer must map cleanly into the internal document model without special cases or raw DOM structure dependencies.

Any HTML structure not representable in the internal model must be degraded deterministically before model construction, following the rules defined in the HTML Element Handling section.

**Renderer constraints:**
The renderer must never depend on raw DOM structures. All rendering decisions derive from the internal model only.

**Library reuse:**
HTML parsing and sanitization will reuse mature, well-tested libraries rather than custom implementations.

**Content selection:**
Content selection (main -> article -> body) is deterministic and rule-based. Flowdoc v1 does not include heuristic readability algorithms or scraping logic.

**Rationale:**
- Determinism enables golden-file testing and prevents formatting drift
- Clean parser/model mapping prevents accumulation of special cases and edge-case handling
- Renderer independence from DOM ensures portability and testability
- Mature libraries reduce security vulnerabilities and parsing edge cases
- Deterministic content selection maintains predictable, testable behavior

---

## Success Criteria for v1

1. Accepts semantic HTML
2. Produces self-contained readable HTML
3. Improves measurable readability for dyslexic readers
4. Works across browsers, mobile, and print
5. CLI is simple
6. Licensing documented
7. Predictable failure modes
8. Correct inline rendering
9. Graceful degradation for unsupported elements
10. Secure sanitization

---

## Research Sources

- British Dyslexia Association (2023). Dyslexia Friendly Style Guide
- Kuster et al. (2018). Annals of Dyslexia
- Marinus et al. (2016). Dyslexia
- Wery & Diliberto (2017). Annals of Dyslexia
- Rello & Baeza-Yates (2013). ACM SIGACCESS
- Zorzi et al. (2012). PNAS
- Franzen et al. (2019). Annals of Eye Science (conference abstract)

See [research_typography_guidelines.md](research_typography_guidelines.md) for full research summary.

## Step 3.5 - Architecture & Tech Stack

**Status:** Locked for v1 implementation  
**Last Updated:** February 15, 2026

This section documents all architectural and runtime decisions required before implementing the parser (Step 4) and renderer (Step 5). These decisions are locked to prevent rework caused by discovering architectural incompatibilities during implementation.

---

## Runtime & Distribution Decision

**Decision:** Python 3.12+ with dual distribution (pip package + standalone binaries)

### Evaluation Criteria

Runtime selection evaluated against:
- HTML parsing maturity and ecosystem quality
- Sanitization reliability and security track record
- Iteration speed during transformation rule evolution
- Testing ecosystem capabilities
- Cross-platform packaging feasibility
- Deterministic output capability
- Clean library-first architecture support

### Python 3.12+ (Selected)

**Pros:**
- Best-in-class HTML parsing ecosystem (BeautifulSoup4, lxml, html5lib)
- Modern sanitization library with Rust performance (nh3)
- Fast iteration on transformation rules (the actual differentiator for v1)
- Excellent testing ecosystem (pytest, snapshot testing, coverage tools)
- Natural library-first architecture (clean separation, easy embedding)
- Cross-platform packaging via PyInstaller produces single-file executables
- Deterministic output achievable through pure functions and stable libraries

**Cons:**
- Slower raw execution than compiled languages (mitigated by nh3's Rust backend for sanitization)
- Distribution requires either Python installation (pip) or larger binary bundles (PyInstaller)

**Justification:**

The core differentiator for Flowdoc is not parsing speed but transformation quality. The tool must:
1. Parse real-world, malformed HTML reliably
2. Apply complex typography and spacing rules
3. Degrade unsupported elements deterministically
4. Iterate rapidly based on dyslexic reader feedback

Python's HTML parsing ecosystem (BeautifulSoup4 + lxml) has been battle-tested on billions of pages and handles malformed HTML gracefully. The nh3 sanitizer provides Rust-level performance for security-critical sanitization while maintaining a Python API.

Most importantly, typography rules and degradation logic will evolve based on user testing. Python's iteration speed (modify rule -> test -> validate) is significantly faster than compiled languages, accelerating the feedback loop during v1 validation.

The library-first architecture is natural in Python: core functions accept strings and return strings or model objects, with no file I/O. This enables clean embedding for downstream tools.

**Python 3.12+ floor rationale:**

Minimum Python 3.12 rather than 3.10 or 3.11:
- Reduces test matrix complexity (fewer versions to test/support)
- Python 3.12+ is widely available (released Oct 2023)
- Modern tooling assumes 3.11+ (ruff, mypy improvements)
- v1 scope does not require backward compatibility to older versions
- Can revisit if users request 3.11 support with concrete use cases

### Node.js (Rejected)

**Why considered:**
- Good CLI distribution via npm
- Solid HTML parsing (parse5, jsdom, cheerio)
- Common in web toolchains

**Why rejected:**
- HTML5 parsing correctness more subtle than Python equivalents
- Sanitization ecosystem less mature than nh3
- Larger dependency trees (npm sprawl)
- Single-binary distribution harder without bundling Node runtime
- No clear advantage for Flowdoc's use case

### Go (Rejected)

**Why considered:**
- Excellent single-binary distribution
- Fast execution
- Good for CLI tools

**Why rejected:**
- Significantly thinner HTML parsing ecosystem than Python
- Would require more custom parsing logic (increases maintenance burden)
- Slower iteration on typography rules (compile cycle adds friction)
- Parsing isn't the bottleneck; transformation rules are the focus
- No compelling advantage justifies the ecosystem trade-off

### Rust (Rejected)

**Why considered:**
- Maximum performance
- Strong safety guarantees
- Excellent for long-term engine credibility

**Why rejected:**
- Highest development friction during rule evolution
- HTML parsing ecosystem exists (html5ever) but requires more expertise
- Overkill for v1 scope (not a performance-critical system)
- Slower iteration during user testing phase
- We get Rust performance where it matters (sanitization via nh3) without Rust dev friction

### Distribution Strategy

**Dual approach:**

1. **pip package (primary for developers):**
   - `pip install flowdoc`
   - Requires Python 3.12+
   - Lightweight, fast installation
   - Easy to integrate into Python projects

2. **Standalone binaries (PyInstaller for non-developers):**
   - Single-file executables for Windows, macOS, Linux
   - No Python installation required
   - Larger file size (approximately 20-50MB) but zero dependencies
   - Published via GitHub Releases

This dual approach maximizes accessibility: developers get lightweight pip installs, non-technical users get click-to-run binaries.

---

## Selected Libraries

### Parser: BeautifulSoup4 with lxml Backend

**Library:** `beautifulsoup4` + `lxml`

**Responsibility:**
- Tolerant HTML parsing and stable DOM construction
- Handles malformed, real-world HTML gracefully
- Provides traversal primitives used for content selection and inline extraction

**Why BeautifulSoup4:**
- Most widely used Python HTML parser (tested on billions of pages)
- Excellent handling of malformed HTML (auto-fixes unclosed tags, misnested elements)
- Clean, intuitive API for DOM traversal
- Can switch backends (lxml for speed, html5lib for stricter compliance if needed)
- Mature documentation and large community
- Actively maintained (supports Python 3.8+ as of Feb 2026)

**Why lxml backend:**
- Significantly faster than pure-Python backends (C-based libxml2)
- Handles real-world HTML edge cases well
- Provides XPath support if needed later
- Good balance of speed and correctness for Flowdoc's use case

**Important clarification on "HTML5 compliance":**

BeautifulSoup4 + lxml is NOT strictly HTML5-spec-compliant and does NOT parse exactly like modern browsers. It uses a pragmatic, tolerant approach that fixes common errors but may produce different DOMs than browser parsers for edge cases.

For v1, this is acceptable:
- Flowdoc targets semantic HTML (well-formed structure)
- Input validation rejects div soup (non-semantic HTML)
- Tolerant parsing helps with minor markup errors
- Browser-identical parsing is not a requirement

If future versions require exact browser parsing behavior, html5lib backend (slower, pure Python, strictly HTML5-compliant) can be substituted.

**Alternative considered: html5lib backend**
- Strictly HTML5-compliant (parses exactly like browsers)
- Significantly slower (pure Python)
- Decision: Use lxml for v1 speed; tolerant parsing is sufficient for semantic HTML inputs

**Alternative considered: lxml directly (no BeautifulSoup4)**
- Faster but harder to use
- Less forgiving with malformed HTML
- Steeper learning curve
- Decision: BeautifulSoup4's usability and error-tolerance outweigh raw speed gains

### Sanitizer: nh3

**Library:** `nh3` (Python bindings to Rust ammonia library)

**Responsibility:**
- Strip active content (scripts, event handlers, iframes)
- Filter attributes (keep href only, drop style/class/id/data-*)
- Filter URL protocols (block javascript:, data:; allow http/https)
- Allowlist-based security model

**Allowlist configuration:**
- **Structural tags (required for content selection):** `main`, `article`, `body`
- **Semantic tags:** `h1`, `h2`, `h3`, `h4`, `h5`, `h6`, `p`, `ul`, `ol`, `li`, `blockquote`, `pre`, `code`
- **Inline tags:** `em`, `i`, `strong`, `b`, `a`
- **Allowed attributes:** `href` only (for `<a>` tags)
- **Blocked:** `script`, `style`, `iframe`, `object`, `embed`, event handlers, `javascript:` URLs, `data:` URLs
- **Allowed URLs:** `http:`, `https:`, fragment identifiers (`#`)

**CRITICAL:** `<main>`, `<article>`, and `<body>` must be in the allowlist. Sanitization occurs BEFORE content selection (main -> article -> body logic). If these tags are stripped, content selection breaks silently.

**Critical policy:** Sanitization occurs before DOM-to-model parsing. The internal model never sees unsanitized HTML. This boundary prevents security vulnerabilities from propagating through the system.

**Why nh3:**

We prefer nh3 for v1 based on:
- **Actively maintained:** Regular updates, latest release Oct 2025
- **Allowlist-based:** Secure by design (explicitly allow safe content, block everything else)
- **Performance:** Approximately 20x faster than pure-Python alternatives (Rust backend via ammonia library)
- **Battle-tested:** Rust ammonia library is widely used in production, security-focused
- **MIT licensed**
- **Cross-platform:** Pre-built wheels for Windows, macOS, Linux (Python 3.8+)
- **Clean API:** Straightforward configuration

**Performance benchmark (from nh3 documentation):**
- Pure Python alternative: 2.85ms per page
- nh3: 0.138ms per page
- Speedup: approximately 20x

**Context on bleach:**

The previously common choice, `bleach`, was deprecated in January 2023. The maintainer cited concerns about building a security-focused library on top of html5lib, which had reduced maintenance activity. We avoid bleach for v1 to minimize dependency on unmaintained foundations.

**Alternative considered: lxml.html.clean**
- Blocklist-based approach (harder to maintain securely)
- Has had security vulnerabilities historically
- Explicitly not recommended for security-sensitive use by lxml maintainers
- Removed from lxml core (now separate lxml-html-clean package)
- Decision: Prefer allowlist-based approach (nh3)

**Alternative considered: html-sanitizer**
- Too opinionated (auto-converts tags, normalizes whitespace)
- Does more than sanitization (transformations we don't want)
- Decision: Need pure sanitization without side-effect transformations

**Mapping Flowdoc sanitization rules to nh3:**

From decisions.md sanitization section, nh3 enforces:
- Drop scripts: `tags` parameter excludes `<script>`
- Drop event handlers: `attributes` parameter strips all event attributes
- Drop iframes/object/embed: `tags` parameter excludes these
- Keep href only: `attributes={'a': ['href']}` 
- Block javascript:/data: URLs: `url_schemes` parameter
- Strip style/class/id: Not in `attributes` allowlist

Example configuration:

```
nh3.clean(
    html,
    tags={
        'html', 'head', 'body',
        'main', 'article',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p',
        'ul', 'ol', 'li',
        'blockquote',
        'pre', 'code',
        'em', 'strong',
        'a'
    },
    attributes={'a': ['href']},
    url_schemes={'http', 'https'},
    strip_comments=True
)
```

### Testing Framework: pytest

**Library:** `pytest`

**Responsibility:**
- Unit testing (parser, sanitizer, renderer, degradation)
- Integration testing (golden files, end-to-end)
- Fixture management
- Snapshot testing (via pytest plugins)
- Coverage reporting

**Why pytest:**
- Python standard for testing
- Excellent fixture system (perfect for golden files)
- Parametrized tests (test same logic against multiple fixtures)
- Plugin ecosystem (pytest-snapshot, pytest-cov)
- Clean assertion syntax
- Fast test discovery and execution

**Alternative considered: unittest (stdlib)**
- More verbose
- Less powerful fixtures
- No built-in parametrization
- Decision: pytest's features justify the dependency

---

## Module Architecture

### Directory Structure

```
flowdoc/
├── __init__.py              # Public library API: convert()
├── core/
│   ├── __init__.py
│   ├── constants.py         # Typography values, colors, spacing
│   ├── model.py             # Internal Document Model classes
│   ├── sanitizer.py         # nh3 wrapper with Flowdoc rules
│   ├── content_selector.py  # main -> article -> body selection
│   ├── parser.py            # DOM -> Internal Model transformation
│   ├── degradation.py       # Table/image/form placeholder rules
│   └── renderer.py          # Model -> HTML + CSS generation
├── cli/
│   ├── __init__.py
│   ├── main.py              # Entry point, argument parsing
│   └── commands.py          # convert command implementation
└── io/
    ├── __init__.py
    ├── reader.py            # File/stdin reading
    └── writer.py            # File/stdout writing

tests/
├── fixtures/
│   ├── input/               # HTML test files
│   ├── expected/            # Expected output HTML
│   └── snapshots/           # Model JSON snapshots
├── test_parser.py
├── test_sanitizer.py
├── test_content_selector.py
├── test_degradation.py
├── test_renderer.py
├── test_cli.py
└── test_integration.py      # Golden file tests
```

### Data Flow

```
HTML string (user input)
    ↓
sanitizer.sanitize()
    - nh3.clean() with Flowdoc rules
    - Strips scripts, event handlers, unsafe attributes
    - Blocks javascript:, data: URLs
    ↓
BeautifulSoup(html, 'lxml')
    - Parse to DOM tree
    - Handle malformed HTML
    ↓
content_selector.select_main()
    - Apply main -> article -> body rule
    - Return selected DOM subtree
    ↓
parser.parse_to_model()
    - Walk DOM tree
    - Build Internal Document Model
    - Apply degradation rules (tables -> placeholders, etc.)
    - Extract inline elements explicitly
    ↓
Internal Document Model
    - Document(title, sections[])
    - Section(heading, blocks[])
    - Blocks: Paragraph, List, Quote, Preformatted
    - Inline: Text, Emphasis, Strong, Code, Link
    ↓
renderer.render_html()
    - Model -> HTML string
    - Inject CSS from constants.py
    - Embed OpenDyslexic font if --font flag set
    - Generate self-contained HTML
    ↓
HTML string (output)
```

### Architectural Invariants

**Core layer (pure, no I/O):**

The core layer contains only pure functions and classes. No file I/O, no network access, no environment variables.

Functions accept strings or model objects, return strings or model objects. This enables:
- Deterministic testing (same input -> same output)
- Clean embedding (downstream tools import core, never touch CLI/IO)
- Parallel execution (no shared state)

**Renderer must NEVER access raw DOM:**

The renderer receives only the Internal Document Model. It has zero access to BeautifulSoup objects or raw HTML.

Why: This enforces clean separation. If the renderer needed DOM access, parser/renderer coupling would grow and testing would become brittle. The model is the contract.

**Parser must NEVER leak raw HTML into model:**

Inline elements are modeled explicitly (Text, Emphasis, Strong, Code, Link objects), not raw HTML strings.

Why: Leaking `<em>` tags as strings into Paragraph.content breaks rendering and creates security holes. Explicit modeling prevents this.

**Determinism enforced at core layer:**

All randomness, timestamps, or external state is forbidden in core/. Same input + same version + same flags -> byte-identical output.

How enforced:
- constants.py contains all magic numbers (no inline constants)
- No file I/O in core (no filesystem timestamps)
- No external API calls
- Dependencies use compatible version ranges during development; changes require regenerating golden files intentionally
- Release builds are cut from an exact, locked dependency set (lockfile committed at release tag)

**CLI layer is thin:**

CLI responsibility: argument parsing, file I/O, error formatting, exit codes.

The CLI never contains business logic. All transformation logic lives in core/.

Why: Embedding requires zero CLI dependencies. Downstream tools import `flowdoc.convert()`, never touch argparse or file I/O.

---

## Testing Strategy

### Test Types

**1. Golden File Tests**

Input HTML file -> Expected output HTML file. Byte-stable comparison.

Purpose: Regression prevention. If output changes unexpectedly, test fails.

Implementation:
- tests/fixtures/input/ contains HTML files
- tests/fixtures/expected/ contains expected output HTML
- test_integration.py runs conversion, compares byte-for-byte
- Parametrized test runs all fixtures automatically

**2. Model Snapshot Tests**

Parser output (Internal Document Model) -> JSON snapshot -> Comparison.

Purpose: Test parser independently of renderer. Validates DOM -> Model transformation without caring about HTML output.

Implementation:
- Parser produces Document object
- Serialize to JSON (model.to_json())
- Compare against stored snapshot
- tests/fixtures/snapshots/ contains JSON snapshots
- pytest-snapshot plugin manages snapshots

Benefits:
- Catches "one parser tweak broke list nesting everywhere" failures
- Faster than full HTML comparison
- Validates model structure explicitly

**3. Unit Tests**

Individual function/class testing.

Coverage:
- Sanitization: nh3 rules applied correctly, javascript: URLs blocked, event handlers stripped
- Content selection: main -> article -> body logic, edge cases (multiple articles, no main)
- Degradation: table placeholders count rows/columns correctly, image alt text preserved
- Inline handling: whitespace preserved across element boundaries, nesting handled correctly
- Typography: constants applied correctly, font embedding works
- CLI: argument parsing, exit codes, I/O behavior

**4. Error Contract Tests**

Invalid inputs produce correct errors.

Coverage:
- Non-semantic HTML rejection (no headings/paragraphs) -> exit code 1, clear error message
- Malformed HTML -> parsed gracefully or rejected with clear error
- Missing input file -> exit code 3, clear error
- Output directory doesn't exist -> exit code 3, clear error

### Fixture Corpus (Minimum Required for v1)

All fixtures must be real-world HTML (exported from actual sites/tools), not hand-crafted minimal examples.

Required fixtures:

1. **Recipe** - Semantic structure with ingredients list, instructions, headings
2. **Article/blog post** - Typical web content with paragraphs, headings, links
3. **Technical documentation** - Code blocks, inline code, technical terminology
4. **Instructional content** - How-to with numbered steps, clear hierarchy
5. **List-heavy document** - Nested lists (mixed ordered/unordered), list items with inline elements
6. **Document with quotes** - Blockquotes, citations, nested quotes
7. **Dense inline elements** - Heavy use of em, strong, inline code, links (stress test whitespace)
8. **Main content selection test** - Has header, nav, footer, sidebar PLUS `<main>` or `<article>` to validate selection
9. **Inline whitespace stress test** - Dense inline emphasis/links/code, validates whitespace preservation across boundaries
10. **Edge case document** - Image with missing alt, table with colspan/rowspan, form elements

**Non-semantic HTML fixture (must trigger rejection):**
- Div soup (no h1-h6, no p, no ul/ol)
- Should exit with code 1 and error: "Input HTML lacks semantic structure"

### Optional Future Testing Enhancement

**html5lib-tests corpus:**

The html5lib-tests repository contains thousands of HTML parsing test cases. This is NOT required for v1 but could be considered in v2 for additional validation.

Rationale for deferral:
- v1 targets semantic HTML with clear structure requirements
- Curated fixture corpus covers v1 scope adequately
- html5lib-tests targets exhaustive HTML5 compliance (broader than v1 needs)
- Would add git submodule dependency and test complexity

If revisited in v2, use selectively (cherry-pick relevant malformed-semantic-HTML cases, not exhaustive browser compliance tests).

### Test Execution Requirements

**Performance target:** Full test suite under 30 seconds (enables fast iteration)

**Determinism validation:** Conversion run twice with identical output (byte-stable comparison)

---

## CLI Specification

### Command Structure

**Single command for v1:**

```
flowdoc convert <input.html> [-o OUTPUT] [--font opendyslexic]
```

### Arguments and Flags

**Positional argument:**
- `<input.html>` - Path to input HTML file (required unless reading from stdin)

**stdin detection:**
- If no positional argument provided and stdin is not a TTY (terminal), read from stdin
- If no positional argument provided and stdin IS a TTY, fail with clear error: "Error: No input file specified. Use 'flowdoc convert <file>' or pipe input via stdin."
- Enables pipe workflows without explicit flags
- Prevents confusing hangs when run without arguments in interactive terminal

**Optional flags:**
- `-o, --output PATH` - Output file path (default: `<input>.flowdoc.html` in same directory as input)
- `--font opendyslexic` - Use OpenDyslexic font instead of system fonts (embeds font in output)
- `--help` - Show help message and exit
- `--version` - Show version number and exit

### I/O Behavior

**File input/output (default mode):**

```
flowdoc convert recipe.html
```
- Reads: recipe.html
- Writes: recipe.flowdoc.html (same directory as input)
- Errors: stderr
- Exit code: 0 on success

```
flowdoc convert recipe.html -o readable.html
```
- Reads: recipe.html
- Writes: readable.html (specified path)
- Errors: stderr
- Exit code: 0 on success

```
flowdoc convert /path/to/doc.html -o /different/path/output.html
```
- Reads: /path/to/doc.html
- Writes: /different/path/output.html
- Errors: stderr
- Exit code: 0 on success

**stdin/stdout (pipe mode):**

```
cat recipe.html | flowdoc convert > readable.html
```
- Reads: stdin
- Writes: stdout
- Errors: stderr
- Exit code: 0 on success

```
flowdoc convert < recipe.html > readable.html
```
- Reads: stdin
- Writes: stdout
- Errors: stderr
- Exit code: 0 on success

**stdout/stderr contract:**

- **stdout:** Contains ONLY HTML output when successful (or nothing on failure)
- **stderr:** Contains ALL error messages, warnings, and diagnostics
- This contract enables safe piping: `flowdoc convert input.html 2>/dev/null`

### Output File Naming

**Default pattern:** `<basename>.flowdoc.html`

Examples:
- recipe.html -> recipe.flowdoc.html
- article.html -> article.flowdoc.html
- /path/to/doc.html -> /path/to/doc.flowdoc.html

Rationale:
- `.flowdoc.html` extension clearly identifies Flowdoc output
- Prevents accidental overwriting of original files
- Maintains file in same directory as input (predictable location)

**Overwrite behavior:**

If output file already exists: Silently overwrite without prompting.

Rationale: CLI tools should be automation-friendly. Interactive prompts break scripts.

**Warning:** This can cause data loss if output path is specified incorrectly. Users should:
- Use version control for important files
- Verify output paths before running conversion
- Use shell safeguards (`set -o noclobber`) if desired
- Test with dry-run on disposable files first

### Exit Codes

- `0` - Success (conversion completed, output written)
- `1` - Validation error (non-semantic HTML, missing required elements, parse failure)
- `2` - Render error (internal failure generating output)
- `3` - I/O error (cannot read input, cannot write output, permission denied)

**Exit code examples:**

```
flowdoc convert div-soup.html
# stderr: Error: Input HTML lacks semantic structure (no headings, paragraphs, or lists found)
# stdout: (empty)
# Exit code: 1
```

```
flowdoc convert recipe.html -o /root/output.html
# stderr: Error: Permission denied: /root/output.html
# stdout: (empty)
# Exit code: 3
```

```
flowdoc convert malformed.html
# If BeautifulSoup can repair it: Success (exit 0)
# If too broken to parse: Validation error (exit 1)
```

```
flowdoc convert missing.html
# stderr: Error: Input file not found: missing.html
# stdout: (empty)
# Exit code: 3
```

### Error Message Format

All error messages follow this format:

```
Error: <clear description of what went wrong>
```

Examples:
- `Error: Input file not found: recipe.html`
- `Error: Input HTML lacks semantic structure (no headings, paragraphs, or lists found)`
- `Error: Cannot write to output file: /protected/output.html (Permission denied)`
- `Error: Output directory does not exist: /nonexistent/path/`

No stack traces in production builds. Stack traces only appear with future `--debug` flag (v2).

### Determinism Guarantee

**Contract:**

Same input HTML + same Flowdoc version + same flags -> byte-identical output

**How enforced:**

- Pure core functions (no randomness, no timestamps, no external state)
- Stable library versions (BeautifulSoup4 + lxml deterministic when given same input)
- constants.py prevents magic numbers scattered in code
- Renderer produces HTML in fixed order (sorted dict keys, stable iteration)

**Testing determinism:**

Test validates determinism by:
1. Run: `flowdoc convert input.html -o output1.html`
2. Run: `flowdoc convert input.html -o output2.html`
3. Compare: `diff output1.html output2.html` must show no differences

This test runs in CI to catch non-deterministic behavior.

---

## DevOps Foundation

**v1 Goal:** Establish CI/CD foundations without over-engineering.

### What Gets Automated (v1)

**Continuous Integration:**
- Run test suite on every push and pull request
- Test against Python 3.12, 3.13 (matrix testing)
- Enforce 80% coverage minimum
- Run linting (ruff)
- Check code formatting

**Continuous Deployment:**
- Trigger on git tag (e.g., v1.0.0)
- Build and publish to PyPI
- Build standalone binaries (Windows, macOS, Linux)
- Create GitHub Release with binaries attached

**Dependency Management:**
- Automated dependency update PRs (Dependabot)
- Security vulnerability alerts
- Weekly checks for updates

### What's Deferred (Implementation Details)

Specific CI/CD implementation details (GitHub Actions YAML configuration, workflow files, PyInstaller build commands, Codecov setup) belong in separate documentation or CI.md, not architectural decisions.

v1 locks "what gets automated" as policy. Implementation mechanics can evolve without re-opening Step 3.5.

### Growth Path (v2 and Beyond)

**Future capabilities to add when needed:**

1. **Docker workflows** - If web preview service added
2. **Deployment workflows** - If hosting services (API, web interface)
3. **Monitoring/observability** - If production services launched
4. **Security scanning** - CodeQL, SAST when security posture expands
5. **Infrastructure as Code** - Terraform/CloudFormation if cloud resources needed
6. **Performance benchmarking** - Automated regression tests if speed becomes critical
7. **Multi-stage environments** - Dev/staging/production if service architecture emerges

v1 foundation enables growth without forcing premature complexity.

---

## Constraint Validation

All architectural constraints from the plan are validated:

### Determinism

**What enforces it:**
- Pure core layer (no I/O, no randomness, no timestamps, no external state)
- constants.py contains all magic numbers (prevents inline constants)
- Released versions use exact dependency pins (beautifulsoup4==4.x.y, lxml==5.x.y, nh3==0.x.y)
- Development can use compatible ranges; releases require exact pins
- Renderer generates HTML in fixed order (sorted keys, stable iteration)
- Golden test failures on dependency updates trigger intentional review and regeneration

**What threatens it:**
- None identified in current architecture
- Filesystem timestamps not used
- No random number generation
- No external API calls

**Validation:** ✅ Determinism guaranteed

### Separation

**Can renderer run without DOM?**

Yes. Renderer receives only Internal Document Model objects. Zero BeautifulSoup imports in renderer.py.

Test: renderer.py import check must not import BeautifulSoup or lxml.

**Can parser be tested independently?**

Yes. Model snapshot tests validate parser output (JSON serialization) without running renderer.

Test: test_parser.py produces model snapshots, compared without rendering HTML.

**Validation:** ✅ Clean separation enforced

### Embedding

**Is there a pure library API?**

Yes. Public API in `flowdoc/__init__.py`:

```
def convert(html: str, font: str = "system") -> str:
    """Convert HTML to readable format.
    
    Args:
        html: Input HTML string
        font: "system" or "opendyslexic"
    
    Returns:
        Self-contained readable HTML string
    """
```

No file I/O. No CLI dependencies. Pure function.

**Is CLI thin?**

Yes. CLI responsibilities:
- Argument parsing (argparse)
- File I/O (read input, write output)
- Error formatting (convert exceptions to user messages)
- Exit codes

All transformation logic in core/.

**Validation:** ✅ Embedding-friendly architecture

### Security

**Is sanitization delegated to mature library?**

Yes. nh3 (Rust ammonia bindings):
- Actively maintained (Oct 2025 latest release)
- Allowlist-based (secure by design)
- Battle-tested Rust backend
- Fast and reliable

**Are URL policies explicit?**

Yes. nh3 configured with explicit URL scheme allowlist:
- Allow: `http`, `https`
- Block: `javascript`, `data`, all others
- Configured in sanitizer.py

**Validation:** ✅ Security requirements met

### Scope Discipline

**No heuristic scraping?**

Correct. Content selection is deterministic rule:
1. If `<main>` exists, use it
2. Else if `<article>` exists, use first one
3. Else use `<body>`

No ML, no scoring, no heuristics. Fixed rule.

**No layout preservation?**

Correct. "Readability over fidelity" principle enforced.

Renderer generates fixed typography from constants.py. Original CSS completely discarded.

**No feature creep?**

Correct. Deferred decisions documented:
- `validate` command deferred to v2
- `info` command deferred to v2
- `--report json` deferred to v2
- Additional fonts (Lexend, Atkinson) deferred to v2

Only minimal v1 CLI shipped.

**Validation:** ✅ Scope discipline maintained

---

## Deferred Decisions

**Note on architectural exploration:**

Earlier architectural exploration (architecture_exploration.md) discussed multi-command CLI design (convert, validate, info) as alignment with Unix philosophy. This exploration informed the clean separation between core and CLI layers but did not commit those commands for v1. v1 intentionally ships a single command (`convert`) for scope control. Additional commands represent architectural headroom, not locked features.

**Decisions explicitly NOT made for v1, with rationale for deferral and revisit triggers:**

### `validate` command (Deferred to v2)

**What it would do:**
Check if HTML has semantic structure without converting it. Exit 0 if valid, 1 if invalid. Print validation report.

**Why deferred:**
The `convert` command already validates input and produces clear error messages on failure. A separate `validate` command would duplicate this logic. No user has requested "check without converting" workflow yet.

**Revisit trigger:**
Add when users request ability to check files in batch without generating output. Use case: "validate 100 files, convert only the valid ones."

### `info` command (Deferred to v2)

**What it would do:**
Preview what Flowdoc would do without converting. Print detected title, section count, element counts, degradation summary.

**Why deferred:**
Nice-to-have preview functionality but not essential for core use case. Adds complexity (duplicate parsing logic) without proven user value.

**Revisit trigger:**
Add when users request "what will happen?" dry-run mode. Use case: "I want to see what tables will be dropped before committing to conversion."

### `--report json` flag (Deferred to v2)

**What it would do:**
Output machine-readable diagnostics (detected title, sections, degradations, warnings) as JSON alongside or instead of HTML.

**Why deferred:**
Mentioned in architecture docs for downstream tool integration, but no concrete requirement yet. Would enable "convert + extract metadata" workflow.

**Revisit trigger:**
Add when downstream tools request structured metadata output. Use case: "I'm building a recipe manager that needs to extract ingredient lists after Flowdoc conversion."

### stdin default for output (Rejected, not deferred)

**Proposed behavior:**
If `-o` not specified, write to stdout instead of `<input>.flowdoc.html`.

**Why rejected:**
Would clutter stdout on accidental runs. File default (`<input>.flowdoc.html`) is safer and more intuitive. Users who want stdout can explicitly use `-o -` or redirect via pipe.

**Will not revisit:** This decision is permanent for v1, not deferred.

### Additional font options beyond OpenDyslexic (Deferred to v2)

**Candidate fonts:**
- Lexend (variable spacing for readability)
- Atkinson Hyperlegible (low-vision optimized)
- Dyslexie (commercial, requires licensing)

**Why deferred:**
Binary font choice (system vs OpenDyslexic) is sufficient for v1 validation. Adding multiple fonts increases:
- Testing surface (test each font embedding)
- Distribution size (more fonts to bundle)
- User confusion (which font should I choose?)

**Revisit trigger:**
Add when users request specific fonts based on preference or research. Must include user testing to validate each additional font improves outcomes.

---

**Step 3.5 is now complete and locked. No implementation of Steps 4-7 should begin until this section is reviewed and approved.**
