---
name: "neb-irc-activation-energy"
description: "NEB-IRC activation energy pipeline for reaction barriers using GFN2-xTB and pysisyphus. Optimize reactant and product geometries, run CI-NEB path search, optimize the transition state with a Hessian, verify with IRC (one imaginary mode, endpoints matching reactant/product, single NEB maximum), and report the electronic and Gibbs barriers. Use when you need a transition state, reaction barrier, activation energy, minimum energy path, or intrinsic reaction coordinate. Covers reactant/product atom-ordering pitfalls, feasibility sizing for single-core runs, and thermochemistry corrections. For 2D reaction scheme drawing use rdkit-chemdraw-cdxml."
license: "CC-BY-4.0"
---

# NEB-IRC activation energy pipeline

## Overview

Computes a reaction activation energy end to end: optimize reactant and product, find the
minimum energy path with climbing-image NEB, refine the transition state with a Hessian, and
confirm it with IRC. The engine is GFN2-xTB through pysisyphus, which needs no conda and no
Fortran compiler. Output is a verified transition state geometry and a barrier (ΔE‡, and ΔG‡
once thermal corrections are applied). A converged TS optimization means nothing until the
imaginary mode and the IRC endpoints are checked, so verification is a required stage, not an
optional one.

## When to Use

- Finding the transition state for an elementary reaction step and its activation energy
- Computing a reaction barrier (ΔE‡ or ΔG‡) to rank a series of related reactions
- Running a climbing-image NEB / minimum energy path between a reactant and product
- Verifying a candidate TS with IRC — checking it connects the intended reactant and product
- Screening barriers at a cheap semi-empirical level before committing DFT time
- Deciding whether a quantum-chemistry job fits the available compute before launching it

Reach for DFT on a multi-core node instead when you need quantitative agreement with
experiment; GFN2-xTB barriers are semi-quantitative (see `references/energetics.md`). For
drawing the reaction as a 2D scheme figure, use the `rdkit-chemdraw-cdxml` skill.

## Prerequisites

- **Tools**: `xtb` (GFN2-xTB engine), `pysisyphus` (`pysis` CLI for the path pipeline)
- **Input**: `reactant.xyz` and `product.xyz` with **identical atom ordering** (see Step 2)
- **Environment**: single core is enough; set `OMP_NUM_THREADS` to match physical cores

Check first, install only if missing. Inside a pixi/conda project, invoke tools via the
project runner (e.g. `pixi run xtb`) rather than a global install.

```bash
command -v xtb && command -v pysis && echo "already installed" || \
  bash scripts/setup_env.sh   # fetches xtb binary + pip-installs pysisyphus, ~2-3 min
source "${ROOT:-$HOME/xtbenv}/env.sh"
```

## Quick Start

```bash
# reactant.xyz and product.xyz already prepared with identical atom ordering
cp scripts/pipeline.yaml .
pysis pipeline.yaml > pipeline.log 2>&1          # preopt -> NEB -> TS opt -> IRC
python3 scripts/check_result.py pipeline.log     # three verification gates
# only report the barrier if every gate passes
```

## Workflow

### Step 1: Set up the environment

`xtb` ships prebuilt binaries on GitHub releases and `pysisyphus` installs from PyPI, so
neither needs conda-forge. Keep threads matched to physical cores — on one core, `OMP_NUM_THREADS=1`.

```bash
bash scripts/setup_env.sh
source "${ROOT:-$HOME/xtbenv}/env.sh"
xtb --version && python3 -c "import pysisyphus; print(pysisyphus.__version__)"
```

### Step 2: Prepare reactant and product geometries

Most pipeline failures originate here, not in the NEB. Build the product by editing a **copy**
of the reactant so atom ordering is guaranteed identical — a permuted order gives a path that
is geometrically valid and chemically meaningless. Align non-reacting groups so a spectator
conformational change does not fold into the barrier. For bimolecular reactions, use a
pre-reaction complex as the reactant, not separated fragments (NEB converges poorly from
infinite separation, and the reference state changes the reported barrier — record it).

```python
# Build product from a copy of the reactant, moving only the reacting atoms.
from pathlib import Path

lines = Path("reactant.xyz").read_text().splitlines()
natoms = int(lines[0])
atoms = [ln.split() for ln in lines[2:2 + natoms]]   # [symbol, x, y, z] per atom
# ... edit ONLY the coordinates of atoms that move in the reaction; keep order + symbols ...
out = [str(natoms), "product"] + [" ".join(a) for a in atoms]
Path("product.xyz").write_text("\n".join(out) + "\n")
print(f"product.xyz written, {natoms} atoms, order preserved")
```

