---
name: "uspto-database"
description: "Access USPTO patent data via PatentsView REST API and Google Patents Public Data (BigQuery). Search by inventor, assignee, CPC, or keywords; download metadata and claims; analyze portfolios; track tech trends. For IP landscape analysis, competitor monitoring, prior art search, and tech forecasting in life sciences and biotech."
license: "CC0-1.0"
---

# uspto-database

## Overview

The USPTO provides two primary programmatic access points for patent data: the **PatentsView API** (REST, free, no key required for basic use) for structured queries by inventor, assignee, CPC classification, and keywords; and **Google Patents Public Data** (BigQuery public dataset) for large-scale analytics across the full patent corpus. Both expose data under the CC0 Public Domain Dedication. This skill covers Python-based access patterns for both, plus basic patent portfolio analytics.

## When to Use

- **Prior art search**: Finding existing patents relevant to a technology before filing or to assess freedom-to-operate.
- **Competitor IP landscape analysis**: Querying all patents from a specific assignee (company or institution) to map their technology portfolio.
- **CPC classification search**: Finding patents in a specific technology area using Cooperative Patent Classification codes (e.g., C12N for nucleotides/genetic engineering).
- **Inventor network analysis**: Identifying prolific inventors in a field and their institutional affiliations.
- **Technology trend tracking**: Counting patent filings by year and technology category to identify emerging areas.
- **Life sciences IP analysis**: Searching biotech-specific classifications (A61K for pharmaceuticals, C12N for genetics, G16B for bioinformatics).
- For full-text patent PDF downloads, use the USPTO Bulk Data Storage System (BDSS) or Google Patents direct links.
- **Rate limits**: PatentsView API allows 45 requests/minute without an API key; request a free key for 45 req/min with higher daily limits.

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Optional**: `google-cloud-bigquery` for Google Patents Public Data queries
- **Data requirements**: No account needed for PatentsView basic queries; Google Cloud account required for BigQuery
- **Rate limits**: PatentsView — 45 requests/minute (unauthenticated), higher with free API key

```bash
pip install requests pandas matplotlib
pip install google-cloud-bigquery  # optional: for BigQuery access
```

## Quick Start

```python
import requests
import pandas as pd

# Search PatentsView API: patents assigned to "Genentech" in CPC class C12N
url = "https://api.patentsview.org/patents/query"
payload = {
    "q": {"_and": [
        {"_contains": {"assignee_organization": "Genentech"}},
        {"_contains": {"cpc_subgroup_id": "C12N"}},
    ]},
    "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
    "o": {"per_page": 25},
}
resp = requests.post(url, json=payload)
data = resp.json()
df   = pd.DataFrame(data["patents"])
print(f"Found: {data['total_patent_count']} patents")
print(df[["patent_number", "patent_title", "patent_date"]].head())
```

## Core API

### Query Type 1: Search by Assignee (Company / Institution)

Find all patents granted to a specific organization.

```python
import requests
import pandas as pd

def search_by_assignee(assignee_name: str, per_page: int = 100) -> pd.DataFrame:
    url     = "https://api.patentsview.org/patents/query"
    payload = {
        "q": {"_contains": {"assignee_organization": assignee_name}},
        "f": [
            "patent_number", "patent_title", "patent_date",
            "patent_abstract", "assignee_organization", "assignee_country",
        ],
        "o": {"per_page": per_page, "sort": [{"patent_date": "desc"}]},
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    df   = pd.DataFrame(data.get("patents", []))
    print(f"Assignee '{assignee_name}': {data.get('total_patent_count', 0)} total patents")
    return df

# Example: patents from Broad Institute
df_broad = search_by_assignee("Broad Institute")
print(df_broad[["patent_number", "patent_title", "patent_date"]].head(10))
```

```python
# Paginate through all results for large portfolios
def search_assignee_all_pages(assignee_name: str, page_size: int = 100) -> pd.DataFrame:
    url  = "https://api.patentsview.org/patents/query"
    all_patents = []
    page = 1
    while True:
        payload = {
            "q": {"_contains": {"assignee_organization": assignee_name}},
            "f": ["patent_number", "patent_title", "patent_date", "cpc_subgroup_id"],
            "o": {"per_page": page_size, "page": page},
        }
        resp = requests.post(url, json=payload)
        data = resp.json()
        patents = data.get("patents", [])
        if not patents:
            break
        all_patents.extend(patents)
        total = data.get("total_patent_count", 0)
        if len(all_patents) >= total:
            break
        page += 1

    df = pd.DataFrame(all_patents)
    print(f"Retrieved {len(df)} patents for '{assignee_name}'")
    return df
```

