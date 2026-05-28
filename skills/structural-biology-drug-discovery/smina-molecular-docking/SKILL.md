---
name: "smina-molecular-docking"
description: "smina molecular docking CLI. AutoDock Vina fork with customizable scoring functions, native SDF/MOL2/PDB ligand input, autoboxing, local energy minimization, and per-atom score breakdowns. Pipeline: receptor PDBQT prep -> ligand prep (RDKit/OpenBabel) -> dock via autobox or explicit grid -> rescore/minimize with custom scoring -> rank poses by affinity. Choose smina over Vina when you need custom scoring terms (--custom_scoring), local optimization of an existing pose (--local_only), per-atom contributions (--atom_term_data), or SDF/MOL2 ligands without manual PDBQT conversion. For unknown binding sites use diffdock-blind-docking; for the Python-bindings/Vinardo workflow use autodock-vina-docking."
license: "GPL-2.0"
---

# smina Molecular Docking

## Overview

smina is an AutoDock Vina 1.1.2 fork focused on flexible scoring and minimization. Accepts SDF/MOL2/PDB ligands directly (no manual PDBQT), autoboxes from a reference ligand, ships six built-in scoring functions plus arbitrary `--custom_scoring` terms, and prints per-atom score contributions. CLI-only — drive from Python via `subprocess`.

## When to Use

- Re-scoring or locally minimizing an existing pose (`--local_only`, `--minimize`) without a full search
- Single-pose binding energy without docking (`--score_only`)
- Docking with a custom or empirical scoring function tuned to a target class
- SDF/MOL2/multi-ligand input without per-ligand PDBQT conversion
- Autoboxing the grid around a co-crystallized reference ligand
- Per-atom energy decomposition (`--atom_term_data`) for medchem analog design
- Batch virtual screening that parallelizes well across nodes (one CLI process per ligand)
- Use **autodock-vina-docking** instead when you need Vina Python bindings, Vinardo scoring, or Vina 1.2's expanded force field; use **diffdock-blind-docking** when the binding site is unknown

## Prerequisites

- **smina binary** — conda-forge or SourceForge build
- **Python**: `rdkit`, `openbabel-wheel` (or system `openbabel`), `prody`, `pandas`, `py3Dmol`
- **ADFR Suite** for `prepare_receptor` (receptor PDBQT only — ligands handled by smina)
- **Data**: protein (PDB / PDB ID), ligand(s) as SMILES / SDF / MOL2

Check before installing — inside a pixi/conda env smina is usually already on PATH. If `command -v smina` succeeds, skip install; inside a pixi project invoke as `pixi run smina ...`.

```bash
command -v smina || conda install -c conda-forge smina openbabel
pip install rdkit prody pandas py3Dmol
# ADFR Suite: https://ccsb.scripps.edu/adfr/downloads/
```

## Quick Start

End-to-end docking using autobox from a reference ligand:

```python
import subprocess

result = subprocess.run([
    "smina",
    "-r", "1hpv_receptor.pdbqt",
    "-l", "candidate.sdf",
    "--autobox_ligand", "1hpv_ref_ligand.pdb",
    "--autobox_add", "8",          # padding around reference (Å)
    "-o", "candidate_docked.sdf",
    "--exhaustiveness", "16",
    "--num_modes", "9",
    "--seed", "42",
], check=True, capture_output=True, text=True)

print(result.stdout.splitlines()[-15:])  # affinity table at stdout tail
```

## Workflow

### Step 1: Prepare the Receptor (PDBQT)

Strip waters/hetatms, then run ADFR Suite's `prepare_receptor`.

```python
import subprocess, prody

pdb_id = "1HPV"
prody.fetchPDB(pdb_id, compressed=False)
protein = prody.parsePDB(f"{pdb_id}.pdb").select("protein")
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

### Step 2: Prepare the Ligand (SDF)

smina reads SDF directly. Generate 3D coords with RDKit.

```python
from rdkit import Chem
from rdkit.Chem import AllChem

