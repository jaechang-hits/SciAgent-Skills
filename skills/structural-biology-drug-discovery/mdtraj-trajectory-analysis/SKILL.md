---
name: "mdtraj-trajectory-analysis"
description: "mdtraj molecular dynamics trajectory analysis (Python). Reads DCD/XTC/TRR/NetCDF/H5/PDB topologies and trajectories; computes RMSD vs time, radius of gyration, per-residue RMSF, residue-residue contact frequency maps, phi/psi torsions for Ramachandran plots (general + Gly/Pro), and 8-state DSSP secondary structure. Modules: trajectory I/O, geometry (distances/angles/dihedrals), structural analysis (RMSD/Rg/RMSF/SASA), contacts, hydrogen bonds, secondary structure (DSSP), NMR observables. For broader atom-selection grammar use mdanalysis-trajectory; for running MD simulations use OpenMM/GROMACS."
license: "LGPL-2.1"
---

# mdtraj Trajectory Analysis

## Overview

mdtraj is a fast, dependency-light Python library for reading, writing, and analyzing molecular dynamics (MD) trajectories. It handles every common MD format (DCD, XTC, TRR, NetCDF, H5, AMBER, GROMACS, CHARMM, OpenMM) into a single `Trajectory` object backed by NumPy arrays, then exposes geometry, RMSD/Rg/RMSF/SASA, contacts, hydrogen bonds, torsions, and 8-state DSSP secondary structure as pure-Python functions. This skill covers the analysis-side workflows: structural stability metrics, contact frequency maps, Ramachandran plots (general + Gly/Pro), and DSSP time series across multi-replicate ensembles.

> **Unit note**: mdtraj works in **nanometers** and **picoseconds** internally. Multiply distances by 10 for Ångström output. Torsions are in **radians** — convert with `np.degrees()`.

## When to Use

- Computing RMSD vs time, radius of gyration, and per-residue RMSF to assess structural stability across MD replicates
- Building residue-residue contact frequency maps from a trajectory ensemble
- Extracting backbone phi/psi torsions to plot Ramachandran diagrams (general, glycine-specific, proline-specific)
- Assigning 8-state DSSP secondary structure per residue per frame for time-series visualization
- Lightweight ad-hoc analyses where MDAnalysis's atom selection grammar or AnalysisBase framework is overkill
- NMR observables (J-couplings, chemical shifts via SHIFTX2 wrapper) directly on a trajectory
- Use `mdanalysis-trajectory` instead when you need MDAnalysis's richer selection language, AnalysisBase parallelism, or LAMMPS/NAMD-specific readers
- For running the MD simulation itself, use OpenMM or GROMACS — this skill is post-simulation analysis only

## Prerequisites

- **Python packages**: `mdtraj`, `numpy`, `pandas`, `matplotlib`, `seaborn`
- **Data**: topology (PDB / GRO / PRMTOP / PSF) + trajectory (DCD / XTC / TRR / NetCDF / H5)
- **Environment**: Python 3.9+, conda-forge build recommended for binary wheels

Check before installing — inside a pixi/conda env `mdtraj` is usually already present. Inside a pixi project invoke as `pixi run python ...`:

```bash
command -v python3 && python3 -c "import mdtraj" 2>/dev/null \
  || conda install -c conda-forge mdtraj numpy pandas matplotlib seaborn
```

## Quick Start

Load a trajectory, align to first frame, compute RMSD on alpha-carbons.

```python
import mdtraj as md
import numpy as np

traj = md.load("traj.xtc", top="topology.pdb")
ca = traj.topology.select("name CA")

traj.superpose(traj, frame=0, atom_indices=ca)
rmsd_ang = md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0  # nm -> Å

print(f"Frames: {traj.n_frames}  Residues: {traj.n_residues}")
print(f"RMSD range: {rmsd_ang.min():.2f}–{rmsd_ang.max():.2f} Å")
```

## Core API

### Module 1: Trajectory I/O

Load and write trajectories. mdtraj auto-detects format from extension.

```python
import mdtraj as md

# Load whole trajectory
traj = md.load("rep1.xtc", top="protein.pdb")

# Stream large trajectories chunk-by-chunk (avoids OOM)
chunk_rmsd = []
for chunk in md.iterload("rep1.xtc", top="protein.pdb", chunk=500):
    chunk_rmsd.append(md.rmsd(chunk, chunk, frame=0))
print(f"Total chunks: {len(chunk_rmsd)}")

# Save aligned subset
ca = traj.topology.select("name CA")
traj.atom_slice(ca).save_dcd("ca_only.dcd")
```

