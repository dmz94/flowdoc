# Decant v1 -- Hosted Surface Specification

Status: Draft for review
Date: 2026-03-11
Author: Opus (controller) + Dave (product owner)
Supersedes: success-contract.md section 10 (test surface)

This document specifies the v1 hosted surface for Decant (working
name; engine codebase remains `flowdoc` until full rename before
PyPI). The surface is a v1 deliverable. The engine alone is not a
product.

---

## 1) Purpose

The surface exists to:

1. Make Decant usable by non-technical people (teachers, parents,
   SEN coordinators) without installing Python or using a CLI.
2. Validate the product with real users before broader release.
3. Demonstrate the engine's output quality.
4. Collect feedback to inform v2.

---

## 2) Domain and Branding

- Production domain: decant.cc
- User-facing name: Decant
- Internal module name: flowdoc (rename deferred to pre-PyPI)
- Cloudflare in front of decant.cc from day one
- aglet.club retained but not used for the surface

---

## 3) Repo Structure

Monorepo. Surface lives in `surface/` at the repo root.

```
flowdoc/          # Engine (unchanged)
surface/          # Hosted surface (new)
  app.py          # Flask application
  requirements.txt  # Surface-specific deps (Flask, gunicorn, weasyprint, etc.)
  templates/
  static/
  Dockerfile
tests/            # Existing test suite (unchanged)
docs/             # Existing docs (unchanged)
```

The surface imports the engine as a local package during
development. In production, the engine is installed via pip
(or local path in the Docker image).

Surface dependencies do not leak into pyproject.toml. The engine
stays clean.

---

## 4) Architecture

### Stack

- Backend: Python / Flask
- Frontend: Server-rendered HTML + vanilla JS (no framework)
- PDF generation: weasyprint (server-side, from engine HTML output)
- Hosting: Fly.io (Docker container)
- Edge: Cloudflare (DNS, SSL, DDoS, caching static assets)
- Monitoring: UptimeRobot + Sentry + structured request logging
- Analytics: Plausible

### Request flow

```
User browser
  -> Cloudflare (edge protection, SSL, static cache)
  -> Fly.io (Flask app)
    -> URL fetch (with SSRF protection) or file upload
    -> flowdoc engine (HTML string in, HTML string out)
    -> Response: rendered page with Decant output
    -> Optional: weasyprint for PDF download
```

The engine is invoked as a library call, not a subprocess.
The surface handles URL fetching, file upload, error translation,
and all user interaction. The engine remains file-in/file-out with
no network awareness.

---

## 5) Page Layout

Centered max-width container (1200-1400px). Not full-width.

Three zones:

### Header bar

- Decant logo/name (left)
- Help icon (?) -- opens slide-out panel with instructions
  (see section 6)
- Settings gear icon -- opens slide-out panel with
  customization controls (see section 7)

### Input zone (top)

Clean and minimal. Three elements only:

- URL text input with "Convert" button
- File upload: drag-and-drop area + file picker button
- "Try an example" text link -- click to reveal dropdown of
  3-5 pre-converted samples (hidden by default, see section 8)

### Comparison zone (below input, two panes side-by-side)

- Left pane: original page (iframe)
- Right pane: Decant output

Synced scroll toggle between panes. Default: off.

When original page blocks iframe embedding (X-Frame-Options),
left pane shows: "This site doesn't allow embedding. View
original at [link]." Conversion still works normally.

### Output actions (icon bar at top of Decant output pane)

Compact icon row. Icons only, no labels. Tooltips on hover.

- Printer icon: opens Decant output in new tab, triggers
  print dialog
- Download icon: downloads .decant.html file
- PDF icon: server-side weasyprint PDF generation
- Share icon: copies pre-filled URL to clipboard
- Feedback prompt: inline thumbs up/down (see section 9)

---

## 6) Instructions (Help Panel)

Accessed via the help icon (?) in the header bar. Opens a
slide-out panel. Not visible on the main page by default.

Content:

- One sentence: what Decant does
- What it works well on (articles, blog posts, prose content)
- What it does not handle (JavaScript-heavy pages, login-required
  content, interactive apps)
- Suggestion: "If a page requires login, save it from your
  browser (File > Save As > HTML) and upload it here"

The main page stays clean. Help is discoverable but not
intrusive.

---

## 7) Customization Controls (Settings Panel)

Accessed via the gear icon in the header bar. Opens a slide-out
panel. Changes apply to the Decant output pane in real time.
Panel closes, settings persist. Stored in localStorage.

CSS-only overrides injected by the surface on top of engine
output. The engine is not modified.

### V1 controls

1. Background color: white, cream/sepia, dark
2. Font choice: system sans-serif, OpenDyslexic, serif
3. Font size: slider or +/- buttons
4. Line spacing: slider or discrete steps
5. Content width: slider or discrete steps

