"""
Flowdoc CLI entry point.

Provides convert command for HTML to readable HTML conversion.
"""
import argparse
import sys

from flowdoc.core.parser import parse, ValidationError
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
        
        # Parse to model
        document = parse(html_input)
              
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