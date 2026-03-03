# Test Fixtures

## main/
Active evaluation corpus for the Flowdoc pipeline. HTML source files,
manifest, and eval baselines. Managed by the eval harness
(eval/run_metrics.py). See docs/flowdoc-eval-cheatsheet.md for usage.

## input/ (legacy)
Original 10 exploratory fixtures from early development (identity10).
Superseded by main/ for eval purposes. Retained because unit tests
reference these files directly.

## user-study/ (legacy)
10 fixtures from Phase 2 evaluation (eval20). Superseded by main/
for eval purposes. Retained because unit tests reference these files
directly.
