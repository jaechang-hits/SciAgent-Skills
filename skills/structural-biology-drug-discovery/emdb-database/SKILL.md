---
name: "emdb-database"
description: "Look up EMDB cryo-EM density maps and fitted atomic models via the entry REST API + EBI Search WS. Fetch entry metadata (resolution, method, organism, sample), map download URLs, fitted PDB IDs, and citations. Keyword search via EBI Search. No auth. For atomic coordinates use pdb-database; for AlphaFold predictions use alphafold-database-access."
license: "CC-BY-4.0"
---

# EMDB Database

## Overview

The Electron Microscopy Data Bank (EMDB) at EBI archives 3D electron microscopy density maps — primarily cryo-EM and cryo-ET — for macromolecular assemblies (30,000+ entries: ribosomes, membrane proteins, viruses, large complexes). Access is split across two services:

- **EMDB Entry API** (`https://www.ebi.ac.uk/emdb/api/entry/{EMD-XXXXX}`) — the canonical per-entry JSON containing metadata, map header, fitted PDB list, and citation. Sub-endpoints like `/map`, `/fitted`, `/publications` do **not** exist — all those data live inside the single entry response.
- **EBI Search WS** (`https://www.ebi.ac.uk/ebisearch/ws/rest/emdb`) — the real keyword search backend (the bare `https://www.ebi.ac.uk/emdb/api/search/` endpoint ignores the query and just returns recent entries).

No authentication or API key is required.

## When to Use

- Finding cryo-EM density maps by keyword (e.g., "spike protein", "ribosome 70S")
- Fetching the download URL of a `.map.gz` density file for use in ChimeraX / PyMOL
- Identifying fitted PDB atomic models for an EMDB map (and the reverse)
- Retrieving entry metadata — resolution, reconstruction method, organism, sample
- Listing cryo-EM structures filtered by organism or resolution cutoff
- Pulling the primary citation (journal, DOI, PubMed ID) for an EMDB entry
- Use `pdb-database` instead when you need experimentally determined atomic coordinates
- Use `alphafold-database-access` for AI-predicted structures; EMDB is for experimental EM maps only

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: EMDB entry IDs (`EMD-XXXXX`), keyword search strings, or PDB IDs for cross-referencing
- **Environment**: internet connection; no API key
- **Rate limits**: no official published limits; add `time.sleep(0.2)` between requests in batch loops for polite access

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

EMDB_API   = "https://www.ebi.ac.uk/emdb/api"
EBI_SEARCH = "https://www.ebi.ac.uk/ebisearch/ws/rest/emdb"

# Keyword search via EBI Search WS (NOT /emdb/api/search/, which ignores q=)
r = requests.get(EBI_SEARCH,
                 params={"query": "sars-cov-2 spike", "size": 5, "format": "json",
                         "fields": "id,name,resolution,em_method,organism"},
                 timeout=30)
r.raise_for_status()
res = r.json()
print(f"Total hits: {res['hitCount']}")
for e in res["entries"]:
    f = e["fields"]
    name = (f.get("name") or [""])[0][:60]
    resol = (f.get("resolution") or ["?"])[0]
    print(f"  {e['id']}: {name}  ({resol} Å)")
```

## Core API

### Query 1: Keyword Search (EBI Search WS)

Returns a paged hit list keyed by EMDB ID, with the requested `fields` per entry.

```python
import requests, pandas as pd

EBI_SEARCH = "https://www.ebi.ac.uk/ebisearch/ws/rest/emdb"

def emdb_search(query, size=20, start=0,
                fields="id,name,resolution,em_method,organism"):
    r = requests.get(EBI_SEARCH,
                     params={"query": query, "size": size, "start": start,
                             "format": "json", "fields": fields},
                     timeout=30)
    r.raise_for_status()
    return r.json()

data = emdb_search("ribosome 70S", size=10)
rows = []
for e in data["entries"]:
    f = e["fields"]
    rows.append({
        "emdb_id": e["id"],
        "name": (f.get("name") or [""])[0],
        "resolution_A": float((f.get("resolution") or [0])[0] or 0) or None,
        "em_method": (f.get("em_method") or [""])[0],
        "organism": (f.get("organism") or [""])[0],
    })