Selecting atoms and slicing frames:

```python
# Topology selection language (subset of VMD/MDAnalysis grammar)
backbone = traj.topology.select("backbone")
protein  = traj.topology.select("protein")
chain_a  = traj.topology.select("chainid 0")

# Frame slicing
first_ns      = traj[:1000]            # first 1000 frames
every_10th    = traj[::10]
last_half_ca  = traj[traj.n_frames // 2:].atom_slice(backbone)
print(f"Backbone-only, second half: {last_half_ca}")
```

### Module 2: RMSD, Rg, RMSF (Structural Stability)

mdtraj returns distances in nm — multiply by 10 for Å.

```python
import mdtraj as md
import numpy as np

traj = md.load("rep1.xtc", top="protein.pdb")
ca = traj.topology.select("name CA")

# RMSD vs frame 0 (after internal superposition by md.rmsd)
rmsd_ang = md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0    # Å
time_ns  = traj.time / 1000.0                                       # ps -> ns

# Radius of gyration (uses ALL atoms by default; pass masses=None for unweighted)
rg_ang   = md.compute_rg(traj) * 10.0                               # Å
print(f"<RMSD>={rmsd_ang.mean():.2f}±{rmsd_ang.std():.2f} Å,  <Rg>={rg_ang.mean():.2f} Å")
```

RMSF (per-atom or per-residue):

```python
# RMSF on CA atoms — average-structure reference
ca_traj = traj.atom_slice(ca)
ca_traj.superpose(ca_traj, frame=0)
mean_xyz = ca_traj.xyz.mean(axis=0)                                  # (n_atoms, 3)
diff     = ca_traj.xyz - mean_xyz
rmsf_nm  = np.sqrt((diff ** 2).sum(axis=2).mean(axis=0))             # per CA
rmsf_ang = rmsf_nm * 10.0
res_ids  = [a.residue.resSeq for a in ca_traj.topology.atoms]
print(f"Most flexible residue: {res_ids[np.argmax(rmsf_ang)]}  RMSF={rmsf_ang.max():.2f} Å")
```

### Module 3: Contacts and Distance Maps

Residue-residue contact distances; threshold to get contact frequency.

```python
import mdtraj as md
import numpy as np

traj = md.load("rep1.xtc", top="protein.pdb")

# Distances between every residue pair (closest heavy atom)
distances_nm, residue_pairs = md.compute_contacts(traj, contacts="all", scheme="closest-heavy")
# distances_nm: (n_frames, n_pairs);  residue_pairs: (n_pairs, 2)

# Contact frequency: fraction of frames within 0.5 nm (5 Å)
cutoff = 0.5
contact_freq = (distances_nm < cutoff).mean(axis=0)                  # (n_pairs,)

# Reshape to square matrix
n_res = traj.n_residues
freq_map = np.zeros((n_res, n_res))
for (i, j), f in zip(residue_pairs, contact_freq):
    freq_map[i, j] = freq_map[j, i] = f
print(f"Persistent contacts (>0.8): {(contact_freq > 0.8).sum()}")
```

### Module 4: Torsions (Ramachandran)

Compute phi/psi per residue per frame; mdtraj returns radians.

```python
import mdtraj as md
import numpy as np

traj = md.load("rep1.xtc", top="protein.pdb")

# md.compute_phi / compute_psi return (atom_indices, angles_rad)
phi_indices, phi_rad = md.compute_phi(traj)
psi_indices, psi_rad = md.compute_psi(traj)

# Match phi and psi by residue (phi[i] and psi[i] don't always align; intersect on residue)
def res_of(indices):
    return np.array([traj.topology.atom(ix[1]).residue.index for ix in indices])

phi_res, psi_res = res_of(phi_indices), res_of(psi_indices)
common = np.intersect1d(phi_res, psi_res)
phi_deg = np.degrees(phi_rad[:, np.isin(phi_res, common)])
psi_deg = np.degrees(psi_rad[:, np.isin(psi_res, common)])
print(f"Residues with both phi and psi: {len(common)}")
```

Filtering Ramachandran samples to Gly / Pro residues:

```python
# Residue identity for the columns above
res_names = [traj.topology.residue(r).name for r in common]
gly_cols  = [i for i, n in enumerate(res_names) if n == "GLY"]
pro_cols  = [i for i, n in enumerate(res_names) if n == "PRO"]

phi_gly, psi_gly = phi_deg[:, gly_cols].ravel(), psi_deg[:, gly_cols].ravel()
phi_pro, psi_pro = phi_deg[:, pro_cols].ravel(), psi_deg[:, pro_cols].ravel()
print(f"Gly samples: {len(phi_gly)},  Pro samples: {len(phi_pro)}")
```

### Module 5: DSSP Secondary Structure (8-state)

`md.compute_dssp(traj, simplified=False)` returns an `(n_frames, n_residues)` array of single-character DSSP codes:

| Code | Meaning            |
|------|--------------------|
| `H`  | alpha-helix        |
| `B`  | beta-bridge        |
| `E`  | beta-sheet         |
| `G`  | 3_10-helix         |
| `I`  | pi-helix           |
| `T`  | turn               |
| `S`  | bend               |
| ` ` (space) or `C` | coil |

```python
import mdtraj as md

traj = md.load("rep1.xtc", top="protein.pdb")
dssp = md.compute_dssp(traj, simplified=False)        # 8-state
# Replace whitespace with explicit 'C' for plotting
dssp[dssp == " "] = "C"
print(f"DSSP grid: {dssp.shape}  unique codes: {set(dssp.flatten())}")
```

### Module 6: Visualization Helpers (matplotlib)

mdtraj returns NumPy arrays — plotting is plain matplotlib/seaborn. Convention used across this skill:

```python
import matplotlib.pyplot as plt

# Consistent style for stability metrics
plt.rcParams.update({"figure.dpi": 120, "savefig.bbox": "tight",
                     "axes.spines.top": False, "axes.spines.right": False})

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(time_ns, rmsd_ang, lw=1, label="RMSD")
ax.set_xlabel("Time (ns)"); ax.set_ylabel("RMSD (Å)")
ax.legend(); fig.savefig("rmsd.png")
```

## Key Concepts

### Concept 1: Trajectory units (nm, ps, radians)

mdtraj stores `traj.xyz` in **nm**, `traj.time` in **ps**, and torsions in **radians**. The conversion is your responsibility before plotting:

```python
xyz_ang   = traj.xyz * 10.0
time_ns   = traj.time / 1000.0
import numpy as np
phi_deg   = np.degrees(phi_rad)
```

### Concept 2: Pair indices vs residue indices

`md.compute_contacts(..., contacts="all")` returns `(n_pairs, 2)` of **residue indices** (0-based, contiguous across chains). Reshape into a square `(n_res, n_res)` matrix before plotting heatmaps. Don't confuse with `resSeq` (PDB numbering, may have gaps and chain repeats).

### Concept 3: 8-state vs simplified DSSP

`simplified=False` → 8 states (H/B/E/G/I/T/S/' '). `simplified=True` → 3 states (H/E/C). The 8-state output is required to distinguish 3_10 (G), pi-helix (I), beta-bridge (B), bend (S), and turn (T) — collapsing to 3 states loses these signals.

## Common Workflows

### Workflow 1: Multi-Replicate Stability + Flexibility + Contacts + Ramachandran + DSSP

**Goal**: full structural-analysis report for three MD replicates — RMSD/Rg over time, per-residue RMSF, residue contact frequency map (replica 1), Ramachandran (general + Gly + Pro for replica 1), and DSSP 8-state time series (replica 1). Produces the figures described in the user's analysis brief.