mol = Chem.MolFromSmiles("CC(C)(C)NC(=O)[C@@H]1CN(CCc2ccccc2)C[C@H]1O")
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, randomSeed=42)
AllChem.MMFFOptimizeMolecule(mol)

w = Chem.SDWriter("candidate.sdf"); w.write(mol); w.close()
print(f"Ligand SDF: candidate.sdf ({mol.GetNumAtoms()} atoms)")
```

### Step 3: Extract a Reference Ligand for Autoboxing

`--autobox_ligand` derives the grid from a reference structure.

```python
import prody

ref = prody.parsePDB(f"{pdb_id}.pdb").select("hetero and not water and not ion")
if ref is None:
    raise RuntimeError("No reference ligand — supply explicit --center_x/--size_x")
prody.writePDB(f"{pdb_id}_ref_ligand.pdb", ref)
print(f"Ref ligand: {ref.numAtoms()} atoms, center {ref.getCoords().mean(axis=0).round(2)}")
```

### Step 4: Run Docking with Autobox

Affinity table is printed to stdout — capture it.

```python
import subprocess

proc = subprocess.run([
    "smina",
    "-r", receptor_pdbqt,
    "-l", "candidate.sdf",
    "--autobox_ligand", f"{pdb_id}_ref_ligand.pdb",
    "--autobox_add", "8",
    "-o", "candidate_docked.sdf",
    "--exhaustiveness", "16",
    "--num_modes", "9",
    "--energy_range", "3",
    "--cpu", "4",
    "--seed", "42",
], check=True, capture_output=True, text=True)

for line in proc.stdout.splitlines()[-15:]:
    print(line)
```

### Step 5: Parse Poses and Affinities

Affinities go into the SDF `<minimizedAffinity>` property.

```python
from rdkit import Chem
import pandas as pd

rows = []
for i, mol in enumerate(Chem.SDMolSupplier("candidate_docked.sdf", removeHs=False)):
    if mol is None:
        continue
    aff = float(mol.GetProp("minimizedAffinity")) if mol.HasProp("minimizedAffinity") else None
    rmsd = float(mol.GetProp("minimizedRMSD")) if mol.HasProp("minimizedRMSD") else None
    rows.append({"pose": i + 1, "affinity_kcal_mol": aff, "rmsd_to_best": rmsd})

df = pd.DataFrame(rows).sort_values("affinity_kcal_mol")
print(df.to_string(index=False))
print(f"Best: {df.iloc[0]['affinity_kcal_mol']:.2f} kcal/mol")
```

### Step 6: Local Minimization of an Existing Pose

`--local_only` refines an input pose without global search.

```python
import subprocess

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

with open(f"{pdb_id}_protein.pdb") as f: rec = f.read()
with open("candidate_docked.sdf") as f: lig = f.read()

view = py3Dmol.view(width=800, height=600)
view.addModel(rec, "pdb"); view.setStyle({"model": 0}, {"cartoon": {}})
view.addModel(lig.split("$$$$")[0] + "$$$$", "sdf")
view.setStyle({"model": 1}, {"stick": {}})
view.zoomTo({"model": 1}); view.show()
```

### Step 8: Batch Virtual Screening

One smina process per ligand parallelizes well across cores or cluster nodes.

```python
import subprocess, pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

library = pd.DataFrame({
    "name":   ["cpd_001", "cpd_002", "cpd_003"],
    "smiles": ["CC(=O)Oc1ccccc1C(=O)O",
               "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
               "OC(=O)c1ccccc1O"],
})

