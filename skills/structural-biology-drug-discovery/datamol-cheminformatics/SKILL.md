---
name: datamol-cheminformatics
description: >-
  Pythonic RDKit wrapper with sensible defaults for drug discovery. SMILES parsing,
  standardization, descriptors, fingerprints, similarity, clustering, diversity
  selection, scaffold analysis, BRICS/RECAP fragmentation, 3D conformers, and
  visualization. Returns native rdkit.Chem.Mol. Prefer datamol for standard
  workflows; use RDKit directly for advanced control.
license: Apache-2.0
---

# Datamol Cheminformatics Toolkit

## Overview

Datamol provides a lightweight, Pythonic abstraction layer over RDKit for molecular cheminformatics. It simplifies common drug discovery operations — SMILES parsing, standardization, descriptors, fingerprints, clustering, scaffolds, conformers, and visualization — with sensible defaults, built-in parallelization, and cloud storage support via fsspec. All molecular objects are native `rdkit.Chem.Mol` instances, ensuring full RDKit compatibility.

## When to Use

- Parsing, validating, and standardizing molecular structures from SMILES, SDF, or other formats
- Computing molecular descriptors and fingerprints for ML featurization
- Similarity searching and diversity selection from compound libraries
- Clustering compounds by structural similarity (Butina clustering)
- Scaffold analysis and scaffold-based train/test splitting for ML
- BRICS/RECAP molecular fragmentation for fragment-based design
- 3D conformer generation and analysis
- Visualizing molecules as grids with alignment and highlighting
- Batch processing molecular datasets with parallelization
- For quick gene lookups use **gget** instead; for advanced substructure queries or custom fingerprints, use **RDKit** directly

## Prerequisites

```bash
uv pip install datamol
```

```python
import datamol as dm
import numpy as np
import pandas as pd
```

## Quick Start

```python
import datamol as dm

# Parse and standardize
mol = dm.to_mol("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
mol = dm.standardize_mol(mol)
print(dm.to_smiles(mol))  # Canonical SMILES

# Compute descriptors
desc = dm.descriptors.compute_many_descriptors(mol)
print(f"MW: {desc['mw']:.1f}, LogP: {desc['logp']:.2f}, TPSA: {desc['tpsa']:.1f}")

# Generate fingerprint
fp = dm.to_fp(mol, fp_type='ecfp', radius=2, n_bits=2048)
print(f"Fingerprint shape: {fp.shape}")  # (2048,)
```

## Core API

### 1. Molecular I/O & Standardization

**Parsing molecules**:
```python
import datamol as dm

# From SMILES (returns None on failure)
mol = dm.to_mol("CCO")
if mol is None:
    print("Invalid SMILES")

# Format conversions
smiles = dm.to_smiles(mol, isomeric=True)  # Canonical SMILES
inchi = dm.to_inchi(mol)
inchikey = dm.to_inchikey(mol)
selfies = dm.to_selfies(mol)
```

**Standardization** (always recommended for external data):
```python
mol = dm.standardize_mol(
    mol,
    disconnect_metals=True,
    normalize=True,
    reionize=True
)
clean_smiles = dm.standardize_smiles("C(C)O")  # From SMILES directly
```

**File I/O**:
```python
# Reading (supports local, S3, GCS, HTTP via fsspec)
df = dm.read_sdf("compounds.sdf", mol_column='mol')
df = dm.read_csv("data.csv", smiles_column="SMILES", mol_column="mol")
df = dm.read_excel("compounds.xlsx", sheet_name=0, mol_column="mol")
df = dm.open_df("file.sdf")  # Auto-detect format

# Writing
dm.to_sdf(df, "output.sdf", mol_column="mol")
dm.to_smi(mols, "output.smi")
dm.to_xlsx(df, "output.xlsx", mol_columns=["mol"])  # Renders molecule images

# Remote files
df = dm.read_sdf("s3://bucket/compounds.sdf")
dm.to_sdf(mols, "s3://bucket/output.sdf")
```

### 2. Descriptors & Properties

