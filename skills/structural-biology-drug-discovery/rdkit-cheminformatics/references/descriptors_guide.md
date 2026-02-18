# RDKit Molecular Descriptors Guide

Complete reference for molecular descriptors available through `rdkit.Chem.Descriptors`.

## Quick Calculation

```python
from rdkit.Chem import Descriptors

# All descriptors at once
desc_dict = Descriptors.CalcMolDescriptors(mol)

# List all available descriptor names
all_names = [name for name, _ in Descriptors._descList]
print(f"{len(all_names)} descriptors available")
```

## Physicochemical Descriptors

| Descriptor | Function | Description | Drug-like Range |
|-----------|----------|-------------|-----------------|
| MolWt | `Descriptors.MolWt(mol)` | Average molecular weight (Da) | 150-500 |
| ExactMolWt | `Descriptors.ExactMolWt(mol)` | Monoisotopic mass | 150-500 |
| HeavyAtomMolWt | `Descriptors.HeavyAtomMolWt(mol)` | Weight without hydrogens | - |
| MolLogP | `Descriptors.MolLogP(mol)` | Wildman-Crippen LogP | -0.4 to 5.6 |
| MolMR | `Descriptors.MolMR(mol)` | Molar refractivity | 40-130 |
| TPSA | `Descriptors.TPSA(mol)` | Topological polar surface area | 20-140 Å² |
| LabuteASA | `Descriptors.LabuteASA(mol)` | Labute approximate surface area | - |

## Hydrogen Bond Descriptors

| Descriptor | Function | Description | Drug-like Range |
|-----------|----------|-------------|-----------------|
| NumHDonors | `Descriptors.NumHDonors(mol)` | Lipinski H-bond donors | 0-5 |
| NumHAcceptors | `Descriptors.NumHAcceptors(mol)` | Lipinski H-bond acceptors | 0-10 |
| NOCount | `Descriptors.NOCount(mol)` | Number of N and O atoms | - |
| NHOHCount | `Descriptors.NHOHCount(mol)` | Number of NH and OH groups | - |

## Topology & Complexity

| Descriptor | Function | Description |
|-----------|----------|-------------|
| NumRotatableBonds | `Descriptors.NumRotatableBonds(mol)` | Freely rotatable bonds |
| RingCount | `Descriptors.RingCount(mol)` | Total rings (SSSR) |
| NumAromaticRings | `Descriptors.NumAromaticRings(mol)` | Aromatic ring count |
| NumAliphaticRings | `Descriptors.NumAliphaticRings(mol)` | Non-aromatic ring count |
| NumSaturatedRings | `Descriptors.NumSaturatedRings(mol)` | Fully saturated rings |
| NumHeteroatoms | `Descriptors.NumHeteroatoms(mol)` | Non-C, non-H atoms |
| NumHeterocycles | `Descriptors.NumHeterocycles(mol)` | Rings with heteroatoms |
| FractionCSP3 | `Descriptors.FractionCSP3(mol)` | Fraction sp3 carbons (0-1) |
| HeavyAtomCount | `Descriptors.HeavyAtomCount(mol)` | Non-hydrogen atoms |
| NumValenceElectrons | `Descriptors.NumValenceElectrons(mol)` | Total valence electrons |
| NumRadicalElectrons | `Descriptors.NumRadicalElectrons(mol)` | Radical electrons |

## Connectivity Indices (Chi)

| Descriptor | Function | Description |
|-----------|----------|-------------|
| Chi0 | `Descriptors.Chi0(mol)` | Zeroth-order connectivity |
| Chi1 | `Descriptors.Chi1(mol)` | First-order connectivity |
| Chi0v | `Descriptors.Chi0v(mol)` | Valence Chi0 |
| Chi1v | `Descriptors.Chi1v(mol)` | Valence Chi1 |
| Chi2v | `Descriptors.Chi2v(mol)` | Valence Chi2 |
| Chi3v | `Descriptors.Chi3v(mol)` | Valence Chi3 |
| Chi4v | `Descriptors.Chi4v(mol)` | Valence Chi4 |
| Chi0n | `Descriptors.Chi0n(mol)` | Nonsymmetric Chi0 |
| Chi1n | `Descriptors.Chi1n(mol)` | Nonsymmetric Chi1 |
| Chi2n | `Descriptors.Chi2n(mol)` | Nonsymmetric Chi2 |

