---
name: "autodock-vina-docking"
description: "Molecular docking with AutoDock Vina via Python API. Receptor/ligand preparation (Meeko + RDKit), grid box setup, docking execution, pose extraction, binding energy analysis, and batch virtual screening. Use for protein-ligand docking and hit identification."
license: "CC-BY-4.0"
---

# AutoDock Vina Molecular Docking

## Overview

AutoDock Vina is one of the fastest and most widely used open-source molecular docking engines for predicting protein–ligand binding modes and affinities. This skill covers the full Python-based pipeline: receptor preparation from PDB, ligand preparation from SMILES/SDF via Meeko and RDKit, search box definition, docking execution, pose analysis, and batch virtual screening for hit identification.

## When to Use

- Predicting binding poses of small molecules to a protein target
- Estimating relative binding affinities (kcal/mol) for ligand ranking
- Virtual screening of compound libraries against a target receptor
- Validating docking protocols by re-docking co-crystallized ligands
- Preparing docking inputs from SMILES strings without intermediate files
- Comparing binding modes of analogs in a structure-activity relationship study
- Generating starting poses for molecular dynamics simulations

## Prerequisites

- **Python packages**: `vina`, `meeko`, `rdkit`, `prody` (for PDB fetch), `py3Dmol` (for visualization)
- **External tools**: `ADFR Suite` (provides `prepare_receptor` for PDBQT conversion) — download from https://ccsb.scripps.edu/adfr/downloads/
- **Data requirements**: Protein structure (PDB file or PDB ID), ligand(s) as SMILES, SDF, or MOL2
- **Environment**: Python 3.8+, Linux or macOS recommended

```bash
pip install vina meeko rdkit-pypi prody py3Dmol
# ADFR Suite must be installed separately for prepare_receptor
```

## Workflow

### Step 1: Fetch and Prepare the Receptor

Download the protein structure, remove water/heteroatoms, and convert to PDBQT format.

```python
import prody
import subprocess
from pathlib import Path

# Download PDB structure (example: HIV-1 protease, PDB 1HPV)
pdb_id = "1HPV"
pdb_file = f"{pdb_id}.pdb"
prody.fetchPDB(pdb_id, compressed=False)

# Extract protein chain only (remove water and ligands)
structure = prody.parsePDB(pdb_file)
protein = structure.select("protein")
prody.writePDB(f"{pdb_id}_protein.pdb", protein)
print(f"Protein atoms: {protein.numAtoms()}")

# Convert to PDBQT using ADFR Suite's prepare_receptor
receptor_pdbqt = f"{pdb_id}_receptor.pdbqt"
subprocess.run([
    "prepare_receptor",
    "-r", f"{pdb_id}_protein.pdb",
    "-o", receptor_pdbqt,
    "-A", "hydrogens",  # add hydrogens
], check=True)
print(f"Receptor PDBQT: {receptor_pdbqt}")
```

### Step 2: Identify the Binding Site

Define the docking search box centered on the known binding site or co-crystallized ligand.

```python
import numpy as np

# Option A: Center on co-crystallized ligand coordinates
structure = prody.parsePDB(pdb_file)
ligand = structure.select("hetero and not water and not ion")
if ligand is not None:
    center = ligand.getCoords().mean(axis=0)
    # Box size = ligand extent + padding
    extent = ligand.getCoords().max(axis=0) - ligand.getCoords().min(axis=0)
    box_size = extent + 10.0  # 10 Å padding on each side
    print(f"Binding site center: {center}")
    print(f"Box size: {box_size}")
else:
    # Option B: Manual coordinates (from literature or visual inspection)
    center = np.array([15.0, 54.0, 17.0])
    box_size = np.array([25.0, 25.0, 25.0])
    print(f"Using manual box: center={center}, size={box_size}")
```

### Step 3: Prepare the Ligand from SMILES

Use RDKit for 3D coordinate generation and Meeko for PDBQT conversion.

```python
from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy

# Define ligand (example: Indinavir, HIV protease inhibitor)
smiles = "CC(C)(C)NC(=O)[C@@H]1CN(CCc2ccccc2)C[C@H]1O"
mol_name = "indinavir_analog"

# Generate 3D coordinates with RDKit
mol = Chem.MolFromSmiles(smiles)
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, randomSeed=42)
AllChem.MMFFOptimizeMolecule(mol)

# Convert to PDBQT using Meeko
preparator = MoleculePreparation()
mol_setups = preparator.prepare(mol)

# Write PDBQT string (for Vina API) or file
pdbqt_string = PDBQTWriterLegacy.write_string(mol_setups[0])[0]
ligand_pdbqt = f"{mol_name}.pdbqt"
with open(ligand_pdbqt, "w") as f:
    f.write(pdbqt_string)
print(f"Ligand PDBQT: {ligand_pdbqt} ({mol.GetNumAtoms()} atoms)")
```

