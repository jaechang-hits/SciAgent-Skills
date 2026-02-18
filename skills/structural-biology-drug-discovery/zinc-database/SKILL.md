---
name: "zinc-database"
description: "Query ZINC15/ZINC22 virtual compound libraries for drug discovery. Search purchasable lead-like, fragment-like, and drug-like compounds by molecular weight, logP, reactivity class, or SMILES similarity. Download 3D compound sets for docking, retrieve SMILES for in-silico screening. ZINC20 contains 1.4B compounds; purchasable subset is 750M. For bioactivity data use chembl-database-bioactivity; for approved drugs use drugbank-database-access."
license: "CC-BY-4.0"
---

# ZINC Chemical Library Database

## Overview

ZINC (ZINC Is Not Commercial) is a free database of commercially available compounds curated for virtual screening. ZINC22 contains over 1.4 billion compounds (ZINC20: 1.4B, including purchasable 3D conformers), organized by molecular property filters (lead-like, fragment-like, drug-like) and reactivity class. The REST API enables SMILES-based searches, property-filtered downloads, and compound subset exports for docking campaigns.

## When to Use

- Downloading a purchasable, drug-like or lead-like compound library for virtual screening or docking campaigns
- Filtering compounds by Lipinski/lead-like properties (MW, logP, HBD, HBA) to build focused screening sets
- Searching ZINC for commercially available analogs of a query molecule via SMILES similarity
- Retrieving purchasable fragments (MW < 300, logP < 3) for fragment-based drug discovery
- Building compound diversity libraries for high-throughput screening (HTS) campaigns
- For known drug bioactivity data use `chembl-database-bioactivity`; for approved drug structures use `drugbank-database-access`; for RDKit property calculation use `rdkit-cheminformatics`

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **Data requirements**: SMILES strings, MW/logP ranges, or ZINC subset IDs
- **Environment**: internet connection; no API key needed for ZINC15; large downloads may take minutes
- **Rate limits**: reasonable use; avoid crawling all 1.4B records in automated loops

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

# Search ZINC15 REST API for drug-like compounds
BASE = "https://zinc15.docking.org"

r = requests.get(f"{BASE}/substances.json",
                 params={"mwt__gte": 250, "mwt__lte": 350,
                         "logp__gte": 0, "logp__lte": 3,
                         "availability": "for-sale", "count": 5})
r.raise_for_status()
compounds = r.json()
print(f"Returned {len(compounds)} compounds")
for c in compounds[:3]:
    print(f"  ZINC: {c['zinc_id']:20s} MW: {c['mwt']:.1f}  logP: {c['logp']:.2f}  SMILES: {c['smiles'][:40]}")
```

## Core API

### Query 1: Property-Filtered Compound Search

Search ZINC15 by molecular property ranges (Lipinski, lead-like, fragment-like criteria).

```python
import requests, pandas as pd

BASE = "https://zinc15.docking.org"

def zinc_search(params, max_results=500):
    """Search ZINC15 with property filters. Returns DataFrame."""
    all_results = []
    params = dict(params)
    params["count"] = min(100, max_results)

    r = requests.get(f"{BASE}/substances.json", params=params)
    r.raise_for_status()
    compounds = r.json()
    all_results.extend(compounds)
    return pd.DataFrame(all_results)

# Lead-like set: MW 250-350, logP 1-3, HBD ≤ 3
df_leads = zinc_search({
    "mwt__gte": 250, "mwt__lte": 350,
    "logp__gte": 1, "logp__lte": 3,
    "hbd__lte": 3, "hba__lte": 7,
    "availability": "for-sale",
})
print(f"Lead-like compounds: {len(df_leads)}")
print(df_leads[["zinc_id", "mwt", "logp", "smiles"]].head())
```

```python
# Fragment-like set: MW < 300, logP < 3 (Rule of Three)
df_frags = zinc_search({
    "mwt__lte": 300,
    "logp__lte": 3,
    "hbd__lte": 3,
    "availability": "for-sale",
})
print(f"\nFragment-like compounds: {len(df_frags)}")
print(df_frags[["zinc_id", "mwt", "logp", "smiles"]].head())
```

### Query 2: Retrieve Compound by ZINC ID

Fetch full compound data for a known ZINC identifier.

```python
import requests

