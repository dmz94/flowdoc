# Flowdoc v1 - Development Session Summary

**Date:** February 26, 2026
**Status:** Dual-pipeline architecture implemented. User study completed. Extraction cleanup in progress.
**Test Status:** 109 tests passing locally

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
- 109 tests passing
- test_content_selector.py - routing tests
- test_cli_basic.py - mode flag tests
- test_extract_mode.py - extract mode behavior and known limitations
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

## Current Trafilatura Flags

extract_with_trafilatura() in parser.py uses:
- include_comments=False
- include_tables=False
- favor_precision=True

## Current Typography (renderer.py / constants.py)

- Font size: 22px
- Max width: 58ch
- Line height: 1.7
- Paragraph spacing: 1.8em

## User Study Results

Tested 10 real-world pages. Inputs and Flowdoc outputs stored in tests/fixtures/user-study/.

### Extraction Results
| Page | Result |
|---|---|
| Guardian | COMPLETE FAILURE - no content extracted |
| The Ringer | COMPLETE FAILURE - no content extracted |
| NHS | EXTRACTS - missing intro paragraphs (starts too late) |
| CDC | EXTRACTS |
| Sky Sports | EXTRACTS - opening section junk (captions, tag links) |
| ProPublica | EXTRACTS - boilerplate at end, Reader Mode comparison poor |
| Smithsonian | EXTRACTS |
| Aeon | EXTRACTS |
| Eater | EXTRACTS - opening section junk, boilerplate at end |
| PBS | EXTRACTS - opening section junk, boilerplate at end |

### Comparison with Safari Reader Mode
- Reader Mode is strong on clean pages
- Reader Mode fails on image-heavy pages (Smithsonian, The Ringer)
- Reader Mode leaks boilerplate on complex pages (ProPublica)
- Flowdoc's image-stripping is a feature not a limitation on image-heavy pages
- Typography improvements made Flowdoc outputs significantly more readable than Reader Mode defaults

## Known Issues to Fix (Prioritized)

### Priority 1 - Opening section junk
PBS, Sky Sports, and Eater are pulling in image captions, related article bullets, and tag links before the article body starts.

### Priority 2 - Boilerplate at end
PBS, Eater, and ProPublica are leaking navigation and newsletter sections at the end of output.

### Priority 3 - Missing opening content
NHS is missing intro paragraphs. Trafilatura is starting extraction too late in the page.

### Deferred - Complete extraction failures
Guardian and The Ringer produce no usable output. Separate category of problem. Not addressing in current sprint.

## Next Steps

1. Extraction cleanup: fix opening junk and trailing boilerplate
2. Strategic review of project direction before more coding

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

tests/fixtures/input/ - original fixture set (used by automated tests)
tests/fixtures/user-study/ - 10 real-world HTML pages and 8 Flowdoc outputs from user study

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
|   |   +-- input/          (original fixture set - used by tests)
|   |   +-- user-study/     (10 real-world pages + 8 Flowdoc outputs)
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
|   +-- test_extract_mode.py
+-- docs/
|   +-- decisions.md (authoritative spec)
|   +-- architecture.md
|   +-- product-thinking.md (product positioning and viability)
|   +-- research_typography_guidelines.md
|   +-- flowdoc-v1-plan.md
|   +-- architecture-exploration.md
|   +-- known-limitations.md
|   +-- session-summary.md (this file)
+-- convert_fixtures.py
+-- fetch_fixtures.py
+-- preview_server.py
+-- preview.html
+-- SCOPE.md
+-- ABOUT.md
+-- README.md
+-- pyproject.toml
+-- .editorconfig
+-- .gitignore
```

## Testing Instructions

```
venv\Scripts\activate
pytest -v
python convert_fixtures.py
python preview_server.py
```

Expected: 109 tests passing

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
5. PENDING - Failure modes predictable and clear (validation implemented, extraction quality uneven)
6. OK - Inline elements render correctly
7. OK - Unsupported elements degrade deterministically
8. OK - Sanitization prevents active-content issues

Missing pieces: extraction cleanup, golden file tests, determinism test, font embedding, user testing.