results = []
for _, row in library.iterrows():
    lig_sdf, out_sdf = f"{row['name']}.sdf", f"{row['name']}_docked.sdf"
    mol = Chem.MolFromSmiles(row["smiles"]); mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, randomSeed=42); AllChem.MMFFOptimizeMolecule(mol)
    w = Chem.SDWriter(lig_sdf); w.write(mol); w.close()

    proc = subprocess.run([
        "smina", "-r", receptor_pdbqt, "-l", lig_sdf,
        "--autobox_ligand", f"{pdb_id}_ref_ligand.pdb", "--autobox_add", "8",
        "-o", out_sdf, "--exhaustiveness", "8", "--num_modes", "1",
        "--cpu", "2", "--seed", "42",
    ], capture_output=True, text=True)

    if proc.returncode != 0:
        results.append({"name": row["name"], "affinity_kcal_mol": None})
        continue
    docked = next(iter(Chem.SDMolSupplier(out_sdf, removeHs=False)))
    aff = float(docked.GetProp("minimizedAffinity")) if docked and docked.HasProp("minimizedAffinity") else None
    results.append({"name": row["name"], "affinity_kcal_mol": aff})

ranked = pd.DataFrame(results).sort_values("affinity_kcal_mol")
ranked.to_csv("screening_results.csv", index=False)
print(ranked.to_string(index=False))
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `--exhaustiveness` | `8` | `1`-`128` | MC search effort; 16-32 production, 64+ publication |
| `--num_modes` | `9` | `1`-`20` | Poses written to output SDF |
| `--energy_range` | `3` | `1`-`5` kcal/mol | Max ΔE from best pose in output |
| `--scoring` | `default` | `default`, `vina`, `vinardo`, `dkoes_scoring`, `dkoes_scoring_old`, `ad4_scoring` | Built-in scoring (default ≈ Vina) |
| `--custom_scoring` | — | path | User-defined weighted terms; overrides `--scoring` |
| `--autobox_ligand` | — | PDB/SDF path | Derive grid from reference |
| `--autobox_add` | `4` | `2`-`12` Å | Padding around autobox extent |
| `--center_x/y/z`, `--size_x/y/z` | — | Å | Manual grid (alternative to autobox) |
| `--local_only` | off | flag | Skip global search; local optimization only |
| `--score_only` | off | flag | Energy without minimization or search |
| `--minimize` | off | flag | Energy-minimize without scoring search |
| `--minimize_iters` | `0` (auto) | `0`-`100000` | Local minimizer iterations |
| `--atom_term_data` | off | flag | Per-atom score contributions in output |
| `--cpu` | all | `1`-`N` | Threads per job |
| `--seed` | random | int | RNG seed for reproducibility |
| `--no_lig` | off | flag | Score receptor-only as baseline |

## Common Recipes

### Recipe: Score-Only (Single-Point Energy)

Compare pose energy between scoring functions without re-docking.

```python
import subprocess

proc = subprocess.run([
    "smina", "-r", "receptor.pdbqt", "-l", "pose.sdf",
    "--score_only", "--scoring", "vinardo",   # try vina, vinardo, dkoes_scoring
], capture_output=True, text=True, check=True)

for line in proc.stdout.splitlines():
    if line.startswith("Affinity:"):
        print(line)
```

### Recipe: Custom Scoring Function

Target-class-tuned empirical scoring; reproduce dkoes terms or a custom-fit set.

```python
import subprocess

with open("my_scoring.txt", "w") as f:
    f.write("""\
-0.035579    gauss(o=0,_w=0.5,_c=8)
-0.005156    gauss(o=3,_w=2,_c=8)
0.840245     repulsion(o=0,_c=8)
-0.035069    hydrophobic(g=0.5,_b=1.5,_c=8)
-0.587439    non_dir_h_bond(g=-0.7,_b=0,_c=8)
1.923        num_tors_div
""")

subprocess.run([
    "smina", "-r", "receptor.pdbqt", "-l", "candidate.sdf",
    "--custom_scoring", "my_scoring.txt",
    "--autobox_ligand", "ref.pdb", "--autobox_add", "8",
    "-o", "custom_docked.sdf", "--exhaustiveness", "16",
], check=True)
```

### Recipe: Per-Atom Score Decomposition

Identify which ligand atoms drive binding.