BASE = "https://zinc15.docking.org"

zinc_id = "ZINC000000029632"

r = requests.get(f"{BASE}/substances/{zinc_id}.json")
r.raise_for_status()
c = r.json()

print(f"ZINC ID  : {c['zinc_id']}")
print(f"SMILES   : {c['smiles']}")
print(f"MW       : {c['mwt']:.2f}")
print(f"logP     : {c['logp']:.2f}")
print(f"HBD      : {c['hbd']}")
print(f"HBA      : {c['hba']}")
print(f"TPSA     : {c.get('tpsa', 'n/a')}")
print(f"Rotatable: {c.get('rotatable_bonds', 'n/a')}")
print(f"Suppliers: {len(c.get('suppliers', []))}")
```

### Query 3: Download Compound Subsets (Tranches)

ZINC organizes compounds into "tranches" by MW and logP. Download pre-built SDF/SMILES files.

```python
import requests

# ZINC15 tranche download (MW 200-250, logP 1-2 range)
# Tranche naming: letters encode MW range (A-K) and logP range (A-J)
# See http://zinc15.docking.org/tranches/home

def download_zinc_tranche(tranche_name, dest_file, fmt="smi"):
    """Download a ZINC tranche SMILES file."""
    url = f"https://zinc15.docking.org/tranches/{tranche_name}.{fmt}"
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(dest_file, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded {dest_file}")

# Download one tranche as SMILES
download_zinc_tranche("AABA", "zinc_AABA.smi", fmt="smi")
```

### Query 4: SMILES Similarity Search

Find ZINC compounds similar to a query molecule.

```python
import requests, pandas as pd

BASE = "https://zinc15.docking.org"

query_smiles = "c1ccc(NC(=O)c2ccccc2)cc1"  # benzanilide analog

r = requests.get(f"{BASE}/substances.json",
                 params={
                     "smiles": query_smiles,
                     "similarity": 0.6,       # Tanimoto similarity threshold
                     "count": 20,
                     "availability": "for-sale"
                 })
r.raise_for_status()
results = r.json()
print(f"Similar compounds found: {len(results)}")
df = pd.DataFrame(results)[["zinc_id", "smiles", "mwt", "logp"]]
print(df.head())
```

### Query 5: Catalog and Supplier Information

Retrieve purchasability and supplier catalog data for compounds.

```python
import requests

BASE = "https://zinc15.docking.org"

# Check purchasability and catalog info
zinc_id = "ZINC000000029632"
r = requests.get(f"{BASE}/substances/{zinc_id}/suppliers.json")
r.raise_for_status()
suppliers = r.json()

print(f"Suppliers for {zinc_id}: {len(suppliers)}")
for sup in suppliers[:5]:
    print(f"  {sup.get('name', 'n/a'):30s} | Catalog: {sup.get('catalognum', 'n/a')}")
```

### Query 6: Bulk Download via ZINC Slices

For large-scale virtual screening, download entire ZINC subsets as compressed SMILES.

```python
import requests, gzip, io, pandas as pd

# ZINC15 drug-like purchasable slice (public URL pattern)
# Full drug-like: https://zinc15.docking.org/substances/subsets/drug-like.smi.gz

def download_zinc_subset(subset_name, max_lines=1000):
    """Download a ZINC subset SMILES file and return a DataFrame sample."""
    url = f"https://zinc15.docking.org/substances/subsets/{subset_name}.smi.gz"
    r = requests.get(url, stream=True)
    r.raise_for_status()

    lines = []
    with gzip.open(r.raw, "rt") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line.strip().split())

    df = pd.DataFrame(lines, columns=["smiles", "zinc_id"] + [f"col{i}" for i in range(max(0, len(lines[0])-2))])
    return df[["smiles", "zinc_id"]]

