---
name: "gtopdb-database"
description: "Query IUPHAR/BPS Guide to Pharmacology (GtoPdb) for receptor-ligand interactions, target/ligand metadata, families, and approved drugs. Affinities (pKi/pIC50/pKd), action (Agonist/Antagonist/etc.), species, structures (SMILES/InChI). No auth. Always resolve targets via geneSymbol/accession; most metadata lives in sub-resources (/databaseLinks, /structure, /synonyms)."
license: "ODbL-1.0"
---

# Guide to Pharmacology (GtoPdb) Database

## Overview

The IUPHAR/BPS Guide to Pharmacology (GtoPdb) catalogues drug targets, ligands, and quantitative interactions across receptor pharmacology. The web services REST API at `https://www.guidetopharmacology.org/services/` returns JSON for targets, ligands, interactions, and family hierarchies. Base records are intentionally lean — gene symbols, UniProt accessions, ChEMBL IDs, SMILES/InChI all live in sub-resources (`/targets/{id}/databaseLinks`, `/targets/{id}/synonyms`, `/ligands/{id}/structure`, `/ligands/{id}/databaseLinks`). No authentication required.

## When to Use

- Looking up the affinity (pKi/pIC50/pKd) of a ligand at a specific target
- Listing all annotated ligands for a receptor (e.g., μ-opioid receptor / OPRM1)
- Finding the approval status of a ligand (`approved=true`) and its cross-references (PubChem CID, ChEMBL ID, DrugBank ID)
- Retrieving the IUPHAR family hierarchy (867 families) for receptor classification
- Pulling structure descriptors (SMILES, InChI, InChIKey) for chemoinformatics
- Mapping HGNC symbol → UniProt → GtoPdb target ID for cross-database integration
- Use `chembl-database-bioactivity` for larger bioactivity datasets (2.4M+ compounds); GtoPdb is curated, smaller, with more annotation depth
- Use `dailymed-database` for FDA-approved drug labelling; GtoPdb is for pharmacology, not regulatory text

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: HGNC symbols, UniProt accessions, GtoPdb target/ligand IDs, or drug INNs
- **Environment**: internet connection; no API key
- **Rate limits**: no published limits; use `time.sleep(0.2)` between requests in batch loops

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

BASE = "https://www.guidetopharmacology.org/services"

# Resolve HGNC symbol → GtoPdb target. geneSymbol= and accession= give an
# exact match. (name= matches across all fields and silently returns the
# wrong target — never use it for canonical lookups.)
r = requests.get(f"{BASE}/targets", params={"geneSymbol": "OPRM1"}, timeout=30)
targets = r.json()
print(f"OPRM1 hits: {len(targets)}")  # 1
t = targets[0]
print(f"targetId={t['targetId']}  name='{t['name']}'  type={t['type']}  family={t['familyIds']}")
# targetId=319  name='μ receptor'  type=GPCR  family=[50]
```

## Core API

### Query 1: Resolve a Target (HGNC symbol or UniProt accession)

```python
import requests

BASE = "https://www.guidetopharmacology.org/services"

def find_target(*, geneSymbol=None, accession=None):
    """Exact-match target lookup. Pass ONE of geneSymbol or accession."""
    if geneSymbol:
        params = {"geneSymbol": geneSymbol}
    elif accession:
        params = {"accession": accession}
    else:
        raise ValueError("provide geneSymbol or accession")
    r = requests.get(f"{BASE}/targets", params=params, timeout=30)
    r.raise_for_status()
    hits = r.json()
    if not hits:
        return None
    return hits[0]

print(find_target(geneSymbol="OPRM1"))   # targetId 319 (μ receptor)
print(find_target(accession="P35372"))   # same — UniProt P35372 is OPRM1
```

```python
# Base record has only IDs and family pointers — no gene symbol, UniProt, or
# synonym text. Read sub-resources to get those.
import requests
BASE = "https://www.guidetopharmacology.org/services"
print(requests.get(f"{BASE}/targets/319", timeout=30).json().keys())
# dict_keys(['targetId','name','type','familyIds','subunitIds','complexIds'])
```

### Query 2: Target Cross-References and Synonyms

```python
import requests, pandas as pd

