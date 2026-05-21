---
name: "pride-database"
description: "Search the PRIDE Archive v3 REST API for proteomics datasets: discover projects by keyword + faceted filters (organism, instrument, disease, software), fetch project metadata, list and download RAW/PEAK/RESULT/FASTA files (with FTP/Aspera URLs), look up which projects mention a UniProt accession, and find similar projects. PRIDE v3 no longer exposes peptide/PSM-level identification endpoints — for spectrum-level data download the project's RESULT files. Use uniprot-protein-database for protein sequences; interpro-database for domain architecture."
license: "Apache-2.0"
---

# PRIDE Database

## Overview

The PRIDE Archive (ProteomicsIDEntifications database) at EMBL-EBI is the world's largest public mass-spectrometry proteomics repository — 39,000+ projects and 3.4M+ deposited files as of 2026. Programmatic access is via a JSON REST API at `https://www.ebi.ac.uk/pride/ws/archive/v3/`. No authentication is required. The OpenAPI/Swagger spec is at `https://www.ebi.ac.uk/pride/ws/archive/v3/v3/api-docs`. PRIDE v3 returns **plain JSON arrays** for list endpoints (no HAL+JSON `_embedded` envelope) and intentionally does not expose per-peptide or per-PSM identification endpoints — for spectrum-level identifications, download the project's `RESULT` files (mzIdentML, MaxQuant txt, etc.) and parse them locally.

## When to Use

- Finding published proteomics datasets by free-text keyword and facet filters (organism, tissue, disease, instrument, software, PTM) for meta-analysis or benchmarking
- Downloading raw mass-spectrometry data (RAW, mzML, MGF) or pre-processed identifications (RESULT files) from a specific PRIDE project accession
- Looking up which PRIDE projects mention a specific UniProt protein accession (project-level occurrence map only — no PSM/coverage counts at the API surface)
- Finding similar projects to one of interest for reanalysis or cross-study comparison
- Fetching SDRF (Sample-Data Relationship Format) files for projects so you can model the sample-to-MS-run mapping programmatically
- Discovering valid filter values via faceted search before constructing a structured query
- For protein sequences, Swiss-Prot annotations, and ID mapping use `uniprot-protein-database`
- For protein domain and family classification use `interpro-database` — PRIDE only reports project-level occurrence, not domain-level features
- **PRIDE v3 has no `/peptides`, `/psms`, or `/proteins?proteinAccession=` endpoints** — if you need peptide- or PSM-level data, download the RESULT files from `/projects/{accession}/files` and parse them with `pyteomics` or a search-engine-specific reader

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: a PRIDE project accession (`PXD######` format) or a search keyword, optionally a UniProt accession for protein-occurrence lookup
- **Environment**: internet connection; no API key required
- **Rate limits**: not formally published; keep bursts under ~5 requests/second and add `time.sleep(0.3)` in loops

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

# 1) Free-text search for cancer proteomics projects
projects = requests.get(f"{PRIDE}/search/projects",
                        params={"keyword": "prostate cancer", "pageSize": 5},
                        timeout=30).json()
print(f"Top {len(projects)} projects:")
for p in projects[:3]:
    instr = ", ".join(p.get("instruments", []))[:50]
    print(f"  {p['accession']}  {(p['title'] or '')[:70]}  [{instr}]")

# 2) Drill into one project
acc = projects[0]["accession"]
proj = requests.get(f"{PRIDE}/projects/{acc}", timeout=30).json()
print(f"\n{proj['accession']}: {proj['title'][:70]}")
print(f"  Submitted: {proj.get('submissionDate')}  DOI: {proj.get('doi')}")
print(f"  Organisms: {[o['name'] for o in proj.get('organisms', [])]}")
print(f"  Instruments: {[i['name'] for i in proj.get('instruments', [])]}")

