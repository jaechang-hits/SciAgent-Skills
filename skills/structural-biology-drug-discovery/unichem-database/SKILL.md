---
name: "unichem-database"
description: "Cross-reference chemical compound identifiers across 50+ databases (ChEMBL, DrugBank, PubChem, ChEBI, PDB, KEGG) using the UniChem REST API. Resolve InChIKeys to database-specific IDs, find all sources for a compound, discover related compounds by structural connectivity, and batch-translate compound lists between naming systems. No authentication required."
license: "Apache-2.0"
---

# UniChem Database

## Overview

UniChem is a chemical structure cross-referencing service from EMBL-EBI that links compound records across 50+ public chemistry databases using InChI-based identifiers. It maps a single chemical entity to its corresponding IDs in ChEMBL, DrugBank, PubChem, ChEBI, PDB, KEGG, and many others. Access is via a free REST API at `https://www.ebi.ac.uk/unichem/api/v1/` — no authentication required.

## When to Use

- Translating a ChEMBL compound ID to a PubChem CID, DrugBank accession, or ChEBI ID for cross-database analysis
- Resolving an InChIKey to all database sources where a compound appears
- Finding all structurally related compounds (same connectivity, different stereochemistry/salts) across databases using connectivity search
- Validating compound identity across sources before merging datasets from multiple databases
- Building a compound cross-reference table for a drug discovery project (linking bioactivity data in ChEMBL to structural data in PDB)
- Checking if a synthesized compound or a vendor compound exists in any public database by InChIKey
- For full bioactivity profiles (IC50, Ki) use `chembl-database-bioactivity`; UniChem provides only ID cross-references, not experimental data
- For compound property prediction or substructure searching use `pubchem-compound-search`; UniChem is for identifier translation only

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: compound InChIKeys (standard format: 27-character XXXXXXXXXXXXXX-XXXXXXXXXX-X), ChEMBL IDs, or PubChem CIDs as starting points
- **Environment**: internet connection; no API key required
- **Rate limits**: ~10 requests/second; add `time.sleep(0.1)` between requests in batch loops; no daily quota

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def unichem_get(endpoint: str, params: dict = None) -> dict:
    """GET request to UniChem API; raise on HTTP errors."""
    r = requests.get(f"{UNICHEM_API}/{endpoint}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()

# Find all database sources for aspirin by InChIKey
inchikey = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"  # aspirin
result = unichem_get(f"compounds", params={"compound": inchikey})
compounds = result.get("compounds", [])
print(f"Found {len(compounds)} compound record(s) for {inchikey}")
if compounds:
    sources = compounds[0].get("sources", [])
    print(f"  Present in {len(sources)} databases")
    for src in sources[:5]:
        print(f"  Source {src['sourceId']}: {src['compoundId']}")
# Found 1 compound record(s) for BSYNRYMUTXBXSQ-UHFFFAOYSA-N
#   Present in 32 databases
#   Source 1: CHEMBL25  (ChEMBL)
#   Source 2: DB00945   (DrugBank)
#   Source 22: 2244     (PubChem)
```

## Core API

### Query 1: InChIKey Lookup — All Sources

Search for a compound by its standard InChIKey and retrieve all database records. This is the primary cross-reference method.

```python
import requests, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

# Source ID reference (most commonly used)
SOURCE_NAMES = {
    1: "ChEMBL", 2: "DrugBank", 3: "PDB", 6: "KEGG",
    7: "ChEBI", 14: "FDA SRS", 22: "PubChem", 31: "BindingDB",
    41: "SureChEMBL", 45: "ZINC15",
}

def lookup_by_inchikey(inchikey: str) -> pd.DataFrame:
    """Return all database cross-references for an InChIKey."""
    r = requests.get(f"{UNICHEM_API}/compounds", params={"compound": inchikey}, timeout=15)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return pd.DataFrame()
    rows = []
    for src in compounds[0].get("sources", []):
        rows.append({
            "source_id": src["sourceId"],
            "source_name": SOURCE_NAMES.get(src["sourceId"], f"Source {src['sourceId']}"),
            "compound_id": src["compoundId"],
            "url": src.get("url", ""),
        })
    return pd.DataFrame(rows).sort_values("source_id")

# Ibuprofen cross-references
df = lookup_by_inchikey("HEFNNWSXXWATRW-UHFFFAOYSA-N")
print(f"Ibuprofen found in {len(df)} databases:")
print(df[["source_name", "compound_id"]].to_string(index=False))
```

```python
# Extract specific source IDs from cross-reference table
def get_id_for_source(inchikey: str, source_id: int) -> str | None:
    """Return the compound ID in a specific database, or None if not found."""
    r = requests.get(f"{UNICHEM_API}/compounds", params={"compound": inchikey}, timeout=15)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return None
    for src in compounds[0].get("sources", []):
        if src["sourceId"] == source_id:
            return src["compoundId"]
    return None

ibuprofen_inchikey = "HEFNNWSXXWATRW-UHFFFAOYSA-N"
chembl_id = get_id_for_source(ibuprofen_inchikey, source_id=1)   # ChEMBL
pubchem_id = get_id_for_source(ibuprofen_inchikey, source_id=22)  # PubChem
drugbank_id = get_id_for_source(ibuprofen_inchikey, source_id=2)  # DrugBank
print(f"Ibuprofen: ChEMBL={chembl_id}, PubChem={pubchem_id}, DrugBank={drugbank_id}")
# Ibuprofen: ChEMBL=CHEMBL521, PubChem=3672, DrugBank=DB01050
```

### Query 2: Compound Sources — by Compound ID

Given a known compound ID (e.g., ChEMBL ID), retrieve all cross-references for that compound. Returns the same data as InChIKey lookup but starting from a source-specific ID.

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def get_sources_for_compound(compound_id: str, source_id: int) -> list:
    """Get all database cross-references for a compound identified in a specific source.

    Args:
        compound_id: The ID in the source database (e.g., 'CHEMBL521')
        source_id: UniChem source ID (1=ChEMBL, 2=DrugBank, 22=PubChem, 7=ChEBI)
    """
    endpoint = f"compounds/{source_id}/{compound_id}/sources"
    r = requests.get(f"{UNICHEM_API}/{endpoint}", timeout=15)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return r.json().get("sources", [])

# Sildenafil (Viagra): look up from ChEMBL ID
sources = get_sources_for_compound("CHEMBL192", source_id=1)
print(f"Sildenafil (CHEMBL192) cross-references: {len(sources)} sources")
for s in sources:
    print(f"  [{s['sourceId']}] {s['compoundId']:30s}  {s.get('url', '')[:60]}")
```

### Query 3: Connectivity Search — Structural Relatives

Find compounds with the same core structure but different stereochemistry, salt forms, or isotopic labeling. The connectivity layer of InChI (the first two parts) is used for matching.

```python
import requests, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def connectivity_search(inchikey: str) -> list[dict]:
    """Find all compounds related by InChI connectivity (same skeleton, different stereo/salts).

    Uses the first 14 characters of the InChIKey (connectivity layer only).
    """
    # Extract connectivity key (first block of InChIKey)
    connectivity_key = inchikey.split("-")[0]
    r = requests.get(f"{UNICHEM_API}/connectivity/{connectivity_key}", timeout=15)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return r.json().get("compounds", [])

# Warfarin: find all stereoforms, racemates, and salt forms
warfarin_inchikey = "PJVWKTKQMONHTI-NNFZY2OASA-N"
related = connectivity_search(warfarin_inchikey)
print(f"Warfarin connectivity relatives: {len(related)} compounds")
for cpd in related[:5]:
    inchikey = cpd.get("standardInchiKey", "N/A")
    n_sources = len(cpd.get("sources", []))
    print(f"  {inchikey}  ({n_sources} database sources)")
```

```python
# Compare source coverage across connectivity relatives
def compare_coverage(inchikey: str) -> pd.DataFrame:
    """Show all connectivity relatives and their source counts per database."""
    connectivity_key = inchikey.split("-")[0]
    r = requests.get(f"{UNICHEM_API}/connectivity/{connectivity_key}", timeout=15)
    r.raise_for_status()
    rows = []
    for cpd in r.json().get("compounds", []):
        source_ids = {s["sourceId"] for s in cpd.get("sources", [])}
        rows.append({
            "inchikey": cpd.get("standardInchiKey"),
            "in_chembl": 1 in source_ids,
            "in_drugbank": 2 in source_ids,
            "in_pubchem": 22 in source_ids,
            "in_chebi": 7 in source_ids,
            "n_sources": len(source_ids),
        })
    return pd.DataFrame(rows).sort_values("n_sources", ascending=False)

df = compare_coverage("PJVWKTKQMONHTI-NNFZY2OASA-N")
print(df.to_string(index=False))
```

### Query 4: List All Data Sources

Retrieve the full list of UniChem data sources with their IDs, names, descriptions, and website URLs. Use this to discover available sources and map source IDs to names.

```python
import requests, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def list_sources() -> pd.DataFrame:
    """Return all UniChem data sources as a DataFrame."""
    r = requests.get(f"{UNICHEM_API}/sources", timeout=15)
    r.raise_for_status()
    sources = r.json().get("sources", [])
    rows = []
    for s in sources:
        rows.append({
            "source_id": s.get("sourceId"),
            "name": s.get("nameLong", s.get("nameLabel", "")),
            "label": s.get("nameLabel", ""),
            "description": s.get("description", "")[:80],
            "url": s.get("baseUrl", ""),
        })
    return pd.DataFrame(rows).sort_values("source_id")

sources_df = list_sources()
print(f"Total UniChem sources: {len(sources_df)}")
print(sources_df[["source_id", "label", "name"]].head(15).to_string(index=False))
```

### Query 5: Batch Cross-Reference Translation

Translate a list of compound IDs from one database to another using InChIKey as the pivot. Handles missing entries gracefully.

```python
import requests, time, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def batch_translate(inchikeys: list[str],
                    target_source_ids: list[int] = (1, 2, 7, 22)) -> pd.DataFrame:
    """Translate a list of InChIKeys to IDs in multiple target databases.

    Args:
        inchikeys: List of standard InChIKeys
        target_source_ids: List of UniChem source IDs to retrieve
                          (1=ChEMBL, 2=DrugBank, 7=ChEBI, 22=PubChem)
    Returns:
        DataFrame with one row per InChIKey and one column per target source
    """
    SOURCE_NAMES = {1: "chembl", 2: "drugbank", 7: "chebi", 22: "pubchem",
                    3: "pdb", 6: "kegg", 14: "fda_srs"}
    rows = []
    for ik in inchikeys:
        row = {"inchikey": ik}
        for sid in target_source_ids:
            row[SOURCE_NAMES.get(sid, f"src_{sid}")] = None
        try:
            r = requests.get(f"{UNICHEM_API}/compounds",
                             params={"compound": ik}, timeout=15)
            r.raise_for_status()
            compounds = r.json().get("compounds", [])
            if compounds:
                for src in compounds[0].get("sources", []):
                    col = SOURCE_NAMES.get(src["sourceId"], f"src_{src['sourceId']}")
                    if src["sourceId"] in target_source_ids:
                        row[col] = src["compoundId"]
        except requests.RequestException as e:
            row["error"] = str(e)
        rows.append(row)
        time.sleep(0.1)  # respect ~10 req/s rate limit
    return pd.DataFrame(rows)

# Translate a set of NSAIDs by InChIKey
nsaid_inchikeys = [
    "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",  # aspirin
    "HEFNNWSXXWATRW-UHFFFAOYSA-N",  # ibuprofen
    "CMWTZPSULFXXJA-VIFPVBQESA-N",  # naproxen
    "ZZVUWRFHKOJYTH-UHFFFAOYSA-N",  # diclofenac
]
df = batch_translate(nsaid_inchikeys, target_source_ids=[1, 2, 7, 22])
print(df.to_string(index=False))
df.to_csv("nsaid_xrefs.csv", index=False)
print(f"\nSaved nsaid_xrefs.csv ({len(df)} compounds)")
```

### Query 6: POST Batch Endpoint

Submit multiple InChIKeys in a single POST request for efficient bulk translation (avoids multiple round-trips).

```python
import requests, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def batch_post(inchikeys: list[str]) -> dict[str, list]:
    """Submit multiple InChIKeys in one POST request and return results dict.

    Returns: dict mapping each InChIKey to its list of source records.
    """
    payload = {"type": "inchikey", "compounds": inchikeys}
    r = requests.post(f"{UNICHEM_API}/compounds", json=payload, timeout=30)
    r.raise_for_status()
    results = {}
    for item in r.json().get("compounds", []):
        ik = item.get("standardInchiKey", "")
        results[ik] = item.get("sources", [])
    return results

# Batch query 5 kinase inhibitors
inhibitor_inchikeys = [
    "CMSMOCZEIVJLDB-UHFFFAOYSA-N",  # gefitinib
    "RZEKVGVHFLEQIL-UHFFFAOYSA-N",  # erlotinib
    "ZDZOTLJHXYCWBA-VCVYQWHSSA-N",  # imatinib
    "GXJABQQUPOEUTA-RCHKSFBOSA-N",  # sorafenib
    "SHGAZHPCJJPHSC-ZCFIWIBFSA-N",  # dasatinib
]

results = batch_post(inhibitor_inchikeys)
for ik, sources in results.items():
    source_ids = {s["sourceId"]: s["compoundId"] for s in sources}
    chembl = source_ids.get(1, "N/A")
    drugbank = source_ids.get(2, "N/A")
    pubchem = source_ids.get(22, "N/A")
    print(f"{ik[:14]}...: ChEMBL={chembl}, DrugBank={drugbank}, PubChem={pubchem}")
```

## Key Concepts

### InChI vs InChIKey

UniChem uses the **InChI** (IUPAC International Chemical Identifier) and its hashed form the **InChIKey** as the canonical compound identity. The InChIKey is a 27-character string split into three blocks: the first 14 characters encode the connectivity layer (heavy atoms and bonds), the next 8 encode stereochemistry and charge, and the last character is a version flag. UniChem cross-references compounds by requiring identical standard InChIKeys, ensuring the same chemical entity across databases.

### Source ID Reference Table

| Source ID | Database | Scope |
|-----------|----------|-------|
| 1 | ChEMBL | Bioactive molecules, drug discovery |
| 2 | DrugBank | Approved drugs, pharmacology |
| 3 | PDB | Ligands in crystal structures |
| 6 | KEGG | Metabolites, drugs (Japan) |
| 7 | ChEBI | Chemical ontology, metabolites |
| 14 | FDA SRS | FDA Substance Registration |
| 22 | PubChem | General compound repository |
| 31 | BindingDB | Binding affinity data |
| 41 | SureChEMBL | Patent chemistry |

### Connectivity vs. Standard InChIKey Matching

UniChem offers two matching modes. **Standard InChIKey matching** (the default compound lookup) requires full InChIKey equality — it finds the exact same compound (same stereo, same salt form). **Connectivity search** uses only the first 14 characters and finds all compounds that share the same bond topology, useful for finding racemates, stereoisomers, free acids/bases, and co-crystal partners of the same compound.

## Common Workflows

### Workflow 1: Drug Compound Cross-Reference Report

**Goal**: Given a list of drug names (or ChEMBL IDs), resolve each to all major database IDs and export to CSV.

```python
import requests, time, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"
CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"

SOURCE_NAMES = {1: "chembl", 2: "drugbank", 3: "pdb", 6: "kegg",
                7: "chebi", 22: "pubchem", 14: "fda_srs"}

def chembl_to_inchikey(chembl_id: str) -> str | None:
    """Look up the standard InChIKey for a ChEMBL compound ID."""
    r = requests.get(f"{CHEMBL_API}/molecule/{chembl_id}.json", timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("molecule_structures", {}).get("standard_inchi_key")

def inchikey_to_sources(inchikey: str) -> dict:
    """Return source_id → compound_id dict for an InChIKey."""
    r = requests.get(f"{UNICHEM_API}/compounds",
                     params={"compound": inchikey}, timeout=15)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return {}
    return {s["sourceId"]: s["compoundId"] for s in compounds[0].get("sources", [])}

# Example: top cardiovascular drugs
drug_chembl_ids = {
    "atorvastatin": "CHEMBL1487",
    "lisinopril":   "CHEMBL1237",
    "metoprolol":   "CHEMBL225465",
    "amlodipine":   "CHEMBL1006",
    "warfarin":     "CHEMBL1486228",
}

rows = []
for name, chembl_id in drug_chembl_ids.items():
    ik = chembl_to_inchikey(chembl_id)
    row = {"drug": name, "chembl_id": chembl_id, "inchikey": ik}
    if ik:
        srcs = inchikey_to_sources(ik)
        for sid, col in SOURCE_NAMES.items():
            row[col] = srcs.get(sid)
    rows.append(row)
    time.sleep(0.2)

df = pd.DataFrame(rows)
df.to_csv("drug_xrefs.csv", index=False)
print(df[["drug", "chembl", "drugbank", "pubchem", "chebi"]].to_string(index=False))
print(f"\nSaved drug_xrefs.csv ({len(df)} drugs)")
```

### Workflow 2: Structural Relatives Discovery and Visualization

**Goal**: Find all structural relatives of a compound, summarize their database coverage, and plot a bar chart showing source distribution.

```python
import requests, pandas as pd
import matplotlib.pyplot as plt

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

SOURCE_NAMES = {1: "ChEMBL", 2: "DrugBank", 3: "PDB", 6: "KEGG",
                7: "ChEBI", 22: "PubChem", 14: "FDA SRS", 31: "BindingDB"}

# Metformin connectivity relatives
query_inchikey = "XZWYZXLIPXDOLR-UHFFFAOYSA-N"  # metformin
connectivity_key = query_inchikey.split("-")[0]

r = requests.get(f"{UNICHEM_API}/connectivity/{connectivity_key}", timeout=15)
r.raise_for_status()
compounds = r.json().get("compounds", [])
print(f"Connectivity relatives of metformin: {len(compounds)}")

# Count how often each database appears across all relatives
from collections import Counter
source_counter = Counter()
for cpd in compounds:
    for src in cpd.get("sources", []):
        sid = src["sourceId"]
        if sid in SOURCE_NAMES:
            source_counter[SOURCE_NAMES[sid]] += 1

# Plot source coverage
labels = [k for k, _ in source_counter.most_common()]
counts = [v for _, v in source_counter.most_common()]

fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.bar(labels, counts, color="#2E86AB", edgecolor="white")
ax.bar_label(bars, padding=2)
ax.set_xlabel("Database")
ax.set_ylabel("Number of Structural Relatives Present")
ax.set_title("UniChem Database Coverage — Metformin Connectivity Relatives")
plt.tight_layout()
plt.savefig("unichem_connectivity_coverage.png", dpi=150, bbox_inches="tight")
print(f"Saved unichem_connectivity_coverage.png")

# Summary DataFrame
df = pd.DataFrame([
    {"inchikey": c.get("standardInchiKey"), "n_sources": len(c.get("sources", []))}
    for c in compounds
]).sort_values("n_sources", ascending=False)
print(df.head(10).to_string(index=False))
```

### Workflow 3: Merge ChEMBL Bioactivity with PubChem CIDs

**Goal**: Augment a ChEMBL bioactivity table with PubChem CIDs for downstream analysis in tools that use PubChem identifiers.

```python
import requests, time, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def add_pubchem_cids(df: pd.DataFrame,
                     inchikey_col: str = "standard_inchi_key") -> pd.DataFrame:
    """Add pubchem_cid column to a DataFrame that has an InChIKey column."""
    unique_keys = df[inchikey_col].dropna().unique()
    mapping = {}
    for ik in unique_keys:
        try:
            r = requests.get(f"{UNICHEM_API}/compounds",
                             params={"compound": ik}, timeout=10)
            r.raise_for_status()
            compounds = r.json().get("compounds", [])
            if compounds:
                for src in compounds[0].get("sources", []):
                    if src["sourceId"] == 22:  # PubChem source ID
                        mapping[ik] = src["compoundId"]
                        break
        except requests.RequestException:
            pass
        time.sleep(0.1)
    df = df.copy()
    df["pubchem_cid"] = df[inchikey_col].map(mapping)
    return df

# Simulate a small ChEMBL activity table
chembl_data = pd.DataFrame({
    "compound_name": ["aspirin", "ibuprofen", "naproxen"],
    "standard_inchi_key": [
        "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        "HEFNNWSXXWATRW-UHFFFAOYSA-N",
        "CMWTZPSULFXXJA-VIFPVBQESA-N",
    ],
    "ic50_nm": [2500.0, 13000.0, 1600.0],
})

enriched = add_pubchem_cids(chembl_data)
print(enriched[["compound_name", "ic50_nm", "pubchem_cid"]].to_string(index=False))
enriched.to_csv("chembl_with_pubchem.csv", index=False)
print("\nSaved chembl_with_pubchem.csv")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `compound` | `GET /compounds` | — | Standard InChIKey string (27 chars) | The InChIKey to look up; must be the standard (not non-standard) InChIKey |
| `source_id` (path) | `GET /compounds/{source_id}/{compound_id}/sources` | — | Integer 1-50+ | The source database the input ID belongs to (1=ChEMBL, 22=PubChem) |
| `compound_id` (path) | `GET /compounds/{source_id}/{compound_id}/sources` | — | Database-specific string | The compound ID in the source database (e.g., `CHEMBL25`, `2244`) |
| `connectivity_key` (path) | `GET /connectivity/{key}` | — | First 14 chars of InChIKey | Matches all compounds sharing the same bond topology |
| `type` (POST body) | `POST /compounds` | — | `"inchikey"` | Specifies the identifier type for batch queries |
| `compounds` (POST body) | `POST /compounds` | — | List of InChIKey strings | Batch of InChIKeys to resolve in one request (recommended for 10+ compounds) |
| `timeout` | All requests | 15s | Any positive integer | Seconds before request fails; increase to 30s for connectivity searches |

## Best Practices

1. **Use POST batch endpoint for 10+ compounds**: The `POST /compounds` endpoint accepts multiple InChIKeys in one request, reducing latency and respecting rate limits more efficiently than a loop of GET requests.

2. **Use standard (not non-standard) InChIKeys**: UniChem indexes standard InChIKeys generated by the RDKit or OpenBabel InChI layer. Non-standard InChIKeys (e.g., from proprietary tools without explicit InChI configuration) will return no results. Verify with `from rdkit.Chem.inchi import MolToInchiKey; MolToInchiKey(mol)`.

3. **Fall back to connectivity search when exact match fails**: If a compound is in DrugBank as a salt (e.g., hydrochloride) but you have the free base InChIKey, the standard lookup will miss it. Always run a connectivity search as a fallback for drug cross-referencing.

4. **Cache source list on startup**: The `/sources` endpoint returns all 50+ databases. Call it once at script start and build a `{source_id: name}` dict rather than hard-coding IDs.

   ```python
   def load_source_map() -> dict:
       r = requests.get(f"{UNICHEM_API}/sources", timeout=15)
       r.raise_for_status()
       return {s["sourceId"]: s.get("nameLabel", str(s["sourceId"]))
               for s in r.json().get("sources", [])}
   SOURCE_MAP = load_source_map()
   ```

5. **Handle 404 gracefully**: A 404 from the UniChem API means the compound is not in the database — this is expected, not an error. Use `if r.status_code == 404: return []` rather than `r.raise_for_status()` in batch loops.

## Common Recipes

### Recipe: Resolve Any Compound ID to InChIKey

When to use: You have a PubChem CID or ChEBI ID and need the InChIKey to query UniChem or other services.

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"
PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def pubchem_cid_to_inchikey(cid: int | str) -> str | None:
    """Resolve a PubChem CID to a standard InChIKey via PubChem."""
    r = requests.get(f"{PUBCHEM_API}/compound/cid/{cid}/property/InChIKey/JSON", timeout=10)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    props = r.json()["PropertyTable"]["Properties"]
    return props[0]["InChIKey"] if props else None

def cid_to_all_sources(cid: int | str) -> list:
    """PubChem CID → InChIKey → UniChem cross-references."""
    ik = pubchem_cid_to_inchikey(cid)
    if not ik:
        return []
    r = requests.get(f"{UNICHEM_API}/compounds", params={"compound": ik}, timeout=15)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    return compounds[0].get("sources", []) if compounds else []

sources = cid_to_all_sources(2244)  # PubChem CID for aspirin
print(f"Aspirin (CID=2244) is in {len(sources)} UniChem databases")
for s in sources[:6]:
    print(f"  [{s['sourceId']}] {s['compoundId']}")
```

### Recipe: Check If a Compound Is an Approved Drug

When to use: Quickly flag whether a compound appears in DrugBank (approved drugs) using its InChIKey.

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def is_approved_drug(inchikey: str) -> tuple[bool, str | None]:
    """Check if compound appears in DrugBank (source_id=2). Returns (is_drug, DrugBank_ID)."""
    r = requests.get(f"{UNICHEM_API}/compounds", params={"compound": inchikey}, timeout=15)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return False, None
    for src in compounds[0].get("sources", []):
        if src["sourceId"] == 2:  # DrugBank
            return True, src["compoundId"]
    return False, None

# Test a few compounds
test_compounds = {
    "metformin":     "XZWYZXLIPXDOLR-UHFFFAOYSA-N",
    "caffeine":      "RYYVLZVUVIJVGH-UHFFFAOYSA-N",
    "penicillin G":  "JGSARLDLIJGVTE-MBNYWOFBSA-N",
}
for name, ik in test_compounds.items():
    is_drug, db_id = is_approved_drug(ik)
    status = f"DrugBank:{db_id}" if is_drug else "not in DrugBank"
    print(f"{name}: {status}")
```

### Recipe: Source Coverage Summary for a Compound Set

When to use: Audit which databases cover your compound list — useful before choosing which database to use for downstream analysis.

```python
import requests, time, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"
SOURCE_NAMES = {1: "ChEMBL", 2: "DrugBank", 3: "PDB", 7: "ChEBI",
                22: "PubChem", 6: "KEGG", 14: "FDA SRS"}

def source_coverage_matrix(inchikeys: list[str]) -> pd.DataFrame:
    """Return a boolean matrix: rows=compounds, columns=databases."""
    rows = []
    for ik in inchikeys:
        r = requests.get(f"{UNICHEM_API}/compounds", params={"compound": ik}, timeout=10)
        row = {"inchikey": ik}
        for sid, name in SOURCE_NAMES.items():
            row[name] = False
        if r.ok:
            compounds = r.json().get("compounds", [])
            if compounds:
                for src in compounds[0].get("sources", []):
                    col = SOURCE_NAMES.get(src["sourceId"])
                    if col:
                        row[col] = True
        rows.append(row)
        time.sleep(0.1)
    return pd.DataFrame(rows)

sample_keys = [
    "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",  # aspirin
    "HEFNNWSXXWATRW-UHFFFAOYSA-N",  # ibuprofen
    "XZWYZXLIPXDOLR-UHFFFAOYSA-N",  # metformin
]
coverage = source_coverage_matrix(sample_keys)
print(coverage.to_string(index=False))
print("\nCoverage per database:")
for col in list(SOURCE_NAMES.values()):
    print(f"  {col}: {coverage[col].sum()}/{len(coverage)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `compounds` list for a known compound | Non-standard InChIKey or typo | Verify the InChIKey with RDKit: `Chem.InchiToInchiKey(Chem.MolToInchi(mol))`; ensure it is 27 chars |
| HTTP 404 on compound lookup | Compound not indexed in UniChem | Try connectivity search; compound may be proprietary or very new |
| Connectivity search returns 0 results | Invalid connectivity key (wrong format) | Use only the first 14 characters (first hyphen-separated block) of the standard InChIKey |
| `requests.exceptions.Timeout` | Slow API response under load | Increase timeout to 30s; retry once with exponential backoff |
| Mismatched IDs between ChEMBL and PubChem | Different salt forms indexed separately | Use connectivity search to find the free base/acid form; confirm InChIKey layers match |
| POST batch returns fewer results than input | Some InChIKeys not found | Check the response for missing keys; supplement with individual GET calls for missing ones |
| Source URL field is empty | Not all sources provide URL templates | Use `baseUrl` from the `/sources` endpoint combined with `compoundId` to construct links manually |

## Related Skills

- `chembl-database-bioactivity` — Query ChEMBL for bioactivity data (IC50, Ki) using the compound IDs resolved via UniChem
- `pubchem-compound-search` — Full compound property and bioassay queries using PubChem CIDs from UniChem
- `pdb-database` — Look up 3D ligand structures using PDB ligand codes resolved via UniChem (source ID 3)
- `drugbank-database-access` — Access detailed pharmacology, ADMET, and drug interaction data using DrugBank IDs from UniChem

## References

- [UniChem API documentation](https://www.ebi.ac.uk/unichem/info/webservices) — Official REST API reference with all endpoint descriptions
- [UniChem home page](https://www.ebi.ac.uk/unichem/) — Interactive search interface and database listing
- [Chambers et al., J Cheminform 2013](https://doi.org/10.1186/1758-2946-5-3) — Original UniChem publication describing the InChI-based cross-referencing methodology
- [InChI Trust](https://www.inchi-trust.org/) — InChI standard specification and algorithm documentation
