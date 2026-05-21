---
name: "unichem-database"
description: "Cross-reference compound IDs across 20+ databases (ChEMBL, DrugBank, PubChem, ChEBI, PDB, SureChEMBL, HMDB, DrugCentral, BindingDB) via UniChem REST API. Resolve InChIKeys to source IDs, translate between source-specific IDs, find structurally related compounds by connectivity. POST with a JSON body for all cross-reference queries; only /sources is GET. No auth required."
license: "Apache-2.0"
---

# UniChem Database

## Overview

UniChem is a chemical structure cross-referencing service from EMBL-EBI that links compound records across 20+ public chemistry databases using InChI-based identifiers.
It maps a single chemical entity to its corresponding IDs in ChEMBL, DrugBank, PubChem, ChEBI, PDB (RCSB and PDBe), SureChEMBL, HMDB, DrugCentral, BindingDB, and others.
Access is via a free REST API at https://www.ebi.ac.uk/unichem/api/v1/ - no API key required.
Important: every cross-reference query is sent as POST with a JSON body; only the catalogue endpoint GET /sources is implemented as a GET.

## When to Use

- Translating a ChEMBL compound ID to a PubChem CID, DrugBank accession, or ChEBI ID for cross-database analysis
- Resolving an InChIKey to all database sources where a compound appears
- Finding all structurally related compounds (same connectivity, different stereochemistry/salts) across databases using connectivity search
- Validating compound identity across sources before merging datasets from multiple databases
- Building a compound cross-reference table for a drug discovery project (linking bioactivity data in ChEMBL to structural data in PDB)
- Checking if a synthesized compound or a vendor compound exists in any public database by InChIKey
- For full bioactivity profiles (IC50, Ki) use chembl-database-bioactivity; UniChem provides only ID cross-references, not experimental data
- For compound property prediction or substructure searching use pubchem-compound-search; UniChem is for identifier translation only

## Prerequisites

- **Python packages**: requests, pandas, matplotlib
- **Data requirements**: compound InChIKeys (standard 27-character XXXXXXXXXXXXXX-XXXXXXXXXX-X), source-specific IDs (e.g. CHEMBL25), or PubChem CIDs as starting points
- **Environment**: internet connection; no API key required
- **Rate limits**: ~10 requests/second; add time.sleep(0.1) between requests in batch loops; no daily quota

```bash
pip install requests pandas matplotlib
```

## Quick Start

The UniChem /compounds endpoint is POST-only - GET returns 405 Method Not Allowed. Submit a JSON body {type: inchikey, compound: KEY} and read per-database hits from compounds[0][sources]. Each source record carries an id (numeric database ID) and a compoundId (the ID in that database).

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def unichem_post(endpoint: str, body: dict) -> dict:
    """POST request to UniChem API; raise on HTTP errors."""
    r = requests.post(f"{UNICHEM_API}/{endpoint}", json=body, timeout=20)
    r.raise_for_status()
    return r.json()

# Find all database sources for aspirin by InChIKey
inchikey = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"  # aspirin
result = unichem_post("compounds", {"type": "inchikey", "compound": inchikey})
compounds = result.get("compounds", [])
print(f"Found {len(compounds)} compound record(s) for {inchikey}")
if compounds:
    sources = compounds[0].get("sources", [])
    print(f"  Present in {len(sources)} database records")
    seen = set()
    for src in sources:
        if src["id"] in seen:
            continue
        seen.add(src["id"])
        print(f"  source id={src['id']:>3} ({src['shortName']:>12}): {src['compoundId']}")
        if len(seen) >= 5:
            break
# Found 1 compound record(s) for BSYNRYMUTXBXSQ-UHFFFAOYSA-N
#   Present in many database records
#   source id=  1 (      chembl): CHEMBL25
#   source id=  2 (    drugbank): DB00945
#   source id=  3 (    rcsb_pdb): AIN
```

## Core API

### Query 1: InChIKey Lookup - All Sources

Search for a compound by its standard InChIKey and retrieve all database records. This is the primary cross-reference method. The endpoint is POST /compounds; the response carries one entry in compounds (if found), each with a sources list whose records use id (source database) and compoundId (the ID in that database).

```python
import requests, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

