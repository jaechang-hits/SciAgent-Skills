---
name: "smina-molecular-docking"
description: "smina molecular docking CLI. AutoDock Vina fork with customizable scoring functions, native SDF/MOL2/PDB ligand input, autoboxing, local energy minimization, and per-atom score breakdowns. Pipeline: receptor PDBQT prep -> ligand prep (RDKit/OpenBabel) -> dock via autobox or explicit grid -> rescore/minimize with custom scoring -> rank poses by affinity. Choose smina over Vina when you need custom scoring terms (--custom_scoring), local optimization of an existing pose (--local_only), per-atom contributions (--atom_term_data), or SDF/MOL2 ligands without manual PDBQT conversion. For unknown binding sites use diffdock-blind-docking; for the Python-bindings/Vinardo workflow use autodock-vina-docking."
license: "GPL-2.0"
---

# smina Molecular Docking

## Overview

smina is a fork of AutoDock Vina 1.1.2 (David Koes, University of Pittsburgh) focused on flexible scoring and minimization. It accepts SDF/MOL2/PDB ligands directly (no manual PDBQT conversion), supports autoboxing from a reference ligand, exposes six built-in scoring functions and arbitrary user-defined terms via `--custom_scoring`, and prints per-atom score contributions. The tool is CLI-only; this skill drives it from Python via `subprocess`, with RDKit + OpenBabel for ligand prep and ADFR Suite (`prepare_receptor`) for receptor PDBQT generation.

## When to Use

- Re-scoring or locally minimizing an existing protein–ligand pose (`--local_only`, `--minimize`) without running a full conformational search
- Computing a single-pose binding energy estimate without docking (`--score_only`)
- Running a docking protocol with a custom or empirical scoring function tuned on your target class
- Docking from SDF/MOL2/multi-ligand files without converting each ligand to PDBQT manually
- Autoboxing the search grid around a co-crystallized reference ligand instead of supplying explicit center/size
- Getting per-atom energy decomposition (`--atom_term_data`) to interpret which ligand atoms drive binding
- Batch virtual screening when you want a single self-contained CLI process per ligand (easier to parallelize across nodes than the Python API)
- Use **autodock-vina-docking** instead when you need the Vina Python bindings, Vinardo scoring, or Vina 1.2's expanded force field; use **diffdock-blind-docking** when the binding site is unknown

## Prerequisites

- **smina binary**: install via conda-forge (or download from SourceForge / build from source)
- **Python packages**: `rdkit`, `openbabel-wheel` (or system `openbabel`), `prody`, `pandas`, `py3Dmol`
- **External tools**: `ADFR Suite` for `prepare_receptor` (receptor PDBQT). Ligands can go in as SDF/MOL2/PDB — smina handles them internally.
- **Data**: protein structure (PDB / PDB ID), ligand(s) as SMILES / SDF / MOL2

Before installing, check whether `smina` is already on PATH (it usually is inside a pixi or conda env). If `command -v smina` succeeds, skip the install step. Inside a pixi project invoke as `pixi run smina ...` to use the pinned binary.

```bash
# Check first; install only if missing
command -v smina || conda install -c conda-forge smina openbabel
pip install rdkit prody pandas py3Dmol
# ADFR Suite ships prepare_receptor — install separately
# https://ccsb.scripps.edu/adfr/downloads/
```

## Quick Start

Minimal end-to-end docking using autobox from a reference ligand (no explicit grid coordinates needed):

```python
import subprocess
from pathlib import Path

# Inputs: receptor PDBQT, reference ligand PDB (for autobox), candidate ligand SDF
receptor = "1hpv_receptor.pdbqt"
ref_lig  = "1hpv_ref_ligand.pdb"
ligand   = "candidate.sdf"
out      = "candidate_docked.sdf"

result = subprocess.run([
    "smina",
    "-r", receptor,
    "-l", ligand,
    "--autobox_ligand", ref_lig,
    "--autobox_add", "8",          # 8 Å padding around reference
    "-o", out,
    "--exhaustiveness", "16",
    "--num_modes", "9",
    "--seed", "42",
], check=True, capture_output=True, text=True)

print(result.stdout.splitlines()[-15:])  # affinity table at end of stdout
print(f"Docked poses: {out}")
```

