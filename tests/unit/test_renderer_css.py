"""
Tests for renderer CSS generation.

Part 1 of renderer tests - validates CSS generation from constants.
"""
from decant.core.renderer import generate_css
from decant.core.constants import FONT_STACK, BODY_FONT_SIZE, BACKGROUND_COLOR


def test_generates_basic_css():
    """CSS includes basic typography rules."""
    css = generate_css(use_opendyslexic=False)
    assert FONT_STACK in css
    assert BODY_FONT_SIZE in css
    assert BACKGROUND_COLOR in css


def test_generates_heading_styles():
    """CSS includes styles for all heading levels."""
    css = generate_css(use_opendyslexic=False)
    for level in range(1, 7):
        assert f"h{level}" in css


def test_includes_print_styles():
    """CSS includes print media query."""
    css = generate_css(use_opendyslexic=False)
    assert "@media print" in css


def test_no_font_face_without_opendyslexic():
    """Does not include @font-face when OpenDyslexic not used."""
    css = generate_css(use_opendyslexic=False)
    assert "@font-face" not in css
    assert "OpenDyslexic" not in css


def test_includes_font_face_with_opendyslexic():
    """Includes @font-face when OpenDyslexic requested (if base64 present)."""
    css = generate_css(use_opendyslexic=True)
    # If OPENDYSLEXIC_BASE64 is empty (v1 placeholder), font-face won't be added
    # This test documents the conditional behavior
    from decant.core.constants import OPENDYSLEXIC_BASE64
    if OPENDYSLEXIC_BASE64:
        assert "@font-face" in css
        assert "OpenDyslexic" in css
    else:
        # Placeholder is empty - no font-face added
        assert "@font-face" not in css