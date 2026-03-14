# Flowdoc - Project Rules for Claude Code

## Identity

Flowdoc is a free, open-source CLI tool that converts semantic HTML into
accessible, self-contained, printable HTML documents for readers with
dyslexia and related conditions.

It is a focused utility for parents, teachers, SEN coordinators, and
accessibility practitioners. Not infrastructure. Not a platform. Not a
business. Not a consumer app.

Primary users are developers and technical practitioners. Parents and
teachers are reached through surfaces built on the engine.

## v1 Scope (Non-Negotiable)

Inputs:
- Server-rendered semantic HTML
- Article-like prose structure

Explicit Non-Goals:
- No JavaScript execution
- No SPA rendering
- No URL fetching
- No dynamic DOM evaluation
- No universal web support

Fail fast on unsupported input.
Do not silently guess.

## Engineering Constraints

- Deterministic output:
  Same input + version + flags -> byte-identical output.

- Security boundary:
  Always sanitize before parsing.
  Never trust raw HTML.

- Structured architecture:
  Maintain IR/model layer.
  Renderer must not consume raw DOM.

- Small changes:
  Implement the smallest change that satisfies the task.
  Do not refactor broadly without explicit instruction.

## Work Process Rules

- When behavior changes, update or extend tests and fixtures.
- If a requested change expands scope, stop and ask.
- Do not introduce new features unless explicitly requested.
- Keep strategy, scope, and decisions aligned.

## Working Style

- Dave drives pace. Do not advance to the next task without
  explicit go-ahead.
- One thing at a time. Complete the current task before
  suggesting the next.
- When a concern is raised (e.g. repo cleanliness, naming),
  address it now — it is not a passing comment.
- If the task is exploratory or a discussion, match that pace.
  Do not jump to implementation until a decision is reached.
- Keep responses proportional. Short question, short answer.
- Present options, not conclusions, when a decision is needed.

## Task Completion Rules

- Default: commit and push at end of every task.
  Before committing:
  1. pytest must pass
  2. eval must show 0 REGRESSION, 0 FAIL
  3. If changes feel risky or surprising (large diffs, unexpected
     metric shifts, broad refactors), run additional sanity checks
     and report findings before pushing.

- Cleanup verification (run before every commit):
  1. git status -- only intentional changes should be present
  2. Delete any stray working directories created during the
     session (eval/reports/, scripts/, or anything else not in
     the locked top-level structure)
  3. Delete any __pycache__, .pyc, or temp files outside .venv/
  4. Verify no new top-level directories exist beyond the locked
     set: .claude, .github, .vscode, docs, decant, surface, tests
     (plus dotfiles and root-level config/doc files). If a new
     directory was created, delete it unless the task explicitly
     required it.

- Maintain existing directory structure and naming conventions.
  Do not create new top-level directories without discussion.

- Fixture URLs are chosen by Dave, not by AI.
  AI does the plumbing: fetch, save, manifest, baseline, commit.

- VERIFY BEFORE DESCRIBING OR MODIFYING: Never describe what
  code does, what state it is in, or how it behaves without
  reading it first. This applies to ALL AI sessions: Opus
  controller chats, Claude Code implementation, and any other
  context. If you cannot read the file, say so explicitly and
  either (a) write a diagnostic prompt for CC to read and
  report, or (b) ask Dave to provide the relevant code. Do not
  fill the gap with speculation, inference from specs, or
  assumptions about what the code "probably" does. Specs
  describe intent. Code describes reality. They diverge.

- Wait for Railway deploy to complete before pushing
  another commit. Check the Railway dashboard or allow
  60 seconds.

- Surface fixes: commit and push each fix individually.
  Do not batch pushes.