BASE = "https://www.guidetopharmacology.org/services"

def target_xrefs(target_id):
    """Cross-database accessions: UniProt, HGNC, ChEMBL Target, Ensembl, etc."""
    r = requests.get(f"{BASE}/targets/{target_id}/databaseLinks", timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json())

def target_synonyms(target_id):
    r = requests.get(f"{BASE}/targets/{target_id}/synonyms", timeout=30)
    r.raise_for_status()
    return [s.get("name") for s in r.json()]

df_links = target_xrefs(319)
print(df_links[["database", "accession", "species"]].head(8).to_string(index=False))
# database          accession    species
# ChEMBL Target     CHEMBL233    Human
# UniProtKB         P35372       Human
# HGNC              8156         Human
# ...
print("Synonyms:", target_synonyms(319))
```

### Query 3: Target Interactions and Affinities

```python
import requests, pandas as pd

BASE = "https://www.guidetopharmacology.org/services"

def target_interactions(target_id):
    """All ligand-target interaction records for a target.
    Each row carries ligandId, ligandName, type (Agonist/Antagonist/etc.),
    action, affinity (string), affinityParameter (pKi/pIC50/...), refs."""
    r = requests.get(f"{BASE}/targets/{target_id}/interactions", timeout=60)
    r.raise_for_status()
    rows = []
    for i in r.json():
        rows.append({
            "ligandId": i.get("ligandId"),
            "ligandName": i.get("ligandName"),
            "type": i.get("type"),                     # Agonist/Antagonist/Allosteric modulator/...
            "action": i.get("action"),
            "affinity": i.get("affinity"),             # string, may include "-" (range) or "~"
            "affinityParameter": i.get("affinityParameter"),  # pKi, pIC50, pKd, pEC50, pA2, pKB
            "species": i.get("targetSpecies"),
            "primary": i.get("primaryTarget"),
            "endogenous": i.get("endogenous"),
        })
    return pd.DataFrame(rows)

df_ints = target_interactions(319)  # μ receptor
print(f"OPRM1 interactions: {len(df_ints)}")
# Top pKi values (cast safely — affinity is a string; some are ranges like "8.5-9.0")
df_ints["pki"] = pd.to_numeric(df_ints["affinity"], errors="coerce")
print(df_ints[df_ints["affinityParameter"] == "pKi"]
      .sort_values("pki", ascending=False)
      .head(8)[["ligandName", "type", "pki"]].to_string(index=False))
```

### Query 4: Ligand Lookup and Structure

```python
import requests

BASE = "https://www.guidetopharmacology.org/services"

def ligand(ligand_id):
    """Base ligand record. Keys: ligandId, name, type, approved, approvalSource,
    abbreviation, inn, whoEssential, withdrawn, antibacterial, immuno, malaria,
    labelled, radioactive, activeDrugIds, prodrugIds, subunitIds, complexIds."""
    r = requests.get(f"{BASE}/ligands/{ligand_id}", timeout=30)
    r.raise_for_status()
    return r.json()

def ligand_structure(ligand_id):
    """Structure descriptors: smiles, inchi, inchiKey, iupacName."""
    r = requests.get(f"{BASE}/ligands/{ligand_id}/structure", timeout=30)
    r.raise_for_status()
    return r.json()

l = ligand(1627)            # morphine
s = ligand_structure(1627)
print(f"{l['name']:12s} approved={l['approved']}  type={l['type']}  inn={l.get('inn')}")
print(f"  SMILES   : {s['smiles']}")
print(f"  InChIKey : {s['inchiKey']}")
```

```python
# Ligand cross-references: PubChem CID, ChEMBL, DrugBank, CAS, ChEBI, BindingDB
import requests
BASE = "https://www.guidetopharmacology.org/services"

def ligand_xrefs(ligand_id):
    r = requests.get(f"{BASE}/ligands/{ligand_id}/databaseLinks", timeout=30)
    r.raise_for_status()
    return r.json()