```python
import mdtraj as md
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import seaborn as sns
from pathlib import Path

# --- Inputs -----------------------------------------------------------------
topology = "protein.pdb"
replicas = {
    "rep1": "rep1.xtc",
    "rep2": "rep2.xtc",
    "rep3": "rep3.xtc",
}
outdir = Path("figures"); outdir.mkdir(exist_ok=True)

# --- Load all three replicates ---------------------------------------------
trajs = {name: md.load(path, top=topology) for name, path in replicas.items()}
ca    = next(iter(trajs.values())).topology.select("name CA")

# ============================================================================
# 1. RMSD vs time + Radius of gyration (Å) for all three replicates
# ============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
colors = {"rep1": "#1f77b4", "rep2": "#ff7f0e", "rep3": "#2ca02c"}

for name, traj in trajs.items():
    traj.superpose(traj, frame=0, atom_indices=ca)
    rmsd_ang = md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0
    rg_ang   = md.compute_rg(traj) * 10.0
    t_ns     = traj.time / 1000.0
    ax1.plot(t_ns, rmsd_ang, color=colors[name], lw=1, label=name)
    ax2.plot(t_ns, rg_ang,   color=colors[name], lw=1, label=name)

ax1.set(xlabel="Time (ns)", ylabel="RMSD (Å)", title="Backbone RMSD vs reference")
ax2.set(xlabel="Time (ns)", ylabel="Rg (Å)",   title="Radius of gyration")
for ax in (ax1, ax2): ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(outdir / "01_rmsd_rg.png", dpi=200)
plt.close(fig)

# ============================================================================
# 2. Per-residue RMSF (Å) across three replicates
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 4))
for name, traj in trajs.items():
    ca_traj = traj.atom_slice(ca)
    ca_traj.superpose(ca_traj, frame=0)
    diff     = ca_traj.xyz - ca_traj.xyz.mean(axis=0)
    rmsf_ang = np.sqrt((diff ** 2).sum(axis=2).mean(axis=0)) * 10.0
    res_ids  = [a.residue.resSeq for a in ca_traj.topology.atoms]
    ax.plot(res_ids, rmsf_ang, color=colors[name], lw=1, label=name)
ax.set(xlabel="Residue", ylabel="RMSF (Å)", title="Per-residue flexibility")
ax.legend(frameon=False); fig.tight_layout()
fig.savefig(outdir / "02_rmsf.png", dpi=200); plt.close(fig)

# ============================================================================
# 3. Contact frequency map for replica 1 (white -> blue)
# ============================================================================
rep1 = trajs["rep1"]
dist_nm, pairs = md.compute_contacts(rep1, contacts="all", scheme="closest-heavy")
cutoff_nm  = 0.5                                         # 5 Å
freq       = (dist_nm < cutoff_nm).mean(axis=0)
n_res      = rep1.n_residues
freq_map   = np.zeros((n_res, n_res))
for (i, j), f in zip(pairs, freq):
    freq_map[i, j] = freq_map[j, i] = f
np.fill_diagonal(freq_map, 1.0)

cmap_contact = LinearSegmentedColormap.from_list("white_blue", ["white", "#08306b"])
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(freq_map, cmap=cmap_contact, vmin=0, vmax=1, origin="lower")
ax.set(xlabel="Residue", ylabel="Residue", title="Contact frequency (rep1, 5 Å cutoff)")
fig.colorbar(im, ax=ax, label="Fraction of frames in contact")
fig.tight_layout(); fig.savefig(outdir / "03_contact_map.png", dpi=200)
plt.close(fig)

# ============================================================================
# 4. Ramachandran (replica 1) — density colored blue (low) -> red (high)
# ============================================================================
phi_ix, phi_rad = md.compute_phi(rep1)
psi_ix, psi_rad = md.compute_psi(rep1)

def res_of(indices, traj):
    return np.array([traj.topology.atom(ix[1]).residue.index for ix in indices])

phi_res = res_of(phi_ix, rep1); psi_res = res_of(psi_ix, rep1)
common  = np.intersect1d(phi_res, psi_res)
phi_deg = np.degrees(phi_rad[:, np.isin(phi_res, common)]).ravel()
psi_deg = np.degrees(psi_rad[:, np.isin(psi_res, common)]).ravel()

cmap_density = LinearSegmentedColormap.from_list("blue_red", ["#08306b", "white", "#a50f15"])
fig, ax = plt.subplots(figsize=(5, 5))
H, xe, ye = np.histogram2d(phi_deg, psi_deg, bins=72, range=[[-180, 180], [-180, 180]])
ax.imshow(H.T, origin="lower", extent=[-180, 180, -180, 180],
          cmap=cmap_density, aspect="equal")
ax.set(xlabel=r"$\phi$ (°)", ylabel=r"$\psi$ (°)",
       title="Ramachandran (rep1) — density")
fig.tight_layout(); fig.savefig(outdir / "04_ramachandran_all.png", dpi=200)
plt.close(fig)

# ============================================================================
# 5. Glycine + proline Ramachandran (frequency-colored blue -> red)
# ============================================================================
res_names = [rep1.topology.residue(r).name for r in common]
gly_cols  = [i for i, n in enumerate(res_names) if n == "GLY"]
pro_cols  = [i for i, n in enumerate(res_names) if n == "PRO"]

for label, cols, fname in [("Glycine", gly_cols, "05_rama_gly.png"),
                           ("Proline", pro_cols, "06_rama_pro.png")]:
    if not cols:
        continue
    phi = np.degrees(phi_rad[:, cols]).ravel()
    psi = np.degrees(psi_rad[:, cols]).ravel()
    H, _, _ = np.histogram2d(phi, psi, bins=60, range=[[-180, 180], [-180, 180]])
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(H.T, origin="lower", extent=[-180, 180, -180, 180],
              cmap=cmap_density, aspect="equal")
    ax.set(xlabel=r"$\phi$ (°)", ylabel=r"$\psi$ (°)",
           title=f"{label} Ramachandran (rep1, frequency)")
    fig.tight_layout(); fig.savefig(outdir / fname, dpi=200); plt.close(fig)

# ============================================================================
# 6. DSSP 8-state time series for replica 1
# ============================================================================
dssp = md.compute_dssp(rep1, simplified=False)
dssp[dssp == " "] = "C"

dssp_colors = {
    "C": "#ffffff",  # coil — white
    "E": "#fbb4ae",  # beta-sheet — pastel red
    "B": "#000000",  # beta-bridge — black
    "S": "#ccebc5",  # bend — pastel green
    "T": "#ffffcc",  # turn — pastel yellow
    "H": "#b3cde3",  # alpha-helix — pastel blue
    "I": "#decbe4",  # pi-helix — pastel purple
    "G": "#bdbdbd",  # 3_10-helix — grey
}
codes_order = ["C", "E", "B", "S", "T", "H", "I", "G"]
code_to_int = {c: i for i, c in enumerate(codes_order)}
dssp_int    = np.vectorize(lambda c: code_to_int.get(c, 0))(dssp)    # (n_frames, n_res)

cmap_dssp = ListedColormap([dssp_colors[c] for c in codes_order])
fig, ax = plt.subplots(figsize=(10, 5))
ax.imshow(dssp_int.T, aspect="auto", cmap=cmap_dssp, vmin=-0.5, vmax=len(codes_order) - 0.5,
          origin="lower", interpolation="nearest",
          extent=[rep1.time[0] / 1000.0, rep1.time[-1] / 1000.0, 0, rep1.n_residues])
ax.set(xlabel="Time (ns)", ylabel="Residue", title="DSSP 8-state evolution (rep1)")

# Discrete legend
from matplotlib.patches import Patch
labels = {"C": "Coil", "E": "β-sheet", "B": "β-bridge", "S": "Bend",
          "T": "Turn", "H": "α-helix", "I": "π-helix", "G": "3_10-helix"}
patches = [Patch(facecolor=dssp_colors[c], edgecolor="black", label=labels[c]) for c in codes_order]
ax.legend(handles=patches, bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
fig.tight_layout(); fig.savefig(outdir / "07_dssp_8state.png", dpi=200)
plt.close(fig)

print("All figures written to figures/")
```

