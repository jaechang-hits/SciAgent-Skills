# Receptor Preparation Guide for Molecular Docking

Detailed reference for preparing protein receptors for AutoDock Vina docking.

## Overview

Receptor preparation is the most critical step in a docking workflow. Poor preparation leads to unreliable results regardless of docking parameters. This guide covers common scenarios and decision points.

## Standard Preparation Pipeline

```
PDB file → Clean (remove water, ions, ligands) → Add hydrogens → Assign charges → Convert to PDBQT
```

### 1. Obtain and Clean the Structure

```python
import prody

# Fetch from PDB
structure = prody.parsePDB("1HPV")

# Remove water, ions, and co-crystallized ligands
protein = structure.select("protein")

# For specific chain:
# protein = structure.select("protein and chain A")

prody.writePDB("receptor_clean.pdb", protein)
```

### 2. Handle Missing Residues

**Check for gaps**:
```python
# Inspect for missing residues
residues = protein.select("name CA").getResnums()
gaps = [i for i in range(1, len(residues)) if residues[i] - residues[i-1] > 1]
if gaps:
    print(f"WARNING: Missing residues at positions: {[residues[g] for g in gaps]}")
```

**Decision tree**:
- Missing residues **far from binding site** (>10 Å): safe to ignore
- Missing residues **near binding site**: must model them
  - Use MODELLER, Swiss-Model, or AlphaFold to fill gaps
  - Or choose a different PDB structure with complete binding site

### 3. Protonation States

**Why it matters**: Histidine can be HID (Nδ), HIE (Nε), or HIP (both, charged). Asp/Glu may be protonated at low pH. Wrong protonation changes hydrogen bonding.

**Tools**:
| Tool | Method | Best for |
|------|--------|----------|
| `PDB2PQR` | Empirical pKa | Quick standard protonation |
| `PROPKA` | Empirical pKa | pH-dependent protonation |
| `H++` | Poisson-Boltzmann | Buried residues |
| `reduce` (from Phenix) | Geometry-based | Adding hydrogens only |

**Using PDB2PQR (command line)**:
```bash
pdb2pqr30 --ff AMBER --with-ph 7.4 --drop-water receptor_clean.pdb receptor_protonated.pqr
```

**Using ADFR Suite prepare_receptor (handles protonation automatically)**:
```bash
prepare_receptor -r receptor_clean.pdb -o receptor.pdbqt -A hydrogens
```

The `-A hydrogens` flag adds hydrogens according to standard protonation at pH 7.

### 4. Metal Ions and Cofactors

**Decision**:
- **Catalytic metals** (Zn²⁺ in metalloproteases, Mg²⁺ in kinases): **keep** — critical for binding
- **Crystallographic ions** (Na⁺, Cl⁻, SO₄²⁻): **remove** — artifacts
- **Cofactors** (NADH, FAD, heme): **keep if in binding site** — dock with cofactor present

```python
# Keep specific heteroatoms
protein_with_metal = structure.select("protein or (ion and name ZN)")
prody.writePDB("receptor_with_zinc.pdb", protein_with_metal)
```

### 5. Multi-chain Complexes

- **Homodimer with binding site at interface**: keep both chains
- **Heteromer with binding site on one chain**: keep relevant chains only
- **Symmetric binding sites**: dock against one chain, verify with the other

### 6. Convert to PDBQT

```bash
# Standard preparation
prepare_receptor -r receptor_protonated.pdb -o receptor.pdbqt -A hydrogens

# With specific chain
prepare_receptor -r receptor.pdb -o receptor.pdbqt -A hydrogens -C  # collapse multi-model

# Verbose mode for debugging
prepare_receptor -r receptor.pdb -o receptor.pdbqt -A hydrogens -v
```

## Common Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Non-standard residues (MSE, CSE) | prepare_receptor error | Rename MSE→MET, CSE→CYS in PDB |
| Alternate conformations | Unexpected atoms | Keep only conformer A: remove lines with altLoc ≠ A |
| Insertion codes (e.g., 52A) | Residue numbering errors | Renumber residues sequentially |
| Chain breaks | Disconnected backbone | Model missing residues or use different structure |
| Large receptor (>10k atoms) | Slow map computation | Trim to binding-site vicinity (20 Å sphere) |

## Validation Checklist

- [ ] No water molecules remaining
- [ ] Only relevant chains kept
- [ ] Missing residues handled (modeled or confirmed far from site)
- [ ] Protonation appropriate for target pH
- [ ] Catalytic metals retained, crystallographic artifacts removed
- [ ] PDBQT file opens correctly in visualization tool
- [ ] Atom count matches expected (check prepare_receptor output)