# Common source IDs (verify with the /sources endpoint - see Query 4)
SOURCE_NAMES = {
    1: "ChEMBL", 2: "DrugBank", 3: "RCSB PDB", 4: "GtoPdb", 5: "PDBe",
    7: "ChEBI", 14: "FDA SRS", 15: "SureChEMBL", 18: "HMDB", 22: "PubChem",
    31: "BindingDB", 32: "CompTox", 33: "LIPID MAPS", 34: "DrugCentral",
    37: "BRENDA", 38: "Rhea", 41: "SwissLipids", 49: "Probes-and-Drugs",
}

def lookup_by_inchikey(inchikey: str) -> pd.DataFrame:
    """Return all database cross-references for an InChIKey."""
    r = requests.post(f"{UNICHEM_API}/compounds",
                      json={"type": "inchikey", "compound": inchikey}, timeout=20)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return pd.DataFrame()
    rows = []
    for src in compounds[0].get("sources", []):
        rows.append({
            "source_id": src["id"],
            "source_name": SOURCE_NAMES.get(src["id"], src.get("shortName", "")),
            "compound_id": src["compoundId"],
            "url": src.get("url", ""),
        })
    return pd.DataFrame(rows).sort_values(["source_id", "compound_id"])

# Triclosan cross-references
df = lookup_by_inchikey("XEFQLINVKFYRCS-UHFFFAOYSA-N")
print(f"Triclosan found in {df['source_id'].nunique()} distinct databases ({len(df)} records):")
print(df[["source_name", "compound_id"]].head(8).to_string(index=False))
# Triclosan found in 16 distinct databases
#   ChEMBL    CHEMBL849
#   DrugBank  DB08604
#   RCSB PDB  TCL
#   ChEBI     CHEBI:164200
```
```python
# Extract specific source IDs from cross-reference table
def get_id_for_source(inchikey: str, source_id: int) -> str | None:
    """Return the compound ID in a specific database, or None if not found."""
    r = requests.post(f"{UNICHEM_API}/compounds",
                      json={"type": "inchikey", "compound": inchikey}, timeout=20)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return None
    for src in compounds[0].get("sources", []):
        if src["id"] == source_id:
            return src["compoundId"]
    return None

triclosan = "XEFQLINVKFYRCS-UHFFFAOYSA-N"
chembl_id   = get_id_for_source(triclosan, source_id=1)   # ChEMBL
pubchem_id  = get_id_for_source(triclosan, source_id=22)  # PubChem
drugbank_id = get_id_for_source(triclosan, source_id=2)   # DrugBank
print(f"Triclosan: ChEMBL={chembl_id}, PubChem={pubchem_id}, DrugBank={drugbank_id}")
# Triclosan: ChEMBL=CHEMBL849, PubChem=5564, DrugBank=DB08604
```

### Query 2: Compound Lookup by Source-Specific ID

Given a known compound ID in a specific source database (e.g., a ChEMBL ID), retrieve all cross-references. Use type: sourceID with the compound s source ID alongside the numeric sourceID in the body. Returns the same data shape as the InChIKey lookup.

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def get_sources_for_compound(compound_id: str, source_id: int) -> list:
    """Get all database cross-references for a compound identified in a specific source.

    Args:
        compound_id: The ID in the source database (e.g., CHEMBL192)
        source_id: UniChem source ID (1=ChEMBL, 2=DrugBank, 22=PubChem, 7=ChEBI)
    """
    body = {"type": "sourceID", "compound": compound_id, "sourceID": source_id}
    r = requests.post(f"{UNICHEM_API}/compounds", json=body, timeout=20)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return []
    return compounds[0].get("sources", [])

# Sildenafil (Viagra): look up starting from ChEMBL ID
sources = get_sources_for_compound("CHEMBL192", source_id=1)
distinct_dbs = {s["id"] for s in sources}
print(f"Sildenafil (CHEMBL192): {len(sources)} source records across {len(distinct_dbs)} databases")
seen = set()
for s in sources:
    if s["id"] in seen:
        continue
    seen.add(s["id"])
    print(f"  [{s['id']:>3}] {s['shortName']:>15}: {s['compoundId']}")
    if len(seen) >= 8:
        break
# Sildenafil (CHEMBL192): 272 source records across 19 databases
```

