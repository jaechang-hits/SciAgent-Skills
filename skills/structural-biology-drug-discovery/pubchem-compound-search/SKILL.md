---
name: "pubchem-compound-search"
description: "Query PubChem (110M+ compounds) via PubChemPy/PUG-REST. Search by name/CID/SMILES, get properties (MW, LogP, TPSA), similarity/substructure search, bioactivity. For local cheminformatics use rdkit; for multi-DB queries use bioservices."
license: "CC-BY-4.0"
---

# PubChem Compound Search

## Overview

PubChem is the world's largest freely available chemical database with 110M+ compounds. This skill covers searching compounds by name, structure, or identifier, retrieving molecular properties, performing similarity/substructure searches, and accessing bioactivity data through PubChemPy (Python wrapper) and PUG-REST API (direct HTTP).

## When to Use

- Looking up a compound by name, CAS number, or SMILES to get its PubChem CID and properties
- Retrieving molecular properties (molecular weight, LogP, TPSA, H-bond counts) for known compounds
- Finding structurally similar compounds via Tanimoto similarity search
- Searching for compounds containing a specific substructure (pharmacophore screening)
- Converting between chemical identifier formats (name ↔ CID ↔ SMILES ↔ InChI)
- Accessing bioactivity screening data (assay results, active/inactive status)
- Batch property comparison across a set of drug candidates
- For local molecular computation (fingerprints, descriptors, 3D conformers), use `rdkit` instead
- For querying multiple databases (UniProt, KEGG, ChEMBL) in one workflow, use `bioservices` instead

## Prerequisites

- **Python packages**: `pubchempy`, `requests` (for direct API), `pandas` (for batch processing)
- **No API key required**: PubChem is freely accessible
- **Rate limits**: Max 5 requests/second, 400 requests/minute

```bash
pip install pubchempy requests pandas
```

## Quick Start

```python
import pubchempy as pcp

# Search by name → get properties
compound = pcp.get_compounds("aspirin", "name")[0]
print(f"CID: {compound.cid}")
print(f"SMILES: {compound.canonical_smiles}")
print(f"MW: {compound.molecular_weight}, LogP: {compound.xlogp}")
print(f"HBD: {compound.h_bond_donor_count}, HBA: {compound.h_bond_acceptor_count}")
```

## Workflow

### Step 1: Compound Search

Search by name, CID, SMILES, InChI, or molecular formula.

```python
import pubchempy as pcp

# By name
compounds = pcp.get_compounds("caffeine", "name")
print(f"Found {len(compounds)} compounds for 'caffeine'")

# By CID (fastest)
compound = pcp.Compound.from_cid(2244)  # Aspirin
print(f"CID 2244 = {compound.iupac_name}")

# By SMILES
compound = pcp.get_compounds("CC(=O)OC1=CC=CC=C1C(=O)O", "smiles")[0]
print(f"SMILES lookup: CID {compound.cid}")

# By molecular formula (returns all matches)
formula_matches = pcp.get_compounds("C9H8O4", "formula")
print(f"Formula C9H8O4 matches: {len(formula_matches)} compounds")
```

### Step 2: Property Retrieval

Get molecular properties for one or more compounds.

```python
import pubchempy as pcp

# Full compound object
compound = pcp.get_compounds("ibuprofen", "name")[0]
print(f"MW: {compound.molecular_weight}")
print(f"LogP: {compound.xlogp}")
print(f"TPSA: {compound.tpsa}")
print(f"Rotatable bonds: {compound.rotatable_bond_count}")

# Selective property retrieval (more efficient for specific needs)
props = pcp.get_properties(
    ["MolecularWeight", "XLogP", "TPSA", "HBondDonorCount"],
    "aspirin", "name"
)
print(props)  # List of dicts
```

### Step 3: Similarity Search

Find structurally similar compounds using Tanimoto coefficient.

```python
import pubchempy as pcp

# Get reference compound SMILES
ref = pcp.get_compounds("gefitinib", "name")[0]

# Similarity search (may take 15-30s for async processing)
similar = pcp.get_compounds(
    ref.canonical_smiles, "smiles",
    searchtype="similarity",
    Threshold=85,       # Tanimoto threshold (0-100)
    MaxRecords=50
)
print(f"Found {len(similar)} compounds with ≥85% similarity to gefitinib")
for comp in similar[:5]:
    print(f"  CID {comp.cid}: MW={comp.molecular_weight}")
```

### Step 4: Substructure Search

Find compounds containing a specific structural motif.

```python
import pubchempy as pcp

# Search for sulfonamide-containing compounds
hits = pcp.get_compounds(
    "S(=O)(=O)N", "smiles",
    searchtype="substructure",
    MaxRecords=100
)
print(f"Found {len(hits)} compounds with sulfonamide group")
```

### Step 5: Bioactivity Data Access

Retrieve biological screening results via PUG-REST API.

```python
import requests

cid = 2244  # Aspirin
url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/assaysummary/JSON"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    rows = data.get("Table", {}).get("Row", [])
    print(f"Aspirin has {len(rows)} bioassay records")
```

### Step 6: Batch Property Comparison

Compare properties across multiple compounds.

