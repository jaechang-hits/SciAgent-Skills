---
name: "openalex-database"
description: "Query OpenAlex REST API for 250M+ scholarly works, authors, institutions, journals, concepts. Search by keyword, author, DOI, ORCID, or ID; filter by year, OA, citations, field; retrieve citations, references, author disambiguation. Free, no auth. For PubMed use pubmed-database; preprints use biorxiv-database."
license: "CC0-1.0"
---

# OpenAlex Scholarly Database

## Overview

OpenAlex is a free, open-access index of 250M+ scholarly works, 90M+ authors, 110,000+ journals, and 10,000+ institutions. It succeeds Microsoft Academic Graph and provides rich metadata: abstracts, open-access URLs, citation counts, referenced works, author disambiguated IDs (ORCID), and concept tags. The REST API requires no authentication for up to 100,000 requests/day; a polite pool (email parameter) gives priority processing.

## When to Use

- Building systematic literature review corpora by searching across all academic disciplines (not just biomedical)
- Retrieving citation networks for bibliometric analysis, co-citation clustering, or reference graph traversal
- Disambiguating author identities across institutions using ORCID/OpenAlex author IDs
- Finding open-access full-text URLs for a set of DOIs to build downloadable paper corpora
- Analyzing publication trends by year, institution, country, or research concept
- Enriching a paper list with metadata (citation count, abstract, venue) from DOIs or titles
- For PubMed-indexed biomedical literature use `pubmed-database`; for bioRxiv preprints use `biorxiv-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **Data requirements**: DOIs, OpenAlex Work IDs (W…), author names, ORCID IDs, or search terms
- **Environment**: internet connection; no API key required
- **Rate limits**: 10 req/s anonymous; add `mailto=your@email.com` query param to join polite pool (higher priority, same limit)

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

BASE = "https://api.openalex.org"

# Search for works on CRISPR
r = requests.get(f"{BASE}/works",
                 params={"search": "CRISPR gene editing",
                         "filter": "publication_year:2023",
                         "per_page": 5,
                         "mailto": "your@email.com"})
r.raise_for_status()
data = r.json()
print(f"Total results: {data['meta']['count']}")
for work in data["results"][:3]:
    print(f"  {work['title'][:80]} ({work['publication_year']}) cites={work['cited_by_count']}")
```

## Core API

### Query 1: Works Search

Search works by title/abstract keywords with filters.

```python
import requests, pandas as pd

BASE = "https://api.openalex.org"

def search_works(query, filters=None, per_page=25, mailto="your@email.com"):
    params = {"search": query, "per_page": per_page, "mailto": mailto}
    if filters:
        params["filter"] = ",".join(f"{k}:{v}" for k, v in filters.items())
    r = requests.get(f"{BASE}/works", params=params)
    r.raise_for_status()
    return r.json()

# Search with filters
data = search_works("single-cell RNA sequencing",
                    filters={"publication_year": "2020-2024",
                             "open_access.is_oa": "true"},
                    per_page=10)

print(f"Open-access scRNA-seq papers 2020-2024: {data['meta']['count']}")
rows = []
for w in data["results"]:
    rows.append({
        "title": w["title"],
        "year": w["publication_year"],
        "citations": w["cited_by_count"],
        "doi": w.get("doi"),
        "oa_url": w.get("open_access", {}).get("oa_url"),
    })
df = pd.DataFrame(rows)
print(df[["title", "year", "citations"]].head())
```

```python
# Paginate through all results
def paginate_works(query, filters=None, max_results=200, mailto="your@email.com"):
    """Retrieve up to max_results works, paginating automatically."""
    all_results = []
    cursor = "*"
    while len(all_results) < max_results:
        params = {"search": query, "per_page": 200,
                  "cursor": cursor, "mailto": mailto}
        if filters:
            params["filter"] = ",".join(f"{k}:{v}" for k, v in filters.items())
        r = requests.get(f"{BASE}/works", params=params)
        data = r.json()
        all_results.extend(data["results"])
        cursor = data["meta"].get("next_cursor")
        if not cursor:
            break
    return all_results[:max_results]

papers = paginate_works("transformer protein structure", max_results=100)
print(f"Retrieved {len(papers)} papers")
```

### Query 2: Lookup by DOI or OpenAlex ID

Retrieve a single work by DOI or OpenAlex ID.

