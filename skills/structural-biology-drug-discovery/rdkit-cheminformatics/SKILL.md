---
name: "rdkit-cheminformatics"
description: "Cheminformatics toolkit for molecular analysis and virtual screening. Use for SMILES/SDF parsing, molecular descriptor calculation (MW, LogP, TPSA), fingerprint generation (Morgan/ECFP, MACCS, RDKit), Tanimoto similarity search, substructure filtering with SMARTS, drug-likeness assessment (Lipinski Ro5), chemical reaction enumeration, 2D/3D coordinate generation, and compound library profiling. For simpler high-level API, use datamol. Use RDKit when you need fine-grained control over sanitization, custom fingerprints, SMARTS queries, or reaction SMARTS."
license: "BSD-3-Clause"
---

# RDKit Cheminformatics Toolkit

## Overview

RDKit is the standard open-source cheminformatics library for Python, providing comprehensive APIs for molecular parsing, descriptor calculation, fingerprinting, substructure searching, and chemical reactions. This skill walks through a complete compound library profiling and virtual screening workflow — from loading molecules through drug-likeness filtering, similarity screening, and result visualization.

## When to Use

- Calculate molecular properties (MW, LogP, TPSA, HBD/HBA) for a compound set
- Screen a library against a reference compound using fingerprint similarity
- Filter compounds by substructure (SMARTS patterns) for functional group analysis
- Assess drug-likeness using Lipinski's Rule of Five or custom filters
- Generate 2D depictions or 3D conformers for downstream docking
- Enumerate chemical libraries using reaction SMARTS (combinatorial chemistry)
- Cluster compounds by structural similarity for diversity analysis
- Standardize and deduplicate molecular datasets (canonical SMILES, InChI)
- Use `datamol-cheminformatics` instead for a higher-level RDKit wrapper with batching and error handling; use `openbabel` instead for multi-format conversion (MOL2, XYZ, PDB)

## Prerequisites

- **Python packages**: `rdkit-pypi` (or `rdkit` via conda), `pandas`, `matplotlib`, `numpy`
- **Data requirements**: Molecular structures as SMILES strings, SDF files, or MOL files
- **Environment**: Python 3.8+; conda recommended for full RDKit installation

```bash
# Option 1: pip (lightweight)
pip install rdkit-pypi pandas matplotlib numpy

# Option 2: conda (full features including cartridge)
conda install -c conda-forge rdkit pandas matplotlib numpy
```

## Workflow

### Step 1: Load and Validate Molecules

Read molecular structures from SMILES or SDF and validate parsing.

```python
from rdkit import Chem
import pandas as pd

# --- From SMILES list ---
smiles_list = [
    "CC(=O)Oc1ccccc1C(=O)O",       # Aspirin
    "CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C",  # Testosterone
    "c1ccc2[nH]c(-c3ccccn3)nc2c1",  # Benzimidazole derivative
    "CC(C)Cc1ccc(C(C)C(=O)O)cc1",   # Ibuprofen
    "INVALID_SMILES",                 # Will fail
]

mols = []
failed = []
for smi in smiles_list:
    mol = Chem.MolFromSmiles(smi)
    if mol is not None:
        mol.SetProp("_SMILES", smi)
        mols.append(mol)
    else:
        failed.append(smi)

print(f"Successfully parsed: {len(mols)}/{len(smiles_list)}")
print(f"Failed: {failed}")

# --- From SDF file ---
# suppl = Chem.SDMolSupplier("library.sdf")
# mols = [mol for mol in suppl if mol is not None]
# print(f"Loaded {len(mols)} molecules from SDF")
```

### Step 2: Standardize and Deduplicate

Canonicalize SMILES and remove duplicates to ensure a clean dataset.