### Step 3: Check the endpoints sit in different basins

If the reacting groups start too close, preoptimization carries the reactant downhill over the
barrier and both endpoints relax to the same structure. The NEB then returns a nearly flat
profile and the TS search aborts. This looks like success in the log until it fails minutes
later, so compare the two pre-optimized endpoints explicitly on the key reacting bond.

```python
import numpy as np

def load_xyz(fn):
    lines = open(fn).read().splitlines()
    n = int(lines[0])
    return np.array([[float(v) for v in ln.split()[1:4]] for ln in lines[2:2 + n]])

r, p = load_xyz("first_pre_opt.xyz"), load_xyz("last_pre_opt.xyz")   # written by preopt
i, j = 0, 5                                     # indices of the atoms whose bond changes
dr, dp = np.linalg.norm(r[i] - r[j]), np.linalg.norm(p[i] - p[j])
print(f"reacting distance: reactant {dr:.2f} A, product {dp:.2f} A, delta {abs(dr-dp):.2f} A")
assert abs(dr - dp) > 0.3, "endpoints nearly identical: move the reacting fragment further out"
```

### Step 4: Run the pipeline

The template chains preopt → IDPP interpolation → CI-NEB → RS-I-RFO TS optimization with
Hessian → IRC both directions → endpoint reoptimization. Use IDPP, not linear interpolation,
which produces atom clashes the NEB then wastes cycles undoing. Set `charge` and `mult`
explicitly in the YAML; raise `max_cycles` to 150–200 above ~50 atoms.

```bash
cp scripts/pipeline.yaml .
pysis pipeline.yaml > pipeline.log 2>&1
tail -20 pipeline.log            # confirm it reached the endopt / IRC stage
```

### Step 5: Verify the transition state (three gates)

Never report a barrier before this passes. The checker parses the log and applies all three
gates, returning exit code 0 only if every one passes.

```bash
python3 scripts/check_result.py pipeline.log
# [PASS] imaginary frequencies  exactly 1 at -1243.5 cm-1
# [PASS] IRC endpoints          forward and backward matched distinct inputs
# [PASS] NEB profile            elementary, single barrier, span 62.4 kJ/mol
```

### Step 6: Compute thermochemistry and report the barrier

At minimum report ΔE‡ and the level of theory. For comparison against experimental rates the
user needs ΔG‡, which requires thermal corrections from Hessians on the TS and reactant. State
which quantity is being reported — several differ by tens of kJ/mol (see
`references/energetics.md`).

```bash
xtb reactant.xyz --hess --gfn 2 --etemp 300 > reactant_hess.log 2>&1
# read ZPE, H(T)-H(0), entropy, G from the thermochemistry block; take TS - reactant deltas
grep -iE "zero point|total free energy|G\(RRHO\)" reactant_hess.log
```

## Key Parameters

Set in `pipeline.yaml` unless noted.

| Parameter | Section | Default | Range / Options | Effect |
|-----------|---------|---------|-----------------|--------|
| `gfn` | `calc` | `2` | `0`, `1`, `2` | GFN parametrization; `2` is the default choice |
| `charge` / `mult` | `calc` | `0` / `1` | integers | Set explicitly; wrong values silently give a wrong TS |
| `alpb` | `calc` | off | solvent name (`water`, ...) | Implicit solvation; changes the barrier |
| `pal` | `calc` | `1` | physical cores | Threads; xTB parallel efficiency is modest |
| `between` | `interpol` | `8` | `6`–`12` | Intermediate NEB images (`between`+2 total) |
| `climb` | `cos` | `True` | `True`/`False` | Climbing image; gives a usable TS guess |
| `max_cycles` | `opt` | `80` | `80`–`200` | Raise above ~50 atoms |
| `do_hess` | `tsopt` | `True` | `True`/`False` | Required — the imaginary-frequency gate depends on it |

## Key Concepts

**The three verification gates** and what a failure means:

| Gate | Failure | Meaning and fix |
|---|---|---|
| Imaginary frequencies | 0 found | Optimizer fell into a minimum; perturb along the NEB tangent and rerun tsopt |
| Imaginary frequencies | ≥2 found | Higher-order saddle; displace along the lowest non-reactive mode and reoptimize |
| Imaginary frequencies | 1, wrong mode | Confirm the mode is the bonds breaking/forming — a methyl rotation also shows exactly one |
| IRC endpoints | mismatch | TS connects other species; it may be a real TS for a different reaction — do not report |
| NEB profile | multiple maxima | Not an elementary step; split at the intervening minimum and run each segment |