### Query Type 2: Search by CPC Classification

CPC (Cooperative Patent Classification) codes organize patents by technology. Life sciences codes include C12N (nucleotides/genetics), A61K (pharmaceuticals), and G16B (bioinformatics).

```python
import requests
import pandas as pd

# Search by CPC subgroup: C12N15 (mutation/genetic engineering)
url = "https://api.patentsview.org/patents/query"
payload = {
    "q": {"_begins": {"cpc_subgroup_id": "C12N15"}},
    "f": [
        "patent_number", "patent_title", "patent_date",
        "assignee_organization", "cpc_subgroup_id",
    ],
    "o": {"per_page": 50, "sort": [{"patent_date": "desc"}]},
}
resp = requests.post(url, json=payload)
data = resp.json()
df   = pd.DataFrame(data["patents"])
print(f"C12N15 patents: {data['total_patent_count']}")
print(df[["patent_number", "patent_title", "assignee_organization"]].head(10))
```

```python
# Common life sciences CPC codes
CPC_LIFE_SCIENCES = {
    "C12N":    "Microorganisms / enzymes / compositions",
    "C12N15":  "Mutation / genetic engineering",
    "C12Q":    "Measuring / testing involving enzymes or microorganisms",
    "A61K":    "Preparations for medical use",
    "A61P":    "Therapeutic activity of chemical compounds",
    "G16B":    "Bioinformatics",
    "G16H":    "Healthcare informatics",
    "C07K":    "Peptides / proteins",
}
for code, desc in CPC_LIFE_SCIENCES.items():
    print(f"  {code:10s}: {desc}")
```

### Query Type 3: Full-Text Keyword Search

Search patent titles and abstracts for specific terms.

```python
import requests
import pandas as pd

def keyword_search(keyword: str, per_page: int = 50) -> pd.DataFrame:
    url = "https://api.patentsview.org/patents/query"
    payload = {
        "q": {"_or": [
            {"_text_any": {"patent_title":    keyword}},
            {"_text_any": {"patent_abstract": keyword}},
        ]},
        "f": [
            "patent_number", "patent_title", "patent_date",
            "patent_abstract", "assignee_organization",
        ],
        "o": {"per_page": per_page, "sort": [{"patent_date": "desc"}]},
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    df   = pd.DataFrame(data.get("patents", []))
    print(f"Keyword '{keyword}': {data.get('total_patent_count', 0)} patents found")
    return df

# Search for CRISPR-related patents
df_crispr = keyword_search("CRISPR")
print(df_crispr[["patent_number", "patent_title", "patent_date"]].head(10))
```

### Query Type 4: Inventor Search

Find patents by inventor name or retrieve an inventor's full publication history.

```python
import requests
import pandas as pd

# Search by inventor name
url = "https://api.patentsview.org/inventors/query"
payload = {
    "q": {"_and": [
        {"inventor_last_name":  "Doudna"},
        {"inventor_first_name": "Jennifer"},
    ]},
    "f": ["inventor_id", "inventor_first_name", "inventor_last_name",
          "inventor_city", "inventor_state", "inventor_country"],
    "o": {"per_page": 10},
}
resp = requests.post(url, json=payload)
data = resp.json()
print(f"Found {data.get('total_inventor_count', 0)} inventors matching 'Jennifer Doudna'")
for inv in data.get("inventors", []):
    print(f"  ID: {inv['inventor_id']}, Location: {inv.get('inventor_city')}, {inv.get('inventor_country')}")
```

```python
# Get all patents for a specific inventor by inventor_id
inventor_id = "fl:j_ln:doudna-1"   # PatentsView inventor ID format

url = "https://api.patentsview.org/patents/query"
payload = {
    "q": {"inventor_id": inventor_id},
    "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
    "o": {"per_page": 100, "sort": [{"patent_date": "desc"}]},
}
resp  = requests.post(url, json=payload)
data  = resp.json()
df    = pd.DataFrame(data.get("patents", []))
print(f"Patents for inventor {inventor_id}: {data.get('total_patent_count', 0)}")
print(df.head(5))
```

### Query Type 5: Date Range and Combined Filters

Combine multiple filters for targeted searches.

