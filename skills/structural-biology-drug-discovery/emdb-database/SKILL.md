---
name: "emdb-database"
description: "Search EMDB cryo-EM density maps, fitted atomic models, and metadata via REST API. Query by keyword, resolution, method, or organism; fetch entries, map URLs, linked PDB models, and publications. No auth. For atomic coordinates use pdb-database; for AlphaFold predictions use alphafold-database-access."
license: "CC-BY-4.0"
---

# EMDB Database

## Overview

The Electron Microscopy Data Bank (EMDB) at EBI archives 3D electron microscopy density maps — primarily cryo-EM and cryo-ET maps — for macromolecular assemblies. It holds 30,000+ entries including ribosomes, membrane proteins, viruses, and large complexes not tractable by X-ray crystallography. The EMDB REST API at `https://www.ebi.ac.uk/emdb/api/` provides JSON responses for entry metadata, map download info, fitted atomic models (PDB IDs), and publications. No authentication or API key is required.

## When to Use

- Finding cryo-EM density maps for a protein or complex by keyword (e.g., "spike protein", "ribosome 70S")
- Fetching the download URL for a `.map.gz` density file to use in local structure visualization (UCSF ChimeraX, PyMOL)
- Identifying which PDB atomic models have been fitted into an EMDB map (and vice versa)
- Retrieving EMDB entry metadata — resolution, reconstruction method, fitted model count, and organism — for a literature search or database survey
- Searching for cryo-EM structures of a specific organism or filtered by resolution cutoff (e.g., < 3 Å)
- Linking EMDB maps to their primary publications for citation retrieval
- Use `pdb-database` instead when you need experimentally determined atomic coordinates (X-ray, NMR, or cryo-EM deposited with coordinates); EMDB provides the raw density map, PDB provides the atom positions
- For AlphaFold AI-predicted structures use `alphafold-database-access`; EMDB is for experimental EM maps only

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: EMDB entry IDs (format: `EMD-XXXX`), keyword search strings, or PDB IDs for cross-referencing
- **Environment**: internet connection; no API key required
- **Rate limits**: no official published limits; add `time.sleep(0.2)` between requests in batch loops for polite access

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

# Search for cryo-EM maps of the SARS-CoV-2 spike protein
response = requests.get(f"{EMDB_API}/search/", params={"q": "spike protein SARS-CoV-2"}, timeout=30)
response.raise_for_status()
results = response.json()

hits = results.get("results", [])
print(f"Total hits: {results.get('numFound', 0)}")
for entry in hits[:5]:
    emdb_id = entry.get("emdbId", "")
    title   = entry.get("title", "")
    resol   = entry.get("resolution", "?")
    print(f"  {emdb_id}: {title[:60]}  ({resol} Å)")
