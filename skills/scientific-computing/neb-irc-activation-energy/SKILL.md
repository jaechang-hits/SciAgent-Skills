---
name: "neb-irc-activation-energy"
description: "NEB-IRC activation energy pipeline for reaction barriers using GFN2-xTB and pysisyphus. Optimize reactant and product geometries, run CI-NEB path search, optimize the transition state with a Hessian, verify with IRC (one imaginary mode, endpoints matching reactant/product, single NEB maximum), and report the electronic and Gibbs barriers. Use when you need a transition state, reaction barrier, activation energy, minimum energy path, or intrinsic reaction coordinate. Covers reactant/product atom-ordering pitfalls, feasibility sizing for single-core runs, and thermochemistry corrections. Renders an IRC energy-profile plot and an animated TS imaginary-mode HTML viewer. For 2D reaction scheme drawing use rdkit-chemdraw-cdxml."
license: "CC-BY-4.0"
---

# NEB-IRC activation energy pipeline

## Overview

Computes a reaction activation energy end to end — optimize reactant and product, find the
minimum energy path with climbing-image NEB, refine the transition state with a Hessian, and
confirm it with IRC — using GFN2-xTB through pysisyphus. Outputs a verified TS geometry, the
barrier (ΔE‡; ΔG‡ after thermal corrections), an IRC energy profile (`irc_energy_profile.png`),
and an animated TS imaginary-mode viewer (`ts_imaginary_mode.html`). Verification is required,
not optional: a converged TS is meaningless until its single imaginary mode and IRC endpoints
are checked.

## When to Use

- Finding the transition state for an elementary reaction step and its activation energy
- Computing a reaction barrier (ΔE‡ or ΔG‡) to rank a series of related reactions
- Running a climbing-image NEB / minimum energy path between a reactant and product
- Verifying a candidate TS with IRC — does it connect the intended reactant and product?
- Screening barriers at a cheap semi-empirical level before committing DFT time

Reach for DFT on a multi-core node instead when you need quantitative agreement with
experiment; GFN2-xTB barriers are semi-quantitative (see `references/energetics.md`). For a 2D
scheme figure of the reaction, use the `rdkit-chemdraw-cdxml` skill instead.

## Prerequisites

- **Tools**: `xtb` (GFN2-xTB engine), `pysisyphus` (`pysis` CLI for the path pipeline)
- **Python**: `matplotlib` for the IRC plot (the TS animation HTML needs no packages)
- **Input**: `reactant.xyz` and `product.xyz` with **identical atom ordering** (see Step 1)
- **Environment**: single core suffices; set `OMP_NUM_THREADS` to match physical cores

**Work in a local scratch dir** (e.g. `/tmp/rxn/`), not a mounted/networked workspace:
pysisyphus creates and deletes symlinks and throws `PermissionError` mid-run on s3fs/FUSE.
Copy results out at the end.

**Materialize the bundled scripts into the scratch dir first.** They can't be run in place from
the skill directory, so use your file tools to read each one and save it into your working dir
before running it. The scripts live in this skill's `scripts/` folder (next to this SKILL.md):

- `scripts/setup_env.sh`
- `scripts/pipeline.yaml`
- `scripts/check_result.py`
- `scripts/plot_irc.py`

The TS imaginary-mode animation is **not** produced here — read the
**molecular-visualization-3dmol** skill and use its `mol_viewer.py` (Step 6).

Check for the tools; install only if missing (inside pixi/conda, invoke via `pixi run xtb`):

```bash
cd /tmp/rxn
command -v xtb && command -v pysis || bash setup_env.sh   # xtb binary + pysisyphus, ~2-3 min
source "${ROOT:-${HOME:-/tmp}/xtbenv}/env.sh"              # re-source in every new shell
```

## Workflow

### Step 1: Prepare reactant and product geometries

Most failures originate here, not in the NEB. Build the product by editing a **copy** of the
reactant so atom ordering is identical — a permuted order gives a path that is geometrically
valid and chemically meaningless. Align non-reacting groups so a spectator conformational
change does not fold into the barrier. For bimolecular reactions use a pre-reaction complex as
the reactant, not separated fragments (NEB converges poorly from infinite separation, and the
reference state changes the reported barrier — record it).

