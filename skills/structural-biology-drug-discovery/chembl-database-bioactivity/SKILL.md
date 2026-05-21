---
name: chembl-database-bioactivity
description: Query ChEMBL (2M+ compounds, 19M+ bioactivity measurements, 13K+ targets) via the public REST/JSON API with plain `requests` — no SDK install required. Search compounds, retrieve IC50/Ki/EC50 bioactivities, find target inhibitors, run SAR, access drug mechanism/indication data.
license: CC-BY-SA-3.0
---

# ChEMBL Database — Bioactivity Queries

> **Why no SDK?** The `chembl_webresource_client` package is convenient sugar over a public, no-auth REST/JSON API at `https://www.ebi.ac.uk/chembl/api/data/`. When the SDK is unavailable, every operation can be reproduced with plain `requests` and URL parameters. This SKILL.md uses the REST path throughout so the code runs in any environment with `requests` installed. Django-style filter syntax (`field__icontains=…`, `field__lte=…`, `field__range=a,b`) works as URL query parameters.

## Overview

ChEMBL is EMBL-EBI's bioactive molecule database: 2M+ compounds, 19M+ bioactivity measurements (IC50, Ki, EC50, Kd, …), 13K+ targets. The REST API at `https://www.ebi.ac.uk/chembl/api/data/` returns JSON (append `.json`) or XML/YAML, requires no authentication, and supports Django-style query filters via URL parameters plus cursor-style pagination via `page_meta.next`.

## When to Use

- Finding compounds by name, ChEMBL ID, or physicochemical properties
- Querying bioactivity data (IC50, Ki, EC50) for specific targets
- Performing similarity or substructure searches using SMILES
- Retrieving drug mechanisms of action and clinical indications
- Identifying inhibitors, agonists, or bioactive molecules for a target
- Analyzing structure-activity relationships (SAR) across compound series
- Filtering molecules by Lipinski rule-of-5 or other drug-likeness criteria
- For general cheminformatics (SMILES manipulation, fingerprints, descriptors) use `rdkit-cheminformatics` instead
- For an alternative compound database (NIH, broader coverage) use `pubchem-compound-search`

## Prerequisites

- **Python packages**: `requests` (only requirement). Optional: `pandas` for tabular analysis.
- **No API key required**: ChEMBL is freely accessible.
- **Rate limits**: No published hard limit. The infrastructure is shared — add `time.sleep(0.2-0.5)` between requests in batch loops; back off on HTTP 429.

```bash
pip install requests
# Optional, for DataFrame work:
pip install pandas
```

## Quick Start

```python
import requests

BASE = "https://www.ebi.ac.uk/chembl/api/data"

# Retrieve a molecule by ChEMBL ID
r = requests.get(f"{BASE}/molecule/CHEMBL25.json", timeout=15)
r.raise_for_status()
aspirin = r.json()
print(f"{aspirin['pref_name']}: MW={aspirin['molecule_properties']['mw_freebase']}")
# ASPIRIN: MW=180.16

# Search targets by full name (acronyms like 'EGFR' don't match pref_name — use full term)
r = requests.get(
    f"{BASE}/target.json",
    params={"pref_name__icontains": "epidermal growth factor receptor",
            "target_type": "SINGLE PROTEIN", "limit": 5},
    timeout=15,
)
targets = r.json()["targets"]
print(f"EGFR-like targets: {len(targets)}, first={targets[0]['target_chembl_id']}")

# Potent bioactivities: EGFR (CHEMBL203) IC50 <= 100 nM
r = requests.get(
    f"{BASE}/activity.json",
    params={"target_chembl_id": "CHEMBL203",
            "standard_type": "IC50",
            "standard_value__lte": 100,
            "standard_units": "nM",
            "limit": 5},
    timeout=30,
)
data = r.json()
print(f"EGFR IC50 ≤ 100 nM records: {data['page_meta']['total_count']}")
```

## Key Concepts

