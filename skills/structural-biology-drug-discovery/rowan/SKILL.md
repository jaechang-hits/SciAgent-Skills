---
name: "rowan"
description: "Rowan is a cloud-based computational chemistry platform providing quantum chemistry calculations via a Python SDK. Use it to run geometry optimization, conformer generation, torsional scans, and energy minimization with DFT or semiempirical methods, and retrieve molecular properties (dipole moment, partial charges, frontier orbital energies) — without managing local quantum chemistry software or HPC clusters."
license: "Proprietary"
---

# rowan

## Overview

Rowan is a cloud quantum chemistry platform that exposes DFT and semiempirical calculations through a Python SDK (`rowan`). Submit calculations (geometry optimization, conformer generation, torsional scans, single-point energies) from Python scripts or Jupyter notebooks, and retrieve results — energies, geometries, partial charges, frontier orbital energies — without managing Gaussian, ORCA, or Psi4 installations. Rowan handles job queuing, execution, and storage. A free tier is available for academic and exploratory use.

## When to Use

- **Geometry optimization of small molecules**: Getting accurate equilibrium geometries for drug candidates, fragments, or building blocks using DFT.
- **Conformer generation with energy ranking**: Generating and optimizing multiple conformers to identify the lowest-energy conformation for docking or property prediction.
- **Torsional potential scans**: Mapping the energy profile along a rotatable bond to understand conformational preferences.
- **Quantum mechanical property calculation**: Computing dipole moments, partial charges (Mulliken, ESP), HOMO/LUMO energies, and electrostatic potential surfaces.
- **Energy minimization before docking**: Refining ligand geometries before input to structure-based docking tools (DiffDock, AutoDock Vina).
- **Comparing isomer stability**: Calculating relative energies of tautomers, stereoisomers, or constitutional isomers.
- For large-scale conformer screening (>1000 molecules), use RDKit's ETKDGv3 + MMFF (force field level, no cloud cost).
- For protein-scale quantum mechanics/molecular mechanics (QM/MM), specialized packages like ORCA + CP2K are needed.

## Prerequisites

- **Python packages**: `rowan` (official Python SDK)
- **Account**: Free account at https://rowan.chem.ucla.edu/ (academic) or https://rowanquantum.com/
- **API key**: Set `ROWAN_API_KEY` environment variable after account creation
- **Data requirements**: Molecular structures as SMILES strings or XYZ coordinate blocks

```bash
pip install rowan

# Set API key (add to .bashrc or .env)
export ROWAN_API_KEY="your_api_key_here"
```

## Quick Start

```python
import rowan

# Authenticate (uses ROWAN_API_KEY environment variable automatically)
client = rowan.RowanClient()

# Run geometry optimization of aspirin at GFN2-xTB level
job = client.compute(
    smiles="CC(=O)Oc1ccccc1C(=O)O",
    method="gfn2-xtb",
    tasks=["optimize"],
)
print(f"Job ID: {job.id}, Status: {job.status}")

# Wait for completion and retrieve energy
result = client.wait(job.id)
print(f"Energy: {result.energy:.6f} Hartree")
print(f"Optimized geometry atoms: {len(result.geometry.atoms)}")
```

## Core API

### Module 1: Client Initialization and Authentication

```python
import rowan
import os

# Option 1: automatic (reads ROWAN_API_KEY env variable)
client = rowan.RowanClient()

# Option 2: explicit key
client = rowan.RowanClient(api_key=os.environ["ROWAN_API_KEY"])

print(f"Authenticated as: {client.user.email}")
print(f"Organization: {client.user.organization}")
```

### Module 2: Geometry Optimization

Optimize a molecular geometry to the nearest local minimum.

```python
import rowan

client = rowan.RowanClient()

# GFN2-xTB semiempirical (fast, good for conformer screening)
job_xtb = client.compute(
    smiles="CCc1ccc(cc1)NC(=O)C",    # paracetamol
    method="gfn2-xtb",
    tasks=["optimize"],
)
result_xtb = client.wait(job_xtb.id)
print(f"xTB optimized energy: {result_xtb.energy:.6f} Hartree")
print(f"Geometry: {len(result_xtb.geometry.atoms)} atoms")
```

