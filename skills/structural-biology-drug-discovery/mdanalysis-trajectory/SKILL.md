---
name: "mdanalysis-trajectory"
description: "Analyze MD trajectories from GROMACS, AMBER, NAMD, CHARMM, LAMMPS. Reads topology/trajectory into Universe objects; supports RMSD, RMSF, radius of gyration, contact maps, H-bonds, PCA, and custom distance/angle calculations. Use for post-simulation structural analysis; use OpenMM/GROMACS for running simulations."
license: "GPL-2.0"
---

# MDAnalysis — Molecular Dynamics Trajectory Analysis

## Overview

MDAnalysis provides a uniform Python interface for reading and analyzing molecular dynamics trajectories regardless of MD engine (GROMACS, AMBER, NAMD, CHARMM, LAMMPS, OpenMM). It represents molecular systems as `Universe` objects containing an `AtomGroup` with positions, velocities, forces, and topology data. Trajectories are iterated frame-by-frame or analyzed in bulk using analysis modules for RMSD, RMSF, radius of gyration, hydrogen bonds, solvent-accessible surface area, and PCA. MDAnalysis integrates with NumPy, pandas, and matplotlib, making it the standard tool for post-simulation structural analysis in computational chemistry and drug discovery.

## When to Use

- Computing RMSD and RMSF of protein backbone or specific residue groups after MD simulation
- Analyzing ligand binding stability: pocket RMSD, contact persistence, hydrogen bond occupancy
- Performing principal component analysis (PCA) on trajectory conformations
- Computing solvent-accessible surface area (SASA), radius of gyration, and end-to-end distance
- Extracting representative cluster structures from long MD trajectories for visualization
- Use **GROMACS** or **AMBER** analysis tools (`gmx rms`, `cpptraj`) instead for engine-specific analysis within a HPC pipeline
- Use **OpenMM** or **GROMACS** directly for running MD simulations; MDAnalysis is for post-simulation analysis

## Prerequisites

- **Python packages**: `MDAnalysis`, `numpy`, `matplotlib`, `pandas`
- **Input**: topology file (.psf, .prmtop, .gro, .pdb) + trajectory file (.dcd, .trr, .xtc, .nc, .dms)

```bash
# Install MDAnalysis
pip install MDAnalysis

# Install with all analysis extras
pip install "MDAnalysis[analysis]"

# Verify
python -c "import MDAnalysis as mda; print(mda.__version__)"
# 2.7.0
```

## Quick Start

```python
import MDAnalysis as mda
import numpy as np

# Load a GROMACS topology + trajectory
u = mda.Universe("protein.gro", "trajectory.xtc")

print(f"Atoms: {u.atoms.n_atoms}")
print(f"Residues: {u.residues.n_residues}")
print(f"Frames: {u.trajectory.n_frames}")
print(f"First frame positions (first 3 atoms):\n{u.atoms.positions[:3]}")
```

## Core API

### Module 1: Universe and AtomGroup — Loading and Selecting Atoms

Load trajectories and select atom subsets.

```python
import MDAnalysis as mda

# Load topology + trajectory (GROMACS xtc format)
u = mda.Universe("system.gro", "md_production.xtc")

# AtomGroup selections (CHARMM-style selection language)
protein = u.select_atoms("protein")
backbone = u.select_atoms("backbone")
ca_atoms = u.select_atoms("name CA")
ligand = u.select_atoms("resname LIG")
binding_site = u.select_atoms("protein and around 5.0 resname LIG")

print(f"Protein atoms: {protein.n_atoms}")
print(f"CA atoms: {ca_atoms.n_atoms}")
print(f"Ligand atoms: {ligand.n_atoms}")
print(f"Binding site residues: {binding_site.residues.n_residues}")

# Access atom properties at current frame
print(f"CA positions shape: {ca_atoms.positions.shape}")  # (N, 3)
print(f"Protein mass: {protein.total_mass():.1f} Da")
```

### Module 2: Trajectory Iteration — Per-Frame Analysis

Iterate over trajectory frames for time-series analysis.