```python
import requests
import pandas as pd

# Patents in gene therapy (CPC A61K48) filed 2020-2024 by a US assignee
url = "https://api.patentsview.org/patents/query"
payload = {
    "q": {"_and": [
        {"_begins":    {"cpc_subgroup_id": "A61K48"}},
        {"_gte":       {"patent_date": "2020-01-01"}},
        {"_lte":       {"patent_date": "2024-12-31"}},
        {"_eq":        {"assignee_country": "US"}},
    ]},
    "f": [
        "patent_number", "patent_title", "patent_date",
        "assignee_organization", "patent_num_claims",
    ],
    "o": {"per_page": 100, "sort": [{"patent_date": "desc"}]},
}
resp = requests.post(url, json=payload)
data = resp.json()
df   = pd.DataFrame(data.get("patents", []))
print(f"Gene therapy patents 2020-2024 (US assignee): {data.get('total_patent_count', 0)}")
print(df[["patent_number", "patent_title", "patent_date", "assignee_organization"]].head(10))
```

### Query Type 6: Google Patents BigQuery

For large-scale corpus analytics, use the public Google Patents dataset in BigQuery.

```python
from google.cloud import bigquery

client = bigquery.Client(project="YOUR_GCP_PROJECT")

# Count CRISPR patents by year (Google Patents public data)
query = """
SELECT
    EXTRACT(YEAR FROM filing_date) AS filing_year,
    COUNT(*)                        AS patent_count,
    COUNT(DISTINCT assignee)        AS unique_assignees
FROM `patents-public-data.patents.publications`
WHERE
    (LOWER(title_localized[SAFE_OFFSET(0)].text) LIKE '%crispr%'
     OR LOWER(abstract_localized[SAFE_OFFSET(0)].text) LIKE '%crispr%')
    AND filing_date >= '2010-01-01'
    AND country_code = 'US'
GROUP BY filing_year
ORDER BY filing_year
"""
df_bq = client.query(query).to_dataframe()
print(df_bq)
print(f"Peak year: {df_bq.loc[df_bq.patent_count.idxmax(), 'filing_year']} "
      f"({df_bq.patent_count.max()} patents)")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `per_page` | PatentsView `"o"` | `25` | `1`–`10000` | Results per API call |
| `page` | PatentsView `"o"` | `1` | `1`–max pages | Page number for pagination |
| `sort` | PatentsView `"o"` | API default | any field + `"asc"`/`"desc"` | Sort order of results |
| `"f"` fields | PatentsView | minimal | any valid field list | Fields returned in response (controls payload size) |
| `"_begins"` | query operator | — | field + prefix string | Prefix match (e.g., CPC code prefix) |
| `"_contains"` | query operator | — | field + substring | Substring search (case-insensitive) |
| `"_text_any"` | query operator | — | field + keywords | Full-text search on title/abstract fields |

## Best Practices

1. **Request only the fields you need**: The `"f"` (fields) parameter controls what is returned. Requesting `patent_abstract` for thousands of patents significantly increases payload size and latency.

2. **Always handle pagination for large result sets**: PatentsView caps responses at 10,000 per page maximum. For queries returning >10,000 results, use date-range slicing or narrower CPC codes to split the query.

3. **Cache API responses to disk**: PatentsView is rate-limited; if building a dataset iteratively, save responses to JSON/CSV after each API call.
   ```python
   import json, pathlib
   cache = pathlib.Path("cache")
   cache.mkdir(exist_ok=True)
   cache_file = cache / "genentech_patents.json"
   if not cache_file.exists():
       resp = requests.post(url, json=payload)
       cache_file.write_text(resp.text)
   data = json.loads(cache_file.read_text())
   ```

4. **Use CPC codes for technology-specific searches, not just keywords**: Keywords miss synonyms and foreign-language patents; CPC codes are assigned by patent examiners and are more systematic.

5. **Validate assignee names**: Company names in patent records vary (e.g., "Genentech Inc.", "Genentech, Inc.", "GENENTECH INC"). Use `_contains` for fuzzy matching, then deduplicate in pandas.

## Common Workflows

### Workflow 1: Technology Landscape Analysis — Filing Trends by Year

**Goal**: Count patents filed in a CPC class by year and plot the trend.

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

def count_patents_by_year(cpc_prefix: str, start_year: int = 2010) -> pd.DataFrame:
    url  = "https://api.patentsview.org/patents/query"
    counts = defaultdict(int)
    page   = 1
    while True:
        payload = {
            "q": {"_and": [
                {"_begins": {"cpc_subgroup_id": cpc_prefix}},
                {"_gte":    {"patent_date": f"{start_year}-01-01"}},
            ]},
            "f": ["patent_number", "patent_date"],
            "o": {"per_page": 10000, "page": page},
        }
        resp    = requests.post(url, json=payload)
        patents = resp.json().get("patents", [])
        if not patents:
            break
        for p in patents:
            year = p["patent_date"][:4]
            counts[year] += 1
        total = resp.json().get("total_patent_count", 0)
        if sum(counts.values()) >= total:
            break
        page += 1

    df = pd.DataFrame(sorted(counts.items()), columns=["year", "count"])
    return df

df_trend = count_patents_by_year("C12N15", start_year=2010)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(df_trend["year"], df_trend["count"], color="steelblue", edgecolor="white")
ax.set_xlabel("Year")
ax.set_ylabel("Patents granted")
ax.set_title("US Patents: C12N15 (Genetic Engineering) by Year")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("cpc_trend.png", dpi=150)
print(f"Trend plotted: {df_trend['count'].sum()} total patents -> cpc_trend.png")
```