# 3) List files and total size
files = requests.get(f"{PRIDE}/projects/{acc}/files/all", timeout=60).json()
total_mb = sum(f.get("fileSizeBytes", 0) for f in files) / 1e6
print(f"\n  {len(files)} files, {total_mb:.0f} MB total")
```

## Core API

### Module 1: Project Search — `/search/projects`

Free-text search with optional facet-based filtering, pagination, and sorting. Returns a plain JSON array of project records — there is no HAL+JSON `_embedded`/`page` wrapper.

```python
import requests, pandas as pd

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def search_projects(keyword=None, organism=None, instrument=None,
                    disease=None, software=None,
                    page_size=25, page=0, sort_field="submission_date",
                    sort_direction="DESC"):
    """Search PRIDE v3 for projects.
    Filter syntax (for the `filter` arg) is `field==value, field==value` using `_facet` field names
    that are discoverable via /facet/projects."""
    filters = []
    if organism:   filters.append(f"organisms_facet=={organism}")
    if instrument: filters.append(f"instruments_facet=={instrument}")
    if disease:    filters.append(f"diseases_facet=={disease}")
    if software:   filters.append(f"softwares_facet=={software}")

    params = {"pageSize": page_size, "page": page,
              "sortFields": sort_field, "sortDirection": sort_direction}
    if keyword: params["keyword"] = keyword
    if filters: params["filter"] = ",".join(filters)

    r = requests.get(f"{PRIDE}/search/projects", params=params, timeout=30)
    r.raise_for_status()
    return r.json()   # plain list[dict]

projects = search_projects(keyword="cancer", organism="Homo sapiens (human)",
                           instrument="Q Exactive", page_size=5)
df = pd.DataFrame([{
    "accession": p["accession"],
    "title": (p.get("title") or "")[:70],
    "submission_date": p.get("submissionDate"),
    "diseases": ", ".join(p.get("diseases", []))[:60],
    "instruments": ", ".join(p.get("instruments", []))[:50],
} for p in projects])
print(df.to_string(index=False))
```

```python
# Paginate through all matches for a keyword. The API doesn't return total counts inline;
# walk pages until the next one is empty.
def search_all_projects(keyword, page_size=100, max_pages=20):
    all_records, page = [], 0
    while page < max_pages:
        batch = search_projects(keyword=keyword, page_size=page_size, page=page)
        if not batch:
            break
        all_records.extend(batch)
        if len(batch) < page_size:
            break    # last page
        page += 1
    return all_records