### Step 4: Run Docking

Initialize AutoDock Vina, configure the search space, and execute docking.

```python
from vina import Vina

# Initialize Vina
v = Vina(sf_name="vina", cpu=4)

# Load receptor and ligand
v.set_receptor(receptor_pdbqt)
v.set_ligand_from_file(ligand_pdbqt)

# Define search space
v.compute_vina_maps(
    center=center.tolist(),
    box_size=box_size.tolist(),
)

# Run docking
v.dock(
    exhaustiveness=32,   # Higher = more thorough (default 8)
    n_poses=10,          # Number of output poses
)

# Write output poses
output_file = f"{mol_name}_docked.pdbqt"
v.write_poses(output_file, n_poses=10, overwrite=True)
print(f"Docking complete. Poses written to {output_file}")
```

### Step 5: Analyze Docking Results

Extract binding energies and RMSD values from the docked poses using Vina's built-in API.

```python
# Method A: Vina built-in energies (most reliable)
energies = v.energies(n_poses=10)
# Each row: [total, inter, intra, torsions, intra_best_pose]
print(f"{'Pose':<6} {'Total (kcal/mol)':<18} {'Inter':<10} {'Intra':<10}")
print("-" * 44)
for i, e in enumerate(energies):
    print(f"{i+1:<6} {e[0]:<18.2f} {e[1]:<10.2f} {e[2]:<10.2f}")

print(f"\nBest pose: {energies[0][0]:.2f} kcal/mol")

# Method B: Parse PDBQT output with Meeko (for RDKit conversion)
from meeko import PDBQTMolecule, RDKitMolCreate
pdbqt_mol = PDBQTMolecule.from_file(output_file)
best_pose_rdkit = RDKitMolCreate.from_pdbqt_mol(pdbqt_mol)[0]
print(f"Best pose converted to RDKit mol: {best_pose_rdkit.GetNumAtoms()} atoms")
```

### Step 6: Visualize Docking Results

Generate a 3D visualization of the docked complex using py3Dmol.

```python
import py3Dmol

# Load receptor and best docked pose
with open(f"{pdb_id}_protein.pdb") as f:
    receptor_pdb = f.read()
with open(output_file) as f:
    docked_pdbqt = f.read()

# Create 3D viewer
view = py3Dmol.view(width=800, height=600)
view.addModel(receptor_pdb, "pdb")
view.setStyle({"model": 0}, {"cartoon": {"color": "lightgrey"}})

# Add docked ligand (first model only)
first_model = docked_pdbqt.split("ENDMDL")[0] + "ENDMDL"
view.addModel(first_model, "pdb")
view.setStyle({"model": 1}, {"stick": {"colorscheme": "greenCarbon"}})

# Zoom to ligand
view.zoomTo({"model": 1})
view.show()
# In Jupyter: displays interactive 3D view
# To save: view.png() or view.write_html("docking_result.html")
print("3D visualization rendered")
```

### Step 7: Batch Virtual Screening

Screen a library of compounds against the same receptor.

