"""
Document model to HTML renderer.

Generates self-contained readable HTML with inline CSS.
Pipeline: Step 5 (final - after model creation)
See decisions.md section 10 for rendering invariants.
"""
import html as html_module

from flowdoc.core.model import (
    Document, Section, Heading,
    Paragraph, ListBlock, ListItem, Quote, Preformatted, Image,
    Text, Emphasis, Strong, Code, Link, LineBreak
)
from flowdoc.core.constants import (
    FONT_STACK, BODY_FONT_SIZE, HEADING_MULTIPLIERS,
    LINE_HEIGHT, LETTER_SPACING, WORD_SPACING,
    PARAGRAPH_SPACING, HEADING_MARGIN_TOP, HEADING_MARGIN_BOTTOM,
    LIST_ITEM_SPACING,
    BACKGROUND_COLOR, TEXT_COLOR, LINK_COLOR, LINK_HOVER_COLOR, LINK_VISITED_COLOR,
    MAX_LINE_WIDTH, CONTAINER_PADDING,
    PRINT_MIN_FONT_SIZE,
    OPENDYSLEXIC_BASE64,
    OPENDYSLEXIC_BOLD_BASE64
)


def render(document: Document, use_opendyslexic: bool = False) -> str:
    """
    Render Document model to self-contained HTML.
    
    Args:
        document: Document model with title and sections
        use_opendyslexic: If True, embed OpenDyslexic font
        
    Returns:
        Complete HTML string with inline CSS
    """
    css = generate_css(use_opendyslexic)
    
    # Render sections (TODO: implement next)
    sections_html = "\n".join(render_section(section) for section in document.sections)
    
    # Assemble complete HTML document
    html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html_module.escape(document.title)}</title>
<style>
{css}
</style>
</head>
<body>
<div class="container">
{sections_html}
</div>
</body>
</html>"""
    
    return html_output


def generate_css(use_opendyslexic: bool) -> str:
    """
    Generate CSS from constants.
    
    Args:
        use_opendyslexic: If True, include @font-face for OpenDyslexic
        
    Returns:
        CSS string for inline <style> block
    """
    # Font family - conditional on OpenDyslexic
    if use_opendyslexic and OPENDYSLEXIC_BASE64:
        font_family = "'OpenDyslexic', " + FONT_STACK
        font_face = f"""
@font-face {{
    font-family: 'OpenDyslexic';
    src: url(data:font/woff2;base64,{OPENDYSLEXIC_BASE64}) format('woff2');
    font-weight: normal;
    font-style: normal;
}}

@font-face {{
    font-family: 'OpenDyslexic';
    src: url(data:font/woff2;base64,{OPENDYSLEXIC_BOLD_BASE64}) format('woff2');
    font-weight: bold;
    font-style: normal;
}}
"""
    else:
        font_family = FONT_STACK
        font_face = ""
    
    # Restyle <em> as bold (not italic) for dyslexic readers (BDA guidance)
    em_restyle = ""
    if use_opendyslexic and OPENDYSLEXIC_BASE64:
        em_restyle = """
em {
    font-style: normal;
    font-weight: bold;
}
"""

    # Generate heading styles
    heading_styles = ""
    for level in range(1, 7):
        multiplier = HEADING_MULTIPLIERS[level]
        heading_styles += f"""
h{level} {{
    font-size: calc({BODY_FONT_SIZE} * {multiplier});
    margin-top: {HEADING_MARGIN_TOP};
    margin-bottom: {HEADING_MARGIN_BOTTOM};
    font-weight: bold;
}}
"""
    
    css = f"""{font_face}
* {{
    box-sizing: border-box;
}}

body {{
    font-family: {font_family};
    font-size: {BODY_FONT_SIZE};
    line-height: {LINE_HEIGHT};
    letter-spacing: {LETTER_SPACING};
    word-spacing: {WORD_SPACING};
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    margin: 0;
    padding: 0;
}}

.container {{
    max-width: {MAX_LINE_WIDTH};
    margin: 0 auto;
    padding: {CONTAINER_PADDING};
}}

{heading_styles}

p {{
    margin: 0 0 {PARAGRAPH_SPACING} 0;
    text-align: left;
}}

ul, ol {{
    margin: 0 0 {PARAGRAPH_SPACING} 0;
    padding-left: 2em;
}}

li {{
    margin-bottom: {LIST_ITEM_SPACING};
}}

blockquote {{
    margin: 0 0 {PARAGRAPH_SPACING} 2em;
    padding-left: 1em;
    border-left: 3px solid {TEXT_COLOR};
}}

pre {{
    background-color: #f5f5f5;
    padding: 1em;
    margin: 0 0 {PARAGRAPH_SPACING} 0;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
}}

code {{
    background-color: #f5f5f5;
    padding: 0.2em 0.4em;
    font-family: 'Courier New', monospace;
}}

img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 0 {PARAGRAPH_SPACING} 0;
}}

a {{
    color: {LINK_COLOR};
    text-decoration: underline;
}}