### Query 3: Connectivity Search - Structural Relatives

Find compounds with the same core structure but different stereochemistry, salt forms, isotopic labeling, or protonation. The endpoint is POST /connectivity and accepts a full standard InChIKey (the API rejects 14-character fragments with 404 Not found). Internally UniChem uses the connectivity layer for matching but returns hits that may differ at the stereo/charge/isotope layers.

Unlike /compounds, the connectivity response returns a flat sources list (one entry per database hit across all relatives) plus the queried searchedCompound and totalCompounds/totalSources summary fields. Each hit s comparison dict shows which InChI layers matched.

```python
import requests, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def connectivity_search(inchikey: str) -> dict:
    """Find all compounds related by InChI connectivity (same skeleton, possibly different stereo/salts).

    Pass a FULL standard InChIKey (27 chars). The server rejects 14-char fragments.
    """
    body = {"type": "inchikey", "compound": inchikey}
    r = requests.post(f"{UNICHEM_API}/connectivity", json=body, timeout=30)
    r.raise_for_status()
    return r.json()

# Warfarin: find all stereoforms, racemates, and salt forms
warfarin_inchikey = "PJVWKTKQMONHTI-UHFFFAOYSA-N"
data = connectivity_search(warfarin_inchikey)
print(f"Warfarin connectivity relatives: {data['totalCompounds']} unique compounds, "
      f"{data['totalSources']} database records")
hits = data.get("sources", [])
by_source = {}
for h in hits:
    by_source.setdefault(h["shortName"], []).append(h["compoundId"])
for name, ids in sorted(by_source.items(), key=lambda kv: -len(kv[1]))[:8]:
    print(f"  {name:>15}: {len(ids):>4} IDs (e.g. {ids[0]})")
# Warfarin connectivity relatives: 13 unique compounds, 353 database records
```
```python
# Compare source coverage across connectivity relatives
def compare_coverage(inchikey: str) -> pd.DataFrame:
    """Show connectivity relatives split by their source-database coverage."""
    data = connectivity_search(inchikey)
    rows = []
    for src in data.get("sources", []):
        rows.append({
            "source_id":    src["id"],
            "source_name":  src["shortName"],
            "compound_id":  src["compoundId"],
            "stereo_match": src["comparison"].get("stereoSp3", False),
            "salt_match":   src["comparison"].get("protonation", False),
        })
    return pd.DataFrame(rows)

df = compare_coverage("PJVWKTKQMONHTI-UHFFFAOYSA-N")
print(f"Total records: {len(df)}")
print(df.head(10).to_string(index=False))
print(f"Records with stereo mismatch (skeleton matches, stereo differs): {(~df['stereo_match']).sum()}")
```

### Query 4: List All Data Sources

Retrieve the full list of UniChem data sources with their IDs, names, descriptions, and website URLs. This is the only endpoint served by GET. The response uses sourceID (capital ID) inside each source entry.

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
            "source_id":  s["sourceID"],
            "name":       s.get("nameLong") or s.get("nameLabel", ""),
            "label":      s.get("nameLabel", ""),
            "short_name": s.get("name", ""),
            "uci_count":  s.get("UCICount"),
            "url":        s.get("baseIdUrl", ""),
        })
    return pd.DataFrame(rows).sort_values("source_id")