```python
import requests

BASE = "https://api.openalex.org"

# By DOI
doi = "10.1038/s41592-019-0458-z"  # Scanpy paper
r = requests.get(f"{BASE}/works/https://doi.org/{doi}",
                 params={"mailto": "your@email.com"})
r.raise_for_status()
work = r.json()

print(f"Title   : {work['title']}")
print(f"Year    : {work['publication_year']}")
print(f"Citations: {work['cited_by_count']}")
print(f"Journal : {work.get('primary_location', {}).get('source', {}).get('display_name')}")
abstract = work.get("abstract_inverted_index")
if abstract:
    # Reconstruct abstract from inverted index
    words = {pos: word for word, positions in abstract.items() for pos in positions}
    text = " ".join(words[i] for i in sorted(words))
    print(f"Abstract (first 200): {text[:200]}")
```

### Query 3: Author Search and ORCID Lookup

Find author records, resolve ORCID identifiers, retrieve publication lists.

```python
import requests, pandas as pd

BASE = "https://api.openalex.org"

# Search for an author
r = requests.get(f"{BASE}/authors",
                 params={"search": "Jennifer Doudna",
                         "per_page": 5,
                         "mailto": "your@email.com"})
authors = r.json()["results"]

for a in authors[:3]:
    print(f"Author: {a['display_name']}")
    print(f"  OpenAlex ID : {a['id']}")
    print(f"  ORCID       : {a.get('orcid', 'n/a')}")
    print(f"  Institution : {a.get('last_known_institution', {}).get('display_name', 'n/a')}")
    print(f"  Works count : {a['works_count']}")
    print(f"  h-index     : {a['summary_stats'].get('h_index', 'n/a')}")
    print()
```

```python
# Get all papers by an author (by ORCID)
orcid = "0000-0001-8742-3594"  # Jennifer Doudna
r = requests.get(f"{BASE}/works",
                 params={"filter": f"author.orcid:{orcid}",
                         "sort": "cited_by_count:desc",
                         "per_page": 10,
                         "mailto": "your@email.com"})
papers = r.json()["results"]
for p in papers[:5]:
    print(f"  [{p['publication_year']}] {p['title'][:70]} (cites: {p['cited_by_count']})")
```

### Query 4: Citation Network Retrieval

Get referenced works and citing works for a paper.

```python
import requests, pandas as pd

BASE = "https://api.openalex.org"

work_id = "W2018426904"  # CRISPR paper

# Get what this paper references
r = requests.get(f"{BASE}/works/{work_id}",
                 params={"select": "referenced_works,cited_by_count,title",
                         "mailto": "your@email.com"})
work = r.json()
ref_ids = work.get("referenced_works", [])
print(f"'{work['title']}' cites {len(ref_ids)} papers")
print(f"Total citations: {work['cited_by_count']}")

# Fetch metadata for references (batch)
if ref_ids:
    ids_str = "|".join(id.split("/")[-1] for id in ref_ids[:10])
    r2 = requests.get(f"{BASE}/works",
                      params={"filter": f"openalex_id:{ids_str}",
                              "per_page": 10,
                              "mailto": "your@email.com"})
    refs = r2.json()["results"]
    for ref in refs[:5]:
        print(f"  [{ref['publication_year']}] {ref['title'][:70]}")
```

### Query 5: Concept/Topic Filtering and Trend Analysis

Filter by research concepts and analyze publication trends.

```python
import requests, pandas as pd

BASE = "https://api.openalex.org"

# Get concept ID for "Machine Learning"
r = requests.get(f"{BASE}/concepts",
                 params={"search": "machine learning biology",
                         "per_page": 3,
                         "mailto": "your@email.com"})
concepts = r.json()["results"]
for c in concepts[:3]:
    print(f"Concept: {c['display_name']} (ID: {c['id']}, level: {c['level']})")

# Count papers per year for a concept
concept_id = "C154945302"  # Machine learning (OpenAlex ID)
r2 = requests.get(f"{BASE}/works",
                  params={"filter": f"concepts.id:{concept_id},publication_year:2015-2024",
                          "group_by": "publication_year",
                          "per_page": 200,
                          "mailto": "your@email.com"})
groups = r2.json()["group_by"]
df = pd.DataFrame(groups).rename(columns={"key": "year", "count": "papers"})
df = df.sort_values("year")
print(df.tail(5).to_string(index=False))
```

### Query 6: Institution and Venue Queries

Retrieve papers from a specific institution, journal, or conference.

