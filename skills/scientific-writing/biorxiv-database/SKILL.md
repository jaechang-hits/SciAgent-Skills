---
name: "biorxiv-database"
description: "Query bioRxiv and medRxiv preprint servers via REST API for biology and health science preprints. Search by DOI, category, or date range. Retrieve metadata (title, abstract, authors, category, DOI, version history) and download full-text PDFs. No authentication required. For peer-reviewed biomedical literature use pubmed-database; for broader scholarly search use openalex-database."
license: "CC0-1.0"
---

# bioRxiv / medRxiv Preprint Database

## Overview

bioRxiv (biology) and medRxiv (health sciences) are free preprint servers hosting 200,000+ and 50,000+ manuscripts, respectively, before or alongside peer review. The unified REST API provides programmatic access to preprint metadata (title, abstract, authors, category, DOI, version history) without authentication. Preprints are available as PDF and can be retrieved by DOI, date range, or category.

## When to Use

- Finding the most current research in fast-moving fields before peer review (e.g., infectious disease during outbreaks)
- Monitoring weekly preprint submissions in a specific discipline category (e.g., bioinformatics, genomics, neuroscience)
- Retrieving metadata and abstracts for a set of bioRxiv DOIs for literature screening
- Building a corpus of preprints to track the preprint-to-publication pipeline
- Checking whether a specific preprint has been updated or published in a peer-reviewed journal
- For peer-reviewed biomedical literature use `pubmed-database`; for all disciplines use `openalex-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **Data requirements**: bioRxiv/medRxiv DOIs, date ranges, or category names
- **Environment**: internet connection; no API key or authentication required
- **Rate limits**: no stated hard limit; use reasonable delays for bulk queries

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

BASE = "https://api.biorxiv.org"

# Retrieve recent bioinformatics preprints
r = requests.get(f"{BASE}/details/biorxiv/2024-01-01/2024-01-07/0",
                 params={"category": "bioinformatics"})
r.raise_for_status()
data = r.json()
print(f"Total preprints: {data['messages'][0]['total']}")
for article in data["collection"][:3]:
    print(f"\n{article['title'][:80]}")
    print(f"  Authors : {article['authors'][:60]}")
    print(f"  DOI     : {article['doi']}")
    print(f"  Category: {article['category']}")
```

## Core API

### Query 1: Date-Range Preprint Listing

Retrieve all preprints posted within a date range, optionally filtered by category.

```python
import requests, pandas as pd

BASE = "https://api.biorxiv.org"

def get_preprints(server, date_from, date_to, cursor=0, category=None):
    """
    server: 'biorxiv' or 'medrxiv'
    date_from, date_to: 'YYYY-MM-DD' strings
    cursor: page offset (increments of 100)
    """
    url = f"{BASE}/details/{server}/{date_from}/{date_to}/{cursor}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

data = get_preprints("biorxiv", "2024-01-01", "2024-01-03")
total = data["messages"][0]["total"]
print(f"bioRxiv preprints Jan 1-3, 2024: {total}")

rows = []
for article in data["collection"][:10]:
    rows.append({
        "doi": article["doi"],
        "title": article["title"],
        "authors": article["authors"][:80],
        "category": article["category"],
        "date": article["date"],
        "version": article["version"],
    })
df = pd.DataFrame(rows)
print(df[["title", "category", "date"]].head())
```

```python
# Paginate through all results for a date range
def get_all_preprints(server, date_from, date_to, max_results=500):
    all_articles = []
    cursor = 0
    while len(all_articles) < max_results:
        data = get_preprints(server, date_from, date_to, cursor)
        collection = data["collection"]
        if not collection:
            break
        all_articles.extend(collection)
        total = data["messages"][0]["total"]
        cursor += 100
        if cursor >= total:
            break
    return all_articles[:max_results]

articles = get_all_preprints("biorxiv", "2024-01-01", "2024-01-07")
print(f"Retrieved {len(articles)} preprints from first week of 2024")
```

### Query 2: Preprint Detail by DOI

Retrieve full metadata and version history for a specific preprint by DOI.