**Barrier definitions** differ by which reference and which corrections: ΔE‡ (electronic),
ΔE‡+ZPE, ΔH‡, ΔG‡ (for kinetics). For bimolecular reactions the reference state (separated
reactants vs pre-reaction complex) shifts the number — record which was used. Full table in
`references/energetics.md`.

## Common Recipes

### Recipe: Add implicit solvation and set charge/multiplicity

When to use: reaction in solution, or a charged / open-shell species.

```yaml
calc:
 type: xtb
 pal: 1
 gfn: 2
 charge: -1          # e.g. an anionic mechanism
 mult: 1
 alpb: water         # any xtb solvent: water, acetonitrile, dmso, thf, ...
```

### Recipe: Split a multi-step reaction into elementary steps

When to use: `check_result.py` reports multiple NEB maxima (an intermediate exists).

```bash
# The NEB path .trj holds per-image energies; the intermediate is the interior minimum.
# Extract that geometry as the product of step 1 and the reactant of step 2, then run
# the pipeline twice, once per segment.
python3 -c "import pysisyphus" && echo "re-run pipeline.yaml on reactant.xyz + intermediate.xyz, then intermediate.xyz + product.xyz"
```

### Recipe: Refine the electronic energy with a DFT single point

When to use: xTB geometry is fine but you need a better barrier. Keep xTB geometry + thermal
corrections, replace only the electronic energy on 3 structures (≤30 atoms).

```python
from pyscf import gto, dft

def electronic_energy(xyz_fn, basis="def2-svp", xc="b3lyp"):
    mol = gto.M(atom=xyz_fn, basis=basis)     # xyz file path accepted directly
    mf = dft.RKS(mol); mf.xc = xc
    return mf.kernel()                          # Hartree

e_ts = electronic_energy("ts_final_geometry.xyz")
e_r  = electronic_energy("reactant.xyz")
print(f"DFT dE‡ = {(e_ts - e_r) * 2625.4996:.1f} kJ/mol (add xTB G_corr for dG‡)")
```

## Expected Outputs

- `pipeline.log` — full run log; parsed by `check_result.py`
- `ts_final_geometry.xyz` — the optimized transition state
- `final_geometries.trj` — the converged NEB path (per-image energies in comment lines)
- `left_ts_right_geoms.trj` — IRC endpoints plus TS, for the connectivity check
- A barrier: ΔE‡ from the log, ΔG‡ after applying Hessian thermal corrections

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `xtb: command not found` | Env not sourced | `source "${ROOT:-$HOME/xtbenv}/env.sh"` in every new shell |
| NEB profile nearly flat, TS search aborts | Endpoints in the same basin | Move the reacting fragment further out (Step 3) |
| Path is chemically nonsensical | Permuted atom order between endpoints | Rebuild product from a copy of the reactant (Step 2) |
| Zero imaginary frequencies | Optimizer landed on a minimum | Perturb along the NEB tangent, rerun tsopt |
| Two or more imaginary frequencies | Higher-order saddle point | Displace along the lowest non-reactive mode, reoptimize |
| IRC endpoints don't match inputs | TS connects different species | Do not report; find the TS for the intended reaction |
| Job killed / never finishes | System too large for the budget | Check `references/feasibility.md`; split stages or shrink the model |
| `qm` optimizer crashes on cycle 1 | QuickMin instability | Use `type: lbfgs` under `opt` (the template default) |

## Bundled Resources

- `scripts/setup_env.sh` — installs xtb (GitHub release) + pysisyphus (PyPI), writes `env.sh`
- `scripts/pipeline.yaml` — full preopt→NEB→TSopt→IRC→endopt template with inline comments
- `scripts/check_result.py` — automated verification of the three gates (exit 0 = all pass)
- `references/feasibility.md` — measured timings, atom-count sizing, what DFT can/can't do here
- `references/energetics.md` — ΔE‡/ΔH‡/ΔG‡ definitions, thermochemistry, reporting conventions

## References

- [xtb documentation](https://xtb-docs.readthedocs.io/) — GFN2-xTB methods and CLI
- [pysisyphus documentation](https://pysisyphus.readthedocs.io/) — COS/NEB, TS optimizers, IRC
- Bannwarth, Ehlert, Grimme, *J. Chem. Theory Comput.* 2019, 15, 1652 — GFN2-xTB method paper
- Steinmetzer, Kupfer, Gräfe, *Int. J. Quantum Chem.* 2021, 121, e26550 — pysisyphus paper
- [ASE](https://wiki.fysik.dtu.dk/ase/) / [PySCF](https://pyscf.org/) — geometry I/O and DFT single points
