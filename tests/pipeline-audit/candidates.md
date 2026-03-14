# Corpus Replacement Candidates

Fixtures removed in MARGINAL recalibration session (2026-03-04).
Reason: recipe sites and procedural/image-dependent content are
poor representatives of the Decant target use case (accessible
prose documents).

Each candidate below needs URL screening before being added as
a fixture. See docs/decant-eval-cheatsheet.md for the screening
and fixture-addition workflow.

---

## Removed Fixtures

| fixture                  | reason removed                                      |
|--------------------------|-----------------------------------------------------|
| wikihow-vegetable-garden | procedural/image-dependent, not prose               |
| whatthefork-cornbread    | recipe site, scope boundary                         |
| bakedcollective-muffins  | recipe site, scope boundary                         |

---

## Replacement Candidates

Target: 3 replacements. Format and HTML structure categories
that are underrepresented in the current corpus after removals.

Suggested categories to target:
- Long-form prose (narrative non-fiction, feature journalism)
- Instructional prose (how-to guides written as prose, not
  step-by-step procedural lists)
- Reference and explainer (accessible explainers on health,
  science, or civic topics)

| candidate | url | category | screened | notes |
|-----------|-----|----------|----------|-------|
| TBD       |     |          | no       |       |
| TBD       |     |          | no       |       |
| TBD       |     |          | no       |       |

---

## Screening Checklist (per candidate)

- [ ] URL resolves and returns full HTML (no JS-only rendering)
- [ ] No login wall or paywall
- [ ] Article is prose-dominant (not image-heavy or step-list-heavy)
- [ ] Source word count is reasonable (not extreme chrome bloat)
- [ ] Decant output passes visual review
- [ ] Baselined via --baseline interactive mode before committing
