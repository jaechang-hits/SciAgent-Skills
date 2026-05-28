---
name: "mdtraj-trajectory-analysis"
description: "mdtraj molecular dynamics trajectory analysis (Python). Reads DCD/XTC/TRR/NetCDF/H5/PDB topologies and trajectories; computes RMSD vs time, radius of gyration, per-residue RMSF, residue-residue contact frequency maps, phi/psi torsions for Ramachandran plots (general + Gly/Pro), and 8-state DSSP secondary structure. Modules: trajectory I/O, geometry (distances/angles/dihedrals), structural analysis (RMSD/Rg/RMSF/SASA), contacts, hydrogen bonds, secondary structure (DSSP), NMR observables. For broader atom-selection grammar use mdanalysis-trajectory; for running MD simulations use OpenMM/GROMACS."
license: "LGPL-2.1"
---

# mdtraj Trajectory Analysis

## Overview

mdtraj is a dependency-light Python library for analyzing MD trajectories. Reads DCD/XTC/TRR/NetCDF/H5/AMBER/GROMACS/CHARMM/OpenMM into a `Trajectory` object backed by NumPy arrays, then exposes geometry, RMSD/Rg/RMSF/SASA, contacts, hydrogen bonds, torsions, and 8-state DSSP as pure-Python functions.

> **Units**: mdtraj uses **nm** and **ps** internally. Multiply distances by 10 for Å, divide time by 1000 for ns. Torsions are in **radians** — `np.degrees()`.

## When to Use

- RMSD vs time, Rg, per-residue RMSF for stability across MD replicates
- Residue-residue contact frequency maps from a trajectory ensemble
- Backbone phi/psi for Ramachandran (general, Gly, Pro)
- 8-state DSSP per residue per frame for secondary-structure time series
- Lightweight ad-hoc analyses where MDAnalysis's full framework is overkill
- NMR observables (J-couplings, chemical shifts via SHIFTX2)
- Use **mdanalysis-trajectory** instead when you need MDAnalysis's selection grammar, AnalysisBase parallelism, or LAMMPS/NAMD-specific readers
- Use **OpenMM/GROMACS** to *run* the simulation — this skill is post-simulation only

## Prerequisites

- `mdtraj`, `numpy`, `pandas`, `matplotlib`
- Topology (PDB/GRO/PRMTOP/PSF) + trajectory (DCD/XTC/TRR/NetCDF/H5)
- Python 3.9+, conda-forge build recommended

Check before installing — inside a pixi/conda env mdtraj is usually present:

```bash
python3 -c "import mdtraj" 2>/dev/null || conda install -c conda-forge mdtraj numpy pandas matplotlib
```

## Quick Start

```python
import mdtraj as md

traj = md.load("traj.xtc", top="topology.pdb")
ca = traj.topology.select("name CA")
traj.superpose(traj, frame=0, atom_indices=ca)

rmsd_ang = md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0  # nm -> Å
print(f"Frames: {traj.n_frames}  RMSD: {rmsd_ang.min():.2f}–{rmsd_ang.max():.2f} Å")
```

## Core API

### Module 1: Trajectory I/O

Load whole or streamed. Format auto-detected from extension.

```python
import mdtraj as md

traj = md.load("rep1.xtc", top="protein.pdb")

# Stream large trajectories — avoids OOM
for chunk in md.iterload("rep1.xtc", top="protein.pdb", chunk=500):
    rmsd_chunk = md.rmsd(chunk, chunk, frame=0)

# Save subset
ca = traj.topology.select("name CA")
traj.atom_slice(ca).save_dcd("ca_only.dcd")
```

Selecting atoms and slicing frames:

```python
backbone = traj.topology.select("backbone")
chain_a  = traj.topology.select("chainid 0")

first_ns      = traj[:1000]
every_10th    = traj[::10]
last_half_bb  = traj[traj.n_frames // 2:].atom_slice(backbone)
```

### Module 2: RMSD, Rg, RMSF

`md.rmsd` superposes internally; RMSF you compute manually after explicit superpose.