results = search_all_projects("phosphoproteomics", page_size=100, max_pages=3)
print(f"Phosphoproteomics projects collected (max 300): {len(results)}")
```

### Module 2: Faceted Filter Discovery — `/facet/projects`

Before constructing a filtered search, query the facet endpoint to see which instrument / organism / disease / software values actually exist for a given keyword, along with their counts. The response is a dict of facet groups, each mapping `{value: count}`.

```python
import requests, pandas as pd

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def get_facets(keyword=None, facet_page_size=20):
    """Return facet counts for projects matching `keyword`. Keys are facet groups
    (instruments, organisms, diseases, softwares, experimentTypes, ...); values are
    dicts of {value: count}."""
    params = {"facetPageSize": facet_page_size}
    if keyword: params["keyword"] = keyword
    r = requests.get(f"{PRIDE}/facet/projects", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

facets = get_facets(keyword="cancer", facet_page_size=10)
print(f"Facet groups: {list(facets.keys())}")
print(f"\nTop instruments for 'cancer':")
for instr, n in sorted(facets.get("instruments", {}).items(), key=lambda kv: -kv[1])[:8]:
    print(f"  {instr:<35} {n}")
print(f"\nTop diseases:")
for d, n in sorted(facets.get("diseases", {}).items(), key=lambda kv: -kv[1])[:6]:
    print(f"  {d:<55} {n}")
```

### Module 3: Project Detail — `/projects/{accession}`

Full metadata for a single project: submitters, labPIs, instruments, organisms (CV-coded), diseases, experiment types, references, DOI, submission/publication dates. Lists are `CvParam`-style objects with `accession`, `cvLabel`, `name`, optionally `value`.

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def get_project(accession):
    r = requests.get(f"{PRIDE}/projects/{accession}", timeout=30)
    r.raise_for_status()
    return r.json()

p = get_project("PXD004131")
print(f"Accession    : {p['accession']}")
print(f"Title        : {p['title'][:80]}")
print(f"Submission   : {p.get('submissionDate')}")
print(f"Publication  : {p.get('publicationDate')}")
print(f"DOI          : {p.get('doi')}")
print(f"License      : {p.get('license')}")
print(f"Type         : {p.get('submissionType')}")
print(f"Organisms    : {[o['name'] for o in p.get('organisms', [])]}")
print(f"Instruments  : {[i['name'] for i in p.get('instruments', [])]}")
print(f"Experiment   : {[e['name'] for e in p.get('experimentTypes', [])]}")
print(f"PIs          : {[pi.get('name') for pi in p.get('labPIs', [])]}")
print(f"References   : {[r.get('doi') for r in p.get('references', [])[:3]]}")
```

### Module 4: Project Files — `/projects/{accession}/files` + `/files/all`

List the files associated with a project. Use the paginated endpoint for large projects; `/files/all` returns every file in one shot. Each file record carries `fileCategory.value` (one of `RAW`, `PEAK`, `RESULT`, `FASTA`, `OTHER`), `fileSizeBytes` (note the `Bytes` suffix — not `fileSize`), and a list of `publicFileLocations` each labeled `FTP Protocol` or `Aspera Protocol`.

```python
import requests, pandas as pd

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def get_project_files(accession, file_type=None, page_size=100):
    """Walk paginated /files for a project. Optionally filter by category code
    (RAW, PEAK, RESULT, FASTA, OTHER). Returns a DataFrame."""
    rows, page = [], 0
    while True:
        r = requests.get(f"{PRIDE}/projects/{accession}/files",
                         params={"pageSize": page_size, "page": page},
                         timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        for f in batch:
            cat = f.get("fileCategory") or {}
            ftp = next((loc["value"] for loc in f.get("publicFileLocations", [])
                        if loc.get("name") == "FTP Protocol"), "")
            asp = next((loc["value"] for loc in f.get("publicFileLocations", [])
                        if loc.get("name") == "Aspera Protocol"), "")
            rows.append({
                "file_name": f.get("fileName"),
                "category": cat.get("value"),     # RAW/PEAK/RESULT/FASTA/OTHER
                "size_mb": round((f.get("fileSizeBytes") or 0) / 1e6, 2),
                "ftp_url": ftp,
                "aspera_url": asp,
                "downloads": f.get("totalDownloads"),
            })
        if len(batch) < page_size:
            break
        page += 1

    df = pd.DataFrame(rows)
    if file_type:
        df = df[df["category"] == file_type]
    return df

files_df = get_project_files("PXD004131")
print(f"Total files: {len(files_df)}")
print(files_df.groupby("category")["size_mb"].agg(["count", "sum"]).round(1).to_string())

raw_only = files_df[files_df["category"] == "RAW"]
print(f"\nRAW files: {len(raw_only)}; combined {raw_only['size_mb'].sum():.0f} MB")
print(raw_only[["file_name", "size_mb", "downloads"]].head(5).to_string(index=False))
```

```python
# /files/all returns every file in one response — convenient for small projects
files = requests.get(f"{PRIDE}/projects/PXD000001/files/all", timeout=60).json()
print(f"PXD000001 files (all): {len(files)}")
for f in files[:4]:
    print(f"  [{f.get('fileCategory',{}).get('value','?'):<6}] {f['fileName']}  "
          f"{f.get('fileSizeBytes',0)/1e6:.2f} MB")
```

### Module 5: SDRF File — `/files/sdrf/{projectAccession}`

PRIDE projects that follow the modern submission standard include an SDRF (Sample-Data Relationship Format) TSV that maps each MS run to its biological sample, treatment, label, fraction, etc. Pull it once, parse it as a TSV.

```python
import requests, pandas as pd, io

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def get_sdrf(accession):
    """Fetch the SDRF sample-to-run mapping for a project (404 if not provided)."""
    r = requests.get(f"{PRIDE}/files/sdrf/{accession}", timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), sep="\t")

# Many older projects have no SDRF — newer ones typically do
sdrf = get_sdrf("PXD000001")
if sdrf is None or sdrf.empty:
    print("No SDRF available for this project")
else:
    print(f"SDRF rows: {len(sdrf)}  cols: {len(sdrf.columns)}")
    print(f"First columns: {list(sdrf.columns)[:8]}")
```

### Module 6: Protein → Project Mapping — `/proteins/{accession}`

PRIDE v3's protein endpoint returns *only* the list of project accessions that contain identifications for the given UniProt accession. It does **not** return PSM counts, peptide counts, or sequence coverage — those are not exposed at the API surface in v3. For depth metrics you must download a project's `RESULT` files and parse them locally.

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def get_protein_projects(uniprot_acc):
    """Return the list of PRIDE project accessions that mention this UniProt accession.
    No PSM/peptide/coverage counts are available at this endpoint."""
    r = requests.get(f"{PRIDE}/proteins/{uniprot_acc}", timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    data = r.json()
    return data.get("projects", [])

tp53 = get_protein_projects("P04637")
print(f"TP53 (P04637) is reported in {len(tp53)} PRIDE projects")
print(f"First 8: {tp53[:8]}")

unknown = get_protein_projects("Q99999")
print(f"\nQ99999 (no real protein): "
      f"{'no PRIDE evidence' if not unknown else f'{len(unknown)} projects'}")
```

### Module 7: Discovery Helpers — Similar Projects, Autocomplete

`/projects/{accession}/similarProjects` returns projects with related metadata signatures (organism, instrument, experiment type, tags). `/search/autocomplete?keyword=...` returns project titles starting with the prefix — useful to suggest searches.

```python
import requests, pandas as pd

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

# Find similar projects to one of interest
similar = requests.get(f"{PRIDE}/projects/PXD004131/similarProjects",
                       params={"pageSize": 5}, timeout=30).json()
print(f"Similar to PXD004131: {len(similar)} projects")
for p in similar[:5]:
    print(f"  {p['accession']}  {(p.get('title') or '')[:70]}")

# Autocomplete suggestions for a project-title prefix
suggestions = requests.get(f"{PRIDE}/search/autocomplete",
                           params={"keyword": "tp53"}, timeout=30).json()
print(f"\nAutocomplete for 'tp53': {len(suggestions)} suggestions")
for s in suggestions[:5]:
    print(f"  {s}")
```

### Module 8: Repository-Wide Counts — `/projects/count`, `/files/count`

Get total counts across the repository — useful for status displays and sanity checks. Both endpoints return a plain integer body (no JSON object wrapper).

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

n_projects = int(requests.get(f"{PRIDE}/projects/count", timeout=30).text)
n_files    = int(requests.get(f"{PRIDE}/files/count", timeout=30).text)
print(f"PRIDE Archive current scale:")
print(f"  Projects: {n_projects:,}")
print(f"  Files:    {n_files:,}")
```

## Key Concepts

### Plain JSON Arrays, No HAL Envelope

PRIDE v3 list endpoints return plain JSON arrays — for example `/search/projects` returns `[{...}, {...}, ...]` directly. There is no `_embedded.compactprojects`, no `page.totalElements`/`totalPages`, no `_links.next.href`. Older PRIDE v2 clients that parsed `data["_embedded"]["compactprojects"]` will silently return empty against the current API. To paginate, walk `page=0, 1, 2, ...` until you get an empty array (or a partial page shorter than `pageSize`).

### What v3 Removed

The endpoint families below no longer exist in v3 (and v2 is now an alias for v3 internally — error messages from `/v2/peptides` literally report `path: "/pride/ws/archive/v3/peptides"`):

| Removed endpoint | Status in v3 | Replacement |
|---|---|---|
| `GET /peptides?projectAccessions=X` | 404 | None — download project's RESULT files and parse |
| `GET /psms?projectAccessions=X` | 404 | None — download RESULT files |
| `GET /proteins?proteinAccession=X` (query-param style) | 404 | `GET /proteins/{accession}` (path-param) |
| HAL+JSON `_embedded`/`page` wrapper | Gone | Plain JSON array |
| `/projects?keyword=...&organisms=...&tissues=...` filters | Silently ignored | `/search/projects?keyword=...&filter=field==value` |

### Filter Syntax on `/search/projects`

The `filter` query parameter takes a comma-separated list of `field==value` constraints. Field names use the `_facet` suffix (the underlying Solr-style field). Discover valid field names and values via `/facet/projects` before constructing the filter:

```python
# Valid filter forms
"organisms_facet==Homo sapiens (human)"
"instruments_facet==Q Exactive"
"diseases_facet==Prostate adenocarcinoma"
"softwares_facet==MaxQuant"

# Combine with commas
filter="organisms_facet==Homo sapiens (human),instruments_facet==Orbitrap Fusion Lumos"
```

### File Categories

Each file in a project carries a `fileCategory` CV-param. The `.value` is a category code; the `.name` is the human-readable label:

| `value` code | Description | Common formats |
|---|---|---|
| `RAW` | Unprocessed instrument output | .raw (Thermo), .d (Bruker/Agilent), .wiff (Sciex) |
| `PEAK` | Centroided / deconvoluted spectra | .mzML, .mzXML, .mgf |
| `RESULT` | Identification results | .mzid, .mzTab, MaxQuant txt, PRIDE XML |
| `FASTA` | Protein sequence database used in search | .fasta |
| `OTHER` | Supplementary / scripts / tables | .txt, .xlsx, .csv |

For reanalysis pipelines, `RESULT` is the cheapest entry point — pre-identified peptides without re-searching spectra. `PEAK` lets you re-search with a different engine. `RAW` is only needed for full vendor-format reprocessing.

### Accession Formats

PRIDE project accessions follow ProteomeXchange format `PXD######`. These are stable across PRIDE, MassIVE, jPOST, and iProX. File accessions inside PRIDE are SHA-256-style hashes (e.g., `5bda360133398f66021c8889e01dce921cb51300c7269e1f2b0f20368ab20af6`) — opaque identifiers; use `fileName` for human-readable filenames.

## Common Workflows

### Workflow 1: Faceted Discovery — From Disease Keyword to Filtered Project List

**Goal**: Start from a disease keyword, see which instruments and softwares are common in matching datasets via facet counts, then pull a filtered project list using one of the top values.

```python
import requests, pandas as pd

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"
disease_kw = "colorectal cancer"

# 1) Inspect facet counts to learn which filter values dominate
facets = requests.get(f"{PRIDE}/facet/projects",
                      params={"keyword": disease_kw, "facetPageSize": 10},
                      timeout=30).json()

top_instr = sorted(facets.get("instruments", {}).items(), key=lambda kv: -kv[1])[:5]
top_org = sorted(facets.get("organisms", {}).items(), key=lambda kv: -kv[1])[:3]
print(f"Top instruments for '{disease_kw}':")
for k, v in top_instr: print(f"  {k:<35} {v}")
print(f"Top organisms:")
for k, v in top_org: print(f"  {k:<35} {v}")

# 2) Build a filtered search using one top instrument
target_instr = top_instr[0][0]
projects = requests.get(f"{PRIDE}/search/projects",
                        params={"keyword": disease_kw,
                                "filter": f"organisms_facet==Homo sapiens (human),instruments_facet=={target_instr}",
                                "pageSize": 50,
                                "sortFields": "submission_date",
                                "sortDirection": "DESC"},
                        timeout=30).json()

df = pd.DataFrame([{
    "accession": p["accession"],
    "title": (p.get("title") or "")[:70],
    "submission_date": p.get("submissionDate"),
    "tissues": ", ".join(p.get("organismsPart", []))[:40],
    "submitter": (p.get("submitters") or [""])[0] if p.get("submitters") else "",
} for p in projects])
print(f"\nFiltered projects: {len(df)}  (target instrument: {target_instr})")
print(df.head(10).to_string(index=False))
df.to_csv(f"{disease_kw.replace(' ', '_')}_{target_instr.replace(' ', '_')}_projects.csv",
          index=False)
```

### Workflow 2: File Download Manifest for One Project

**Goal**: Pull the file list for a project, filter to the categories you actually want (`RAW` + `RESULT`), and emit an `aria2c`-ready URL list for parallel FTP download.

```python
import requests, pandas as pd
from pathlib import Path

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"
accession = "PXD004131"
keep_categories = {"RAW", "RESULT"}
output_dir = Path(f"/data/pride/{accession}")

files = requests.get(f"{PRIDE}/projects/{accession}/files/all", timeout=120).json()

manifest = []
for f in files:
    cat = (f.get("fileCategory") or {}).get("value")
    if cat not in keep_categories:
        continue
    ftp = next((loc["value"] for loc in f.get("publicFileLocations", [])
                if loc.get("name") == "FTP Protocol"), None)
    if not ftp:
        continue
    manifest.append({
        "file_name": f["fileName"],
        "category": cat,
        "size_mb": round((f.get("fileSizeBytes") or 0) / 1e6, 2),
        "ftp": ftp,
    })

mdf = pd.DataFrame(manifest).sort_values(["category", "file_name"])
print(f"{accession}: keeping {len(mdf)}/{len(files)} files "
      f"({mdf['size_mb'].sum():.0f} MB total)")
print(mdf.groupby("category")[["size_mb"]].sum().round(0))

# aria2c -i pride_dl.list -d /data/pride/PXD004131 -x 8 -j 4
with open("pride_dl.list", "w") as fh:
    fh.write("\n".join(mdf["ftp"]))
print(f"\nWrote pride_dl.list with {len(mdf)} URLs (use aria2c -i)")
```

### Workflow 3: Protein Cross-Project Occurrence

**Goal**: For a candidate protein panel (e.g., from a differential-expression analysis), look up how many PRIDE projects mention each one and shortlist the most-evidenced proteins. Note: this is a project-count signal only — there are no PSM/peptide counts at the API surface in v3, so a high project count is breadth, not depth.

```python
import requests, time, pandas as pd, matplotlib.pyplot as plt

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

candidates = {
    "P04637": "TP53", "P38398": "BRCA1", "P31749": "AKT1",
    "P40763": "STAT3", "O15530": "PDPK1", "P10275": "AR",
}

rows = []
for acc, sym in candidates.items():
    r = requests.get(f"{PRIDE}/proteins/{acc}", timeout=30)
    projs = r.json().get("projects", []) if r.status_code == 200 else []
    rows.append({"uniprot": acc, "symbol": sym, "n_projects": len(projs)})
    time.sleep(0.3)

df = pd.DataFrame(rows).sort_values("n_projects", ascending=False)
print(df.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 3.5))
bars = ax.bar(df["symbol"], df["n_projects"], color="#3182BD")
ax.bar_label(bars, fmt="%d", fontsize=9, padding=2)
ax.set_ylabel("# PRIDE projects mentioning the protein")
ax.set_title("PRIDE project-level occurrence — candidate panel")
plt.tight_layout()
plt.savefig("pride_protein_occurrence.png", dpi=150, bbox_inches="tight")
print("Saved pride_protein_occurrence.png")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|---|---|---|---|---|
| `keyword` | `/search/projects`, `/facet/projects`, `/search/autocomplete` | — | free-text string | Full-text search across title, description, tags |
| `filter` | `/search/projects` | — | `field_facet==value, field_facet==value` | Server-side filter using facet field names |
| `pageSize` | `/search/projects`, `/projects`, `/projects/{acc}/files`, `/projects/{acc}/similarProjects` | 100 | positive integer | Results per page |
| `page` | same as above | 0 | 0-indexed integer | Page number (no metadata returned — walk pages until empty) |
| `sortFields` | `/search/projects` | `submission_date` | comma-separated field names | Sort key(s) |
| `sortDirection` | `/search/projects` | `DESC` | `ASC` or `DESC` | Sort order |
| `facetPageSize` | `/facet/projects` | 20 | positive integer | Values returned per facet group |
| `dateGap` | `/search/projects`, `/facet/projects` | — | e.g. `+1MONTH`, `+1YEAR` | Date-range aggregation granularity |
| (path) `accession` | `/projects/{acc}`, `/projects/{acc}/files`, `/projects/{acc}/similarProjects`, `/proteins/{acc}` | required | PXD######  or UniProt acc | Identifies the resource |

## Best Practices

1. **Use `/search/projects` for searching, not `/projects`.** Plain `/projects` is a paginated listing endpoint and silently ignores keyword / organism / disease filters. Filtering only works through `/search/projects` with the `filter=field_facet==value` syntax.

2. **Discover filter values via `/facet/projects` before filtering.** Facet field values must match exactly (e.g., `organisms_facet==Homo sapiens (human)`, parentheses and all). The facet endpoint tells you which values exist and how many projects each has — saves a lot of trial-and-error.

3. **Don't try to query peptide- or PSM-level data over the API.** Those endpoints were removed in v3. Download the project's RESULT files and parse them locally with `pyteomics`, `pyOpenMS`, or a search-engine reader (MaxQuant, ProteomeDiscoverer, etc.).

4. **Prefer FTP URLs for bulk file downloads.** Each file record carries both `FTP Protocol` and `Aspera Protocol` URLs. FTP is more universally supported; pair it with `aria2c -x 8 -j 4` for parallel chunks. Use Aspera only if you have an Aspera client and need >100 Mbit transfer speeds.

5. **Watch the field name `fileSizeBytes`.** The current v3 field is `fileSizeBytes`, not `fileSize` (old v2 docs may say `fileSize`). Sizes are in bytes — divide by `1e6` for MB, `1e9` for GB.

6. **Filter file downloads by `fileCategory.value`.** A project can have hundreds of files spanning RAW (GB-scale) and OTHER (KB-scale). Always filter to the categories you actually need before queueing downloads — otherwise you'll easily download tens of gigabytes of vendor RAW files when you only wanted the identification tables.

7. **Pagination has no metadata — walk until empty.** Unlike old PRIDE v2, the v3 API doesn't return `totalElements`/`totalPages`. Iterate `page=0, 1, 2, ...` and stop when a page returns an empty array, or when its length is less than `pageSize`.

## Common Recipes

### Recipe: Quick Project File Summary

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def project_file_summary(accession):
    files = requests.get(f"{PRIDE}/projects/{accession}/files/all", timeout=60).json()
    by_cat = {}
    for f in files:
        cat = (f.get("fileCategory") or {}).get("value", "OTHER")
        by_cat.setdefault(cat, [0, 0])
        by_cat[cat][0] += 1
        by_cat[cat][1] += (f.get("fileSizeBytes") or 0) / 1e6
    print(f"\n{accession} file summary:")
    for cat, (n, mb) in sorted(by_cat.items()):
        print(f"  {cat:<8} {n:>4} file(s)   {mb:>10.1f} MB")
    total_mb = sum(mb for _, mb in by_cat.values())
    total_n  = sum(n  for n, _  in by_cat.values())
    print(f"  {'TOTAL':<8} {total_n:>4} file(s)   {total_mb:>10.1f} MB")

project_file_summary("PXD000001")
```

### Recipe: Check If a Protein Has Any PRIDE Evidence

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

def pride_evidence(uniprot_acc):
    """Return (has_evidence, n_projects). PRIDE v3 only exposes project list, no PSM counts."""
    r = requests.get(f"{PRIDE}/proteins/{uniprot_acc}", timeout=30)
    if r.status_code != 200:
        return False, 0
    projs = r.json().get("projects", [])
    return bool(projs), len(projs)

for acc in ["P04637", "Q99999"]:
    has, n = pride_evidence(acc)
    print(f"{acc}: evidence={has}  projects={n}")
```

### Recipe: Recent Submissions for a Keyword (sorted by date)

```python
import requests, pandas as pd

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

r = requests.get(f"{PRIDE}/search/projects",
                 params={"keyword": "single-cell proteomics",
                         "sortFields": "submission_date",
                         "sortDirection": "DESC",
                         "pageSize": 15},
                 timeout=30)
recent = r.json()
df = pd.DataFrame([{
    "submission_date": p.get("submissionDate"),
    "accession": p["accession"],
    "title": (p.get("title") or "")[:80],
} for p in recent]).sort_values("submission_date", ascending=False)
print(df.to_string(index=False))
```

### Recipe: Suggest-as-You-Type via Autocomplete

```python
import requests

PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v3"

for prefix in ["alzheimer", "single cell", "brca"]:
    s = requests.get(f"{PRIDE}/search/autocomplete",
                     params={"keyword": prefix}, timeout=30).json()
    print(f"\n'{prefix}' → {len(s)} suggestions:")
    for sug in s[:3]:
        print(f"  · {sug[:80]}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| Parsing returns empty list even when `r.json()` has data | Code is doing `data["_embedded"]["compactprojects"]` — old HAL+JSON wrapper that v3 no longer returns | Parse the response directly as a list: `projects = r.json()` |
| `HTTP 404` on `/peptides`, `/psms`, or `/proteins?proteinAccession=X` | These endpoints were removed in v3 | For peptide/PSM data, download the project's RESULT files and parse locally. For protein lookup, use `/proteins/{accession}` (path param) |
| `/projects?keyword=cancer` returns the same 100 results as `/projects` with no keyword | The `/projects` endpoint only accepts `pageSize` / `page` — keyword and other filters are silently ignored | Use `/search/projects?keyword=...&filter=...` instead |
| `/projects/{acc}/files` shows file size 0 | Reading `fileSize` instead of `fileSizeBytes` | The v3 field is `fileSizeBytes` (bytes); compute MB via `fileSizeBytes / 1e6` |
| Filter has no effect | Facet value doesn't exactly match a real value | Call `/facet/projects?keyword=...` first to enumerate valid values (`Homo sapiens (human)`, not `Homo sapiens`) |
| `pageSize` beyond the actual result set returns an empty array | Normal pagination behavior | Stop iterating when the returned array length is < `pageSize`, or when it is empty |
| `findAllOrganismsCount` returns HTTP 406 Not Acceptable | The endpoint requires a non-JSON Accept header | Skip this endpoint — facet counts via `/facet/projects` cover the same need |
| `HTTP 429` or `ConnectionError` on bursts | Shared EBI infrastructure | Add `time.sleep(0.3)` in loops; retry on 5xx with exponential backoff |

## Related Skills

- `uniprot-protein-database` — UniProt sequences, Swiss-Prot annotations, ID mapping; pair with PRIDE protein lookups to enrich each UniProt accession with sequence and functional information
- `interpro-database` — Protein domain architecture (Pfam, SMART, PANTHER) for proteins reported in PRIDE
- `pdb-database` — Resolved 3D structures for proteins with PRIDE evidence
- `pyteomics` (off-skill Python library) — Parse mzIdentML / mzML / mzTab files downloaded from `/projects/{accession}/files`; the path for spectrum- and PSM-level analysis now that the REST API no longer exposes those

## References

- [PRIDE Archive v3 REST API root](https://www.ebi.ac.uk/pride/ws/archive/v3/) — base URL
- [PRIDE v3 OpenAPI/Swagger spec](https://www.ebi.ac.uk/pride/ws/archive/v3/v3/api-docs) — authoritative endpoint inventory
- [PRIDE Archive web portal](https://www.ebi.ac.uk/pride/) — interactive dataset browser
- [Perez-Riverol et al., *Nucleic Acids Research* 2022](https://doi.org/10.1093/nar/gkab1038) — PRIDE 2022 update describing repository and architecture
- [ProteomeXchange Consortium](http://www.proteomexchange.org/) — standard accession system shared across PRIDE, MassIVE, jPOST, iProX
- [SDRF-Proteomics specification](https://github.com/bigbio/proteomics-sample-metadata) — format used by `/files/sdrf/{projectAccession}`
