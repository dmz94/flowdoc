# Flowdoc v1 - Development Session Summary

**Date:** February 26, 2026
**Status:** Dual-pipeline architecture implemented and visually validated. 112 tests passing.
**Release Readiness:** NOT release-ready. Required before release: Trafilatura audit, fixture corpus refresh, golden file tests, determinism test, OpenDyslexic font embedding, and user validation.
**Test Status:** 112 tests passing locally

## What We Built

Complete end-to-end HTML conversion pipeline with dual-mode routing:

### Core Modules (flowdoc/core/)
1. **model.py** - Document model classes (Document, Section, Heading, Block types, Inline types including LineBreak)
2. **constants.py** - Typography values from BDA guidelines
3. **sanitizer.py** - nh3 wrapper with security allowlist (includes br tag)
4. **content_selector.py** - detect_mode() for auto-routing between transform and extract pipelines. Scoring: scripts >= 10 OR nav >= 5 -> extract, else transform.
5. **degradation.py** - Placeholder generation for tables/images/forms
6. **parser.py** - DOM to model conversion. Includes extract_with_trafilatura() for boilerplate removal and parse() which accepts optional original_title parameter.
7. **renderer.py** - Model to readable HTML with inline CSS

### CLI Layer (flowdoc/cli/, flowdoc/io/)
1. **main.py** - Argument parsing, orchestration, exit codes. --mode transform|extract|auto flag (default: auto). --verbose flag.
2. **reader.py** - File/stdin input
3. **writer.py** - File/stdout output

### Dev Tools (project root)
1. **preview_server.py** - Flask server with mode detection and routing. GET / serves preview.html, POST /convert runs pipeline. Adds HTML comment showing which mode was used.
2. **preview.html** - Drag-drop UI with iframe and OpenDyslexic toggle
3. **fetch_fixtures.py** - Dev tool to fetch HTML fixture files from the web
4. **convert_fixtures.py** - Dev tool to batch convert all fixtures. Run with: python convert_fixtures.py. Creates .flowdoc.html files alongside inputs for visual inspection.

### Test Coverage
- 112 tests passing
- test_content_selector.py - 8 new routing tests
- test_cli_basic.py - 4 new mode flag tests
- test_extract_mode.py - 9 new tests documenting extract mode behavior and known limitations
- All tests run with: `pytest -v`

## Dual Pipeline Architecture

### The Core Decision
Two distinct use cases require different handling:
- **Transform mode**: Developer-generated clean semantic HTML. Fidelity-first. No Trafilatura. Preserves all structure exactly.
- **Extract mode**: Real-world web pages with boilerplate. Runs Trafilatura first to strip nav/ads/footer, then parses cleaned HTML.

### Auto-Detection Logic (detect_mode in content_selector.py)
Score-based routing derived from analysis of all fixtures:
- Count nav/header/footer/aside tags and script tags
- scripts >= 10 OR nav >= 5 -> extract
- else -> transform
- Default to transform when ambiguous

### Pipeline Flow (auto mode)
1. Read HTML
2. detect_mode() -> transform or extract
3. If extract: capture original title, run extract_with_trafilatura()
4. Sanitize with nh3
5. Parse to BeautifulSoup DOM
6. Validate structure (requires h1-h3 and p/ul/ol)
7. Build internal model
8. Render to self-contained HTML
9. Write output

### Known Extract Mode Limitations (documented, not bugs)
See docs/known-limitations.md for full reference.

## Visual Validation Results (February 25, 2026)

Ran convert_fixtures.py against all fixtures. Results:

| Fixture | Mode | Result | Notes |
|---|---|---|---|
| simple_article.html | transform | EXCELLENT | Perfect baseline |
| nhs_dyslexia.html | extract | GOOD | Clean article, title whitespace fixed |
| clevelandclinic_dyslexia.html | extract | GOOD | Main content clean, trailing boilerplate leaked |
| readability_001_tech_blog.html | extract | GOOD | Nav gone, inline code fragmentation issue |
| wikihow_ride_a_bike.html | extract | ACCEPTABLE | Content readable, duplicate list items, reference noise |
| wikipedia_photosynthesis.html | extract | POOR | Lead section badly fragmented by dense links |
| wikipedia_dyslexia.html | extract | NOT TESTED | Expected same fragmentation as photosynthesis |
| mdn_html_elements.html | extract | SCOPE BOUNDARY | Reference table page - content IS the tables |
| bbcgoodfood_carbonara.html | extract | VALIDATION FAIL | Trafilatura strips headings, no h1-h3 survives |
| paulgraham_identity.html | extract | VALIDATION FAIL | Intentional bad fixture |