df = pd.DataFrame(rows)
print(f"hitCount={data['hitCount']}; first {len(df)} rows:")
print(df.to_string(index=False))
```

```python
# Paged retrieval — iterate `start` until exhausting hitCount
def emdb_search_all(query, size=100, max_pages=5,
                    fields="id,name,resolution,em_method"):
    out = []
    for page in range(max_pages):
        d = emdb_search(query, size=size, start=page * size, fields=fields)
        if not d["entries"]:
            break
        out.extend(d["entries"])
        if len(out) >= d["hitCount"]:
            break
    return out

hits = emdb_search_all("ferritin", size=50, max_pages=2)
print(f"Pulled {len(hits)} ferritin entries")
```

### Query 2: Entry Metadata

The single entry endpoint returns all metadata, the map header, fitted PDB list, and the citation in one document. Read field paths carefully — most are nested.

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def emdb_entry(emdb_id):
    r = requests.get(f"{EMDB_API}/entry/{emdb_id}", timeout=30)
    r.raise_for_status()
    return r.json()

e = emdb_entry("EMD-30210")  # nsp12-nsp7-nsp8 + Remdesivir (RdRp)
print(f"Title       : {e['admin']['title']}")
print(f"Status      : {e['admin']['current_status']}")
print(f"Key dates   : {e['admin'].get('key_dates')}")

sd = e["structure_determination_list"]["structure_determination"][0]
ip = sd["image_processing"][0]
res = ip["final_reconstruction"]["resolution"]
print(f"Method      : {sd['method']}")
print(f"Resolution  : {res['valueOf_']} {res['units']}  (type: {res['res_type']})")
```

### Query 3: Map Header / Download Info

`entry["map"]` contains the file name, format, voxel grid, axis order, cell, contour level(s), and recommended display threshold.

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"
e = requests.get(f"{EMDB_API}/entry/EMD-30210", timeout=30).json()

m = e["map"]
print(f"Map file     : {m.get('file')}")          # e.g. emd_30210.map.gz
print(f"Format       : {m.get('format')}")        # 'CCP4'
print(f"Dimensions   : {m.get('dimensions')}")    # {'col': ..., 'row': ..., 'sec': ...}
print(f"Axis order   : {m.get('axis_order')}")    # {'fast': 'X', 'medium': 'Y', 'slow': 'Z'}
print(f"Contour list : {m.get('contour_list')}")  # recommended threshold(s)

# Conventional FTP/HTTPS download URL pattern (mirror at EBI):
EMDB_FTP = "https://ftp.ebi.ac.uk/pub/databases/emdb/structures"
emdb_num = "EMD-30210"
print(f"Download URL : {EMDB_FTP}/{emdb_num}/map/{m['file']}")
```

### Query 4: Fitted PDB Atomic Models

EMDB cross-references the PDB entries that fitted into the map. Each item has the PDB ID and a relationship tag (e.g., `FULLOVERLAP`).

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"
e = requests.get(f"{EMDB_API}/entry/EMD-30210", timeout=30).json()

pdblist = e.get("crossreferences", {}).get("pdb_list", {})
pdb_refs = pdblist.get("pdb_reference", []) if isinstance(pdblist, dict) else []
print(f"Fitted PDB entries: {len(pdb_refs)}")
for ref in pdb_refs:
    in_frame = (ref.get("relationship") or {}).get("in_frame")
    print(f"  {ref['pdb_id'].upper():6s}  relationship={in_frame}")
# 7BV2  relationship=FULLOVERLAP
```

### Query 5: Citation and Publications

Primary citation lives at `entry["crossreferences"]["citation_list"]`. The shape varies by citation type (journal vs. preprint).

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"
e = requests.get(f"{EMDB_API}/entry/EMD-30210", timeout=30).json()

citations = e.get("crossreferences", {}).get("citation_list", {})
primary = citations.get("primary_citation", {})
ct = primary.get("citation_type") or primary

title   = (ct.get("title") or "").strip()
journal = ct.get("journal") or ct.get("book_title")
year    = ct.get("year")
authors = [a.get("name") or a.get("name_str")
           for a in (ct.get("author") or ct.get("author_order") or [])
           if a]
xrefs = ct.get("external_references", []) or ct.get("xref", [])