### Filter Operators (Django-style, as URL parameters)

The SDK's `field__operator=value` syntax maps 1:1 to URL query parameters. Use `&` to combine filters.

| Operator | URL pattern | Example URL fragment |
|----------|-------------|----------------------|
| `__exact` | `field=value` | `target_type=SINGLE+PROTEIN` |
| `__iexact` | `field__iexact=value` | `pref_name__iexact=aspirin` |
| `__contains` / `__icontains` | `field__icontains=value` | `pref_name__icontains=kinase` |
| `__startswith` / `__endswith` | `field__startswith=Epi` | `pref_name__endswith=nib` |
| `__gt` / `__gte` / `__lt` / `__lte` | `field__lte=100` | `standard_value__lte=100` |
| `__range` | `field__range=lo,hi` | `molecule_properties__mw_freebase__range=300,500` |
| `__in` | `field__in=a,b,c` | `standard_type__in=IC50,Ki,Kd` |
| `__isnull` | `field__isnull=False` (Python `False`/`True` strings) | `pchembl_value__isnull=False` |
| `__regex` | `field__regex=…` | `pref_name__regex=^EGF.*kinase$` |
| `__search` | `field__search=…` | `description__search=apoptosis` |

When passed via `requests.get(..., params={...})`, the library handles URL encoding automatically (including the commas in `__range` and `__in`).

### Core Endpoints

All endpoints accept `.json`, `.xml`, or `.yaml` suffix. JSON is the default below.

| Endpoint URL | Returns | Key fields |
|--------------|---------|------------|
| `/molecule/{chembl_id}.json` | Compound by ID | `pref_name`, `molecule_chembl_id`, `molecule_properties`, `molecule_structures` |
| `/molecule.json?<filters>` | Compound search | paginated `molecules[]` |
| `/target/{chembl_id}.json` | Target by ID | `pref_name`, `target_type`, `organism`, `target_components` |
| `/target.json?<filters>` | Target search | paginated `targets[]` |
| `/activity.json?<filters>` | Bioactivity records | paginated `activities[]` |
| `/assay.json?<filters>` | Assay details | paginated `assays[]` |
| `/drug.json?<filters>` | Approved drug info | paginated `drugs[]`; supports `/drug/{chembl_id}.json` |
| `/mechanism.json?<filters>` | Mechanism of action | paginated `mechanisms[]` |
| `/drug_indication.json?<filters>` | Therapeutic indications | paginated `drug_indications[]` |
| `/similarity/{smiles}/{tanimoto}.json` | Tanimoto similarity (0–100) | paginated `molecules[]` with `similarity` field |
| `/substructure/{smiles}.json` | Substructure search | paginated `molecules[]` |
| `/image/{chembl_id}.svg` | SVG structure image | binary SVG (NOT JSON) |
| `/molecule_form/{chembl_id}.json` | Parent/salt forms | `molecule_forms[]` |
| `/protein_class.json` | Protein classification hierarchy | hierarchical browse |
| `/document.json?<filters>` | Literature source records | paginated `documents[]` |

### Response Shape

```jsonc
{
  "page_meta": {
    "limit": 20,
    "offset": 0,
    "total_count": 12145,
    "next": "/chembl/api/data/activity.json?...&offset=20",
    "previous": null
  },
  "activities": [ /* or molecules[], targets[], etc. */ ]
}
```

Walk `page_meta.next` (a relative URL — prefix with `https://www.ebi.ac.uk`) until it becomes `null`.

### Molecular Properties

Properties accessible via `molecule_properties` on each record:

| Field | Description |
|-------|-------------|
| `mw_freebase` | Molecular weight (free base) |
| `full_mwt` | Full molecular weight (including salts) |
| `alogp` | Calculated LogP |
| `hba` | Hydrogen bond acceptors |
| `hbd` | Hydrogen bond donors |
| `psa` | Polar surface area |
| `rtb` | Rotatable bonds |
| `num_ro5_violations` | Lipinski rule-of-5 violations |
| `ro3_pass` | Rule of 3 compliance |
| `cx_most_apka` / `cx_most_bpka` | Most acidic / basic pKa |

