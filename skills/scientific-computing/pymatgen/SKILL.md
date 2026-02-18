---
name: "pymatgen"
description: "pymatgen (Python Materials Genomics) is a materials science Python library for structure analysis, thermodynamics, and electronic property calculation. Parse and create crystal structures (CIF, POSCAR, CIF), query the Materials Project database for DFT-computed properties, analyze phase diagrams and pourbaix diagrams, compute X-ray diffraction patterns, and generate DFT input files for VASP, Quantum ESPRESSO, and CP2K. Alternatives: ASE (Atomic Simulation Environment) for MD/geometry; AFLOW for high-throughput; OVITO for visualization."
license: "MIT"
---

# pymatgen

## Overview

pymatgen is the standard Python library for materials science computation. Its core data model — `Structure` (periodic crystalline materials) and `Molecule` (non-periodic) — provides a unified representation for input/output across 30+ file formats (CIF, POSCAR/CONTCAR, XYZ, PDB, Gaussian, VASP). The library integrates with the Materials Project REST API (`mp_api`) to retrieve 150,000+ DFT-computed structures with band gaps, formation energies, and elastic constants. pymatgen is the foundation of the atomate2 and Custodian workflow frameworks for high-throughput DFT.

## When to Use

- Parsing and converting crystal structure files between CIF, POSCAR, XYZ, and other formats
- Querying the Materials Project API for computed band gaps, formation energies, and stability data
- Constructing and analyzing phase diagrams and Pourbaix diagrams for thermodynamic stability
- Generating VASP, Quantum ESPRESSO, or CP2K input files from structure objects
- Computing X-ray diffraction (XRD) and neutron diffraction patterns for comparison with experiment
- Analyzing symmetry, space groups, and Wyckoff positions of crystal structures
- Use ASE when running molecular dynamics or interfacing with multiple MD/DFT codes via a unified runner

## Prerequisites