```python
import requests

BASE = "https://api.biorxiv.org"

# Retrieve specific preprint by DOI
doi = "10.1101/2024.01.01.000001"  # Replace with real DOI

def get_by_doi(server, doi):
    r = requests.get(f"{BASE}/details/{server}/{doi}")
    r.raise_for_status()
    return r.json()

# Generic example using bioRxiv DOI pattern
r = requests.get(f"{BASE}/details/biorxiv/10.1101/2021.01.01.425318")
if r.ok:
    data = r.json()
    articles = data.get("collection", [])
    if articles:
        art = articles[-1]  # Latest version
        print(f"Title   : {art['title']}")
        print(f"Authors : {art['authors'][:100]}")
        print(f"Category: {art['category']}")
        print(f"Date    : {art['date']}")
        print(f"Version : {art['version']}")
        print(f"DOI     : {art['doi']}")
        print(f"Abstract (first 300): {art['abstract'][:300]}")
```

### Query 3: Published Preprint Lookup

Check if a preprint has been published in a peer-reviewed journal.

```python
import requests

BASE = "https://api.biorxiv.org"

def check_published(server, doi):
    """Check if a preprint DOI has a corresponding published article."""
    r = requests.get(f"{BASE}/publisher/{server}/{doi}")
    r.raise_for_status()
    data = r.json()
    return data.get("collection", [])

# Check one known preprint
doi = "10.1101/2021.01.01.425318"
published = check_published("biorxiv", doi)
if published:
    pub = published[0]
    print(f"Published in: {pub.get('published_journal')}")
    print(f"Published DOI: {pub.get('published_doi')}")
else:
    print(f"Preprint {doi} has not been published yet (or not tracked)")
```

### Query 4: Category-Based Monitoring

Monitor preprints by specific research category.

```python
import requests, pandas as pd
from datetime import date, timedelta

BASE = "https://api.biorxiv.org"

# bioRxiv categories include: bioinformatics, genomics, neuroscience,
# immunology, cell-biology, biochemistry, microbiology, etc.

def weekly_category_digest(category, days_back=7):
    """Get preprints from last N days for a specific category."""
    today = date.today()
    date_from = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to = today.strftime("%Y-%m-%d")

    all_articles = []
    cursor = 0
    while True:
        r = requests.get(f"{BASE}/details/biorxiv/{date_from}/{date_to}/{cursor}")
        data = r.json()
        batch = [a for a in data["collection"] if category.lower() in a["category"].lower()]
        all_articles.extend(batch)
        if len(data["collection"]) < 100:
            break
        cursor += 100

    return pd.DataFrame(all_articles)[["doi", "title", "authors", "date"]] if all_articles else pd.DataFrame()

df = weekly_category_digest("genomics", days_back=3)
print(f"Recent genomics preprints: {len(df)}")
print(df[["title", "date"]].head())
```

### Query 5: medRxiv Clinical/Health Research

Query medRxiv for health and clinical science preprints.

```python
import requests, pandas as pd

BASE = "https://api.biorxiv.org"

# medRxiv categories: infectious diseases, epidemiology, oncology,
# cardiology, neurology, psychiatry, public and global health, etc.

r = requests.get(f"{BASE}/details/medrxiv/2024-01-01/2024-01-07/0")
r.raise_for_status()
data = r.json()
total = data["messages"][0]["total"]
print(f"medRxiv preprints Jan 1-7, 2024: {total}")

# Group by category
from collections import Counter
category_counts = Counter(a["category"] for a in data["collection"])
print("\nTop categories:")
for cat, count in category_counts.most_common(5):
    print(f"  {cat}: {count}")
```

### Query 6: Bulk DOI Resolution and Abstract Extraction

Retrieve abstracts for a list of bioRxiv DOIs.

```python
import requests, time, pandas as pd

BASE = "https://api.biorxiv.org"

dois = [
    "10.1101/2023.01.01.000001",
    "10.1101/2023.02.01.000002",
    "10.1101/2023.03.01.000003",
]

rows = []
for doi in dois:
    r = requests.get(f"{BASE}/details/biorxiv/{doi}")
    if r.ok:
        collection = r.json().get("collection", [])
        if collection:
            art = collection[-1]  # Latest version
            rows.append({
                "doi": doi,
                "title": art.get("title"),
                "category": art.get("category"),
                "date": art.get("date"),
                "abstract": art.get("abstract", "")[:300],
            })
    time.sleep(0.2)

df = pd.DataFrame(rows)
if not df.empty:
    df.to_csv("preprint_abstracts.csv", index=False)
    print(df[["doi", "title", "category"]].to_string(index=False))
else:
    print("No valid preprints found for provided DOIs")
```