### Workflow 2: Hydrogen-Bond Persistence + SASA Time Series

**Goal**: classify hydrogen bonds present in >50% of frames (Baker–Hubbard) and track solvent-accessible surface area over time.

```python
import mdtraj as md
import numpy as np
import pandas as pd

traj = md.load("rep1.xtc", top="protein.pdb")

# Baker–Hubbard H-bonds: returns (n_hbonds, 3) of [donor, H, acceptor] atom indices
hbonds = md.baker_hubbard(traj, freq=0.5, periodic=False)
label  = lambda a: f"{traj.topology.atom(a).residue}-{traj.topology.atom(a).name}"
hbonds_df = pd.DataFrame({
    "donor":     [label(d) for d, _, _ in hbonds],
    "acceptor":  [label(a) for _, _, a in hbonds],
})
print(f"Persistent H-bonds (>=50% frames): {len(hbonds_df)}")

# SASA in nm^2 per residue per frame; sum residues for total
sasa_nm2 = md.shrake_rupley(traj, mode="residue")     # (n_frames, n_residues)
total_ang2 = sasa_nm2.sum(axis=1) * 100.0              # nm^2 -> Å^2
print(f"<Total SASA> = {total_ang2.mean():.0f} ± {total_ang2.std():.0f} Å²")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `chunk` (`md.iterload`) | I/O | `100` | `100`-`5000` | Frames per streamed chunk; raise for speed, lower for RAM |
| `atom_indices` (`md.rmsd`) | Stability | `None` (all) | array of ints | Restrict superposition + RMSD to subset (e.g., CA only) |
| `frame` (`md.rmsd`) | Stability | `0` | `0`-`n_frames-1` | Reference frame for RMSD |
| `contacts` (`md.compute_contacts`) | Contacts | `"all"` | `"all"`, `[(i,j),...]` | Compute every residue pair, or a custom pair list |
| `scheme` (`md.compute_contacts`) | Contacts | `"closest-heavy"` | `"ca"`, `"closest"`, `"closest-heavy"`, `"sidechain"`, `"sidechain-heavy"` | Atom subset for inter-residue distance |
| `cutoff` (contact threshold, user-defined) | Contacts | `0.5` nm | `0.4`-`0.8` nm | Distance below which pair counts as in contact (5 Å is standard for CA, 4 Å for closest-heavy) |
| `simplified` (`md.compute_dssp`) | Secondary structure | `True` | `True`/`False` | `False` returns 8-state codes; `True` returns 3-state H/E/C |
| `freq` (`md.baker_hubbard`) | H-bonds | `0.1` | `0.0`-`1.0` | Min fraction of frames an H-bond must appear to be reported |
| `mode` (`md.shrake_rupley`) | SASA | `"atom"` | `"atom"`, `"residue"` | Per-atom or summed per residue |
| `probe_radius` (`md.shrake_rupley`) | SASA | `0.14` nm | `0.12`-`0.20` nm | Solvent probe radius (1.4 Å is the convention) |
| `periodic` (geometry funcs) | Geometry | `True` | bool | Apply minimum-image convention if box info is present |

## Best Practices

1. **Always convert units before plotting**: mdtraj returns nm / ps / radians. Multiply by 10 (Å), divide by 1000 (ns), wrap in `np.degrees()` (deg). Forgetting this is the #1 cause of "my RMSD looks 10× too small".

   ```python
   rmsd_ang = md.rmsd(traj, traj, 0) * 10.0
   ```

2. **Superpose before RMSD/RMSF**: `md.rmsd` superposes internally each call. For RMSF you compute manually — call `traj.superpose(...)` first or RMSF will include rigid-body motion.

3. **Use `md.iterload` for trajectories that don't fit in RAM**: a 1 µs all-atom trajectory at 1 ps/frame is millions of frames. Streaming avoids OOM and is often faster than `md.load` for selective metrics.

4. **Don't trust `simplified=True` DSSP for fine-grained analysis**: collapsing 8 states to 3 hides 3_10 / pi-helix / bend transitions. Use `simplified=False` whenever the secondary structure signal matters.

5. **Pair indices, not `resSeq`**: `md.compute_contacts` returns **0-based residue indices** (contiguous across chains), not the PDB `resSeq`. Map back via `traj.topology.residue(i).resSeq` only when labeling.

6. **Strip waters early**: `traj = traj.atom_slice(traj.topology.select("protein"))` before downstream analysis cuts memory and speed by 5–20× on solvated systems.

## Common Recipes

### Recipe: Convert Trajectory Format

When to use: convert AMBER NetCDF to GROMACS XTC, or DCD to multi-frame PDB.

```python
import mdtraj as md