```python
import subprocess
from rdkit import Chem

subprocess.run([
    "smina", "-r", "receptor.pdbqt", "-l", "pose.sdf",
    "--score_only", "--atom_term_data", "-o", "pose_decomp.sdf",
], check=True)

mol = next(iter(Chem.SDMolSupplier("pose_decomp.sdf", removeHs=False)))
for prop in mol.GetPropNames():
    if "atom_term" in prop:
        print(f"{prop}: {mol.GetProp(prop)[:120]}")
```

### Recipe: Re-Docking Validation

Re-dock the co-crystallized ligand; confirm RMSD < 2.0 Å.

```python
import subprocess
from rdkit import Chem
from rdkit.Chem import AllChem

subprocess.run([
    "smina", "-r", "receptor.pdbqt", "-l", "ref_ligand.sdf",
    "--autobox_ligand", "ref_ligand.sdf", "--autobox_add", "8",
    "-o", "redocked.sdf", "--exhaustiveness", "32",
    "--num_modes", "1", "--seed", "42",
], check=True)

ref = next(iter(Chem.SDMolSupplier("ref_ligand.sdf", removeHs=False)))
docked = next(iter(Chem.SDMolSupplier("redocked.sdf", removeHs=False)))
rmsd = AllChem.GetBestRMS(ref, docked)
print(f"Re-docking RMSD: {rmsd:.2f} Å  ->  {'PASS' if rmsd < 2.0 else 'FAIL'}")
```

## Expected Outputs

- `*_docked.sdf` — multi-model SDF, one molecule per pose; affinity in `<minimizedAffinity>`, RMSD-to-best in `<minimizedRMSD>`
- `screening_results.csv` — name, SMILES, affinity (kcal/mol)
- `*_receptor.pdbqt` — prepared receptor
- stdout — affinity table: pose, affinity (kcal/mol), rmsd lower/upper bound

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `smina: command not found` | Binary not on PATH | `conda install -c conda-forge smina`; in pixi env use `pixi run smina` |
| `Parse error on line ...` (ligand) | Malformed SDF/MOL2 | Re-export with RDKit `SDWriter` after `AddHs` + `EmbedMolecule` |
| `Could not figure out box dimensions` | Missing both `--autobox_ligand` and `--center_x/--size_x` | Supply autobox reference or explicit grid |
| Highly positive affinities (>0) | Ligand outside grid or steric clash on input | Raise `--autobox_add`; verify reference pose is inside binding site |
| `--local_only` returns input unchanged | `--minimize_iters 0` = "no minimization" in some builds | Set `--minimize_iters 1000` explicitly |
| Identical poses across runs | Fixed `--seed` + low `--exhaustiveness` | Raise to 32+; vary `--seed` for ensemble |
| Receptor PDBQT generation fails | `prepare_receptor` not on PATH | Install ADFR Suite, add `<adfr>/bin` to PATH |
| Empty SDF after dock | smina aborted silently | Drop `capture_output`, inspect `proc.stderr`; check receptor charges |
| Score differs between `--score_only` and `--local_only` | Local opt moves the pose | Expected — score-only for fixed pose, local-only for refined energy |
| `--custom_scoring` file rejected | Term typo or missing weight column | Each line: `<weight><whitespace><term_name(args)>` — whitespace strict |
| Per-atom decomposition empty | Used with `--minimize` / dock, not `--score_only` | `--atom_term_data` most reliable with `--score_only` |

## References

- [smina on SourceForge](https://sourceforge.net/projects/smina/) — original distribution
- [smina GitHub mirror](https://github.com/mwojcikowski/smina) — maintained builds
- [Koes, Baumgartner, Camacho (2013)](https://doi.org/10.1021/ci300604z) — smina + dkoes scoring paper, *J Chem Inf Model*
- [Trott & Olson (2010)](https://doi.org/10.1002/jcc.21334) — upstream Vina paper, *J Comput Chem*
- [ADFR Suite](https://ccsb.scripps.edu/adfr/downloads/) — `prepare_receptor` for receptor PDBQT
- [RDKit documentation](https://www.rdkit.org/docs/) — ligand 3D generation and SDF I/O
- [Open Babel](https://openbabel.org/docs/) — alternative ligand format conversion