## Key Concepts

### API Endpoint Structure

The bioRxiv API follows the pattern: `https://api.biorxiv.org/details/{server}/{interval}/{cursor}`
- `server`: `biorxiv` or `medrxiv`
- `interval`: either a DOI (for single record) or `date_from/date_to` (for date range)
- `cursor`: pagination offset (0, 100, 200…)

### Version Tracking

Preprints can be updated; each update creates a new version (v1, v2, v3…). The API returns all versions chronologically; the last item in `collection` is always the most recent.

## Common Workflows

### Workflow 1: Weekly Preprint Digest Pipeline

**Goal**: Automatically collect last week's preprints in target categories and export for review.

```python
import requests, time, pandas as pd
from datetime import date, timedelta

BASE = "https://api.biorxiv.org"

TARGET_CATEGORIES = ["bioinformatics", "genomics", "systems biology"]
DAYS_BACK = 7

today = date.today()
date_from = (today - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
date_to = today.strftime("%Y-%m-%d")

print(f"Fetching bioRxiv preprints from {date_from} to {date_to}")

all_articles = []
cursor = 0
while True:
    r = requests.get(f"{BASE}/details/biorxiv/{date_from}/{date_to}/{cursor}")
    r.raise_for_status()
    data = r.json()
    batch = data["collection"]
    if not batch:
        break
    all_articles.extend(batch)
    total = data["messages"][0]["total"]
    cursor += 100
    if cursor >= total:
        break
    time.sleep(0.1)

# Filter by target categories
filtered = [a for a in all_articles
            if any(cat in a.get("category", "").lower() for cat in TARGET_CATEGORIES)]

df = pd.DataFrame(filtered)[["doi", "title", "authors", "category", "date"]]
df = df.drop_duplicates(subset="doi")  # Remove duplicate versions

output_file = f"biorxiv_digest_{date_to}.csv"
df.to_csv(output_file, index=False)
print(f"\nSaved {len(df)} preprints across {len(TARGET_CATEGORIES)} categories → {output_file}")
print(df[["title", "category", "date"]].head(5).to_string(index=False))
```

### Workflow 2: Preprint-to-Publication Tracker

**Goal**: For a list of preprint DOIs, check which have been published and retrieve publication details.

```python
import requests, time, pandas as pd

BASE = "https://api.biorxiv.org"

preprint_dois = [
    "10.1101/2021.01.01.425318",
    "10.1101/2020.04.01.020370",
]

results = []
for doi in preprint_dois:
    # Get preprint metadata
    r_meta = requests.get(f"{BASE}/details/biorxiv/{doi}")
    meta = {}
    if r_meta.ok and r_meta.json().get("collection"):
        art = r_meta.json()["collection"][-1]
        meta = {"title": art["title"], "category": art["category"],
                "preprint_date": art["date"]}

    # Check publication status
    r_pub = requests.get(f"{BASE}/publisher/biorxiv/{doi}")
    published = {}
    if r_pub.ok and r_pub.json().get("collection"):
        pub = r_pub.json()["collection"][0]
        published = {"journal": pub.get("published_journal"),
                     "pub_doi": pub.get("published_doi")}

    results.append({"preprint_doi": doi, **meta, **published})
    time.sleep(0.25)

df = pd.DataFrame(results)
print(df.to_string(index=False))
df.to_csv("preprint_publication_status.csv", index=False)
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `server` | URL path | required | `"biorxiv"`, `"medrxiv"` | Select preprint server |
| `date_from` | URL path | required | `"YYYY-MM-DD"` | Start of date range |
| `date_to` | URL path | required | `"YYYY-MM-DD"` | End of date range |
| `cursor` | URL path | `0` | `0`, `100`, `200`… | Pagination offset (100 per page) |
| `category` | Filter | — | e.g., `"bioinformatics"` | Category name substring match (post-filter) |
| `version` | — | all versions | — | API returns all versions; use `[-1]` for latest |

## Best Practices

1. **Always take the last element for latest version**: The `collection` array is sorted oldest-to-newest version. Use `collection[-1]` to get the most current version of a preprint.

2. **Post-filter by category**: The API does not natively filter by category; retrieve all preprints for a date range and filter client-side using `if category in article["category"].lower()`.

3. **Respect server resources**: Add `time.sleep(0.2)` between individual DOI lookups; avoid bulk hammering the API.

4. **Cross-check with PubMed**: The `publisher` endpoint reveals when a preprint is published; use `pubmed-database` to retrieve the full peer-reviewed article metadata.

5. **Handle missing abstracts**: Some preprints have empty `abstract` fields. Always guard with `art.get("abstract", "") or "No abstract available"`.

## Common Recipes

### Recipe: Download Preprint PDF

When to use: Retrieve full-text PDF for a bioRxiv preprint.

```python
import requests