### Target Information Fields

| Field | Description |
|-------|-------------|
| `target_chembl_id` | ChEMBL target identifier |
| `pref_name` | Preferred (full) target name — acronyms like "EGFR" do NOT match; use the spelled-out term |
| `target_type` | `SINGLE PROTEIN`, `PROTEIN COMPLEX`, `ORGANISM`, … |
| `organism` | Target organism (e.g., `Homo sapiens`) |
| `tax_id` | NCBI taxonomy ID |
| `target_components[]` | Components (UniProt accession, sequence, …) |

### Bioactivity Data Fields

| Field | Description |
|-------|-------------|
| `standard_type` | Activity type: `IC50`, `Ki`, `Kd`, `EC50`, … |
| `standard_value` | Numerical activity value |
| `standard_units` | Units: `nM`, `uM`, … |
| `pchembl_value` | Normalized -log10 activity (>6 = potent) |
| `activity_comment` | Activity annotations |
| `data_validity_comment` | Data quality flags (check before analysis) |
| `potential_duplicate` | Duplicate flag |

## Core API

### 1. Molecule Queries

```python
import requests
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# By ChEMBL ID
r = requests.get(f"{BASE}/molecule/CHEMBL25.json", timeout=15)
aspirin = r.json()
print(f"{aspirin['pref_name']}: MW={aspirin['molecule_properties']['mw_freebase']}")

# By name (case-insensitive substring)
r = requests.get(f"{BASE}/molecule.json",
                 params={"pref_name__icontains": "imatinib", "limit": 5},
                 timeout=15)
for mol in r.json()["molecules"]:
    print(f"  {mol['molecule_chembl_id']}  {mol.get('pref_name')!r}")

# By Lipinski-compliant property ranges
r = requests.get(f"{BASE}/molecule.json",
                 params={"molecule_properties__mw_freebase__range": "300,500",
                         "molecule_properties__alogp__lte": 5,
                         "molecule_properties__hba__lte": 10,
                         "molecule_properties__hbd__lte": 5,
                         "limit": 3},
                 timeout=15)
print(f"Lipinski-compliant total: {r.json()['page_meta']['total_count']}")
```

### 2. Target Queries

```python
import requests
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# By ChEMBL ID
r = requests.get(f"{BASE}/target/CHEMBL203.json", timeout=15)
egfr = r.json()
print(f"{egfr['pref_name']} ({egfr['organism']}) — type={egfr['target_type']}")

# Search by full name (NOT acronym) + type
r = requests.get(f"{BASE}/target.json",
                 params={"pref_name__icontains": "kinase",
                         "target_type": "SINGLE PROTEIN", "limit": 5},
                 timeout=15)
d = r.json()
print(f"Kinase SINGLE_PROTEIN targets: total={d['page_meta']['total_count']}")
for t in d["targets"][:5]:
    print(f"  {t['target_chembl_id']:12s} {t.get('pref_name')!r}  ({t['organism']})")

# By organism
r = requests.get(f"{BASE}/target.json",
                 params={"organism": "Homo sapiens", "limit": 3},
                 timeout=15)
print(f"Human targets: total={r.json()['page_meta']['total_count']}")
```

### 3. Bioactivity Data