# Load first 1000 from lead-like subset
df_sample = download_zinc_subset("lead-like", max_lines=1000)
print(f"Loaded {len(df_sample)} compounds from lead-like subset")
print(df_sample.head())
```

## Key Concepts

### ZINC Tranches

Compounds are organized into a 2D grid of "tranches" based on MW (rows A–K: <200 to >600 Da) and logP (columns A–J: <-1 to >5). Each tranche can be downloaded as a SMILES or SDF file. This tranching enables targeted downloads of specific property spaces for docking.

### Availability Classes

- **for-sale**: Purchasable from ≥1 supplier
- **in-stock**: Available for immediate purchase
- **wait-ok**: Longer lead time acceptable
- **on-demand**: Custom synthesis required

## Common Workflows

### Workflow 1: Build a Focused Docking Library

**Goal**: Curate a purchasable, lead-like compound library within specific property ranges, deduplicate, and export for docking.

```python
import requests, pandas as pd

BASE = "https://zinc15.docking.org"

# Fetch lead-like purchasable compounds with Lipinski compliance
params = {
    "mwt__gte": 200, "mwt__lte": 500,
    "logp__gte": -1, "logp__lte": 5,
    "hbd__lte": 5, "hba__lte": 10,
    "rotatable_bonds__lte": 10,
    "availability": "for-sale",
    "count": 200,
}
r = requests.get(f"{BASE}/substances.json", params=params)
r.raise_for_status()
compounds = r.json()

df = pd.DataFrame(compounds)[["zinc_id", "smiles", "mwt", "logp", "hbd", "hba"]]
df = df.drop_duplicates(subset=["smiles"])
print(f"Curated library: {len(df)} unique compounds")

# Export as SMILES for docking input
df[["smiles", "zinc_id"]].to_csv("docking_library.smi", sep=" ", index=False, header=False)
print("Saved: docking_library.smi")
print(df.head())
```

### Workflow 2: Fragment Library for FBDD

**Goal**: Download fragment-like (Rule of Three) compounds for fragment-based drug discovery.

```python
import requests, pandas as pd

BASE = "https://zinc15.docking.org"

# Rule of Three: MW ≤ 300, logP ≤ 3, HBD ≤ 3, HBA ≤ 3, RotB ≤ 3
params = {
    "mwt__lte": 300,
    "logp__lte": 3,
    "hbd__lte": 3,
    "hba__lte": 3,
    "rotatable_bonds__lte": 3,
    "availability": "for-sale",
    "count": 200,
}
r = requests.get(f"{BASE}/substances.json", params=params)
fragments = r.json()
df = pd.DataFrame(fragments)[["zinc_id", "smiles", "mwt", "logp"]]

print(f"Fragment library: {len(df)} compounds (Rule of Three)")
df.to_csv("fragment_library.smi", sep=" ", index=False, header=False)
print("Saved: fragment_library.smi")
df.describe()
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `mwt__gte` / `mwt__lte` | Search | — | numeric (Da) | Molecular weight lower/upper bound |
| `logp__gte` / `logp__lte` | Search | — | numeric | logP (lipophilicity) range |
| `hbd__lte` | Search | — | integer | Max hydrogen bond donors |
| `hba__lte` | Search | — | integer | Max hydrogen bond acceptors |
| `rotatable_bonds__lte` | Search | — | integer | Max rotatable bonds |
| `availability` | Search | all | `"for-sale"`, `"in-stock"`, `"on-demand"` | Purchasability filter |
| `count` | Search | 10 | `1`–`1000` | Max compounds returned per request |
| `similarity` | Similarity | — | `0.0`–`1.0` | Tanimoto similarity threshold |

## Best Practices

1. **Use tranches for large docking campaigns**: Downloading entire MW/logP tranches as pre-built SDF files is faster than paginating the API. Use the ZINC tranches page to identify the subset of property space you need.

