"""
Extraction mode trial runner.

Runs all 10 user-study fixtures through baseline, precision, and recall
extraction modes and prints a summary table.

Columns:
  fixture     - filename stem
  mode        - baseline | precision | recall
  chars       - len() of the string returned by extract_with_trafilatura()
                (post-Trafilatura call, pre-sanitize; consistent across all rows)
  paragraphs  - count of top-level Paragraph blocks in sections after full parse
                (0 on REJECT because parse raises ValidationError before model is built)
  status      - ACCEPT or REJECT
  reason      - empty on ACCEPT; validation error message or exception text on REJECT

Exit code: always 0 (reporting tool only).

Fixture discovery: resolved relative to this file's location, not CWD.

Usage:
    python scripts/extraction_trial.py
    python -m scripts.extraction_trial   (from repo root)
"""
import pathlib
import sys

# Resolve repo root relative to this file so the script runs correctly
# regardless of which directory it is invoked from.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import trafilatura as _traf

from flowdoc.core.parser import extract_with_trafilatura, parse, ValidationError
from flowdoc.core.model import Paragraph

FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures" / "user-study"

# Per-mode Trafilatura kwargs: single source of truth for both dispatch
# (passed to extract_with_trafilatura) and the printed header.
# "baseline" kwargs are identical to the pre-ExtractionMode hardcoded call.
_MODE_KWARGS: dict[str, dict] = {
    "baseline":  {"favor_precision": True,  "favor_recall": False, "no_fallback": False},
    "precision": {"favor_precision": True,  "favor_recall": False, "no_fallback": True},
    "recall":    {"favor_precision": False, "favor_recall": True,  "no_fallback": False},
}

MODES = tuple(_MODE_KWARGS)


def count_paragraphs(doc) -> int:
    """Count top-level Paragraph blocks across all sections in a Document."""
    return sum(
        1
        for section in doc.sections
        for block in section.blocks
        if isinstance(block, Paragraph)
    )


def run_fixture(html: str, mode: str) -> dict:
    """
    Run one fixture through extraction + parse for a given mode.

    Returns a dict with keys: chars, paragraphs, status, reason.
    """
    extracted = extract_with_trafilatura(html, extraction_mode=mode)
    chars = len(extracted)

    try:
        # parse() sanitizes, selects content, validates, and builds the model.
        # original_title is not captured here; this is a diagnostic tool.
        doc = parse(extracted)
        paragraphs = count_paragraphs(doc)
        return dict(chars=chars, paragraphs=paragraphs, status="ACCEPT", reason="")
    except ValidationError as e:
        return dict(chars=chars, paragraphs=0, status="REJECT", reason=str(e))
    except Exception as e:
        return dict(chars=chars, paragraphs=0, status="REJECT", reason=f"Error: {e}")


def print_header():
    """Print run metadata: Trafilatura version and per-mode kwargs."""
    traf_version = getattr(_traf, "__version__", "unknown")
    print(f"trafilatura {traf_version}")
    print("extraction mode kwargs:")
    for mode, kwargs in _MODE_KWARGS.items():
        kw_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"  {mode:<9}  {kw_str}")
    print()


def main():
    fixture_paths = sorted(FIXTURE_DIR.glob("*.html"))
    if not fixture_paths:
        print(f"ERROR: No fixtures found in {FIXTURE_DIR}", file=sys.stderr)
        sys.exit(0)

    print_header()

    # Column widths
    w_fix = max(len(p.stem) for p in fixture_paths)
    w_fix = max(w_fix, 11)  # min width for "fixture" header
    w_mode = 9
    w_chars = 7
    w_para = 10
    w_status = 6

    header = (
        f"{'fixture':<{w_fix}}  {'mode':<{w_mode}}  {'chars':>{w_chars}}  "
        f"{'paragraphs':>{w_para}}  {'status':<{w_status}}  reason"
    )
    sep = "-" * len(header)

    print(header)
    print(sep)

    for fixture_path in fixture_paths:
        html = fixture_path.read_text(encoding="utf-8")
        for mode in MODES:
            result = run_fixture(html, mode)
            print(
                f"{fixture_path.stem:<{w_fix}}  "
                f"{mode:<{w_mode}}  "
                f"{result['chars']:>{w_chars}}  "
                f"{result['paragraphs']:>{w_para}}  "
                f"{result['status']:<{w_status}}  "
                f"{result['reason']}"
            )
        print()  # blank line between fixtures


if __name__ == "__main__":
    main()