These directly address tester feedback and match baseline
expectations set by browser reader modes (Edge, Firefox,
Chrome, Safari all offer these).

Settings persisted in localStorage across sessions.

### Deferred to v2 (informed by tester feedback)

- Line focus (highlight N lines)
- Read aloud / text-to-speech
- Letter / word spacing
- Font weight
- Custom color themes
- Irlen Syndrome filters

A link to the Canny feature voting board allows users to
request and vote on future controls.

---

## 8) Samples

3-5 pre-converted examples shipped as static assets. Accessed
via the "Try an example" link near the URL input (dropdown,
hidden by default).

Clicking a sample loads both the original and the Decant output
into the two panes. No server-side fetch required. Pre-baked
during build.

Samples are the implicit demonstration: users see what "good"
looks like before trying their own URLs.

### Categories

1. Health / medical -- the NHS or Mayo Clinic type article a
   parent searches after a diagnosis. Emotional core use case.
2. Education / parenting -- Understood.org or BDA-style article
   about supporting a child with learning differences.
3. News / current affairs -- BBC or Guardian long-form article.
   Shows the tool works on mainstream content.
4. Long-form feature -- Atlantic, Ars Technica, or similar
   in-depth piece. Demonstrates handling of substantial content.
5. Government / public service -- GOV.UK or CDC informational
   page. Dense, authoritative, often poorly formatted.

Curation process: Dave selects specific URLs. Pipeline converts
them. Output verified for quality. Only articles that convert
cleanly and demonstrate range ship as samples.

---

## 9) Feedback Mechanism

### Inline feedback (built into surface)

After conversion, a prompt appears in the output pane:

"How did this look?" with thumbs up / thumbs down and an
optional free-text field.

Submitted to a lightweight backend endpoint. Stored as
structured logs (URL converted, rating, text, timestamp).

### Feature requests (external)

Canny free tier. Link on the surface: "Request a feature" or
"What should we build next?"

GitHub Discussions remains available for developer-oriented
feedback.

---

## 10) Share

"Share" button copies a URL to the user's clipboard:

```
https://decant.cc?url=https://example.com/article
```

Recipient clicks the link. The surface opens with the URL
pre-filled. Recipient clicks "Convert" to generate the output.

No server-side storage. No expiry management. No copyright
complication. If the original article changes or goes down,
the share link reflects that.

Auto-convert on shared links is a design choice to resolve
during implementation (trade-off: faster experience vs.
unexpected server load from link previews).

---

## 11) Error Handling

All errors appear inline in the Decant output pane (where the
converted document would normally render). No modals, no browser
alerts, no stack traces.

Every error message includes: what happened, why, and a
suggested next action.

### Error catalog

| Condition | Detection | Message approach |
|---|---|---|
| Invalid input (not a URL) | URL format validation | "That doesn't look like a web address. Paste the full URL from your browser -- it should start with https://" |
| URL unreachable (DNS, timeout, refused) | Fetch failure, 15-20s timeout | "Couldn't reach that page. The site might be down or the address might have a typo." |
| Paywall / login required | Short body, login form heuristics, engine validation failure | "This page requires a login or subscription. If you have access, save the page from your browser (File > Save As > HTML) and upload it here." |
| JavaScript-required SPA | Empty/minimal extraction, engine validation failure | "This page loads its content using JavaScript, which Decant can't process. Try saving the page from your browser and uploading it instead." |
| No article detected | Engine validation (no headings, insufficient text) | "Couldn't find an article on this page. Decant works best with articles and blog posts. Try a direct link to a specific article." |
| SSRF blocked (private IP, non-HTTP scheme) | IP validation | "That address can't be converted. Decant works with public web addresses (https://)." |
| Response too large (>5-10MB) | Content-length / stream abort | "That page is too large to convert." |
| Non-HTML content (PDF, image, etc.) | Content-type header | "That link points to a [PDF/image/file], not a web page. Try linking to the page that contains the content." |
| Rate limited | Rate limiter | "You've converted several pages recently. Please wait a few minutes before trying again." |
| Server error | Catch-all exception handler | "Something went wrong on our end. Try again in a moment." + optional issue report link |

Design principles:
- Never reveal infrastructure details (rate limits, IP rules,
  internal architecture)
- Never show tracebacks to users (log server-side via Sentry)
- Keep tone honest, brief, not apologetic
- Always suggest a next action

---

## 12) Security

### SSRF prevention (critical)

- Resolve URL IP before fetching
- Block all private/reserved ranges (10.x, 172.16-31.x,
  192.168.x, 127.x, 169.254.x, ::1, link-local IPv6)