```python
import requests
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# Potent inhibitors for a target (EGFR = CHEMBL203)
r = requests.get(f"{BASE}/activity.json",
                 params={"target_chembl_id": "CHEMBL203",
                         "standard_type": "IC50",
                         "standard_value__lte": 100,
                         "standard_units": "nM",
                         "limit": 5},
                 timeout=30)
data = r.json()
print(f"EGFR IC50≤100nM: total={data['page_meta']['total_count']}")
for act in data["activities"][:5]:
    print(f"  {act['molecule_chembl_id']:14s} IC50={act['standard_value']} nM "
          f"pChEMBL={act.get('pchembl_value')}")

# All pChEMBL-tagged activities for a compound
r = requests.get(f"{BASE}/activity.json",
                 params={"molecule_chembl_id": "CHEMBL25",
                         "pchembl_value__isnull": "False",
                         "limit": 5},
                 timeout=30)
print(f"Aspirin pChEMBL activities: total={r.json()['page_meta']['total_count']}")

# Multiple activity types (CHEMBL240 = D2 dopamine receptor)
r = requests.get(f"{BASE}/activity.json",
                 params={"target_chembl_id": "CHEMBL240",
                         "standard_type__in": "IC50,Ki,Kd",
                         "limit": 5},
                 timeout=30)
print(f"D2 receptor IC50/Ki/Kd: total={r.json()['page_meta']['total_count']}")
```

### 4. Structure-Based Search

```python
import requests
from urllib.parse import quote
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# Similarity search (Tanimoto ≥ 85%)
# Path-style endpoint: /similarity/{smiles}/{threshold}
# The SMILES MUST be URL-encoded (it contains '/', '(', ')' etc.)
aspirin_smiles = quote("CC(=O)Oc1ccccc1C(=O)O", safe="")
r = requests.get(f"{BASE}/similarity/{aspirin_smiles}/85.json",
                 params={"limit": 5}, timeout=30)
data = r.json()
print(f"Similar to aspirin (≥85% Tanimoto): total={data['page_meta']['total_count']}")
for m in data["molecules"][:5]:
    print(f"  {m['molecule_chembl_id']}  similarity={m.get('similarity')}")
```

```python
# Substructure search
benzimidazole = quote("c1ccc2[nH]cnc2c1", safe="")
r = requests.get(f"{BASE}/substructure/{benzimidazole}.json",
                 params={"limit": 3}, timeout=30)
print(f"Benzimidazole substructure total: {r.json()['page_meta']['total_count']}")
```

### 5. Drug and Mechanism Data

```python
import requests
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# Drug record (max clinical phase, ATC class, etc.)
r = requests.get(f"{BASE}/drug/CHEMBL941.json", timeout=15)   # imatinib
drug = r.json()
print(f"Imatinib max_phase={drug.get('max_phase')}")

# Mechanisms of action — note: not every drug has mechanism records.
# Imatinib (CHEMBL941) returns 0 mechanism rows; sunitinib (CHEMBL535) has many.
r = requests.get(f"{BASE}/mechanism.json",
                 params={"molecule_chembl_id": "CHEMBL535"}, timeout=15)
for m in r.json()["mechanisms"]:
    print(f"  {m['mechanism_of_action']} → target {m.get('target_chembl_id')}")

# Therapeutic indications
r = requests.get(f"{BASE}/drug_indication.json",
                 params={"molecule_chembl_id": "CHEMBL941", "limit": 5},
                 timeout=15)
for ind in r.json()["drug_indications"]:
    print(f"  {ind.get('mesh_heading')!r}  max_phase_for_ind={ind.get('max_phase_for_ind')}")
```

```python
# SVG molecular structure image — direct binary response, NOT JSON
# Do NOT call /image/{cid}.json — that endpoint raises JSONDecodeError.
r = requests.get(f"{BASE}/image/CHEMBL25.svg", timeout=15)
r.raise_for_status()
with open("aspirin.svg", "w") as f:
    f.write(r.text)
print(f"Saved aspirin.svg ({len(r.text)} bytes, looks_svg={'<svg' in r.text})")
```

## Common Workflows

### Workflow 1: Find Inhibitors for a Target

**Note:** `pref_name__icontains` matches the spelled-out name. Acronyms like `'EGFR'` or `'BRAF'` return 0 results — use `'epidermal growth factor receptor'` or `'B-raf'` (with the hyphen).