```python
from rdkit.Chem.MolStandardize import rdMolStandardize

# Standardize: neutralize charges, remove fragments, canonicalize
uncharger = rdMolStandardize.Uncharger()
chooser = rdMolStandardize.LargestFragmentChooser()

standardized = []
seen_smiles = set()

for mol in mols:
    # Keep largest fragment (remove salts/counterions)
    mol = chooser.choose(mol)
    # Neutralize charges
    mol = uncharger.uncharge(mol)
    # Canonical SMILES for deduplication
    canon_smi = Chem.MolToSmiles(mol)
    if canon_smi not in seen_smiles:
        seen_smiles.add(canon_smi)
        mol.SetProp("canonical_smiles", canon_smi)
        standardized.append(mol)

print(f"After standardization: {len(standardized)} unique molecules")
print(f"Removed {len(mols) - len(standardized)} duplicates/salts")
```

### Step 3: Calculate Molecular Descriptors

Compute physicochemical properties for each molecule.

```python
from rdkit.Chem import Descriptors

records = []
for mol in standardized:
    desc = {
        "SMILES": Chem.MolToSmiles(mol),
        "MW": round(Descriptors.MolWt(mol), 2),
        "LogP": round(Descriptors.MolLogP(mol), 2),
        "TPSA": round(Descriptors.TPSA(mol), 2),
        "HBD": Descriptors.NumHDonors(mol),
        "HBA": Descriptors.NumHAcceptors(mol),
        "RotBonds": Descriptors.NumRotatableBonds(mol),
        "AromaticRings": Descriptors.NumAromaticRings(mol),
        "HeavyAtoms": mol.GetNumHeavyAtoms(),
        "RingCount": Descriptors.RingCount(mol),
    }
    records.append(desc)

df = pd.DataFrame(records)
print(df.to_string(index=False))
print(f"\nDescriptor summary:\n{df.describe().round(2)}")
```

### Step 4: Apply Drug-Likeness Filters

Filter compounds using Lipinski's Rule of Five and Veber criteria.

```python
def lipinski_filter(row):
    """Lipinski Ro5: MW<=500, LogP<=5, HBD<=5, HBA<=10"""
    return (row["MW"] <= 500 and row["LogP"] <= 5 and
            row["HBD"] <= 5 and row["HBA"] <= 10)

def veber_filter(row):
    """Veber: RotBonds<=10, TPSA<=140"""
    return row["RotBonds"] <= 10 and row["TPSA"] <= 140

df["Lipinski"] = df.apply(lipinski_filter, axis=1)
df["Veber"] = df.apply(veber_filter, axis=1)
df["DrugLike"] = df["Lipinski"] & df["Veber"]

print(f"Lipinski pass: {df['Lipinski'].sum()}/{len(df)}")
print(f"Veber pass:    {df['Veber'].sum()}/{len(df)}")
print(f"Drug-like:     {df['DrugLike'].sum()}/{len(df)}")

drug_like_mols = [standardized[i] for i in df[df["DrugLike"]].index]
print(f"\n{len(drug_like_mols)} drug-like compounds retained")
```

### Step 5: Generate Fingerprints and Similarity Search

Compute Morgan fingerprints and screen against a reference compound.

```python
from rdkit.Chem import AllChem
from rdkit import DataStructs

# Reference compound (e.g., known active)
ref_smi = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
ref_mol = Chem.MolFromSmiles(ref_smi)
ref_fp = AllChem.GetMorganFingerprintAsBitVect(ref_mol, radius=2, nBits=2048)

# Screen library
results = []
for mol in drug_like_mols:
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
    tanimoto = DataStructs.TanimotoSimilarity(ref_fp, fp)
    results.append({
        "SMILES": Chem.MolToSmiles(mol),
        "Tanimoto": round(tanimoto, 3),
    })

sim_df = pd.DataFrame(results).sort_values("Tanimoto", ascending=False)
print("Similarity ranking:")
print(sim_df.to_string(index=False))

# Filter by threshold
threshold = 0.3
hits = sim_df[sim_df["Tanimoto"] >= threshold]
print(f"\n{len(hits)} compounds with Tanimoto >= {threshold}")
```

### Step 6: Substructure Filtering with SMARTS

Filter compounds containing specific functional groups.