traj = md.load("input.nc", top="topology.parm7")
traj.save_xtc("output.xtc")
traj.save_pdb("output.pdb")             # whole trajectory in one multi-MODEL PDB
print(f"Converted {traj.n_frames} frames → output.xtc")
```

### Recipe: Compute Per-Residue Average RMSF Across Replicates

When to use: ensemble-averaged flexibility, used as input to flexibility-aware docking or homology refinement.

```python
import mdtraj as md
import numpy as np
import pandas as pd

paths = {"rep1": "rep1.xtc", "rep2": "rep2.xtc", "rep3": "rep3.xtc"}
top   = "protein.pdb"
rmsf_per_rep = {}

for name, p in paths.items():
    t  = md.load(p, top=top)
    ca = t.topology.select("name CA")
    ct = t.atom_slice(ca); ct.superpose(ct, frame=0)
    diff = ct.xyz - ct.xyz.mean(axis=0)
    rmsf_per_rep[name] = np.sqrt((diff ** 2).sum(axis=2).mean(axis=0)) * 10.0

df = pd.DataFrame(rmsf_per_rep)
df["mean"] = df.mean(axis=1)
df["std"]  = df.std(axis=1)
df.to_csv("rmsf_replicates.csv", index_label="residue_index")
print(df.head())
```

### Recipe: Save Only Frames Where RMSD > Threshold

When to use: cluster late conformational states or build a curated set of "open" conformations.

```python
import mdtraj as md