```python
import datamol as dm

mol = dm.to_mol("c1ccc(cc1)CCN")

# Standard descriptor set (single molecule)
desc = dm.descriptors.compute_many_descriptors(mol)
# Returns dict: {'mw': 121.18, 'logp': 1.41, 'hbd': 1, 'hba': 1,
#                'tpsa': 26.02, 'n_aromatic_atoms': 6, ...}

# Batch computation (parallel)
mols = [dm.to_mol(s) for s in ["CCO", "c1ccccc1", "CC(=O)O"]]
desc_df = dm.descriptors.batch_compute_many_descriptors(
    mols, n_jobs=-1, progress=True
)
print(desc_df.head())

# Specific descriptors
n_stereo = dm.descriptors.n_stereo_centers(mol)
n_aromatic = dm.descriptors.n_aromatic_atoms(mol)
aromatic_ratio = dm.descriptors.n_aromatic_atoms_proportion(mol)
n_rigid = dm.descriptors.n_rigid_bonds(mol)
```

**Drug-likeness filtering (Lipinski Rule of Five)**:
```python
def is_druglike(mol):
    desc = dm.descriptors.compute_many_descriptors(mol)
    return (desc['mw'] <= 500 and desc['logp'] <= 5
            and desc['hbd'] <= 5 and desc['hba'] <= 10)

druglike = [m for m in mols if is_druglike(m)]
print(f"Drug-like: {len(druglike)}/{len(mols)}")
```

### 3. Fingerprints & Similarity

```python
import datamol as dm

mol = dm.to_mol("c1ccc(cc1)CCN")

# Fingerprint types
fp_ecfp = dm.to_fp(mol, fp_type='ecfp', radius=2, n_bits=2048)  # Morgan/ECFP
fp_maccs = dm.to_fp(mol, fp_type='maccs')    # MACCS keys (167 bits)
fp_topo = dm.to_fp(mol, fp_type='topological')  # Topological
fp_ap = dm.to_fp(mol, fp_type='atompair')    # Atom pairs

# Pairwise distances (Tanimoto distance = 1 - similarity)
mols = [dm.to_mol(s) for s in ["CCO", "CCCO", "c1ccccc1"]]
dist_matrix = dm.pdist(mols, n_jobs=-1)
print(f"Distance vector shape: {dist_matrix.shape}")

# Distances between two sets
query = [dm.to_mol("CCO")]
library = [dm.to_mol(s) for s in ["CCCO", "c1ccccc1", "CC(=O)O"]]
distances = dm.cdist(query, library, n_jobs=-1)
print(f"Query-library distances: {distances.shape}")
```

### 4. Clustering & Diversity Selection

```python
import datamol as dm

mols = [dm.to_mol(s) for s in smiles_list]  # Assume smiles_list defined

# Butina clustering (suitable for ~1000 molecules, builds full distance matrix)
clusters = dm.cluster_mols(mols, cutoff=0.2, n_jobs=-1)
for i, cluster in enumerate(clusters[:5]):
    print(f"Cluster {i}: {len(cluster)} molecules")

# Diversity selection (works for larger libraries)
diverse_mols = dm.pick_diverse(mols, npick=100)
print(f"Selected {len(diverse_mols)} diverse molecules")

# Cluster centroids
centroids = dm.pick_centroids(mols, npick=50)
print(f"Selected {len(centroids)} centroids")
```

### 5. Scaffolds & Fragments

**Murcko scaffold extraction**:
```python
import datamol as dm
from collections import Counter

mol = dm.to_mol("c1ccc(cc1)CCN")
scaffold = dm.to_scaffold_murcko(mol)
print(f"Scaffold: {dm.to_smiles(scaffold)}")

# Scaffold frequency analysis
scaffolds = [dm.to_scaffold_murcko(m) for m in mols]
scaffold_smiles = [dm.to_smiles(s) for s in scaffolds]
counts = Counter(scaffold_smiles)
print(f"Top scaffolds: {counts.most_common(5)}")

# Scaffold-based train/test split (for ML)
scaffold_to_mols = {}
for mol, scaf in zip(mols, scaffold_smiles):
    scaffold_to_mols.setdefault(scaf, []).append(mol)
scaffolds_list = list(scaffold_to_mols.keys())
split_idx = int(0.8 * len(scaffolds_list))
train_mols = [m for s in scaffolds_list[:split_idx] for m in scaffold_to_mols[s]]
test_mols = [m for s in scaffolds_list[split_idx:] for m in scaffold_to_mols[s]]
```

