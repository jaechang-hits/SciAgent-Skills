---
name: "diffdock"
description: "DiffDock is a diffusion-based molecular docking tool that predicts protein-ligand binding poses without requiring a predefined binding site. Use it when the binding site is unknown, when traditional docking fails, or when exploring multiple binding modes. Pipeline: prepare protein (PDB) and ligand (SMILES/SDF) inputs → run DiffDock inference → analyze confidence-ranked poses → visualize in PyMOL or NGLview."
license: "MIT"
---

# diffdock

## Overview

DiffDock uses a diffusion generative model to predict protein-ligand binding poses directly from protein structure and ligand SMILES, treating docking as a generative rather than a search problem. Unlike traditional docking tools (AutoDock Vina, Glide), DiffDock does not require a predefined binding site — it samples poses across the full protein surface. It outputs a ranked set of binding poses with associated confidence scores. DiffDock excels at blind docking tasks and produces diverse pose hypotheses, making it valuable for de novo binding site discovery and challenging targets.

## When to Use

- **Blind docking (unknown binding site)**: You do not know where on the protein the ligand binds and want to discover candidate binding sites.
- **Challenging targets that fail traditional docking**: Allosteric sites, flexible regions, or proteins without a co-crystal structure in the target binding site.
- **Exploring multiple binding modes**: Generating a diverse ensemble of poses to understand conformational flexibility in the binding event.
- **Structure-activity relationship (SAR) exploration**: Rapidly docking a series of analogs to compare predicted binding modes.
- **Fragment screening hypothesis generation**: Identifying plausible binding sites for fragment molecules.
- For known binding sites with rigid protein assumptions, AutoDock Vina or GNINA may be faster and equally accurate.
- For large-scale virtual screening (>10,000 compounds), consider GNINA or DiffDock-L (the large-scale version) rather than standard DiffDock.

## Prerequisites

- **Python packages**: `diffdock` (conda install recommended), `rdkit`, `torch`, `biopython`, `nglview` (visualization)
- **System**: GPU strongly recommended (NVIDIA CUDA); CPU inference is slow (~5-10 min/compound)
- **Data requirements**: Protein PDB file (cleaned, protonated), ligand as SMILES string or SDF file
- **Environment**: conda environment with CUDA-compatible PyTorch

```bash
# Recommended: clone and install from source
git clone https://github.com/gcorso/DiffDock.git
cd DiffDock
conda create -n diffdock python=3.9
conda activate diffdock
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

# Download pretrained model weights
python -c "from utils.download import download_pretrained; download_pretrained()"
```

## Workflow

### Step 1: Prepare the Protein Structure

```python
from Bio import PDB
from Bio.PDB import PDBParser, PDBIO, Select

class NonHetSelect(Select):
    """Remove HETATM records (ligands, water) — keep only protein atoms."""
    def accept_residue(self, residue):
        return residue.id[0] == " "

def clean_pdb(input_pdb: str, output_pdb: str):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein", input_pdb)
    io = PDBIO()
    io.set_structure(structure)
    io.save(output_pdb, NonHetSelect())
    print(f"Cleaned PDB saved to: {output_pdb}")

clean_pdb("raw_protein.pdb", "protein_clean.pdb")
```

### Step 2: Prepare the Ligand Input

```python
from rdkit import Chem
from rdkit.Chem import AllChem, SDWriter

def smiles_to_sdf(smiles: str, output_sdf: str, n_confs: int = 1):
    """Convert SMILES to 3D SDF for DiffDock input."""
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    AllChem.MMFFOptimizeMolecule(mol)
    writer = SDWriter(output_sdf)
    writer.write(mol)
    writer.close()
    print(f"Ligand SDF written to: {output_sdf}")
    return mol

# Example: ibuprofen
smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
mol    = smiles_to_sdf(smiles, "ligand.sdf")
print(f"Ligand formula: {Chem.rdMolDescriptors.CalcMolFormula(mol)}")
```

### Step 3: Run DiffDock Inference

```bash
# Command-line inference (run from the DiffDock directory)
python inference.py \
    --protein_path protein_clean.pdb \
    --ligand       "CC(C)Cc1ccc(cc1)C(C)C(=O)O" \
    --out_dir      results/ \
    --inference_steps 20 \
    --samples_per_complex 40 \
    --batch_size 10 \
    --no_final_step_noise
```