```python
# Build product from a copy of the reactant, moving only the reacting atoms.
from pathlib import Path

lines = Path("reactant.xyz").read_text().splitlines()
natoms = int(lines[0])
atoms = [ln.split() for ln in lines[2:2 + natoms]]   # [symbol, x, y, z] per atom
# ... edit ONLY the coordinates of atoms that move; keep order + symbols ...
Path("product.xyz").write_text("\n".join([str(natoms), "product"] + [" ".join(a) for a in atoms]) + "\n")
```

### Step 2: Check the endpoints sit in different basins

If the reacting groups start too close, preoptimization carries the reactant over the barrier
and both endpoints relax to the same structure; the NEB then returns a flat profile and the TS
search aborts. This looks like success in the log until it fails minutes later, so compare the
two pre-optimized endpoints on the key reacting bond.

```python
import numpy as np

def load_xyz(fn):
    lines = open(fn).read().splitlines()
    return np.array([[float(v) for v in ln.split()[1:4]] for ln in lines[2:2 + int(lines[0])]])

r, p = load_xyz("first_pre_opt.xyz"), load_xyz("last_pre_opt.xyz")   # written by preopt
i, j = 0, 5                                     # indices of the atoms whose bond changes
dr, dp = np.linalg.norm(r[i] - r[j]), np.linalg.norm(p[i] - p[j])
assert abs(dr - dp) > 0.3, "endpoints nearly identical: move the reacting fragment further out"
```

### Step 3: Run the pipeline

The template chains preopt → IDPP interpolation → CI-NEB → RS-I-RFO TS optimization with
Hessian → IRC both directions → endpoint reoptimization. **Set `charge` and `mult` in
`pipeline.yaml` before running** — the default `charge: 0` is wrong for any ion and converges
silently to a meaningless TS. Add `alpb: <solvent>` for solution reactions. Whatever you set
here must match every standalone `xtb` call in Step 5. Raise `max_cycles` to 150–200 above
~50 atoms.

```bash
pysis pipeline.yaml > pipeline.log 2>&1
tail -40 pipeline.log            # confirm it reached the endopt/IRC stage
```

ΔE‡ and the reaction energy come from the pipeline's `| BARRIERS |` block, referenced to the
reactant endpoint (`check_result.py` in Step 4 reports the same numbers):

```
  Left:     0.00 kJ mol-1      # reactant endpoint
    TS:   107.84 kJ mol-1      # dE‡ = TS - Left = 107.84 kJ/mol
 Right:    10.19 kJ mol-1      # dE_rxn = Right - Left = 10.19 kJ/mol
```

### Step 4: Verify the transition state

Never report a barrier before this passes. The checker applies all three gates (see Key
Concepts) and exits 0 only if every one passes.

```bash
python3 check_result.py pipeline.log
# [PASS] imaginary frequencies  exactly 1 at -621.8 cm-1
# [PASS] IRC endpoints          forward and backward matched distinct inputs
# [PASS] NEB profile            elementary, single barrier, span 107.5 kJ/mol
#   electronic barrier dE‡ (GFN2-xTB): 107.8 kJ/mol = 25.77 kcal/mol
```

### Step 5: Compute thermochemistry and report the barrier

Report ΔE‡ and the level of theory; for comparison against experimental rates, report ΔG‡,
which needs Hessians on the TS and reactant. **Every standalone `xtb` call must use the same
`--chrg`, `--uhf`, and solvent as `pipeline.yaml`, on the pipeline's optimized geometries — not
the raw input.** A gas-phase Hessian against a solvated barrier, or a missing `--chrg`, yields
a nonsensical (often negative) ΔG‡.

```bash
# flags must match pipeline.yaml (here: charge -1, aqueous)
xtb forward_end_final_geometry.xyz --hess --gfn 2 --alpb water --chrg -1 --uhf 0 > r_hess.log 2>&1
xtb ts_final_geometry.xyz          --hess --gfn 2 --alpb water --chrg -1 --uhf 0 > ts_hess.log 2>&1
# dG‡ = G(TS) - G(reactant), from the "TOTAL FREE ENERGY" lines
grep -i "TOTAL FREE ENERGY" r_hess.log ts_hess.log
```