```python
import MDAnalysis as mda
import numpy as np

u = mda.Universe("protein.gro", "trajectory.xtc")
backbone = u.select_atoms("backbone")

times = []
rg_values = []

for ts in u.trajectory:
    times.append(u.trajectory.time)
    rg_values.append(backbone.radius_of_gyration())

import pandas as pd
df = pd.DataFrame({"time_ps": times, "Rg_A": rg_values})
print(f"Frames analyzed: {len(df)}")
print(f"Mean Rg: {df['Rg_A'].mean():.2f} Å")
print(f"Rg std: {df['Rg_A'].std():.2f} Å")
df.to_csv("radius_of_gyration.csv", index=False)
```

### Module 3: RMSD Analysis — Structural Drift Over Time

Compute backbone RMSD relative to a reference structure.

```python
import MDAnalysis as mda
from MDAnalysis.analysis import rms
import numpy as np
import matplotlib.pyplot as plt

u = mda.Universe("protein.gro", "trajectory.xtc")

# RMSD of Cα atoms relative to first frame
rmsd = rms.RMSD(u, select="name CA")
rmsd.run()

# Results: frame, time (ps), RMSD (Å)
results = rmsd.results.rmsd
print(f"Mean RMSD: {results[:, 2].mean():.2f} Å")
print(f"Max RMSD: {results[:, 2].max():.2f} Å")

# Plot
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(results[:, 1] / 1000, results[:, 2], color="steelblue", lw=0.8)
ax.set_xlabel("Time (ns)")
ax.set_ylabel("RMSD (Å)")
ax.set_title("Backbone RMSD")
plt.tight_layout()
plt.savefig("rmsd.png", dpi=150)
print("Saved: rmsd.png")
```

### Module 4: RMSF Analysis — Per-Residue Flexibility

Compute root-mean-square fluctuations to identify flexible regions.

```python
import MDAnalysis as mda
from MDAnalysis.analysis import rms
import numpy as np
import matplotlib.pyplot as plt

u = mda.Universe("protein.gro", "trajectory.xtc")

# RMSF per Cα atom (after aligning trajectory)
ca_atoms = u.select_atoms("name CA")
rmsf_analysis = rms.RMSF(ca_atoms)
rmsf_analysis.run()

rmsf_values = rmsf_analysis.results.rmsf
resids = ca_atoms.resids

print(f"Most flexible residue: {resids[np.argmax(rmsf_values)]} ({rmsf_values.max():.2f} Å)")
print(f"Most rigid residue:    {resids[np.argmin(rmsf_values)]} ({rmsf_values.min():.2f} Å)")

# Plot B-factor-like profile
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(resids, rmsf_values, color="coral", lw=1)
ax.fill_between(resids, 0, rmsf_values, alpha=0.3, color="coral")
ax.set_xlabel("Residue ID")
ax.set_ylabel("RMSF (Å)")
ax.set_title("Per-residue RMSF")
plt.tight_layout()
plt.savefig("rmsf.png", dpi=150)
```

### Module 5: Hydrogen Bond Analysis

Identify and count hydrogen bonds between protein and ligand over the trajectory.

```python
import MDAnalysis as mda
from MDAnalysis.analysis.hydrogenbonds import HydrogenBondAnalysis
import pandas as pd

u = mda.Universe("complex.gro", "trajectory.xtc")

# Protein-ligand hydrogen bond analysis
hbonds = HydrogenBondAnalysis(
    universe=u,
    donors_sel="protein",
    acceptors_sel="resname LIG",
    d_h_cutoff=1.2,      # donor-hydrogen distance cutoff (Å)
    d_a_cutoff=3.0,      # donor-acceptor distance cutoff (Å)
    d_h_a_angle_cutoff=150.0,  # angle cutoff (degrees)
)
hbonds.run()

# Get occupancy: fraction of frames with each H-bond
hbonds.generate_table()
df = pd.DataFrame(hbonds.table)
print(f"Total unique H-bonds observed: {len(df['donor_resid'].unique())}")

# Count H-bonds per frame
counts = hbonds.count_by_time()
print(f"Mean H-bonds per frame: {counts[:, 1].mean():.2f}")
print(f"Max H-bonds in one frame: {counts[:, 1].max():.0f}")
```