doi = next((x.get("valueOf_") for x in xrefs if x.get("type") == "DOI"), None)
pmid = next((x.get("valueOf_") for x in xrefs if x.get("type") == "PUBMED"), None)

print(f"Title   : {title[:80]}")
print(f"Journal : {journal} ({year})")
print(f"Authors : {', '.join(a for a in authors[:5] if a)}{'...' if len(authors) > 5 else ''}")
print(f"DOI     : {doi}")
print(f"PMID    : {pmid}")
```

### Query 6: Sample and Organism

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"
e = requests.get(f"{EMDB_API}/entry/EMD-30210", timeout=30).json()

sample = e.get("sample", {})
sm_list = (sample.get("supramolecule_list") or {}).get("supramolecule", [])
for sm in sm_list:
    ns = sm.get("natural_source") or sm.get("natural_source_list", {}).get("natural_source") or []
    if isinstance(ns, dict):
        ns = [ns]
    for n in ns:
        org = (n.get("organism") or {}).get("valueOf_")
        print(f"  Supramolecule '{sm.get('name', {}).get('valueOf_', '?')}': {org}")
```

## Key Concepts

### Field-Path Map (`/api/entry/{id}` document)

| What | Path |
|------|------|
| Title | `admin.title` |
| Release dates | `admin.key_dates` |
| Authors | `admin.authors_list.author[*].name`/`name_str` |
| EM method | `structure_determination_list.structure_determination[0].method` (e.g. `singleParticle`, `tomography`) |
| Resolution | `structure_determination_list.structure_determination[0].image_processing[0].final_reconstruction.resolution.valueOf_` (string Å; cast to float) |
| Map file name | `map.file` |
| Map format/dims | `map.format` / `map.dimensions` |
| Contour level(s) | `map.contour_list` |
| Fitted PDB | `crossreferences.pdb_list.pdb_reference[*].pdb_id` |
| Citation | `crossreferences.citation_list.primary_citation.citation_type` (journal/year/title/authors/external_references) |
| DOI/PubMed | `…citation_type.external_references[]` with `type` in `{DOI, PUBMED}` |
| Organism | `sample.supramolecule_list.supramolecule[*].natural_source[*].organism.valueOf_` |

### Search vs. Entry

- **Keyword search** → EBI Search WS (`/ebisearch/ws/rest/emdb`). Use this for `query=`, `size=`, `start=`, and `fields=` selection.
- **`/emdb/api/search/` is unreliable** — it silently ignores `q=` and returns the latest released entries. Don't depend on it.
- **Entry detail** → `/emdb/api/entry/{EMD-XXXXX}`. There is **no** `/map`, `/fitted`, or `/publications` sub-endpoint — they're all inside the entry document.

## Common Workflows

### Workflow 1: Resolution Filter for a Topic

**Goal**: Find SARS-CoV-2 spike entries at high resolution and report their fitted PDB models.

```python
import requests, time, pandas as pd

EBI_SEARCH = "https://www.ebi.ac.uk/ebisearch/ws/rest/emdb"
EMDB_API   = "https://www.ebi.ac.uk/emdb/api"

# Step 1: keyword search via EBI Search
hits = []
for start in (0, 50):
    r = requests.get(EBI_SEARCH,
        params={"query": "sars-cov-2 spike", "size": 50, "start": start,
                "format": "json", "fields": "id,name,resolution"},
        timeout=30)
    r.raise_for_status()
    hits.extend(r.json()["entries"])
    time.sleep(0.2)

# Step 2: filter to resolution ≤ 3.0 Å (skip entries with missing field)
rows = []
for h in hits:
    f = h["fields"]
    name = (f.get("name") or [""])[0]
    try:
        resol = float((f.get("resolution") or [None])[0])
    except (TypeError, ValueError):
        continue
    if resol <= 3.0:
        rows.append({"emdb_id": h["id"], "resolution_A": resol, "name": name[:60]})

df = pd.DataFrame(rows).sort_values("resolution_A")
print(f"Spike entries ≤ 3.0 Å: {len(df)}")
print(df.head(10).to_string(index=False))

# Step 3: pull fitted PDB ids for the top 5
for emdb_id in df["emdb_id"].head(5):
    e = requests.get(f"{EMDB_API}/entry/{emdb_id}", timeout=30).json()
    pdblist = e.get("crossreferences", {}).get("pdb_list", {}) or {}
    pdbs = [p["pdb_id"].upper() for p in pdblist.get("pdb_reference", [])]
    print(f"  {emdb_id} -> PDB: {', '.join(pdbs) if pdbs else '(none fitted)'}")
    time.sleep(0.2)
```