## Workflow

### Step 1: Prepare the Receptor (PDBQT)

smina requires receptor in PDBQT. Use ADFR Suite's `prepare_receptor` after stripping waters/hetatms.

```python
import subprocess
import prody

pdb_id = "1HPV"
prody.fetchPDB(pdb_id, compressed=False)
structure = prody.parsePDB(f"{pdb_id}.pdb")

# Save protein-only PDB (no water, no ligand, no ion)
protein = structure.select("protein")
prody.writePDB(f"{pdb_id}_protein.pdb", protein)

receptor_pdbqt = f"{pdb_id}_receptor.pdbqt"
subprocess.run([
    "prepare_receptor",
    "-r", f"{pdb_id}_protein.pdb",
    "-o", receptor_pdbqt,
    "-A", "hydrogens",
], check=True)
print(f"Receptor: {receptor_pdbqt} ({protein.numAtoms()} atoms)")
```

### Step 2: Prepare the Ligand (SDF, no manual PDBQT)

Unlike Vina, smina reads SDF/MOL2 directly. Generate 3D coordinates with RDKit and write SDF — smina handles the rest.

```python
from rdkit import Chem
from rdkit.Chem import AllChem

smiles = "CC(C)(C)NC(=O)[C@@H]1CN(CCc2ccccc2)C[C@H]1O"  # example
mol = Chem.MolFromSmiles(smiles)
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, randomSeed=42)
AllChem.MMFFOptimizeMolecule(mol)

writer = Chem.SDWriter("candidate.sdf")
writer.write(mol)
writer.close()
print(f"Ligand SDF: candidate.sdf ({mol.GetNumAtoms()} atoms)")
```

### Step 3: Extract a Reference Ligand for Autoboxing

smina's `--autobox_ligand` derives the grid from a reference structure. Pull the co-crystallized ligand out of the original PDB.

```python
import prody

structure = prody.parsePDB(f"{pdb_id}.pdb")
ref = structure.select("hetero and not water and not ion")
if ref is None:
    raise RuntimeError("No reference ligand in PDB — supply explicit --center_x/--size_x")

prody.writePDB(f"{pdb_id}_ref_ligand.pdb", ref)
center = ref.getCoords().mean(axis=0)
print(f"Reference ligand: {ref.numAtoms()} atoms, center {center.round(2)}")
```

### Step 4: Run Docking with Autobox

Drive smina via `subprocess`. Capture stdout — the affinity table is printed there, not just in the output SDF.

```python
import subprocess

cmd = [
    "smina",
    "-r", receptor_pdbqt,
    "-l", "candidate.sdf",
    "--autobox_ligand", f"{pdb_id}_ref_ligand.pdb",
    "--autobox_add", "8",            # padding (Å) on each side of reference
    "-o", "candidate_docked.sdf",
    "--exhaustiveness", "16",
    "--num_modes", "9",
    "--energy_range", "3",
    "--cpu", "4",
    "--seed", "42",
]
proc = subprocess.run(cmd, check=True, capture_output=True, text=True)

# Affinity table appears at end of stdout
for line in proc.stdout.splitlines()[-15:]:
    print(line)
```

### Step 5: Parse Poses and Affinities from Output SDF

smina writes affinity into the SDF `<minimizedAffinity>` and `<CNNscore>`-style tags. Read them with RDKit.

```python
from rdkit import Chem
import pandas as pd

suppl = Chem.SDMolSupplier("candidate_docked.sdf", removeHs=False)
rows = []
for i, mol in enumerate(suppl):
    if mol is None:
        continue
    aff = mol.GetProp("minimizedAffinity") if mol.HasProp("minimizedAffinity") else None
    rmsd_lb = mol.GetProp("minimizedRMSD") if mol.HasProp("minimizedRMSD") else None
    rows.append({"pose": i + 1, "affinity_kcal_mol": float(aff) if aff else None,
                 "rmsd_to_best": float(rmsd_lb) if rmsd_lb else None})

df = pd.DataFrame(rows).sort_values("affinity_kcal_mol")
print(df.to_string(index=False))
print(f"Best: {df.iloc[0]['affinity_kcal_mol']:.2f} kcal/mol")
```