sources_df = list_sources()
print(f"Total UniChem sources: {len(sources_df)}")
print(sources_df[["source_id", "label", "uci_count"]].to_string(index=False))
# Total UniChem sources: 23
#   1   ChEMBL          2854815
#   2   DrugBank          14622
#  22   PubChem      123392679
```

### Query 5: Per-Compound Loop (No Batch Endpoint)

UniChem does not support a list-batch shape - the /compounds POST accepts only a single compound per request. Submitting {compounds: [...]} or {inchikeys: [...]} returns 400 illegal_argument_exception. For multiple inputs, iterate with a small sleep to respect the ~10 req/s rate limit.

```python
import requests, time, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def batch_translate(inchikeys: list[str],
                    target_source_ids=(1, 2, 7, 22)) -> pd.DataFrame:
    """Translate a list of InChIKeys to IDs in multiple target databases.

    Loops one POST per InChIKey (UniChem has no list-batch endpoint).
    """
    SOURCE_NAMES = {1: "chembl", 2: "drugbank", 3: "pdb", 7: "chebi",
                    14: "fda_srs", 22: "pubchem", 34: "drugcentral"}
    rows = []
    for ik in inchikeys:
        row = {"inchikey": ik}
        for sid in target_source_ids:
            row[SOURCE_NAMES.get(sid, f"src_{sid}")] = None
        try:
            r = requests.post(f"{UNICHEM_API}/compounds",
                              json={"type": "inchikey", "compound": ik}, timeout=20)
            r.raise_for_status()
            compounds = r.json().get("compounds", [])
            if compounds:
                for src in compounds[0].get("sources", []):
                    if src["id"] in target_source_ids:
                        col = SOURCE_NAMES.get(src["id"], f"src_{src['id']}")
                        if row[col] is None:
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
    "DCOPUUMXTXDBNB-UHFFFAOYSA-N",  # diclofenac (free acid)
]
df = batch_translate(nsaid_inchikeys, target_source_ids=[1, 2, 7, 22])
print(df.to_string(index=False))
df.to_csv("nsaid_xrefs.csv", index=False)
print(f"Saved nsaid_xrefs.csv ({len(df)} compounds)")
```

### Query 6: Per-Compound Loop with Source-ID Inputs

When the starting identifiers are not InChIKeys but source-specific IDs (e.g., a list of ChEMBL IDs from a bioactivity table), use type=sourceID and loop, again one POST per ID.

```python
import requests, time

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def translate_source_ids(ids: list[str], from_source: int,
                         to_sources=(2, 22, 34)) -> list[dict]:
    """Translate IDs in one source database to IDs in target databases.

    Args:
        ids: list of compound IDs in the from_source database
        from_source: source ID of the input list (1=ChEMBL, 22=PubChem, ...)
        to_sources: iterable of target source IDs to extract
    """
    out = []
    for cid in ids:
        body = {"type": "sourceID", "compound": cid, "sourceID": from_source}
        r = requests.post(f"{UNICHEM_API}/compounds", json=body, timeout=20)
        row = {"input": cid}
        if r.ok:
            compounds = r.json().get("compounds", [])
            if compounds:
                row["inchikey"] = compounds[0].get("standardInchiKey")
                hits = {s["id"]: s["compoundId"] for s in compounds[0].get("sources", [])}
                for tsid in to_sources:
                    row[f"src_{tsid}"] = hits.get(tsid)
        out.append(row)
        time.sleep(0.1)
    return out

# Three kinase inhibitors known by ChEMBL ID
chembl_inputs = ["CHEMBL535", "CHEMBL553", "CHEMBL941"]  # nilotinib, dasatinib, imatinib
rows = translate_source_ids(chembl_inputs, from_source=1, to_sources=(2, 22, 34))
for row in rows:
    ik = (row.get("inchikey") or "?")[:14]
    print(f"{row['input']:>10}  ik={ik}...  "
          f"DrugBank={row.get('src_2')}, PubChem={row.get('src_22')}, "
          f"DrugCentral={row.get('src_34')}")
