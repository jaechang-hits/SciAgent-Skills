---
name: "protocolsio-integration"
description: "Access protocols.io public library via REST API. Search and retrieve experimental protocols (wet-lab, bioinformatics, clinical) by keyword, DOI, or category. Download step-by-step protocol content including reagents, materials, equipment, and timing. Free public access; authentication needed for private protocols or publishing. Use alongside opentrons-integration or benchling-integration to programmatically execute downloaded protocols."
license: "CC-BY-4.0"
---

# protocols.io Integration

## Overview

protocols.io is the leading protocol repository for life sciences with 90,000+ open-access experimental protocols covering molecular biology, cell biology, bioinformatics, clinical research, and lab automation. The REST API provides programmatic access to protocol search, full protocol retrieval (steps, reagents, materials, equipment), protocol versioning, workspace management, and protocol publishing. Public protocols are freely accessible; authentication (OAuth2 token) is required for private protocols or creating/editing.

## When to Use

- Searching for validated wet-lab protocols by keyword, technique, or journal article DOI
- Retrieving the full step-by-step content of a protocol (reagents, timing, volumes, notes) for automation or analysis
- Finding protocols associated with a specific reagent, kit, or instrument
- Building lab automation workflows by extracting protocol steps and reagent lists programmatically
- Verifying protocol versions and citing the correct DOI for methods sections
- Discovering community-validated protocols as alternatives to proprietary methods
- Use alongside `opentrons-integration` or `benchling-integration` to implement downloaded protocols in automated workflows

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **Data requirements**: protocol keywords, DOIs, or protocols.io protocol IDs
- **Environment**: internet connection; public protocols: no auth needed; private: OAuth2 token from https://www.protocols.io/developers
- **Rate limits**: 10 requests/second for public API; unauthenticated requests allowed for public protocols

```bash
pip install requests pandas
# For private protocol access or publishing:
# Register at https://www.protocols.io/developers to obtain an API token
```

## Quick Start

```python
import requests

BASE = "https://www.protocols.io/api/v4"
# For public protocols, no token needed (but add for higher rate limits)
HEADERS = {"Authorization": "Bearer YOUR_TOKEN_HERE"}  # Optional for public

# Search for CRISPR protocols
r = requests.get(f"{BASE}/protocols",
                 params={"q": "CRISPR guide RNA design", "order_field": "views",
                         "page_size": 5},
                 headers=HEADERS)
r.raise_for_status()
data = r.json()
print(f"Total CRISPR protocols: {data['pagination']['total_results']}")
for p in data["items"][:3]:
    print(f"\n  {p['title']}")
    print(f"  DOI: {p.get('doi')} | Views: {p.get('stats', {}).get('number_of_views')}")
    print(f"  Authors: {', '.join(a['name'] for a in p.get('creators', [])[:3])}")
```

## Core API

### Query 1: Protocol Search

Search the protocols.io public library by keyword, technique, or full-text.

```python
import requests, pandas as pd

BASE = "https://www.protocols.io/api/v4"

def search_protocols(query, page_size=20, order_field="relevance", category_id=None):
    params = {"q": query, "page_size": page_size, "order_field": order_field}
    if category_id:
        params["filter[categories_ids][]"] = category_id
    r = requests.get(f"{BASE}/protocols", params=params)
    r.raise_for_status()
    return r.json()

data = search_protocols("RNA extraction tissue", page_size=10, order_field="views")
total = data["pagination"]["total_results"]
print(f"RNA extraction protocols: {total}")

rows = []
for p in data["items"][:10]:
    rows.append({
        "id": p.get("id"),
        "title": p.get("title"),
        "doi": p.get("doi"),
        "views": p.get("stats", {}).get("number_of_views", 0),
        "created": p.get("created_on"),
        "category": p.get("categories", [{}])[0].get("name", "n/a"),
    })
df = pd.DataFrame(rows).sort_values("views", ascending=False)
print(df.to_string(index=False))
```

```python
# Search with category filter (get category IDs from /categories endpoint)
data_pcr = search_protocols("qPCR primer design", order_field="views")
print(f"\nqPCR protocols: {data_pcr['pagination']['total_results']}")
for p in data_pcr["items"][:3]:
    print(f"  {p['title'][:70]} (DOI: {p.get('doi', 'n/a')})")
```

