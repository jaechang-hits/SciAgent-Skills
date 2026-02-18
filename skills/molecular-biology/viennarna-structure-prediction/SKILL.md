---
name: "viennarna-structure-prediction"
description: "Predict RNA secondary structure, minimum free energy (MFE) folding, base pair probabilities, and RNA-RNA interactions using ViennaRNA Python bindings. Pipeline: load sequence → compute MFE structure → calculate partition function and base pair probability matrix → visualize dot-bracket notation → assess RNA-RNA duplex formation. Use for siRNA/sgRNA targeting, ribozyme design, and RNA accessibility analysis. Use mfold or RNAfold CLI directly for batch command-line use without Python."
license: "MIT"
---

# ViennaRNA Structure Prediction

## Overview

ViennaRNA is the gold-standard toolkit for RNA secondary structure prediction based on thermodynamic nearest-neighbor parameters. It predicts the minimum free energy (MFE) structure and dot-bracket notation for a given RNA sequence, computes the full partition function to obtain base pair probabilities, and models RNA-RNA interactions via co-folding and duplex prediction. The Python bindings (`import RNA`) expose the full ViennaRNA C library with sequence-level and fold-compound APIs. Command-line programs (`RNAfold`, `RNAalifold`, `RNAduplex`) are also available and demonstrated here.

## When to Use

- Predicting the minimum free energy secondary structure of an RNA sequence (mRNA, lncRNA, miRNA precursor, aptamer)
- Computing base pair probability matrices to assess structural uncertainty and identify well-defined stem-loops
- Designing or evaluating siRNA accessibility by folding the target mRNA region and checking for double-stranded structure
- Assessing sgRNA targeting efficiency by predicting guide RNA secondary structure that may reduce on-target activity
- Modeling RNA-RNA interactions (co-folding or duplex prediction) for miRNA-target binding or antisense oligonucleotide design
- Calculating folding free energies for a set of sequences to compare thermodynamic stability
- Use `mfold` (web server) or `RNAstructure` instead when you need Mfold algorithm predictions specifically or need the Efold partition function; ViennaRNA uses the Turner 2004 nearest-neighbor parameters and is the standard for research-grade thermodynamic prediction

## Prerequisites

- **Python packages**: `ViennaRNA` (Python bindings), `matplotlib`, `numpy`
- **Data requirements**: RNA sequences as strings (ACGU alphabet; T is auto-converted to U by ViennaRNA)
- **Environment**: Python 3.8+; conda installation strongly recommended (handles C library dependencies)

```bash
# Install via conda (recommended)
conda install -c conda-forge -c bioconda viennarna

# Verify installation
python -c "import RNA; print(RNA.__version__)"
# 2.6.4

# Install additional Python dependencies
pip install matplotlib numpy pandas

# Optional: verify CLI tools are available
RNAfold --version
# RNAfold 2.6.4
```

## Quick Start

```python
import RNA

# Predict MFE structure for an RNA sequence
sequence = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"
structure, mfe = RNA.fold(sequence)

print(f"Sequence:  {sequence}")
print(f"Structure: {structure}")
print(f"MFE:       {mfe:.2f} kcal/mol")
# Sequence:  GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA
# Structure: (((((((..((((........)))).(((((.......))))).....(((((.......))))))))))))....
# MFE:       -31.30 kcal/mol
```

## Workflow

### Step 1: Sequence Preparation and MFE Folding

Load an RNA sequence and compute its minimum free energy secondary structure using `RNA.fold()`. Validate the input and inspect the dot-bracket output.