2. **Apply reactivity filters**: ZINC marks reactive compounds with "reactivity" flags. Exclude compounds with reactive groups (`reactivity: "clean"` filter) for cell-based assays.

3. **Deduplicate by SMILES**: API results may contain duplicates across supplier catalog entries. Canonical SMILES deduplication with RDKit (`Chem.MolToSmiles(Chem.MolFromSmiles(smi))`) before docking.

4. **Combine with RDKit filtering**: After downloading, apply additional filters (PAINS, Brenk alerts) using `rdkit-cheminformatics` or `medchem` before investing compute in docking.

5. **Cache SMILES downloads**: ZINC data is updated periodically. Cache downloads with a date-stamped filename and avoid re-downloading within a project.

## Common Recipes

### Recipe: Lookup ZINC ID from SMILES

When to use: Find the ZINC ID for a known compound to check purchasability.

```python
import requests

BASE = "https://zinc15.docking.org"
smiles = "CC(=O)Nc1ccc(O)cc1"  # paracetamol / acetaminophen

r = requests.get(f"{BASE}/substances.json",
                 params={"smiles": smiles, "count": 3})
for c in r.json():
    print(f"ZINC: {c['zinc_id']} | MW: {c['mwt']:.1f} | In stock: {c.get('availability')}")
```

### Recipe: Export SDF for Docking

When to use: Download 3D SDF conformers for a list of ZINC IDs for use in docking software.

```python
import requests

BASE = "https://zinc15.docking.org"
zinc_ids = ["ZINC000000029632", "ZINC000001532592"]

for zid in zinc_ids:
    r = requests.get(f"{BASE}/substances/{zid}.sdf")
    if r.ok:
        with open(f"{zid}.sdf", "w") as f:
            f.write(r.text)
        print(f"Downloaded {zid}.sdf")
    else:
        print(f"Not available: {zid}")
```

### Recipe: Property Distribution of a Library

When to use: Quickly assess the property coverage of a downloaded compound set.

```python
import pandas as pd

df = pd.read_csv("docking_library.smi", sep=" ", names=["smiles", "zinc_id"])
print(f"Library size: {len(df)}")

# If you have the full ZINC metadata:
# df = pd.DataFrame(compounds)[["mwt", "logp", "hbd", "hba"]]
# print(df.describe())
# import matplotlib.pyplot as plt
# df[["mwt", "logp"]].hist(bins=30, figsize=(10, 4)); plt.show()
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 404` for compound ID | ZINC ID format incorrect | Use full 12-digit ZINC ID (e.g., `ZINC000000029632`) |
| Empty results for property search | Filters too restrictive | Relax ranges; check `mwt__gte < mwt__lte` is not inverted |
| Similarity search returns nothing | SMILES invalid or unusual scaffold | Validate SMILES with RDKit first; try lower similarity threshold |
| Tranche file download fails | Tranche code wrong | Verify tranche naming at zinc15.docking.org/tranches/home |
| API returns HTML error page | Server maintenance | Retry after a few minutes; check ZINC status |
| Slow large downloads | Large compound sets | Download tranche files via FTP/HTTP bulk download instead of API pagination |

## Related Skills

- `rdkit-cheminformatics` — Compute additional properties and apply PAINS filters on downloaded ZINC compounds
- `autodock-vina-docking` — Use downloaded ZINC SMILES/SDF files for molecular docking campaigns
- `chembl-database-bioactivity` — Bioactivity data for compounds identified in ZINC virtual screens
- `medchem` — Apply medicinal chemistry filters (Lipinski, PAINS, NIBR) on ZINC libraries

## References

- [ZINC15 website](https://zinc15.docking.org/) — Main ZINC15 database and API
- [ZINC15 REST API reference](https://zinc15.docking.org/api/) — Query parameters and endpoint documentation
- [ZINC22 update paper](https://doi.org/10.1021/acs.jcim.2c00852) — Irwin et al., J. Chem. Inf. Model. 2022
- [ZINC tranches download page](https://zinc15.docking.org/tranches/home) — Bulk compound subset downloads by MW/logP
