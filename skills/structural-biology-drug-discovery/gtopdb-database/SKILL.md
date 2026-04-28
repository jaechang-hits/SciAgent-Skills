---
name: "gtopdb-database"
description: "Query IUPHAR/BPS Guide to Pharmacology (GtoPdb) REST API for receptor-ligand interactions and affinity (pKi/pIC50/pEC50). Get ligand classes (drugs, biologics, natural products), target families (GPCRs, ion channels, nuclear receptors, kinases), selectivity profiles."
license: "ODbL-1.0"
---

# GtoPdb Database

## Overview

The Guide to Pharmacology (GtoPdb), maintained by IUPHAR/BPS, is the curated reference database for pharmacological targets and their ligands. It covers 3,000+ targets (GPCRs, ion channels, nuclear receptors, catalytic receptors, transporters, and enzymes) with 12,000+ ligands and 90,000+ interaction records annotated with quantitative affinity values (Ki, IC50, EC50, Kd). Access is via a free REST API at `https://www.guidetopharmacology.org/services/` — no authentication required.

## When to Use

- Retrieving curated receptor-ligand interaction data with quantitative affinity (pKi, pIC50, pEC50) for GPCR, ion channel, or kinase targets
- Finding all approved drugs, clinical candidates, or research ligands that act on a specific receptor family
- Getting the pharmacological target classification for a receptor (family, type, HGNC symbol, UniProt ID)
- Building selectivity profiles for a ligand across all annotated targets in GtoPdb
- Identifying receptor families (GPCR subfamilies, ion channel families) and browsing their member targets
- Retrieving quantitative agonist/antagonist/allosteric modulator affinity data for lead optimization
- Comparing endogenous ligand potency with drug affinity at the same receptor
- For large-scale ADMET/bioactivity data use `chembl-database-bioactivity`; GtoPdb is the authoritative source for receptor pharmacology annotation
- For structural data (binding poses, crystal structures) use `pdb-database`; GtoPdb provides affinity numbers, not 3D structures

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: GtoPdb target IDs, ligand IDs, or receptor family names as starting points; HGNC gene symbols or UniProt IDs accepted for target lookup
- **Environment**: internet connection; no API key required
- **Rate limits**: ~50 requests/minute; no hard enforcement but use `time.sleep(0.2)` in batch loops for polite access

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def gtopdb_get(endpoint: str, params: dict = None) -> list | dict:
    """GET request to GtoPdb API; raise on HTTP errors."""
    r = requests.get(f"{GTOPDB_API}/{endpoint}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()

# Find the beta-2 adrenoceptor target
targets = gtopdb_get("targets", params={"name": "beta-2 adrenoceptor"})
if targets:
    t = targets[0]
    tid = t["targetId"]
    print(f"Target: {t['name']} (GtoPdb ID: {tid})")
    print(f"Family: {t.get('familyIds', [])}")

# Get its approved drug interactions
interactions = gtopdb_get(f"targets/{tid}/interactions")
approved = [i for i in interactions if i.get("ligandType") == "Approved"]
print(f"Approved drugs acting on beta-2 AR: {len(approved)}")
for ia in approved[:3]:
    affinity = ia.get("affinityParameter", ""), ia.get("affinity", "")
    print(f"  {ia['ligandName']:25s}  {affinity[0]}={affinity[1]}")
```

## Core API

### Query 1: Target Search and Details

Search targets by name, HGNC symbol, UniProt accession, or target family type. Returns target metadata including GtoPdb target ID, gene symbol, family assignment, and species.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def search_targets(name: str = None, hgnc_symbol: str = None,
                   target_type: str = None) -> pd.DataFrame:
    """Search GtoPdb targets.

    Args:
        name: Partial target name (case-insensitive substring match)
        hgnc_symbol: Exact HGNC gene symbol (e.g., 'ADRB2')
        target_type: One of 'GPCR', 'Ion channel', 'Nuclear receptor',
                     'Catalytic receptor', 'Transporter', 'Enzyme', 'Other'
    """
    params = {}
    if name:
        params["name"] = name
    if hgnc_symbol:
        params["geneSymbol"] = hgnc_symbol
    if target_type:
        params["type"] = target_type
    r = requests.get(f"{GTOPDB_API}/targets", params=params, timeout=20)
    r.raise_for_status()
    targets = r.json()
    if not targets:
        return pd.DataFrame()
    rows = []
    for t in targets:
        rows.append({
            "target_id": t.get("targetId"),
            "name": t.get("name"),
            "type": t.get("type"),
            "hgnc_symbol": t.get("hgncSymbol"),
            "uniprot_id": t.get("uniprotId"),
            "species": t.get("species", "Human"),
        })
    return pd.DataFrame(rows)

# Search for dopamine receptors
df = search_targets(name="dopamine receptor")
print(f"Found {len(df)} dopamine receptor targets:")
print(df[["target_id", "name", "type", "hgnc_symbol"]].to_string(index=False))
```

```python
# Get full details for a specific target
def get_target_details(target_id: int) -> dict:
    """Retrieve full target record by GtoPdb target ID."""
    r = requests.get(f"{GTOPDB_API}/targets/{target_id}", timeout=15)
    r.raise_for_status()
    return r.json()

# Mu-opioid receptor (OPRM1)
target = get_target_details(319)
print(f"Target: {target['name']}")
print(f"Type: {target.get('type')}")
print(f"HGNC symbol: {target.get('hgncSymbol')}")
print(f"UniProt: {target.get('uniprotId')}")
print(f"Family IDs: {target.get('familyIds', [])}")
print(f"Synonyms: {', '.join(target.get('synonyms', [])[:4])}")
```

### Query 2: Target Interactions — Ligand Affinity Data

Retrieve all ligand-target interactions for a given target, including quantitative affinity values, ligand type classification, and experimental context.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def get_target_interactions(target_id: int,
                            species: str = "Human") -> pd.DataFrame:
    """Get all interactions for a target with affinity data.

    Returns a DataFrame with ligand name, type, affinity parameters, and action type.
    """
    r = requests.get(f"{GTOPDB_API}/targets/{target_id}/interactions",
                     params={"species": species}, timeout=20)
    r.raise_for_status()
    interactions = r.json()
    rows = []
    for ia in interactions:
        rows.append({
            "ligand_id": ia.get("ligandId"),
            "ligand_name": ia.get("ligandName"),
            "ligand_type": ia.get("ligandType"),
            "action": ia.get("action"),               # agonist, antagonist, etc.
            "action_comment": ia.get("actionComment"),
            "affinity_param": ia.get("affinityParameter"),  # pKi, pIC50, pEC50
            "affinity": ia.get("affinity"),           # numeric value
            "affinity_high": ia.get("affinityHigh"),
            "affinity_low": ia.get("affinityLow"),
            "endogenous": ia.get("endogenous", False),
            "primary_target": ia.get("primaryTarget", False),
            "assay_type": ia.get("assayType"),
            "pubmed_id": ia.get("refs", [{}])[0].get("pmid") if ia.get("refs") else None,
        })
    return pd.DataFrame(rows)

# Serotonin 2A receptor (5-HT2A, target_id=11)
df = get_target_interactions(11)
print(f"5-HT2A receptor interactions: {len(df)} total")
print(f"\nAction type breakdown:")
print(df["action"].value_counts().head(8))
print(f"\nLigand type breakdown:")
print(df["ligand_type"].value_counts().head(6))

# Show top antagonists by affinity
antagonists = df[df["action"] == "Antagonist"].dropna(subset=["affinity"])
antagonists = antagonists.sort_values("affinity", ascending=False)
print(f"\nTop 5-HT2A antagonists (by pKi/pIC50):")
print(antagonists[["ligand_name", "ligand_type", "affinity_param", "affinity"]].head(8).to_string(index=False))
```

### Query 3: Ligand Search and Details

Search for ligands by name, approved drug status, or ligand type. Retrieve full ligand records including structure IDs (InChIKey, SMILES), clinical status, and cross-references.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def search_ligands(name: str = None, approved_drug: bool = None,
                   ligand_type: str = None) -> pd.DataFrame:
    """Search GtoPdb ligands.

    Args:
        name: Ligand name substring (case-insensitive)
        approved_drug: If True, filter to approved drugs only
        ligand_type: One of 'Approved', 'Labelled', 'Peptide', 'Antibody',
                     'Endogenous', 'Inorganic', 'Metabolite', 'Natural product',
                     'Synthetic organic'
    """
    params = {}
    if name:
        params["name"] = name
    if approved_drug is not None:
        params["approvedDrug"] = str(approved_drug).lower()
    if ligand_type:
        params["type"] = ligand_type
    r = requests.get(f"{GTOPDB_API}/ligands", params=params, timeout=20)
    r.raise_for_status()
    ligands = r.json()
    rows = []
    for lig in ligands:
        rows.append({
            "ligand_id": lig.get("ligandId"),
            "name": lig.get("name"),
            "type": lig.get("type"),
            "approved": lig.get("approvedDrug", False),
            "inchikey": lig.get("inchikey"),
            "smiles": lig.get("smiles", "")[:60] if lig.get("smiles") else "",
            "pubchem_cid": lig.get("pubchemCid"),
            "chembl_id": lig.get("chemblId"),
        })
    return pd.DataFrame(rows)

# Search for beta-blocker drugs
df = search_ligands(name="propranolol")
print(df[["ligand_id", "name", "type", "approved", "inchikey", "chembl_id"]].to_string(index=False))
```

```python
# Get full details for a specific ligand
def get_ligand_details(ligand_id: int) -> dict:
    """Retrieve full ligand record by GtoPdb ligand ID."""
    r = requests.get(f"{GTOPDB_API}/ligands/{ligand_id}", timeout=15)
    r.raise_for_status()
    return r.json()

# Morphine (ligand_id=1627)
lig = get_ligand_details(1627)
print(f"Name: {lig['name']}")
print(f"Type: {lig.get('type')}")
print(f"Approved drug: {lig.get('approvedDrug')}")
print(f"InChIKey: {lig.get('inchikey')}")
print(f"SMILES: {lig.get('smiles', 'N/A')[:80]}")
print(f"ChEMBL ID: {lig.get('chemblId')}")
print(f"PubChem CID: {lig.get('pubchemCid')}")
```

### Query 4: Ligand Interactions — Target Selectivity Profile

Given a ligand, retrieve all targets it acts on with affinity values. Use this to build a selectivity profile or identify off-target effects.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def get_ligand_interactions(ligand_id: int,
                            species: str = "Human") -> pd.DataFrame:
    """Get all target interactions for a ligand.

    Returns a DataFrame with target name, type, action, and affinity.
    """
    r = requests.get(f"{GTOPDB_API}/ligands/{ligand_id}/interactions",
                     params={"species": species}, timeout=20)
    r.raise_for_status()
    interactions = r.json()
    rows = []
    for ia in interactions:
        rows.append({
            "target_id": ia.get("targetId"),
            "target_name": ia.get("targetName"),
            "target_type": ia.get("targetType"),
            "action": ia.get("action"),
            "affinity_param": ia.get("affinityParameter"),
            "affinity": ia.get("affinity"),
            "endogenous": ia.get("endogenous", False),
            "primary_target": ia.get("primaryTarget", False),
        })
    return pd.DataFrame(rows)

# Clozapine selectivity profile (ligand_id=31 in GtoPdb)
df = get_ligand_interactions(31)
print(f"Clozapine interactions: {len(df)} targets")
# Filter to records with affinity data
has_affinity = df.dropna(subset=["affinity"]).sort_values("affinity", ascending=False)
print(f"\nTargets with quantitative affinity (n={len(has_affinity)}):")
print(has_affinity[["target_name", "target_type", "action",
                     "affinity_param", "affinity"]].head(10).to_string(index=False))
```

### Query 5: Browse Target Families

Retrieve the receptor family hierarchy: superfamilies → families → individual targets. Use this to enumerate all GPCRs, ion channels, or nuclear receptors.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def get_families(family_id: int = None) -> list:
    """Get all families or a specific family by ID."""
    endpoint = f"families/{family_id}" if family_id else "families"
    r = requests.get(f"{GTOPDB_API}/{endpoint}", timeout=20)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else [data]

def get_family_targets(family_id: int) -> pd.DataFrame:
    """Get all targets in a given receptor family."""
    r = requests.get(f"{GTOPDB_API}/targets",
                     params={"familyId": family_id}, timeout=20)
    r.raise_for_status()
    targets = r.json()
    rows = [{"target_id": t.get("targetId"), "name": t.get("name"),
             "type": t.get("type"), "hgnc_symbol": t.get("hgncSymbol"),
             "uniprot_id": t.get("uniprotId")} for t in targets]
    return pd.DataFrame(rows)

# Browse top-level families
families = get_families()
print(f"Total GtoPdb families: {len(families)}")
for fam in families[:8]:
    print(f"  [{fam['familyId']}] {fam['name']}")

# Get all targets in a specific GPCR subfamily
# Family ID 694 = Adenosine receptors
adenosine_targets = get_family_targets(694)
print(f"\nAdenosine receptor targets: {len(adenosine_targets)}")
print(adenosine_targets[["target_id", "name", "hgnc_symbol"]].to_string(index=False))
```

### Query 6: Global Interaction Search

Search all interactions by affinity type, action, or ligand type to extract a curated dataset for pharmacological analysis.

```python
import requests, pandas as pd, time

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def search_interactions(action: str = None,
                        target_type: str = None,
                        affinity_param: str = None,
                        species: str = "Human") -> pd.DataFrame:
    """Search all GtoPdb interactions with optional filters.

    Args:
        action: 'Agonist', 'Antagonist', 'Inhibitor', 'Allosteric modulator', etc.
        target_type: 'GPCR', 'Ion channel', 'Nuclear receptor', etc.
        affinity_param: 'pKi', 'pIC50', 'pEC50', 'pKd'
        species: 'Human' (default), 'Mouse', 'Rat'
    """
    params = {"species": species}
    if action:
        params["action"] = action
    if target_type:
        params["targetType"] = target_type
    if affinity_param:
        params["affinityParameter"] = affinity_param

    r = requests.get(f"{GTOPDB_API}/interactions", params=params, timeout=60)
    r.raise_for_status()
    interactions = r.json()

    rows = []
    for ia in interactions:
        rows.append({
            "target_id": ia.get("targetId"),
            "target_name": ia.get("targetName"),
            "target_type": ia.get("targetType"),
            "ligand_id": ia.get("ligandId"),
            "ligand_name": ia.get("ligandName"),
            "ligand_type": ia.get("ligandType"),
            "action": ia.get("action"),
            "affinity_param": ia.get("affinityParameter"),
            "affinity": ia.get("affinity"),
            "endogenous": ia.get("endogenous", False),
            "approved_drug": ia.get("approvedDrug", False),
        })
    return pd.DataFrame(rows)

# Get all GPCR antagonist interactions with pKi values
df = search_interactions(action="Antagonist", target_type="GPCR", affinity_param="pKi")
print(f"GPCR antagonists with pKi data: {len(df)} interactions")
df_clean = df.dropna(subset=["affinity"])
print(f"With numeric affinity: {len(df_clean)}")
print(f"\npKi distribution:")
print(df_clean["affinity"].describe().round(2))
print(f"\nTop 5 by pKi:")
print(df_clean.nlargest(5, "affinity")[["ligand_name", "target_name", "affinity"]].to_string(index=False))
```

## Key Concepts

### GtoPdb Pharmacological Hierarchy

GtoPdb organizes targets into a two-level hierarchy: **target types** (GPCR, Ion channel, Nuclear receptor, Catalytic receptor, Transporter, Enzyme, Other protein) → **families** (e.g., GPCR > Aminergic receptors > Adrenoceptors > beta-Adrenoceptors) → **individual targets** (e.g., beta-2 adrenoceptor). The `familyId` parameter lets you enumerate all members of a receptor family efficiently.

### Affinity Parameters

| Parameter | Definition | Typical range | Notes |
|-----------|-----------|--------------|-------|
| `pKi` | -log₁₀(Ki) equilibrium dissociation constant | 4–12 | Direct binding; higher = tighter |
| `pIC50` | -log₁₀(IC50) half-maximal inhibitory concentration | 4–12 | Functional inhibition |
| `pEC50` | -log₁₀(EC50) half-maximal effective concentration | 4–12 | Functional activation |
| `pKd` | -log₁₀(Kd) dissociation constant | 4–12 | Equilibrium binding (often from SPR/ITC) |
| `%` | Percent effect at fixed concentration | 0–100 | Qualitative; no affinity constant |

A pKi of 9 = Ki of 1 nM (high affinity); pKi of 6 = Ki of 1 µM (moderate). GtoPdb requires at least two independent measurements to include a value.

### Ligand Type Classifications

| Type | Description |
|------|-------------|
| `Approved` | Regulatory-approved drug (FDA, EMA) |
| `Synthetic organic` | Research tool compound |
| `Natural product` | Plant/animal/microbial origin |
| `Endogenous` | Endogenous ligand (neurotransmitter, hormone) |
| `Peptide` | Peptide/peptidomimetic |
| `Antibody` | Therapeutic antibody |
| `Inorganic` | Metal ions, inorganic compounds |
| `Metabolite` | Metabolic product |

## Common Workflows

### Workflow 1: Build a Target Pharmacology Table for a Receptor

**Goal**: Retrieve all interactions for a GPCR, separate by action type, and export a structured table with quantitative affinities for SAR analysis.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def get_pharmacology_table(target_id: int, species: str = "Human") -> pd.DataFrame:
    """Full pharmacology table for a target: agonists, antagonists, allosteric modulators."""
    r = requests.get(f"{GTOPDB_API}/targets/{target_id}/interactions",
                     params={"species": species}, timeout=30)
    r.raise_for_status()
    rows = []
    for ia in r.json():
        rows.append({
            "ligand_id": ia.get("ligandId"),
            "ligand_name": ia.get("ligandName"),
            "ligand_type": ia.get("ligandType"),
            "action": ia.get("action"),
            "action_comment": ia.get("actionComment"),
            "affinity_param": ia.get("affinityParameter"),
            "affinity": ia.get("affinity"),
            "affinity_high": ia.get("affinityHigh"),
            "affinity_low": ia.get("affinityLow"),
            "endogenous": ia.get("endogenous", False),
            "approved": ia.get("approvedDrug", False),
            "pubmed_id": ia.get("refs", [{}])[0].get("pmid") if ia.get("refs") else None,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["affinity"] = pd.to_numeric(df["affinity"], errors="coerce")
    return df

# Adenosine A2A receptor (target_id=3)
df = get_pharmacology_table(3)
print(f"Adenosine A2A receptor — {len(df)} total interactions")

# Pivot by action type
for action in ["Agonist", "Antagonist", "Allosteric modulator"]:
    subset = df[df["action"] == action].dropna(subset=["affinity"])
    subset = subset.sort_values("affinity", ascending=False)
    print(f"\n{action}s with affinity data (n={len(subset)}):")
    cols = ["ligand_name", "ligand_type", "affinity_param", "affinity", "approved"]
    print(subset[cols].head(5).to_string(index=False))

df.to_csv("A2A_pharmacology.csv", index=False)
print(f"\nSaved A2A_pharmacology.csv ({len(df)} interactions)")
```

### Workflow 2: Multi-Target Selectivity Heatmap

**Goal**: For a set of ligands, query their affinity across a receptor panel and visualize as a heatmap.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def get_ligand_selectivity(ligand_id: int, species: str = "Human") -> dict:
    """Return {target_name: affinity} for a ligand (best affinity per target)."""
    r = requests.get(f"{GTOPDB_API}/ligands/{ligand_id}/interactions",
                     params={"species": species}, timeout=20)
    r.raise_for_status()
    targets = {}
    for ia in r.json():
        name = ia.get("targetName", "")
        aff = ia.get("affinity")
        if name and aff is not None:
            try:
                val = float(aff)
                if name not in targets or val > targets[name]:
                    targets[name] = val
            except (ValueError, TypeError):
                pass
    return targets

# Typical antipsychotics: clozapine, haloperidol, olanzapine
# Use small sample GtoPdb ligand IDs for illustration
ligands = {
    "clozapine":   31,   # GtoPdb ligand ID
    "haloperidol": 78,
    "olanzapine":  4,
}

all_data = {}
for name, lid in ligands.items():
    all_data[name] = get_ligand_selectivity(lid)
    time.sleep(0.2)

# Build matrix: rows=ligands, columns=shared targets
all_targets = sorted(set().union(*all_data.values()))
matrix = pd.DataFrame(index=ligands.keys(), columns=all_targets, dtype=float)
for lig, targets in all_data.items():
    for tgt, aff in targets.items():
        matrix.loc[lig, tgt] = aff

# Keep only targets with data for at least 2 ligands
matrix = matrix.dropna(axis=1, thresh=2)
print(f"Selectivity matrix: {matrix.shape[0]} ligands × {matrix.shape[1]} targets")

# Plot heatmap
fig, ax = plt.subplots(figsize=(max(10, matrix.shape[1] * 0.5), 4))
im = ax.imshow(matrix.values.astype(float), aspect="auto", cmap="YlOrRd", vmin=5, vmax=10)
ax.set_xticks(range(matrix.shape[1]))
ax.set_xticklabels(matrix.columns, rotation=45, ha="right", fontsize=7)
ax.set_yticks(range(matrix.shape[0]))
ax.set_yticklabels(matrix.index)
plt.colorbar(im, ax=ax, label="pAffinity (pKi / pIC50 / pEC50)")
ax.set_title("GtoPdb Antipsychotic Selectivity Profile")
plt.tight_layout()
plt.savefig("antipsychotic_selectivity.png", dpi=150, bbox_inches="tight")
print("Saved antipsychotic_selectivity.png")
```

### Workflow 3: Approved Drug Target Coverage for a Family

**Goal**: Enumerate all members of a receptor family, count approved drugs per target, and rank by drug coverage.

```python
import requests, time, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def approved_drug_coverage(family_id: int, species: str = "Human") -> pd.DataFrame:
    """Return approved drug counts and ligands for each target in a receptor family.

    Args:
        family_id: GtoPdb family ID (e.g., 694 for Adenosine receptors)
        species: 'Human', 'Mouse', 'Rat'
    """
    # Get all targets in the family
    r = requests.get(f"{GTOPDB_API}/targets",
                     params={"familyId": family_id}, timeout=20)
    r.raise_for_status()
    targets = r.json()

    rows = []
    for t in targets:
        tid = t["targetId"]
        time.sleep(0.2)
        r2 = requests.get(f"{GTOPDB_API}/targets/{tid}/interactions",
                          params={"species": species}, timeout=20)
        if not r2.ok:
            continue
        interactions = r2.json()
        approved = [ia for ia in interactions if ia.get("approvedDrug")]
        drug_names = list({ia["ligandName"] for ia in approved})[:5]
        rows.append({
            "target_id": tid,
            "target_name": t.get("name"),
            "hgnc_symbol": t.get("hgncSymbol"),
            "n_interactions": len(interactions),
            "n_approved_drugs": len(approved),
            "approved_drugs": ", ".join(drug_names),
        })

    df = pd.DataFrame(rows).sort_values("n_approved_drugs", ascending=False)
    return df

# Opioid receptor family (family_id varies; search for it)
r = requests.get(f"{GTOPDB_API}/families", timeout=15)
families = r.json()
opioid = next((f for f in families if "opioid" in f.get("name", "").lower()), None)
if opioid:
    print(f"Opioid family: {opioid['name']} (ID={opioid['familyId']})")
    df = approved_drug_coverage(opioid["familyId"])
    print(df[["target_name", "n_approved_drugs", "approved_drugs"]].to_string(index=False))
    df.to_csv("opioid_approved_drugs.csv", index=False)
    print(f"\nSaved opioid_approved_drugs.csv")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `name` | `GET /targets`, `GET /ligands` | — | Partial string (case-insensitive) | Substring match on target or ligand name |
| `type` | `GET /targets` | — | `'GPCR'`, `'Ion channel'`, `'Nuclear receptor'`, `'Catalytic receptor'`, `'Transporter'`, `'Enzyme'`, `'Other'` | Filter targets by receptor class |
| `familyId` | `GET /targets` | — | Integer family ID | Return all targets belonging to a receptor family |
| `geneSymbol` | `GET /targets` | — | HGNC symbol string (e.g., `'ADRB2'`) | Exact match on HGNC gene symbol |
| `species` | `GET /targets/{id}/interactions`, `GET /ligands/{id}/interactions` | `'Human'` | `'Human'`, `'Mouse'`, `'Rat'` | Filter interactions to a specific species |
| `approvedDrug` | `GET /ligands` | — | `'true'`, `'false'` | Filter ligands to FDA/EMA approved drugs |
| `action` | `GET /interactions` | — | `'Agonist'`, `'Antagonist'`, `'Inhibitor'`, `'Allosteric modulator'`, `'Activator'`, `'Blocker'`, `'Opener'` | Filter by pharmacological action type |
| `affinityParameter` | `GET /interactions` | — | `'pKi'`, `'pIC50'`, `'pEC50'`, `'pKd'` | Return only interactions with this affinity type |
| `targetType` | `GET /interactions` | — | Same as `type` for targets | Filter interactions by target class |

## Best Practices

1. **Resolve target IDs before batch queries**: GtoPdb uses integer target IDs. Always start with a `GET /targets?name=...` search to get the correct `targetId` rather than hard-coding IDs across analyses, as family assignments and IDs can change between database releases.

2. **Filter interactions by species for quantitative analyses**: The same target may have interactions from multiple species. For drug discovery (human pharmacology), always pass `species=Human`. Cross-species data is useful for selectivity validation but should be flagged separately.

3. **Use `dropna(subset=["affinity"])` before ranking**: Many interaction records have qualitative action annotations (e.g., "Agonist" without a Ki value). Always filter to records with numeric affinity before computing potency rankings.

4. **Check `endogenous` flag to separate endogenous ligands from drugs**: Endogenous peptides, neurotransmitters, and lipids will appear in interaction tables. Use `df[~df["endogenous"]]` to focus on drug/tool compound interactions in SAR analyses.

5. **Cross-reference with ChEMBL via `chembl_id`**: Ligand records include `chemblId`. Use this to enrich GtoPdb affinity data with larger bioactivity datasets from ChEMBL using `chembl-database-bioactivity`.

   ```python
   lig = get_ligand_details(ligand_id)
   chembl_id = lig.get("chemblId")  # e.g., 'CHEMBL192'
   # Then query ChEMBL for full bioactivity profile
   ```

## Common Recipes

### Recipe: Get All Approved Drugs for a Target by HGNC Symbol

When to use: Quick lookup of marketed drugs targeting a specific receptor given only the gene name.

```python
import requests

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def approved_drugs_for_gene(hgnc_symbol: str, species: str = "Human") -> list[dict]:
    """Return approved drugs for a target identified by HGNC gene symbol."""
    # Step 1: find the target
    r = requests.get(f"{GTOPDB_API}/targets",
                     params={"geneSymbol": hgnc_symbol}, timeout=15)
    r.raise_for_status()
    targets = r.json()
    human_targets = [t for t in targets if t.get("species", "Human") == "Human"]
    if not human_targets:
        print(f"No human target found for {hgnc_symbol}")
        return []

    target_id = human_targets[0]["targetId"]
    target_name = human_targets[0]["name"]

    # Step 2: get interactions
    r2 = requests.get(f"{GTOPDB_API}/targets/{target_id}/interactions",
                      params={"species": species}, timeout=20)
    r2.raise_for_status()

    approved = [
        {"ligand_name": ia["ligandName"], "action": ia.get("action"),
         "affinity_param": ia.get("affinityParameter"), "affinity": ia.get("affinity")}
        for ia in r2.json() if ia.get("approvedDrug")
    ]
    print(f"{target_name} (ID={target_id}): {len(approved)} approved drugs")
    return approved

drugs = approved_drugs_for_gene("DRD2")  # Dopamine D2 receptor
for d in drugs[:6]:
    aff = f"{d['affinity_param']}={d['affinity']}" if d['affinity'] else "no affinity"
    print(f"  {d['ligand_name']:20s}  {d['action']:15s}  {aff}")
```

### Recipe: Compare Endogenous vs Drug Affinity at a Receptor

When to use: Assess how drug potency compares to the endogenous agonist at a given receptor.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

def compare_endogenous_vs_drugs(target_id: int, species: str = "Human") -> pd.DataFrame:
    """Compare endogenous ligand affinities to approved drug affinities."""
    r = requests.get(f"{GTOPDB_API}/targets/{target_id}/interactions",
                     params={"species": species}, timeout=20)
    r.raise_for_status()
    rows = []
    for ia in r.json():
        aff = ia.get("affinity")
        if aff is None:
            continue
        try:
            rows.append({
                "ligand": ia["ligandName"],
                "category": "Endogenous" if ia.get("endogenous") else
                            ("Approved drug" if ia.get("approvedDrug") else "Research compound"),
                "action": ia.get("action"),
                "affinity_param": ia.get("affinityParameter"),
                "affinity": float(aff),
            })
        except (ValueError, TypeError):
            pass
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["category", "affinity"], ascending=[True, False])

# Beta-2 adrenoceptor (target_id=24)
df = compare_endogenous_vs_drugs(24)
print("Beta-2 adrenoceptor — Endogenous vs approved drug affinities:")
for cat, group in df.groupby("category"):
    print(f"\n{cat} (n={len(group)}):")
    print(group[["ligand", "action", "affinity_param", "affinity"]].head(5).to_string(index=False))
```

### Recipe: Export All GPCR-Approved Drug Interactions to CSV

When to use: Build a comprehensive dataset of all approved GPCR drugs with quantitative affinity for pharmacological analysis.

```python
import requests, pandas as pd

GTOPDB_API = "https://www.guidetopharmacology.org/services"

# Get all interactions filtered to GPCR targets and approved drugs
r = requests.get(f"{GTOPDB_API}/interactions",
                 params={"targetType": "GPCR", "species": "Human"}, timeout=60)
r.raise_for_status()
interactions = r.json()

rows = []
for ia in interactions:
    if not ia.get("approvedDrug"):
        continue
    rows.append({
        "target_id": ia.get("targetId"),
        "target_name": ia.get("targetName"),
        "ligand_id": ia.get("ligandId"),
        "ligand_name": ia.get("ligandName"),
        "action": ia.get("action"),
        "affinity_param": ia.get("affinityParameter"),
        "affinity": ia.get("affinity"),
        "endogenous": ia.get("endogenous", False),
    })

df = pd.DataFrame(rows)
df_clean = df.dropna(subset=["affinity"])
df_clean["affinity"] = pd.to_numeric(df_clean["affinity"], errors="coerce")
df_clean = df_clean.dropna(subset=["affinity"]).sort_values("affinity", ascending=False)

df_clean.to_csv("gpcr_approved_drugs.csv", index=False)
print(f"GPCR approved drug interactions: {len(df_clean)} with affinity data")
print(f"Unique targets: {df_clean['target_id'].nunique()}")
print(f"Unique drugs: {df_clean['ligand_name'].nunique()}")
print(df_clean.head(5)[["target_name", "ligand_name", "action", "affinity_param", "affinity"]].to_string(index=False))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty list from `GET /targets?name=...` | Exact name mismatch; GtoPdb uses official IUPHAR nomenclature | Try a shorter substring (e.g., `"beta-2"` instead of `"beta-2 adrenoceptor"`); use HGNC symbol with `geneSymbol` param |
| `GET /interactions` times out | Large result set (all GPCRs is 90K+ records) | Add filters (`action`, `targetType`, `affinityParameter`) to reduce result set; increase timeout to 120s |
| Interactions return `None` affinity for many records | Many interactions are qualitative (presence/absence, not Ki values) | Use `df.dropna(subset=["affinity"])` to work only with quantitative records; expect ~40% have numeric values |
| Ligand search returns unexpected results | `name` parameter does substring match; common words match multiple ligands | Filter results by `ligand_type` or `approved` flag after retrieval; use `ligandId` if known |
| Target found but no interactions returned | Rare target with no curated interactions or wrong species | Check `species` param — some targets have only Rat/Mouse data; try without species filter |
| `requests.exceptions.ConnectionError` | GtoPdb server temporarily unavailable | Retry after 30s; GtoPdb is academic infrastructure and has occasional downtime |
| Duplicate interactions for same ligand-target pair | Multiple assay entries per interaction (different labs, assay conditions) | Deduplicate by keeping the highest affinity value: `df.sort_values("affinity").drop_duplicates(subset=["ligand_id","target_id"], keep="last")` |

## Related Skills

- `chembl-database-bioactivity` — Larger bioactivity dataset for SAR studies; complement GtoPdb curated potency data with ChEMBL's broader coverage
- `unichem-database` — Translate GtoPdb `chemblId` or `pubchemCid` fields to cross-database identifiers
- `pdb-database` — Retrieve 3D binding structures for receptor-ligand pairs identified in GtoPdb
- `opentargets-database` — Integrate GtoPdb pharmacology data with genetic evidence and disease associations via Open Targets

## References

- [Guide to Pharmacology REST API](https://www.guidetopharmacology.org/webServices.jsp) — Official web services documentation with all endpoint descriptions and example queries
- [GtoPdb home page](https://www.guidetopharmacology.org/) — Interactive database browser and target/ligand search
- [Alexander et al., Br J Pharmacol 2023](https://doi.org/10.1111/bph.15649) — Concise Guide to Pharmacology 2023/24 — the data content reference for GtoPdb
- [Harding et al., Nucleic Acids Res 2022](https://doi.org/10.1093/nar/gkab1010) — GtoPdb database paper describing the data model, curation process, and API
