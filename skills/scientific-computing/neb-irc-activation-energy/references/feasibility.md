# Feasibility and sizing

Use this to decide whether a job fits before starting it. The most common way to waste a run
is to launch one that could never finish. Timings below were measured on a single Intel Xeon
2.10 GHz core; scale roughly linearly with clock speed and modestly with core count (xTB
parallel efficiency is limited).

## Measured timings

**GFN2-xTB with ALPB solvation, single core:**

| Atoms | gradient | full opt | Hessian |
|---|---|---|---|
| 20 | 0.04 s | 0.4 s | 0.7 s |
| 50 | 0.06 s | 2.1 s | 8.5 s |
| 80 | 0.14 s | 4.9 s | 31.3 s |

**B3LYP via PySCF, single core:**

| System | basis functions | SCF | gradient |
|---|---|---|---|
| 9 atoms / def2-SVP | 72 | 5.9 s | 4.7 s |
| 20 atoms / STO-3G | 44 | 10.2 s | 5.3 s |
| 20 atoms / def2-SVP | 154 | 46.4 s | 38.2 s |

**Validated end-to-end run.** Malonaldehyde intramolecular proton transfer, 9 atoms, the
complete pipeline through IRC and endpoint verification: **19 seconds wall clock**, 26 MB of
scratch, barrier 15.7 kJ/mol against a literature value near 4 kcal/mol.

## Sizing the pipeline

A full run costs roughly 1,000–1,500 gradient calls plus 2–3 Hessians. Applying the measured
per-call costs (GFN2-xTB, single core):

| Atoms | ideal | with retries | ~60 min budget |
|---|---|---|---|
| ~10 | 20 s | 1 min | trivial |
| ~30 | 1 min | 3–5 min | comfortable |
| ~50 | 2 min | 5–10 min | comfortable |
| ~80 | 5 min | 15–25 min | fits |
| ~150 | 16 min | 40–60 min | borderline, checkpoint |
| 250+ | Hessian dominates | 2 h+ | split into stages |

Above ~150 atoms the numerical Hessian, not the NEB, becomes the bottleneck. Budget 30–50% of
runs for a retry: non-convergence and failed verification gates are routine. Charged,
open-shell, and transition-metal systems fail more often.

## Where DFT fits and where it does not

**DFT NEB is out of reach at any system size.** A 20-atom DFT gradient costs ~85 s, so the
~1,000 gradient calls a NEB needs is a multi-day job. This is not a convergence-threshold
tuning problem.

**DFT geometry optimization** is viable only up to ~15–20 atoms — 40–60 cycles at ~85 s each
already runs long at 20 atoms.

**DFT single-point refinement** is the one place DFT fits comfortably: recompute the electronic
energy on 3 structures (reactant, TS, product) at ≤30 atoms in minutes. Take xTB-optimized
geometries and thermal corrections, replace only the electronic energy (see
`energetics.md` for the composite formula).

**Coupled cluster** (DLPNO-CCSD(T) etc.) needs ORCA and more memory than a small node has;
treat it as off-box.

## Method availability constraints

The install route (`setup_env.sh`) uses GitHub-release binaries and PyPI, not conda-forge.
That combination gives xtb, pysisyphus, PySCF, ASE, and geomeTRIC. It does **not** give ORCA,
Psi4, or CREST, which are distributed through conda-forge or require a Fortran compiler. If a
job needs those, run it on a node where they are installed rather than trying to build them.

**Conformer ensemble search** without CREST: ASE-driven random torsion sampling followed by
xtb optimization, or RDKit ETKDG embedding. Neither matches CREST's metadynamics coverage.

## Recommended division of labour

Treat the xTB pipeline as development and screening: lock down geometries, verification gates,
and thermal corrections cheaply, then hand DFT refinement (single points on 3 structures) to a
multi-core node. Requesting 16–32 cores per DFT job is the right granularity — parallel
efficiency falls off beyond that, so throughput comes from many independent jobs, not one wide
one.