traj = md.load("rep1.xtc", top="protein.pdb")
ca   = traj.topology.select("name CA")
traj.superpose(traj, frame=0, atom_indices=ca)
rmsd_ang = md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0

open_state = traj[rmsd_ang > 4.0]                  # frames with RMSD > 4 Å
open_state.save_dcd("open_state.dcd")
print(f"Saved {open_state.n_frames}/{traj.n_frames} frames as open state")
```

### Recipe: Cross-Replicate DSSP Helix Fraction

When to use: quantitative summary of secondary structure stability across replicates.

```python
import mdtraj as md
import numpy as np

paths = ["rep1.xtc", "rep2.xtc", "rep3.xtc"]
top   = "protein.pdb"
helix_fracs = []
for p in paths:
    t = md.load(p, top=top)
    dssp = md.compute_dssp(t, simplified=False)
    helix_fracs.append((dssp == "H").mean())
print(f"α-helix fraction per replicate: {[f'{h:.2f}' for h in helix_fracs]}")
print(f"Mean ± std: {np.mean(helix_fracs):.2f} ± {np.std(helix_fracs):.2f}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `RuntimeError: No topology` | Trajectory format (XTC/DCD/TRR) carries no topology | Pass `top="protein.pdb"` or `top="topology.prmtop"` to `md.load` |
| RMSD values 10× too small | mdtraj returns nm, not Å | Multiply by `10.0` before plotting/reporting |
| RMSF spikes at termini | Termini have higher intrinsic flexibility; not a bug | Slice them off (`ct.atom_slice(ct.topology.select("residue 2 to -2"))`) or report explicitly |
| `md.compute_dssp` returns only `H/E/C` | `simplified=True` is the default | Pass `simplified=False` for 8-state output |
| Empty DSSP cells / `' '` codes | Spaces represent coil — they aren't missing | Replace with `'C'` before plotting: `dssp[dssp == " "] = "C"` |
| Memory error on large trajectory | Whole trajectory loaded into RAM | Switch to `md.iterload(path, top=top, chunk=500)` |
| Phi/psi arrays have different residue counts | First residue has no phi; last has no psi | Intersect the residue index sets before pairing |
| Ramachandran plot off-center | Forgot `np.degrees(...)`; angles are radians | Wrap with `np.degrees` and set `range=[[-180, 180], [-180, 180]]` in `histogram2d` |
| `md.compute_contacts` returns NaNs | Some pairs lack heavy atoms for `closest-heavy` (e.g., glycine sidechain) | Use `scheme="closest"` or `"ca"`; drop NaN columns before plotting |
| Contact-map heatmap is asymmetric | Only filled the upper triangle | Mirror with `freq_map[j, i] = freq_map[i, j]` after filling |
| Trajectory has no `time` array | Some writers store every step as `time=0` | Reconstruct: `traj.time = np.arange(traj.n_frames) * dt_ps` |

## Related Skills

- **mdanalysis-trajectory** — alternative trajectory library with richer atom-selection grammar and the AnalysisBase framework
- **autodock-vina-docking** / **smina-molecular-docking** — feed representative frames from MD as docking targets
- **opentargets-database** / **chembl-database-bioactivity** — fetch ligand bioactivity to overlay on MD-derived flexibility maps

## References

- [mdtraj documentation](https://mdtraj.org/) — official docs, API reference, tutorials
- [McGibbon et al. (2015)](https://doi.org/10.1016/j.bpj.2015.08.015) — "MDTraj: A Modern Open Library for the Analysis of Molecular Dynamics Trajectories", *Biophys J*
- [DSSP algorithm](https://doi.org/10.1002/bip.360221211) — Kabsch & Sander (1983) "Dictionary of protein secondary structure"
- [Baker–Hubbard H-bond criterion](https://doi.org/10.1016/S0006-3495(99)77244-7) — Baker & Hubbard (1984) "Hydrogen bonding in globular proteins"
- [Shrake–Rupley SASA](https://doi.org/10.1016/0022-2836(73)90011-9) — Shrake & Rupley (1973) "Environment and exposure to solvent of protein atoms"
- [mdtraj on GitHub](https://github.com/mdtraj/mdtraj) — source, issue tracker, examples