```python
import pandas as pd

# Define compound library
compounds = pd.DataFrame({
    "name": ["cpd_001", "cpd_002", "cpd_003", "cpd_004", "cpd_005"],
    "smiles": [
        "CC(=O)Oc1ccccc1C(=O)O",          # Aspirin
        "CC(C)Cc1ccc(cc1)C(C)C(=O)O",      # Ibuprofen
        "OC(=O)c1ccccc1O",                  # Salicylic acid
        "CC12CCC3C(CCC4CC(=O)CCC34C)C1CCC2O",  # Testosterone
        "c1ccc2c(c1)cc1ccc3cccc4ccc2c1c34",     # Pyrene
    ],
})

# Screen all compounds
results = []
for _, row in compounds.iterrows():
    try:
        # Prepare ligand
        mol = Chem.MolFromSmiles(row["smiles"])
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        AllChem.MMFFOptimizeMolecule(mol)

        mol_setups = preparator.prepare(mol)
        pdbqt_str = PDBQTWriterLegacy.write_string(mol_setups[0])[0]

        # Dock
        v_screen = Vina(sf_name="vina", cpu=2)
        v_screen.set_receptor(receptor_pdbqt)
        v_screen.set_ligand_from_string(pdbqt_str)
        v_screen.compute_vina_maps(center=center.tolist(), box_size=box_size.tolist())
        v_screen.dock(exhaustiveness=16, n_poses=1)

        energy = v_screen.energies(n_poses=1)[0][0]
        results.append({"name": row["name"], "smiles": row["smiles"], "energy_kcal": energy})
        print(f"  {row['name']}: {energy:.2f} kcal/mol")

    except Exception as e:
        results.append({"name": row["name"], "smiles": row["smiles"], "energy_kcal": None})
        print(f"  {row['name']}: FAILED ({e})")

# Rank by binding energy
results_df = pd.DataFrame(results).sort_values("energy_kcal")
results_df.to_csv("screening_results.csv", index=False)
print(f"\nTop hits:\n{results_df.head()}")
```

### Step 8: Save and Export

```python
import os
os.makedirs("results", exist_ok=True)

# Save summary
results_df.to_csv("results/screening_results.csv", index=False)

# Save best poses for top hits
for _, row in results_df.head(3).iterrows():
    print(f"Top hit: {row['name']} → {row['energy_kcal']:.2f} kcal/mol")

print("Virtual screening complete. Results in results/screening_results.csv")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `exhaustiveness` | `8` | `8`-`128` | Search thoroughness; 32+ recommended for publication |
| `n_poses` | `9` | `1`-`20` | Number of output binding poses |
| `energy_range` | `3.0` | `1.0`-`5.0` | Max energy difference (kcal/mol) from best pose to include |
| `sf_name` | `"vina"` | `"vina"`, `"ad4"`, `"vinardo"` | Scoring function choice |
| `cpu` | all | `1`-`N` | Number of CPU cores for docking |
| `box_size` (xyz) | — | `15`-`30` Å per side | Search space dimensions; must enclose binding site + 5-10Å padding |
| `center` (xyz) | — | Binding site coordinates | Center of the search box |
| `randomSeed` (RDKit) | random | any int | Reproducible 3D conformer generation |
| `padding` (box) | `10.0` Å | `5.0`-`15.0` Å | Extra space around known ligand for box definition |

## Common Recipes

### Recipe: Re-docking Validation (Cognate Docking)

When to use: validating your protocol by re-docking the co-crystallized ligand and checking RMSD < 2.0 Å.

```python
from rdkit.Chem import AllChem, rdMolAlign

# Extract co-crystallized ligand from PDB
ref_ligand = Chem.MolFromPDBFile(f"{pdb_id}_ligand.pdb", removeHs=False)

# Dock the same ligand
# ... (use steps 3-4 above with the extracted ligand)

# Calculate RMSD between docked pose and crystal structure
rmsd = AllChem.GetBestRMS(ref_ligand, best_pose_rdkit)
print(f"Re-docking RMSD: {rmsd:.2f} Å")
print(f"Validation: {'PASS' if rmsd < 2.0 else 'FAIL'} (threshold: 2.0 Å)")
```

### Recipe: Flexible Receptor Docking

When to use: key binding-site residues need conformational freedom (e.g., induced fit).

```python
# Prepare receptor with flexible sidechains (using ADFR Suite)
# prepare_receptor -r protein.pdb -o rigid.pdbqt -A hydrogens
# prepare_flexreceptor -r rigid.pdbqt -s "A:ARG8,A:ASP25,A:ILE50"

v_flex = Vina(sf_name="vina", cpu=4)
v_flex.set_receptor("rigid.pdbqt", "flex.pdbqt")  # rigid + flexible parts
v_flex.set_ligand_from_file(ligand_pdbqt)
v_flex.compute_vina_maps(center=center.tolist(), box_size=box_size.tolist())
v_flex.dock(exhaustiveness=64, n_poses=10)
v_flex.write_poses("docked_flex.pdbqt", n_poses=5, overwrite=True)
```

### Recipe: Scoring Only (No Docking)

When to use: evaluating the binding energy of a pre-positioned ligand without running a full search.

```python
v_score = Vina(sf_name="vina")
v_score.set_receptor(receptor_pdbqt)
v_score.set_ligand_from_file("pre_positioned_ligand.pdbqt")
v_score.compute_vina_maps(center=center.tolist(), box_size=box_size.tolist())