**Fragmentation**:
```python
mol = dm.to_mol("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin

# BRICS (16 bond types, retrosynthetic)
brics_frags = dm.fragment.brics(mol)
print(f"BRICS fragments: {brics_frags}")  # Set of fragment SMILES with [1*] attachment points

# RECAP (11 bond types, combinatorial)
recap_frags = dm.fragment.recap(mol)

# MMPA (matched molecular pair analysis)
mmpa_frags = dm.fragment.mmpa_frag(mol)
```

### 6. 3D Conformers

```python
import datamol as dm

mol = dm.to_mol("c1ccc(cc1)CCN")

# Generate conformers
mol_3d = dm.conformers.generate(
    mol,
    n_confs=50,           # Number to generate
    rms_cutoff=0.5,       # Filter similar (Angstroms)
    minimize_energy=True,  # UFF minimization
    method='ETKDGv3'      # Embedding method
)
print(f"Generated {mol_3d.GetNumConformers()} conformers")

# Access coordinates
conf = mol_3d.GetConformer(0)
positions = conf.GetPositions()  # Nx3 array
print(f"Atom positions shape: {positions.shape}")

# Cluster conformers by RMSD
clusters = dm.conformers.cluster(mol_3d, rms_cutoff=1.0)
centroids = dm.conformers.return_centroids(mol_3d, clusters)

# Solvent accessible surface area
sasa = dm.conformers.sasa(mol_3d, n_jobs=-1)
print(f"SASA values: {sasa[:3]}")
```

## Key Concepts

### Datamol vs RDKit Decision Guide

| Use Datamol when... | Use RDKit directly when... |
|---------------------|---------------------------|
| Standard SMILES ↔ Mol conversions | Custom fingerprint definitions |
| Batch processing with parallelization | Low-level atom/bond manipulation |
| Quick descriptor computation | Substructure query optimization |
| File I/O (SDF, CSV, Excel, cloud) | Reaction enumeration (large-scale) |
| Clustering & diversity selection | Custom force field parameters |
| Scaffold analysis | Advanced stereochemistry handling |

### Key Data Types

- All molecules are native `rdkit.Chem.Mol` objects — fully compatible with RDKit functions
- Fingerprints are numpy arrays (dense bit vectors)
- DataFrames use pandas with a `mol` column containing Mol objects
- Distance matrices use Tanimoto distance (0 = identical, 1 = completely different)

### Parallelization

Functions supporting `n_jobs` parameter: `dm.read_sdf`, `dm.descriptors.batch_compute_many_descriptors`, `dm.cluster_mols`, `dm.pdist`, `dm.cdist`, `dm.conformers.sasa`. Use `n_jobs=-1` for all cores, `progress=True` for progress bars.

## Common Workflows

### 1. Drug Discovery Pipeline: Load → Filter → Cluster → Visualize

```python
import datamol as dm

# 1. Load and standardize
df = dm.read_sdf("compounds.sdf")
df['mol'] = df['mol'].apply(lambda m: dm.standardize_mol(m) if m else None)
df = df[df['mol'].notna()]
print(f"Loaded {len(df)} valid molecules")

# 2. Compute descriptors and filter by drug-likeness
desc_df = dm.descriptors.batch_compute_many_descriptors(
    df['mol'].tolist(), n_jobs=-1, progress=True
)
druglike = (desc_df['mw'] <= 500) & (desc_df['logp'] <= 5) & (desc_df['hbd'] <= 5) & (desc_df['hba'] <= 10)
filtered_df = df[druglike.values].reset_index(drop=True)
print(f"Drug-like compounds: {len(filtered_df)}")

# 3. Select diverse subset
diverse = dm.pick_diverse(filtered_df['mol'].tolist(), npick=100)

# 4. Visualize
dm.viz.to_image(diverse[:20], legends=[dm.to_smiles(m) for m in diverse[:20]],
                n_cols=5, mol_size=(300, 300), outfile="diverse_hits.png")
```

