---
name: "neb-irc-activation-energy"
description: "NEB-IRC activation energy pipeline for reaction barriers using GFN2-xTB and pysisyphus. Optimize reactant and product geometries, run CI-NEB path search, optimize the transition state with a Hessian, verify with IRC (one imaginary mode, endpoints matching reactant/product, single NEB maximum), and report the electronic and Gibbs barriers. Use when you need a transition state, reaction barrier, activation energy, minimum energy path, or intrinsic reaction coordinate. Covers reactant/product atom-ordering pitfalls, feasibility sizing for single-core runs, and thermochemistry corrections. Renders an IRC energy-profile plot and an animated TS imaginary-mode HTML viewer. For 2D reaction scheme drawing use rdkit-chemdraw-cdxml."
license: "CC-BY-4.0"
---

# NEB-IRC activation energy pipeline

## Overview

Computes a reaction activation energy end to end: optimize reactant and product, find the
minimum energy path with climbing-image NEB, refine the transition state with a Hessian, and
confirm it with IRC. The engine is GFN2-xTB through pysisyphus, which needs no conda and no
Fortran compiler. Output is a verified transition state geometry, a barrier (ΔE‡, and ΔG‡ once
thermal corrections are applied), and two standard visual deliverables — an **IRC energy
profile** (`irc_energy_profile.png`) and an animated **TS imaginary-mode** viewer
(`ts_imaginary_mode.html`). A converged TS optimization means nothing until the imaginary mode
and the IRC endpoints are checked, so verification is a required stage, not an optional one.

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
- **Python**: `matplotlib` for the IRC energy plot (the TS animation HTML needs no packages)
- **Input**: `reactant.xyz` and `product.xyz` with **identical atom ordering** (see Step 2)
- **Environment**: single core is enough; set `OMP_NUM_THREADS` to match physical cores

**Run on a local filesystem, not a mounted/networked workspace.** pysisyphus creates and
deletes symlinks as it runs; on s3fs/FUSE-mounted directories that throws a `PermissionError`
mid-run and the whole pipeline dies. Work in a local scratch dir (e.g. `/tmp/rxn/`) and copy
results back out at the end.

**Materialize the bundled scripts into the scratch dir first.** The `scripts/` files can be
*read* from the skill path but are not on the execution sandbox's path — `bash scripts/setup_env.sh`
from the wrong directory gives "No such file or directory", and they are **not** fetchable from
GitHub. Read each with your file tool using the **leading-slash** skill path (a path without the
leading `/` is looked up in the sandbox workdir, where the file does not exist) and write it
locally:

```python
import os
os.makedirs("/tmp/rxn", exist_ok=True); os.chdir("/tmp/rxn")
_SKILL = "/SciAgent-Skills/skills/scientific-computing/neb-irc-activation-energy/scripts"
for name in ("setup_env.sh", "pipeline.yaml", "check_result.py", "make_visuals.py"):
    open(name, "w").write(read_file(f"{_SKILL}/{name}"))   # read_file = your file tool
```

Then check for the tools, installing only if missing. Inside a pixi/conda project, invoke via
the project runner (e.g. `pixi run xtb`) instead.

```bash
cd /tmp/rxn
command -v xtb && command -v pysis && echo "already installed" || \
  bash setup_env.sh           # fetches xtb binary + pip-installs pysisyphus, ~2-3 min
source "${ROOT:-${HOME:-/tmp}/xtbenv}/env.sh"
```

## Quick Start

```bash
# in the local scratch dir, scripts materialized, env sourced (see Prerequisites)
# reactant.xyz and product.xyz prepared with identical atom ordering
# edit pipeline.yaml: set charge/mult (and alpb solvent) for YOUR system before running
pysis pipeline.yaml > pipeline.log 2>&1          # preopt -> NEB -> TS opt -> IRC
python3 check_result.py pipeline.log             # three verification gates + dE‡, dE_rxn
# only report the barrier if every gate passes
```

## Workflow

### Step 1: Set up the environment

`xtb` ships prebuilt binaries on GitHub releases and `pysisyphus` installs from PyPI, so
neither needs conda-forge. Keep threads matched to physical cores — on one core, `OMP_NUM_THREADS=1`.