```python
import requests, pandas as pd, time
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# Step 1: Resolve the target by full name
r = requests.get(f"{BASE}/target.json",
                 params={"pref_name__icontains": "B-raf",
                         "target_type": "SINGLE PROTEIN", "limit": 5},
                 timeout=15)
targets = r.json()["targets"]
human_braf = next(t for t in targets if t["organism"] == "Homo sapiens")
target_id = human_braf["target_chembl_id"]
print(f"Using {target_id} — {human_braf['pref_name']}")

# Step 2: Paginate all potent IC50 activities (cap at 500 for demo)
url = (f"{BASE}/activity.json"
       f"?target_chembl_id={target_id}"
       f"&standard_type=IC50"
       f"&standard_value__lte=100"
       f"&standard_units=nM"
       f"&pchembl_value__isnull=False"
       f"&limit=200")
records = []
while url and len(records) < 500:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    records.extend(data["activities"])
    nxt = data["page_meta"].get("next")
    url = f"https://www.ebi.ac.uk{nxt}" if nxt else None
    time.sleep(0.2)

df = pd.DataFrame(records)
df["standard_value"] = pd.to_numeric(df["standard_value"])
print(f"Retrieved {len(df)} potent {target_id} compounds")
print(df[["molecule_chembl_id", "standard_value", "pchembl_value"]].head(10))
```

### Workflow 2: Analyze a Known Drug

```python
import requests
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# Sunitinib (CHEMBL535) — has documented mechanisms + indications.
# Imatinib (CHEMBL941) sometimes returns 0 mechanism rows depending on ChEMBL release.
chembl_id = "CHEMBL535"

# Molecule record
m = requests.get(f"{BASE}/molecule/{chembl_id}.json", timeout=15).json()
print(f"Name: {m['pref_name']}")
print(f"MW  : {m['molecule_properties']['mw_freebase']}")

# Mechanisms
mechs = requests.get(f"{BASE}/mechanism.json",
                     params={"molecule_chembl_id": chembl_id},
                     timeout=15).json()["mechanisms"]
for mc in mechs:
    print(f"  Mechanism: {mc['mechanism_of_action']}")

# Indications
inds = requests.get(f"{BASE}/drug_indication.json",
                    params={"molecule_chembl_id": chembl_id, "limit": 5},
                    timeout=15).json()["drug_indications"]
for ind in inds:
    print(f"  Indication: {ind.get('mesh_heading')}  "
          f"(Phase {ind.get('max_phase_for_ind')})")

# Bioactivity record count
total = requests.get(f"{BASE}/activity.json",
                     params={"molecule_chembl_id": chembl_id,
                             "pchembl_value__isnull": "False",
                             "limit": 1},
                     timeout=30).json()["page_meta"]["total_count"]
print(f"Total bioactivity records (pChEMBL-tagged): {total}")
```

### Workflow 3: SAR Study

```python
import requests, pandas as pd, time
from urllib.parse import quote
BASE = "https://www.ebi.ac.uk/chembl/api/data"

# Step 1: Similar compounds to a lead (e.g., quinoline scaffold)
lead_smiles = "c1ccc2c(c1)cc(nc2N)c3ccc(cc3)NC(=O)c4ccccc4"
r = requests.get(f"{BASE}/similarity/{quote(lead_smiles, safe='')}/80.json",
                 params={"limit": 20}, timeout=30)
analogs = r.json()["molecules"]
print(f"Analogs found: {len(analogs)}")

# Step 2: Collect bioactivities for each analog
records = []
for compound in analogs[:20]:
    cid = compound["molecule_chembl_id"]
    acts = requests.get(f"{BASE}/activity.json",
                        params={"molecule_chembl_id": cid,
                                "standard_type": "IC50",
                                "pchembl_value__isnull": "False",
                                "limit": 20},
                        timeout=30).json()["activities"]
    for act in acts:
        records.append({
            "chembl_id": cid,
            "target": act.get("target_pref_name"),
            "IC50_nM": act.get("standard_value"),
            "pchembl": act.get("pchembl_value"),
            "mw":    (compound.get("molecule_properties") or {}).get("mw_freebase"),
            "alogp": (compound.get("molecule_properties") or {}).get("alogp"),
        })
    time.sleep(0.2)

df = pd.DataFrame(records)
if not df.empty:
    df["IC50_nM"] = pd.to_numeric(df["IC50_nM"])
    print(df.groupby("target")["IC50_nM"].describe())
```

