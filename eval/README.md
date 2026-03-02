# Flowdoc Eval

Automated metrics runner. Separate from pytest.

Usage:
  python eval/run_metrics.py --corpus identity10
  python eval/run_metrics.py --corpus eval20
  python eval/run_metrics.py --corpus identity10 --fixture 01_nhs_dyslexia
  python eval/run_metrics.py --corpus identity10 --baseline
  python eval/run_metrics.py --corpus identity10 --report

See sonnet-metrics-prompt.md for full design spec.