```python
import subprocess

def run_diffdock(protein_pdb: str, ligand_smiles: str, out_dir: str,
                 n_samples: int = 40, n_steps: int = 20):
    cmd = [
        "python", "inference.py",
        "--protein_path",      protein_pdb,
        "--ligand",            ligand_smiles,
        "--out_dir",           out_dir,
        "--inference_steps",   str(n_steps),
        "--samples_per_complex", str(n_samples),
        "--batch_size",        "10",
        "--no_final_step_noise",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="DiffDock/")
    if result.returncode == 0:
        print(f"DiffDock complete. Results in: {out_dir}")
    else:
        print(f"Error: {result.stderr}")
    return result

run_diffdock("protein_clean.pdb", "CC(C)Cc1ccc(cc1)C(C)C(=O)O", "results/")
```

### Step 4: Parse and Rank Confidence Scores

```python
import re
from pathlib import Path
import pandas as pd

def parse_diffdock_results(out_dir: str) -> pd.DataFrame:
    """Parse DiffDock output SDF files and confidence scores."""
    out_path = Path(out_dir)
    records  = []

    # DiffDock names output files: rank{N}_confidence{score}.sdf
    for sdf_file in sorted(out_path.glob("rank*_confidence*.sdf")):
        name = sdf_file.stem
        # Extract rank and confidence from filename
        rank_match = re.search(r"rank(\d+)", name)
        conf_match = re.search(r"confidence(-?[\d.]+)", name)
        if rank_match and conf_match:
            records.append({
                "rank":       int(rank_match.group(1)),
                "confidence": float(conf_match.group(1)),
                "sdf_file":   str(sdf_file),
            })

    df = pd.DataFrame(records).sort_values("rank")
    print(f"Found {len(df)} poses")
    print(df[["rank", "confidence", "sdf_file"]].head(10))
    return df

df_results = parse_diffdock_results("results/")
```

### Step 5: Analyze Top Poses — Extract Binding Site Residues

```python
from rdkit import Chem
from rdkit.Chem import AllChem
from Bio.PDB import PDBParser
import numpy as np

def get_binding_residues(protein_pdb: str, ligand_sdf: str, cutoff_angstrom: float = 4.0):
    """Find protein residues within cutoff distance of the top-ranked ligand pose."""
    parser    = PDBParser(QUIET=True)
    structure = parser.get_structure("prot", protein_pdb)
    prot_atoms = [(atom.get_coord(), residue.resname, residue.id[1])
                  for chain in structure for residue in chain
                  for atom in residue.get_atoms()]

    mol = Chem.SDMolSupplier(ligand_sdf, removeHs=False)[0]
    lig_coords = mol.GetConformer().GetPositions()

    contacts = []
    for prot_coord, resname, resnum in prot_atoms:
        dists = np.linalg.norm(lig_coords - prot_coord, axis=1)
        if dists.min() <= cutoff_angstrom:
            contacts.append((resnum, resname))

    contacts = sorted(set(contacts))
    print(f"Binding site residues within {cutoff_angstrom} A: {contacts[:10]}")
    return contacts

# Use top-ranked pose
top_sdf = df_results.loc[df_results.rank == 1, "sdf_file"].iloc[0]
contacts = get_binding_residues("protein_clean.pdb", top_sdf)
```

### Step 6: Visualize Poses in NGLview

```python
import nglview as nv
from rdkit import Chem

# Load protein + top pose in Jupyter notebook
view = nv.NGLWidget()
view.add_pdbfile("protein_clean.pdb")

top_sdf  = df_results.loc[df_results.rank == 1, "sdf_file"].iloc[0]
view.add_component(top_sdf)
view.representations = [
    {"type": "cartoon", "params": {"color": "chainindex"}},
    {"type": "ball+stick", "params": {"sele": "ligand"}},
]
print(f"Visualizing top pose: confidence={df_results.confidence.iloc[0]:.3f}")
view
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `--inference_steps` | `20` | `10`–`40` | Number of diffusion reverse steps; more steps = slower but more accurate |
| `--samples_per_complex` | `40` | `10`–`100` | Number of poses sampled; more = better coverage of binding modes |
| `--batch_size` | `10` | `1`–`32` | GPU batch size; reduce if OOM error |
| `--no_final_step_noise` | off | flag | Removes noise at last diffusion step; improves pose quality |
| `--actual_steps` | equals `inference_steps` | `1`–`inference_steps` | Steps to actually run (can be fewer than total) |
| `--save_visualisation` | off | flag | Also saves PDB visualization files alongside SDF |
| `cutoff_angstrom` | `4.0` | `3.0`–`6.0` Å | Distance cutoff for defining binding site residues |

## Common Recipes

### Recipe: Batch Docking of Multiple Ligands

When to use: Dock a library of analogs to the same protein for SAR analysis.

```python
import pandas as pd
import subprocess