## Backlog of Issues Found in Visual Validation

### Priority 1 - Fixable bugs
1. **FIXED - Empty paragraphs** - `<p></p>` appearing in output. Returns None from parse_block() when no inline content.
2. **FIXED - Title newline** - NHS title had `\n` in it. Added re.sub whitespace normalization in extract_title().
3. **FIXED - "Advertisement" paragraphs** - Cleveland Clinic ad markers. Added regex filter in extract_with_trafilatura().
4. **OPEN - Trailing boilerplate** - Cleveland Clinic footer/signup/references leaking through. May be addressable with favor_precision=True - pending Trafilatura audit.

### Priority 2 - Known Trafilatura limitations (pending audit)
5. **OPEN - Inline code becoming pre blocks** - `<code>` inside `<p>` becoming standalone `<pre>` in extract mode.
6. **OPEN - Missing spaces around inline elements** - "data-cover attribute" losing space.
7. **OPEN - Duplicate list items** - WikiHow nested list items appearing twice. deduplicate=True unlikely to help for single-page use - confirmed in audit.
8. **OPEN - Wikipedia lead section fragmentation** - Dense link structures fragment into single-phrase paragraphs.

### Priority 3 - Accessibility concern
9. **CLOSED - Italic overuse** - Gutenberg fixture removed. No remaining fixtures exhibit wall-of-italic problem.

### Priority 4 - Scope boundaries (do not fix in v1)
10. **MDN reference tables** - Content lives in tables which we strip. Wrong input type for Flowdoc.
11. **BBC Good Food validation failure** - Recipe site structure strips all headings. Out of scope.
12. **Wikipedia dense links** - Structural issue with Wikipedia's HTML format. Defer to v2.

## What Works Right Now

**Batch visual testing:**
```
python convert_fixtures.py
```
Creates .flowdoc.html files in tests/fixtures/input/ for browser inspection.

**Single file conversion:**
```
python -m flowdoc.cli.main tests/fixtures/input/simple_article.html
```

**Mode flag:**
```
python -m flowdoc.cli.main --mode transform input.html
python -m flowdoc.cli.main --mode extract input.html
python -m flowdoc.cli.main --mode auto input.html
```

**Preview tool:**
```
python preview_server.py
# Open http://localhost:5000
# Drag any HTML file onto the drop zone
# View source to see <!-- flowdoc mode: transform|extract --> comment
```

## Fixture Corpus

10 HTML fixtures in tests/fixtures/input/ (8 GOOD, 2 BAD):

GOOD fixtures (pass validation):
- simple_article.html - hand-crafted test fixture (transform mode)
- wikipedia_dyslexia.html - encyclopedia article (extract mode)
- wikipedia_photosynthesis.html - science article (extract mode)
- nhs_dyslexia.html - health/medical page (extract mode)
- clevelandclinic_dyslexia.html - health/medical page (extract mode)
- wikihow_ride_a_bike.html - how-to guide (extract mode)
- mdn_html_elements.html - technical documentation (extract mode)
- readability_001_tech_blog.html - tech blog article (extract mode)

BAD fixtures (fail validation):
- paulgraham_identity.html - no semantic structure (intentional)
- bbcgoodfood_carbonara.html - headings stripped by Trafilatura (known limitation)

Note: gutenberg_pride_prejudice.html removed - 19th century book scan, not representative of target use case.

## Known Limitations (Intentional for v1)

1. **OpenDyslexic font:** Placeholder empty in constants.py - needs base64 embedding
2. **Golden file tests:** Not yet implemented - blocked on Trafilatura audit
3. **Determinism test:** Not yet implemented
4. **Extract mode is lossy:** Documented limitation - inline formatting, spacing, some structure lost
5. **Trafilatura usage audit pending:** Current extract() call parameters have not been fully audited against library capabilities. Do not implement golden files until audit is complete.

## What's Left for v1 Completion

### 1. Trafilatura Audit (NEXT PRIORITY - blocks everything else)
Read Trafilatura source via project knowledge search and audit extract_with_trafilatura() in parser.py.
Key questions:
- Is include_formatting=True correct for output_format="html"?
- Should we pass include_comments=False and include_tables=False?
- Should we pass favor_precision=True?
- Can prune_xpath address trailing boilerplate?
- Should we switch to the Extractor class?

### 2. Fixture Corpus Refresh (after audit)
Current corpus is thin and unrepresentative. Need to add:
- News article (clean semantic structure)
- Long-form blog post
- Government/official page
- Simple how-to (non-WikiHow format)

### 3. Golden File Tests (after audit and fixture refresh)
- For each GOOD fixture, store expected output in tests/fixtures/expected/
- Test: input -> convert -> compare bytes with expected
- Location: Add test_golden_files.py