xrefs = ligand_xrefs(1627)
for x in xrefs[:10]:
    print(f"  {x['database']:25s}  {x['accession']}")
```

### Query 5: Family Hierarchy

```python
import requests, pandas as pd

BASE = "https://www.guidetopharmacology.org/services"

# Correct endpoint is /targets/families (NOT /families, which is 404)
def list_families():
    r = requests.get(f"{BASE}/targets/families", timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json())

df_fams = list_families()
print(f"Total families: {len(df_fams)}")  # ~867
print(df_fams[df_fams["name"].str.contains("opioid", case=False, na=False)]
      [["familyId", "name"]].to_string(index=False))
```

### Query 6: Approved Drugs (Server-Side Alias)

```python
import requests, pandas as pd

BASE = "https://www.guidetopharmacology.org/services"

# Special: `type=Approved` is a server-side alias that returns all `approved=true`
# ligands. The `approved=true` query param is silently ignored — use type=.
def approved_ligands():
    r = requests.get(f"{BASE}/ligands", params={"type": "Approved"}, timeout=60)
    r.raise_for_status()
    return pd.DataFrame(r.json())

df = approved_ligands()
print(f"Approved ligands in GtoPdb: {len(df)}")  # ~2,197
print(df[df["name"].str.contains("morphine|fentanyl|naloxone", case=False, na=False)]
      [["ligandId", "name", "approvalSource"]].head(8).to_string(index=False))
```

## Key Concepts

### Base Records vs Sub-Resources

GtoPdb deliberately keeps base records lean. To get the data you usually want, you must call a sub-resource:

| Want | Endpoint |
|------|----------|
| Gene symbol / UniProt / HGNC / ChEMBL Target | `/targets/{id}/databaseLinks` |
| Target synonyms | `/targets/{id}/synonyms` |
| Species annotation | `/targets/{id}/databaseLinks` (each row has `species`) |
| Interactions / affinities for a target | `/targets/{id}/interactions` |
| SMILES / InChI / InChIKey | `/ligands/{id}/structure` |
| PubChem CID / ChEMBL / DrugBank / CAS / ChEBI | `/ligands/{id}/databaseLinks` |
| Ligand pharmacology summary | `/ligands/{id}/pharmacology` (long text fields) |

### `geneSymbol=` and `accession=` are Exact-Match

The `name=` filter searches across all target fields — it returns false positives (e.g. `name=beta-2` matches PLC β2 and GABA_A β2 alongside β2-adrenoceptor). Always prefer `geneSymbol=HGNC` or `accession=UniProt` for canonical lookups.

### Filters That Are Silently Ignored

- On `/interactions`: `targetId`, `ligandId`, `targetType`, `ligandType` are accepted but **silently ignored** — the endpoint returns ~280k rows for any filter. Use `/targets/{id}/interactions` or `/ligands/{id}/interactions` instead.
- On `/ligands`: `approved=true` is silently ignored. Use `type=Approved` (server alias) to filter.

### Affinity Parameters

`affinityParameter` is one of `pKi`, `pKd`, `pIC50`, `pEC50`, `pA2`, `pKB`. The `affinity` field is a **string** — it can be a number (`"9.4"`), a range (`"8.5-9.0"`), or qualified (`"~7.5"`, `">8"`). Always cast via `pd.to_numeric(..., errors="coerce")`.

## Common Workflows

### Workflow 1: Build a Target Ligand Profile

**Goal**: For a target (by HGNC), retrieve all approved drugs with affinity ≥ pKi 7.

```python
import requests, pandas as pd

BASE = "https://www.guidetopharmacology.org/services"