```python
# Define SMARTS patterns for functional groups of interest
patterns = {
    "Carboxylic acid": "[CX3](=O)[OX2H1]",
    "Amide": "[CX3](=[OX1])[NX3]",
    "Aromatic ring": "c1ccccc1",
    "Hydroxyl": "[OX2H]",
    "Ester": "[CX3](=O)[OX2][C]",
}

print("Substructure matches:")
for name, smarts in patterns.items():
    query = Chem.MolFromSmarts(smarts)
    match_count = sum(1 for mol in drug_like_mols if mol.HasSubstructMatch(query))
    print(f"  {name}: {match_count}/{len(drug_like_mols)} compounds")

# Get specific matches with atom indices
query = Chem.MolFromSmarts("[CX3](=O)[OX2H1]")  # Carboxylic acid
for mol in drug_like_mols:
    matches = mol.GetSubstructMatches(query)
    if matches:
        smi = Chem.MolToSmiles(mol)
        print(f"\n{smi}: {len(matches)} carboxylic acid group(s)")
        for match in matches:
            print(f"  Atom indices: {match}")
```

### Step 7: 2D Visualization and Grid Plots

Generate publication-quality molecular depictions.

```python
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D

# Grid image of top hits
legends = [f"Tan={row['Tanimoto']}" for _, row in sim_df.head(4).iterrows()]
top_mols = [Chem.MolFromSmiles(smi) for smi in sim_df.head(4)["SMILES"]]

img = Draw.MolsToGridImage(
    top_mols,
    molsPerRow=2,
    subImgSize=(300, 300),
    legends=legends,
)
img.save("top_hits_grid.png")
print("Saved top_hits_grid.png")

# Highlight substructure in a molecule
mol = top_mols[0]
query = Chem.MolFromSmarts("[CX3](=O)[OX2H1]")
match = mol.GetSubstructMatch(query)
if match:
    highlight_img = Draw.MolToImage(mol, size=(400, 400), highlightAtoms=match)
    highlight_img.save("substructure_highlight.png")
    print("Saved substructure_highlight.png")
```

### Step 8: Export Results

Save the profiling results and filtered compounds.

```python
import os

os.makedirs("results", exist_ok=True)

# Save descriptor table
df.to_csv("results/descriptors.csv", index=False)
print(f"Saved descriptors for {len(df)} compounds to results/descriptors.csv")

# Save drug-like compounds as SDF
writer = Chem.SDWriter("results/drug_like_compounds.sdf")
for i, mol in enumerate(drug_like_mols):
    # Attach descriptors as SDF properties
    row = df[df["DrugLike"]].iloc[i]
    mol.SetProp("MW", str(row["MW"]))
    mol.SetProp("LogP", str(row["LogP"]))
    mol.SetProp("TPSA", str(row["TPSA"]))
    writer.write(mol)
writer.close()
print(f"Saved {len(drug_like_mols)} drug-like compounds to results/drug_like_compounds.sdf")

# Save similarity results
sim_df.to_csv("results/similarity_results.csv", index=False)
print(f"Saved similarity rankings to results/similarity_results.csv")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `MolFromSmiles(sanitize=)` | `True` | `True`, `False` | Automatic validation and aromaticity perception on parsing |
| `Morgan radius` | `2` | `1`-`3` | Fingerprint radius; 2 ≈ ECFP4, 3 ≈ ECFP6 |
| `Morgan nBits` | `2048` | `1024`-`4096` | Fingerprint bit length; higher = fewer collisions |
| `Tanimoto threshold` | `0.7` | `0.3`-`0.9` | Similarity cutoff; lower = more permissive |
| `Lipinski MW cutoff` | `500` | `300`-`600` | Max molecular weight for drug-likeness |
| `Lipinski LogP cutoff` | `5` | `3`-`6` | Max lipophilicity |
| `Veber RotBonds cutoff` | `10` | `7`-`15` | Max rotatable bonds for oral bioavailability |
| `Veber TPSA cutoff` | `140` | `120`-`160` | Max polar surface area (Å²) |
| `EmbedMolecule(randomSeed=)` | `None` | Any integer | Seed for reproducible 3D conformer generation |
| `Butina distThresh` | `0.3` | `0.2`-`0.5` | Distance cutoff for Butina clustering |

## Common Recipes

### Recipe: Butina Clustering for Diversity Selection

When to use: select a diverse subset from a large compound library.

```python
from rdkit.ML.Cluster import Butina
from rdkit.Chem import AllChem
from rdkit import DataStructs, Chem