### Module 6: PCA and Conformational Clustering

Extract principal modes of motion and cluster conformations.

```python
import MDAnalysis as mda
from MDAnalysis.analysis import pca, align
import numpy as np
import matplotlib.pyplot as plt

u = mda.Universe("protein.gro", "trajectory.xtc")

# Align trajectory to first frame
aligner = align.AlignTraj(u, u, select="backbone", in_memory=True)
aligner.run()

# PCA on backbone Cα atoms
ca = u.select_atoms("name CA")
pc = pca.PCA(u, select="backbone")
pc.run()

# Explained variance
cumvar = np.cumsum(pc.results.variance / pc.results.variance.sum())
n_for_90 = np.searchsorted(cumvar, 0.90) + 1
print(f"PCs to explain 90% variance: {n_for_90}")
print(f"PC1 variance: {pc.results.variance[0] / pc.results.variance.sum() * 100:.1f}%")

# Project trajectory onto PC1-PC2 space
transformed = pc.transform(ca, n_components=2)
plt.scatter(transformed[:, 0], transformed[:, 1], c=range(len(transformed)),
            cmap="viridis", s=2)
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.colorbar(label="Frame")
plt.title("PCA Conformational Landscape")
plt.savefig("pca.png", dpi=150)
print("Saved: pca.png")
```

## Key Parameters

| Parameter | Module | Default | Effect |
|-----------|--------|---------|--------|
| `select` (Universe) | AtomGroup | — | MDAnalysis selection language string (e.g., `"protein and name CA"`) |
| `in_memory` | align.AlignTraj | `False` | Load full trajectory into RAM for faster analysis |
| `step` | trajectory loop | `1` | Analyze every Nth frame; `step=10` reduces computation 10× |
| `start/stop` | analysis.run() | all | Frame range; `run(start=100, stop=500)` analyzes frames 100-500 |
| `d_a_cutoff` | HydrogenBondAnalysis | `3.0` | Donor-acceptor distance cutoff (Å) |
| `d_h_a_angle_cutoff` | HydrogenBondAnalysis | `150.0` | H-bond angle cutoff (degrees) |
| `n_components` | PCA.transform | all | Number of PCs to project onto |
| `groupselection` | RMSD | `None` | Secondary selection for fitting; primary used for RMSD calculation |
| `weights` | RMSD/align | `None` | `"mass"` for mass-weighted RMSD |
| `verbose` | analysis.run() | `False` | Print progress bar during analysis |

## Common Workflows

### Workflow 1: Complete Protein-Ligand Binding Stability Analysis

```python
import MDAnalysis as mda
from MDAnalysis.analysis import rms, align
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

u = mda.Universe("complex.gro", "md_100ns.xtc")

# Align trajectory to initial frame
align.AlignTraj(u, u, select="protein and backbone", in_memory=True).run()

protein_bb = u.select_atoms("backbone")
ligand = u.select_atoms("resname LIG")

results = {"time_ns": [], "protein_rmsd": [], "ligand_rmsd": [], "pocket_rg": []}
ref_positions = {"protein": protein_bb.positions.copy(), "ligand": ligand.positions.copy()}

for ts in u.trajectory:
    results["time_ns"].append(ts.time / 1000)
    results["protein_rmsd"].append(
        rms.rmsd(protein_bb.positions, ref_positions["protein"], superposition=False))
    results["ligand_rmsd"].append(
        rms.rmsd(ligand.positions, ref_positions["ligand"], superposition=False))
    results["pocket_rg"].append(
        u.select_atoms("protein and around 6.0 resname LIG").radius_of_gyration())

df = pd.DataFrame(results)
df.to_csv("binding_stability.csv", index=False)
print(f"Ligand mean RMSD: {df['ligand_rmsd'].mean():.2f} Å")
print(f"Pocket stable: {'Yes' if df['pocket_rg'].std() < 0.5 else 'No'}")
```

### Workflow 2: Extract Minimum RMSD Representative Structures

