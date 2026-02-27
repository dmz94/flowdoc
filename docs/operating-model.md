# Flowdoc Operating Model

Purpose:
This document describes how to run Flowdoc development using a controller loop and Claude Code, without requiring the controller to access the repo.

## System Roles

- You (Owner): sets priorities, approves diffs, decides what ships.
- Controller Chat (ChatGPT or Claude chat): sequences work, defines acceptance gates, produces exact prompts for Claude Code, reviews pasted outputs/diffs.
- Claude Code (VS Code): reads repo, edits code/docs, runs tests, produces diffs and summaries.

Key principle:
The controller does not need repo access because Claude Code is the repo-aware executor. The controller operates on (a) the canonical docs, and (b) pasted outputs (diffs, test results, summaries).

## Canonical Control Docs

- docs/program-board.md: identity, v1 success, scope boundaries, ranked backlog. Changes rarely.
- docs/phase-2-plan.md: current milestone execution plan. Updated as work completes.

## Daily Build Loop (Execution)

1) Open docs/program-board.md and docs/phase-2-plan.md.
2) Ask the controller for ONE next step tied to the next incomplete Phase 2 item.
3) Paste the controller's prompt into Claude Code.
4) Claude Code executes and stops at the requested gate (usually: show diff + test output; no commit).
5) Paste results back to the controller.
6) Commit only after you review the diff and tests.

Rule: one step per cycle. No parallel work.

## Weekly Review Loop (Planning)

Once per week (or at milestone boundaries):

1) Review phase-2-plan.md progress and any blockers.
2) Confirm backlog order in program-board.md still matches reality.
3) Make only minimal updates:
   - mark completed items
   - adjust ordering
   - record new decisions in decisions.md when needed

## When to Use Which Tool

- Use Claude Code for all repo operations: edits, tests, diffs.
- Use the controller chat for sequencing, gates, and review.
- Use Claude chat (Sonnet/Opus) for timeboxed research or audits only, with explicit constraints.

## Guardrails

- No scope expansion inside implementation steps.
- Tests-first for behavioral changes.
- Preserve determinism.
- Prefer small, end-anchored, structural heuristics over broad scoring systems.
- Archive superseded docs rather than rewriting history.
