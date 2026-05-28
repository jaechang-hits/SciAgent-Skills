---
name: pubmed-database
description: >-
  Programmatic PubMed access via NCBI E-utilities REST API. Covers
  Boolean/MeSH queries, field-tagged search, endpoints (ESearch,
  EFetch, ESummary, EPost, ELink), history server for batches,
  citation matching, systematic review strategies. Use for biomedical
  literature search or automated pipelines.
license: CC-BY-4.0
---

# PubMed Database

## Overview

PubMed is the U.S. National Library of Medicine's database providing free access to 36M+ biomedical citations from MEDLINE and life sciences journals. This skill covers programmatic access via the E-utilities REST API and advanced search query construction using Boolean operators, MeSH terms, and field tags.

## When to Use

- Searching biomedical literature with structured Boolean/MeSH queries
- Building automated literature monitoring or extraction pipelines
- Conducting systematic literature reviews or meta-analyses
- Retrieving article metadata, abstracts, or citation information by PMID/DOI
- Finding related articles or exploring citation networks programmatically
- Batch processing large sets of PubMed records
- For Python-native PubMed access, prefer BioPython (`Bio.Entrez`) — this skill covers direct REST API usage
- For broader academic search (non-biomedical), use OpenAlex or Semantic Scholar APIs

## Prerequisites

```bash
pip install requests  # HTTP client for E-utilities API
# Optional: pip install biopython  — Bio.Entrez wrapper (higher-level API)
```