doi = "10.1101/2021.01.01.425318"
# bioRxiv PDF URL pattern
pdf_url = f"https://www.biorxiv.org/content/{doi}.full.pdf"

r = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
if r.ok:
    with open(f"{doi.replace('/', '_')}.pdf", "wb") as f:
        f.write(r.content)
    print(f"Downloaded PDF ({len(r.content)//1024} KB)")
else:
    print(f"PDF not available: HTTP {r.status_code}")
```

### Recipe: Count Preprints by Category

When to use: Analyze the distribution of preprints across bioRxiv categories in a time window.

```python
import requests, pandas as pd
from collections import Counter

r = requests.get("https://api.biorxiv.org/details/biorxiv/2024-01-01/2024-01-07/0")
data = r.json()
total = data["messages"][0]["total"]

# Fetch all pages
all_articles = data["collection"]
for cursor in range(100, min(total, 1000), 100):
    r2 = requests.get(f"https://api.biorxiv.org/details/biorxiv/2024-01-01/2024-01-07/{cursor}")
    all_articles.extend(r2.json()["collection"])

counts = Counter(a["category"] for a in all_articles)
df = pd.DataFrame(counts.most_common(), columns=["category", "count"])
print(df.head(10).to_string(index=False))
```

### Recipe: Check if Preprint Has Been Published

When to use: Quick single-preprint publication check.

```python
import requests

doi = "10.1101/2021.01.01.425318"
r = requests.get(f"https://api.biorxiv.org/publisher/biorxiv/{doi}")
collection = r.json().get("collection", [])
if collection:
    print(f"Published: {collection[0]['published_journal']} | DOI: {collection[0]['published_doi']}")
else:
    print("Not published or not tracked")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `collection` is empty | DOI not found or date range has no results | Verify DOI format (starts with `10.1101/`); check date range |
| Duplicate preprints in results | Multiple versions returned | Deduplicate by DOI: `df.drop_duplicates(subset='doi', keep='last')` |
| Missing abstract field | Some preprints don't have structured abstracts | Guard with `art.get("abstract", "") or "N/A"` |
| `total` count vs retrieved mismatch | New preprints added during pagination | Accept approximate totals; preprints are added continuously |
| PDF download blocked | Anti-bot protection | Add a User-Agent header; respect `robots.txt`; use for research only |
| Slow pagination for large date ranges | Large number of preprints | Use narrower date windows (3-7 days) for busy periods |

## Related Skills

- `pubmed-database` — Peer-reviewed biomedical literature for verifying published versions of preprints
- `openalex-database` — Broader scholarly index including bioRxiv content after indexing lag
- `literature-review` — Guide for incorporating preprints into systematic reviews
- `scientific-brainstorming` — Using preprint alerts as input for hypothesis generation

## References

- [bioRxiv API documentation](https://api.biorxiv.org/) — Official API endpoint and response format
- [bioRxiv about page](https://www.biorxiv.org/about/home) — Server overview, submission guidelines
- [medRxiv about page](https://www.medrxiv.org/about/home) — Health science preprint server details
- [Preprint guidelines review (Fraser et al. 2021)](https://doi.org/10.1371/journal.pbio.3001285) — Best practices for citing and using preprints in research