### Query 2: Retrieve Full Protocol Content

Fetch the complete protocol with steps, reagents, materials, and equipment.

```python
import requests

BASE = "https://www.protocols.io/api/v4"

def get_protocol(protocol_id):
    r = requests.get(f"{BASE}/protocols/{protocol_id}")
    r.raise_for_status()
    return r.json()

# Retrieve protocol by ID (from search results or DOI lookup)
protocol_id = 45979  # Example: a public protocol
data = get_protocol(protocol_id)
protocol = data.get("payload", data)  # Handle API response structure

print(f"Title: {protocol.get('title')}")
print(f"DOI: {protocol.get('doi')}")
print(f"Authors: {', '.join(a['name'] for a in protocol.get('creators', []))}")
print(f"Steps: {len(protocol.get('steps', []))}")
print(f"Materials: {len(protocol.get('materials', []))}")
print(f"Abstract: {protocol.get('description', '')[:200]}")
```

```python
# Parse protocol steps
protocol_steps = protocol.get("steps", [])
for i, step in enumerate(protocol_steps[:5], 1):
    step_desc = step.get("description", "")
    duration = step.get("duration", {})
    print(f"\nStep {i}: {step_desc[:120]}")
    if duration:
        print(f"  Duration: {duration.get('duration')} {duration.get('unit_label', '')}")
```

### Query 3: Retrieve Protocol by DOI

Fetch a protocol using its DOI for precise citation-based retrieval.

```python
import requests, json

BASE = "https://www.protocols.io/api/v4"

def get_protocol_by_doi(doi):
    """Retrieve protocol using its DOI."""
    # URL-encode the DOI for the query
    r = requests.get(f"{BASE}/protocols",
                     params={"q": doi, "page_size": 5})
    r.raise_for_status()
    items = r.json()["items"]
    for item in items:
        if item.get("doi") == doi:
            return item
    return None

doi = "10.17504/protocols.io.bvb3n2qn"  # Example protocols.io DOI
protocol = get_protocol_by_doi(doi)
if protocol:
    print(f"Found: {protocol['title']}")
    print(f"  ID: {protocol['id']}")
    print(f"  Version: {protocol.get('version_id')}")
```

### Query 4: Extract Reagents and Materials

Parse out the materials list from a retrieved protocol.

```python
import requests, pandas as pd

BASE = "https://www.protocols.io/api/v4"

def get_reagents(protocol_id):
    r = requests.get(f"{BASE}/protocols/{protocol_id}")
    r.raise_for_status()
    data = r.json()
    protocol = data.get("payload", data)
    return protocol.get("materials", [])

# Get reagents list
materials = get_reagents(45979)  # Example protocol ID
print(f"Materials ({len(materials)} items):")
rows = []
for m in materials[:10]:
    rows.append({
        "name": m.get("name"),
        "quantity": m.get("quantity"),
        "unit": m.get("unit", {}).get("name", ""),
        "supplier": m.get("supplier", {}).get("name", ""),
        "catalog": m.get("sku"),
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

### Query 5: Browse Protocol Categories

List available protocol categories for targeted searches.

```python
import requests, pandas as pd

BASE = "https://www.protocols.io/api/v4"

r = requests.get(f"{BASE}/categories")
r.raise_for_status()
data = r.json()
categories = data.get("items", data.get("payload", []))

print(f"protocols.io categories: {len(categories)}")
df = pd.DataFrame(categories)[["id", "name"]].head(20)
print(df.to_string(index=False))
```

### Query 6: List Protocol Versions

Retrieve version history for a protocol to track updates.

```python
import requests

BASE = "https://www.protocols.io/api/v4"

def get_protocol_versions(protocol_id):
    r = requests.get(f"{BASE}/protocols/{protocol_id}")
    r.raise_for_status()
    protocol = r.json().get("payload", r.json())
    return {
        "title": protocol.get("title"),
        "version": protocol.get("version_id"),
        "published": protocol.get("published_on"),
        "doi": protocol.get("doi"),
        "parent_doi": protocol.get("parent_publication", {}).get("doi"),
    }

