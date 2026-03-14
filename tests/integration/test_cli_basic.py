"""
Basic CLI tests.

Validates argument parsing and basic I/O flow.
"""
import sys
from decant.cli.main import main


def test_cli_file_to_file(tmp_path):
    """CLI converts file to file."""
    input_file = tmp_path / "input.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

    output_file = tmp_path / "output.html"

    sys.argv = ['decant', str(input_file), '-o', str(output_file)]

    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    assert output_file.exists()
    output_html = output_file.read_text()
    assert "<h1>" in output_html
    assert "Content" in output_html


def test_cli_default_output_naming(tmp_path):
    """CLI uses default .decant.html naming."""
    input_file = tmp_path / "test.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

    sys.argv = ['decant', str(input_file)]

    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    expected_output = tmp_path / "test.decant.html"
    assert expected_output.exists()


def test_cli_exits_1_on_validation_error(tmp_path):
    """CLI exits with code 1 for validation errors."""
    input_file = tmp_path / "invalid.html"
    input_file.write_text("<html><body><p>No headings</p></body></html>")

    output_file = tmp_path / "output.html"

    sys.argv = ['decant', str(input_file), '-o', str(output_file)]

    try:
        main()
    except SystemExit as e:
        assert e.code == 1


def test_cli_exits_3_on_io_error():
    """CLI exits with code 3 for I/O errors."""
    sys.argv = ['decant', '/nonexistent/file.html', '-o', '/tmp/out.html']

    try:
        main()
    except SystemExit as e:
        assert e.code == 3


def test_cli_mode_transform(tmp_path):
    """--mode transform flag is accepted and exits 0."""
    input_file = tmp_path / "input.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

    output_file = tmp_path / "output.html"

    sys.argv = ['decant', str(input_file), '-o', str(output_file), '--mode', 'transform']

    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    assert output_file.exists()


def test_cli_mode_extract(tmp_path):
    """--mode extract flag is accepted and exits 0."""
    input_file = tmp_path / "input.html"
    # Paragraph needs >= 20 words to pass the extract-mode article body guard.
    prose = "This is a test article with enough prose words to satisfy the minimum article body word count required by the extract mode article body guard check."
    input_file.write_text(f"<html><body><h1>Test</h1><p>{prose}</p></body></html>")

    output_file = tmp_path / "output.html"

    sys.argv = ['decant', str(input_file), '-o', str(output_file), '--mode', 'extract']

    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    assert output_file.exists()


def test_cli_mode_auto(tmp_path):
    """--mode auto flag is accepted and exits 0."""
    input_file = tmp_path / "input.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

    output_file = tmp_path / "output.html"

    sys.argv = ['decant', str(input_file), '-o', str(output_file), '--mode', 'auto']

    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    assert output_file.exists()


def test_cli_verbose_flag(tmp_path, capsys):
    """--verbose prints mode decision to stderr."""
    input_file = tmp_path / "input.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

    output_file = tmp_path / "output.html"

    sys.argv = ['decant', str(input_file), '-o', str(output_file), '--verbose']

    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "Mode:" in captured.err


def test_cli_font_opendyslexic(tmp_path):
    """--font opendyslexic embeds the OpenDyslexic @font-face."""
    input_file = tmp_path / "input.html"
    input_file.write_text("<html><body><h1>Test</h1><p>Content</p></body></html>")

    output_file = tmp_path / "output.html"

    sys.argv = ['decant', str(input_file), '-o', str(output_file), '--font', 'opendyslexic']

    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    output_html = output_file.read_text(encoding="utf-8")
    assert "@font-face" in output_html
    assert "OpenDyslexic" in output_html


def test_cli_source_url_flag(tmp_path):
    """--source-url adds View original links to placeholders."""
    input_file = tmp_path / "input.html"
    input_file.write_text(
        "<html><body><h1>Test</h1>"
        "<table><tr><td>A</td></tr></table>"
        "<p>Content here.</p></body></html>"
    )
    output_file = tmp_path / "output.html"
    sys.argv = [
        'decant', str(input_file),
        '-o', str(output_file),
        '--source-url', 'https://example.com/article',
    ]
    try:
        main()
    except SystemExit as e:
        assert e.code == 0
    output = output_file.read_text()
    assert "View original" in output
    assert "https://example.com/article" in output
    assert '<div class="decant-notice">' in output