```python
import MDAnalysis as mda
from MDAnalysis.analysis import rms
import numpy as np

u = mda.Universe("protein.gro", "trajectory.xtc")

# Compute RMSD for all frames
rmsd_analysis = rms.RMSD(u, select="backbone")
rmsd_analysis.run()
rmsd_values = rmsd_analysis.results.rmsd[:, 2]

# Find frame with lowest RMSD (most representative)
min_frame = np.argmin(rmsd_values)
print(f"Most representative frame: {min_frame} (RMSD: {rmsd_values[min_frame]:.2f} Å)")

# Extract and save that frame as PDB
u.trajectory[min_frame]
with mda.Writer("representative_structure.pdb", u.atoms.n_atoms) as writer:
    writer.write(u.atoms)
print("Saved: representative_structure.pdb")
```

## Common Recipes

### Recipe 1: Compute Contact Map Between Two Protein Domains

```python
import MDAnalysis as mda
from MDAnalysis.analysis import contacts
import numpy as np

u = mda.Universe("protein.gro", "trajectory.xtc")

# Define two domains
domain_A = u.select_atoms("resid 1-100 and name CA")
domain_B = u.select_atoms("resid 200-300 and name CA")

# Count domain-domain contacts (< 8 Å) over time
contact_counts = []
for ts in u.trajectory[::10]:  # every 10th frame
    dist_matrix = np.sqrt(np.sum(
        (domain_A.positions[:, None] - domain_B.positions[None, :]) ** 2, axis=-1
    ))
    contact_counts.append((dist_matrix < 8.0).sum())

print(f"Mean contacts: {np.mean(contact_counts):.1f}")
print(f"Contact count range: {min(contact_counts)} – {max(contact_counts)}")
```

### Recipe 2: Write Trajectory Subset to New File

```python
import MDAnalysis as mda

u = mda.Universe("system.gro", "long_trajectory.xtc")

# Write only protein atoms, every 10th frame, frames 500-2000
protein = u.select_atoms("protein")
with mda.Writer("protein_subset.xtc", protein.n_atoms) as writer:
    for ts in u.trajectory[500:2000:10]:
        writer.write(protein)

print(f"Subset trajectory written: {(2000-500)//10} frames")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: Universe has no file` | Missing trajectory argument | Provide both topology AND trajectory: `mda.Universe(top, traj)` |
| RMSD drift despite alignment | Wrong selection for fitting | Use `"backbone"` for fitting; verify topology matches trajectory |
| `KeyError: 'resname LIG'` | Non-standard residue name | Check `u.residues.resnames`; use exact name from topology |
| Very slow frame iteration | Large trajectory in memory | Use `step=10` to skip frames; convert xtc to smaller DCD |
| Hydrogen bond count is 0 | No explicit hydrogens in topology | Use topology with explicit H atoms; add hydrogens with `psfgen` or `tleap` |
| `NoDataError: xtc has no charges` | Property not in trajectory | Use topology file that contains charges (.psf, .prmtop, .gro with itp) |
| Memory error with `in_memory=True` | Trajectory too large for RAM | Remove `in_memory=True`; increase RAM; or process in chunks |
| Import error on Apple Silicon | Binary not compiled for arm64 | Install via conda-forge: `conda install -c conda-forge MDAnalysis` |

## References

- [MDAnalysis documentation](https://docs.mdanalysis.org/) — official API reference and user guide
- [MDAnalysis GitHub: MDAnalysis/mdanalysis](https://github.com/MDAnalysis/mdanalysis) — source code, tutorials, and issue tracker
- Michaud-Agrawal N et al. (2011) "MDAnalysis: A toolkit for the analysis of molecular dynamics simulations" — *J Comput Chem* 32:2319-2327. [DOI:10.1002/jcc.21787](https://doi.org/10.1002/jcc.21787)
- Gowers RJ et al. (2016) "MDAnalysis: A Python Package for the Rapid Analysis of Molecular Dynamics Simulations" — *Proc SciPy 2016*. [DOI:10.25080/majora-629e541a-00e](https://doi.org/10.25080/majora-629e541a-00e)