# EMD-30210: SARS-CoV-2 spike protein in the prefusion conf...  (3.46 Å)
# EMD-22221: SARS-CoV-2 spike protein glycoprotein structure...  (2.8 Å)
```

## Core API

### Query 1: Full-Text Search

Search EMDB entries by keyword. Returns a paginated result list with basic metadata for each hit.

```python
import requests
import pandas as pd

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def emdb_search(query: str, rows: int = 20, start: int = 0) -> dict:
    """Full-text search of EMDB entries. Returns JSON response."""
    params = {"q": query, "rows": rows, "start": start}
    r = requests.get(f"{EMDB_API}/search/", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

data = emdb_search("ribosome 70S bacterial", rows=10)
print(f"Total entries found: {data.get('numFound', 0)}")

rows = []
for entry in data.get("results", []):
    rows.append({
        "emdb_id":    entry.get("emdbId"),
        "title":      entry.get("title", "")[:80],
        "resolution": entry.get("resolution"),
        "method":     entry.get("imageAcquisition", {}).get("imagingMethod", ""),
        "organism":   entry.get("organism", ""),
    })

df = pd.DataFrame(rows)
print(df.to_string(index=False))
```

```python
# Search with resolution filter using pandas post-filtering
data = emdb_search("membrane protein", rows=50)
rows = []
for entry in data.get("results", []):
    resol = entry.get("resolution")
    if resol is not None and resol <= 3.0:
        rows.append({
            "emdb_id":    entry.get("emdbId"),
            "title":      entry.get("title", "")[:70],
            "resolution": resol,
        })

df_highres = pd.DataFrame(rows).sort_values("resolution") if rows else pd.DataFrame()
print(f"High-resolution membrane protein maps (≤3.0 Å): {len(df_highres)}")
if not df_highres.empty:
    print(df_highres.head(5).to_string(index=False))
```

### Query 2: Entry Details

Retrieve full metadata for a single EMDB entry by its ID (e.g., `EMD-1234`).

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def get_entry(emdb_id: str) -> dict:
    """Fetch full metadata for a single EMDB entry. emdb_id e.g. 'EMD-1234'."""
    r = requests.get(f"{EMDB_API}/entry/{emdb_id}", timeout=30)
    r.raise_for_status()
    return r.json()

entry = get_entry("EMD-30210")   # SARS-CoV-2 spike

# Navigate the nested JSON
header = entry.get("map", {}).get("header", {})
title  = header.get("title", "")
deposited = header.get("depositionDate", "")

print(f"Entry: EMD-30210")
print(f"Title: {title}")
print(f"Deposited: {deposited}")

# Resolution
resol_block = entry.get("processing", {}).get("reconstruction", {}).get("resolutionByAuthor", "")
print(f"Resolution: {resol_block}")

# Sample organism
sample = entry.get("sample", {})
name_block = sample.get("name", "")
print(f"Sample: {name_block}")
```

### Query 3: Map Download Information

Retrieve the download URL and file format for the associated `.map.gz` density file.

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def get_map_info(emdb_id: str) -> dict:
    """Retrieve map file download metadata for an EMDB entry."""
    r = requests.get(f"{EMDB_API}/entry/{emdb_id}/map", timeout=30)
    r.raise_for_status()
    return r.json()

map_info = get_map_info("EMD-30210")
print("Map download info:")
for item in map_info if isinstance(map_info, list) else [map_info]:
    file_url  = item.get("url", "")
    file_size = item.get("size", "")
    format_   = item.get("format", "")
    print(f"  URL:    {file_url}")
    print(f"  Format: {format_}  |  Size: {file_size}")

# Construct standard download URL manually (always available)
num = "30210"  # numeric part of EMD-30210
standard_url = f"https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-{num}/map/emd_{num}.map.gz"
print(f"\nFTP map URL: {standard_url}")
```

### Query 4: Fitted Atomic Models (PDB Cross-Reference)

List the PDB IDs of atomic models that have been fitted into this EM map.

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def get_fitted_models(emdb_id: str) -> list:
    """Return list of PDB IDs fitted to the EMDB map."""
    r = requests.get(f"{EMDB_API}/entry/{emdb_id}/fitted", timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    return data.get("fittedModels", [])

models = get_fitted_models("EMD-30210")
print(f"Fitted PDB models for EMD-30210: {len(models)}")
for m in models:
    pdb_id = m.get("pdbId") if isinstance(m, dict) else m
    print(f"  PDB: {pdb_id}")
```

```python
# Reverse lookup: given a PDB ID, find associated EMDB entries via search
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def find_emdb_for_pdb(pdb_id: str) -> list:
    """Search EMDB for entries associated with a PDB ID."""
    r = requests.get(f"{EMDB_API}/search/", params={"q": pdb_id, "rows": 10}, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", [])
    return [e.get("emdbId") for e in results if e.get("emdbId")]

pdb_id = "7BNM"   # SARS-CoV-2 spike structure
associated = find_emdb_for_pdb(pdb_id)
print(f"EMDB entries associated with PDB {pdb_id}: {associated}")
```

### Query 5: Publications

Retrieve primary publications (citations) linked to an EMDB entry.

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def get_publications(emdb_id: str) -> list:
    """Retrieve publications associated with an EMDB entry."""
    r = requests.get(f"{EMDB_API}/entry/{emdb_id}/publications", timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    return data.get("publications", [])

pubs = get_publications("EMD-30210")
print(f"Publications for EMD-30210: {len(pubs)}")
for pub in pubs:
    title  = pub.get("title", "")
    doi    = pub.get("doi", "")
    year   = pub.get("year", "")
    print(f"  [{year}] {title[:70]}")
    if doi:
        print(f"         DOI: {doi}")
```

### Query 6: Overall Statistics

Retrieve aggregate EMDB database statistics — total entry count, resolution distribution, method breakdown.

```python
import requests

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def get_statistics() -> dict:
    """Retrieve overall EMDB database statistics."""
    r = requests.get(f"{EMDB_API}/statistics/", timeout=30)
    r.raise_for_status()
    return r.json()

stats = get_statistics()
print("EMDB Database Statistics:")
total = stats.get("totalEntries", stats.get("total", "n/a"))
print(f"  Total entries: {total}")

# Method breakdown if available
methods = stats.get("methods", stats.get("imagingMethods", {}))
if methods:
    print("  By method:")
    for method, count in sorted(methods.items(), key=lambda x: -x[1] if isinstance(x[1], int) else 0):
        print(f"    {method}: {count}")
```

### Query 7: Visualization — Resolution Distribution

Plot the resolution distribution of a set of EMDB search results.

```python
import requests
import matplotlib.pyplot as plt

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

# Fetch 200 entries for visualization
r = requests.get(f"{EMDB_API}/search/", params={"q": "cryo-EM", "rows": 200}, timeout=60)
r.raise_for_status()
results = r.json().get("results", [])

resolutions = [
    entry["resolution"] for entry in results
    if entry.get("resolution") is not None and 1.0 <= entry["resolution"] <= 10.0
]

fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(resolutions, bins=30, color="#2c7fb8", edgecolor="white", alpha=0.85)
ax.axvline(x=3.0, color="#d62728", lw=1.5, ls="--", label="3 Å threshold")
ax.set_xlabel("Resolution (Å)")
ax.set_ylabel("Number of entries")
ax.set_title(f"EMDB Resolution Distribution (n={len(resolutions)})")
ax.legend()
plt.tight_layout()
plt.savefig("emdb_resolution_distribution.png", dpi=150, bbox_inches="tight")
print(f"Saved emdb_resolution_distribution.png  ({len(resolutions)} entries)")
below3 = sum(1 for r in resolutions if r <= 3.0)
print(f"Entries at ≤3.0 Å: {below3}/{len(resolutions)} ({below3/len(resolutions)*100:.1f}%)")
```

## Key Concepts

### EMDB ID Format

EMDB IDs follow the pattern `EMD-XXXX` (e.g., `EMD-1234`, `EMD-30210`). The numeric part is used in FTP paths. The API accepts both `EMD-1234` and `1234` in most endpoints. FTP download paths use zero-padded 4-digit numbers for older entries.

### Map vs. Atomic Model

An EMDB entry holds the raw **electron density map** (`.map` or `.map.gz`, in MRC/CCP4 format) — a 3D voxel grid of electron scattering density. The fitted **atomic model** (PDB entry) is a separate record with ATOM/HETATM coordinates interpreted from the map. Many maps have multiple fitted models from different groups; some maps have none (primary data without model deposition).

### Resolution and Quality

| Resolution | Typical interpretability |
|------------|--------------------------|
| < 2.5 Å   | Near-atomic: side-chain positions visible |
| 2.5–3.5 Å | High-res: backbone well-resolved, some side chains |
| 3.5–5.0 Å | Medium: secondary structure clear, limited side-chain detail |
| > 5.0 Å   | Low-res: domain arrangement only |

Use the `resolution` field from search results to filter for structures appropriate for your analysis task.

## Common Workflows

### Workflow 1: Survey All High-Resolution Entries for a Target

**Goal**: Find all EMDB maps for a protein target with resolution ≤ 3.5 Å, export to CSV with PDB model cross-references.

```python
import requests
import time
import pandas as pd

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def emdb_search_all(query: str, rows_per_page: int = 50) -> list:
    """Paginate through all search results."""
    all_results = []
    start = 0
    while True:
        r = requests.get(f"{EMDB_API}/search/",
                         params={"q": query, "rows": rows_per_page, "start": start},
                         timeout=30)
        r.raise_for_status()
        data = r.json()
        batch = data.get("results", [])
        all_results.extend(batch)
        if start + rows_per_page >= data.get("numFound", 0) or not batch:
            break
        start += rows_per_page
        time.sleep(0.2)
    return all_results

target = "ACE2"
print(f"Searching EMDB for: {target}")
entries = emdb_search_all(target)
print(f"Total entries: {len(entries)}")

rows = []
for entry in entries:
    resol = entry.get("resolution")
    if resol is None or resol > 3.5:
        continue
    emdb_id = entry.get("emdbId", "")
    # Fetch fitted PDB models
    try:
        r2 = requests.get(f"{EMDB_API}/entry/{emdb_id}/fitted", timeout=15)
        models = r2.json() if r2.status_code == 200 else []
        pdb_ids = [m.get("pdbId") if isinstance(m, dict) else str(m) for m in (models if isinstance(models, list) else [])]
    except Exception:
        pdb_ids = []
    time.sleep(0.2)
    rows.append({
        "emdb_id":    emdb_id,
        "title":      entry.get("title", "")[:80],
        "resolution": resol,
        "pdb_models": ";".join(pdb_ids) if pdb_ids else "",
        "organism":   entry.get("organism", ""),
    })

df = pd.DataFrame(rows).sort_values("resolution")
df.to_csv(f"{target}_emdb_highres.csv", index=False)
print(f"High-res entries (≤3.5 Å): {len(df)}")
print(df[["emdb_id", "resolution", "pdb_models", "title"]].head(8).to_string(index=False))
```

### Workflow 2: Batch Metadata Collection from Entry ID List

**Goal**: Given a list of EMDB IDs from a literature search, fetch structured metadata and build a summary table.

```python
import requests
import time
import pandas as pd

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

emdb_ids = ["EMD-30210", "EMD-22221", "EMD-23970", "EMD-13731", "EMD-14127"]

records = []
for emdb_id in emdb_ids:
    try:
        r = requests.get(f"{EMDB_API}/entry/{emdb_id}", timeout=20)
        r.raise_for_status()
        entry = r.json()

        header     = entry.get("map", {}).get("header", {})
        processing = entry.get("processing", {})
        recon      = processing.get("reconstruction", {})

        records.append({
            "emdb_id":    emdb_id,
            "title":      header.get("title", "")[:80],
            "deposited":  header.get("depositionDate", ""),
            "resolution": recon.get("resolutionByAuthor", ""),
            "software":   recon.get("software", {}).get("name", "") if isinstance(recon.get("software"), dict) else "",
        })
    except Exception as e:
        print(f"Warning: {emdb_id} failed — {e}")
    time.sleep(0.2)

df = pd.DataFrame(records)
print(df.to_string(index=False))
df.to_csv("emdb_batch_metadata.csv", index=False)
print(f"\nSaved emdb_batch_metadata.csv ({len(df)} entries)")
```

### Workflow 3: Download a Density Map File

**Goal**: Download an EMDB `.map.gz` file programmatically for use in ChimeraX or PyMOL.

```python
import requests
from pathlib import Path

def download_emdb_map(emdb_id: str, output_dir: str = ".") -> str:
    """
    Download an EMDB map file (.map.gz) via FTP.
    Returns the path to the downloaded file.
    """
    num = emdb_id.replace("EMD-", "").replace("emd-", "").lstrip("0") or "0"
    num_padded = num.zfill(4) if len(num) < 4 else num
    url = (f"https://ftp.ebi.ac.uk/pub/databases/emdb/structures/"
           f"EMD-{num_padded}/map/emd_{num_padded}.map.gz")
    out_path = Path(output_dir) / f"emd_{num_padded}.map.gz"

    print(f"Downloading {emdb_id} map from EBI FTP...")
    print(f"  URL: {url}")
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()

    total_mb = int(r.headers.get("content-length", 0)) / 1e6
    downloaded = 0
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)

    print(f"  Saved: {out_path}  ({downloaded/1e6:.1f} MB)")
    return str(out_path)

# Example: download spike protein map
path = download_emdb_map("EMD-30210", output_dir="/tmp")
print(f"Map file: {path}")
print("Open in ChimeraX with: open /tmp/emd_30210.map.gz")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `q` | `/search/` | — | Any keyword string | Full-text search query; supports boolean and phrase matching |
| `rows` | `/search/` | `10` | `1`–`200` | Number of results per page |
| `start` | `/search/` | `0` | `0`–`numFound` | Pagination offset for large result sets |
| `emdb_id` | `/entry/{id}` | — | `EMD-XXXX` format | Specific entry identifier |
| `resolution` | Result field | — | float (Å) | Filter post-query by `entry["resolution"]` threshold |
| `imagingMethod` | Result field | — | `"cryo EM"`, `"cryo ET"` | Method filter; applies via pandas post-fetch |
| `organism` | Result field | — | organism name string | Organism filter; match with `.str.contains()` |

## Best Practices

1. **Use the FTP endpoint for large map files**: The REST API provides metadata; the actual `.map.gz` files are served via the EBI FTP. Construct the FTP URL as `https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-XXXX/map/emd_XXXX.map.gz`.
   ```python
   num = "30210"
   url = f"https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-{num}/map/emd_{num}.map.gz"
   ```

2. **Add `time.sleep(0.2)` in batch loops**: The EMDB REST API is shared infrastructure with no published rate limits. Polite delays prevent throttling.

3. **Filter by resolution post-query**: The `/search/` endpoint does not support server-side numeric range filtering. Fetch a larger `rows` value and filter the `resolution` field with pandas locally.

4. **Cross-reference via both directions**: An EMDB entry can have 0–10+ fitted PDB models. Always check `/entry/{emdb_id}/fitted` for the definitive PDB list; keyword search alone may miss older depositions.

5. **Check for `None` resolution**: Some cryo-ET and subtomogram averages lack a numeric resolution estimate. Guard with `if entry.get("resolution") is not None` before numeric comparisons.

## Common Recipes

### Recipe: Get All PDB Models Fitted to a Map

When to use: You have an EMDB ID and want to load all associated atomic coordinates.

```python
import requests

def get_pdb_ids_for_emdb(emdb_id: str) -> list:
    """Return list of PDB IDs fitted into the given EMDB map."""
    r = requests.get(f"https://www.ebi.ac.uk/emdb/api/entry/{emdb_id}/fitted", timeout=15)
    if r.status_code != 200:
        return []
    data = r.json()
    models = data if isinstance(data, list) else data.get("fittedModels", [])
    return [m.get("pdbId") if isinstance(m, dict) else str(m) for m in models]

pdb_ids = get_pdb_ids_for_emdb("EMD-30210")
print(f"PDB models for EMD-30210: {pdb_ids}")
# PDB models for EMD-30210: ['7BNM', '7BNN']
```

### Recipe: Batch Resolution Summary for a Gene List

When to use: Survey EMDB coverage and resolution for a list of protein targets.

```python
import requests
import time
import pandas as pd

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

targets = ["KRAS", "EGFR", "ACE2", "p53", "mTOR"]
rows = []
for target in targets:
    r = requests.get(f"{EMDB_API}/search/",
                     params={"q": target, "rows": 100}, timeout=30)
    r.raise_for_status()
    entries = r.json().get("results", [])
    resolutions = [e["resolution"] for e in entries if e.get("resolution") is not None]
    rows.append({
        "target":     target,
        "n_entries":  len(entries),
        "best_resol": min(resolutions) if resolutions else None,
        "mean_resol": round(sum(resolutions)/len(resolutions), 2) if resolutions else None,
    })
    time.sleep(0.3)

df = pd.DataFrame(rows)
print(df.to_string(index=False))
#   target  n_entries  best_resol  mean_resol
#     KRAS         12        2.19        3.84
#     EGFR         31        2.60        4.12
#     ACE2         45        2.05        3.27
```

### Recipe: Find All Entries Below a Resolution Cutoff

When to use: Build a benchmark set of high-resolution cryo-EM structures for a specific system.

```python
import requests
import pandas as pd

EMDB_API = "https://www.ebi.ac.uk/emdb/api"

def find_highres_entries(query: str, resolution_cutoff: float = 3.0, max_results: int = 200) -> pd.DataFrame:
    r = requests.get(f"{EMDB_API}/search/",
                     params={"q": query, "rows": max_results}, timeout=60)
    r.raise_for_status()
    entries = r.json().get("results", [])
    rows = []
    for e in entries:
        resol = e.get("resolution")
        if resol is not None and resol <= resolution_cutoff:
            rows.append({
                "emdb_id":    e.get("emdbId"),
                "resolution": resol,
                "title":      e.get("title", "")[:70],
                "organism":   e.get("organism", ""),
            })
    return pd.DataFrame(rows).sort_values("resolution") if rows else pd.DataFrame()

df = find_highres_entries("ion channel", resolution_cutoff=3.0)
print(f"Ion channel maps at ≤3.0 Å: {len(df)}")
print(df.head(5).to_string(index=False))
df.to_csv("ion_channel_highres_emdb.csv", index=False)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTPError: 404` for `/entry/{emdb_id}` | Entry ID not found or wrong format | Verify format is `EMD-XXXX` with correct numeric suffix; confirm entry exists on https://www.ebi.ac.uk/emdb/ |
| Empty `results` list | Query too specific or misspelled | Broaden the search term; try the gene name alone without qualifiers |
| `resolution` field is `None` | Cryo-ET or subtomogram averaging entries without reported resolution | Skip with `if entry.get("resolution") is not None`; these are valid entries |
| FTP download returns `404` | Wrong numeric padding in FTP path | Use the raw number without leading zeros for EMD-XXXX where XXXX is < 4 digits; verify the path at https://ftp.ebi.ac.uk/pub/databases/emdb/structures/ |
| Fitted models list is empty | Map has no associated deposited PDB model | Some authors deposit maps without atomic models; cross-reference by keyword search with the EMDB title |
| Slow search for common terms | Large result sets | Limit `rows` to a manageable number (50–200) and filter post-fetch; avoid open-ended queries like `q=protein` |
| `ConnectionError` / `Timeout` | Network issue or server overload | Retry with exponential backoff; increase `timeout` to 60s for large requests |

## Related Skills

- `pdb-database` — RCSB PDB REST API for experimental atomic coordinates; complement to EMDB maps
- `alphafold-database-access` — AlphaFold predicted structures (200M+ proteins), no EM map
- `pubmed-database` — Retrieve publications by DOI or PMID retrieved from EMDB publications endpoint
- `mdanalysis-trajectory` — Analyze MD trajectories of structures initially determined by cryo-EM

## References

- [EMDB website](https://www.ebi.ac.uk/emdb/) — Browse entries, access documentation, and download maps via web interface
- [EMDB REST API documentation](https://www.ebi.ac.uk/emdb/api/) — Endpoint reference and JSON schema for all API routes
- [Lawson et al., Nucleic Acids Res. 2016](https://doi.org/10.1093/nar/gkv1054) — EMDB database description and content overview
- [EMDB FTP archive](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/) — Direct download of `.map.gz` density files and XML metadata