## Common Recipes

### Recipe: Virtual Screening Filter (Lipinski rule-of-5)

```python
import requests
BASE = "https://www.ebi.ac.uk/chembl/api/data"
r = requests.get(f"{BASE}/molecule.json",
                 params={"molecule_properties__mw_freebase__range": "300,500",
                         "molecule_properties__alogp__lte": 5,
                         "molecule_properties__hba__lte": 10,
                         "molecule_properties__hbd__lte": 5,
                         "molecule_properties__num_ro5_violations": 0,
                         "limit": 1},
                 timeout=15)
print(f"Drug-like candidates: {r.json()['page_meta']['total_count']}")
```

### Recipe: Paginate Activities to CSV

```python
import requests, pandas as pd, time
BASE = "https://www.ebi.ac.uk/chembl/api/data"

url = (f"{BASE}/activity.json"
       f"?target_chembl_id=CHEMBL203"
       f"&standard_type=IC50"
       f"&pchembl_value__isnull=False"
       f"&limit=500")
all_acts = []
while url:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()
    all_acts.extend(data["activities"])
    nxt = data["page_meta"].get("next")
    url = f"https://www.ebi.ac.uk{nxt}" if nxt else None
    time.sleep(0.3)

df = pd.DataFrame(all_acts)
df.to_csv("egfr_activities.csv", index=False)
print(f"Exported {len(df)} records → egfr_activities.csv")
```

### Recipe: Robust Session with Retries

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def chembl_session(retries=3, backoff=1.0):
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=retries, backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"])))
    return s

session = chembl_session()
r = session.get("https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL25.json", timeout=15)
print(r.json()["pref_name"])
```

### Recipe: Download SVG Structure Image

```python
import requests
r = requests.get("https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL25.svg", timeout=15)
r.raise_for_status()
with open("aspirin.svg", "w") as f:
    f.write(r.text)