### 2. Virtual Screening: Query → Similarity → Rank

```python
import datamol as dm
import numpy as np

# Query actives and screening library
actives = [dm.to_mol(s) for s in active_smiles]  # Known actives
library = [dm.to_mol(s) for s in library_smiles]  # Screening library

# Calculate distances (Tanimoto)
distances = dm.cdist(actives, library, n_jobs=-1)
min_distances = distances.min(axis=0)  # Best match to any active
similarities = 1 - min_distances

# Rank and select top hits
top_idx = np.argsort(similarities)[::-1][:100]
top_hits = [library[i] for i in top_idx]
top_scores = [similarities[i] for i in top_idx]
print(f"Top hit similarity: {top_scores[0]:.3f}")

# Visualize top hits
dm.viz.to_image(top_hits[:20],
    legends=[f"Sim: {s:.3f}" for s in top_scores[:20]],
    outfile="screening_hits.png")
```

### 3. SAR Analysis: Group by Scaffold → Compare Activities

```python
import datamol as dm

# Group compounds by scaffold
scaffolds = [dm.to_scaffold_murcko(m) for m in mols]
scaffold_smiles = [dm.to_smiles(s) for s in scaffolds]

sar_df = pd.DataFrame({
    'mol': mols, 'scaffold': scaffold_smiles, 'activity': activities
})

# Analyze each scaffold series
for scaffold, group in sar_df.groupby('scaffold'):
    if len(group) >= 3:
        print(f"Scaffold: {scaffold} | N={len(group)} | "
              f"Activity: {group['activity'].min():.2f}–{group['activity'].max():.2f}")
        dm.viz.to_image(group['mol'].tolist(), align=True,
            legends=[f"Act: {a:.2f}" for a in group['activity']])
```

## Key Parameters

| Function | Parameter | Default | Description |
|----------|-----------|---------|-------------|
| `dm.to_fp` | `fp_type` | `'ecfp'` | Fingerprint type: ecfp, maccs, topological, atompair |
| `dm.to_fp` | `radius` | `2` | Morgan radius (ecfp only); radius=2 ≈ ECFP4 |
| `dm.to_fp` | `n_bits` | `2048` | Fingerprint length (ecfp, topological) |
| `dm.cluster_mols` | `cutoff` | `0.2` | Tanimoto distance threshold (0=identical, 1=different) |
| `dm.pick_diverse` | `npick` | required | Number of diverse molecules to select |
| `dm.conformers.generate` | `n_confs` | `None` | Number of conformers (None = auto) |
| `dm.conformers.generate` | `rms_cutoff` | `None` | RMSD filter threshold (Angstroms) |
| `dm.conformers.generate` | `method` | `'ETKDGv3'` | Embedding: ETKDGv3, ETKDGv2, ETKDG |
| `dm.standardize_mol` | `disconnect_metals` | `False` | Remove metal-ligand bonds |
| `dm.read_sdf` | `sanitize` | `True` | Apply molecule sanitization |
| `dm.read_sdf` | `remove_hs` | `True` | Remove explicit hydrogens |
| `dm.viz.to_image` | `align` | `False` | Align molecules by MCS |
| `dm.viz.to_image` | `use_svg` | `False` | Output SVG (True) or PNG (False) |

## Best Practices