```bash
bash setup_env.sh
source "${ROOT:-${HOME:-/tmp}/xtbenv}/env.sh"
xtb --version && python3 -c "from importlib.metadata import version; print('pysisyphus', version('pysisyphus'))"
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
which produces atom clashes the NEB then wastes cycles undoing. **Set `charge` and `mult` in
`pipeline.yaml` before running** — the default `charge: 0` is wrong for any ion, and a wrong
charge converges silently to a meaningless TS. Add `alpb: <solvent>` for solution reactions.
Whatever you set here must match every standalone `xtb` call in Step 6. Raise `max_cycles` to
150–200 above ~50 atoms.

```bash
pysis pipeline.yaml > pipeline.log 2>&1
tail -40 pipeline.log            # confirm it reached endopt/IRC and printed the BARRIERS block
```

Read ΔE‡ and the reaction energy from the pipeline's own **`| BARRIERS |`** block (referenced
to the reactant endpoint), not from a NEB-image estimate:

```
  Left:     0.00 kJ mol-1      # reactant endpoint
    TS:   107.84 kJ mol-1      # dE‡ = 107.84 kJ/mol (TS - Left)
 Right:    10.19 kJ mol-1      # dE_rxn = 10.19 kJ/mol (Right - Left)
```

### Step 5: Verify the transition state (three gates)

Never report a barrier before this passes. The checker parses the log and applies all three
gates, returning exit code 0 only if every one passes.

```bash
python3 check_result.py pipeline.log
# [PASS] imaginary frequencies  exactly 1 at -621.8 cm-1
# [PASS] IRC endpoints          forward and backward matched distinct inputs
# [PASS] NEB profile            elementary, single barrier, span 107.5 kJ/mol
#   electronic barrier dE‡ (GFN2-xTB): 107.8 kJ/mol = 25.77 kcal/mol
```

### Step 6: Compute thermochemistry and report the barrier

At minimum report ΔE‡ and the level of theory. For comparison against experimental rates the
user needs ΔG‡, which requires thermal corrections from Hessians on the TS and reactant.

**Every standalone `xtb` call must use the same `--chrg`, `--uhf`, and solvent as `pipeline.yaml`,
and run on the pipeline's optimized endpoint/TS geometries — not the raw input.** A gas-phase
Hessian against a solvated barrier (or a missing `--chrg`) produces a nonsensical ΔG‡ — a
negative value is the usual symptom. Use `forward_end_final_geometry.xyz` (the relaxed reactant
endpoint) and `ts_final_geometry.xyz`.

```bash
# charge -1, aqueous, matching a pipeline.yaml with `charge: -1` and `alpb: water`
xtb forward_end_final_geometry.xyz --hess --gfn 2 --alpb water --chrg -1 --uhf 0 > r_hess.log 2>&1
xtb ts_final_geometry.xyz          --hess --gfn 2 --alpb water --chrg -1 --uhf 0 > ts_hess.log 2>&1
# dG‡ = G(TS) - G(reactant); take the difference of "TOTAL FREE ENERGY"
grep -i "TOTAL FREE ENERGY" r_hess.log ts_hess.log
```

### Step 7: Generate the two visual deliverables

Always deliver both, alongside the numbers. `make_visuals.py` produces them in one call: the
IRC energy profile (`irc_energy_profile.png`) and the animated TS imaginary-mode viewer
(`ts_imaginary_mode.html`). It reads gfn/charge/mult/solvent straight from `pipeline.yaml`, so
the IRC single-point energies are recomputed at the pipeline's exact level — no need to
re-specify them (override with `--charge/--mult/--alpb/--gfn` only if the pipeline was edited
after running).

```bash
python3 make_visuals.py            # -> irc_energy_profile.png + ts_imaginary_mode.html
# recomputes ~2N single points along the IRC (N = images per direction); cheap at xTB level
```

The IRC energies are recomputed per frame because pysisyphus writes `forward_irc.trj` /
`backward_irc.trj` with bare `step N` comment lines that carry no energy. The animation reuses
`ts_imaginary_mode_000.trj`, which `tsopt: do_hess: True` already wrote — open the HTML in a
browser (it pulls 3Dmol.js from a CDN) to see the mode play back and forth.

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

**Submerged barriers.** For an ion + neutral in the gas phase (e.g. an anionic SN2), the TS
often sits *below* the separated reactants because the ion–dipole pre-reaction complex is deep.
A negative ΔE‡/ΔG‡ measured against separated reactants is then physically real, not a bug —
but it means the reference state must be the pre-reaction complex, and/or you should add
solvation (`alpb`), which raises the barrier back to a positive, experiment-comparable value.
This is exactly why the pipeline references the barrier to the reactant *endpoint*, and why the
thermochemistry Hessians must use the same solvent as the pipeline.

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
- `ts_imaginary_mode_000.trj` — TS displaced along the imaginary mode (input to the animation)
- `irc_energy_profile.png` — IRC step vs relative energy, TS marked (Step 7)
- `ts_imaginary_mode.html` — animated 3D viewer of the imaginary vibrational mode (Step 7)
- A barrier: ΔE‡ from the log, ΔG‡ after applying Hessian thermal corrections

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `xtb: command not found` | Env not sourced | `source "${ROOT:-${HOME:-/tmp}/xtbenv}/env.sh"` in every new shell |
| `scripts/…: No such file or directory` / GitHub 404 | Bundled scripts not on sandbox path | Materialize them via the leading-slash skill path + `read_file` (Prerequisites); don't fetch from GitHub |
| `setup_env.sh: HOME: unbound variable` | `HOME` unset under `set -u` | Fixed in the shipped script; if patching, `export HOME="${HOME:-/tmp}"` first |
| `PermissionError` on a symlink mid-run | pysisyphus symlinks on a mounted/s3fs dir | Run in a local dir (`/tmp/rxn/`), copy results back (Prerequisites) |
| ΔG‡ negative or absurd | Hessian charge/solvent ≠ pipeline, or raw input geometry used | Match `--chrg`/`--uhf`/`alpb` to `pipeline.yaml`; use the optimized endpoint geometry (Step 6) |
| Barrier below separated reactants | Submerged barrier for ion + neutral | Expected in gas phase; reference to the pre-reaction complex and/or add `alpb` solvation |
| NEB profile nearly flat, TS search aborts | Endpoints in the same basin | Move the reacting fragment further out (Step 3) |
| Path is chemically nonsensical | Permuted atom order between endpoints | Rebuild product from a copy of the reactant (Step 2) |
| Zero imaginary frequencies | Optimizer landed on a minimum | Perturb along the NEB tangent, rerun tsopt |
| Two or more imaginary frequencies | Higher-order saddle point | Displace along the lowest non-reactive mode, reoptimize |
| IRC endpoints don't match inputs | TS connects different species | Do not report; find the TS for the intended reaction |
| Job killed / never finishes | System too large for the budget | Check `references/feasibility.md`; split stages or shrink the model |
| `qm` optimizer crashes on cycle 1 | QuickMin instability | Use `type: lbfgs` under `opt` (the template default) |
| IRC plot flat / all-zero energies | Read `*_irc.trj` comment lines (no energy there) | `make_visuals.py` recomputes per-frame single points — use it instead of parsing the trj |
| `No imaginary-mode trajectory found` | `ts_imaginary_mode_000.trj` absent | Ensure `tsopt: do_hess: True` ran; re-run tsopt so the Hessian/mode is written |
| Animation HTML blank | 3Dmol.js blocked (offline / strict CSP) | Open with network access; the viewer loads 3Dmol from a CDN |

## Bundled Resources

- `scripts/setup_env.sh` — installs xtb (GitHub release) + pysisyphus (PyPI), writes `env.sh`
- `scripts/pipeline.yaml` — full preopt→NEB→TSopt→IRC→endopt template with inline comments
- `scripts/check_result.py` — automated verification of the three gates (exit 0 = all pass)
- `scripts/make_visuals.py` — builds `irc_energy_profile.png` + `ts_imaginary_mode.html` in one call
- `references/feasibility.md` — measured timings, atom-count sizing, what DFT can/can't do here
- `references/energetics.md` — ΔE‡/ΔH‡/ΔG‡ definitions, thermochemistry, reporting conventions

## References

- [xtb documentation](https://xtb-docs.readthedocs.io/) — GFN2-xTB methods and CLI
- [pysisyphus documentation](https://pysisyphus.readthedocs.io/) — COS/NEB, TS optimizers, IRC
- Bannwarth, Ehlert, Grimme, *J. Chem. Theory Comput.* 2019, 15, 1652 — GFN2-xTB method paper
- Steinmetzer, Kupfer, Gräfe, *Int. J. Quantum Chem.* 2021, 121, e26550 — pysisyphus paper
- [ASE](https://wiki.fysik.dtu.dk/ase/) / [PySCF](https://pyscf.org/) — geometry I/O and DFT single points