def target_profile(gene_symbol, min_pki=7.0):
    t = requests.get(f"{BASE}/targets",
                     params={"geneSymbol": gene_symbol}, timeout=30).json()
    if not t:
        return None
    tid = t[0]["targetId"]
    ints = requests.get(f"{BASE}/targets/{tid}/interactions", timeout=60).json()
    rows = []
    for i in ints:
        # Skip rows without numeric pKi
        if i.get("affinityParameter") != "pKi":
            continue
        try:
            pki = float(i.get("affinity"))
        except (TypeError, ValueError):
            continue
        if pki < min_pki:
            continue
        # Check approval via the ligand base record
        lig = requests.get(f"{BASE}/ligands/{i['ligandId']}", timeout=30).json()
        rows.append({
            "ligand": i["ligandName"],
            "ligandId": i["ligandId"],
            "type": i.get("type"),
            "pki": pki,
            "approved": lig.get("approved"),
            "withdrawn": lig.get("withdrawn"),
        })
    return pd.DataFrame(rows).sort_values("pki", ascending=False)

df = target_profile("OPRM1", min_pki=8.0)
print(df.head(10).to_string(index=False))
df.to_csv("OPRM1_profile.csv", index=False)
```

### Workflow 2: Ligand → Targets

**Goal**: List the off-targets of a ligand with their affinities.

```python
import requests, pandas as pd

BASE = "https://www.guidetopharmacology.org/services"

def ligand_targets(ligand_id):
    r = requests.get(f"{BASE}/ligands/{ligand_id}/interactions", timeout=60)
    r.raise_for_status()
    rows = []
    for i in r.json():
        rows.append({
            "targetId": i.get("targetId"),
            "targetName": i.get("targetName"),
            "type": i.get("type"),
            "affinity": pd.to_numeric(i.get("affinity"), errors="coerce"),
            "affinityParameter": i.get("affinityParameter"),
            "species": i.get("targetSpecies"),
            "primary": i.get("primaryTarget"),
        })
    return pd.DataFrame(rows).sort_values("affinity", ascending=False)

df = ligand_targets(1627)  # morphine
print(f"Morphine interactions across all targets: {len(df)}")
print(df.head(8).to_string(index=False))
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `geneSymbol` | `/targets` | — | HGNC symbol | **Exact-match** target lookup |
| `accession` | `/targets` | — | UniProt accession | **Exact-match** target lookup |
| `name` | `/targets`, `/ligands` | — | any string | Fuzzy — matches across all fields; can return wrong record |
| `type` | `/ligands` | — | `Synthetic organic`, `Peptide`, `Natural product`, `Metabolite`, `Antibody`, `Nucleic acid`, `Inorganic`, `Approved` (alias) | Filter ligand list by type or approval |
| (path) `{targetId}` | `/targets/{id}/{rel}` | required | integer | Target sub-resource lookup (databaseLinks/synonyms/interactions/…) |
| (path) `{ligandId}` | `/ligands/{id}/{rel}` | required | integer | Ligand sub-resource lookup (structure/databaseLinks/interactions/pharmacology) |
| (path) `families` | `/targets/families` | — | — | List of 867 IUPHAR families |

## Best Practices

1. **Use `geneSymbol=`/`accession=` for canonical lookups**, never `name=` — fuzzy `name=` matches across all fields and silently returns the wrong target.
2. **Read sub-resources for everything beyond IDs.** Base `/targets/{id}` and `/ligands/{id}` records lack gene symbols, UniProt, SMILES, ChEMBL, etc. — they live under `/databaseLinks`, `/synonyms`, `/structure`.
3. **Filter interactions via `/targets/{id}/interactions` or `/ligands/{id}/interactions`** — never `/interactions?targetId=…`, which silently ignores the filter.
4. **Use `type=Approved` server alias** to fetch approved drugs; `approved=true` query param is ignored.
5. **Always cast `affinity` numerically with `errors="coerce"`** — it's a string that can be ranges, qualified, or missing.
6. **Family endpoint is `/targets/families`** — not `/families` (which 404s).

## Common Recipes

### Recipe: Resolve Gene Symbol → UniProt via GtoPdb

```python
import requests
BASE = "https://www.guidetopharmacology.org/services"

def gene_to_uniprot(symbol):
    t = requests.get(f"{BASE}/targets", params={"geneSymbol": symbol}, timeout=30).json()
    if not t:
        return None
    links = requests.get(f"{BASE}/targets/{t[0]['targetId']}/databaseLinks", timeout=30).json()
    for x in links:
        if x.get("database") == "UniProtKB" and x.get("species") == "Human":
            return x["accession"]
    return None

print(gene_to_uniprot("OPRM1"))   # P35372
print(gene_to_uniprot("ADRB2"))   # P07550
```