1. **Always standardize molecules from external sources** — call `dm.standardize_mol()` with `disconnect_metals=True, normalize=True, reionize=True` before any analysis. Different SMILES representations of the same molecule will produce different fingerprints
2. **Check for None after parsing** — `dm.to_mol()` returns `None` for invalid SMILES. Filter these before batch operations to avoid crashes
3. **Use parallel processing for datasets** — pass `n_jobs=-1, progress=True` to batch operations. Sequential processing of 10,000+ molecules is unnecessarily slow
4. **Choose fingerprints by use case** — ECFP (Morgan): general structural similarity; MACCS: fast, smaller space; Atom pairs: distance-sensitive. ECFP with radius=2, n_bits=2048 is the most common default
5. **Mind clustering scale limits** — Butina clustering (`dm.cluster_mols`) builds a full distance matrix. Use for ≤~1,000 molecules. For larger sets, use `dm.pick_diverse()` or hierarchical methods
6. **Use scaffold splitting for ML** — random splits leak similar structures into train/test. Always use scaffold-based splitting for molecular property prediction models
7. **Leverage fsspec for cloud data** — all I/O functions accept S3, GCS, and HTTP paths directly. Install `s3fs` or `gcsfs` for cloud support

## Common Recipes

### Recipe: Batch SMILES Validation and Standardization

When to use: Clean a list of SMILES strings before any downstream analysis.

```python
import datamol as dm

smiles_list = ["CC(=O)Oc1ccccc1C(=O)O", "c1ccccc1", "invalid_smiles", "CC(N)C(=O)O"]
mols = [dm.to_mol(s) for s in smiles_list]
valid = [(s, m) for s, m in zip(smiles_list, mols) if m is not None]
standardized = [(s, dm.standardize_mol(m)) for s, m in valid]
print(f"Valid: {len(valid)}/{len(smiles_list)}")
for orig, mol in standardized:
    print(f"  {orig} → {dm.to_smiles(mol)}")
```

### Recipe: Pairwise Similarity Matrix

When to use: Compare a small compound set against each other or a reference library.

```python
import datamol as dm
import numpy as np

smiles = ["CC(=O)Oc1ccccc1C(=O)O", "c1ccc(cc1)C(=O)O", "CC(N)C(=O)O", "c1ccccc1"]
mols = [dm.to_mol(s) for s in smiles]
fps = [dm.to_fp(m) for m in mols]

# Pairwise Tanimoto similarity
n = len(fps)
sim_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        sim_matrix[i, j] = dm.similarity.tanimoto(fps[i], fps[j])
print(f"Similarity matrix shape: {sim_matrix.shape}")
print(f"Most similar pair: {np.unravel_index(np.argsort(sim_matrix.ravel())[-3], (n, n))}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `dm.to_mol()` returns None | Invalid or non-canonical SMILES | Try `dm.standardize_smiles()` first; check for kekulization issues |
| MemoryError during clustering | Full distance matrix for large set | Use `dm.pick_diverse()` instead of `dm.cluster_mols` for >1000 molecules |
| Slow conformer generation | Too many conformers or large molecule | Reduce `n_confs`, increase `rms_cutoff`, or limit molecule size |
| Remote file access fails | Missing fsspec backend | Install `s3fs` (AWS), `gcsfs` (GCP), or `adlfs` (Azure) |
| Descriptor computation fails | Molecule has no conformer | Standardize first; some 3D descriptors need `dm.conformers.generate()` |
| `dm.to_xlsx` missing images | openpyxl not installed | `uv pip install openpyxl` |
| Inconsistent fingerprints | Different SMILES for same molecule | Standardize all molecules before fingerprint computation |
| Scaffold extraction returns full molecule | No ring system in molecule | Murcko scaffolds require at least one ring; acyclic molecules return themselves |
| Reaction product is None | Reactant doesn't match SMARTS pattern | Verify reactant matches reaction template; check atom mapping |
| Import error for `dm.viz` | Missing visualization dependencies | `uv pip install Pillow cairosvg` |

## Related Skills

- **rdkit-cheminformatics** — full RDKit API for advanced operations not covered by datamol's simplified interface
- **pubchem-compound-search** — retrieve compound data by name, CID, or structure from PubChem
- **scikit-learn-machine-learning** — ML model training using datamol-generated features
- **matplotlib-scientific-plotting** — custom publication-quality molecular property plots

## References

- Datamol documentation: https://docs.datamol.io/
- RDKit documentation: https://www.rdkit.org/docs/
- GitHub repository: https://github.com/datamol-io/datamol
- Bemis, G. W. & Murcko, M. A. (1996). The Properties of Known Drugs. J. Med. Chem. 39(15), 2887–2893