### Step 6: Local Minimization of an Existing Pose

When you already have a candidate pose (from MD, manual placement, or another docker), use `--local_only` to refine it without a global search.

```python
import subprocess

# minimize_only_iters set via --minimize; --local_only runs the local search
subprocess.run([
    "smina",
    "-r", receptor_pdbqt,
    "-l", "candidate_pose.sdf",
    "--autobox_ligand", "candidate_pose.sdf",   # box around the pose itself
    "--autobox_add", "4",
    "-o", "candidate_min.sdf",
    "--local_only",
    "--minimize_iters", "1000",
], check=True, capture_output=True, text=True)
print("Local minimization complete: candidate_min.sdf")
```

### Step 7: Visualize the Docked Complex

```python
import py3Dmol

with open(f"{pdb_id}_protein.pdb") as f:
    rec = f.read()
with open("candidate_docked.sdf") as f:
    lig = f.read()

view = py3Dmol.view(width=800, height=600)
view.addModel(rec, "pdb")
view.setStyle({"model": 0}, {"cartoon": {"color": "lightgrey"}})

# First docked pose (first molecule block in SDF)
first_pose = lig.split("$$$$")[0] + "$$$$"
view.addModel(first_pose, "sdf")
view.setStyle({"model": 1}, {"stick": {"colorscheme": "cyanCarbon"}})
view.zoomTo({"model": 1})
view.show()
print("3D view rendered")
```

### Step 8: Batch Virtual Screening

Single smina process per ligand parallelizes well across cores or cluster nodes. Concatenate SMILES into one SDF, then loop.

```python
import subprocess
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

library = pd.DataFrame({
    "name":   ["cpd_001", "cpd_002", "cpd_003"],
    "smiles": [
        "CC(=O)Oc1ccccc1C(=O)O",
        "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "OC(=O)c1ccccc1O",
    ],
})

results = []
for _, row in library.iterrows():
    lig_sdf = f"{row['name']}.sdf"
    out_sdf = f"{row['name']}_docked.sdf"

    mol = Chem.MolFromSmiles(row["smiles"])
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, randomSeed=42)
    AllChem.MMFFOptimizeMolecule(mol)
    w = Chem.SDWriter(lig_sdf); w.write(mol); w.close()

    proc = subprocess.run([
        "smina",
        "-r", receptor_pdbqt,
        "-l", lig_sdf,
        "--autobox_ligand", f"{pdb_id}_ref_ligand.pdb",
        "--autobox_add", "8",
        "-o", out_sdf,
        "--exhaustiveness", "8",
        "--num_modes", "1",
        "--cpu", "2",
        "--seed", "42",
    ], capture_output=True, text=True)

    if proc.returncode != 0:
        results.append({"name": row["name"], "affinity_kcal_mol": None, "error": proc.stderr[-200:]})
        continue

    docked = next(iter(Chem.SDMolSupplier(out_sdf, removeHs=False)))
    aff = float(docked.GetProp("minimizedAffinity")) if docked and docked.HasProp("minimizedAffinity") else None
    results.append({"name": row["name"], "affinity_kcal_mol": aff, "error": None})

ranked = pd.DataFrame(results).sort_values("affinity_kcal_mol")
ranked.to_csv("screening_results.csv", index=False)
print(ranked.to_string(index=False))
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `--exhaustiveness` | `8` | `1`-`128` | Monte Carlo search effort; 16–32 for production, 64+ for publication |
| `--num_modes` | `9` | `1`-`20` | Number of poses written to output SDF |
| `--energy_range` | `3` | `1`-`5` (kcal/mol) | Max ΔE from best pose included in output |
| `--scoring` | `default` | `default`, `vina`, `vinardo`, `dkoes_scoring`, `dkoes_scoring_old`, `ad4_scoring` | Built-in scoring function (`default` ≈ Vina) |
| `--custom_scoring` | — | path to terms file | User-defined weighted terms; overrides `--scoring` |
| `--autobox_ligand` | — | PDB/SDF path | Derive grid from reference structure |
| `--autobox_add` | `4` | `2`-`12` (Å) | Padding added around autobox extent |
| `--center_x/y/z`, `--size_x/y/z` | — | Å | Manual grid placement (alternative to autobox) |
| `--local_only` | off | flag | Skip global search; only local optimization of input pose |
| `--score_only` | off | flag | Compute energy without minimization or search |
| `--minimize` | off | flag | Energy-minimize ligand without scoring search |
| `--minimize_iters` | `0` (auto) | `0`-`100000` | Max iterations for local minimizer |
| `--atom_term_data` | off | flag | Print per-atom score contributions in output SDF |
| `--cpu` | all cores | `1`-`N` | Threads per dock job |
| `--seed` | random | any int | RNG seed for reproducible docking |
| `--no_lig` | off | flag | Allow scoring receptor-only as reference baseline |

## Common Recipes

### Recipe: Score-Only (Single-Point Energy)

When to use: comparing the binding energy of a pose between scoring functions without re-docking.

```python
import subprocess

