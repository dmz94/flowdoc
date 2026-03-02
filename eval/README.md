# Flowdoc Eval

Automated metrics runner. Separate from pytest.

## Usage

  python eval/run_metrics.py --corpus main
  python eval/run_metrics.py --corpus main --fixture 01_nhs_dyslexia
  python eval/run_metrics.py --corpus main --baseline
  python eval/run_metrics.py --corpus main --report

## Statuses

  PASS        Metrics within thresholds, matches baseline.
  REGRESSION  Threshold violation or metric drop vs PASS baseline.
  MARGINAL    Baseline approved in a known-imperfect state.
              Stable MARGINAL is not a regression.
  FAIL        Pipeline error.
  NEW         No baseline exists yet.

## Adding Fixtures

1. Add HTML file to tests/fixtures/main/
2. Add a row to tests/fixtures/main/manifest.md
3. Run: python eval/run_metrics.py --corpus main --baseline
   Only fixtures without a baseline will be presented for review.

## Full Reference

See docs/flowdoc-eval-cheatsheet.md for complete usage guide.
