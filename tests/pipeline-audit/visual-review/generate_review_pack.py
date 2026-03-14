"""
Generate a self-contained review pack for non-technical reviewers.

Creates a folder of converted articles (system font + OpenDyslexic variants)
with index pages linking to each article and its original source URL.
The folder can be zipped and sent to reviewers who just open index.html.

Usage (from project root with venv active):
    python tests/pipeline-audit/visual-review/generate_review_pack.py
"""
from pathlib import Path

from bs4 import BeautifulSoup

from decant.core.content_selector import detect_mode
from decant.core.parser import parse, extract_with_trafilatura, ValidationError
from decant.core.renderer import render

SCRIPT_DIR = Path(__file__).resolve().parent
AUDIT_DIR = SCRIPT_DIR.parent
FIXTURE_DIR = AUDIT_DIR / "test-pages"
MANIFEST_PATH = AUDIT_DIR / "manifest.md"
OUTPUT_DIR = SCRIPT_DIR / "review-pack"
ARTICLES_DIR = OUTPUT_DIR / "articles"

# Fixtures to include in the review pack.
FIXTURES = [
    "espn-jalen-ramsey",
    "yale360-baboons",
    "smithsonian-homo-sapiens",
    "ghost-accessibility-blog",
    "nhs-couch-to-5k",
    "nhs-mindfulness",
    "pbs-crowd-surges",
    "undark-brain-organoids",
    "propublica-3m-pfas",
    "additude-adhd-in-children",
]

# Human-readable labels for the index page.
LABELS = {
    "espn-jalen-ramsey": "Jalen Ramsey (ESPN)",
    "yale360-baboons": "Cape Town Baboons (Yale e360)",
    "smithsonian-homo-sapiens": "Evolution of Homo Sapiens (Smithsonian)",
    "ghost-accessibility-blog": "My Journey to Ghost (Marco Zehe)",
    "nhs-couch-to-5k": "Couch to 5K (NHS)",
    "nhs-mindfulness": "Mindfulness (NHS)",
    "pbs-crowd-surges": "Why Crowd Surges Kill (PBS)",
    "undark-brain-organoids": "Brain Organoids (Undark)",
    "propublica-3m-pfas": "3M Forever Chemicals (ProPublica)",
    "additude-adhd-in-children": "ADHD in Children (ADDitude)",
}

README_TEXT = """\
DECANT REVIEW PACK
====================

Decant is a tool that takes web articles and converts them
into cleaner, easier-to-read versions. It is still a work in
progress -- there are known bugs and rough edges. That is
exactly why we need your feedback.

I would really appreciate 10 minutes of your time to look at
a few articles and tell me what you think.

WHAT'S IN THIS FOLDER
---------------------
Two starting pages and a folder of converted articles.

  index.html
    Start here. Shows 10 articles. For each one you can see
    the original website and the Decant version side by side.

  index-opendyslexic.html
    Same articles, but using a font called OpenDyslexic. The
    letters are shaped to be easier to tell apart. Try this
    one too if you are curious -- some people find it more
    comfortable to read, others prefer the standard version.

WHAT TO DO
----------
1. Open index.html in your browser
2. Pick 2 or 3 articles that interest you
3. For each one, click "Original" to see the website,
   then click "Decant" to see our version
4. Read a bit of each and compare

WHAT TO EXPECT
--------------
The articles will not look like the original websites. That
is intentional -- Decant strips away the clutter and
reformats the text to be easier to read. What we care about
is whether the important content came through cleanly.

Some things you might notice that we already know about:

- Some articles may include bits of website furniture at the
  end -- navigation links, newsletter signups, related
  article sections. We are still working on trimming these.
- Some decorative images from the original site may appear
  where they should not. We are improving how we filter
  content images from site decoration.
- Not every article converts perfectly. Some websites are
  harder to extract content from than others.

Do not worry about reporting things gently. If something
looks wrong, odd, or broken -- that is exactly what we need
to hear.

WHAT WE WANT TO KNOW
---------------------
After you have looked at a few:

- Which articles did you look at?
- Is the Decant version actually easier to read than the
  original website, or just different?
- Is anything important missing or broken in the Decant
  version compared to the original?
- Did you notice anything odd -- missing images, weird
  spacing, content that looks out of place?
- How does the spacing and layout feel? Comfortable to read?
- If you tried both font versions, any preference?

Just send me your thoughts however is easiest. A few
sentences is plenty.
"""


