# Flowdoc

Flowdoc is a CLI tool that converts HTML documents into **readable, accessibility-friendly HTML** that works consistently across devices and print. The initial focus is dyslexia, grounded in British Dyslexia Association typography guidelines, but the same approach applies to related conditions such as ADHD, Irlen Syndrome, and low vision — making Flowdoc a general-purpose accessibility conversion tool.

Why Flowdoc? Many documents are technically "readable" but visually fatiguing for readers with dyslexia and related conditions due to cramped line length, poor spacing, and layout choices that prioritize appearance over readability. Flowdoc deliberately **throws away layout fidelity** and re-renders content with typography and spacing tuned for readability.

## v1 scope (summary)

- Input: HTML with semantic structure (headings, paragraphs, lists)
- Output: a single, self-contained HTML file (no external CSS/fonts/scripts/images)
- Readability over fidelity: no attempt to preserve original styling or branding
- Optional font toggle: `--font opendyslexic` (not default)

Full boundaries: see [SCOPE.md](SCOPE.md).

## Status

Core pipeline implemented and tested. First real-world validation complete. Active development continuing.

## Planned CLI

```bash
flowdoc convert input.html
flowdoc convert input.html -o output.html
flowdoc convert input.html --font opendyslexic
```

Print to PDF: open the output in a browser and use print-to-PDF.

## Documentation

- [SCOPE.md](SCOPE.md) - frozen v1 product boundaries and success criteria
- [docs/decisions.md](docs/decisions.md) - authoritative implementation/test spec (contracts + invariants)
- [docs/architecture.md](docs/architecture.md) - locked v1 implementation choices (runtime, libraries, module structure, pipeline, testing)
- [docs/flowdoc-v1-plan.md](docs/flowdoc-v1-plan.md) - execution checklist for v1
- [docs/research_typography_guidelines.md](docs/research_typography_guidelines.md) - typography research/reference
- [docs/architecture-exploration.md](docs/architecture-exploration.md) - non-normative historical exploration/background
- [docs/session-summary.md](docs/session-summary.md) - current development state and next steps
- [ABOUT.md](ABOUT.md) - project origin story and motivation
- [CHANGELOG.md](CHANGELOG.md) - notable changes

## License

[MIT](LICENSE)
