# Pipeline Audit

Automated metrics runner. Separate from pytest.

## Usage

  python tests/pipeline-audit/run_metrics.py --select-corpus main
  python tests/pipeline-audit/run_metrics.py --select-corpus main --select-fixture nhs-dyslexia
  python tests/pipeline-audit/run_metrics.py --select-corpus main --interactive-baseline
  python tests/pipeline-audit/run_metrics.py --select-corpus main --quality-json-report

## Statuses

  PASS        Metrics within thresholds, matches baseline.
  REGRESSION  Threshold violation or metric drop vs PASS baseline.
  MARGINAL    Baseline approved in a known-imperfect state.
              Stable MARGINAL is not a regression.
  FAIL        Pipeline error.
  NEW         No baseline exists yet.

## Adding Fixtures

1. Add HTML file to tests/pipeline-audit/test-pages/
2. Add a row to tests/pipeline-audit/manifest.md
3. Run: python tests/pipeline-audit/run_metrics.py --select-corpus main --interactive-baseline
   Only fixtures without a baseline will be presented for review.

## Full Reference

See docs/decant-eval-cheatsheet.md for complete usage guide.
