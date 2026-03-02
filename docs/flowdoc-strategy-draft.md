# Flowdoc -- Revised Strategy and Product Direction

*Draft for review -- produced from strategy session 2026-03-02*
*Status: Draft. Pending review and controlled doc updates via Claude Code.*

---

## 1. Core Identity

Flowdoc is a free, open-source accessible HTML compiler. It transforms semantic
web articles into clean, portable, printable HTML documents formatted for readers
with dyslexia and related conditions.

It is not a browser reader mode. It is not a consumer app. It is not a platform
or business.

It is an engine that developers and technical users can build on, with a hosted
reference implementation that demonstrates what the engine does.

End beneficiaries are readers with dyslexia. Primary users of the tool itself are
developers and technically capable practitioners. Parents, teachers, and SEN
coordinators are reached through surfaces built on top of the engine -- not
through the CLI directly.

---

## 2. Product Architecture

Flowdoc is structured as three layers:

**Engine** -- the core conversion pipeline. Semantic HTML in, accessible HTML out.
Deterministic, security-bounded, model-driven. This is the primary development focus.

**PyPI package** -- the engine exposed as a clean Python API. Enables developers
to integrate Flowdoc into their own tools, plugins, and surfaces without
maintaining the engine themselves.

**Reference surface** -- a hosted implementation demonstrating the engine.
Initially on a temporary domain for testing and demos. Accepts a URL or uploaded
HTML file, returns a converted document. Primary purpose is validation and
demonstration, not scale.

All three layers are the responsibility of this project. Surfaces built on top of
the PyPI package -- browser extensions, CMS plugins, educational platform
integrations -- are community responsibility, not this project's.

---

## 3. Differentiation

The primary differentiator is artifact output, not features.

Browser reader modes (Edge Immersive Reader, Chrome, Safari) provide a better
in-session reading experience. Flowdoc does not compete on that ground.

Flowdoc produces a file. That file can be printed, emailed, saved offline, handed
to a student, or built into a resource pack. It exists outside the browser session
and outside the original website. That is a categorically different use case, not
a feature gap.

Secondary differentiators:
- BDA-aligned typography defaults, not user-configured guesswork
- Deterministic, reproducible output -- same input always produces the same file
- Security-bounded transformation -- strict sanitization before parsing
- No external dependencies in output -- single self-contained HTML file

The portable artifact use case is currently unvalidated with real users. This is a
known gap to be addressed through early tester recruitment before any surface
investment.

---

## 4. Current State

- Core pipeline built and tested
- 158 pytest tests passing
- Identity10 evaluation: 7 PASS, 1 MARGINAL, 3 FAIL
- Phase 2 complete
- CLI functional but not the target user surface
- Zero external user data or feedback
- Print quality unvalidated
- Test corpus insufficient for confident v1 definition

**Known engine gaps:**
- Wikipedia dense link-heavy content fails -- significance unclear until corpus
  is expanded
- Sample corpus too small to define v1 confidently
- OpenDyslexic embedding spec'd but not implemented

**What "done" means for the engine:**
Cannot be defined until corpus expansion results are in. v1 definition is
explicitly deferred until after the corpus expansion session.

---

## 5. Immediate Next Steps (Sequenced)

**Step 1 -- Corpus expansion session** *(next dedicated session)*
Expand test fixtures beyond Identity10 and Eval20. More document types, styles,
and sources. Diagnose Wikipedia failure -- fixable or architectural boundary.
Results determine v1 definition.

**Step 2 -- Print validation** *(needs dedicated planning)*
Requires thought before execution. Questions to resolve:
- Which document types represent real use cases?
- What are we evaluating -- typography, layout, readability, page breaks?
- Who is assessing -- owner alone, or a dyslexic reader?
- What is pass/fail criteria?

Primary reviewer candidate: owner's son. Selection of documents and evaluation
criteria to be agreed before printing anything.

**Step 3 -- Define "done" for the engine**
Explicit, measurable, agreed criteria before corpus results come in. Without this
the engine work has no natural stopping point.

**Step 4 -- Define v1**
Based on corpus results, print validation, and "done" definition. Rewrite
program-board.md Phase 3 tasks against real data.

**Step 5 -- OpenDyslexic embedding**
Contained, spec'd work. Implement before any public release. Not a current
priority.

**Step 6 -- Hosted reference surface**
Build after engine is stable and v1 is defined. Temporary domain for early
testing. URL input required. Basic typography controls included.
Note: temporary domain (aglet.club) for early testing only -- not the permanent
home.

**Step 7 -- PyPI package**
Clean API, well-documented. Enables community surfaces. Architecture and code
review by human contacts before release.

**Step 8 -- Tester recruitment**
Warm introductions via NSPCC network and personal connections. After hosted
surface exists -- nothing to test before then.

---

**Doc update triggers:**
- After corpus results: known-limitations.md, program-board.md, decisions.md
- After v1 definition: SCOPE.md, strategy.md, program-board.md
- After engine done: all docs for release

---

## 6. Elevator Pitch

If you have a child with dyslexia, you know the problem. You find a great article
online -- NHS, Wikipedia, BBC Bitesize. The content is exactly what you need. But
the website is cluttered, the text is cramped, and the formatting makes it hard
to read.

Browser reading modes help, but only while you're at that screen. You can't print
them reliably, email them to a teacher, or hand them to a student.

Flowdoc solves that. Give it a web article, it gives you back a clean, single
document -- formatted using dyslexia-friendly typography recommended by the
British Dyslexia Association. Ready to print, email, or save. No clutter. No
browser. No internet connection needed once you have the file.

It's free, open-source, and built for parents, teachers, and anyone who prepares
reading materials for people with dyslexia.

---

## 7. Deferred Items (Not v1)

**User typography controls**
Background color, font size, font choice, line spacing. Surface-layer feature for
hosted implementation. Engine stays deterministic, surface passes parameters.

**Browser extension**
Viable delivery method. Eliminates "save page as HTML" friction entirely. Evaluate
after hosted surface is validated.

**URL input**
Not needed for CLI v1. Mandatory for hosted surface. Server-side fetching adds
privacy and infrastructure considerations -- needs deliberate design decision
before implementation.

**Architecture and code review**
Human review when engine is stable and PyPI API is drafted, before hosted surface
build. Claude Code for tactical review in the meantime.

**Red team -- strategy assumptions**
Before committing to any surface, stress-test:
- Is the portable document use case real or assumed?
- Is "save page as HTML" too much friction even for technical users?
- Does BDA typography matter to users or just to the builder?

**Additional font toggles**
Lexend, Atkinson Hyperlegible, Dyslexie -- v2 candidates per research docs.
Not v1.

**Content transformation**
Sentence simplification, jargon expansion, paragraph breaking. v2 direction
per strategy.md.