### Workflow 2: Build a Cohort Metadata Table

**Goal**: For a query, return a DataFrame with method, resolution, organism, and map download URL — useful for survey papers.

```python
import requests, time, pandas as pd

EBI_SEARCH = "https://www.ebi.ac.uk/ebisearch/ws/rest/emdb"
EMDB_API   = "https://www.ebi.ac.uk/emdb/api"
EMDB_FTP   = "https://ftp.ebi.ac.uk/pub/databases/emdb/structures"

def cohort_table(query, size=10):
    r = requests.get(EBI_SEARCH,
        params={"query": query, "size": size, "format": "json", "fields": "id"},
        timeout=30)
    r.raise_for_status()
    rows = []
    for h in r.json()["entries"]:
        emdb_id = h["id"]
        e = requests.get(f"{EMDB_API}/entry/{emdb_id}", timeout=30).json()
        sd = e["structure_determination_list"]["structure_determination"][0]
        ip = sd["image_processing"][0]
        try:
            resol = float(ip["final_reconstruction"]["resolution"]["valueOf_"])
        except (KeyError, ValueError, TypeError):
            resol = None
        m = e["map"]
        rows.append({
            "emdb_id": emdb_id,
            "title": e["admin"]["title"][:60],
            "method": sd.get("method"),
            "resolution_A": resol,
            "map_url": f"{EMDB_FTP}/{emdb_id}/map/{m['file']}" if m.get("file") else None,
        })
        time.sleep(0.2)
    return pd.DataFrame(rows)

df = cohort_table("ribosome 70S bacterial", size=6)
print(df.to_string(index=False))
df.to_csv("emdb_cohort.csv", index=False)
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `query` | EBI Search `/emdb` | required | text search string | Keyword to match |
| `size` | EBI Search `/emdb` | `15` | 1–100 | Hits per page |
| `start` | EBI Search `/emdb` | `0` | non-negative int | Pagination offset |
| `fields` | EBI Search `/emdb` | (subset) | comma-separated EBI Search fields | Which per-hit fields to return (`id,name,resolution,em_method,organism`, etc.) |
| `format` | EBI Search `/emdb` | `json` | `json`, `xml` | Response format |
| (path) `{EMD-XXXXX}` | `/api/entry/{id}` | required | EMDB accession | Single-entry detail |

## Best Practices

1. **Always use EBI Search WS for keyword search.** `https://www.ebi.ac.uk/emdb/api/search/` ignores `q=` and just returns the latest releases — relying on it produces silently wrong cohorts.
2. **There are no sub-endpoints.** Don't call `/api/entry/{id}/map`, `/fitted`, `/publications`, or `/api/statistics/` — all return 404 (or HTML for `/statistics/`). Read everything from the single entry document.
3. **Cast `resolution.valueOf_` to float explicitly.** The field is a string like `"2.5"`; numeric filters need an explicit cast (with `try/except` for entries that lack a value).
4. **EBI Search field values arrive as lists.** Even single-valued fields like `name` come as `{"name": ["..."]}` — always index `[0]` or join.
5. **Add `time.sleep(0.2)` in entry-by-entry loops.** No rate limit is published, but the API is hosted on a shared service; polite spacing avoids transient 502s.
6. **Map download URLs follow `https://ftp.ebi.ac.uk/pub/databases/emdb/structures/{EMDB_ID}/map/{file}`** — derive them from `entry["map"]["file"]`, don't hardcode.

## Common Recipes

### Recipe: PDB → EMDB Cross-Reference

```python
import requests

# Given an EMDB ID, get its fitted PDB; given a PDB ID, you'd query
# RCSB PDB /rest/v2/entry/{pdb_id} and read `rcsb_external_references.emdb_id`.
EMDB_API = "https://www.ebi.ac.uk/emdb/api"
e = requests.get(f"{EMDB_API}/entry/EMD-30210", timeout=30).json()
pdblist = e.get("crossreferences", {}).get("pdb_list") or {}
print({"emdb": e["emdb_id"],
       "pdbs": [p["pdb_id"].upper() for p in pdblist.get("pdb_reference", [])]})
```