- Block non-HTTP(S) schemes (no file://, ftp://, gopher://,
  data://)
- Re-check resolved IP at each redirect hop
- Consider DNS-pinning or manual resolution

### Rate limiting

- Per-IP: 10 conversions per hour (adjustable after observing
  real traffic)
- Global: 5-10 concurrent fetches maximum
- Request timeout: 15-20 seconds hard cap

### Input validation

- Well-formed HTTP(S) URL required
- Maximum URL length: 2048 characters
- Maximum response body: 5-10MB
- Content-type must be text/html

### Output safety

- Engine sanitizes via nh3 (existing)
- Original-page iframe: sandbox="allow-same-origin" (no script
  execution, no form submission, no top-level navigation)
- All surface error messages and metadata HTML-escaped
- Content-Security-Policy headers on all surface pages
- CORS: API endpoint accepts requests from decant.cc origin only

### Platform-level

- Cloudflare free tier: DDoS protection, bot detection, rate
  limiting rules
- HTTPS mandatory (Cloudflare or Let's Encrypt)
- Structured request logging (URL, status, processing time,
  IP hash) for abuse detection

### Cloudflare deployment checklist

At deploy time:
- Upgrade SSL/TLS from Flexible to Full (Strict) -- Fly.io
  provides valid origin cert
- Set minimum TLS version to 1.2 (SSL/TLS > Edge Certificates)
- Add Cloudflare rate limiting rule on the URL submission
  endpoint (defense in depth, in addition to application-level
  rate limiting)
- Review WAF managed ruleset (OWASP) for Flask/Python stack
- Block AI bots (Security > Settings) -- the domain hosts an
  accessibility tool, not training data
- robots.txt: disallow AI crawlers explicitly

Already configured (2026-03-11):
- SSL/TLS mode: Flexible (upgrade at deploy)
- Always Use HTTPS: On
- DNSSEC: Enabled
- Bot Fight Mode: On
- Browser Integrity Check: On
- SPF record: v=spf1 -all (no email sending)
- DMARC record: v=DMARC1; p=reject (reject spoofed mail)

---

## 13) Monitoring and Analytics

### Monitoring (day one)

- UptimeRobot: uptime checks, downtime alerts
- Sentry: error tracking with full context
- Structured request logs: URL submitted, status code,
  processing time, error category

### Analytics

- Plausible: page views, referrer sources, country, user
  flow (privacy-respecting, no cookies)

---

## 14) Mobile

Deferred. Side-by-side layout does not translate to small
screens. The surface ships desktop-first. Mobile would likely
require a different interaction pattern (single-pane, output
only). Revisit after v1 feedback.

---

## 15) About / Footer

- One sentence: what Decant is
- Link to GitHub repo
- Link to PyPI (when published)
- Link to Canny feature board
- "Developers: install via pip" with CLI example

---

## 16) Cross-Platform

It's a web app. Works on macOS, Linux, Windows in any modern
browser. No platform-specific concerns.

---

## 17) Pre-Release CLI Security Audit

Separate from the surface, but flagged here for completeness.
Before v1 ship, audit:

- nh3 allowlist review (no active content survives sanitization)
- Path traversal on --output flag
- Dependency supply chain (pinned versions, known CVE check)
- Resource exhaustion (input size limits for huge/nested HTML)

This is a checklist item, not a surface feature.

---

## 18) UX Polish (Post-Functional)

After the surface is functional and tested, engage Digiteum
for professional UX/UI review and skinning. Sequence:

1. Build functional surface
2. Ship to testers
3. Collect feedback
4. Digiteum review and polish
5. Iterate

Do not let polish block tester access.

---

## 19) Conflicts and Dependencies

- success-contract.md section 10 describes a "test surface"
  that this spec supersedes. Section 10 should be updated to
  reference this spec.
- success-contract.md section 11 still says "No table
  rendering" -- needs updating (tables shipped in commit
  682f7f4).
- success-contract.md section 12 says v1 has no
  user-configurable parameters beyond OpenDyslexic toggle.
  This spec adds surface-layer CSS overrides (background,
  font, size, spacing, width). The engine remains unchanged.
  Section 12 should note that the surface offers these controls.
- success-contract.md section 13 lists "Profile system or
  user-configurable typography parameters" as a non-goal.
  This spec's customization is surface-only CSS injection,
  not a profile system. No conflict, but worth noting.
- pyproject.toml is not modified. Surface dependencies live in
  surface/requirements.txt.
- Program-board.md Step 6 references aglet.club as the
  temporary domain. Update to decant.cc.

---

## 20) Open Items for Implementation

- Auto-convert on shared links: decide during implementation
  (UX vs. server load from link previews)
- Exact rate limit thresholds: tune after observing real traffic
- Maximum response body size: 5MB or 10MB (test with real pages)
- Sample article selection: Dave to pick 3-5 URLs from corpus
- Iframe sandbox attribute: exact policy to be tested during
  implementation
- Feedback storage: structured logs vs. lightweight database
  (depends on volume expectations)