```

## Key Parameters

| Parameter | Endpoint | Default | Description |
|-----------|----------|---------|-------------|
| `limit` | all list endpoints | `20` | Page size; max 1000 |
| `offset` | all list endpoints | `0` | Pagination offset (or follow `page_meta.next`) |
| `format` | all endpoints | `json` (via `.json` suffix) | Also `.xml`, `.yaml` |
| `pref_name__icontains` | `/target`, `/molecule` | — | Substring on full name; **acronyms don't match**, use full term |
| `target_chembl_id` | `/activity` | — | E.g., `CHEMBL203` (EGFR), `CHEMBL240` (D2 receptor) |
| `molecule_chembl_id` | `/activity`, `/mechanism`, `/drug_indication` | — | E.g., `CHEMBL25` (aspirin) |
| `standard_type` | `/activity` | — | `IC50`, `Ki`, `Kd`, `EC50` |
| `standard_value__lte` | `/activity` | — | Max activity value (paired with `standard_units`) |
| `pchembl_value__isnull` | `/activity` | — | `"False"` to require pChEMBL-tagged data |
| `target_type` | `/target` | — | `SINGLE PROTEIN`, `PROTEIN COMPLEX`, `ORGANISM`, … |
| `{tanimoto}` (path) | `/similarity/{smiles}/{tanimoto}` | — | `0`–`100` Tanimoto threshold |
| `{smiles}` (path) | `/similarity`, `/substructure` | — | URL-encoded SMILES (`urllib.parse.quote(s, safe="")`) |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `pref_name__icontains=EGFR` (or `BRAF`) returns 0 | ChEMBL stores spelled-out names; acronyms don't match | Use `"epidermal growth factor receptor"`; for BRAF use `"B-raf"` with the hyphen |
| `mechanism.json?molecule_chembl_id=CHEMBL941` returns empty | Not every drug has mechanism rows in every release (e.g., imatinib has 0 in current data) | Use `CHEMBL535` (sunitinib) or `CHEMBL192` (sildenafil) as known-populated examples |
| `JSONDecodeError` on `/image/{cid}.json` | The image endpoint is binary, not JSON | Always use `.svg` or `.png` suffix: `/image/{cid}.svg` |
| 404 on `/molecule/{id}` | Invalid ChEMBL ID format | IDs must include the prefix: `CHEMBL25`, not `25` |
| 400 on similarity search | Unencoded SMILES (`/` collides with URL path) | URL-encode: `urllib.parse.quote(smiles, safe="")` |
| Empty `next` page but `total_count` higher | Reached internal limit (typically 10000 with `offset` pagination) | Narrow filters (date range, target class) and re-paginate; or use the ChEMBL FTP downloads for >100K records |
| `HTTP 429 Too Many Requests` | Burst pace | Add `time.sleep(0.3)`; mount a `Retry` adapter (see Recipe) |
| Mixed units in `activity` records | Different assays report in nM / µM / % inhibition | Filter `standard_units="nM"` and prefer `pchembl_value` for cross-assay comparison |
| `data_validity_comment` is non-empty | Curation flag (e.g., "Potential transcription error", "Outside typical range") | Drop these rows before SAR/regression analysis |
| Duplicate activity records | Same measurement reported in multiple sources | Check `potential_duplicate=True` and dedupe |

## Best Practices

- **Use `pchembl_value`** for cross-study comparisons — it normalizes IC50/Ki/EC50 to a comparable -log10 scale.
- **Always check `data_validity_comment`** before computing aggregates — flagged rows can skew distributions.
- **Pin `standard_units="nM"`** in activity queries to avoid mixing nM with µM.
- **Follow `page_meta.next` for pagination** instead of incrementing `offset` manually — the URL already carries the right cursor.
- **URL-encode SMILES** in path-style endpoints (`/similarity/{smiles}/...`, `/substructure/{smiles}`) with `urllib.parse.quote(smi, safe="")`.
- **Use a `Session` with retry adapter** for batch work (see Recipe) — ChEMBL handles a fair amount of traffic and occasionally returns 502/503.
- **For >100K records** prefer the [ChEMBL FTP downloads](https://chembl.gitbook.io/chembl-interface-documentation/downloads) over paginated API calls.
- **Be deliberate about acronyms in `pref_name__icontains`** — `EGFR`, `BRAF`, `HER2` all return 0 hits. Use the spelled-out term or filter via `target_components__accession=<UniProt>` instead.

## Related Skills

- `rdkit-cheminformatics` — SMILES manipulation, fingerprints, descriptors
- `datamol-cheminformatics` — molecular preprocessing & featurization
- `pubchem-compound-search` — alternative compound database (NIH; broader coverage but less bioactivity depth)
- `pdb-database` — 3D structures of ChEMBL targets via RCSB PDB REST API
- `opentargets-database` — links ChEMBL drug-target evidence to disease associations

## References

- ChEMBL website: https://www.ebi.ac.uk/chembl/
- REST API root: https://www.ebi.ac.uk/chembl/api/data/
- API docs: https://www.ebi.ac.uk/chembl/api/data/docs
- Interface docs (Django filter syntax): https://chembl.gitbook.io/chembl-interface-documentation/web-services
- Bulk downloads (for >100K records): https://chembl.gitbook.io/chembl-interface-documentation/downloads
- For SDK-based usage, see the `chembl_webresource_client` PyPI package; this SKILL.md uses the underlying REST API directly so no SDK install is needed.
