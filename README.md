# Flowdoc

Flowdoc converts structured documents into dyslexia-friendly, readable formats that work consistently across devices and print.

## Why Flowdoc?

Reading shouldn't be harder than it needs to be. Standard document formats often use layouts, fonts, and spacing that create unnecessary barriers for dyslexic readers. Flowdoc removes those barriers by transforming documents into formats optimized for readability.

Instead of preserving original layouts and visual design, Flowdoc prioritizes what matters: making content accessible and easy to read.

## Features

- **Dyslexia-friendly typography** - Typography informed by British Dyslexia Association guidance and published research
- **Optimized layout** - Single-column flow, proper line length, generous margins
- **Semantic structure** - Clear heading hierarchy, well-formatted lists and quotes
- **Self-contained output** - No external dependencies, works offline
- **Cross-platform** - Modern browsers, mobile devices, print-to-PDF
- **Privacy-focused** - Local conversion, no cloud processing

## Use Cases

Flowdoc works with any text-based structured content:

- Recipes
- Articles and blog posts
- Educational materials
- Technical documentation
- How-to guides and instructional content
- Work documents
- Reports and presentations

If your document has headings, paragraphs, and lists, Flowdoc can make it more readable.

## Project Status

**v1 is currently in development.**

Status: Early CLI prototype. Not production-ready.

v1 scope:
- **Input:** HTML with semantic structure (h1-h6, p, ul, ol, blockquote, code)
- **Output:** Self-contained, readable HTML
- **Font options:** System fonts (Arial/Verdana) or OpenDyslexic toggle
- **PDF output:** Via browser print-to-PDF

See [SCOPE.md](SCOPE.md) for complete v1 boundaries and design principles.

## Installation

*Coming soon - v1 in development*

## Usage

*Coming soon - v1 in development*

Planned CLI:
```bash
flowdoc convert input.html
flowdoc convert input.html -o output.html
flowdoc convert input.html --font opendyslexic
```

Example output: flowdoc convert recipe.html produces recipe.flowdoc.html

## Design Principles

**Readability over fidelity** - Flowdoc intentionally does not preserve original layout, branding, or page geometry. The goal is readable content for dyslexic readers, not visual reproduction of source documents.

**Semantic structure required** - Input documents must use proper HTML semantic elements (headings, paragraphs, lists), not div-based layouts.

**Research-informed defaults** - Typography and layout decisions are based on British Dyslexia Association guidelines and peer-reviewed research.

## Documentation

- [SCOPE.md](SCOPE.md) - Project scope, boundaries, and what Flowdoc is (and isn't)
- [docs/decisions.md](docs/decisions.md) - Technical decisions, typography research, and implementation rationale

## Contributing

*Coming soon - contribution guidelines will be added once v1 reaches stability*

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

Typography guidelines based on:
- British Dyslexia Association Style Guide (2023)
- Peer-reviewed research on dyslexia-friendly design
- Feedback from dyslexic readers