### Workflow 2: Assignee Portfolio Comparison

**Goal**: Compare patent counts across multiple biotech companies in a target CPC class.

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

def count_patents_by_assignee(assignees: list, cpc_prefix: str) -> pd.DataFrame:
    url     = "https://api.patentsview.org/patents/query"
    records = []
    for assignee in assignees:
        payload = {
            "q": {"_and": [
                {"_contains": {"assignee_organization": assignee}},
                {"_begins":   {"cpc_subgroup_id": cpc_prefix}},
            ]},
            "f": ["patent_number"],
            "o": {"per_page": 1},  # only need total count
        }
        resp  = requests.post(url, json=payload)
        total = resp.json().get("total_patent_count", 0)
        records.append({"assignee": assignee, "patent_count": total})
        print(f"  {assignee}: {total} patents")

    df = pd.DataFrame(records).sort_values("patent_count", ascending=True)
    return df

companies = ["Genentech", "Amgen", "Regeneron", "AstraZeneca", "Novartis"]
df_comp   = count_patents_by_assignee(companies, cpc_prefix="A61K")

fig, ax = plt.subplots(figsize=(7, 4))
ax.barh(df_comp["assignee"], df_comp["patent_count"], color="salmon")
ax.set_xlabel("Patent count (A61K)")
ax.set_title("Pharmaceutical Patents by Assignee (CPC A61K)")
plt.tight_layout()
plt.savefig("assignee_comparison.png", dpi=150)
print("Comparison chart saved -> assignee_comparison.png")
```

## Expected Outputs

- `pd.DataFrame` with patent records (columns depend on requested `"f"` fields)
- `cpc_trend.png` — bar chart of patent counts by year
- `assignee_comparison.png` — horizontal bar chart comparing companies
- `total_patent_count` in API response gives the full corpus size for a query

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTPError 429 Too Many Requests` | Exceeded 45 req/min rate limit | Add `time.sleep(1.5)` between requests; request a free API key |
| Empty `patents` list in response | Query too narrow or field name incorrect | Check field names in [PatentsView API docs](https://patentsview.org/apis/api-endpoints/patents); test query in the web UI first |
| Results miss known patents | Exact string matching on assignee name | Use `_contains` instead of `_eq`; check for name variants |
| `KeyError: patent_date` | Field not requested in `"f"` list | Add `"patent_date"` to the `"f"` array |
| BigQuery auth error | GCP credentials not configured | Run `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS` |
| CPC prefix returns no results | Invalid CPC code or typo | Verify code at [CPC classification browser](https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/table.html) |

## References

- [PatentsView API Documentation](https://patentsview.org/apis/api-endpoints/patents) — full field list and query operator reference
- [PatentsView API Explorer](https://patentsview.org/query) — browser-based query builder for testing
- [Google Patents Public Data (BigQuery)](https://cloud.google.com/blog/topics/public-datasets/google-patents-public-data-connecting-public-paid-and-private-patent-data) — schema documentation
- [CPC Classification Browser](https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/table.html) — browse life sciences CPC codes
- [USPTO Bulk Data Storage System](https://bulkdata.uspto.gov/) — full-text patent XML downloads