# Score current pose
energy = v_score.score()
print(f"Score: {energy[0]:.2f} kcal/mol")

# Local minimization
energy_min = v_score.optimize()
print(f"After local optimization: {energy_min[0]:.2f} kcal/mol")
v_score.write_pose("minimized.pdbqt", overwrite=True)
```

### Recipe: Multiple Scoring Functions Comparison

When to use: consensus scoring to increase confidence in docking results.

```python
scoring_results = {}
for sf in ["vina", "vinardo", "ad4"]:
    v_sf = Vina(sf_name=sf, cpu=2)
    v_sf.set_receptor(receptor_pdbqt)
    v_sf.set_ligand_from_file(ligand_pdbqt)
    v_sf.compute_vina_maps(center=center.tolist(), box_size=box_size.tolist())
    v_sf.dock(exhaustiveness=16, n_poses=1)
    scoring_results[sf] = v_sf.energies(n_poses=1)[0][0]

for sf, energy in scoring_results.items():
    print(f"  {sf}: {energy:.2f} kcal/mol")
```

## Expected Outputs

- `{name}_docked.pdbqt` — Docked poses in PDBQT format with binding energies in header
- `results/screening_results.csv` — Virtual screening results: compound name, SMILES, binding energy (kcal/mol)
- `{pdb_id}_receptor.pdbqt` — Prepared receptor in PDBQT format
- Figures: 3D docking visualization (interactive py3Dmol or static image)
- Console output: ranked binding energies and RMSD values per pose

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `prepare_receptor` not found | ADFR Suite not in PATH | Add ADFR Suite bin to `$PATH` or use full path |
| `RuntimeError: receptor not set` | Forgot to call `set_receptor` | Call `v.set_receptor(pdbqt_file)` before docking |
| Very positive docking scores (>0) | Ligand outside box or bad geometry | Check box center/size covers binding site; verify 3D coords |
| All poses identical | `exhaustiveness` too low | Increase to 32-64 for reliable sampling |
| `Meeko MoleculePreparation` error | Missing hydrogens on input mol | Always call `Chem.AddHs(mol)` before Meeko |
| RMSD > 2Å in re-docking | Box too small or wrong center | Expand box by 5Å; verify center on co-crystallized ligand |
| `EmbedMolecule` returns -1 | RDKit failed to generate 3D coords | Use `AllChem.EmbedMolecule(mol, maxAttempts=1000)` or try `useRandomCoords=True` |
| Slow screening (>1min/compound) | High exhaustiveness + large box | Reduce `exhaustiveness` to 8-16 for screening; narrow box |
| `PDBQTWriterLegacy` not found | Old Meeko version | `pip install meeko>=0.5` — API changed from `write_pdbqt_string` |
| Inconsistent energies across runs | Non-deterministic search | Set `seed` parameter in `v.dock(seed=42)` for reproducibility |

## Bundled Resources

This skill includes reference files for deeper lookup. Read these on demand.

### references/receptor_preparation_guide.md
Detailed guide for receptor preparation: handling missing residues, protonation states (pH-dependent), metal ions, cofactors, and multi-chain complexes. Decision tree for when to use PDB2PQR, PROPKA, or manual protonation.

### references/scoring_functions_comparison.md
Comparison of Vina, Vinardo, and AD4 scoring functions: accuracy benchmarks, speed trade-offs, and recommendations by target class (kinase, protease, GPCR, nuclear receptor).

## References

- [AutoDock Vina documentation](https://autodock-vina.readthedocs.io/) — Official docs and Python API (Apache-2.0)
- [Eberhardt et al. (2021)](https://doi.org/10.1021/acs.jcim.1c00203) — "AutoDock Vina 1.2.0: New Docking Methods, Expanded Force Field, and Python Bindings", *J Chem Inf Model*
- [Meeko: Preparation of small molecules for AutoDock](https://github.com/forlilab/Meeko) — Ligand PDBQT preparation from RDKit (LGPL)
- [ADFR Suite](https://ccsb.scripps.edu/adfr/downloads/) — Receptor preparation tools from Scripps (free academic license)
- [Forli et al. (2016)](https://doi.org/10.1038/nprot.2016.051) — "Computational protein-ligand docking and virtual drug screening with the AutoDock suite", *Nat Protoc*
- [RDKit documentation](https://www.rdkit.org/docs/) — Cheminformatics toolkit for ligand handling (BSD)