```python
# DFT optimization: B3LYP/6-31G* (accurate, slower)
job_dft = client.compute(
    smiles="CCc1ccc(cc1)NC(=O)C",
    method="b3lyp",
    basis_set="6-31g*",
    tasks=["optimize"],
    solvent="water",               # implicit solvent (SMD model)
)
result_dft = client.wait(job_dft.id)
print(f"B3LYP/6-31G* energy (water): {result_dft.energy:.6f} Hartree")
print(f"Dipole moment: {result_dft.dipole_moment:.3f} Debye")
```

### Module 3: Conformer Generation

Generate multiple 3D conformers and rank by energy.

```python
import rowan
import pandas as pd

client = rowan.RowanClient()

# Generate and optimize 10 conformers at GFN2-xTB level
job = client.compute(
    smiles="CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",  # ibuprofen
    method="gfn2-xtb",
    tasks=["conformers"],
    n_conformers=10,
)
result = client.wait(job.id)

# Rank conformers by relative energy
conformers = result.conformers
df = pd.DataFrame([
    {"conformer_id": i,
     "energy_hartree":    c.energy,
     "rel_energy_kcal":   (c.energy - min(c2.energy for c2 in conformers)) * 627.509}
    for i, c in enumerate(conformers)
]).sort_values("rel_energy_kcal")

print(df.to_string(index=False))
print(f"\nLowest energy conformer ID: {df.iloc[0]['conformer_id']}")
```

### Module 4: Torsional Scan

Map energy as a function of a dihedral angle.

```python
import rowan
import numpy as np
import matplotlib.pyplot as plt

client = rowan.RowanClient()

# Scan the C-C=C-C dihedral of butene
job = client.compute(
    smiles="CC=CC",             # but-2-ene
    method="gfn2-xtb",
    tasks=["torsion_scan"],
    torsion_atoms=[0, 1, 2, 3],  # atom indices defining dihedral
    n_scan_points=36,             # 36 points = 10-degree steps
)
result = client.wait(job.id)

angles  = [point.angle  for point in result.torsion_scan]
energies = [point.energy for point in result.torsion_scan]
rel_e = [(e - min(energies)) * 627.509 for e in energies]  # convert to kcal/mol

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(angles, rel_e, "o-", color="steelblue")
ax.set_xlabel("Dihedral angle (degrees)")
ax.set_ylabel("Relative energy (kcal/mol)")
ax.set_title("Torsional potential: but-2-ene C-C=C-C dihedral")
plt.tight_layout()
plt.savefig("torsion_scan.png", dpi=150)
print("Torsion scan saved -> torsion_scan.png")
```

### Module 5: Single-Point Properties

Compute electronic properties at a fixed geometry (HOMO/LUMO, partial charges, ESP).

```python
import rowan

client = rowan.RowanClient()

# Single-point DFT: get frontier orbital energies and partial charges
job = client.compute(
    smiles="c1ccccc1N",          # aniline
    method="b3lyp",
    basis_set="6-311+g**",
    tasks=["single_point", "partial_charges", "orbitals"],
)
result = client.wait(job.id)

print(f"HOMO energy: {result.homo_energy:.4f} eV")
print(f"LUMO energy: {result.lumo_energy:.4f} eV")
print(f"HOMO-LUMO gap: {result.lumo_energy - result.homo_energy:.4f} eV")
print(f"Dipole moment: {result.dipole_moment:.3f} Debye")

# Partial charges (Mulliken)
for i, (atom, charge) in enumerate(zip(result.geometry.atoms, result.partial_charges)):
    print(f"  Atom {i} ({atom.symbol}): {charge:+.4f} e")
```

### Module 6: Batch Job Submission

Submit multiple molecules concurrently.

