# Decant Program Board

## Current State

v1 shipped. Surface live at decant.cc. Engine published on
PyPI as decant-cli 0.1.0. 47 fixtures, 47 PASS, 264 tests.
First tester round active.

## v1 Remaining

- Wider tester recruitment -- teachers, SEN coordinators
  via personal contacts

## v2 Backlog (unranked)

**Engine**

- **ML-based boilerplate detection** -- Trafilatura catches
  most site chrome but misses mid-article noise (newsletter
  signup blocks, related article widgets, social sharing bars
  embedded between paragraphs). An ML pass after extraction
  could identify and strip these.
- **Site-specific extractor registry** -- Some sites have
  consistent extraction problems. A registry of per-domain
  rules (CSS selectors, known junk patterns) would let the
  engine handle them without broadening general heuristics.
- **Paragraph repair** -- Trafilatura sometimes fragments
  long paragraphs into single-phrase chunks, especially on
  link-heavy pages like Wikipedia. A merge pass could
  reassemble these using sentence-boundary heuristics.
- **Definition list support** -- dl/dt/dd elements currently
  degrade to a flat list of "term - definition" strings.
  Proper rendering would preserve the term/definition
  relationship with appropriate styling.
- **Non-standard caption patterns** -- The caption harvester
  only recognizes semantic figcaption. Many sites use
  div.caption or similar class-based patterns. Structural
  audit found 1,074 instances across the WCEB benchmark.
- **Layout table unwrapping** -- Some older sites use tables
  for page layout, not data. These get rendered as data
  tables or trigger the "too complex" placeholder. Detecting
  and unwrapping layout tables would recover the prose inside.

**Output**

- **Dedicated PDF export** -- Currently "choose Print, then
  Save as PDF." A proper PDF export (server-side, via
  weasyprint or similar) would produce a downloadable PDF
  directly from the surface. Deferred from v1 due to hosting
  complexity.

**Surface**

- **Mobile and tablet layout** -- v1 is desktop-only. The
  toolbar does not work on small screens. Needs a different
  interaction pattern (hamburger menu, bottom sheet, or
  single-pane layout).
- **~~Canny integration~~** -- Replaced by Fider. Feature
  board live at https://decant.fider.io. Linked from Help
  popout and footer. Completed 2026-03-17.
- **Color vision support** -- Additional theme options or
  color adjustments for users with color vision deficiencies.
  Current themes address dyslexia; color blindness is a
  separate axis.
- **ADHD and processing difficulty profiles** -- Different
  typography and layout adjustments for readers with ADHD or
  other processing difficulties. Same engine, different
  rendering parameters.

**Distribution**

- **Browser extension** -- Convert articles without visiting
  decant.cc. Right-click a page, get a clean version.
  Significant UX and packaging work.
- **Automated PyPI publish via GitHub Actions** -- Currently
  manual (build + twine upload). A GitHub Actions workflow
  triggered by version tags would automate the release
  pipeline.
- **Contributing, Security, and Acknowledgments sections** --
  Add CONTRIBUTING.md, SECURITY.md, and an Acknowledgments
  section to the README. Follow the pattern used by similar
  open-source projects (contributor guidelines, vulnerability
  reporting instructions, credits for tools and people).
  Reference: https://github.com/TobiiNT/ClaudeTracker for
  a good example of these sections.

**Testing & Quality**

- **AI-powered corpus evaluation** -- A set of evaluation
  personas (completeness, noise detection, structure
  fidelity, readability, semantic accuracy, metadata) that
  read source pages and converted output, producing
  structured qualitative feedback per fixture. Complements
  the existing metrics runner, which measures quantities
  but not quality. Design in progress.
- **Accessibility audit of renderer output** -- One-time
  task: run axe-core against representative conversions,
  fix any issues in the renderer. Repeat after major
  renderer changes. Not a recurring automated layer --
  the renderer produces identical HTML structure for every
  fixture, so one audit covers all.
- **CSS regression tooling** -- Playwright screenshot
  diffing for before/after comparison when theme or
  surface CSS changes. Only worth building if CSS changes
  become frequent enough to warrant automation.

## Known Issues (v1 accepted)

(none)
