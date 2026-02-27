---

# Product Thinking (Aligned)

Status: Active (Aligned with canonical strategy)

This document supports the canonical strategy defined in docs/strategy.md.

Flowdoc is infrastructure-first:
an accessibility document compiler for prose content.

The primary product identity is not a consumer reading app.
Any user-facing surface exists only for validation and demonstration
of infrastructure output quality.

If conflicts exist between this document and docs/strategy.md,
docs/strategy.md wins.

---

# Flowdoc - Current Thinking (February 2026)

## What Flowdoc is
A Python CLI tool that converts article-like web pages into dyslexia-friendly,
self-contained, portable HTML using British Dyslexia Association typography
guidelines. By article-like, we mean pages whose primary content is longform
prose with headings and paragraphs - not tables, apps, or structured forms.

Input is HTML (string, file, or stdin), not a URL fetcher or browser renderer.
Output is a single self-contained HTML file with inline CSS and no external
dependencies (optional embedded font when enabled).

## The honest viability question
Browser Reader Mode already handles article readability for free in every major
browser. "Do people prefer Flowdoc over Reader Mode" is the wrong test. The
right question is: is there a population that needs what only Flowdoc provides,
and is that population large enough to matter?

## What only Flowdoc provides that Reader Mode does not
- Portable, self-contained file - save, share, print, archive, and read offline;
  no external dependencies; designed to be consistent across modern browsers
- Byte-identical output under pinned versions and flags, enforced by golden
  tests in CI
- Embeddable engine - runs server-side or in a pipeline without a browser
- BDA-grounded typography defaults applied consistently
- Dependencies are permissive-licensed; a licensing summary will be provided
  for integration review

## Critical constraint for any integration discussion
Flowdoc does not execute JavaScript. It requires HTML that already contains the
rendered article content. This rules out JS-rendered single-page apps and must
be stated upfront in any integration conversation.

## The distribution decision
Three possible targets: developer integration (B2B), power-user CLI, mainstream
end user. These require different tests and different product investments.
Mainstream end user requires a wrapper (browser extension or web app) that does
not exist yet.

## Recommended primary v1 target: Developer integration
The CLI exists and is the right reference interface for developers evaluating
integration. Portability, determinism, and the embeddable engine are the wedge
- not reading preference.

## Current integration surface (important to be honest about)
v1 is CLI-first with an internal Python library. The library is not yet a
stable public API contract. Engineers evaluating integration should treat the
CLI as the interface and expect the library contract to be formalized before
production use.

## First gating signal: end-user reaction
Before developer integration conversations, validate that real end users find
the output meaningfully better or meaningfully more useful (portable, offline,
printable). End-user evidence strengthens the developer pitch. If users see no
difference versus Reader Mode, the integration wedge is much harder to sell.

## What we test first
Find 4-5 diagnosed dyslexic readers plus additional non-dyslexic testers.
Show them Flowdoc output vs their browser's Reader Mode on 3-4 article-like
pages. Ask:
- Does this help you read?
- Would you want to save, share, or print this?
- Which would you choose and why?

## What we bring to developer conversations (after user signal)
A one-page integration spec covering: input assumptions, output contract,
determinism contract, failure modes and exit codes, security boundary,
licensing, and known limitations.

## Content scope
Article-like prose pages only (news, health, blogs, Wikipedia-style
encyclopedic prose). Non-article content fails fast with a clear error
rather than producing worse output.

## Known limitations
- Flowdoc does not execute JavaScript - input must be server-rendered or
  static HTML
- Wikipedia and similar dense link-heavy pages are supported but long
  lead sections can fragment into short paragraphs
- The internal Python library is not yet a stable public API
