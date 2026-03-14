# Decant

Decant is a free, open-source tool that converts web articles
into clean, accessible HTML documents styled for readers with
dyslexia and related conditions. It strips site chrome,
extracts article content, and produces a single portable
document with accessibility-focused typography -- printable,
offline-readable, and ready to hand to a student or email to
a teacher.

Many web pages are technically readable but visually fatiguing
for dyslexic readers due to cramped line length, poor spacing,
and layouts that prioritize appearance over readability. Browser
Reader Mode helps but is ephemeral -- you cannot save it, print
it with controlled typography, or share it reliably. Decant
produces actual documents.

## Try it

**Web:** [decant.cc](https://decant.cc) -- paste a URL or
upload an HTML file.

**CLI:**

    pip install decant-cli
    decant input.html
    decant input.html -o output.html
    decant input.html --font opendyslexic

Print to PDF: open the output in a browser and use
print-to-PDF.

## What it handles

- Articles, blog posts, and long-form prose with semantic HTML
- Headings, paragraphs, lists, blockquotes, code blocks,
  images, tables
- Inline emphasis, strong, code, and links
- Automatic content extraction via Trafilatura
- Strict sanitization of active content

## What it does not handle

- JavaScript-rendered pages or SPAs
- Login-required content (save the page as HTML and upload it
  instead)
- PDF, DOCX, or Markdown input
- Layout-heavy or table-dominant reference pages

These are documented boundaries, not defects. When Decant
encounters content outside its scope, it says so clearly.

## Output

A single self-contained HTML file:
- No external CSS, fonts, or scripts
- Images reference original source URLs
- OpenDyslexic font embedded when enabled
- Designed for screen, print, and offline reading

## Testing

- Unit and integration tests (pytest)
- 47-fixture real-world corpus with metrics-based regression
  tracking
- ScrapingHub Article Extraction Benchmark (181 pages)
- Webis Web Content Extraction Benchmark (3,985 pages)

## Documentation

- [docs/decisions.md](docs/decisions.md) -- authoritative
  implementation spec
- [docs/architecture.md](docs/architecture.md) -- tech stack
  and module structure
- [docs/strategy.md](docs/strategy.md) -- identity and
  direction
- [docs/research-typography-guidelines.md](docs/research-typography-guidelines.md)
  -- typography research
- [ABOUT.md](ABOUT.md) -- project origin story

## Status

v1 surface live at [decant.cc](https://decant.cc). Engine
tested against 47 real-world fixtures (47 PASS, 264
unit/integration tests). Published on
[PyPI](https://pypi.org/project/decant-cli/) as decant-cli.

## License

[MIT](LICENSE)