```python
import mdtraj as md, numpy as np

traj = md.load("rep1.xtc", top="protein.pdb")
ca = traj.topology.select("name CA")

rmsd_ang = md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0    # Å
rg_ang   = md.compute_rg(traj) * 10.0                              # Å
time_ns  = traj.time / 1000.0
print(f"<RMSD>={rmsd_ang.mean():.2f} Å,  <Rg>={rg_ang.mean():.2f} Å")
```

```python
# Per-CA RMSF — average-structure reference
ca_traj = traj.atom_slice(ca)
ca_traj.superpose(ca_traj, frame=0)
diff     = ca_traj.xyz - ca_traj.xyz.mean(axis=0)
rmsf_ang = np.sqrt((diff ** 2).sum(axis=2).mean(axis=0)) * 10.0
res_ids  = [a.residue.resSeq for a in ca_traj.topology.atoms]
print(f"Max RMSF: residue {res_ids[np.argmax(rmsf_ang)]} = {rmsf_ang.max():.2f} Å")
```

### Module 3: Contacts and Distance Maps

Threshold distances to get contact frequency.

```python
import mdtraj as md, numpy as np

traj = md.load("rep1.xtc", top="protein.pdb")
distances_nm, pairs = md.compute_contacts(traj, contacts="all", scheme="closest-heavy")
# distances_nm: (n_frames, n_pairs);  pairs: (n_pairs, 2) of residue indices

contact_freq = (distances_nm < 0.5).mean(axis=0)                  # 5 Å cutoff
n_res    = traj.n_residues
freq_map = np.zeros((n_res, n_res))
for (i, j), f in zip(pairs, contact_freq):
    freq_map[i, j] = freq_map[j, i] = f
print(f"Persistent contacts (>0.8): {(contact_freq > 0.8).sum()}")
```

### Module 4: Torsions (Ramachandran)

phi/psi returned in radians; intersect on residue since first residue has no phi and last has no psi.

```python
import mdtraj as md, numpy as np

traj = md.load("rep1.xtc", top="protein.pdb")
phi_ix, phi_rad = md.compute_phi(traj)
psi_ix, psi_rad = md.compute_psi(traj)

def res_of(indices): return np.array([traj.topology.atom(ix[1]).residue.index for ix in indices])
phi_res, psi_res = res_of(phi_ix), res_of(psi_ix)
common  = np.intersect1d(phi_res, psi_res)
phi_deg = np.degrees(phi_rad[:, np.isin(phi_res, common)])
psi_deg = np.degrees(psi_rad[:, np.isin(psi_res, common)])
```

Filter to Gly / Pro residues:

```python
res_names = [traj.topology.residue(r).name for r in common]
gly_cols  = [i for i, n in enumerate(res_names) if n == "GLY"]
pro_cols  = [i for i, n in enumerate(res_names) if n == "PRO"]
phi_gly, psi_gly = phi_deg[:, gly_cols].ravel(), psi_deg[:, gly_cols].ravel()
phi_pro, psi_pro = phi_deg[:, pro_cols].ravel(), psi_deg[:, pro_cols].ravel()
```

### Module 5: DSSP Secondary Structure (8-state)

`md.compute_dssp(traj, simplified=False)` returns `(n_frames, n_residues)` of one-character codes:

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
dssp = md.compute_dssp(traj, simplified=False)
dssp[dssp == " "] = "C"
print(f"DSSP grid: {dssp.shape}  unique codes: {set(dssp.flatten())}")
```

### Module 6: Hydrogen Bonds and SASA

```python
import mdtraj as md
import pandas as pd

traj = md.load("rep1.xtc", top="protein.pdb")

# Baker–Hubbard: returns (n_hbonds, 3) of [donor, H, acceptor] atom indices
hbonds = md.baker_hubbard(traj, freq=0.5, periodic=False)
label  = lambda a: f"{traj.topology.atom(a).residue}-{traj.topology.atom(a).name}"
hbonds_df = pd.DataFrame({"donor": [label(d) for d, _, _ in hbonds],
                         "acceptor": [label(a) for _, _, a in hbonds]})