## Kappa Shape Indices

| Descriptor | Function | Description |
|-----------|----------|-------------|
| Kappa1 | `Descriptors.Kappa1(mol)` | First kappa (branching) |
| Kappa2 | `Descriptors.Kappa2(mol)` | Second kappa (linearity) |
| Kappa3 | `Descriptors.Kappa3(mol)` | Third kappa |
| HallKierAlpha | `Descriptors.HallKierAlpha(mol)` | Hall-Kier alpha value |

## Estate & VSA Descriptors

```python
# Estate indices
from rdkit.Chem import EState

# EState sum
estate_sum = sum(EState.EStateIndices(mol))

# VSA (Van der Waals Surface Area) descriptors
# Grouped by property contribution ranges
from rdkit.Chem import MolSurf

slogp_vsa = MolSurf.SlogP_VSA_(mol)  # LogP-binned VSA
smr_vsa = MolSurf.SMR_VSA_(mol)      # MR-binned VSA
peoe_vsa = MolSurf.PEOE_VSA_(mol)    # Charge-binned VSA
```

## Fragment-Based Descriptors (fr_ prefix)

RDKit includes 85 fragment-based descriptors counting specific functional groups:

| Descriptor | Function | What It Counts |
|-----------|----------|----------------|
| fr_Al_OH | `Descriptors.fr_Al_OH(mol)` | Aliphatic hydroxyl groups |
| fr_Ar_OH | `Descriptors.fr_Ar_OH(mol)` | Aromatic hydroxyl groups |
| fr_NH0 | `Descriptors.fr_NH0(mol)` | Tertiary amines |
| fr_NH1 | `Descriptors.fr_NH1(mol)` | Secondary amines |
| fr_NH2 | `Descriptors.fr_NH2(mol)` | Primary amines |
| fr_COO | `Descriptors.fr_COO(mol)` | Carboxylic acids |
| fr_COO2 | `Descriptors.fr_COO2(mol)` | Carboxylate salts |
| fr_ester | `Descriptors.fr_ester(mol)` | Ester groups |
| fr_ether | `Descriptors.fr_ether(mol)` | Ether groups |
| fr_amide | `Descriptors.fr_amide(mol)` | Amide groups |
| fr_halogen | `Descriptors.fr_halogen(mol)` | Halogen atoms |
| fr_sulfide | `Descriptors.fr_sulfide(mol)` | Sulfide groups |
| fr_nitro | `Descriptors.fr_nitro(mol)` | Nitro groups |
| fr_benzene | `Descriptors.fr_benzene(mol)` | Benzene rings |
| fr_pyridine | `Descriptors.fr_pyridine(mol)` | Pyridine rings |

## Drug-Likeness Rules Summary

| Rule | Criteria | Reference |
|------|----------|-----------|
| **Lipinski Ro5** | MW≤500, LogP≤5, HBD≤5, HBA≤10 | Lipinski 2001 |
| **Veber** | RotBonds≤10, TPSA≤140 | Veber 2002 |
| **Ghose** | 160≤MW≤480, -0.4≤LogP≤5.6, 40≤MR≤130, 20≤atoms≤70 | Ghose 1999 |
| **Egan** | LogP≤5.88, TPSA≤131.6 | Egan 2000 |
| **Muegge** | 200≤MW≤600, -2≤LogP≤5, TPSA≤150, rings≤7, carbons>4, heteroatoms>1 | Muegge 2001 |
| **Lead-like** | MW≤350, LogP≤3.5, RotBonds≤7 | Teague 1999 |

```python
def multi_rule_filter(mol):
    """Check multiple drug-likeness rules."""
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    rotb = Descriptors.NumRotatableBonds(mol)

    return {
        "Lipinski": mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10,
        "Veber": rotb <= 10 and tpsa <= 140,
        "Egan": logp <= 5.88 and tpsa <= 131.6,
        "Lead-like": mw <= 350 and logp <= 3.5 and rotb <= 7,
    }
```