### Recipe: Approved Drugs in a Receptor Family

```python
import requests, pandas as pd
BASE = "https://www.guidetopharmacology.org/services"

def family_targets(family_id):
    fams = requests.get(f"{BASE}/targets/families", timeout=30).json()
    return next((f.get("targetIds", []) for f in fams if f["familyId"] == family_id), [])

def approved_drugs_for_family(family_id):
    rows = []
    for tid in family_targets(family_id):
        ints = requests.get(f"{BASE}/targets/{tid}/interactions", timeout=60).json()
        for i in ints:
            lig = requests.get(f"{BASE}/ligands/{i['ligandId']}", timeout=30).json()
            if not lig.get("approved"):
                continue
            rows.append({"targetId": tid, "drug": i["ligandName"],
                         "type": i.get("type"),
                         "affinity": pd.to_numeric(i.get("affinity"), errors="coerce"),
                         "param": i.get("affinityParameter")})
    return pd.DataFrame(rows).drop_duplicates(subset=["targetId", "drug"])

# family 50 = opioid receptors (example)
df = approved_drugs_for_family(50)
print(df.head(10).to_string(index=False))
```

### Recipe: SMILES Lookup for a List of GtoPdb Ligand IDs

```python
import requests, pandas as pd, time
BASE = "https://www.guidetopharmacology.org/services"

def smiles_table(ligand_ids):
    rows = []
    for lid in ligand_ids:
        s = requests.get(f"{BASE}/ligands/{lid}/structure", timeout=30).json()
        rows.append({"ligandId": lid, "smiles": s.get("smiles"),
                     "inchiKey": s.get("inchiKey")})
        time.sleep(0.2)
    return pd.DataFrame(rows)

print(smiles_table([1627, 1638, 5466]).to_string(index=False))  # morphine, naloxone, fentanyl
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `name=...` returns wrong target | `name=` matches across all fields | Use `geneSymbol=` or `accession=` for canonical lookups |
| `target["hgncSymbol"]` / `target["uniprotId"]` `KeyError` | Base record only has IDs | Call `/targets/{id}/databaseLinks` |
| `ligand["smiles"]` / `inchikey` / `pubchemCid` `KeyError` | Base ligand record has flags only | Call `/ligands/{id}/structure` and `/ligands/{id}/databaseLinks` |
| `/interactions?targetId=...` returns ~280k rows | Filter silently ignored | Use `/targets/{id}/interactions` |
| `?approved=true` returns the full ligand list | Param silently ignored | Use `?type=Approved` (server alias) |
| `/families` → HTTP 404 | Wrong path | Use `/targets/families` |
| `ValueError: could not convert string to float` on `affinity` | Field is a string that can be a range or qualifier | `pd.to_numeric(s, errors="coerce")`; or parse ranges manually |
| Filter by `ligandType="Approved"` on interactions returns empty | `ligandType` field does not exist on interactions | Filter via the ligand record's `approved` flag instead |

## Related Skills

- `chembl-database-bioactivity` — Larger-scale bioactivity (2.4M+ compounds) for the same target classes
- `pubchem-compound-search` — Compound-centric chemoinformatics; cross-reference via PubChem CID from `/ligands/{id}/databaseLinks`
- `dailymed-database` — FDA-approved label text for marketed drugs (regulatory complement)
- `uniprot-protein-database` — Resolve the UniProt accession that GtoPdb cross-references

## References

- [Guide to Pharmacology home](https://www.guidetopharmacology.org/)
- [Web services API reference](https://www.guidetopharmacology.org/webServices.jsp)
- [Nomenclature & Curation](https://www.guidetopharmacology.org/helpPage.jsp)
- Harding SD et al. "The IUPHAR/BPS Guide to PHARMACOLOGY in 2024." *Nucleic Acids Research* 52(D1): D1438–D1449 (2024). https://doi.org/10.1093/nar/gkad944