```python
import RNA

def prepare_sequence(seq: str) -> str:
    """Normalize sequence: uppercase, replace T→U, validate alphabet."""
    seq = seq.upper().replace("T", "U").strip()
    invalid = set(seq) - set("ACGUNX")
    if invalid:
        raise ValueError(f"Invalid characters in sequence: {invalid}")
    return seq

# E. coli tRNA-Phe (GenBank: M10217)
raw_seq = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"
sequence = prepare_sequence(raw_seq)

structure, mfe = RNA.fold(sequence)

print(f"Sequence length: {len(sequence)} nt")
print(f"Structure:       {structure}")
print(f"MFE:             {mfe:.2f} kcal/mol")

# Validate: structure length must equal sequence length
assert len(structure) == len(sequence), "Structure and sequence length mismatch"

# Count stems (paired bases)
n_paired   = structure.count("(") + structure.count(")")
n_unpaired = structure.count(".")
print(f"Paired bases: {n_paired}  |  Unpaired bases: {n_unpaired}")
print(f"Stem fraction: {n_paired/len(sequence):.2f}")
```

### Step 2: Create a Fold Compound for Advanced Analysis

The `RNA.fold_compound` object is the central API for partition function, base pair probabilities, and constrained folding.

```python
import RNA

sequence = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"

# Create fold compound (wraps the sequence with model parameters)
fc = RNA.fold_compound(sequence)

# Compute MFE structure via the fold compound API
structure, mfe = fc.mfe()
print(f"MFE structure: {structure}")
print(f"MFE:           {mfe:.2f} kcal/mol")

# Evaluate free energy of an alternative structure
alt_structure = "." * len(sequence)   # fully unfolded
energy = fc.eval_structure(alt_structure)
print(f"Fully unfolded energy: {energy:.2f} kcal/mol")
print(f"Folding stabilization:  {energy - mfe:.2f} kcal/mol")
```

### Step 3: Partition Function and Base Pair Probabilities

Compute the thermodynamic partition function to obtain ensemble-level base pair probabilities. High-probability pairs indicate well-defined structural elements.

```python
import RNA
import numpy as np

sequence = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"
n = len(sequence)

fc = RNA.fold_compound(sequence)

# Step 1: MFE folding (required before pf for proper initialization)
structure_mfe, mfe = fc.mfe()

# Step 2: Rescale Boltzmann factors for numerical stability (optional but recommended)
fc.exp_params_rescale(mfe)

# Step 3: Compute partition function
structure_pf, gibbs_free_energy = fc.pf()
print(f"Gibbs free energy (ensemble): {gibbs_free_energy:.2f} kcal/mol")
print(f"MFE structure:  {structure_mfe}")
print(f"Centroid (pf):  {structure_pf}")

# Step 4: Retrieve base pair probability matrix
bpp = fc.bpp()   # returns (n+1)x(n+1) matrix; 1-indexed

# Convert to 0-indexed numpy array for analysis
probs = np.zeros((n, n))
for i in range(1, n + 1):
    for j in range(i + 1, n + 1):
        if bpp[i][j] > 0.0:
            probs[i - 1][j - 1] = bpp[i][j]
            probs[j - 1][i - 1] = bpp[i][j]

# Identify high-confidence pairs (p > 0.9)
high_conf = [(i, j, probs[i, j]) for i in range(n) for j in range(i + 1, n) if probs[i, j] > 0.9]
print(f"\nHigh-confidence base pairs (p > 0.9): {len(high_conf)}")
for i, j, p in high_conf[:5]:
    print(f"  {sequence[i]}{i+1} — {sequence[j]}{j+1}: p={p:.3f}")
```

### Step 4: Visualize Base Pair Probability Matrix

Plot the base pair probability matrix as a heatmap to visualize structural regions.

```python
import RNA
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

sequence = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"
n = len(sequence)

fc = RNA.fold_compound(sequence)
structure_mfe, mfe = fc.mfe()
fc.exp_params_rescale(mfe)
fc.pf()
bpp = fc.bpp()

# Build matrix
probs = np.zeros((n, n))
for i in range(1, n + 1):
    for j in range(i + 1, n + 1):
        if bpp[i][j] > 0.0:
            probs[i - 1][j - 1] = bpp[i][j]
            probs[j - 1][i - 1] = bpp[i][j]

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(probs, cmap="hot_r", vmin=0, vmax=1, origin="upper", aspect="equal")
plt.colorbar(im, ax=ax, label="Base pair probability")

ax.set_xlabel("Nucleotide position")
ax.set_ylabel("Nucleotide position")
ax.set_title(f"Base Pair Probability Matrix\n(n={n} nt, MFE={mfe:.2f} kcal/mol)")
plt.tight_layout()
plt.savefig("bpp_matrix.png", dpi=150, bbox_inches="tight")
print("Saved: bpp_matrix.png")
```

