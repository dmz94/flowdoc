"""
HTML output writer.

Handles file and stdout output for CLI.
"""
import sys


def write_html(html: str, output_path: str | None) -> None:
    """
    Write HTML to file or stdout.
    
    Args:
        html: HTML string to write
        output_path: Path to output file, or None for stdout
        
    Raises:
        IOError: If write fails
    """
    if output_path:
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    else:
        # Write to stdout
        sys.stdout.write(html)