- **Python packages**: `pymatgen`, `mp-api` (Materials Project client)
- **Data requirements**: structure files (CIF, POSCAR) or Materials Project API key
- **API key**: free at [materialsproject.org](https://materialsproject.org/) — set `PMG_MAPI_KEY` env var

```bash
pip install pymatgen mp-api
# Set API key
export PMG_MAPI_KEY="your_api_key_here"
# Or via pymatgen config
python -c "from pymatgen.core import SETTINGS; SETTINGS['PMG_MAPI_KEY'] = 'your_key'"
```

## Quick Start

```python
from pymatgen.core import Structure, Lattice, Species

# Build silicon diamond cubic structure from scratch
a = 5.431  # Angstroms
lattice = Lattice.cubic(a)
silicon = Structure(
    lattice=lattice,
    species=["Si", "Si"],
    coords=[[0, 0, 0], [0.25, 0.25, 0.25]],
)
print(f"Silicon: {silicon.formula}, {silicon.volume:.2f} Å³")
print(f"Space group: {silicon.get_space_group_info()}")
# Silicon: Si2, 40.89 Å³
# Space group: ('Fd-3m', 227)
```

## Core API

### Module 1: Structure and Lattice

Core data structures for periodic crystals.

```python
from pymatgen.core import Structure, Lattice, Element, Species
import numpy as np

# From lattice parameters
lattice = Lattice.from_parameters(a=4.05, b=4.05, c=4.05,
                                   alpha=90, beta=90, gamma=90)

# Build FCC aluminum
al_fcc = Structure(lattice, ["Al", "Al", "Al", "Al"],
                   [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])

print(f"Formula: {al_fcc.formula}")
print(f"Sites: {len(al_fcc)}")
print(f"Volume: {al_fcc.volume:.3f} Å³")
print(f"Density: {al_fcc.density:.3f} g/cm³")

# Access sites
for site in al_fcc:
    print(f"  {site.species_string} at {site.frac_coords}")
```

```python
# Load from file
from pymatgen.core import Structure

# From CIF (most common exchange format)
struct = Structure.from_file("material.cif")

# From POSCAR (VASP format)
struct_vasp = Structure.from_file("POSCAR")

# Get neighbors within cutoff
site = struct[0]
neighbors = struct.get_neighbors(site, r=3.0)
print(f"Neighbors within 3 Å: {len(neighbors)}")
for nn in neighbors[:3]:
    print(f"  {nn.species_string}: {nn.nn_distance:.3f} Å")
```

### Module 2: Materials Project API Query

Retrieve DFT-computed properties for 150,000+ materials.

```python
from mp_api.client import MPRester
import os

api_key = os.environ.get("PMG_MAPI_KEY", "your_key")

with MPRester(api_key) as mpr:
    # Search by chemical system
    docs = mpr.materials.summary.search(
        chemsys=["Li-Fe-O"],
        fields=["material_id", "formula_pretty", "energy_above_hull",
                "band_gap", "is_stable"]
    )
    print(f"Li-Fe-O materials: {len(docs)}")
    for d in docs[:5]:
        print(f"  {d.material_id}: {d.formula_pretty}, "
              f"Eg={d.band_gap:.2f} eV, above_hull={d.energy_above_hull:.3f} eV/atom")
```

```python
# Get specific material by MP ID
with MPRester(api_key) as mpr:
    doc = mpr.materials.summary.get_data_by_id(
        "mp-149",  # Silicon
        fields=["structure", "band_gap", "formation_energy_per_atom",
                "density", "is_stable", "symmetry"]
    )
    struct = doc.structure
    print(f"Si mp-149: band_gap={doc.band_gap:.3f} eV, "
          f"density={doc.density:.3f} g/cm³")
    print(f"Space group: {doc.symmetry.symbol}")
```

### Module 3: Symmetry Analysis

```python
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core import Structure

struct = Structure.from_file("material.cif")

# Symmetry analysis
sga = SpacegroupAnalyzer(struct, symprec=0.1)

print(f"Space group: {sga.get_space_group_symbol()} ({sga.get_space_group_number()})")
print(f"Crystal system: {sga.get_crystal_system()}")
print(f"Point group: {sga.get_point_group_symbol()}")

# Get conventional / primitive cell
primitive = sga.get_primitive_standard_structure()
conventional = sga.get_conventional_standard_structure()
print(f"Primitive: {len(primitive)} sites | Conventional: {len(conventional)} sites")

# Wyckoff positions
sym_dataset = sga.get_symmetry_dataset()
print(f"Wyckoff letters: {set(sym_dataset['wyckoffs'])}")
```

### Module 4: Phase Diagrams

Thermodynamic stability and phase boundary analysis.

```python
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDPlotter
from mp_api.client import MPRester
import os

api_key = os.environ.get("PMG_MAPI_KEY", "your_key")

with MPRester(api_key) as mpr:
    # Get all entries in the Li-Fe-P-O chemical system
    entries = mpr.get_pourbaix_entries(["Li", "Fe"])

# For phase diagram, use computed entries
with MPRester(api_key) as mpr:
    entries = mpr.get_entries_in_chemsys(["Li", "Fe", "O"])

pd = PhaseDiagram(entries)
print(f"Stable phases: {len(pd.stable_entries)}")

# Check stability of a specific composition
from pymatgen.core import Composition
comp = Composition("LiFeO2")
e_hull = pd.get_e_above_hull(pd.qhull_entries[0])
print(f"E above hull: {e_hull:.3f} eV/atom")

# Plot (requires matplotlib)
plotter = PDPlotter(pd, backend="matplotlib")
plotter.show()
```

### Module 5: XRD Pattern Simulation

```python
from pymatgen.analysis.diffraction.xrd import XRDCalculator
from pymatgen.core import Structure
import matplotlib.pyplot as plt

struct = Structure.from_file("material.cif")  # or build programmatically

# Calculate XRD pattern (Cu Kα radiation, λ = 1.5406 Å)
calculator = XRDCalculator(wavelength="CuKa")
pattern = calculator.get_pattern(struct, two_theta_range=(10, 80))

print(f"Diffraction peaks: {len(pattern.x)}")
for two_theta, intensity, hkl in zip(pattern.x[:5], pattern.y[:5], pattern.hkls[:5]):
    print(f"  2θ={two_theta:.2f}°, I={intensity:.1f}, hkl={hkl}")

# Plot
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(pattern.x, pattern.y, width=0.3, color="black")
ax.set_xlabel("2θ (degrees)")
ax.set_ylabel("Intensity (arb. units)")
ax.set_title(f"XRD Pattern — {struct.formula}")
plt.tight_layout()
plt.savefig("xrd_pattern.pdf", bbox_inches="tight")
```

### Module 6: DFT Input File Generation

Generate VASP input sets for DFT calculations.

```python
from pymatgen.io.vasp.sets import MPRelaxSet, MPStaticSet
from pymatgen.core import Structure

struct = Structure.from_file("material.cif")

# Generate VASP relaxation input set (Materials Project standard)
relax_set = MPRelaxSet(struct)

# Write to directory
import os
os.makedirs("vasp_relax", exist_ok=True)
relax_set.write_input("vasp_relax")
print("Generated: POSCAR, INCAR, KPOINTS, POTCAR (requires VASP pseudopotentials)")

# Inspect key INCAR settings
incar = relax_set.incar
print(f"ENCUT: {incar.get('ENCUT')} eV")
print(f"KPOINTS: {relax_set.kpoints}")

# For static calculation after relaxation
static_set = MPStaticSet.from_prev_calc(prev_calc_dir="vasp_relax")
static_set.write_input("vasp_static")
```

## Key Concepts

### Fractional vs Cartesian Coordinates

pymatgen `Structure` stores atomic positions in **fractional coordinates** (relative to lattice vectors, range 0–1). Convert to/from Cartesian (Angstroms) using `struct.lattice.get_cartesian_coords(frac)` or `struct.lattice.get_fractional_coords(cart)`. Most file formats use Cartesian; pymatgen converts automatically on read/write.

### Composition and Oxidation States

`Composition("LiFePO4")` parses chemical formulas. `Structure.add_oxidation_state_by_guess()` uses bond valence to assign formal charges (+Li, -O, etc.) needed for Pourbaix diagrams and some property calculations.

## Common Workflows

### Workflow 1: High-Throughput Stability Screen

```python
from mp_api.client import MPRester
from pymatgen.analysis.phase_diagram import PhaseDiagram
import pandas as pd, os

api_key = os.environ.get("PMG_MAPI_KEY", "your_key")

# Screen lithium-transition-metal oxides for stability
systems = [f"Li-{m}-O" for m in ["Mn", "Co", "Ni", "Fe", "V"]]
results = []

with MPRester(api_key) as mpr:
    for system in systems:
        docs = mpr.materials.summary.search(
            chemsys=[system],
            fields=["material_id", "formula_pretty", "energy_above_hull",
                    "band_gap", "is_stable", "formation_energy_per_atom"]
        )
        for d in docs:
            results.append({
                "system": system,
                "mpid": d.material_id,
                "formula": d.formula_pretty,
                "e_above_hull": d.energy_above_hull,
                "band_gap": d.band_gap,
                "stable": d.is_stable,
            })

df = pd.DataFrame(results)
stable = df[df["stable"] == True].sort_values("band_gap")
print(f"Stable phases: {len(stable)}/{len(df)}")
print(stable[["formula", "system", "band_gap", "e_above_hull"]].head(10))
stable.to_csv("stability_screen.csv", index=False)
```

### Workflow 2: Structure Manipulation and Export

```python
from pymatgen.core import Structure
from pymatgen.transformations.standard_transformations import (
    SupercellTransformation, SubstitutionTransformation
)

# Load and analyze structure
struct = Structure.from_file("material.cif")
print(f"Original: {struct.formula}, {len(struct)} sites")

# Create 2×2×2 supercell
sc_matrix = [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
supercell = SupercellTransformation(sc_matrix).apply_transformation(struct)
print(f"Supercell: {len(supercell)} sites")

# Substitute element (e.g., 10% Fe doping on Mn sites)
sub = SubstitutionTransformation({"Mn": {"Mn": 0.9, "Fe": 0.1}})
doped = sub.apply_transformation(struct)
print(f"Doped composition: {doped.composition.reduced_formula}")

# Export in multiple formats
struct.to(filename="output.cif")            # CIF
struct.to(filename="POSCAR")               # VASP POSCAR
struct.to(filename="output.xyz")           # XYZ
print("Exported CIF, POSCAR, XYZ")
```

## Key Parameters

| Parameter | Module/Function | Default | Range / Options | Effect |
|-----------|----------------|---------|-----------------|--------|
| `symprec` | `SpacegroupAnalyzer` | 0.01 | 0.01–0.5 Å | Symmetry detection tolerance; larger = more permissive |
| `wavelength` | `XRDCalculator` | `"CuKa"` | `"CuKa"`, `"MoKa"`, float (Å) | X-ray wavelength for diffraction simulation |
| `two_theta_range` | `XRDCalculator.get_pattern` | `(0, 90)` | tuple of degrees | Angular range for XRD pattern |
| `ENCUT` | `MPRelaxSet` INCAR | 520 eV | 300–800 eV | Plane-wave energy cutoff for VASP |
| `chemsys` | `MPRester.search` | — | `["Li-Fe-O"]` | Chemical system filter for Materials Project query |
| `fields` | `MPRester.search` | all | list of strings | Limit returned fields to reduce API transfer |
| `r` | `Structure.get_neighbors` | — | 1–8 Å | Neighbor search cutoff radius |

## Common Recipes

### Recipe: Batch CIF to POSCAR Conversion

```python
from pymatgen.core import Structure
from pathlib import Path

cif_dir = Path("cif_files")
poscar_dir = Path("poscar_files")
poscar_dir.mkdir(exist_ok=True)

for cif_path in cif_dir.glob("*.cif"):
    try:
        struct = Structure.from_file(str(cif_path))
        out_path = poscar_dir / f"{cif_path.stem}_POSCAR"
        struct.to(filename=str(out_path))
        print(f"Converted: {cif_path.name} → {out_path.name}")
    except Exception as e:
        print(f"FAILED {cif_path.name}: {e}")
```

### Recipe: Get Band Gap for List of Materials

```python
from mp_api.client import MPRester
import pandas as pd, os

mp_ids = ["mp-149", "mp-2815", "mp-1265"]  # Si, GaAs, TiO2

api_key = os.environ.get("PMG_MAPI_KEY", "your_key")
with MPRester(api_key) as mpr:
    docs = mpr.materials.summary.get_data_by_ids(
        mp_ids, fields=["material_id", "formula_pretty", "band_gap", "is_gap_direct"]
    )

df = pd.DataFrame([{
    "mpid": d.material_id,
    "formula": d.formula_pretty,
    "band_gap_eV": d.band_gap,
    "direct_gap": d.is_gap_direct,
} for d in docs])
print(df.to_string(index=False))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `APIError: Invalid API key` | `PMG_MAPI_KEY` not set or expired | Set env var: `export PMG_MAPI_KEY="your_key"`; regenerate key at materialsproject.org |
| `SpacegroupAnalyzer` returns wrong space group | Atom positions have small disorder; `symprec` too tight | Increase `symprec` from 0.01 to 0.1; use `get_refined_structure()` first |
| `Structure.from_file` fails for CIF | Disorder, partial occupancies, or non-standard CIF | Use `CifParser(file).get_structures(primitive=False)`; set `occupancy_tolerance=2.0` |
| `MPRester` hangs or times out | Large query returning thousands of results | Add `fields=["material_id", "formula_pretty"]` to reduce payload; use `chunk_size` |
| POTCAR not found in VASP input set | VASP pseudopotential library not configured | Run `pmg config --add PMG_VASP_PSP_DIR /path/to/potpaw` |
| Memory error on large supercell | Supercell has thousands of atoms | Reduce supercell size; use `Structure.get_sorted_structure()` then write incrementally |
| `XRDCalculator` gives zero peaks | Structure has only 1 site or all-same species | Ensure multi-site structure; check that structure loaded correctly with `print(struct)` |

## Related Skills

- `pymoo` — multi-objective optimization for materials property screening using pymatgen descriptors
- `autodock-vina-docking` — structure preparation workflow analogous to pymatgen for molecular docking
- `zarr-python` — efficient storage of large arrays from MD trajectories or property databases

## References

- [pymatgen documentation](https://pymatgen.org/) — full API reference, tutorials, and compatibility matrix
- [Materials Project API docs](https://api.materialsproject.org/) — REST API and mp-api client reference
- [pymatgen paper: Ong et al. (2013), CMS](https://doi.org/10.1016/j.commatsci.2012.10.028) — original publication and design philosophy
- [Materials Project paper: Jain et al. (2013), APL Materials](https://doi.org/10.1063/1.4812323) — database description and computed properties
- [pymatgen GitHub](https://github.com/materialsproject/pymatgen) — source code and examples