### 4. Determinism Test
- Same input + same flags -> byte-identical output
- Location: Add to test_integration.py

### 5. OpenDyslexic Font Embedding (REQUIRED for --font flag)
- Download OpenDyslexic-Regular.woff2 from https://opendyslexic.org/
- Convert to base64: base64 -w 0 OpenDyslexic-Regular.woff2
- Replace OPENDYSLEXIC_BASE64 placeholder in constants.py

## Policy Decisions (Intentional - Do Not Change Without Discussion)

1. **Validation rule is intentional v1 product requirement:** Requiring h1-h3 and p/ul/ol is a deliberate policy decision. Do not relax without explicit decision.
2. **CLI failure contract:** On validation failure - exit code 1, error message to stderr, no output file written.
3. **Extract mode is lossy by design:** Documented limitation for v1. Transform mode is fidelity-first.
4. **Auto-detection thresholds are evidence-based:** scripts >= 10 OR nav >= 5 derived from fixture corpus analysis. Do not change without re-running analysis.
5. **Golden file process:** Run conversion, manually verify output, save as expected. Regenerate only when output changes are intentional.
6. **Determinism scope:** Byte-identical within same Python version (3.12.x) and pinned dependencies only.

## What's NOT in v1 Scope

- PDF input
- DOCX input/output
- Native PDF output
- GUI or web interface
- Batch processing features
- Additional fonts beyond OpenDyslexic
- Content transformation (readability improvements)

## Development Environment

- Python 3.12.9
- VS Code with Python extension
- Virtual environment at project root (venv/)
- Windows 11, Command Prompt terminal (not PowerShell)
- GitHub Desktop for version control
- Dependencies: beautifulsoup4, lxml, nh3, pytest, flask, requests, trafilatura
- GitHub repo linked to Claude project via GitHub integration
- Trafilatura repo (adbar/trafilatura) also linked to Claude project for source reading

## Key Decisions Made

1. **Dual pipeline architecture:** transform vs extract modes with auto-detection
2. **Trafilatura used for extraction only:** Not for parsing - extract_with_trafilatura() returns HTML, parse() handles DOM
3. **Evidence-based thresholds:** Auto-detection thresholds derived from fixture corpus analysis, not theory
4. **ChatGPT consulted for architecture:** Independent validation of dual pipeline decision (GPT-5.2 Thinking mode agreed)
5. **Extract mode documented as lossy:** Honest v1 choice - accept limitations, document them
6. **Incremental development:** Build module by module with tests
7. **Always read files first:** Use project_knowledge_search for .py files, view tool for .md files
8. **Step-by-step process:** Purpose -> Strategy -> Plan -> Code. Wait for approval after each step.
9. **One file at a time:** Show one file, wait for "done" before showing next file.
10. **Commit between tasks:** Clean checkpoint after each completed task
11. **Trafilatura audit before golden files:** Do not lock in output until extract() call is confirmed optimal

## File Organization

```
flowdoc/
+-- flowdoc/
|   +-- __init__.py
|   +-- core/
|   |   +-- __init__.py
|   |   +-- model.py
|   |   +-- constants.py
|   |   +-- sanitizer.py
|   |   +-- content_selector.py  (detect_mode() - auto-routing)
|   |   +-- degradation.py
|   |   +-- parser.py            (extract_with_trafilatura(), parse())
|   |   +-- renderer.py
|   +-- cli/
|   |   +-- __init__.py
|   |   +-- main.py              (--mode transform|extract|auto)
|   +-- io/
|       +-- __init__.py
|       +-- reader.py
|       +-- writer.py
+-- tests/
|   +-- fixtures/
|   |   +-- input/          (10 files - see Fixture Corpus above)
|   |   +-- expected/       (empty - for golden files)
|   |   +-- snapshots/      (empty - reserved)
|   +-- test_model.py
|   +-- test_constants.py
|   +-- test_sanitizer.py
|   +-- test_content_selector.py  (includes detect_mode tests)
|   +-- test_degradation.py
|   +-- test_parser_title.py
|   +-- test_parser_sections.py
|   +-- test_parser_blocks.py
|   +-- test_parser_inlines.py
|   +-- test_renderer_css.py
|   +-- test_renderer_blocks.py
|   +-- test_renderer_inlines.py
|   +-- test_cli_basic.py         (includes mode flag tests)
|   +-- test_validation.py
|   +-- test_integration.py
|   +-- test_extract_mode.py      (extract mode behavior and known limitations)
+-- docs/
|   +-- decisions.md (authoritative spec)
|   +-- architecture.md
|   +-- research_typography_guidelines.md
|   +-- flowdoc-v1-plan.md
|   +-- architecture-exploration.md
|   +-- known-limitations.md     (Trafilatura limitations reference for v2)
|   +-- session-summary.md (this file)
+-- convert_fixtures.py  (dev tool - batch convert all fixtures)
+-- fetch_fixtures.py    (dev tool - fetch HTML fixtures from web)
+-- preview_server.py    (dev tool - Flask server with mode routing)
+-- preview.html         (dev tool - drag-drop UI)
+-- SCOPE.md
+-- ABOUT.md
+-- README.md
+-- pyproject.toml
+-- .editorconfig
+-- .gitignore
```