# SASA in nm^2 per residue per frame
sasa_nm2 = md.shrake_rupley(traj, mode="residue")
total_ang2 = sasa_nm2.sum(axis=1) * 100.0                # nm^2 -> Å^2
print(f"Persistent H-bonds: {len(hbonds_df)},  <SASA>: {total_ang2.mean():.0f} Å²")
```

## Key Concepts

### Units (nm, ps, radians)

`traj.xyz` is in nm, `traj.time` in ps, torsions in radians. Convert before plotting:

```python
import numpy as np
xyz_ang  = traj.xyz * 10.0
time_ns  = traj.time / 1000.0
phi_deg  = np.degrees(phi_rad)
```

### Pair indices vs `resSeq`

`md.compute_contacts(..., contacts="all")` returns **0-based residue indices** (contiguous across chains), not PDB `resSeq`. Reshape into `(n_res, n_res)` before heatmaps. Map back via `traj.topology.residue(i).resSeq` only when labeling.

### 8-state vs simplified DSSP

`simplified=False` → 8 states. `simplified=True` → 3 states (H/E/C), which loses 3_10 (G), pi-helix (I), beta-bridge (B), bend (S), turn (T).

## Common Workflows

### Workflow 1: Multi-Replicate Stability + Flexibility + Contacts + Ramachandran + DSSP

**Goal**: structural-analysis report for three MD replicates — RMSD/Rg over time, per-residue RMSF, residue contact frequency map (rep1), Ramachandran general + Gly + Pro (rep1), DSSP 8-state time series (rep1). Plots use matplotlib defaults; the consumer picks palette downstream.

```python
import mdtraj as md, numpy as np, matplotlib.pyplot as plt
from pathlib import Path

replicas = {"rep1": "rep1.xtc", "rep2": "rep2.xtc", "rep3": "rep3.xtc"}
topology = "protein.pdb"
outdir = Path("figures"); outdir.mkdir(exist_ok=True)

trajs = {name: md.load(p, top=topology) for name, p in replicas.items()}
ca    = next(iter(trajs.values())).topology.select("name CA")

# 1. RMSD vs time + Rg (Å) for all replicates
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
for name, traj in trajs.items():
    traj.superpose(traj, frame=0, atom_indices=ca)
    ax1.plot(traj.time / 1000.0, md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0, lw=1, label=name)
    ax2.plot(traj.time / 1000.0, md.compute_rg(traj) * 10.0, lw=1, label=name)
ax1.set(xlabel="Time (ns)", ylabel="RMSD (Å)", title="Backbone RMSD")
ax2.set(xlabel="Time (ns)", ylabel="Rg (Å)",   title="Radius of gyration")
for ax in (ax1, ax2): ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(outdir / "01_rmsd_rg.png"); plt.close(fig)

# 2. Per-residue RMSF (Å) across replicates
fig, ax = plt.subplots(figsize=(10, 4))
for name, traj in trajs.items():
    ct = traj.atom_slice(ca); ct.superpose(ct, frame=0)
    rmsf = np.sqrt(((ct.xyz - ct.xyz.mean(axis=0)) ** 2).sum(axis=2).mean(axis=0)) * 10.0
    ax.plot([a.residue.resSeq for a in ct.topology.atoms], rmsf, lw=1, label=name)
ax.set(xlabel="Residue", ylabel="RMSF (Å)", title="Per-residue flexibility")
ax.legend(frameon=False); fig.tight_layout()
fig.savefig(outdir / "02_rmsf.png"); plt.close(fig)

# 3. Contact frequency map (rep1, 5 Å cutoff)
rep1 = trajs["rep1"]
dist_nm, pairs = md.compute_contacts(rep1, contacts="all", scheme="closest-heavy")
freq = (dist_nm < 0.5).mean(axis=0)
freq_map = np.zeros((rep1.n_residues, rep1.n_residues))
for (i, j), f in zip(pairs, freq):
    freq_map[i, j] = freq_map[j, i] = f