# Generate fingerprints
fps = [AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
       for mol in standardized]

# Build distance matrix (lower triangle)
dists = []
for i in range(1, len(fps)):
    sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])
    dists.extend([1 - s for s in sims])

# Cluster
clusters = Butina.ClusterData(dists, len(fps), distThresh=0.3, isDistData=True)
print(f"{len(clusters)} clusters from {len(fps)} compounds")

# Pick centroid from each cluster (first element = centroid)
diverse_indices = [c[0] for c in clusters]
diverse_mols = [standardized[i] for i in diverse_indices]
print(f"Selected {len(diverse_mols)} diverse representatives")
```

### Recipe: Reaction Enumeration (Amide Coupling)

When to use: generate a combinatorial library from building blocks via reaction SMARTS.

```python
from rdkit.Chem import AllChem, Chem

# Amide coupling: carboxylic acid + amine → amide
rxn = AllChem.ReactionFromSmarts(
    "[C:1](=[O:2])[OH].[N:3]([H])([H])[C:4]>>[C:1](=[O:2])[N:3][C:4]"
)

acids = [Chem.MolFromSmiles(s) for s in ["OC(=O)c1ccccc1", "OC(=O)CC"]]
amines = [Chem.MolFromSmiles(s) for s in ["NCC", "NC1CCCCC1"]]

products = []
for acid in acids:
    for amine in amines:
        ps = rxn.RunReactants((acid, amine))
        for product_set in ps:
            for prod in product_set:
                Chem.SanitizeMol(prod)
                products.append(Chem.MolToSmiles(prod))

print(f"Generated {len(products)} products:")
for p in products:
    print(f"  {p}")
```

### Recipe: 3D Conformer Generation and MMFF Optimization

When to use: prepare molecules for docking or 3D pharmacophore analysis.

```python
from rdkit import Chem
from rdkit.Chem import AllChem

mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
mol = Chem.AddHs(mol)  # Required for 3D embedding

# Generate multiple conformers
params = AllChem.ETKDGv3()
params.randomSeed = 42
params.numThreads = 0  # Use all available cores
conf_ids = AllChem.EmbedMultipleConfs(mol, numConfs=10, params=params)
print(f"Generated {len(conf_ids)} conformers")

# Optimize with MMFF94 force field
energies = []
for conf_id in conf_ids:
    result = AllChem.MMFFOptimizeMolecule(mol, confId=conf_id)
    ff = AllChem.MMFFGetMoleculeForceField(mol, AllChem.MMFFGetMoleculeProperties(mol), confId=conf_id)
    energy = ff.CalcEnergy()
    energies.append((conf_id, energy))
    print(f"  Conformer {conf_id}: {energy:.2f} kcal/mol (converged={result == 0})")

# Get lowest energy conformer
best_id = min(energies, key=lambda x: x[1])[0]
print(f"\nBest conformer: {best_id} ({min(e for _, e in energies):.2f} kcal/mol)")

# Save to SDF
writer = Chem.SDWriter("conformers.sdf")
for conf_id, energy in energies:
    mol.SetProp("Energy", f"{energy:.2f}")
    writer.write(mol, confId=conf_id)
writer.close()
```

### Recipe: Molecular Visualization with Atom Indices and Custom Drawing

When to use: debug SMARTS matches, annotate atom positions for reports.

```python
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
AllChem.Compute2DCoords(mol)

# Custom drawer with atom indices and stereo annotations
drawer = rdMolDraw2D.MolDraw2DCairo(500, 400)
opts = drawer.drawOptions()
opts.addAtomIndices = True
opts.addStereoAnnotation = True
opts.bondLineWidth = 2.0

