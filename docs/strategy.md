# Flowdoc Strategy (Canonical)

Status: Active  
Supersedes: prior exploratory and session summary documents  
Last Updated: 2026-03-02  

This document defines the canonical identity, scope, and direction of Flowdoc.
If any other document conflicts with this one, this document wins.

---

# Flowdoc - Strategic Positioning (Revised)
## An Accessibility Document Compiler for Prose Content

Version: Strategy Draft v2
Status: For structured review and critique

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

## 3. Problem Definition

A parent gets their child's dyslexia diagnosis. They search NHS, BDA,
Understood.org. The content is there but buried in site chrome, cramped
typography, and layouts designed for sighted neurotypical readers.

Browser Reader Mode helps but is ephemeral -- you cannot save it reliably,
print it with controlled typography, email it to a teacher, or hand it to
a student on a USB stick.

Teachers, SEN coordinators, and parents need actual documents: portable,
printable, readable offline, with typography tuned for accessibility.
Today that means manual reformatting. Flowdoc automates it.

The same problem applies across educational articles, health information,
knowledge base content, and editorial/blog content -- any prose article
where the content is "there" but presented in a way that creates
unnecessary barriers for dyslexic readers.

---

## 4. System Architecture (Conceptual)

Flowdoc behaves like a compiler:

Input: Semantic HTML (prose)
    -> Main content extraction
    -> Sanitization (security boundary)
    -> Parse into explicit internal model (IR)
    -> Deterministic structural transformation and degradation
    -> Render to self-contained accessible HTML

Key properties:

- Deterministic: same input + version + flags = byte-identical output
- Self-contained: single HTML file, no external dependencies
- Security-bounded: strict sanitization before parsing
- Model-driven: renderer consumes IR only (no raw DOM)
- Fail-fast: non-semantic inputs are rejected explicitly
- Version-pinned: dependency changes are intentional events

---

## 5. v1 Scope (Intentionally Narrow)

Supported inputs:
- Article-like prose documents
- Structured via h1-h3 and p/ul/ol
- Server-rendered semantic HTML only

Explicit exclusions:
- JavaScript-rendered SPAs
- Table-heavy reference content
- Forms and interactive applications
- Layout fidelity preservation
- PDF/DOCX input
- GUI or hosted SaaS

Flowdoc rejects non-semantic HTML rather than guessing.

This constraint preserves determinism and clarity.

---

## 6. Accessibility Focus

Initial focus: dyslexia-informed readability principles.

Includes:
- Sans-serif typography
- Controlled line length
- Increased spacing
- High-contrast palette
- No full justification
- Print-friendly formatting
- Portable offline artifact

Flowdoc does not claim universal efficacy.
Validation must be empirical.

---

## 7. Differentiation

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

## 8. Intended Users

End beneficiaries:
Readers with dyslexia or related conditions who benefit from improved
readability.

Primary users:
- Parents preparing reading materials for dyslexic children
- SEN coordinators and teachers creating accessible handouts
- Accessibility practitioners who need portable document conversion
- Tutors preparing session materials from web content

Distribution:
Free open-source tool distributed via pip and standalone binaries.
No monetization. No institutional sales dependency.

---

## 9. User-Facing Surface

Flowdoc ships as a CLI tool. A minimal local preview capability exists
for testing and demonstration.

The primary workflow is: give it an HTML file (or URL content saved as
HTML), get back a single self-contained accessible document.

Future consideration: a simple upload-and-convert web page or drag-and-drop
local app could lower the barrier for non-technical users. Any such surface
must not compromise input constraints, determinism, or security boundary.

---

## 10. Quality Model

Flowdoc follows a compiler-style quality model:

- Deterministic output
- Explicit internal representation
- Structured degradation rules
- Stable contracts
- Golden test corpus
- Dependency pinning

Future improvements resemble compiler passes:
- Paragraph repair
- Boilerplate trimming
- Structural normalization
- Fragment merging
- Nested list correction

Expansion deepens prose quality before broadening scope.

---

## 11. Known Limitations (v1)

- Dependent on extraction engine behavior
- CMS boilerplate may leak
- Dense link-heavy pages may fragment
- Table-heavy reference pages rejected intentionally
- No JS-rendered page support

These are documented boundaries, not defects.

---

## 12. Validation Plan

Before expansion:

1. Structured testing with diagnosed dyslexic readers
2. Compare:
   - Original formatting
   - Browser Reader Mode
   - Flowdoc output
3. Measure:
   - Reread frequency
   - Line-loss incidents
   - Subjective fatigue
   - Preference and print usability

If no meaningful benefit is demonstrated,
scope expansion is premature.

---

## 13. Strategic Expansion Path

Phase 2:
- Improve extraction repair quality
- Increase tolerance for imperfect semantic HTML

Phase 3:
- Additional accessibility profiles (ADHD, low vision, etc.)
- Additional delivery surfaces (hosted or extension)

Phase 4:
- Optional additional input front-ends (PDF/DOCX) if IR stability remains intact

All expansion must preserve:
- Determinism
- Security boundary
- Explicit failure modes

---

## 14. Open Questions

- Is the CLI sufficient for the target audience, or is a simpler interface
  needed for non-technical users (parents, teachers)?
- What distribution channels reach the dyslexia/SEN community effectively?
  (BDA, dyslexia forums, SEN coordinator networks, parent groups)
- What level of extraction imperfection is tolerable for the target use cases?
- Does the tool need to handle URL input directly, or is "save page as HTML"
  an acceptable workflow step?

---

## 15. Long-Term Identity

Flowdoc aims to be:

A free, focused tool that saves parents, teachers, and practitioners
the effort of manually reformatting documents for dyslexic readers.

It produces durable, portable, printable accessible documents from web
content. If it saves even a fraction of the manual reformatting effort
and produces a better result, it justifies existing.
