"""
HTML input reader.

Handles file and stdin input for CLI.
"""
import sys


def read_html(input_path: str | None) -> str:
    """
    Read HTML from file or stdin.
    
    Args:
        input_path: Path to HTML file, or None for stdin
        
    Returns:
        HTML string
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        IOError: If read fails
    """
    if input_path:
        # Read from file
        with open(input_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        # Read from stdin
        if sys.stdin.isatty():
            raise IOError("No input provided (stdin is a TTY)")
        return sys.stdin.read()