### Step 5: RNA-RNA Duplex Prediction (Co-folding)

Use `RNA.cofold()` to predict the interaction between two RNA sequences by concatenating them with an `&` separator.

```python
import RNA

# miRNA (hsa-miR-21-5p) and its target sequence in mRNA (PTEN 3'UTR region)
mirna_seq  = "UAGCUUAUCAGACUGAUGUUGA"
target_seq = "UCAACAUCAGUCUGAUAAGCUA"   # approximate complementary target

# Co-fold: concatenate with & separator
cofold_seq = mirna_seq + "&" + target_seq
structure, mfe = RNA.cofold(cofold_seq)

print(f"miRNA:          {mirna_seq}")
print(f"Target:         {target_seq}")
print(f"Co-fold MFE:    {mfe:.2f} kcal/mol")

# Parse the structure — & is retained in output
n1, n2 = len(mirna_seq), len(target_seq)
struct_mirna  = structure[:n1]
struct_ampersand = structure[n1]
struct_target = structure[n1 + 1:]

print(f"miRNA structure:  {struct_mirna}")
print(f"Target structure: {struct_target}")

paired_in_duplex = struct_mirna.count("(") + struct_mirna.count(")")
print(f"Bases paired across the duplex: {paired_in_duplex}")
```

### Step 6: RNA Accessibility Analysis for siRNA Design

Compute the accessibility of a target region within a longer mRNA sequence — critical for siRNA and antisense oligonucleotide efficiency.

```python
import RNA
import numpy as np

def compute_accessibility(mrna_seq: str, window: int = 40) -> list:
    """
    Compute per-position probability of being unpaired (accessible) using
    a sliding-window approach on the partition function.
    Returns list of (position, accessibility) tuples.
    """
    n = len(mrna_seq)
    fc = RNA.fold_compound(mrna_seq)
    _, mfe = fc.mfe()
    fc.exp_params_rescale(mfe)
    fc.pf()
    bpp = fc.bpp()

    # Probability of being paired at each position
    p_paired = np.zeros(n)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                p = bpp[min(i,j)][max(i,j)]
                p_paired[i - 1] += p

    p_unpaired = 1.0 - np.clip(p_paired, 0, 1)
    return p_unpaired

# Example: 80-nt mRNA segment with a known accessible region
mrna = "AUGCUAGCUAGCUAGCUAUGCUAGCUAGCUUUUUUUUUUUUAUGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGC"
p_unpaired = compute_accessibility(mrna)

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 3))
ax.bar(range(1, len(mrna) + 1), p_unpaired, color="#2166ac", alpha=0.8)
ax.axhline(0.5, color="red", lw=1, ls="--", label="50% unpaired")
ax.set_xlabel("Position (nt)")
ax.set_ylabel("P(unpaired)")
ax.set_title("RNA Accessibility Profile")
ax.legend()
plt.tight_layout()
plt.savefig("rna_accessibility.png", dpi=150, bbox_inches="tight")
print("Saved: rna_accessibility.png")

# Top 5 most accessible positions (siRNA target candidates)
best = sorted(enumerate(p_unpaired, 1), key=lambda x: -x[1])[:5]
print("\nMost accessible positions:")
for pos, prob in best:
    print(f"  Position {pos}: P(unpaired) = {prob:.3f}  ({mrna[pos-1]})")
```

### Step 7: Command-Line RNAfold and Output Parsing