proc = subprocess.run([
    "smina",
    "-r", "receptor.pdbqt",
    "-l", "pose.sdf",
    "--score_only",
    "--scoring", "vinardo",       # try vina, vinardo, dkoes_scoring
], capture_output=True, text=True, check=True)

# Affinity line: "## Name Affinity Intramolecular ...
for line in proc.stdout.splitlines():
    if line.startswith("Affinity:"):
        print(line)
```

### Recipe: Custom Scoring Function

When to use: target class for which a tuned empirical scoring set outperforms defaults; reproducing the dkoes scoring family or a custom-fit set from your own benchmark.

```python
# 1. Write the terms file
custom_terms = """\
-0.035579    gauss(o=0,_w=0.5,_c=8)
-0.005156    gauss(o=3,_w=2,_c=8)
0.840245     repulsion(o=0,_c=8)
-0.035069    hydrophobic(g=0.5,_b=1.5,_c=8)
-0.587439    non_dir_h_bond(g=-0.7,_b=0,_c=8)
1.923        num_tors_div
"""
with open("my_scoring.txt", "w") as f:
    f.write(custom_terms)

import subprocess
subprocess.run([
    "smina",
    "-r", "receptor.pdbqt",
    "-l", "candidate.sdf",
    "--custom_scoring", "my_scoring.txt",
    "--autobox_ligand", "ref.pdb", "--autobox_add", "8",
    "-o", "custom_docked.sdf",
    "--exhaustiveness", "16",
], check=True)
```

### Recipe: Per-Atom Score Decomposition

When to use: interpreting which ligand atoms drive binding affinity (medchem analog design).

```python
import subprocess
from rdkit import Chem

subprocess.run([
    "smina",
    "-r", "receptor.pdbqt",
    "-l", "pose.sdf",
    "--score_only",
    "--atom_term_data",
    "-o", "pose_decomp.sdf",
], check=True)

# Per-atom terms appear in SDF properties (e.g., 'atom_term_0', 'atom_term_1', ...)
mol = next(iter(Chem.SDMolSupplier("pose_decomp.sdf", removeHs=False)))
for prop in mol.GetPropNames():
    if "atom_term" in prop:
        print(f"{prop}: {mol.GetProp(prop)[:120]}")
```

### Recipe: Re-Docking Validation

When to use: protocol validation — re-dock the co-crystallized ligand and confirm RMSD < 2.0 Å.

```python
import subprocess
from rdkit import Chem
from rdkit.Chem import AllChem