```python
import requests, pandas as pd

BASE = "https://api.openalex.org"

# Papers from a specific journal in the last year
r = requests.get(f"{BASE}/works",
                 params={
                     "filter": "primary_location.source.issn:0028-0836,publication_year:2023",
                     "per_page": 10,
                     "sort": "cited_by_count:desc",
                     "mailto": "your@email.com"
                 })
data = r.json()
print(f"Nature papers 2023: {data['meta']['count']}")
for w in data["results"][:5]:
    print(f"  [{w['cited_by_count']} cites] {w['title'][:70]}")
```

## Key Concepts

### Inverted Index Abstracts

OpenAlex stores abstracts as inverted indexes (word → list of positions) rather than plain text due to copyright restrictions. Reconstruct with: `" ".join(words[i] for i in sorted({pos: w for w, ps in inv.items() for pos in ps}))`.

### Cursor-Based Pagination

OpenAlex uses cursor-based pagination (`cursor` parameter) instead of offset. Start with `cursor="*"` and use the `next_cursor` from each response. Maximum 200 results per page; cursor pagination supports up to 10,000 results.

## Common Workflows

### Workflow 1: Systematic Literature Search

**Goal**: Download all papers matching a topic query with metadata for systematic review.

```python
import requests, time, pandas as pd

BASE = "https://api.openalex.org"
MAILTO = "your@email.com"

def systematic_search(query, year_from, year_to, max_results=500):
    """Paginate through results and return a DataFrame."""
    all_results = []
    cursor = "*"
    filters = f"publication_year:{year_from}-{year_to}"

    while len(all_results) < max_results:
        r = requests.get(f"{BASE}/works",
                         params={"search": query, "filter": filters,
                                 "per_page": 200, "cursor": cursor,
                                 "mailto": MAILTO,
                                 "select": "id,doi,title,publication_year,cited_by_count,open_access"})
        r.raise_for_status()
        data = r.json()
        all_results.extend(data["results"])
        cursor = data["meta"].get("next_cursor")
        if not cursor:
            break
        time.sleep(0.1)

    rows = []
    for w in all_results[:max_results]:
        rows.append({
            "openalex_id": w["id"],
            "doi": w.get("doi"),
            "title": w.get("title"),
            "year": w.get("publication_year"),
            "citations": w.get("cited_by_count"),
            "is_oa": w.get("open_access", {}).get("is_oa"),
            "oa_url": w.get("open_access", {}).get("oa_url"),
        })
    return pd.DataFrame(rows)

# Example: papers on drug repurposing 2019-2024
df = systematic_search("drug repurposing machine learning", 2019, 2024, max_results=200)
df.to_csv("drug_repurposing_literature.csv", index=False)
print(f"Retrieved {len(df)} papers")
print(df[["title", "year", "citations", "is_oa"]].head(5).to_string(index=False))
```

### Workflow 2: Author Collaboration Network

**Goal**: Map co-authors for a researcher to analyze their collaboration network.

```python
import requests, time, pandas as pd
from collections import defaultdict

BASE = "https://api.openalex.org"
MAILTO = "your@email.com"

def get_author_works(orcid, max_papers=50):
    r = requests.get(f"{BASE}/works",
                     params={"filter": f"author.orcid:{orcid}",
                             "sort": "cited_by_count:desc",
                             "per_page": min(max_papers, 200),
                             "mailto": MAILTO})
    r.raise_for_status()
    return r.json()["results"]

def extract_collaborators(works):
    collab_count = defaultdict(int)
    for work in works:
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                collab_count[name] += 1
    return collab_count

# Map collaborators for a researcher
orcid = "0000-0001-8742-3594"
works = get_author_works(orcid, max_papers=50)
collabs = extract_collaborators(works)

top_collabs = sorted(collabs.items(), key=lambda x: -x[1])
df = pd.DataFrame(top_collabs, columns=["collaborator", "papers_together"])
df = df[df["collaborator"] != "Jennifer A. Doudna"]  # exclude self
print("Top collaborators:")
print(df.head(10).to_string(index=False))
df.to_csv("collaboration_network.csv", index=False)
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `search` | All | — | text string | Full-text search across title+abstract |
| `filter` | All | — | `field:value,field:value` | Structured filters (AND logic) |
| `per_page` | All | `25` | `1`–`200` | Results per page |
| `cursor` | Pagination | `"*"` | cursor string | Cursor for pagination |
| `sort` | Works | `relevance` | `cited_by_count:desc`, `publication_year:desc` | Result ordering |
| `select` | All | all fields | comma-separated field names | Limit response fields (faster) |
| `group_by` | Works | — | field name | Aggregate counts by field |
| `mailto` | All | — | email address | Polite pool access (prioritized) |

## Best Practices

1. **Always include `mailto`**: Add `mailto=your@email.com` to all requests to join the polite pool and receive priority processing without rate throttling.

2. **Use `select` for large paginations**: When paginating through thousands of results, specify only needed fields (`select=id,doi,title,cited_by_count`) to reduce response size and speed up parsing.

3. **Use cursor pagination, not offset**: OpenAlex does not support offset pagination beyond 10,000 results. Use cursor-based pagination (`cursor` parameter) for deep traversals.

4. **Reconstruct abstracts from inverted index**: Not all works have abstracts; check `abstract_inverted_index is not None` before reconstructing to avoid KeyError.

5. **Cache by work ID**: OpenAlex Work IDs (W…) are stable identifiers. Cache retrieved work metadata to avoid re-fetching within a project.

## Common Recipes

### Recipe: DOI to Metadata Batch Lookup

When to use: Enrich a list of DOIs with citation counts, open-access URLs, and abstracts.

```python
import requests, pandas as pd, time