a:hover {{
    color: {LINK_HOVER_COLOR};
}}

a:visited {{
    color: {LINK_VISITED_COLOR};
}}

figure {{
    margin: 1.5em 0;
    padding: 0;
}}

figure img {{
    display: block;
    max-width: 100%;
    height: auto;
}}

figcaption {{
    font-size: 0.9em;
    color: #555;
    margin-top: 0.5em;
    line-height: 1.4;
}}

{em_restyle}
@media print {{
    body {{
        font-size: {PRINT_MIN_FONT_SIZE};
    }}
    img {{
        max-width: 100%;
        page-break-inside: avoid;
    }}
    figcaption {{
        color: #333;
    }}
}}
"""
    
    return css


def render_section(section: Section) -> str:
    """
    Render Section to HTML.
    
    Args:
        section: Section with heading and blocks
        
    Returns:
        HTML string for section
    """
    # Render heading
    level = section.heading.level
    heading_html = render_inlines(section.heading.inlines)
    heading = f"<h{level}>{heading_html}</h{level}>\n"
    
    # Render blocks
    blocks_html = "\n".join(render_block(block) for block in section.blocks)
    
    return heading + blocks_html


def render_block(block) -> str:
    """
    Render Block to HTML (dispatcher).
    
    Args:
        block: Block model object
        
    Returns:
        HTML string for block
    """
    if isinstance(block, Paragraph):
        return render_paragraph(block)
    elif isinstance(block, ListBlock):
        return render_list(block)
    elif isinstance(block, Quote):
        return render_quote(block)
    elif isinstance(block, Preformatted):
        return render_preformatted(block)
    elif isinstance(block, Image):
        return render_image(block)
    else:
        # Unknown block type - skip
        return ""


def render_paragraph(para: Paragraph) -> str:
    """
    Render Paragraph to HTML.
    
    Args:
        para: Paragraph with inlines
        
    Returns:
        HTML <p> element
    """
    content = render_inlines(para.inlines)
    return f"<p>{content}</p>\n"


def render_list(list_block: ListBlock) -> str:
    """
    Render ListBlock to HTML (handles nested lists).
    
    Args:
        list_block: ListBlock with items
        
    Returns:
        HTML <ul> or <ol> element
    """
    tag = "ol" if list_block.ordered else "ul"
    items_html = ""
    
    for item in list_block.items:
        # Render item inlines
        content = render_inlines(item.inlines)
        
        # Render nested lists if present
        nested = ""
        for child_list in item.children:
            nested += render_list(child_list)
        
        items_html += f"<li>{content}{nested}</li>\n"
    
    return f"<{tag}>\n{items_html}</{tag}>\n"


def render_quote(quote: Quote) -> str:
    """
    Render Quote to HTML (recursive).
    
    Args:
        quote: Quote containing blocks
        
    Returns:
        HTML <blockquote> element
    """
    blocks_html = "\n".join(render_block(block) for block in quote.blocks)
    return f"<blockquote>\n{blocks_html}</blockquote>\n"


def render_preformatted(pre: Preformatted) -> str:
    """
    Render Preformatted to HTML.
    
    Args:
        pre: Preformatted with text
        
    Returns:
        HTML <pre> element
    """
    escaped_text = html_module.escape(pre.text)
    return f"<pre>{escaped_text}</pre>\n"


def render_image(image: Image) -> str:
    """Render Image to HTML <img> tag, wrapped in <figure> if captioned."""
    escaped_src = html_module.escape(image.src)
    escaped_alt = html_module.escape(image.alt)
    img_tag = f'<img src="{escaped_src}" alt="{escaped_alt}">'
    if image.caption:
        escaped_caption = html_module.escape(image.caption)
        return f'<figure>{img_tag}\n<figcaption>{escaped_caption}</figcaption></figure>\n'
    return img_tag + '\n'


def render_inlines(inlines: list) -> str:
    """
    Render list of Inline elements to HTML.
    
    Args:
        inlines: List of Inline model objects
        
    Returns:
        HTML string with inline elements
    """
    return "".join(render_inline(inline) for inline in inlines)


def render_inline(inline) -> str:
    """
    Render single Inline element to HTML (dispatcher).
    
    Args:
        inline: Inline model object
        
    Returns:
        HTML string for inline element
    """
    if isinstance(inline, Text):
        return html_module.escape(inline.text)
    elif isinstance(inline, Emphasis):
        content = render_inlines(inline.children)
        return f"<em>{content}</em>"
    elif isinstance(inline, Strong):
        content = render_inlines(inline.children)
        return f"<strong>{content}</strong>"
    elif isinstance(inline, Code):
        escaped = html_module.escape(inline.text)
        return f"<code>{escaped}</code>"
    elif isinstance(inline, Link):
        escaped_href = html_module.escape(inline.href)
        content = render_inlines(inline.children)
        return f'<a href="{escaped_href}">{content}</a>'
    elif isinstance(inline, LineBreak):
        return "<br>"
    else:
        # Unknown inline type
        return ""