```python
import rowan
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

client = rowan.RowanClient()

smiles_list = [
    ("aspirin",      "CC(=O)Oc1ccccc1C(=O)O"),
    ("caffeine",     "Cn1cnc2c1c(=O)n(c(=O)n2C)C"),
    ("paracetamol",  "CC(=O)Nc1ccc(O)cc1"),
    ("ibuprofen",    "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
]

def submit_and_wait(name, smiles):
    job = client.compute(smiles=smiles, method="gfn2-xtb", tasks=["optimize"])
    result = client.wait(job.id)
    return {"name": name, "smiles": smiles, "energy": result.energy}

results = []
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(submit_and_wait, n, s): n for n, s in smiles_list}
    for future in as_completed(futures):
        results.append(future.result())

df = pd.DataFrame(results)
df.to_csv("batch_energies.csv", index=False)
print(df)
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `method` | compute | required | `"gfn2-xtb"`, `"b3lyp"`, `"wb97x-d"`, `"mp2"` | QC method; xTB is fastest, DFT is accurate, MP2 for correlation |
| `basis_set` | compute (DFT) | method-dependent | `"6-31g*"`, `"6-311+g**"`, `"def2-svp"`, `"def2-tzvp"` | Basis set; larger = more accurate and slower |
| `tasks` | compute | required | `["optimize"]`, `["single_point"]`, `["conformers"]`, `["torsion_scan"]` | What calculation to run |
| `n_conformers` | conformers task | `10` | `1`–`100` | Number of conformers to generate and optimize |
| `n_scan_points` | torsion_scan | `36` | `12`–`72` | Number of dihedral scan points (360/n gives step size) |
| `solvent` | compute | `None` | `"water"`, `"dmso"`, `"methanol"`, etc. | Implicit SMD solvation model |
| `torsion_atoms` | torsion_scan | required | list of 4 atom indices | Defines the dihedral angle for the scan |

## Best Practices

1. **Use GFN2-xTB for screening, DFT for final characterization**: xTB is 100–1000x faster than DFT and adequate for conformer ranking and geometry exploration. Switch to B3LYP or wB97X-D for accurate energetics, HOMO/LUMO gaps, and publishable results.

2. **Always optimize geometry before computing properties**: Single-point calculations on unrelaxed geometries (e.g., from SMILES 3D embedding) give unreliable energies and electronic properties. Run `tasks=["optimize"]` first.

3. **Set `solvent` for biologically relevant molecules**: Gas-phase energies often differ dramatically from solution-phase for charged or highly polar molecules. Use `solvent="water"` for drug candidates evaluated in aqueous conditions.

4. **Poll job status for long DFT calculations**: Use `client.wait()` with a timeout or poll with `client.get_job(job_id).status` in long-running batch workflows to avoid blocking.

5. **Export optimized geometries as XYZ for reuse**: Save the optimized geometry to avoid re-running costly DFT jobs when different property calculations are needed on the same structure.
   ```python
   with open("optimized.xyz", "w") as f:
       f.write(result.geometry.to_xyz())
   ```

## Common Workflows

### Workflow 1: Conformer Search and Property Calculation

**Goal**: Find the lowest-energy conformer of a drug candidate and compute its electronic properties.

```python
import rowan
import pandas as pd

client = rowan.RowanClient()
smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"   # ibuprofen

# Step 1: Generate and rank conformers at fast xTB level
conf_job = client.compute(
    smiles=smiles, method="gfn2-xtb", tasks=["conformers"], n_conformers=20
)
conf_result = client.wait(conf_job.id)
lowest_conf = min(conf_result.conformers, key=lambda c: c.energy)
print(f"Lowest conformer energy: {lowest_conf.energy:.6f} Hartree")

# Step 2: Refine with DFT and compute properties
dft_job = client.compute(
    xyz=lowest_conf.to_xyz(),      # use optimized xTB geometry as DFT start
    method="b3lyp",
    basis_set="6-31g*",
    tasks=["optimize", "partial_charges", "orbitals"],
    solvent="water",
)
dft_result = client.wait(dft_job.id)

print(f"B3LYP/6-31G* energy (water): {dft_result.energy:.6f} Hartree")
print(f"HOMO-LUMO gap: {dft_result.lumo_energy - dft_result.homo_energy:.4f} eV")
print(f"Dipole moment: {dft_result.dipole_moment:.3f} Debye")
```

### Workflow 2: Relative Stability of Tautomers

**Goal**: Compare the energies of two tautomers to determine which is more stable in water.

```python
import rowan