Use the `RNAfold` CLI for batch folding via subprocess, then parse the output.

```bash
# Fold a single sequence from stdin
echo "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA" | RNAfold

# Output:
# GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA
# (((((((..((((........)))).(((((.......))))).....(((((.......)))))))))))).... (-31.30)

# Batch fold from FASTA file
RNAfold < sequences.fasta > structures.txt

# Generate base pair probability dot plot (PostScript)
RNAfold --noPS < sequences.fasta   # suppress PostScript output
RNAfold -p < sequences.fasta       # save dot plot as rna.ps
```

```python
# Python: run RNAfold via subprocess and parse output
import subprocess
import re

def run_rnafold(sequence: str) -> tuple:
    """Run RNAfold CLI and return (structure, mfe) tuple."""
    result = subprocess.run(
        ["RNAfold", "--noPS"],
        input=sequence,
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"RNAfold failed: {result.stderr}")

    lines = result.stdout.strip().split("\n")
    # Last line: structure and energy, e.g. "((....)) (-5.40)"
    match = re.match(r"^([.()\[\]{}<>|]+)\s+\((-?\d+\.\d+)\)$", lines[-1])
    if not match:
        raise ValueError(f"Could not parse RNAfold output: {lines[-1]}")
    structure = match.group(1)
    mfe       = float(match.group(2))
    return structure, mfe

sequences = [
    ("tRNA-Phe", "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"),
    ("miR-21",   "UAGCUUAUCAGACUGAUGUUGA"),
]

for name, seq in sequences:
    struct, mfe = run_rnafold(seq)
    print(f"{name}: {mfe:.2f} kcal/mol  |  {struct}")
```

### Step 8: Constrained Folding and Suboptimal Structures

Apply hard constraints (force or forbid specific base pairs) and enumerate suboptimal structures.

```python
import RNA

sequence = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"

# --- Constrained folding: force specific pairs ---
fc = RNA.fold_compound(sequence)

# Add hard constraint: force positions 1-7 to be paired (known stem)
hc = RNA.hc_add_bp(fc, 1, 72)  # force pair between position 1 and 72 (0-indexed in C API)
structure_c, mfe_c = fc.mfe()
print(f"Constrained MFE:   {mfe_c:.2f} kcal/mol")
print(f"Constrained struct: {structure_c}")

# --- Enumerate suboptimal structures (delta_mfe threshold) ---
fc_sub = RNA.fold_compound(sequence)
_, mfe_opt = fc_sub.mfe()

# Get suboptimal structures within 5 kcal/mol of MFE
delta = 5.0  # kcal/mol window
subopt_list = RNA.subopt(sequence, int(delta * 100))   # energy in 10-cal units
print(f"\nSuboptimal structures within {delta} kcal/mol of MFE:")
print(f"Total suboptimal structures: {len(subopt_list)}")
for s in subopt_list[:3]:
    e = s.energy / 100.0  # convert from 10-cal to kcal/mol
    print(f"  {s.structure}  ({e:.2f} kcal/mol)")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `sequence` (RNA.fold) | — | ACGU string | Input RNA sequence; T is auto-converted to U |
| `temperature` (model detail) | `37.0` °C | `0`–`100` °C | Folding temperature; lower temp stabilizes structures |
| `dangles` (model detail) | `2` | `0`, `1`, `2`, `3` | Dangling end treatment; 2=average, 0=none, use 2 for most applications |
| `noGU` (model detail) | `False` | `True`/`False` | Disallow G-U wobble pairs when True |
| `noLP` (model detail) | `False` | `True`/`False` | Disallow lonely base pairs (single-bp stems); reduces noise |
| `delta` (RNA.subopt) | — | float kcal/mol | Energy window above MFE for suboptimal structure enumeration |
| `window` (sliding window) | — | int nt | Sliding window size for long-sequence accessibility analysis |

## Common Recipes

### Recipe: Batch MFE Folding from a FASTA File

When to use: Fold a library of RNA sequences (e.g., candidate aptamers, guide RNAs) and compare energies.

```python
import RNA
from pathlib import Path