smiles_list = [
    ("compound_1", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
    ("compound_2", "CC(C)Cc1ccc(cc1)C(C)C(=O)N"),
    ("compound_3", "CC(C)Cc1ccc(cc1)C(C)C(=O)OC"),
]

results = []
for name, smiles in smiles_list:
    out = f"results/{name}"
    cmd = ["python", "inference.py",
           "--protein_path", "protein_clean.pdb",
           "--ligand", smiles,
           "--out_dir", out,
           "--inference_steps", "20",
           "--samples_per_complex", "20"]
    subprocess.run(cmd, cwd="DiffDock/", capture_output=True)
    # Parse top confidence score
    df_r = parse_diffdock_results(out)
    if not df_r.empty:
        top_conf = df_r.loc[df_r.rank == 1, "confidence"].iloc[0]
        results.append({"name": name, "smiles": smiles, "top_confidence": top_conf})

df_batch = pd.DataFrame(results).sort_values("top_confidence", ascending=False)
df_batch.to_csv("batch_docking_results.csv", index=False)
print(df_batch)
```

### Recipe: Filter Poses by Confidence Threshold

When to use: Keep only high-confidence poses for further analysis or visualization.

```python
# Confidence > 0 generally indicates a plausible binding pose
# DiffDock confidence scores: higher = more confident; ~0 is marginal; < -1 is poor
high_conf = df_results[df_results["confidence"] > 0.0]
print(f"High-confidence poses: {len(high_conf)} / {len(df_results)}")
print(high_conf[["rank", "confidence", "sdf_file"]])
```

### Recipe: Convert Top Pose to PDBQT for Rescoring with Vina

When to use: Rescore DiffDock poses with AutoDock Vina's energy function.

```bash
# Convert SDF to PDBQT using OpenBabel
obabel rank1_confidence0.75.sdf -O rank1_ligand.pdbqt
obabel protein_clean.pdb -O protein.pdbqt -xr

# Rescore (no docking search, just energy evaluation)
vina --receptor protein.pdbqt --ligand rank1_ligand.pdbqt \
     --score_only --out rank1_rescored.pdbqt
```

## Expected Outputs

- `results/rank{N}_confidence{score}.sdf` — 3D ligand poses ranked by confidence score
- `df_results` DataFrame with rank, confidence score, and file path per pose
- Binding site residues list (residue numbers and names within cutoff distance)
- NGLview interactive 3D visualization in Jupyter notebooks

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `CUDA out of memory` | Batch size too large for GPU | Reduce `--batch_size` to `4` or `2` |
| Empty results directory | Protein PDB parsing failed | Ensure PDB contains only ATOM records; remove HETATM with `clean_pdb()` |
| All confidence scores < -2 | Ligand or protein format issue | Validate SMILES with RDKit; ensure protein is protonated and complete |
| Very slow inference (>30 min) | Running on CPU | GPU is strongly recommended; CUDA environment must be correctly configured |
| `ModuleNotFoundError: e3nn` | Dependency not installed | `pip install e3nn` in the DiffDock conda environment |
| Poses cluster at one site | Low `--samples_per_complex` | Increase to `40`–`100` for better site coverage |
| Protein missing residues | Incomplete crystal structure | Use MODELLER or Swiss-Model to fill gaps before docking |

## References

- [DiffDock GitHub (gcorso/DiffDock)](https://github.com/gcorso/DiffDock) — source code, installation, and pretrained weights
- [Corso et al. (2023), ICLR — DiffDock paper](https://arxiv.org/abs/2210.01776) — original diffusion docking publication
- [DiffDock web server](https://huggingface.co/spaces/reginabarzilaygroup/DiffDock-Web) — browser-based inference without local installation
- [PatentsView API Documentation](https://patentsview.org/apis/api-endpoints/patents) — for IP analysis context