**API Rate Limits**:
- Without API key: **3 requests/second**
- With API key: **10 requests/second** (register at https://www.ncbi.nlm.nih.gov/account/)
- Always include `User-Agent` header with contact email

## Quick Start

```python
import requests
import time

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
API_KEY = "YOUR_API_KEY"  # Optional but recommended

def pubmed_request(endpoint, params):
    """Reusable helper for E-utilities API calls with rate limiting."""
    params.setdefault("api_key", API_KEY)
    response = requests.get(f"{BASE_URL}{endpoint}", params=params)
    response.raise_for_status()
    time.sleep(0.1 if API_KEY != "YOUR_API_KEY" else 0.34)  # Rate limit
    return response

# Search → Fetch workflow
search_resp = pubmed_request("esearch.fcgi", {
    "db": "pubmed", "term": "CRISPR[tiab] AND 2024[dp]",
    "retmax": 5, "retmode": "json"
})
pmids = search_resp.json()["esearchresult"]["idlist"]
print(f"Found {len(pmids)} articles: {pmids}")

fetch_resp = pubmed_request("efetch.fcgi", {
    "db": "pubmed", "id": ",".join(pmids),
    "rettype": "abstract", "retmode": "text"
})
print(fetch_resp.text[:500])
```

## Core API

### 1. Search Query Construction

Build PubMed queries using Boolean operators, field tags, and MeSH terms.

```python
# Boolean operators: AND, OR, NOT (must be uppercase)
queries = {
    "basic": "diabetes AND treatment AND 2024[dp]",
    "synonyms": "(metformin OR insulin) AND type 2 diabetes",
    "exclude": "cancer NOT review[pt]",
    "phrase": '"gene expression" AND RNA-seq',
    "field_tags": "smith ja[au] AND cancer[tiab] AND 2023[dp]",
}

# Common field tags:
# [tiab] = title/abstract    [au] = author       [mh] = MeSH term
# [pt]   = publication type   [dp] = date          [ta] = journal
# [1au]  = first author       [lastau] = last author
# [affil] = affiliation       [doi] = DOI          [pmid] = PubMed ID

# Date filtering
date_queries = {
    "single_year": "cancer AND 2024[dp]",
    "range": "cancer AND 2020:2024[dp]",
    "specific": "cancer AND 2024/03/15[dp]",
}
```

```python
# MeSH terms — controlled vocabulary for precise searching
mesh_queries = {
    # [mh] includes narrower terms automatically
    "broad": "diabetes mellitus[mh]",
    # [majr] limits to major topic focus
    "focused": "diabetes mellitus[majr]",
    # MeSH + subheading
    "therapy": "diabetes mellitus, type 2[mh]/drug therapy",
    # Substance name
    "drug": "metformin[nm] AND diabetes mellitus[mh]",
}

# Common MeSH subheadings:
# /diagnosis  /drug therapy  /epidemiology  /etiology
# /prevention & control  /therapy  /genetics
```

### 2. ESearch — Search and Retrieve PMIDs

```python
# Basic search
resp = pubmed_request("esearch.fcgi", {
    "db": "pubmed",
    "term": "CRISPR[tiab] AND genome editing[tiab] AND 2024[dp]",
    "retmax": 100,
    "retmode": "json",
    "sort": "relevance",  # or "pub_date", "first_author"
})
result = resp.json()["esearchresult"]
pmids = result["idlist"]
total = result["count"]
print(f"Total hits: {total}, Retrieved: {len(pmids)}")

# With history server (for large result sets > 500)
resp = pubmed_request("esearch.fcgi", {
    "db": "pubmed",
    "term": "cancer AND 2024[dp]",
    "usehistory": "y",
    "retmode": "json",
})
result = resp.json()["esearchresult"]
webenv = result["webenv"]
query_key = result["querykey"]
total = int(result["count"])
print(f"Stored {total} results on history server")
```

### 3. EFetch — Download Full Records

```python
# Fetch abstracts as text
resp = pubmed_request("efetch.fcgi", {
    "db": "pubmed",
    "id": ",".join(pmids[:10]),
    "rettype": "abstract",
    "retmode": "text",
})
print(resp.text[:500])

# Fetch XML for structured parsing
resp = pubmed_request("efetch.fcgi", {
    "db": "pubmed",
    "id": ",".join(pmids[:10]),
    "rettype": "xml",
    "retmode": "xml",
})

# Fetch from history server (batch processing)
batch_size = 500
for start in range(0, total, batch_size):
    resp = pubmed_request("efetch.fcgi", {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": webenv,
        "retstart": start,
        "retmax": batch_size,
        "rettype": "xml",
        "retmode": "xml",
    })
    print(f"Fetched records {start}–{start + batch_size}")
    time.sleep(0.5)  # Extra delay for large batches
```

### 4. ESummary and ELink — Summaries and Related Articles

```python
# ESummary — lightweight document summaries
resp = pubmed_request("esummary.fcgi", {
    "db": "pubmed",
    "id": ",".join(pmids[:5]),
    "retmode": "json",
})
for uid, data in resp.json()["result"].items():
    if uid == "uids":
        continue
    print(f"PMID {uid}: {data.get('title', '')[:80]}")
    print(f"  Journal: {data.get('fulljournalname', '')}, "
          f"Date: {data.get('pubdate', '')}")

# ELink — find related articles
resp = pubmed_request("elink.fcgi", {
    "dbfrom": "pubmed",
    "db": "pubmed",
    "id": pmids[0],
    "cmd": "neighbor",
    "retmode": "json",
})
# Links to other NCBI databases
resp = pubmed_request("elink.fcgi", {
    "dbfrom": "pubmed",
    "db": "pmc",  # PubMed Central
    "id": pmids[0],
    "retmode": "json",
})
```

### 5. Citation Matching and Identifier Lookup

```python
# Search by identifiers
id_queries = {
    "pmid": "12345678[pmid]",
    "doi": "10.1056/NEJMoa123456[doi]",
    "pmc": "PMC123456[pmc]",
}

# ECitMatch — match partial citations to PMIDs
# Format: journal|year|volume|first_page|author_name|key|
citation = "Science|2008|320|5880|1185|key1|"
resp = pubmed_request("ecitmatch.cgi", {
    "db": "pubmed",
    "rettype": "xml",
    "bdata": citation,
})
print(f"Matched PMID: {resp.text.strip()}")

# Batch citation matching
citations = [
    "Nature|2020|580|7801|71|ref1|",
    "Science|2019|366|6463|347|ref2|",
]
resp = pubmed_request("ecitmatch.cgi", {
    "db": "pubmed",
    "rettype": "xml",
    "bdata": "\r".join(citations),
})
```

### 6. Publication Filtering

```python
# Filter by publication type
type_filters = {
    "rcts": "randomized controlled trial[pt]",
    "reviews": "systematic review[pt]",
    "meta": "meta-analysis[pt]",
    "guidelines": "guideline[pt]",
    "case_reports": "case reports[pt]",
}

# Filter by text availability
availability = {
    "free_text": "free full text[sb]",
    "has_abstract": "hasabstract[text]",
}

# Combine filters
query = (
    "diabetes mellitus[mh] AND "
    "randomized controlled trial[pt] AND "
    "2023:2024[dp] AND "
    "free full text[sb] AND "
    "english[la]"
)
resp = pubmed_request("esearch.fcgi", {
    "db": "pubmed", "term": query, "retmax": 100, "retmode": "json"
})
print(f"Free RCTs on diabetes (2023-2024): {resp.json()['esearchresult']['count']}")
```

## Key Concepts

### E-utilities Endpoint Summary

| Endpoint | Purpose | Key Parameters |
|----------|---------|----------------|
| `esearch.fcgi` | Search, return PMIDs | `term`, `retmax`, `sort`, `usehistory` |
| `efetch.fcgi` | Download full records | `id`/`query_key`+`WebEnv`, `rettype`, `retmode` |
| `esummary.fcgi` | Lightweight summaries | `id`, `retmode` |
| `epost.fcgi` | Upload UIDs to server | `id` (comma-separated) |
| `elink.fcgi` | Related articles, cross-DB | `id`, `dbfrom`, `db`, `cmd` |
| `einfo.fcgi` | List databases/fields | `db` (optional) |
| `egquery.fcgi` | Count hits across DBs | `term` |
| `espell.fcgi` | Spelling suggestions | `term` |
| `ecitmatch.cgi` | Match citations to PMIDs | `bdata` |

### History Server Pattern

For result sets >500 articles, use the history server to avoid URL length limits:

1. **ESearch** with `usehistory=y` → returns `WebEnv` + `QueryKey`
2. **EFetch** in batches using `WebEnv` + `QueryKey` + `retstart`/`retmax`
3. **EPost** to upload additional PMIDs to the same `WebEnv`

### Automatic Term Mapping (ATM)

When no field tag is specified, PubMed maps terms through: MeSH Translation Table → Journals Translation Table → Author Index → Full Text. Bypass ATM with explicit field tags or quoted phrases.

### Common MeSH Subheadings

| Subheading | Abbreviation | Use |
|------------|-------------|-----|
| /diagnosis | /DI | Diagnostic methods |
| /drug therapy | /DT | Pharmaceutical treatment |
| /epidemiology | /EP | Disease patterns |
| /etiology | /ET | Disease causes |
| /genetics | /GE | Genetic aspects |
| /prevention & control | /PC | Preventive measures |
| /therapy | /TH | Treatment approaches |

## Common Workflows

### Workflow 1: Systematic Review Search

```python
import requests, time, json

# 1. Define PICO-structured query
query = (
    # Population
    "(diabetes mellitus, type 2[mh] OR type 2 diabetes[tiab]) AND "
    # Intervention + Comparison
    "(metformin[nm] OR lifestyle modification[tiab]) AND "
    # Outcome
    "(glycemic control[tiab] OR HbA1c[tiab]) AND "
    # Study design filter
    "(randomized controlled trial[pt] OR systematic review[pt]) AND "
    # Date range
    "2020:2024[dp]"
)

# 2. Search with history server
resp = pubmed_request("esearch.fcgi", {
    "db": "pubmed", "term": query,
    "usehistory": "y", "retmode": "json"
})
result = resp.json()["esearchresult"]
total = int(result["count"])
print(f"Systematic review hits: {total}")

# 3. Batch fetch all results as XML
import xml.etree.ElementTree as ET
articles = []
for start in range(0, total, 200):
    resp = pubmed_request("efetch.fcgi", {
        "db": "pubmed", "query_key": result["querykey"],
        "WebEnv": result["webenv"],
        "retstart": start, "retmax": 200,
        "rettype": "xml", "retmode": "xml"
    })
    root = ET.fromstring(resp.text)
    for article in root.findall('.//PubmedArticle'):
        pmid = article.findtext('.//PMID')
        title = article.findtext('.//ArticleTitle')
        articles.append({"pmid": pmid, "title": title})
    time.sleep(0.5)

print(f"Retrieved {len(articles)} articles for screening")
```

### Workflow 2: Literature Monitoring Pipeline

```python
import json, datetime

# 1. Construct monitoring query
topic_query = (
    "(CRISPR[tiab] OR gene editing[tiab]) AND "
    "(therapeutics[tiab] OR clinical trial[pt])"
)

# 2. Search recent publications (last 30 days)
today = datetime.date.today()
start_date = today - datetime.timedelta(days=30)
query = f"{topic_query} AND {start_date.strftime('%Y/%m/%d')}:{today.strftime('%Y/%m/%d')}[dp]"

resp = pubmed_request("esearch.fcgi", {
    "db": "pubmed", "term": query,
    "retmax": 100, "retmode": "json", "sort": "pub_date"
})
pmids = resp.json()["esearchresult"]["idlist"]

# 3. Get summaries for new articles
if pmids:
    resp = pubmed_request("esummary.fcgi", {
        "db": "pubmed", "id": ",".join(pmids), "retmode": "json"
    })
    for uid in pmids:
        info = resp.json()["result"].get(uid, {})
        print(f"[{uid}] {info.get('title', 'N/A')[:80]}")
        print(f"  {info.get('fulljournalname', '')} — {info.get('pubdate', '')}")
```

## Key Parameters

| Parameter | Endpoint | Default | Effect |
|-----------|----------|---------|--------|
| `term` | ESearch | Required | Search query with Boolean/field tags |
| `retmax` | ESearch/EFetch | 20 | Max records returned (up to 10,000) |
| `retstart` | ESearch/EFetch | 0 | Offset for pagination |
| `rettype` | EFetch | `full` | Output type: `abstract`, `medline`, `xml`, `uilist` |
| `retmode` | All | `xml` | Output format: `xml`, `json`, `text` |
| `sort` | ESearch | `relevance` | Sort order: `relevance`, `pub_date`, `first_author` |
| `usehistory` | ESearch | `n` | Enable history server: `y` for large result sets |
| `api_key` | All | None | NCBI API key for 10 req/sec (vs 3 without) |
| `cmd` | ELink | `neighbor` | Link type: `neighbor`, `neighbor_score`, `prlinks` |
| `datetype` | ESearch | `pdat` | Date field: `pdat` (publication), `edat` (entrez) |

## Best Practices

1. **Always use an API key** — register at NCBI for 10 req/sec instead of 3
2. **Use history server for >500 results** — avoids URL length limits and enables batch fetching
3. **Include rate limiting** — `time.sleep(0.1)` with API key, `time.sleep(0.34)` without
4. **Cache results locally** — PubMed data changes slowly; cache responses to minimize API calls
5. **Use MeSH terms + free text** — combine `[mh]` and `[tiab]` for comprehensive coverage: `(diabetes mellitus[mh] OR diabetes[tiab])`
6. **Document search strategies** — for systematic reviews, record exact queries, dates, and result counts
7. **Parse XML for structured data** — text output is human-readable but XML preserves field structure for automated extraction

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| HTTP 429 (Too Many Requests) | Exceeding rate limit | Add `time.sleep()`; use API key for higher limit |
| HTTP 414 (URI Too Long) | Too many PMIDs in URL | Use history server (`usehistory=y`) or EPost |
| Empty result set | Overly restrictive query | Remove filters one at a time; check ATM with EInfo |
| Unexpected MeSH mapping | Automatic Term Mapping | Use explicit field tags: `term[tiab]` instead of bare `term` |
| Missing abstracts | Pre-1975 articles or certain types | Filter: `hasabstract[text]` |
| XML parsing errors | Malformed response | Check `retmode=xml` and `rettype=xml`; handle encoding |
| Stale history server | Session expired (8h inactivity) | Re-run ESearch with `usehistory=y` to get new WebEnv |
| Truncated results | Default `retmax=20` | Set `retmax=100` or higher (max 10,000) |

## Common Recipes

### Recipe: Download Abstracts for a Gene Set

```python
import requests
import time

def fetch_abstracts(gene_list, max_per_gene=5):
    """Retrieve PubMed abstracts for each gene in a list."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    records = []
    for gene in gene_list:
        r = requests.get(f"{base}/esearch.fcgi",
                         params={"db": "pubmed", "term": f"{gene}[gene] AND Homo sapiens[orgn]",
                                 "retmax": max_per_gene, "retmode": "json"})
        ids = r.json()["esearchresult"]["idlist"]
        if ids:
            fetch = requests.get(f"{base}/efetch.fcgi",
                                 params={"db": "pubmed", "id": ",".join(ids), "rettype": "abstract"})
            records.append({"gene": gene, "pmids": ids, "text": fetch.text[:500]})
        time.sleep(0.34)
    return records

results = fetch_abstracts(["BRCA1", "TP53", "EGFR"])
for r in results:
    print(f"{r['gene']}: {r['pmids']}")
```

### Recipe: Track New Publications via Date Filter

```python
import requests
from datetime import date, timedelta

# Find papers published in the last 7 days on a topic
week_ago = (date.today() - timedelta(days=7)).strftime("%Y/%m/%d")
today = date.today().strftime("%Y/%m/%d")

resp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    params={"db": "pubmed", "term": "CRISPR AND cancer",
                            "datetype": "pdat", "mindate": week_ago, "maxdate": today,
                            "retmax": 20, "retmode": "json"})
data = resp.json()["esearchresult"]
print(f"New CRISPR+cancer papers this week: {data['count']}")
print("PMIDs:", data["idlist"])
```

## Bundled Resources

- `references/search_syntax.md` — Complete field tag reference, Boolean/wildcard/proximity syntax, automatic term mapping rules, all filter types (age groups, species, languages), and clinical query filters
- `references/common_queries.md` — Ready-to-use query templates organized by domain (disease-specific, population-specific, methodology, drug research, epidemiology) with ~40 example patterns

Not migrated from original: `references/api_reference.md` (298 lines) — endpoint parameter details are consolidated into Core API sections 2-5 and the E-utilities Endpoint Summary table in Key Concepts.

## References

- PubMed Help: https://pubmed.ncbi.nlm.nih.gov/help/
- E-utilities Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- NCBI API Key Registration: https://www.ncbi.nlm.nih.gov/account/

## Related Skills

- **biopython** — higher-level Python wrapper (`Bio.Entrez`) for E-utilities
- **openalex-database** — broader academic literature beyond biomedical
- **literature-review** — systematic review methodology and PRISMA framework