```python
import pubchempy as pcp
import pandas as pd
import time

compounds = ["aspirin", "ibuprofen", "naproxen", "celecoxib"]
results = []

for name in compounds:
    comp = pcp.get_compounds(name, "name")[0]
    results.append({
        "Name": name, "CID": comp.cid,
        "MW": comp.molecular_weight, "LogP": comp.xlogp,
        "TPSA": comp.tpsa, "HBD": comp.h_bond_donor_count,
        "HBA": comp.h_bond_acceptor_count,
    })
    time.sleep(0.25)  # Respect rate limits

df = pd.DataFrame(results)
print(df.to_string(index=False))
```

### Step 7: Identifier Format Conversion

Convert between chemical identifier formats.

```python
import pubchempy as pcp

compound = pcp.get_compounds("caffeine", "name")[0]
print(f"CID:      {compound.cid}")
print(f"IUPAC:    {compound.iupac_name}")
print(f"SMILES:   {compound.canonical_smiles}")
print(f"InChI:    {compound.inchi}")
print(f"InChIKey: {compound.inchikey}")
print(f"Formula:  {compound.molecular_formula}")

# Download structure files
pcp.download("SDF", "caffeine", "name", "caffeine.sdf", overwrite=True)
print("Downloaded caffeine.sdf")
```

## Key Parameters

| Parameter | Function | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `namespace` | `get_compounds` | required | `"name"`, `"cid"`, `"smiles"`, `"inchi"`, `"formula"` | Identifier type for search |
| `searchtype` | `get_compounds` | `None` | `"similarity"`, `"substructure"` | Type of structure search |
| `Threshold` | similarity search | `90` | `0`-`100` | Tanimoto similarity cutoff (%) |
| `MaxRecords` | structure search | `None` | `1`-`10000` | Maximum results returned |
| `properties` | `get_properties` | required | See API reference | Which molecular properties to retrieve |
| `record_type` | `download` | `"2d"` | `"2d"`, `"3d"` | Structure dimensionality |

## Common Recipes

### Recipe: Drug-Likeness Screening (Lipinski's Rule of Five)

When to use: Quick check if a compound is orally bioavailable.

```python
import pubchempy as pcp

def check_lipinski(name):
    comp = pcp.get_compounds(name, "name")[0]
    rules = {
        "MW ≤ 500": comp.molecular_weight <= 500,
        "LogP ≤ 5": (comp.xlogp or 0) <= 5,
        "HBD ≤ 5": comp.h_bond_donor_count <= 5,
        "HBA ≤ 10": comp.h_bond_acceptor_count <= 10,
    }
    violations = sum(1 for v in rules.values() if not v)
    return rules, violations

rules, v = check_lipinski("metformin")
print(f"Violations: {v}/4 — {'PASS' if v <= 1 else 'FAIL'}")
for rule, passed in rules.items():
    print(f"  {'✓' if passed else '✗'} {rule}")
```

### Recipe: Get All Synonyms for a Compound

When to use: Finding alternative names, trade names, or CAS numbers.

```python
import pubchempy as pcp

synonyms = pcp.get_synonyms("aspirin", "name")
if synonyms:
    names = synonyms[0]["Synonym"]
    print(f"Found {len(names)} synonyms for aspirin:")
    for name in names[:10]:
        print(f"  {name}")
```

### Recipe: Download 2D Structure Image

When to use: Generating structure images for reports or presentations.

```python
import requests

cid = 2519  # Caffeine
url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size=large"
response = requests.get(url)
with open("caffeine_structure.png", "wb") as f:
    f.write(response.content)
print("Saved caffeine_structure.png")
```

## Expected Outputs

- **Compound search**: `pubchempy.Compound` objects with properties (CID, name, SMILES, MW, etc.)
- **Property retrieval**: List of dictionaries with requested properties
- **Similarity search**: List of `Compound` objects sorted by similarity
- **Bioactivity query**: JSON with assay results (activity outcome, assay ID, target)
- **Structure download**: SDF, JSON, or PNG files

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `IndexError: list index out of range` | No compounds found for query | Check spelling; try alternative names or CID |
| Request timeout (>30s) | Large similarity/substructure search | Reduce `MaxRecords`; PubChemPy handles async polling automatically |
| Empty property values (`None`) | Property not available for this compound | Check if property exists before use: `if comp.xlogp is not None` |
| `HTTP 503 Service Unavailable` | Rate limit exceeded | Add `time.sleep(0.25)` between requests; max 5 req/sec |
| `BadRequestError` | Invalid SMILES or identifier | Validate SMILES syntax; use canonical SMILES from RDKit |
| Formula search returns too many hits | Common formula shared by many isomers | Use SMILES or InChI for more specific searches |
| Bioactivity API returns empty | Compound has no bioassay data | Not all compounds have been tested; check PubChem web interface |

## References

- [PubChem PUG-REST API](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) — official REST API docs
- [PubChemPy documentation](https://pubchempy.readthedocs.io/) — Python wrapper docs
- [PubChem PUG-REST tutorial](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest-tutorial) — step-by-step guide
- [PubChem database](https://pubchem.ncbi.nlm.nih.gov/) — web interface
