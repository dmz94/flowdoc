# Flowdoc v1 - Development Session Summary

**Date:** February 23, 2026
**Status:** Core conversion pipeline feature-complete for v1 scope. Input validation complete. Fixture corpus complete.
**Release Readiness:** NOT release-ready. Required before release: golden file tests, determinism test, OpenDyslexic font embedding, and user validation with dyslexic readers.
**Test Status:** 90 tests passing locally

## What We Built

Complete end-to-end HTML conversion pipeline:

### Core Modules (flowdoc/core/)
1. **model.py** - Document model classes (Document, Section, Heading, Block types, Inline types including LineBreak)
2. **constants.py** - Typography values from BDA guidelines
3. **sanitizer.py** - nh3 wrapper with security allowlist (includes br tag)
4. **content_selector.py** - Deterministic main content selection (main -> article -> body)
5. **degradation.py** - Placeholder generation for tables/images/forms
6. **parser.py** - DOM to model conversion (recursive, handles nesting, collapse_whitespace helper). Includes ValidationError and validate_structure().
7. **renderer.py** - Model to readable HTML with inline CSS

### CLI Layer (flowdoc/cli/, flowdoc/io/)
1. **main.py** - Argument parsing, orchestration, exit codes. Handles ValidationError with exit code 1.
2. **reader.py** - File/stdin input
3. **writer.py** - File/stdout output

### Dev Tools (project root)
1. **preview_server.py** - Flask server, two routes: GET / serves preview.html, POST /convert runs pipeline
2. **preview.html** - Drag-drop UI with iframe and OpenDyslexic toggle
3. **fetch_fixtures.py** - Dev tool to fetch HTML fixture files from the web. Run with: python fetch_fixtures.py

### Test Coverage
- 90 tests passing (unit + integration)
- Tests organized by module
- Includes test_validation.py (9 tests)
- Integration test with real HTML fixture (simple_article.html)
- All tests run with: `pytest -v`

## What Works Right Now

**The core conversion pipeline is functional for in-scope semantic HTML:**

```
# In VS Code terminal with venv active:
python -m flowdoc.cli.main tests/fixtures/input/simple_article.html
# Creates: tests/fixtures/input/simple_article.flowdoc.html
# Open in browser - renders with readable typography
```

**Preview tool:**

```
python preview_server.py
# Open http://localhost:5000
# Drag any HTML file onto the drop zone
```

**Pipeline flow:**
1. Read HTML (file or stdin)
2. Sanitize with nh3 (strip scripts, dangerous attributes)
3. Parse to BeautifulSoup DOM
4. Select main content (main -> article -> body)
5. Validate structure (requires h1-h3 and p/ul/ol content - raises ValidationError if missing)
6. Build internal model (sections with headings and blocks)
7. Render to self-contained HTML with inline CSS
8. Write output (file or stdout)

## Fixture Corpus

11 HTML fixtures in tests/fixtures/input/ (10 GOOD, 1 BAD):

GOOD fixtures (pass validation):
- simple_article.html - hand-crafted test fixture
- wikipedia_dyslexia.html - encyclopedia article
- wikipedia_photosynthesis.html - science article
- nhs_dyslexia.html - health/medical page
- clevelandclinic_dyslexia.html - health/medical page
- bbcgoodfood_carbonara.html - recipe
- wikihow_ride_a_bike.html - how-to guide
- mdn_html_elements.html - technical documentation
- gutenberg_pride_prejudice.html - long-form book
- readability_001_tech_blog.html - tech blog article

BAD fixtures (fail validation intentionally):
- paulgraham_identity.html - no semantic structure (font/table layout, no h1-h3)

## Known Limitations (Intentional for v1)

1. **OpenDyslexic font:** Placeholder empty in constants.py - needs base64 embedding
2. **Golden file tests:** Not yet implemented
3. **Determinism test:** Not yet implemented

## What's Left for v1 Completion

### 1. Golden File Tests (REQUIRED)
- For each fixture, store expected output in tests/fixtures/expected/
- Test: input -> convert -> compare bytes with expected
- Catches unintended changes to output
- Location: Add test_golden_files.py
- Note: only run against GOOD fixtures, not paulgraham_identity.html

