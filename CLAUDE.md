# Decant - Project Rules for Claude Code

## Identity

Decant is a free, open-source tool that converts semantic HTML into
accessible, self-contained, printable HTML documents for readers with
dyslexia and related conditions.

## v1 Scope

Inputs: server-rendered semantic HTML with article-like prose structure.
Fail fast on unsupported input. Do not silently guess.

Non-goals: JavaScript execution, SPA rendering, URL fetching, dynamic
DOM evaluation, universal web support.

## Engineering Constraints

- Deterministic output: same input + version + flags = byte-identical output.
- Security boundary: always sanitize before parsing. Never trust raw HTML.
- Structured architecture: maintain IR/model layer. Renderer must not consume raw DOM.
- Small changes: implement the smallest change that satisfies the task.
  Do not refactor broadly without explicit instruction.

## Work Process Rules

- When behavior changes, update or extend tests and fixtures.
- If a requested change expands scope, stop and ask.
- Do not introduce new features unless explicitly requested.
- Fixture URLs are chosen by Dave, not by AI.

## Session Start (IMPORTANT)

Every session must begin with:
1. git pull
2. Read this file (CLAUDE.md)
3. Read any files relevant to the task BEFORE making changes

## Read Before Modify (IMPORTANT)

NEVER modify a file without reading it first in the same session.
NEVER describe what code does without reading it first.
Do not guess at file contents, function signatures, paths, or
directory structures. If you cannot read a file, say so.

## Diagnostic Before Fix (IMPORTANT)

If a task involves changing code, read all relevant files first
and report what you find BEFORE making any changes. If anything
is surprising or unclear, stop and report instead of proceeding.
Do not assume what the code does based on specs or memory.
Specs describe intent. Code describes reality. They diverge.

## DYRI (IMPORTANT)

DYRI = "Did You Read It?" When a prompt starts with DYRI,
you must verify you have actually read all relevant files
before responding. If you have not read them, say so and
read them first. Do not guess, infer, or describe file
contents without reading them.

## Working Style

- Dave drives pace. Do not advance to the next task without
  explicit go-ahead.
- One thing at a time. Complete the current task before
  suggesting the next.
- When a concern is raised, address it now.
- If the task is exploratory or a discussion, match that pace.
  Do not jump to implementation until a decision is reached.
- Keep responses proportional. Short question, short answer.
- Present options, not conclusions, when a decision is needed.

## Commit and Deploy Rules

- Default: commit and push at end of every task.
  Before committing:
  1. pytest must pass
  2. eval must show 0 REGRESSION, 0 FAIL
  3. If changes feel risky or surprising, run additional sanity
     checks and report findings before pushing.
- Surface fixes: commit and push each fix individually.
  Do not batch pushes.
- Wait for Railway deploy to complete before pushing another
  commit. Allow 60 seconds.

## Cleanup (run before every commit)

1. git status -- only intentional changes should be present.
2. Delete stray working directories (eval/reports/, scripts/,
   or anything not in the locked top-level structure).
3. Delete __pycache__, .pyc, or temp files outside .venv/.
4. Verify no new top-level directories exist beyond the locked
   set: .claude, .github, .vscode, docs, decant, scripts, surface, tests
   (plus dotfiles and root-level config/doc files). Delete any
   unauthorized new directories.

## Directory Structure

Maintain existing directory structure and naming conventions.
Do not create new top-level directories without discussion.