drawer.DrawMolecule(mol)
drawer.FinishDrawing()

with open("annotated_molecule.png", "wb") as f:
    f.write(drawer.GetDrawingText())
print("Saved annotated_molecule.png with atom indices")
```

## Expected Outputs

- `results/descriptors.csv` — Tabular descriptors (SMILES, MW, LogP, TPSA, HBD, HBA, RotBonds, Lipinski, Veber, DrugLike)
- `results/drug_like_compounds.sdf` — Filtered compounds in SDF format with attached properties
- `results/similarity_results.csv` — Tanimoto similarity rankings against reference compound
- `top_hits_grid.png` — 2D grid image of top similar compounds
- `substructure_highlight.png` — Molecule image with highlighted functional group
- `conformers.sdf` — 3D conformer ensemble with MMFF energies
- `annotated_molecule.png` — Atom-indexed 2D depiction

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `MolFromSmiles` returns `None` | Invalid SMILES string or valence error | Check SMILES validity; use `Chem.MolFromSmiles(smi, sanitize=False)` then `DetectChemistryProblems()` to diagnose |
| `Kekulization error` | Invalid aromatic ring system | Check for non-standard aromaticity; try `Chem.SanitizeMol(mol, sanitizeOps=Chem.SANITIZE_ALL ^ Chem.SANITIZE_KEKULIZE)` |
| `EmbedMolecule` returns `-1` | 3D embedding failed (ring strain, steric clash) | Use `AllChem.EmbedMolecule(mol, maxAttempts=50, useRandomCoords=True)` |
| `MMFF has null force field` | Missing MMFF parameters for atom types | Switch to UFF: `AllChem.UFFOptimizeMolecule(mol)` |
| Wrong descriptor values | Missing explicit hydrogens | Call `Chem.AddHs(mol)` before descriptor calculation for H-dependent properties |
| `ForwardSDMolSupplier` empty | File not found or wrong format | Verify path; use `Chem.SDMolSupplier(path, sanitize=False)` to skip problematic molecules |
| Slow fingerprint computation on large library | Sequential processing | Use `AllChem.GetMorganFingerprintAsBitVect` with pre-allocated arrays; consider `rdkit.Chem.MultithreadedSDMolSupplier` |
| SMARTS pattern no matches | Incorrect SMARTS syntax or aromaticity mismatch | Test pattern with simple SMILES first; use `[#6]` instead of `C` for any carbon |
| `MemoryError` on large SDF | Loading entire file into memory | Use `ForwardSDMolSupplier` for streaming; process in batches |
| Inconsistent canonical SMILES | Different RDKit versions | Pin RDKit version; use `Chem.MolToSmiles(mol, canonical=True)` explicitly |

## Bundled Resources

This skill includes reference files in the `references/` subdirectory:

- `references/api_reference.md` — Key RDKit modules and function lookup organized by capability (I/O, descriptors, fingerprints, drawing, reactions)
- `references/descriptors_guide.md` — Complete list of 200+ molecular descriptors with names, descriptions, and typical ranges
- `references/smarts_patterns.md` — Common SMARTS patterns for functional group detection, organized by chemical class

## References

- [RDKit Documentation](https://www.rdkit.org/docs/) — Official documentation and Getting Started guide
- [RDKit Cookbook](https://www.rdkit.org/docs/Cookbook.html) — Recipes and common workflow patterns
- [Getting Started with RDKit in Python](https://www.rdkit.org/docs/GettingStartedInPython.html) — Comprehensive tutorial
- [Lipinski, C.A. et al. (2001) Advanced Drug Delivery Reviews 46:3-26](https://doi.org/10.1016/S0169-409X(00)00129-0) — Rule of Five
- [Veber, D.F. et al. (2002) J. Med. Chem. 45:2615-2623](https://doi.org/10.1021/jm020017n) — Oral bioavailability criteria
- [Morgan, H.L. (1965) J. Chem. Doc. 5:107-113](https://doi.org/10.1021/c160017a018) — Circular fingerprint algorithm