### 2. Determinism Test (REQUIRED)
- Same input + same flags -> byte-identical output
- Test: run conversion twice, compare bytes
- Location: Add to test_integration.py

### 3. OpenDyslexic Font Embedding (REQUIRED for --font flag)
- Download OpenDyslexic-Regular.woff2 from https://opendyslexic.org/
- Convert to base64: base64 -w 0 OpenDyslexic-Regular.woff2
- Replace OPENDYSLEXIC_BASE64 placeholder in constants.py
- Test: python -m flowdoc.cli.main input.html --font opendyslexic
- Verify @font-face appears in output


## Policy Decisions (Intentional - Do Not Change Without Discussion)

1. **Validation rule is intentional v1 product requirement:** Requiring h1-h3 and p/ul/ol is a deliberate policy decision, not a temporary heuristic. Flowdoc is designed for semantic HTML. Do not relax this without explicit decision.
2. **CLI failure contract:** On validation failure - exit code 1, error message to stderr, no output file written.
3. **Golden file process:** Run conversion against each GOOD fixture, manually verify output looks correct, save as expected file. Regenerate expected files only when output changes are intentional.
4. **Determinism scope:** Byte-identical output expected within same Python version (3.12.x) and pinned dependency versions. Cross-environment determinism is not a v1 requirement.
5. **--font opendyslexic before embedding:** Currently outputs HTML without the font (falls back to system fonts). This is acceptable until font is embedded - do not make it a hard failure.
## What's NOT in v1 Scope

These are explicitly deferred (see SCOPE.md):
- PDF input
- DOCX input/output
- Native PDF output
- GUI or web interface
- Batch processing features
- Additional fonts beyond OpenDyslexic
- Heuristic/scraping for non-semantic HTML
- Content transformation (readability improvements)

## Development Environment

- Python 3.12.9
- VS Code with Python extension
- Virtual environment at project root (venv/)
- Windows 11, Command Prompt terminal (not PowerShell)
- GitHub Desktop for version control
- Dependencies: beautifulsoup4, lxml, nh3, pytest, flask, requests
- GitHub repo linked to Claude project via GitHub integration

## Key Decisions Made

1. **Incremental development:** Build module by module with tests
2. **For documentation files:** Ask user each time - code block or whole file download?
3. **For source code files:** Always use code blocks for copy/paste into VS Code.
4. **Step-by-step process:** Explain -> Strategize -> Plan -> Code -> Test
5. **Locked specs:** decisions.md is authoritative, no scope changes during implementation
6. **Real testing:** Validate with actual HTML files and user feedback before v2
7. **Preview tool testing:** Manual only - no automated tests for preview_server.py
8. **fetch_fixtures.py uses requests library** - listed in dev dependencies in pyproject.toml
9. **paulgraham_identity.html kept as bad fixture** - intentional validation failure test case

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
|   |   +-- content_selector.py
|   |   +-- degradation.py
|   |   +-- parser.py
|   |   +-- renderer.py
|   +-- cli/
|   |   +-- __init__.py
|   |   +-- main.py
|   +-- io/
|       +-- __init__.py
|       +-- reader.py
|       +-- writer.py
+-- tests/
|   +-- fixtures/
|   |   +-- input/          (11 files - see Fixture Corpus above)
|   |   +-- expected/       (empty - for golden files)
|   |   +-- snapshots/      (empty - reserved)
|   +-- test_model.py
|   +-- test_constants.py
|   +-- test_sanitizer.py
|   +-- test_content_selector.py
|   +-- test_degradation.py
|   +-- test_parser_title.py
|   +-- test_parser_sections.py
|   +-- test_parser_blocks.py
|   +-- test_parser_inlines.py
|   +-- test_renderer_css.py
|   +-- test_renderer_blocks.py
|   +-- test_renderer_inlines.py
|   +-- test_cli_basic.py
|   +-- test_validation.py
|   +-- test_integration.py
+-- docs/
|   +-- decisions.md (authoritative spec)
|   +-- ARCHITECTURE.md
|   +-- research_typography_guidelines.md
|   +-- 0_0_FLOWDOC_V1_PLAN.md
|   +-- architecture_exploration.md
+-- fetch_fixtures.py  (dev tool - fetch HTML fixtures from web)
+-- preview_server.py  (dev tool - Flask server)
+-- preview.html       (dev tool - drag-drop UI)
+-- SCOPE.md
+-- ABOUT.md
+-- README.md
+-- pyproject.toml
+-- .editorconfig
+-- .gitignore
```

## Next Steps

1. **Implement golden file tests** - Next priority
2. **Add determinism test** - Add to test_integration.py
3. **Embed OpenDyslexic font** - Complete the --font flag

## Testing Instructions for Next Session

All tests must pass before v1 release:

```
# Activate venv
venv\Scripts\activate