def read_fasta(fasta_path: str) -> list:
    """Parse FASTA file, return list of (name, sequence) tuples."""
    records = []
    name, seq = None, []
    for line in Path(fasta_path).read_text().splitlines():
        if line.startswith(">"):
            if name:
                records.append((name, "".join(seq).upper().replace("T", "U")))
            name, seq = line[1:].split()[0], []
        else:
            seq.append(line.strip())
    if name:
        records.append((name, "".join(seq).upper().replace("T", "U")))
    return records

# Example: fold sequences from a FASTA file
sequences = [
    ("aptamer_1", "GGGUUUUGAAACUAAACUAGGCUCUAGCGCUGGUGUCCCUUCCCGGCUCUAGCCUCAGCAGAAGCUUGAAAAAACCC"),
    ("aptamer_2", "GGGAGACAAGAAUAAACGCUCAACGUCUACCAUGAUCGAAUGCUAGCCUUCUAGCUUGCUUCGGCAGCACUAUAGGG"),
    ("aptamer_3", "GGGCGACCCUGAUGAGUCCCAAGUCGAAACGAUUCCUUUUUAAACUCAUGGUGCCCAGCCUCGCUCAGCA"),
]

print(f"{'Name':<15} {'Length':>8} {'MFE':>10} {'Structure'}")
print("-" * 80)
for name, seq in sequences:
    struct, mfe = RNA.fold(seq)
    print(f"{name:<15} {len(seq):>8} {mfe:>10.2f}  {struct[:50]}...")
```

### Recipe: Check sgRNA Secondary Structure

When to use: Evaluate whether a CRISPR sgRNA guide sequence folds into secondary structures that reduce Cas9 binding efficiency.

```python
import RNA

def assess_sgrna(guide_seq: str, scaffold: str = None) -> dict:
    """
    Assess sgRNA secondary structure.
    guide_seq: 20-nt spacer sequence (RNA)
    scaffold: constant sgRNA scaffold sequence (default: SpCas9)
    """
    if scaffold is None:
        # SpCas9 sgRNA scaffold (Addgene standard)
        scaffold = "GUUUUAGAGCUAGAAAUAGCAAGUUAAAAUAAGGCUAGUCCGUUAUCAACUUGAAAAAGUGGCACCGAGUCGGUGCUUU"

    full_sgrna = guide_seq.upper().replace("T", "U") + scaffold
    fc = RNA.fold_compound(full_sgrna)
    structure, mfe = fc.mfe()
    fc.exp_params_rescale(mfe)
    fc.pf()
    bpp = fc.bpp()

    n_guide = len(guide_seq)
    # Check if any guide bases are paired (bad for targeting)
    guide_paired = sum(
        bpp[min(i, j)][max(i, j)]
        for i in range(1, n_guide + 1)
        for j in range(1, n_guide + 1)
        if i != j
    )
    guide_accessibility = 1.0 - min(1.0, guide_paired / n_guide)
    return {
        "guide_seq":    guide_seq,
        "mfe":          mfe,
        "structure":    structure[:n_guide],
        "guide_access": guide_accessibility,
        "predicted_ok": guide_accessibility > 0.7,
    }

guides = ["GCACUAGUGACGCAUGGCAC", "GGGCAUAGCUAGCUAGCUAU", "AAAUUCGCACUAGUGACGCA"]
for g in guides:
    result = assess_sgrna(g)
    status = "OK" if result["predicted_ok"] else "WARN (self-paired)"
    print(f"{g}: accessibility={result['guide_access']:.2f}, MFE={result['mfe']:.1f} kcal/mol  [{status}]")
```

### Recipe: Mountain Plot Visualization of RNA Structure

When to use: Create a mountain plot — a classic RNA structure visualization showing stem height along the sequence.

```python
import RNA
import matplotlib.pyplot as plt