def parse_manifest() -> dict[str, str]:
    """Parse manifest.md and return {fixture_name: source_url}."""
    urls: dict[str, str] = {}
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| #") or line.startswith("|---"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) >= 5:
            fname = cols[2].replace(".html", "")
            urls[fname] = cols[3]
    return urls


def convert_fixture(input_path: Path, use_opendyslexic: bool = False) -> str:
    """Run the Decant pipeline on a single fixture and return rendered HTML."""
    html = input_path.read_text(encoding="utf-8")
    mode = detect_mode(html)

    original_title = None
    html_to_parse = html

    if mode == "extract":
        original_soup = BeautifulSoup(html, "lxml")
        original_title = original_soup.find("title")
        html_to_parse = extract_with_trafilatura(html)

    doc = parse(html_to_parse, original_title=original_title)
    return render(doc, use_opendyslexic=use_opendyslexic)


def generate_index(urls: dict[str, str], opendyslexic: bool = False) -> str:
    """Generate the index.html or index-opendyslexic.html content."""
    if opendyslexic:
        top_text = (
            "This page shows the same articles as index.html, but "
            "using a font called OpenDyslexic. It is designed to make "
            "reading easier for people with dyslexia \u2014 the letters have "
            "weighted bottoms to help prevent them flipping or rotating. "
            "Some people find it much more comfortable; others prefer a "
            "standard font. Both reactions are completely normal.</p>\n"
            "      <p>For each article below, click 'Original' to see the website "
            "version, then click 'Decant (OpenDyslexic)' to see our "
            "converted output."
        )
        decant_col_header = "Decant (OpenDyslexic)"
        suffix = ".decant.od.html"
        bottom_questions = (
            "        <li>Which articles did you look at?</li>\n"
            "        <li>Is the Decant version actually easier to read than\n"
            "          the original website, or just different?</li>\n"
            "        <li>Is anything important missing or broken in the Decant\n"
            "          version compared to the original?</li>\n"
            "        <li>Did you notice anything odd \u2014 missing images, weird\n"
            "          spacing, content that looks out of place?</li>\n"
            "        <li>How does the spacing and layout feel? Comfortable to read?</li>\n"
            "        <li>If you tried both font versions, any preference?</li>\n"
        )
    else:
        top_text = (
            "Decant converts web articles into cleaner, more readable "
            "documents. We would love your feedback on how well it works.</p>\n"
            "      <p>For each article below, click 'Original' to see the website "
            "version, then click 'Decant' to see our converted output. "
            "Read a bit of each and let us know what you think.</p>\n"
            "      <p>This folder also contains a second version of each article "
            "using a specialist font called OpenDyslexic. If you are "
            "curious, open index-opendyslexic.html to see those."
        )
        decant_col_header = "Decant"
        suffix = ".decant.html"
        bottom_questions = (
            "        <li>Which articles did you look at?</li>\n"
            "        <li>Is the Decant version actually easier to read than\n"
            "          the original website, or just different?</li>\n"
            "        <li>Is anything important missing or broken in the Decant\n"
            "          version compared to the original?</li>\n"
            "        <li>Did you notice anything odd \u2014 missing images, weird\n"
            "          spacing, content that looks out of place?</li>\n"
            "        <li>How does the spacing and layout feel? Comfortable to read?</li>\n"
        )

    rows = ""
    for name in FIXTURES:
        label = LABELS[name]
        url = urls.get(name, "#")
        local_file = "articles/" + name + suffix
        rows += (
            f"        <tr>\n"
            f"          <td>{label}</td>\n"
            f'          <td><a href="{url}" target="_blank">Original</a></td>\n'
            f'          <td><a href="{local_file}">{decant_col_header}</a></td>\n'
            f"        </tr>\n"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Decant Review Pack</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      background: #f5f5f5;
      color: #222;
      line-height: 1.6;
      margin: 0;
      padding: 2rem 1rem;
    }}
    .container {{
      max-width: 720px;
      margin: 0 auto;
      background: #fff;
      border-radius: 8px;
      padding: 2rem 2.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    h1 {{
      font-size: 1.5rem;
      margin-top: 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.5rem 0;
    }}
    th, td {{
      text-align: left;
      padding: 0.6rem 0.8rem;
      border-bottom: 1px solid #e0e0e0;
    }}
    th {{
      font-weight: 600;
      border-bottom: 2px solid #ccc;
    }}
    a {{
      color: #0051a5;
    }}
    a:visited {{
      color: #551a8b;
    }}
    ol {{
      padding-left: 1.2em;
    }}
    li {{
      margin-bottom: 0.4em;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Decant Review Pack</h1>

    <section>
      <p>{top_text}</p>
      <p>Note: Decant is still a work in progress. You may spot
        rough edges \u2014 bits of website furniture leaking through,
        decorative images that should not be there, or sections
        that feel out of place. That is expected, and your
        feedback helps us fix it.</p>
    </section>

    <section>
      <table>
        <thead>
          <tr>
            <th>Article</th>
            <th>Original</th>
            <th>{decant_col_header}</th>
          </tr>
        </thead>
        <tbody>
{rows}        </tbody>
      </table>
    </section>

    <section>
      <p>After reading a few articles, we'd appreciate your thoughts:</p>
      <ol>
{bottom_questions}      </ol>
      <p>Just send me your thoughts however is easiest. A few
        sentences is plenty.</p>
    </section>
  </div>
</body>
</html>
"""


def main():
    urls = parse_manifest()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating review pack in {OUTPUT_DIR}\n")

    converted = 0
    failed = 0

    for name in FIXTURES:
        input_path = FIXTURE_DIR / f"{name}.html"
        if not input_path.exists():
            print(f"  MISSING  {name}.html")
            failed += 1
            continue

        # Standard font variant
        try:
            output = convert_fixture(input_path, use_opendyslexic=False)
            out_path = ARTICLES_DIR / f"{name}.decant.html"
            out_path.write_text(output, encoding="utf-8")
            print(f"  OK  {out_path.name}")
            converted += 1
        except (ValidationError, Exception) as e:
            print(f"  FAIL  {name}.decant.html: {e}")
            failed += 1

        # OpenDyslexic variant
        try:
            output = convert_fixture(input_path, use_opendyslexic=True)
            out_path = ARTICLES_DIR / f"{name}.decant.od.html"
            out_path.write_text(output, encoding="utf-8")
            print(f"  OK  {out_path.name}")
            converted += 1
        except (ValidationError, Exception) as e:
            print(f"  FAIL  {name}.decant.od.html: {e}")
            failed += 1

    # Generate index files
    index_html = generate_index(urls, opendyslexic=False)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"  OK  index.html")

    index_od_html = generate_index(urls, opendyslexic=True)
    (OUTPUT_DIR / "index-opendyslexic.html").write_text(index_od_html, encoding="utf-8")
    print(f"  OK  index-opendyslexic.html")

    # Generate README.txt
    (OUTPUT_DIR / "README.txt").write_text(README_TEXT, encoding="utf-8")
    print(f"  OK  README.txt")

    top_files = len(list(OUTPUT_DIR.glob("*"))) - 1  # exclude articles/ dir
    article_files = len(list(ARTICLES_DIR.glob("*.html")))
    print(f"\n{converted} articles converted, {failed} failed.")
    print(f"{top_files} files + articles/ ({article_files} files) in {OUTPUT_DIR.name}/")


if __name__ == "__main__":
    main()
