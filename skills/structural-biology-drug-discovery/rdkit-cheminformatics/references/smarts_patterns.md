# Common SMARTS Patterns for Functional Group Detection

Reference for substructure searching with `Chem.MolFromSmarts()`.

## SMARTS Basics

| Notation | Meaning | Example |
|----------|---------|---------|
| `[#6]` | Any carbon | Matches C, c |
| `[#7]` | Any nitrogen | Matches N, n |
| `[CX3]` | Carbon with 3 connections | sp2 carbon |
| `[CX4]` | Carbon with 4 connections | sp3 carbon |
| `[OX2H]` | Oxygen with 2 connections + 1H | Hydroxyl |
| `a` | Any aromatic atom | Ring aromatic |
| `A` | Any aliphatic atom | Non-ring |
| `[R]` | In any ring | Ring atom |
| `[R2]` | In exactly 2 rings | Fused ring |
| `[r5]` | In 5-membered ring | Furan, etc. |
| `[D3]` | Degree 3 (3 explicit bonds) | Branching |

## Functional Groups — Oxygen

| Group | SMARTS | Notes |
|-------|--------|-------|
| Hydroxyl (any) | `[OX2H]` | Both aliphatic and aromatic |
| Aliphatic alcohol | `[CX4][OX2H]` | R-OH |
| Phenol | `c[OX2H]` | Ar-OH |
| Ether | `[OD2]([#6])[#6]` | R-O-R |
| Carbonyl | `[CX3]=[OX1]` | C=O (any) |
| Aldehyde | `[CX3H1](=O)[#6]` | R-CHO |
| Ketone | `[#6][CX3](=O)[#6]` | R-CO-R |
| Carboxylic acid | `[CX3](=O)[OX2H1]` | R-COOH |
| Ester | `[CX3](=O)[OX2][#6]` | R-COO-R |
| Anhydride | `[CX3](=[OX1])[OX2][CX3](=[OX1])` | RCO-O-COR |
| Epoxide | `[OX2r3]` | 3-membered ring O |
| Peroxide | `[OX2][OX2]` | R-O-O-R |

## Functional Groups — Nitrogen

| Group | SMARTS | Notes |
|-------|--------|-------|
| Primary amine | `[NX3;H2;!$(NC=O)]` | R-NH2 (not amide) |
| Secondary amine | `[NX3;H1;!$(NC=O)]` | R2-NH (not amide) |
| Tertiary amine | `[NX3;H0;!$(NC=O)]` | R3-N (not amide) |
| Amide | `[NX3][CX3](=[OX1])` | R-CONH-R |
| Primary amide | `[NX3H2][CX3](=[OX1])` | R-CONH2 |
| Nitro | `[$([NX3](=O)=O),$([NX3+](=O)[O-])]` | R-NO2 |
| Nitrile | `[NX1]#[CX2]` | R-CN |
| Imine | `[CX3]=[NX2]` | C=N |
| Hydrazine | `[NX3][NX3]` | N-N |
| Azide | `[$(-[NX2-]-[NX2+]#[NX1]),$(-[NX2]=[NX2+]=[NX1-])]` | R-N3 |
| Guanidine | `[NX3]C(=[NX2])[NX3]` | R-C(=NH)NH2 |
| Sulfonamide | `[NX3]S(=O)(=O)` | R-SO2NH-R |

## Functional Groups — Sulfur & Halogens

| Group | SMARTS | Notes |
|-------|--------|-------|
| Thiol | `[SX2H]` | R-SH |
| Sulfide (thioether) | `[#16X2]([#6])[#6]` | R-S-R |
| Disulfide | `[SX2][SX2]` | R-S-S-R |
| Sulfoxide | `[SX3](=O)([#6])[#6]` | R-SO-R |
| Sulfone | `[SX4](=O)(=O)([#6])[#6]` | R-SO2-R |
| Sulfonyl chloride | `[SX4](=O)(=O)[Cl]` | R-SO2Cl |
| Fluorine | `[F]` | Any fluorine |
| Chlorine | `[Cl]` | Any chlorine |
| Bromine | `[Br]` | Any bromine |
| Any halogen | `[F,Cl,Br,I]` | Any halide |