np.fill_diagonal(freq_map, 1.0)
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(freq_map, vmin=0, vmax=1, origin="lower")
ax.set(xlabel="Residue", ylabel="Residue", title="Contact frequency (rep1)")
fig.colorbar(im, ax=ax, label="Fraction of frames in contact")
fig.tight_layout(); fig.savefig(outdir / "03_contact_map.png"); plt.close(fig)

# 4. Ramachandran (rep1) — phi/psi 2D density
phi_ix, phi_rad = md.compute_phi(rep1)
psi_ix, psi_rad = md.compute_psi(rep1)
def res_of(ix, t): return np.array([t.topology.atom(i[1]).residue.index for i in ix])
phi_res, psi_res = res_of(phi_ix, rep1), res_of(psi_ix, rep1)
common = np.intersect1d(phi_res, psi_res)
phi_deg = np.degrees(phi_rad[:, np.isin(phi_res, common)]).ravel()
psi_deg = np.degrees(psi_rad[:, np.isin(psi_res, common)]).ravel()
H, _, _ = np.histogram2d(phi_deg, psi_deg, bins=72, range=[[-180, 180], [-180, 180]])
fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(H.T, origin="lower", extent=[-180, 180, -180, 180], aspect="equal")
ax.set(xlabel=r"$\phi$ (°)", ylabel=r"$\psi$ (°)", title="Ramachandran (rep1)")
fig.tight_layout(); fig.savefig(outdir / "04_ramachandran_all.png"); plt.close(fig)

# 5. Glycine + proline Ramachandran
res_names = [rep1.topology.residue(r).name for r in common]
for label, cols, fname in [("Glycine", [i for i, n in enumerate(res_names) if n == "GLY"], "05_rama_gly.png"),
                           ("Proline", [i for i, n in enumerate(res_names) if n == "PRO"], "06_rama_pro.png")]:
    if not cols: continue
    phi = np.degrees(phi_rad[:, cols]).ravel()
    psi = np.degrees(psi_rad[:, cols]).ravel()
    H, _, _ = np.histogram2d(phi, psi, bins=60, range=[[-180, 180], [-180, 180]])
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(H.T, origin="lower", extent=[-180, 180, -180, 180], aspect="equal")
    ax.set(xlabel=r"$\phi$ (°)", ylabel=r"$\psi$ (°)", title=f"{label} Ramachandran (rep1)")
    fig.tight_layout(); fig.savefig(outdir / fname); plt.close(fig)

# 6. DSSP 8-state time series (rep1)
dssp = md.compute_dssp(rep1, simplified=False); dssp[dssp == " "] = "C"
codes_order = ["C", "E", "B", "S", "T", "H", "I", "G"]
code_to_int = {c: i for i, c in enumerate(codes_order)}
dssp_int = np.vectorize(lambda c: code_to_int.get(c, 0))(dssp)
fig, ax = plt.subplots(figsize=(10, 5))
ax.imshow(dssp_int.T, aspect="auto", origin="lower", interpolation="nearest",
          extent=[rep1.time[0] / 1000.0, rep1.time[-1] / 1000.0, 0, rep1.n_residues])
ax.set(xlabel="Time (ns)", ylabel="Residue", title="DSSP 8-state (rep1)")
fig.tight_layout(); fig.savefig(outdir / "07_dssp_8state.png"); plt.close(fig)

# Dump DSSP code mapping so downstream code can pick its own legend/palette
np.savez(outdir / "07_dssp_8state.npz", dssp=dssp, dssp_int=dssp_int, codes_order=codes_order)
print("All figures written to figures/")
```

### Workflow 2: H-Bond Persistence + SASA Across Replicates

**Goal**: persistent hydrogen bonds (≥50% of frames) and total SASA time series per replicate.

```python
import mdtraj as md, numpy as np, pandas as pd

