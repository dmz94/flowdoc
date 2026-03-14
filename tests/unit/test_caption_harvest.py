"""
Tests for image caption support: harvest_captions, parse_figure, caption_map
threading, and renderer figure/figcaption output.
"""
from decant.core.model import Document, Section, Heading, Paragraph, Image, Text
from decant.core.parser import harvest_captions, parse
from decant.core.renderer import render


# ---------------------------------------------------------------------------
# harvest_captions unit tests
# ---------------------------------------------------------------------------

def test_harvest_figure_with_img_and_figcaption():
    """Figure with one img and figcaption yields a caption entry."""
    html = '<figure><img src="https://example.com/photo.jpg" alt="Photo"><figcaption>A photo caption</figcaption></figure>'
    result = harvest_captions(html)
    assert result == {"https://example.com/photo.jpg": "A photo caption"}


def test_harvest_figure_no_figcaption():
    """Figure without figcaption yields empty dict."""
    html = '<figure><img src="https://example.com/photo.jpg"></figure>'
    result = harvest_captions(html)
    assert result == {}


def test_harvest_figure_empty_figcaption():
    """Figure with whitespace-only figcaption is skipped."""
    html = '<figure><img src="https://x.com/a.jpg"><figcaption>  </figcaption></figure>'
    result = harvest_captions(html)
    assert result == {}


def test_harvest_figure_multiple_imgs_skipped():
    """Figure with multiple http imgs is ambiguous and skipped."""
    html = '<figure><img src="https://x.com/a.jpg"><img src="https://x.com/b.jpg"><figcaption>Which one?</figcaption></figure>'
    result = harvest_captions(html)
    assert result == {}


def test_harvest_figure_no_img():
    """Figure with no img is skipped."""
    html = '<figure><figcaption>Orphan caption</figcaption></figure>'
    result = harvest_captions(html)
    assert result == {}


def test_harvest_figure_data_src_skipped():
    """Figure with data URI img is skipped (not http/https)."""
    html = '<figure><img src="data:image/png;base64,abc"><figcaption>Data URI</figcaption></figure>'
    result = harvest_captions(html)
    assert result == {}


def test_harvest_multiple_figures():
    """Multiple valid figures each produce a caption entry."""
    html = """
    <figure><img src="https://x.com/a.jpg" alt="A"><figcaption>Caption A</figcaption></figure>
    <figure><img src="https://x.com/b.jpg" alt="B"><figcaption>Caption B</figcaption></figure>
    """
    result = harvest_captions(html)
    assert len(result) == 2
    assert result["https://x.com/a.jpg"] == "Caption A"
    assert result["https://x.com/b.jpg"] == "Caption B"


def test_harvest_no_figures():
    """HTML with no figures yields empty dict."""
    html = "<p>Just a paragraph</p>"
    result = harvest_captions(html)
    assert result == {}


# ---------------------------------------------------------------------------
# parse_figure (transform mode) tests
# ---------------------------------------------------------------------------

def test_figure_with_img_and_caption_transform():
    """Figure with img and figcaption produces Image with caption."""
    html = '<body><h1>T</h1><p>Text.</p><figure><img src="https://x.com/a.jpg" alt="A"><figcaption>Caption text</figcaption></figure></body>'
    doc = parse(html)
    images = [b for s in doc.sections for b in s.blocks if isinstance(b, Image)]
    assert len(images) == 1
    assert images[0].caption == "Caption text"


def test_figure_with_img_no_caption_transform():
    """Figure with img but no figcaption produces Image with empty caption."""
    html = '<body><h1>T</h1><p>Text.</p><figure><img src="https://x.com/a.jpg" alt="A"></figure></body>'
    doc = parse(html)
    images = [b for s in doc.sections for b in s.blocks if isinstance(b, Image)]
    assert len(images) == 1
    assert images[0].caption == ""


def test_figure_no_img_with_caption_transform():
    """Figure with no img but with figcaption produces Paragraph."""
    html = '<body><h1>T</h1><p>Text.</p><figure><figcaption>Orphan</figcaption></figure></body>'
    doc = parse(html)
    paras = [b for s in doc.sections for b in s.blocks if isinstance(b, Paragraph)]
    texts = [il.text for p in paras for il in p.inlines if isinstance(il, Text)]
    assert any("Orphan" in t for t in texts)


# ---------------------------------------------------------------------------
# caption_map (extract mode) tests
# ---------------------------------------------------------------------------

def test_caption_map_attaches_to_matching_image():
    """caption_map attaches caption to image with matching src."""
    html = '<body><h1>T</h1><p>Text.</p><img src="https://x.com/a.jpg" alt="A"></body>'
    caption_map = {"https://x.com/a.jpg": "Matched caption"}
    doc = parse(html, caption_map=caption_map)
    images = [b for s in doc.sections for b in s.blocks if isinstance(b, Image)]
    assert len(images) == 1
    assert images[0].caption == "Matched caption"


def test_caption_map_no_match_leaves_empty():
    """caption_map with no matching src leaves caption empty."""
    html = '<body><h1>T</h1><p>Text.</p><img src="https://x.com/a.jpg" alt="A"></body>'
    caption_map = {"https://x.com/other.jpg": "Wrong URL"}
    doc = parse(html, caption_map=caption_map)
    images = [b for s in doc.sections for b in s.blocks if isinstance(b, Image)]
    assert len(images) == 1
    assert images[0].caption == ""


def test_caption_map_none_leaves_empty():
    """No caption_map leaves caption empty."""
    html = '<body><h1>T</h1><p>Text.</p><img src="https://x.com/a.jpg" alt="A"></body>'
    doc = parse(html)
    images = [b for s in doc.sections for b in s.blocks if isinstance(b, Image)]
    assert len(images) == 1
    assert images[0].caption == ""


# ---------------------------------------------------------------------------
# Renderer tests
# ---------------------------------------------------------------------------

def test_render_image_with_caption():
    """Image with caption renders as figure with figcaption."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Image(src="https://x.com/a.jpg", alt="A", caption="Cap")]
            )
        ]
    )
    html = render(doc)
    assert "<figure>" in html
    assert "<figcaption>Cap</figcaption>" in html
    assert "</figure>" in html


def test_render_image_without_caption():
    """Image without caption renders as bare img, no figure wrapper."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Image(src="https://x.com/a.jpg", alt="A")]
            )
        ]
    )
    html = render(doc)
    assert "<figure>" not in html
    assert "<figcaption>" not in html
    assert '<img src="https://x.com/a.jpg"' in html


def test_render_image_empty_caption():
    """Image with empty caption renders as bare img, no figure wrapper."""
    doc = Document(
        title="Test",
        sections=[
            Section(
                heading=Heading(level=1, inlines=[Text(text="Title")]),
                blocks=[Image(src="https://x.com/a.jpg", alt="A", caption="")]
            )
        ]
    )
    html = render(doc)
    assert "<figure>" not in html
    assert "<figcaption>" not in html