### Step 6: Deliver the two visuals

**IRC energy profile** — `plot_irc.py` reads gfn/charge/mult/solvent from `pipeline.yaml` and
recomputes each IRC frame's energy at that exact level (the `*_irc.trj` comment lines carry
none). Override with `--charge/--mult/--alpb/--gfn` only if you edited the pipeline after running.

```bash
python3 plot_irc.py               # -> irc_energy_profile.png
```

**TS imaginary-mode animation** — produced by the **molecular-visualization-3dmol** skill, not
here. Read that skill and run its `mol_viewer.py` on the `ts_imaginary_mode_000.trj` that
`tsopt: do_hess: True` wrote (grab the frequency from `check_result.py` for the label):

```bash
# after materializing mol_viewer.py per the molecular-visualization-3dmol skill
python3 mol_viewer.py ts_imaginary_mode_000.trj --mode trajectory \
    --title "Transition-state mode" --subtitle "imaginary mode -621.8 cm-1" --out ts_imaginary_mode.html
```

## Key Parameters

Set in `pipeline.yaml` unless noted.

| Parameter | Section | Default | Range / Options | Effect |
|-----------|---------|---------|-----------------|--------|
| `gfn` | `calc` | `2` | `0`, `1`, `2` | GFN parametrization; `2` is the standard choice |
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
| Imaginary frequencies | 1, wrong mode | Confirm it is the bonds breaking/forming — a methyl rotation also shows exactly one |
| IRC endpoints | mismatch | TS connects other species; may be a real TS for a different reaction — do not report |
| NEB profile | multiple maxima | Not an elementary step; split at the intervening minimum and run each segment |

**Barrier definitions** differ by reference and corrections: ΔE‡ (electronic), ΔE‡+ZPE, ΔH‡,
ΔG‡ (for kinetics). For bimolecular reactions the reference state (separated reactants vs
pre-reaction complex) shifts the number — record which was used. Full table in
`references/energetics.md`.

