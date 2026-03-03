# scripts/corpus/

Tools for managing Flowdoc test fixture corpora.

## Scripts

**fetch_corpus.py** -- Download HTML fixtures from their source URLs.

    python scripts/corpus/fetch_corpus.py                  # fetch all corpora
    python scripts/corpus/fetch_corpus.py --corpus input   # fetch one corpus

Available corpora: `input`, `user-study`. Includes polite 1-second
delay between requests. Requires `pip install requests`.