```

## Key Concepts

### InChI vs InChIKey

UniChem uses the **InChI** (IUPAC International Chemical Identifier) and its hashed form the **InChIKey** as the canonical compound identity. The InChIKey is a 27-character string split into three blocks: the first 14 characters encode the connectivity layer (heavy atoms and bonds), the next 8 encode stereochemistry and charge, and the last character is a version flag. UniChem cross-references compounds by requiring identical standard InChIKeys, ensuring the same chemical entity across databases.

### Source ID Reference Table (verified live against /sources)

| Source ID | Database | Scope |
|-----------|----------|-------|
| 1  | ChEMBL          | Bioactive molecules, drug discovery |
| 2  | DrugBank        | Approved drugs, pharmacology |
| 3  | RCSB PDB        | Ligands in crystal structures (US) |
| 4  | Guide to Pharmacology | Pharmacology targets/ligands |
| 5  | PDBe            | Ligands in crystal structures (Europe) |
| 7  | ChEBI           | Chemical ontology, metabolites |
| 14 | FDA SRS         | FDA Substance Registration System |
| 15 | SureChEMBL      | Patent chemistry |
| 18 | HMDB            | Human Metabolome Database |
| 22 | PubChem         | General compound repository |
| 31 | BindingDB       | Binding affinity data |
| 32 | CompTox         | Environmental tox dashboard |
| 33 | LIPID MAPS      | Lipid structures |
| 34 | DrugCentral     | Approved drugs + pharmacology |
| 37 | BRENDA          | Enzyme substrates/products |
| 38 | Rhea            | Biochemical reactions |
| 41 | SwissLipids     | Lipid structures |
| 49 | Probes-and-Drugs| Chemical probes |

### Field Naming: id vs sourceID

This is the single most common error when scripting UniChem. The two endpoints use different field names for the source database identifier:

- **GET /sources** lists databases as objects with a **sourceID** field (capital ID).
- **POST /compounds** and **POST /connectivity** return per-database hits inside sources lists, where the source identifier is a plain **id** field. There is no sourceID or sourceId key on these per-hit records.

Always use src["id"] when iterating compound or connectivity responses, and use s["sourceID"] when iterating the /sources catalogue.

### Connectivity vs Standard InChIKey Matching

POST /compounds returns exact InChIKey matches (same stereo, salt, isotopes). POST /connectivity returns all compounds sharing the bond topology - useful for finding racemates, stereoisomers, free acids/bases, and co-crystal partners. The connectivity response includes a comparison dict per hit indicating which InChI layers matched (stereoSp3, protonation, isotope, etc.); use it to filter for same skeleton, different stereo only relatives.

## Common Workflows

### Workflow 1: Drug Compound Cross-Reference Report

**Goal**: Given a list of drug names (or ChEMBL IDs), resolve each to all major database IDs and export to CSV.

```python
import requests, time, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"
CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"

SOURCE_NAMES = {1: "chembl", 2: "drugbank", 3: "rcsb_pdb",
                7: "chebi", 22: "pubchem", 14: "fda_srs", 34: "drugcentral"}

