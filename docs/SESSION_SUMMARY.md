# Flowdoc v1 - Development Session Summary

**Date:** February 23, 2026
**Status:** Core pipeline complete and tested. Task 6 (drag-drop preview) complete.
**Test Status:** 81 tests passing locally

## What We Built

Complete end-to-end HTML conversion pipeline:

### Core Modules (flowdoc/core/)
1. **model.py** - Document model classes (Document, Section, Heading, Block types, Inline types including LineBreak)
2. **constants.py** - Typography values from BDA guidelines
3. **sanitizer.py** - nh3 wrapper with security allowlist (includes br tag)
4. **content_selector.py** - Deterministic main content selection (main -> article -> body)
5. **degradation.py** - Placeholder generation for tables/images/forms
6. **parser.py** - DOM to model conversion (recursive, handles nesting, collapse_whitespace helper)
7. **renderer.py** - Model to readable HTML with inline CSS

### CLI Layer (flowdoc/cli/, flowdoc/io/)
1. **main.py** - Argument parsing, orchestration, exit codes
2. **reader.py** - File/stdin input
3. **writer.py** - File/stdout output

### Dev Tools (project root)
1. **preview_server.py** - Flask server, two routes: GET / serves preview.html, POST /convert runs pipeline
2. **preview.html** - Drag-drop UI with iframe and OpenDyslexic toggle

### Test Coverage
- 81 tests passing (unit + integration)
- Tests organized by module
- Integration test with real HTML fixture (simple_article.html)
- All tests run with: `pytest -v`

## What Works Right Now

**The system is fully functional:**

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
5. Build internal model (sections with headings and blocks)
6. Render to self-contained HTML with inline CSS
7. Write output (file or stdout)

## Bugs Fixed in February 23 Session

1. **Inline whitespace** - collapse_whitespace() added to parser.py. Preserves boundary spaces between text and inline elements (em, strong, etc.)
2. **br tag handling** - LineBreak inline type added to model.py. Parser returns LineBreak() for br tags. Renderer emits br element.
3. **br stripped by sanitizer** - Added "br" to ALLOWED_TAGS in sanitizer.py

## Known Limitations (Intentional for v1)

1. **OpenDyslexic font:** Placeholder empty in constants.py - needs base64 embedding
2. **Input validation:** Doesn't yet reject non-semantic HTML
3. **Fixture corpus:** Only one test fixture (simple_article.html)
4. **Golden file tests:** Not yet implemented
5. **Determinism test:** Not yet implemented

## What's Left for v1 Completion

### 1. Input Validation (REQUIRED)
- Implement validation from decisions.md section 3
- Reject if no h1-h3 headings found
- Reject if no p/ul/ol content found
- Error message: "Input HTML lacks semantic structure (requires at least one h1-h3 and body content in p/ul/ol)."
- Exit code: 1
- **Location:** Add validation in parser.py after model building
- **Test:** Add test_validation.py

### 2. Fixture Corpus (REQUIRED for confidence)
- Create 5-10 real HTML files in tests/fixtures/input/
- Sources: recipe sites, articles, technical docs, Wikipedia exports
- Ensure variety: nested lists, blockquotes, links, code blocks
- **Goal:** Validate parser handles real-world HTML, not just hand-crafted tests

### 3. Golden File Tests (REQUIRED)
- For each fixture, store expected output in tests/fixtures/expected/
- Test: input -> convert -> compare bytes with expected
- Catches unintended changes to output
- **Location:** Add test_golden_files.py

### 4. Determinism Test (REQUIRED)
- Same input + same flags -> byte-identical output
- Test: run conversion twice, compare bytes
- **Location:** Add to test_integration.py