replicas = {"rep1": "rep1.xtc", "rep2": "rep2.xtc", "rep3": "rep3.xtc"}
top = "protein.pdb"
rows = []
for name, p in replicas.items():
    t = md.load(p, top=top)
    hbonds = md.baker_hubbard(t, freq=0.5, periodic=False)
    sasa_ang2 = (md.shrake_rupley(t, mode="residue").sum(axis=1) * 100.0)
    rows.append({"replica": name, "n_persistent_hbonds": len(hbonds),
                 "sasa_mean_ang2": sasa_ang2.mean(), "sasa_std_ang2": sasa_ang2.std()})
print(pd.DataFrame(rows).to_string(index=False))
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `chunk` (`md.iterload`) | I/O | `100` | `100`-`5000` | Frames per stream chunk; trade speed vs RAM |
| `atom_indices` (`md.rmsd`) | Stability | `None` | array of ints | Restrict superposition + RMSD (e.g., CA only) |
| `frame` (`md.rmsd`) | Stability | `0` | `0`-`n_frames-1` | Reference frame |
| `contacts` (`md.compute_contacts`) | Contacts | `"all"` | `"all"`, `[(i,j),...]` | All residue pairs or custom list |
| `scheme` (`md.compute_contacts`) | Contacts | `"closest-heavy"` | `"ca"`, `"closest"`, `"closest-heavy"`, `"sidechain"`, `"sidechain-heavy"` | Atom subset for inter-residue distance |
| `cutoff` (contact threshold, user-set) | Contacts | `0.5` nm | `0.4`-`0.8` nm | In-contact distance (5 Å for CA, 4 Å for closest-heavy) |
| `simplified` (`md.compute_dssp`) | DSSP | `True` | `True`/`False` | `False` → 8-state codes |
| `freq` (`md.baker_hubbard`) | H-bonds | `0.1` | `0.0`-`1.0` | Min frame fraction to report |
| `mode` (`md.shrake_rupley`) | SASA | `"atom"` | `"atom"`, `"residue"` | Per-atom or summed per residue |
| `probe_radius` (`md.shrake_rupley`) | SASA | `0.14` nm | `0.12`-`0.20` nm | Solvent probe (1.4 Å standard) |
| `periodic` (geometry funcs) | Geometry | `True` | bool | Minimum-image convention if box info present |

## Best Practices

1. **Convert units before plotting** — nm → Å (×10), ps → ns (÷1000), rad → deg (`np.degrees`). #1 cause of "my RMSD is 10× too small".
2. **Superpose before RMSF** — `md.rmsd` superposes internally; RMSF doesn't. Without explicit `traj.superpose(...)`, RMSF picks up rigid-body motion.
3. **`md.iterload` for big trajectories** — 1 µs at 1 ps/frame is millions of frames. Streaming avoids OOM.
4. **`simplified=False` for fine-grained DSSP** — 3-state collapses 3_10 / pi-helix / bend transitions.
5. **Pair indices, not `resSeq`** — `md.compute_contacts` returns 0-based contiguous indices. Map to `resSeq` only for labeling.
6. **Strip waters early** — `traj.atom_slice(traj.topology.select("protein"))` cuts memory/time 5–20× on solvated systems.

## Common Recipes

### Recipe: Convert Trajectory Format

```python
import mdtraj as md

traj = md.load("input.nc", top="topology.parm7")
traj.save_xtc("output.xtc")
traj.save_pdb("output.pdb")
print(f"Converted {traj.n_frames} frames -> output.xtc")
```

### Recipe: Per-Residue Mean ± SD RMSF Across Replicates

Ensemble flexibility input for flexibility-aware docking or homology refinement.

```python
import mdtraj as md, numpy as np, pandas as pd

paths = {"rep1": "rep1.xtc", "rep2": "rep2.xtc", "rep3": "rep3.xtc"}
top = "protein.pdb"
rmsf_by_rep = {}
for name, p in paths.items():
    t  = md.load(p, top=top)
    ct = t.atom_slice(t.topology.select("name CA")); ct.superpose(ct, frame=0)
    rmsf_by_rep[name] = np.sqrt(((ct.xyz - ct.xyz.mean(axis=0)) ** 2).sum(axis=2).mean(axis=0)) * 10.0

df = pd.DataFrame(rmsf_by_rep)
df["mean"], df["std"] = df.mean(axis=1), df.std(axis=1)
df.to_csv("rmsf_replicates.csv", index_label="residue_index")
```

