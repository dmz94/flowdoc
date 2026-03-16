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
- **Structural quality checker** -- Automated scoring of
  output quality beyond the current metrics: heading hierarchy
  coherence, paragraph length distribution, placeholder
  density. Would feed into a quality dashboard.
- **Vision model scoring** -- Use a vision model to compare
  rendered output against the original page and score visual
  quality. Expensive but could automate what is currently
  manual visual review.

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
- **Canny integration** -- Feature request voting board so
  testers and users can suggest and prioritize improvements.
  Deferred from v1 to keep the surface simple.
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

## Known Issues (v1 accepted)

- **Feedback double-send** -- Clicking a thumb POSTs
  immediately. If the user then types a comment and clicks
  Send, a second POST fires. Two Airtable rows per
  feedback-with-comment. Acceptable at tester scale.
- **Demo page social proof line** -- "2,847 wine
  enthusiasts..." leaks through Trafilatura extraction.
  Shows testers where engine gaps are. Not worth a
  special-case fix.
- **Relative links in uploaded files** -- When a user uploads
  a saved HTML file, relative links in the content have no
  base URL to resolve against. Links break. Documented in
  Help but not fixable without the original URL.