info = get_protocol_versions(45979)
for k, v in info.items():
    print(f"  {k}: {v}")
```

## Key Concepts

### Protocol DOIs and Versioning

Each published protocols.io protocol has a citable DOI (format: `10.17504/protocols.io.XXXXX`). When a protocol is updated, a new version is created with a new DOI while the original DOI remains valid. Always cite the specific version DOI in methods sections for reproducibility.

### API Authentication

Public protocols are accessible without authentication. OAuth2 Bearer tokens are needed for: private protocols, workspace management, protocol creation/editing, and user-specific queries. Obtain tokens at https://www.protocols.io/developers.

## Common Workflows

### Workflow 1: Protocol Discovery and Comparison

**Goal**: Search for protocols matching a technique, compare them, and select the best one for adaptation.

```python
import requests, pandas as pd

BASE = "https://www.protocols.io/api/v4"

def search_and_rank(query, top_n=20):
    """Search protocols and return ranked by views + forks."""
    r = requests.get(f"{BASE}/protocols",
                     params={"q": query, "page_size": top_n, "order_field": "views"})
    r.raise_for_status()
    data = r.json()

    rows = []
    for p in data["items"]:
        stats = p.get("stats", {})
        rows.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "doi": p.get("doi"),
            "views": stats.get("number_of_views", 0),
            "forks": stats.get("number_of_forks", 0),
            "steps": p.get("number_of_steps"),
            "created": p.get("created_on")[:10] if p.get("created_on") else "n/a",
            "category": p.get("categories", [{}])[0].get("name", "n/a"),
        })

    df = pd.DataFrame(rows)
    df["popularity_score"] = df["views"] * 0.7 + df["forks"] * 0.3 * 100
    return df.sort_values("popularity_score", ascending=False)

# Compare western blotting protocols
df = search_and_rank("western blot protein detection", top_n=15)
df.to_csv("western_blot_protocols.csv", index=False)
print("Top western blot protocols:")
print(df[["title", "views", "forks", "steps"]].head(8).to_string(index=False))
```

### Workflow 2: Protocol Step Extraction for Automation

**Goal**: Extract protocol steps, timing, and reagent volumes for downstream automation scripting.

```python
import requests, pandas as pd

BASE = "https://www.protocols.io/api/v4"

def extract_protocol_steps(protocol_id):
    """Extract structured step data from a protocol."""
    r = requests.get(f"{BASE}/protocols/{protocol_id}")
    r.raise_for_status()
    protocol = r.json().get("payload", r.json())

    steps = []
    for i, step in enumerate(protocol.get("steps", []), 1):
        duration = step.get("duration", {})
        steps.append({
            "step_number": i,
            "description": step.get("description", ""),
            "duration_value": duration.get("duration"),
            "duration_unit": duration.get("unit_label", ""),
            "temperature": step.get("temperature", {}).get("value"),
            "temp_unit": step.get("temperature", {}).get("unit_label", ""),
        })

    materials = [{
        "name": m.get("name"),
        "quantity": m.get("quantity"),
        "unit": m.get("unit", {}).get("name", ""),
    } for m in protocol.get("materials", [])]

    return {
        "title": protocol.get("title"),
        "doi": protocol.get("doi"),
        "steps": pd.DataFrame(steps),
        "materials": pd.DataFrame(materials),
    }

result = extract_protocol_steps(45979)
print(f"Protocol: {result['title']}")
print(f"\nSteps ({len(result['steps'])}):")
print(result["steps"][["step_number", "description", "duration_value", "duration_unit"]].head(5).to_string(index=False))
print(f"\nMaterials ({len(result['materials'])}):")
print(result["materials"].head(5).to_string(index=False))

# Export for automation
result["steps"].to_csv("protocol_steps.csv", index=False)
result["materials"].to_csv("protocol_materials.csv", index=False)
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `q` | Search | — | keyword string | Full-text search query |
| `order_field` | Search | `"relevance"` | `"relevance"`, `"views"`, `"date"`, `"activity"` | Sort order for results |
| `page_size` | Search | `10` | `1`–`50` | Results per page |
| `page_id` | Search | `1` | integer | Page number for pagination |
| `filter[categories_ids][]` | Search | — | category integer ID | Filter by protocol category |
| Protocol ID | Retrieve | required | integer | Specific protocol to fetch |