**Submerged barriers.** For an ion + neutral in the gas phase (e.g. anionic SN2) the TS can
sit *below* the separated reactants — a negative barrier against separated reactants is real,
not a bug. Reference to the pre-reaction complex (the pipeline's endpoint) and/or add `alpb`
solvation, which lifts it to a positive, experiment-comparable value.

## Common Recipes

### Recipe: Split a multi-step reaction into elementary steps

When to use: `check_result.py` reports multiple NEB maxima — it names the intermediate image
index(es). Extract that image from the NEB path and run the pipeline on each half.

```python
from pathlib import Path

N = 5   # interior-minimum image index reported by check_result.py's NEB profile gate
lines = Path("final_geometries.trj").read_text().splitlines()   # one frame per NEB image
n = int(lines[0].split()[0])
Path("intermediate.xyz").write_text("\n".join(lines[N * (n + 2):(N + 1) * (n + 2)]) + "\n")
# then: pipeline on reactant.xyz + intermediate.xyz, and intermediate.xyz + product.xyz
```

### Recipe: Refine the electronic energy with a DFT single point

When to use: the xTB geometry is fine but you need a better barrier. Keep the xTB geometry and
thermal corrections; replace only the electronic energy on 3 structures (≤30 atoms).

```python
from pyscf import gto, dft

def electronic_energy(xyz_fn, basis="def2-svp", xc="b3lyp"):
    mol = gto.M(atom=xyz_fn, basis=basis)     # xyz file path accepted directly
    mf = dft.RKS(mol); mf.xc = xc
    return mf.kernel()                          # Hartree

dE = (electronic_energy("ts_final_geometry.xyz") - electronic_energy("reactant.xyz")) * 2625.4996
print(f"DFT dE‡ = {dE:.1f} kJ/mol (add xTB G_corr for dG‡)")
```

## Expected Outputs

- `pipeline.log` — full run log; parsed by `check_result.py`
- `ts_final_geometry.xyz` — the optimized transition state
- `final_geometries.trj` — the converged NEB path (per-image energies in comment lines)
- `ts_imaginary_mode_000.trj` — TS displaced along the imaginary mode (input to the animation)
- `irc_energy_profile.png` — from `plot_irc.py`; `ts_imaginary_mode.html` — from the molecular-visualization-3dmol skill (Step 6)
- A barrier: ΔE‡ from the BARRIERS block, ΔG‡ after Hessian thermal corrections

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `xtb: command not found` | Env not sourced | `source "${ROOT:-${HOME:-/tmp}/xtbenv}/env.sh"` in every new shell |
| `scripts/…: No such file` / GitHub 404 | Bundled scripts not copied into the workdir | Read them from this skill's `scripts/` folder with your file tools and save locally (Prerequisites); not on GitHub |
| `setup_env.sh: HOME: unbound variable` | `HOME` unset under `set -u` | Fixed in the shipped script; if patching, `export HOME="${HOME:-/tmp}"` first |
| `PermissionError` on a symlink mid-run | pysisyphus symlinks on a mounted/s3fs dir | Run in a local dir (`/tmp/rxn/`), copy results back |
| ΔG‡ negative or absurd | Hessian charge/solvent ≠ pipeline, or raw input geometry used | Match `--chrg`/`--uhf`/`alpb` to `pipeline.yaml`; use the optimized endpoint geometry (Step 5) |
| Barrier below separated reactants | Submerged barrier for ion + neutral | Expected in gas phase; reference the pre-reaction complex and/or add `alpb` |
| NEB profile nearly flat, TS aborts | Endpoints in the same basin | Move the reacting fragment further out (Step 2) |
| Path is chemically nonsensical | Permuted atom order between endpoints | Rebuild product from a copy of the reactant (Step 1) |
| Job killed / never finishes | System too large for the budget | Check `references/feasibility.md`; split stages or shrink the model |
| `qm` optimizer crashes on cycle 1 | QuickMin instability | Use `type: lbfgs` under `opt` (the template default) |
| `No imaginary-mode trajectory found` | `ts_imaginary_mode_000.trj` absent | Ensure `tsopt: do_hess: True` ran; re-run tsopt |
| Animation HTML blank | 3Dmol.js blocked (offline / strict CSP) | Open with network access; the viewer loads 3Dmol from a CDN |

## Bundled Resources

- `scripts/setup_env.sh` — installs xtb (GitHub release) + pysisyphus (PyPI), writes `env.sh`
- `scripts/pipeline.yaml` — full preopt→NEB→TSopt→IRC→endopt template with inline comments
- `scripts/check_result.py` — verification of the three gates (exit 0 = all pass); prints ΔE‡
- `scripts/plot_irc.py` — builds `irc_energy_profile.png` (recomputes IRC-frame energies at the pipeline level)
- `references/feasibility.md` — measured timings, atom-count sizing, what DFT can/can't do here
- `references/energetics.md` — ΔE‡/ΔH‡/ΔG‡ definitions, thermochemistry, reporting conventions

## Related Skills

- **molecular-visualization-3dmol** — supplies `mol_viewer.py`, which renders the TS imaginary-mode animation and can play back the IRC/NEB path; materialize it alongside this skill's scripts
- **rdkit-chemdraw-cdxml** — draw the reaction as a 2D scheme figure

## References

- [xtb documentation](https://xtb-docs.readthedocs.io/) — GFN2-xTB methods and CLI
- [pysisyphus documentation](https://pysisyphus.readthedocs.io/) — COS/NEB, TS optimizers, IRC
- Bannwarth, Ehlert, Grimme, *J. Chem. Theory Comput.* 2019, 15, 1652 — GFN2-xTB method paper
- Steinmetzer, Kupfer, Gräfe, *Int. J. Quantum Chem.* 2021, 121, e26550 — pysisyphus paper
- [ASE](https://wiki.fysik.dtu.dk/ase/) / [PySCF](https://pyscf.org/) — geometry I/O and DFT single points
