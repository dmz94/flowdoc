"""
Tests for typography and layout constants.

Validates that constants exist, have correct types, and are properly formatted.
"""
from flowdoc.core.constants import (
    FONT_STACK, BODY_FONT_SIZE, HEADING_MULTIPLIERS,
    LINE_HEIGHT, LETTER_SPACING, WORD_SPACING,
    BACKGROUND_COLOR, TEXT_COLOR, LINK_COLOR,
    MAX_LINE_WIDTH, CONTAINER_PADDING,
    PRINT_MIN_FONT_SIZE, OPENDYSLEXIC_BASE64
)


def test_typography_constants_exist():
    """Typography constants are defined and are strings."""
    assert isinstance(FONT_STACK, str)
    assert isinstance(BODY_FONT_SIZE, str)
    assert BODY_FONT_SIZE.endswith("px")


def test_spacing_constants_exist():
    """Spacing constants are defined with proper units."""
    assert isinstance(LINE_HEIGHT, str)
    assert isinstance(LETTER_SPACING, str)
    assert isinstance(WORD_SPACING, str)
    assert LETTER_SPACING.endswith("em")
    assert WORD_SPACING.endswith("em")


def test_color_format_valid():
    """Colors are valid hex codes."""
    colors = [BACKGROUND_COLOR, TEXT_COLOR, LINK_COLOR]
    for color in colors:
        assert color.startswith("#")
        assert len(color) == 7  # #rrggbb format
        # Verify hex characters after #
        assert all(c in "0123456789abcdefABCDEF" for c in color[1:])


def test_heading_multipliers_complete():
    """Heading multipliers cover all levels 1-6."""
    assert isinstance(HEADING_MULTIPLIERS, dict)
    assert set(HEADING_MULTIPLIERS.keys()) == {1, 2, 3, 4, 5, 6}
    # All values should be positive floats
    for level, multiplier in HEADING_MULTIPLIERS.items():
        assert isinstance(multiplier, float)
        assert multiplier > 0


def test_layout_constants_valid():
    """Layout constants have proper units."""
    assert MAX_LINE_WIDTH.endswith("ch")
    assert CONTAINER_PADDING.endswith("rem")
    assert PRINT_MIN_FONT_SIZE.endswith("pt")


def test_opendyslexic_base64_exists():
    """OpenDyslexic base64 font data is present and non-empty."""
    assert isinstance(OPENDYSLEXIC_BASE64, str)
    assert len(OPENDYSLEXIC_BASE64) > 0