### Recipe: Top Resolutions for an Organism

```python
import requests, time, pandas as pd

EBI_SEARCH = "https://www.ebi.ac.uk/ebisearch/ws/rest/emdb"

def best_by_organism(organism, size=50):
    r = requests.get(EBI_SEARCH,
        params={"query": f'organism:"{organism}"', "size": size,
                "format": "json", "fields": "id,name,resolution"},
        timeout=30)
    r.raise_for_status()
    rows = []
    for h in r.json()["entries"]:
        f = h["fields"]
        try:
            resol = float((f.get("resolution") or [None])[0])
        except (TypeError, ValueError):
            continue
        rows.append({"emdb_id": h["id"], "resolution_A": resol,
                     "name": (f.get("name") or [""])[0][:60]})
    return pd.DataFrame(rows).sort_values("resolution_A").reset_index(drop=True)

df = best_by_organism("Saccharomyces cerevisiae", size=20)
print(df.head(8).to_string(index=False))
```

### Recipe: Citation Export (BibTeX-ready)

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"
e = requests.get(f"{EMDB_API}/entry/EMD-30210", timeout=30).json()
ct = (e.get("crossreferences", {})
        .get("citation_list", {})
        .get("primary_citation", {})
        .get("citation_type")) or {}
authors = [a.get("name") or a.get("name_str")
           for a in (ct.get("author") or ct.get("author_order") or [])]
xrefs = ct.get("external_references", []) or ct.get("xref", [])
doi = next((x.get("valueOf_") for x in xrefs if x.get("type") == "DOI"), "")
print({"title": (ct.get("title") or "").strip(),
       "journal": ct.get("journal"),
       "year": ct.get("year"),
       "authors_n": len(authors),
       "doi": doi})
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `KeyError: 'results'` or `'numFound'` on EMDB search | `/api/search/` returns a raw JSON array and ignores `q=` | Use EBI Search WS (`/ebisearch/ws/rest/emdb`) — wrapper is `{hitCount, entries, facets}` |
| HTTP 404 on `/api/entry/{id}/map` (or `/fitted`, `/publications`) | These sub-endpoints don't exist | Read `entry["map"]`, `entry["crossreferences"]["pdb_list"]`, `entry["crossreferences"]["citation_list"]` from the single entry response |
| Resolution comes back as a string | EMDB stores numeric fields as strings | `float(entry[...]['resolution']['valueOf_'])` — wrap in try/except |
| EBI Search fields look like single-element lists | EBI Search returns multi-valued fields as lists | Read `f["name"][0]` (or fall back to `(... or [""])[0]`) |
| Empty `entries` from EBI Search | Wrong field qualifier or typo | Drop the field qualifier, search plain text; check at https://www.ebi.ac.uk/ebisearch/ |
| HTML response from `/api/statistics/` | `/statistics/` returns HTML, not JSON | Endpoint is for the web UI; don't call it programmatically |
| `pdb_list` is `{}` for an entry | Map has no fitted atomic model | This is genuine — many tomograms / sub-tomogram averages lack fitted PDB |

## Related Skills

- `pdb-database` — RCSB PDB for the atomic-model side of EMDB cross-references
- `alphafold-database-access` — AI-predicted structures (complement to experimental EMDB maps)
- `uniprot-protein-database` — Resolve organism / sequence context for an EMDB sample
- `cellxgene-census` — Tissue/cell-type expression data complementary to structural surveys

## References

- [EMDB at EBI](https://www.ebi.ac.uk/emdb/) — Browse, download, statistics, deposition
- [EMDB Entry API](https://www.ebi.ac.uk/emdb/api/entry/EMD-30210) — Example entry JSON
- [EBI Search WS — EMDB](https://www.ebi.ac.uk/ebisearch/swagger.ebi#/emdb) — Keyword search docs
- [EMDB FTP mirror](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/) — Density map and metadata downloads
- Lawson CL et al. "EMDB — the Electron Microscopy Data Bank." *Nucleic Acids Research* 52(D1): D456–D465 (2024). https://doi.org/10.1093/nar/gkad1019