## Next Steps

1. **Trafilatura audit** - read source via project knowledge, audit extract_with_trafilatura() call in parser.py
2. **Fixture corpus refresh** - add representative real-world fixtures (news article, long-form blog, government page, simple how-to)
3. **Golden file tests** - after audit and fixture refresh confirm output is stable
4. **Determinism test** - add to test_integration.py
5. **OpenDyslexic font embedding** - complete the --font flag

## Testing Instructions

```
venv\Scripts\activate
pytest -v
python convert_fixtures.py
python preview_server.py
```

Expected: 112 tests passing

## Communication Rules - CRITICAL

These rules MUST be followed in every response:

1. **Read project files first:** At the start of every session read session-summary.md, decisions.md, SCOPE.md, and architecture.md using the view tool BEFORE doing anything else. State which file you are reading. No exceptions.
2. **Four-step process:** Purpose -> Strategy -> Plan -> Code. Wait for "yes" after EACH step before proceeding. No exceptions.
3. **One file at a time:** Show one file, wait for "done" before showing next file.
4. **Always read source files before modifying:** Use project_knowledge_search for .py files. State "Reading X now" before every call. Never assume file contents.
5. **Verify function signatures:** Never assume parameter names. Read the actual source file first.
6. **Complete changes across files:** Read ALL affected files first, then list every change needed before touching any of them.
7. **New dependencies:** Never introduce without checking pyproject.toml first. Call out pip install BEFORE run command.
8. **File locations:** Always tell the user exactly where to save each file.
9. **4-space indentation in code blocks, not tabs.**
10. **ASCII only in code blocks:** No em dashes, smart quotes, or Unicode.
11. **Commit guidance:** Provide summary and description for GitHub Desktop after each completed task.
12. **Never guess:** Not at URLs, parameter names, file contents, or anything verifiable. Look it up first.
13. **No excessive formatting:** No unnecessary bold, headers, or bullet points in responses.

## Critical Files to Read at Start of Every Session

1. /mnt/project/docs/session-summary.md - Current state (this file) - use view tool
2. /mnt/project/decisions.md - Implementation contracts - use view tool
3. /mnt/project/SCOPE.md - v1 boundaries - use view tool
4. /mnt/project/docs/architecture.md - Tech stack and structure - use view tool

## How to Access Source Files

The view tool only reaches root-level .md files at /mnt/project/.
Python source files and test files are NOT accessible via the view tool.

Use project_knowledge_search to read any .py file before modifying it.
State "Reading X now" before each search.

Limitation: search returns chunks, not whole files. Use multiple searches
with different keywords if a file is long.

Files under flowdoc/core/: model.py, constants.py, sanitizer.py,
content_selector.py, degradation.py, parser.py, renderer.py

Files under flowdoc/cli/: main.py
Files under flowdoc/io/: reader.py, writer.py
Dev tools (project root): preview_server.py, preview.html, fetch_fixtures.py,
convert_fixtures.py

## Trafilatura Source Access

The Trafilatura GitHub repo (adbar/trafilatura) is connected to this Claude project.
Use project_knowledge_search to read Trafilatura source files directly.
Key files: trafilatura/core.py, trafilatura/settings.py, trafilatura/htmlprocessing.py,
trafilatura/settings.cfg, docs/usage-python.rst, docs/settings.rst, docs/deduplication.rst

## Success Criteria (from SCOPE.md)

v1 is complete when:
1. OK - Accepts semantic HTML inputs within scope
2. OK - Produces self-contained readable HTML
3. PENDING - Output measurably better for dyslexic readers (needs user testing)
4. PENDING - Works on browsers, mobile, print (manually verified in limited testing only)
5. PENDING - Failure modes predictable and clear (validation implemented, fixture corpus mostly clean)
6. OK - Inline elements render correctly
7. OK - Unsupported elements degrade deterministically
8. OK - Sanitization prevents active-content issues

Missing pieces: Trafilatura audit, fixture corpus refresh, golden file tests, determinism test, font embedding, user testing.