client = rowan.RowanClient()

tautomers = {
    "keto":   "CC(=O)CC(=O)C",     # acetylacetone keto form
    "enol":   "CC(=O)C=C(O)C",     # acetylacetone enol form
}

energies = {}
for name, smiles in tautomers.items():
    job = client.compute(
        smiles=smiles,
        method="b3lyp",
        basis_set="6-311+g**",
        tasks=["optimize"],
        solvent="water",
    )
    result = client.wait(job.id)
    energies[name] = result.energy
    print(f"{name}: {result.energy:.6f} Hartree")

delta_e_hartree = energies["enol"] - energies["keto"]
delta_e_kcal    = delta_e_hartree * 627.509
print(f"\nDelta E (enol - keto): {delta_e_kcal:.2f} kcal/mol")
print(f"More stable form: {'enol' if delta_e_kcal < 0 else 'keto'}")
```

## Expected Outputs

- `result.energy` — total electronic energy in Hartree
- `result.geometry` — optimized 3D geometry (atoms + coordinates)
- `result.dipole_moment` — scalar dipole moment in Debye
- `result.homo_energy`, `result.lumo_energy` — frontier orbital energies in eV
- `result.partial_charges` — list of per-atom charges in elementary charge units
- `result.conformers` — list of conformer objects with individual energies
- `result.torsion_scan` — list of (angle, energy) scan points

## Common Recipes

### Recipe: Quick Single-Point Energy

When to use: Compare relative energies of two conformers or reaction intermediates in one call.

```python
import rowan

client = rowan.Client()

smiles_list = ["CC(=O)O", "C(=O)(O)C"]  # Acetic acid, two representations
jobs = []
for smi in smiles_list:
    job = client.compute(
        molecule=rowan.Molecule.from_smiles(smi),
        theory_level="gfn2-xtb",
        task="single_point",
    )
    jobs.append(job)

# Collect energies
for smi, job in zip(smiles_list, jobs):
    result = client.wait(job)
    print(f"{smi}: energy = {result.energy:.6f} Hartree")
```

### Recipe: Check Running Job Status

When to use: Monitor a long-running optimization or conformer search without blocking.

```python
import rowan, time

client = rowan.Client()
job = client.compute(
    molecule=rowan.Molecule.from_smiles("c1ccccc1"),
    theory_level="gfn2-xtb",
    task="optimize",
)
print(f"Job ID: {job.id}")

# Poll every 10 seconds (non-blocking)
for _ in range(30):
    status = client.status(job)
    print(f"Status: {status}")
    if status in ("completed", "failed"):
        break
    time.sleep(10)

result = client.get(job)
print(f"Final energy: {result.energy:.6f} Hartree")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `AuthenticationError` | API key not set or expired | Set `ROWAN_API_KEY` env variable; regenerate key at rowanquantum.com |
| Job stays in `queued` status | High server load on free tier | Wait or upgrade to paid tier; free tier may queue during peak hours |
| `SCF not converged` error | DFT self-consistent field failed | Try a smaller basis set; use `method="gfn2-xtb"` first to get a better starting geometry |
| `ValueError: invalid SMILES` | Malformed SMILES string | Validate with `Chem.MolFromSmiles(smiles)` using RDKit before submission |
| High energy after optimization | Geometry stuck in local minimum | Generate multiple conformers with `tasks=["conformers"]` and pick the lowest |
| Missing `result.homo_energy` | Orbital calculation not requested | Add `"orbitals"` to the `tasks` list |

## References

- [Rowan Documentation](https://docs.rowanquantum.com/) — official SDK and API reference
- [Rowan Python SDK (GitHub)](https://github.com/rowansci/rowan-python) — source code and examples
- [GFN2-xTB paper: Bannwarth et al. (2019), J. Chem. Theory Comput.](https://doi.org/10.1021/acs.jctc.8b01176) — xTB semiempirical method used by Rowan
- [B3LYP functional reference: Becke (1993), J. Chem. Phys.](https://doi.org/10.1063/1.464913) — foundational DFT method