## Best Practices

1. **Sort by views for quality**: Use `order_field=views` when searching for well-validated protocols, as highly-viewed protocols have been tested by many groups.

2. **Always cite the specific DOI**: protocols.io DOIs are versioned; cite the exact version DOI (not just the protocol title) in methods sections so readers can reproduce your exact protocol.

3. **Check license before use**: All public protocols.io protocols are CC-BY 4.0 by default. Commercial use requires checking individual protocol licenses.

4. **Extract materials list for reagent ordering**: The materials API returns catalog numbers and supplier names, enabling direct procurement list generation.

5. **Store protocol ID + DOI for reproducibility**: Record both the integer ID (for API access) and the DOI (for stable citation) when selecting protocols for a project.

## Common Recipes

### Recipe: Search by Reagent Name

When to use: Find protocols that use a specific commercial kit or reagent.

```python
import requests

r = requests.get("https://www.protocols.io/api/v4/protocols",
                 params={"q": "RNeasy Mini Kit RNA extraction", "page_size": 5,
                         "order_field": "views"})
data = r.json()
print(f"Protocols using RNeasy: {data['pagination']['total_results']}")
for p in data["items"][:3]:
    print(f"  {p['title'][:70]} ({p.get('doi', 'n/a')})")
```

### Recipe: Get Protocol Citation for Methods Section

When to use: Generate a citation string for a methods section.

```python
import requests

protocol_id = 45979
r = requests.get(f"https://www.protocols.io/api/v4/protocols/{protocol_id}")
p = r.json().get("payload", r.json())
authors = "; ".join(a["name"] for a in p.get("creators", [])[:3])
print(f"Citation: {authors} ({p.get('created_on', '')[:4]}). ")
print(f"{p.get('title')}. protocols.io. https://doi.org/{p.get('doi')}")
```

### Recipe: Find Most-Forked Protocols

When to use: Identify widely-adapted protocols (high forks = adapted by many labs).

```python
import requests, pandas as pd

r = requests.get("https://www.protocols.io/api/v4/protocols",
                 params={"q": "ChIP-seq chromatin", "page_size": 20})
data = r.json()
df = pd.DataFrame([{
    "title": p["title"][:60],
    "forks": p.get("stats", {}).get("number_of_forks", 0),
    "views": p.get("stats", {}).get("number_of_views", 0),
} for p in data["items"]])
print(df.sort_values("forks", ascending=False).head(5).to_string(index=False))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `items` in search | Query too specific or no match | Broaden query; remove special characters |
| `HTTP 401` accessing protocol | Private protocol without auth | Obtain OAuth2 token; public protocols don't need auth |
| Protocol steps have empty descriptions | Protocol uses rich text formatting | Strip HTML tags from `description` with `re.sub(r'<[^>]+>', '', text)` |
| `materials` list is empty | Protocol has no structured materials | Materials may be embedded in step descriptions as free text |
| DOI lookup returns wrong protocol | Similar title match instead of DOI | Compare DOI field exactly; use string equality check `if item.get("doi") == doi` |
| Rate limit errors | >10 requests/second | Add `time.sleep(0.15)` between requests |

## Related Skills

- `opentrons-integration` — Execute protocols on Opentrons liquid handling robots using steps extracted via this skill
- `benchling-integration` — Store retrieved protocols in Benchling ELN with reagent tracking
- `scientific-manuscript-writing` — Reference protocols correctly in methods sections using protocols.io DOIs

## References

- [protocols.io API documentation](https://www.protocols.io/developers) — Official REST API reference
- [protocols.io platform](https://www.protocols.io/) — Public protocol library and search
- [protocols.io citation guide](https://www.protocols.io/researcher-tools/citing-protocols) — How to cite protocols.io in publications
- [Teytelman et al. (2016) Nature Methods](https://doi.org/10.1038/nmeth.3999) — protocols.io platform description paper