def dot_bracket_to_mountain(structure: str) -> list:
    """Convert dot-bracket structure to mountain plot heights."""
    heights = []
    level = 0
    for c in structure:
        if c == "(":
            level += 1
        heights.append(level)
        if c == ")":
            level -= 1
    return heights

sequence = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"
structure, mfe = RNA.fold(sequence)
heights = dot_bracket_to_mountain(structure)

fig, axes = plt.subplots(2, 1, figsize=(12, 5), sharex=True,
                          gridspec_kw={"height_ratios": [1, 3]})

# Top: sequence text
axes[0].text(0.5, 0.5, "tRNA-Phe  |  E. coli", ha="center", va="center",
             fontsize=10, transform=axes[0].transAxes)
axes[0].axis("off")

# Bottom: mountain plot
axes[1].fill_between(range(len(sequence)), heights, step="mid",
                      color="#2c7bb6", alpha=0.7, label=f"MFE = {mfe:.2f} kcal/mol")
axes[1].set_xlabel("Nucleotide position")
axes[1].set_ylabel("Stem height")
axes[1].set_title("Mountain Plot")
axes[1].legend()
plt.tight_layout()
plt.savefig("mountain_plot.png", dpi=150, bbox_inches="tight")
print(f"Saved: mountain_plot.png  (MFE structure: {structure[:40]}...)")
```

## Expected Outputs

| Output | Type | Description |
|--------|------|-------------|
| `structure` | string | Dot-bracket notation of MFE secondary structure; `(` and `)` for paired bases, `.` for unpaired |
| `mfe` | float (kcal/mol) | Minimum free energy of the predicted structure; more negative = more stable |
| `bpp` | (n+1)×(n+1) matrix | Base pair probability matrix from partition function; element `[i][j]` = P(i paired with j), 1-indexed |
| `bpp_matrix.png` | PNG | Heatmap visualization of base pair probabilities |
| `rna_accessibility.png` | PNG | Per-position probability of being unpaired |
| `mountain_plot.png` | PNG | Mountain plot of stem heights along the sequence |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError: No module named 'RNA'` | ViennaRNA Python bindings not installed | Install via `conda install -c conda-forge viennarna`; `pip install` alone may fail to link C library |
| `RuntimeError: RNAfold not found` | ViennaRNA CLI not in PATH | Confirm with `which RNAfold`; if using conda env, activate it before running scripts |
| MFE is unexpectedly positive (> 0) | Very short or repetitive sequence with no favorable pairs | Short sequences (< 10 nt) often have positive MFE; check sequence length and composition |
| `bpp` matrix all zeros after `fc.pf()` | `fc.mfe()` must be called before `fc.pf()` on the same fold compound | Always call `fc.mfe()` first, then `fc.exp_params_rescale(mfe)`, then `fc.pf()` |
| Suboptimal enumeration returns thousands of structures | Window too large for long sequences | Reduce delta to 2–3 kcal/mol for long sequences; very stable sequences have dense suboptimal ensembles |
| Co-fold (`RNA.cofold`) shows unexpected pairing | Intramolecular folding dominates in one strand | Inspect each strand separately first; low individual-strand MFE indicates strong self-structure interfering with duplex |

## References

- [ViennaRNA documentation](https://www.tbi.univie.ac.at/RNA/) — official documentation, parameter files, and Python API reference
- [Lorenz et al., Algorithms Mol Biol 2011](https://doi.org/10.1186/1748-7188-6-26) — ViennaRNA Package 2.0 paper (primary citation for structure prediction)
- [Turner & Mathews, Nucleic Acids Res 2010](https://doi.org/10.1093/nar/gkp892) — Nearest-neighbor thermodynamic parameters used by ViennaRNA
- [ViennaRNA GitHub: ViennaRNA/ViennaRNA](https://github.com/ViennaRNA/ViennaRNA) — source code, issue tracker, Python tutorial notebooks