BASE = "https://api.openalex.org"

dois = [
    "10.1038/s41592-019-0458-z",
    "10.1186/s13059-021-02519-4",
    "10.1038/s41587-019-0071-9",
]

rows = []
for doi in dois:
    r = requests.get(f"{BASE}/works/https://doi.org/{doi}",
                     params={"select": "title,publication_year,cited_by_count,open_access",
                             "mailto": "your@email.com"})
    if r.ok:
        w = r.json()
        rows.append({
            "doi": doi, "title": w.get("title"),
            "year": w.get("publication_year"),
            "citations": w.get("cited_by_count"),
            "is_oa": w.get("open_access", {}).get("is_oa"),
        })
    time.sleep(0.1)

df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

### Recipe: Count Papers by Country

When to use: Geographic analysis of research output on a topic.

```python
import requests, pandas as pd

r = requests.get(
    "https://api.openalex.org/works",
    params={"search": "CRISPR therapeutics",
            "filter": "publication_year:2023",
            "group_by": "authorships.institutions.country_code",
            "per_page": 200,
            "mailto": "your@email.com"}
)
df = pd.DataFrame(r.json()["group_by"]).rename(columns={"key": "country", "count": "papers"})
print(df.sort_values("papers", ascending=False).head(10).to_string(index=False))
```

### Recipe: Find Most-Cited Papers in a Field

When to use: Identify landmark papers on a topic for background reading.

```python
import requests, pandas as pd

r = requests.get(
    "https://api.openalex.org/works",
    params={"search": "protein language model",
            "sort": "cited_by_count:desc",
            "per_page": 10,
            "mailto": "your@email.com"}
)
for w in r.json()["results"]:
    print(f"[{w['cited_by_count']:5d} cites] ({w['publication_year']}) {w['title'][:70]}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 429 Too Many Requests` | Rate limit exceeded | Add `time.sleep(0.15)` between requests; use polite pool (`mailto`) |
| Empty `abstract_inverted_index` | No abstract available | Check for `None` before reconstructing; not all works have abstracts |
| Cursor pagination returns duplicates | Cursor expired | Re-start pagination with `cursor="*"` |
| DOI lookup returns 404 | DOI not indexed in OpenAlex | Try title search instead; OpenAlex indexes 250M+ but not 100% of literature |
| Filter returns 0 results | Field name wrong or filter syntax error | Check filter syntax: `field:value` with no spaces; verify field names in API docs |
| `cited_by_count` is stale | Citation counts update periodically | Counts are refreshed regularly but may lag by days; use for trends not exact figures |

## Related Skills

- `pubmed-database` — Biomedical literature with MeSH controlled vocabulary; better for clinical and life sciences
- `biorxiv-database` — Biomedical preprints not yet indexed in OpenAlex
- `scientific-brainstorming` — Hypothesis generation workflows using literature as input
- `literature-review` — Guide for designing systematic literature reviews using OpenAlex

## References

- [OpenAlex documentation](https://docs.openalex.org/) — Full API reference and data model
- [OpenAlex API endpoint](https://api.openalex.org/) — Interactive API explorer
- [OpenAlex paper (Priem et al. 2022)](https://arxiv.org/abs/2205.01833) — Description of the OpenAlex data system
- [OpenAlex entity types](https://docs.openalex.org/api-entities/works) — Works, Authors, Sources, Institutions, Concepts documentation
