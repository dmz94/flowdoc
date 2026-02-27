"""Fetch HTML pages for user study testing."""
import os
import requests

DEST = os.path.dirname(os.path.abspath(__file__))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

PAGES = [
    ("https://www.skysports.com/football/news/11095/13511444/home-advantage-is-on-the-wane-in-the-premier-league-between-the-lines", "skysports.html"),
    ("https://www.theringer.com/2024/07/25/olympics/chase-budinger-paris-2024-olympics-beach-volleyball", "theringer.html"),
    ("https://www.smithsonianmag.com/science-nature/essential-timeline-understanding-evolution-homo-sapiens-180976807/", "smithsonian.html"),
    ("https://aeon.co/essays/how-the-harsh-icy-world-of-snowball-earth-shaped-life-today", "aeon.html"),
    ("https://www.theguardian.com/food/2020/feb/13/how-ultra-processed-food-took-over-your-shopping-basket-brazil-carlos-monteiro", "guardian.html"),
    ("https://www.eater.com/dining-out/919418/lisbon-pastel-de-nata-tourism-gentrification-portugal", "eater.html"),
    ("https://www.pbs.org/newshour/arts/explainer-here-is-why-crowd-surges-can-kill-people", "pbs.html"),
    ("https://www.propublica.org/article/3m-forever-chemicals-pfas-pfos-inside-story", "propublica.html"),
    ("https://www.nhs.uk/conditions/dyslexia/", "nhs.html"),
    ("https://www.cdc.gov/west-nile-virus/symptoms-diagnosis-treatment/index.html", "cdc.html"),
]

MIN_SIZE = 10 * 1024  # 10 KB

results = []
for url, filename in PAGES:
    path = os.path.join(DEST, filename)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        html = resp.text
        size = len(html.encode("utf-8"))
        if resp.status_code != 200:
            status = f"FETCH FAILED (HTTP {resp.status_code})"
            results.append((filename, status, size))
        elif size < MIN_SIZE:
            status = f"FETCH FAILED (only {size} bytes - too short)"
            results.append((filename, status, size))
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            status = f"OK ({size // 1024} KB)"
            results.append((filename, status, size))
    except Exception as e:
        results.append((filename, f"FETCH FAILED ({e})", 0))

print("\n=== FETCH RESULTS ===")
for filename, status, _ in results:
    print(f"  {filename:<22} {status}")
print()
