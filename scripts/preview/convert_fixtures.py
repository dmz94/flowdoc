"""
Dev tool: batch convert all fixture HTML files.

Runs the full Flowdoc pipeline on every .html file in tests/fixtures/input/
and writes .flowdoc.html output alongside each input file.

Usage (from project root with venv active):
    python scripts/preview/convert_fixtures.py

Output files are written to tests/fixtures/input/ alongside inputs.
Open them directly in a browser to inspect visually.
"""
from pathlib import Path
from bs4 import BeautifulSoup

from flowdoc.core.content_selector import detect_mode
from flowdoc.core.parser import parse, extract_with_trafilatura, ValidationError
from flowdoc.core.renderer import render

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "input"


def convert_fixture(input_path: Path) -> None:
    html = input_path.read_text(encoding="utf-8")

    mode = detect_mode(html)

    original_title = None
    html_to_parse = html

    if mode == "extract":
        original_soup = BeautifulSoup(html, "lxml")
        original_title = original_soup.find("title")
        html_to_parse = extract_with_trafilatura(html)

    doc = parse(html_to_parse, original_title=original_title)
    output = render(doc)

    output_path = input_path.with_suffix(".flowdoc.html")
    output_path.write_text(output, encoding="utf-8")
    print(f"  OK  [{mode}]  {output_path.name}")


def main():
    fixtures = sorted(FIXTURE_DIR.glob("*.html"))
    # Skip already-converted files
    fixtures = [f for f in fixtures if ".flowdoc." not in f.name]

    print(f"Converting {len(fixtures)} fixtures from {FIXTURE_DIR}\n")

    passed = 0
    failed = 0

    for fixture in fixtures:
        try:
            convert_fixture(fixture)
            passed += 1
        except ValidationError as e:
            print(f"  SKIP [validation]  {fixture.name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL [error]       {fixture.name}: {e}")
            failed += 1

    print(f"\n{passed} converted, {failed} skipped/failed.")


if __name__ == "__main__":
    main()