# Dock the reference ligand back into the receptor
subprocess.run([
    "smina",
    "-r", "receptor.pdbqt",
    "-l", "ref_ligand.sdf",
    "--autobox_ligand", "ref_ligand.sdf",
    "--autobox_add", "8",
    "-o", "redocked.sdf",
    "--exhaustiveness", "32",
    "--num_modes", "1",
    "--seed", "42",
], check=True)

ref     = next(iter(Chem.SDMolSupplier("ref_ligand.sdf", removeHs=False)))
docked  = next(iter(Chem.SDMolSupplier("redocked.sdf",   removeHs=False)))
rmsd    = AllChem.GetBestRMS(ref, docked)
print(f"Re-docking RMSD: {rmsd:.2f} Å  ->  {'PASS' if rmsd < 2.0 else 'FAIL'}")
```

## Expected Outputs

- `*_docked.sdf` — multi-model SDF with one molecule per pose; affinities in `<minimizedAffinity>` property, RMSD-to-best in `<minimizedRMSD>`
- `screening_results.csv` — tabular: name, SMILES, affinity (kcal/mol)
- `*_receptor.pdbqt` — PDBQT receptor ready for repeated docking
- stdout — affinity table: pose index, affinity (kcal/mol), rmsd lower bound, rmsd upper bound
- Optional 3D visualization (py3Dmol interactive view or HTML export)

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `smina: command not found` | Binary not on PATH | `conda install -c conda-forge smina` or use full path; in pixi env run `pixi run smina ...` |
| `Parse error on line ...` in ligand | Malformed SDF/MOL2 | Re-export with RDKit `SDWriter` after `Chem.AddHs` + `EmbedMolecule` |
| `Could not figure out box dimensions` | Missing both `--autobox_ligand` and `--center_x/--size_x` | Supply either autobox reference or explicit grid coords |
| Highly positive affinities (>0) | Ligand outside grid or steric clash on input pose | Increase `--autobox_add`; verify reference pose is inside binding site |
| `--local_only` returns input pose unchanged | `--minimize_iters 0` interpreted as "no minimization" in some builds | Set `--minimize_iters 1000` explicitly |
| Identical poses across runs | `--seed` fixed but `--exhaustiveness` too low | Increase `--exhaustiveness` to 32+; vary `--seed` for ensemble |
| Receptor PDBQT generation fails | `prepare_receptor` not in PATH | Install ADFR Suite and add `<adfr>/bin` to PATH |
| SDF output empty after dock | smina aborted silently | Re-run without `capture_output` or inspect `proc.stderr`; check receptor charges |
| Different affinity between `--score_only` and `--local_only` | Local opt moves the pose; score-only does not | Expected — report score-only for fixed-pose comparison, local-only for refined energy |
| `--custom_scoring` file rejected | Term name typo or missing weight column | Each line must be `<weight><whitespace><term_name(args)>`; whitespace strict |
| Per-atom decomposition empty | Used with `--minimize` or `--dock`, not `--score_only` | `--atom_term_data` is most reliable with `--score_only` |

## References

- [smina on SourceForge](https://sourceforge.net/projects/smina/) — original distribution, source, and binary releases
- [smina GitHub mirror](https://github.com/mwojcikowski/smina) — actively maintained fork with builds
- [Koes, Baumgartner, Camacho (2013)](https://doi.org/10.1021/ci300604z) — "Lessons Learned in Empirical Scoring with smina from the CSAR 2011 Benchmarking Exercise", *J Chem Inf Model* (smina + dkoes scoring paper)
- [Trott & Olson (2010)](https://doi.org/10.1002/jcc.21334) — "AutoDock Vina: improving the speed and accuracy of docking", *J Comput Chem* (upstream Vina paper)
- [ADFR Suite](https://ccsb.scripps.edu/adfr/downloads/) — provides `prepare_receptor` for receptor PDBQT
- [RDKit documentation](https://www.rdkit.org/docs/) — ligand 3D generation and SDF I/O (BSD)
- [Open Babel](https://openbabel.org/docs/) — alternative ligand format conversion (GPL-2.0)
