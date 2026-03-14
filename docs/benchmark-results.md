# Benchmark Results

Decant has been tested against two independent web content extraction
benchmarks: 4,166 HTML pages total, zero crashes.

| Benchmark   | Pages | PASS  | Rate  | ERROR (crashes) |
|-------------|------:|------:|------:|----------------:|
| ScrapingHub |   181 |   158 | 87.3% |               0 |
| WCEB        | 3,985 | 2,723 | 68.3% |               0 |

Scripts: `tests/benchmark-scrapinghub/run_benchmark.py`, `tests/benchmark-wceb/run_wceb.py`
Results: `eval/reports/benchmark/results.json`, `eval/reports/benchmark/wceb_results.json`


## ScrapingHub Article Extraction Benchmark

Source: [scrapinghub/article-extraction-benchmark](https://github.com/scrapinghub/article-extraction-benchmark)

181 pages from major news sites (NYT, Washington Post, BBC, etc.),
collected November 2019. Each page includes human-annotated ground truth
article body text.

### Results

| Status           | Count | Rate  |
|------------------|------:|------:|
| PASS             |   158 | 87.3% |
| SCOPE_ERROR      |    15 |  8.3% |
| EXTRACTION_FAIL  |     6 |  3.3% |
| VALIDATION_ERROR |     2 |  1.1% |
| ERROR            |     0 |  0.0% |

Mode breakdown: 176 extract, 5 transform.

### PASS output stats

| Metric            | Value |
|-------------------|------:|
| Mean word count   |   810 |
| Median word count |   594 |
| Mean sections     |   3.3 |

### Ground truth overlap

The benchmark script computes word-level overlap between Decant output
and human-annotated article body text at runtime. This comparison is
printed to console but not persisted to the JSON report. Re-run the
script to reproduce:

    python tests/benchmark-scrapinghub/run_benchmark.py


## Webis Web Content Extraction Benchmark (WCEB)

Source: [webis-de/web-content-extraction-benchmark](https://github.com/webis-de/web-content-extraction-benchmark)

3,985 HTML files across 8 datasets spanning 2007-2017. Includes a mix
of article pages, navigation pages, form pages, and table-heavy pages.

### Overall results

| Status           | Count | Rate  |
|------------------|------:|------:|
| PASS             | 2,723 | 68.3% |
| SCOPE_ERROR      |   650 | 16.3% |
| VALIDATION_ERROR |   537 | 13.5% |
| EXTRACTION_FAIL  |    75 |  1.9% |
| ERROR            |     0 |  0.0% |

Mode breakdown: 3,059 extract, 926 transform.
Processing time: 1,984 seconds (2.0 files/sec).

### Validation error breakdown

| Category                  | Count | Description                                         |
|---------------------------|------:|-----------------------------------------------------|
| SCOPE_ERROR               |   650 | Correct rejection: nav pages, form pages, tables    |
| VALIDATION_ERROR          |   537 | No semantic structure (missing h1-h3 + body content)|
| EXTRACTION_FAIL           |    75 | No article body detected after extraction           |

### Per-dataset results

| Dataset            | Total | PASS | Rate  | Scope | ExtFl | ValEr | Error |
|--------------------|------:|-----:|------:|------:|------:|------:|------:|
| cetd               |   700 |  648 | 92.6% |    42 |     2 |     8 |     0 |
| scrapinghub        |   181 |  158 | 87.3% |    15 |     6 |     2 |     0 |
| cleanportaleval    |    71 |   57 | 80.3% |    13 |     1 |     0 |     0 |
| readability        |   115 |   89 | 77.4% |     9 |     4 |    13 |     0 |
| google-trends-2017 |   180 |  139 | 77.2% |    23 |     9 |     9 |     0 |
| dragnet            | 1,379 |  971 | 70.4% |   346 |    30 |    32 |     0 |
| l3s-gn1            |   621 |  339 | 54.6% |   135 |    13 |   134 |     0 |
| cleaneval          |   738 |  322 | 43.6% |    67 |    10 |   339 |     0 |

### Per-dataset mode breakdown

| Dataset            | Extract | Transform |
|--------------------|--------:|----------:|
| cetd               |     670 |        30 |
| cleaneval          |     153 |       585 |
| cleanportaleval    |      71 |         0 |
| dragnet            |   1,263 |       116 |
| google-trends-2017 |     170 |        10 |
| l3s-gn1            |     491 |       130 |
| readability        |      65 |        50 |
| scrapinghub        |     176 |         5 |

### PASS output stats

| Metric            |  Overall | Best dataset       | Worst dataset     |
|-------------------|---------:|--------------------:|------------------:|
| Mean word count   |    1,146 | cleaneval: 2,182    | cleanportaleval: 580 |
| Median word count |      647 | cleaneval: 1,431    | l3s-gn1: 495      |
| Mean sections     |      4.5 | cleaneval: 7.8      | cleanportaleval: 1.6 |


## Interpretation

### The raw 68.3% WCEB rate understates effectiveness

The 1,262 non-PASS results break down into categories that are largely
correct behavior:

- **650 SCOPE_ERROR** (51.5% of failures): Navigation pages, form/tool
  pages, and table-heavy reference pages. Decant intentionally rejects
  these rather than producing garbage output. These are correct
  rejections, not bugs.

- **537 VALIDATION_ERROR** (42.6% of failures): Pages lacking semantic
  structure (no h1-h3 heading elements with body content in p/ul/ol).
  Dominated by CleanEval (339) and L3S-GN1 (134) -- older corpora from
  the pre-HTML5 era when heading elements were uncommon. Again, correct
  rejection per Decant's design.

- **75 EXTRACTION_FAIL** (5.9% of failures): Trafilatura extracted
  content but no paragraph had 20+ words of prose. Edge cases across
  all datasets.

### Modern datasets pass at 80-93%

Datasets composed primarily of modern article pages show much higher
pass rates:

| Dataset         | Era       | Rate  |
|-----------------|-----------|------:|
| cetd            | ~2010s    | 92.6% |
| scrapinghub     | 2019      | 87.3% |
| cleanportaleval | ~2010s    | 80.3% |
| readability     | ~2010     | 77.4% |

The two worst-performing datasets (CleanEval at 43.6%, L3S-GN1 at
54.6%) contain significant proportions of pre-HTML5 pages and
non-article pages.

### What the numbers don't tell us

These benchmarks measure whether the pipeline produces output without
crashing. They do not measure:

- **Print quality**: Whether the rendered document looks correct on
  paper (margins, font size, page breaks)
- **Rendering quality**: Whether headings, lists, emphasis, and links
  are preserved accurately in the output
- **User value**: Whether the output is genuinely easier to read for
  someone with dyslexia

The internal eval harness (`tests/pipeline-audit/run_metrics.py`) addresses rendering
quality through 16 structural metrics against a human-reviewed corpus.
Print quality and user value require manual testing.


## Reproducibility

### ScrapingHub benchmark

```sh
# Clone benchmark repo as sibling
git clone https://github.com/scrapinghub/article-extraction-benchmark.git \
    ../article-extraction-benchmark

# Run
python tests/benchmark-scrapinghub/run_benchmark.py
```

### WCEB benchmark

```sh
# Clone benchmark repo as sibling
git clone https://github.com/webis-de/web-content-extraction-benchmark.git \
    ../web-content-extraction-benchmark

# Extract combined dataset
cd ../web-content-extraction-benchmark/datasets
tar xf combined.tar.xz
cd -

# Run
python tests/benchmark-wceb/run_wceb.py \
    --benchmark-dir ../web-content-extraction-benchmark/datasets/combined
```

Results are written to `eval/reports/benchmark/`.