### Recipe: Save Frames Above RMSD Threshold

Curate "open" conformations for clustering or downstream analysis.

```python
import mdtraj as md

traj = md.load("rep1.xtc", top="protein.pdb")
ca   = traj.topology.select("name CA")
traj.superpose(traj, frame=0, atom_indices=ca)
rmsd_ang = md.rmsd(traj, traj, frame=0, atom_indices=ca) * 10.0

open_state = traj[rmsd_ang > 4.0]
open_state.save_dcd("open_state.dcd")
print(f"Saved {open_state.n_frames}/{traj.n_frames} frames")
```

### Recipe: Cross-Replicate Helix Fraction

```python
import mdtraj as md, numpy as np

paths = ["rep1.xtc", "rep2.xtc", "rep3.xtc"]
helix_fracs = [(md.compute_dssp(md.load(p, top="protein.pdb"), simplified=False) == "H").mean() for p in paths]
print(f"α-helix per replicate: {[f'{h:.2f}' for h in helix_fracs]}")
print(f"Mean ± std: {np.mean(helix_fracs):.2f} ± {np.std(helix_fracs):.2f}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `RuntimeError: No topology` | XTC/DCD/TRR carry no topology | Pass `top="protein.pdb"` (or `.prmtop`) to `md.load` |
| RMSD 10× too small | mdtraj returns nm | Multiply by 10.0 |
| RMSF spikes at termini | Intrinsic terminal flexibility, not a bug | Slice termini off or report explicitly |
| DSSP returns only `H/E/C` | `simplified=True` default | Pass `simplified=False` |
| Empty/`' '` DSSP cells | Space = coil, not missing | `dssp[dssp == " "] = "C"` |
| MemoryError on big trajectory | Whole trajectory in RAM | Switch to `md.iterload(..., chunk=500)` |
| phi/psi arrays differ in residue count | First residue has no phi; last has no psi | Intersect residue index sets before pairing |
| Ramachandran off-center | Angles still in radians | Wrap with `np.degrees`; set `range=[[-180, 180], [-180, 180]]` |
| `md.compute_contacts` returns NaN | Some pairs lack heavy atoms for `closest-heavy` (e.g., glycine sidechain) | Use `scheme="closest"` or `"ca"`; drop NaN columns |
| Contact map asymmetric | Only filled upper triangle | Mirror: `freq_map[j, i] = freq_map[i, j]` |
| `traj.time` all zeros | Some writers leave time blank | Reconstruct: `traj.time = np.arange(traj.n_frames) * dt_ps` |

## Related Skills

- **mdanalysis-trajectory** — richer atom-selection grammar and AnalysisBase framework
- **autodock-vina-docking** / **smina-molecular-docking** — feed representative MD frames as docking targets
- **chembl-database-bioactivity** — overlay ligand bioactivity on MD-derived flexibility maps

## References

- [mdtraj documentation](https://mdtraj.org/) — official docs, API reference, tutorials
- [McGibbon et al. (2015)](https://doi.org/10.1016/j.bpj.2015.08.015) — "MDTraj: A Modern Open Library for the Analysis of Molecular Dynamics Trajectories", *Biophys J*
- [DSSP algorithm](https://doi.org/10.1002/bip.360221211) — Kabsch & Sander (1983)
- [Baker–Hubbard H-bond criterion](https://doi.org/10.1016/S0006-3495(99)77244-7) — Baker & Hubbard (1984)
- [Shrake–Rupley SASA](https://doi.org/10.1016/0022-2836(73)90011-9) — Shrake & Rupley (1973)
- [mdtraj GitHub](https://github.com/mdtraj/mdtraj) — source, issues, examples