def chembl_to_inchikey(chembl_id: str) -> str | None:
    """Look up the standard InChIKey for a ChEMBL compound ID."""
    r = requests.get(f"{CHEMBL_API}/molecule/{chembl_id}.json", timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("molecule_structures", {}).get("standard_inchi_key")

def inchikey_to_sources(inchikey: str) -> dict:
    """Return source_id -> compound_id dict for an InChIKey (first hit per source)."""
    r = requests.post(f"{UNICHEM_API}/compounds",
                      json={"type": "inchikey", "compound": inchikey}, timeout=20)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return {}
    out = {}
    for s in compounds[0].get("sources", []):
        out.setdefault(s["id"], s["compoundId"])
    return out

# Example: top cardiovascular drugs
drug_chembl_ids = {
    "atorvastatin": "CHEMBL1487",
    "lisinopril":   "CHEMBL1237",
    "metoprolol":   "CHEMBL13",
    "amlodipine":   "CHEMBL1491",
    "warfarin":     "CHEMBL1464",
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
print(f"Saved drug_xrefs.csv ({len(df)} drugs)")
```

### Workflow 2: Structural Relatives Discovery and Visualization

**Goal**: Find all structural relatives of a compound, summarize their database coverage, and plot a bar chart showing source distribution.

```python
import requests, pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

SOURCE_NAMES = {1: "ChEMBL", 2: "DrugBank", 3: "RCSB PDB", 5: "PDBe",
                7: "ChEBI", 14: "FDA SRS", 15: "SureChEMBL",
                22: "PubChem", 31: "BindingDB", 34: "DrugCentral"}

# Aspirin connectivity relatives (covers acetylsalicylate salts)
query_inchikey = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"

r = requests.post(f"{UNICHEM_API}/connectivity",
                  json={"type": "inchikey", "compound": query_inchikey}, timeout=30)
r.raise_for_status()
data = r.json()
hits = data.get("sources", [])
print(f"Aspirin connectivity relatives: {data['totalCompounds']} unique compounds, "
      f"{len(hits)} database records")

# Count how often each named database appears
source_counter = Counter()
for h in hits:
    if h["id"] in SOURCE_NAMES:
        source_counter[SOURCE_NAMES[h["id"]]] += 1

labels = [k for k, _ in source_counter.most_common()]
counts = [v for _, v in source_counter.most_common()]

fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.bar(labels, counts, color="#2E86AB", edgecolor="white")
ax.bar_label(bars, padding=2)
ax.set_xlabel("Database")
ax.set_ylabel("Number of Source Records (relatives x hits)")
ax.set_title("UniChem Connectivity Records - Aspirin Skeleton")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig("unichem_connectivity_coverage.png", dpi=150, bbox_inches="tight")
print("Saved unichem_connectivity_coverage.png")
plt.close(fig)

# DataFrame summary by source
df = pd.DataFrame(source_counter.most_common(), columns=["database", "records"])
print(df.to_string(index=False))
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
            r = requests.post(f"{UNICHEM_API}/compounds",
                              json={"type": "inchikey", "compound": ik}, timeout=15)
            r.raise_for_status()
            compounds = r.json().get("compounds", [])
            if compounds:
                for src in compounds[0].get("sources", []):
                    if src["id"] == 22:  # PubChem
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
print("Saved chembl_with_pubchem.csv")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| type (body) | POST /compounds, POST /connectivity | - | inchikey, sourceID | Selects the kind of identifier in compound. inchikey requires a 27-char standard InChIKey; sourceID also requires the numeric sourceID field. |
| compound (body) | POST /compounds, POST /connectivity | - | One string (no list) | The identifier to look up. UniChem does NOT support a list-batch shape; loop one POST per compound. |
| sourceID (body) | POST /compounds (with type=sourceID) | - | Integer DB id from /sources | The source database the input compound belongs to (1=ChEMBL, 2=DrugBank, 22=PubChem, ...). |
| Per-hit id (response) | POST /compounds, POST /connectivity | - | Integer | Source database id of each hit in sources. **Use src["id"], NOT src["sourceID"]** for these per-hit records. |
| sourceID (response) | GET /sources | - | Integer | Numeric ID of each database entry in the catalogue (capital ID). |
| timeout | All requests | 20s | Any positive integer | Seconds before request fails; raise to 30s for /connectivity on common skeletons. |

## Best Practices

1. **Use POST everywhere except /sources**: GET /compounds returns 405 Method Not Allowed; GET /compounds/{src}/{id} and GET /connectivity/{key} return 404. The only GET endpoint is /sources. Always POST with a JSON body.

2. **Use the correct field - id on hits, sourceID on /sources**: Inside the sources list returned by POST /compounds and POST /connectivity, each record s source database is in the id key. Reading src["sourceID"] raises KeyError. The capital-ID sourceID field only appears in the catalogue returned by GET /sources.

3. **Use standard (not non-standard) InChIKeys**: UniChem indexes standard InChIKeys. Non-standard InChIKeys will return no results. Verify with: from rdkit.Chem.inchi import MolToInchiKey; MolToInchiKey(mol).

4. **Fall back to connectivity search when exact match fails**: If a compound is in DrugBank as a salt (e.g., hydrochloride) but you have the free base InChIKey, the standard lookup will miss it. Run a connectivity search as a fallback for drug cross-referencing.

5. **Pass the full InChIKey to /connectivity**: The endpoint expects a complete 27-character standard InChIKey. Submitting only the 14-char connectivity fragment returns {response: Not found}. UniChem strips the stereo/charge layers internally.

6. **Cache the source list on startup**: Call /sources once and build a {sourceID: nameLabel} dict rather than hard-coding IDs.

```python
def load_source_map() -> dict:
    r = requests.get(f"{UNICHEM_API}/sources", timeout=15)
    r.raise_for_status()
    return {s["sourceID"]: s.get("nameLabel", str(s["sourceID"]))
            for s in r.json().get("sources", [])}
```

7. **No batch endpoint exists - loop with sleep**: Submitting {compounds: [...]} or {inchikeys: [...]} returns 400 illegal_argument_exception. Iterate POSTs with time.sleep(0.1) between calls (~10 req/s).

## Common Recipes

### Recipe: Resolve Any Compound ID to InChIKey

When to use: You have a PubChem CID or ChEBI ID and need the InChIKey to query UniChem or other services.

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"
PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def pubchem_cid_to_inchikey(cid) -> str | None:
    """Resolve a PubChem CID to a standard InChIKey via PubChem."""
    r = requests.get(f"{PUBCHEM_API}/compound/cid/{cid}/property/InChIKey/JSON", timeout=10)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    props = r.json()["PropertyTable"]["Properties"]
    return props[0]["InChIKey"] if props else None

def cid_to_all_sources(cid) -> list:
    """PubChem CID -> InChIKey -> UniChem cross-references."""
    ik = pubchem_cid_to_inchikey(cid)
    if not ik:
        return []
    r = requests.post(f"{UNICHEM_API}/compounds",
                      json={"type": "inchikey", "compound": ik}, timeout=20)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    return compounds[0].get("sources", []) if compounds else []

sources = cid_to_all_sources(2244)  # PubChem CID for aspirin
distinct = {s["id"] for s in sources}
print(f"Aspirin (CID=2244) is in {len(distinct)} UniChem databases ({len(sources)} records)")
seen = set()
for s in sources:
    if s["id"] in seen:
        continue
    seen.add(s["id"])
    print(f"  [{s['id']:>3}] {s['shortName']:>15}: {s['compoundId']}")
    if len(seen) >= 6:
        break
```

### Recipe: Check If a Compound Is an Approved Drug

When to use: Quickly flag whether a compound appears in DrugBank (source 2) using its InChIKey.

```python
import requests

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"

def is_approved_drug(inchikey: str) -> tuple[bool, str | None]:
    """Check if compound appears in DrugBank (id=2). Returns (is_drug, DrugBank_ID)."""
    r = requests.post(f"{UNICHEM_API}/compounds",
                      json={"type": "inchikey", "compound": inchikey}, timeout=20)
    r.raise_for_status()
    compounds = r.json().get("compounds", [])
    if not compounds:
        return False, None
    for src in compounds[0].get("sources", []):
        if src["id"] == 2:  # DrugBank
            return True, src["compoundId"]
    return False, None

# Test a few compounds
test_compounds = {
    "aspirin":      "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
    "triclosan":    "XEFQLINVKFYRCS-UHFFFAOYSA-N",
    "sildenafil":   "BNRNXUUZRGQAQC-UHFFFAOYSA-N",
}
for name, ik in test_compounds.items():
    is_drug, db_id = is_approved_drug(ik)
    status = f"DrugBank:{db_id}" if is_drug else "not in DrugBank"
    print(f"{name:>12}: {status}")
```

### Recipe: Source Coverage Summary for a Compound Set

When to use: Audit which databases cover your compound list - useful before choosing which database to use for downstream analysis.

```python
import requests, time, pandas as pd

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1"
SOURCE_NAMES = {1: "ChEMBL", 2: "DrugBank", 3: "RCSB PDB", 7: "ChEBI",
                14: "FDA SRS", 22: "PubChem", 34: "DrugCentral"}

def source_coverage_matrix(inchikeys: list[str]) -> pd.DataFrame:
    """Return a boolean matrix: rows=compounds, columns=databases."""
    rows = []
    for ik in inchikeys:
        r = requests.post(f"{UNICHEM_API}/compounds",
                          json={"type": "inchikey", "compound": ik}, timeout=15)
        row = {"inchikey": ik}
        for sid, name in SOURCE_NAMES.items():
            row[name] = False
        if r.ok:
            compounds = r.json().get("compounds", [])
            if compounds:
                ids_present = {s["id"] for s in compounds[0].get("sources", [])}
                for sid, name in SOURCE_NAMES.items():
                    row[name] = sid in ids_present
        rows.append(row)
        time.sleep(0.1)
    return pd.DataFrame(rows)

sample_keys = [
    "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",  # aspirin
    "HEFNNWSXXWATRW-UHFFFAOYSA-N",  # ibuprofen
    "XEFQLINVKFYRCS-UHFFFAOYSA-N",  # triclosan
]
coverage = source_coverage_matrix(sample_keys)
print(coverage.to_string(index=False))
print("Coverage per database:")
for col in list(SOURCE_NAMES.values()):
    print(f"  {col}: {coverage[col].sum()}/{len(coverage)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| 405 Method Not Allowed on /compounds | Hitting the endpoint with GET | UniChem /compounds is POST-only. Send requests.post(url, json={type:inchikey, compound:ik}). |
| KeyError: sourceID (or sourceId) on per-hit records | Reading the wrong field name | Use src["id"] for hits inside compounds[0][sources] and the sources list from /connectivity. sourceID only exists in the /sources catalogue. |
| 400 illegal_argument_exception field name is null or empty | Tried {compounds: [...]} or {inchikeys: [...]} batch | No batch endpoint exists. Loop with time.sleep(0.1) between POSTs. |
| {response: Not found} from /connectivity | Passed only the 14-char fragment | Send the full 27-char standard InChIKey; UniChem strips the stereo layers internally. |
| Empty compounds list for a known compound | Non-standard InChIKey, salt-form mismatch, or compound missing | Verify the InChIKey with RDKit; try POST /connectivity to catch salt/stereo variants. |
| Too many records from connectivity | Same skeleton matches many SureChEMBL patent IDs | Filter by src["id"] to drop source 15 (SureChEMBL) or by comparison.stereoSp3 == True. |
| requests.exceptions.Timeout | Slow API response under load | Increase timeout to 30s for /connectivity; retry once with exponential backoff. |
| Source URL field is empty | Not all sources provide URL templates | Use baseIdUrl from the /sources endpoint combined with compoundId to construct links manually. |

## Related Skills

- chembl-database-bioactivity - Query ChEMBL for bioactivity data (IC50, Ki) using the compound IDs resolved via UniChem
- pubchem-compound-search - Full compound property and bioassay queries using PubChem CIDs from UniChem
- pdb-database - Look up 3D ligand structures using PDB ligand codes (source 3 or 5) resolved via UniChem
- drugbank-database-access - Detailed pharmacology, ADMET, and drug interaction data using DrugBank IDs from UniChem

## References

- [UniChem API documentation](https://www.ebi.ac.uk/unichem/info/webservices) - Official REST API reference with all endpoint descriptions
- [UniChem home page](https://www.ebi.ac.uk/unichem/) - Interactive search interface and database listing
- [Chambers et al., J Cheminform 2013](https://doi.org/10.1186/1758-2946-5-3) - Original UniChem publication describing the InChI-based cross-referencing methodology
- [InChI Trust](https://www.inchi-trust.org/) - InChI standard specification and algorithm documentation