## Ring Systems

| Pattern | SMARTS | Notes |
|---------|--------|-------|
| Benzene | `c1ccccc1` | 6-membered aromatic |
| Pyridine | `c1ccncc1` | N-containing aromatic 6-ring |
| Pyrimidine | `c1ccnc(n1)` | 2N-containing aromatic 6-ring |
| Pyrrole | `c1cc[nH]c1` | N-containing aromatic 5-ring |
| Furan | `c1ccoc1` | O-containing aromatic 5-ring |
| Thiophene | `c1ccsc1` | S-containing aromatic 5-ring |
| Imidazole | `c1cnc[nH]1` | 2N aromatic 5-ring |
| Indole | `c1ccc2[nH]ccc2c1` | Fused benzene-pyrrole |
| Naphthalene | `c1ccc2ccccc2c1` | Fused benzene-benzene |
| Cyclohexane | `C1CCCCC1` | Saturated 6-ring |
| Any aromatic ring | `[aR]` | Atom in aromatic ring |
| Macrocycle (>12) | `[r{13-}]` | Large ring atom |

## Drug Discovery Patterns

### PAINS (Pan-Assay Interference) Alerts

| Alert | SMARTS | Risk |
|-------|--------|------|
| Rhodanine | `[#6]1(=[#16])~[#16]~[#6](~[#8])~[#7]~1` | Frequent hitter |
| Catechol | `c1cc(O)c(O)cc1` | Redox cycling |
| Quinone | `O=C1C=CC(=O)C=C1` | Michael acceptor |
| Hydrazide | `[NX3H][NX3H]C=O` | Reactive |
| Acyl hydrazide | `C(=O)[NH][NH]` | Reactive |

### Privileged Scaffolds in Medicinal Chemistry

| Scaffold | SMARTS | Found In |
|----------|--------|----------|
| Benzodiazepine | `c1ccc2c(c1)C(=O)NC(=N2)` | Anxiolytics |
| DHP (dihydropyridine) | `C1=CC(=CC(=N1)C)C` | Ca²⁺ blockers |
| Biphenyl | `c1ccc(-c2ccccc2)cc1` | ARBs |
| Piperazine | `C1CNCCN1` | Antipsychotics |
| Piperidine | `C1CCNCC1` | Many drug classes |
| Morpholine | `C1COCCN1` | Kinase inhibitors |

## Usage Examples

```python
from rdkit import Chem

# Check for reactive functional groups
reactive_patterns = {
    "Aldehyde": "[CX3H1](=O)[#6]",
    "Michael_acceptor": "[CX3]=[CX3][CX3]=[OX1]",
    "Epoxide": "[OX2r3]",
    "Acyl_halide": "[CX3](=[OX1])[F,Cl,Br,I]",
    "Isocyanate": "[NX2]=[CX2]=[OX1]",
}

mol = Chem.MolFromSmiles("O=CC1CO1")  # Glycidaldehyde
for name, smarts in reactive_patterns.items():
    pat = Chem.MolFromSmarts(smarts)
    if mol.HasSubstructMatch(pat):
        print(f"  ALERT: {name} detected")
```

```python
# Count functional groups in a library
from collections import Counter

functional_groups = {
    "Carboxylic_acid": "[CX3](=O)[OX2H1]",
    "Primary_amine": "[NX3;H2;!$(NC=O)]",
    "Amide": "[NX3][CX3](=[OX1])",
    "Ester": "[CX3](=O)[OX2][#6]",
    "Hydroxyl": "[OX2H]",
}

counts = Counter()
for mol in mols:
    for name, smarts in functional_groups.items():
        pat = Chem.MolFromSmarts(smarts)
        if mol.HasSubstructMatch(pat):
            counts[name] += 1

for name, count in counts.most_common():
    print(f"  {name}: {count}/{len(mols)} molecules")
```
