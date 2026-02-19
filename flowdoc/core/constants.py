"""
Typography and layout constants for readable HTML output.

All values are based on BDA Style Guide recommendations and WCAG AA standards.
See research_typography_guidelines.md for evidence and decisions.md for contracts.
"""

# === Typography ===

FONT_STACK: str = "Arial, Verdana, sans-serif"
BODY_FONT_SIZE: str = "18px"

# Heading size multipliers (applied to body font size)
# h1 = 2.0x, h2 = 1.75x, h3 = 1.5x, h4 = 1.25x, h5 = 1.1x, h6 = 1.0x
HEADING_MULTIPLIERS: dict[int, float] = {
    1: 2.0,
    2: 1.75,
    3: 1.5,
    4: 1.25,
    5: 1.1,
    6: 1.0,
}


# === Spacing ===

LINE_HEIGHT: str = "1.5"
LETTER_SPACING: str = "0.02em"  # ~35% of average letter width (BDA guideline)
WORD_SPACING: str = "0.16em"  # 3.5x letter spacing (BDA guideline)

PARAGRAPH_SPACING: str = "1.5em"  # Space between paragraphs
HEADING_MARGIN_TOP: str = "2em"  # Space before headings
HEADING_MARGIN_BOTTOM: str = "0.75em"  # Space after headings

LIST_ITEM_SPACING: str = "0.5em"  # Space between list items


# === Colors ===

BACKGROUND_COLOR: str = "#faf8f3"  # Cream/off-white (reduces glare)
TEXT_COLOR: str = "#1a1a1a"  # Near-black (WCAG AA compliant on cream)

LINK_COLOR: str = "#0051a5"  # Blue with sufficient contrast
LINK_HOVER_COLOR: str = "#003d7a"  # Darker blue for hover state
LINK_VISITED_COLOR: str = "#551a8b"  # Purple for visited links


# === Layout ===

MAX_LINE_WIDTH: str = "70ch"  # 60-70 characters (BDA recommendation)
CONTAINER_PADDING: str = "2rem"  # Padding around content


# === Print Styles ===

PRINT_MIN_FONT_SIZE: str = "12pt"  # Do not shrink below 12pt (BDA minimum)


# === OpenDyslexic Font (v1 placeholder) ===

# TODO: Before v1 release, embed actual OpenDyslexic font as base64 string
# Font must be embedded to keep output self-contained when --font opendyslexic is used
# Download from: https://opendyslexic.org/
# Convert to base64: base64 -w 0 OpenDyslexic-Regular.woff2
# This placeholder allows renderer to be written and tested with system fonts first

OPENDYSLEXIC_BASE64: str = ""