# Run all tests
pytest -v

# Test CLI manually
python -m flowdoc.cli.main tests/fixtures/input/simple_article.html

# Open output in browser
start tests/fixtures/input/simple_article.flowdoc.html

# Run preview tool
python preview_server.py
```

**Expected:** 90 tests passing

## Communication Rules - CRITICAL

These rules MUST be followed in every response:

1. **Four-step process:** Purpose -> Strategy -> Plan -> Code. Wait for "yes" after EACH step before proceeding. No exceptions.
2. **One file at a time:** Show one file, wait for "done" before showing next file.
3. **Code blocks contain code and commands ONLY:** Never put file names, instructions, or explanations inside code blocks. These go outside the block.
4. **Always read files first:** Use project_knowledge_search for .py files, view tool for .md files. State "Reading X now" before every call. No exceptions.
5. **Verify function signatures:** Never assume parameter names. Read the actual source file first.
6. **Complete changes across files:** When a change spans multiple files, read ALL affected files first, then list every change needed before touching any of them.
7. **New dependencies:** Never introduce new dependencies without checking pyproject.toml first. Call out pip install command BEFORE showing the run command.
8. **File locations:** Always tell the user exactly where to save each file.
9. **Code blocks must use 4 spaces for indentation, not tabs:** This ensures pasting into VS Code works correctly every time.
10. **No em dashes or smart quotes in code blocks:** ASCII only (straight quotes, hyphens).
11. **Commit guidance:** Provide summary and description for GitHub Desktop after each completed task.
12. **Documentation files output:** Ask the user each time - code block or whole file download? For source code files, always use code blocks.
14. **Never guess:** Not at URLs, parameter names, file contents, or anything verifiable. Look it up first.

## Critical Files to Read at Start of Every Session

1. /mnt/project/SESSION_SUMMARY.md - Current state (this file) - use view tool
2. /mnt/project/decisions.md - Implementation contracts - use view tool
3. /mnt/project/SCOPE.md - v1 boundaries - use view tool
4. /mnt/project/ARCHITECTURE.md - Tech stack and structure - use view tool

## How to Access Source Files

The view tool only reaches root-level .md files at /mnt/project/.
Python source files and test files are NOT accessible via the view tool.

Use project_knowledge_search to read any .py file before modifying it.
State "Reading X now" before each search. This replaces the view tool
for all source files.

Limitation: search returns chunks, not whole files. Use multiple searches
with different keywords if a file is long.

Files under flowdoc/core/: model.py, constants.py, sanitizer.py,
content_selector.py, degradation.py, parser.py, renderer.py

Files under flowdoc/cli/: main.py
Files under flowdoc/io/: reader.py, writer.py
Dev tools (project root): preview_server.py, preview.html, fetch_fixtures.py

## Success Criteria (from SCOPE.md)

v1 is complete when:
1. OK - Accepts semantic HTML inputs within scope
2. OK - Produces self-contained readable HTML
3. PENDING - Output measurably better for dyslexic readers (needs user testing)
4. PENDING - Works on browsers, mobile, print (manually verified in limited testing only)
5. PENDING - Failure modes predictable and clear (validation implemented but not yet tested against full fixture corpus)
6. OK - Inline elements render correctly
7. OK - Unsupported elements degrade deterministically
8. OK - Sanitization prevents active-content issues

Missing pieces: golden file tests, determinism test, font embedding, user testing (#3).
