"""
Basic CLI tests.

Validates argument parsing and basic I/O flow.
"""
import sys
from io import StringIO
from flowdoc.cli.main import main


def test_cli_file_to_file(tmp_path):
    """CLI converts file to file."""
    # Create input file
    input_file = tmp_path / "input.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")
    
    output_file = tmp_path / "output.html"
    
    # Run CLI
    sys.argv = ['flowdoc', str(input_file), '-o', str(output_file)]
    
    try:
        main()
    except SystemExit as e:
        assert e.code == 0
    
    # Verify output exists and has content
    assert output_file.exists()
    output_html = output_file.read_text()
    assert "<h1>" in output_html
    assert "Content" in output_html


def test_cli_default_output_naming(tmp_path):
    """CLI uses default .flowdoc.html naming."""
    input_file = tmp_path / "test.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")
    
    # Run without -o
    sys.argv = ['flowdoc', str(input_file)]
    
    try:
        main()
    except SystemExit as e:
        assert e.code == 0
    
    # Check default output file
    expected_output = tmp_path / "test.flowdoc.html"
    assert expected_output.exists()


def test_cli_exits_1_on_validation_error(tmp_path):
    """CLI exits with code 1 for validation errors."""
    input_file = tmp_path / "invalid.html"
    input_file.write_text("<html><body><p>No headings</p></body></html>")
    
    output_file = tmp_path / "output.html"
    
    sys.argv = ['flowdoc', str(input_file), '-o', str(output_file)]
    
    try:
        main()
    except SystemExit as e:
        assert e.code == 1


def test_cli_exits_3_on_io_error():
    """CLI exits with code 3 for I/O errors."""
    sys.argv = ['flowdoc', '/nonexistent/file.html', '-o', '/tmp/out.html']
    
    try:
        main()
    except SystemExit as e:
        assert e.code == 3