### 5. OpenDyslexic Font Embedding (REQUIRED for --font flag)
- Download OpenDyslexic-Regular.woff2 from https://opendyslexic.org/
- Convert to base64: base64 -w 0 OpenDyslexic-Regular.woff2
- Replace OPENDYSLEXIC_BASE64 placeholder in constants.py
- Test: python -m flowdoc.cli.main input.html --font opendyslexic
- Verify @font-face appears in output

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
- Dependencies: beautifulsoup4, lxml, nh3, pytest, flask
- GitHub linked to Claude project - source files accessible via view tool at /mnt/project/

## Key Decisions Made

1. **Incremental development:** Build module by module with tests
2. **Code in chat blocks:** Show code in code blocks for copy/paste, NOT as downloadable files
3. **Step-by-step process:** Explain -> Strategize -> Plan -> Code -> Test
4. **Locked specs:** decisions.md is authoritative, no scope changes during implementation
5. **Real testing:** Validate with actual HTML files and user feedback before v2
6. **Preview tool testing:** Manual only - no automated tests for preview_server.py

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
|   |   +-- input/
|   |   |   +-- simple_article.html
|   |   +-- expected/  (empty - for golden files)
|   |   +-- snapshots/  (empty - reserved)
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
|   +-- test_integration.py
+-- docs/
|   +-- decisions.md (authoritative spec)
|   +-- ARCHITECTURE.md
|   +-- research_typography_guidelines.md
|   +-- 0_0_FLOWDOC_V1_PLAN.md
|   +-- architecture_exploration.md
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

1. **Add input validation** - Start here, clear spec in decisions.md section 3
2. **Create fixture corpus** - Gather real HTML files
3. **Implement golden file tests** - Lock down output format
4. **Add determinism test** - Ensure reproducibility
5. **Embed OpenDyslexic font** - Complete the toggle feature

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

**Expected:** 81+ tests passing

## Communication Rules - CRITICAL

These rules MUST be followed in every response:

1. **Four-step process:** Purpose -> Strategy -> Plan -> Code. Wait for "yes" after EACH step before proceeding. No exceptions.
2. **One file at a time:** Show one file, wait for "done" before showing next file.
3. **Code blocks contain code and commands ONLY:** Never put file names, instructions, or explanations inside code blocks. These go outside the block.
4. **Always read files first:** Use view tool to read ANY file before showing changes to it. State "Reading X now" before every view call. No exceptions.
5. **Verify function signatures:** Never assume parameter names. Read the actual source file first.
6. **Complete changes across files:** When a change spans multiple files, read ALL affected files first, then list every change needed before touching any of them.
7. **New dependencies:** Call out pip install command BEFORE showing the run command.
8. **File locations:** Always tell the user exactly where to save each file.
9. **Code blocks must use 4 spaces for indentation, not tabs:** This ensures pasting into VS Code works correctly every time.
10. **No em dashes or smart quotes in code blocks:** ASCII only (straight quotes, hyphens).
11. **Commit guidance:** Provide summary and description for GitHub Desktop after each completed task.

## Critical Files to Read at Start of Every Session

1. /mnt/project/SESSION_SUMMARY.md - Current state (this file)
2. /mnt/project/decisions.md - Implementation contracts
3. /mnt/project/SCOPE.md - v1 boundaries
4. /mnt/project/ARCHITECTURE.md - Tech stack and structure

## Source Files Accessible via View Tool

All source files are at /mnt/project/ (flat, not in subdirectories in the project view):
- model.py, constants.py, sanitizer.py, content_selector.py
- degradation.py, parser.py, renderer.py
- main.py, reader.py, writer.py
- preview_server.py, preview.html

## Success Criteria (from SCOPE.md)

v1 is complete when:
1. OK - Accepts semantic HTML inputs within scope
2. OK - Produces self-contained readable HTML
3. PENDING - Output measurably better for dyslexic readers (needs user testing)
4. OK - Works on browsers, mobile, print
5. PENDING - Failure modes predictable and clear (needs validation)
6. OK - Inline elements render correctly
7. OK - Unsupported elements degrade deterministically
8. OK - Sanitization prevents active-content issues

Missing pieces: validation (#5) and user testing (#3).
