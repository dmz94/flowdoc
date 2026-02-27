"""
Flowdoc CLI entry point.

Provides convert command for HTML to readable HTML conversion.
"""
import argparse
import sys

from flowdoc.core.content_selector import detect_mode
from flowdoc.core.parser import parse, extract_with_trafilatura, ValidationError
from flowdoc.core.renderer import render
from flowdoc.io.reader import read_html
from flowdoc.io.writer import write_html


def main():
    """
    Main CLI entry point.

    Exit codes:
    - 0: Success
    - 1: Validation/parse error
    - 2: Render error
    - 3: I/O error
    """
    parser = argparse.ArgumentParser(
        prog='flowdoc',
        description='Convert semantic HTML to dyslexia-friendly readable HTML'
    )

    parser.add_argument(
        'input',
        nargs='?',
        help='Input HTML file (omit for stdin)'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: <input>.flowdoc.html or stdout)'
    )

    parser.add_argument(
        '--font',
        choices=['opendyslexic'],
        help='Use alternative font (opendyslexic)'
    )

    parser.add_argument(
        '--mode',
        choices=['transform', 'extract', 'auto'],
        default='auto',
        help=(
            'Processing mode (default: auto). '
            'transform: fidelity-first, no boilerplate removal. '
            'extract: boilerplate removal via Trafilatura, formatting best-effort. '
            'auto: detect mode from input (defaults to transform when ambiguous).'
        )
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print processing decisions to stderr'
    )

    args = parser.parse_args()

    # Determine input/output paths
    input_path = args.input
    output_path = args.output

    # If no output specified and reading from file, use default naming
    if not output_path and input_path:
        if input_path.endswith('.html'):
            output_path = input_path.replace('.html', '.flowdoc.html')
        else:
            output_path = input_path + '.flowdoc.html'

    # Font flag
    use_opendyslexic = args.font == 'opendyslexic'

    try:
        # Read input
        html_input = read_html(input_path)

        # Determine mode
        if args.mode == 'auto':
            mode = detect_mode(html_input)
            if args.verbose:
                print(f"Mode: {mode} (auto-detected)", file=sys.stderr)
        else:
            mode = args.mode
            if args.verbose:
                print(f"Mode: {mode} (explicit)", file=sys.stderr)

        # Route to appropriate pipeline
        original_title = None
        if mode == 'extract':
            # Capture title before Trafilatura strips <head>
            from bs4 import BeautifulSoup
            original_soup = BeautifulSoup(html_input, "lxml")
            original_title = original_soup.find("title")

            if args.verbose:
                print("Extract mode: running Trafilatura boilerplate removal", file=sys.stderr)

            html_input = extract_with_trafilatura(html_input)

            if args.verbose:
                print("Extract mode: boilerplate removal complete", file=sys.stderr)
        else:
            if args.verbose:
                print("Transform mode: fidelity-first parsing, no boilerplate removal", file=sys.stderr)

        # Parse to model
        document = parse(
            html_input,
            original_title=original_title,
            require_article_body=(mode == "extract"),
        )

        # Render to readable HTML
        html_output = render(document, use_opendyslexic=use_opendyslexic)

        # Write output
        write_html(html_output, output_path)

        # Success
        sys.exit(0)

    except IOError as e:
        print(f"I/O error: {e}", file=sys.stderr)
        sys.exit(3)
    except ValidationError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
