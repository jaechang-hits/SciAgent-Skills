---
name: medchem
description: >-
  Medicinal chemistry filters for drug discovery compound triage. Drug-likeness rules
  (Lipinski Ro5, Veber, Oprea, CNS, leadlike, REOS, Golden Triangle, Rule of Three),
  structural alerts (PAINS, NIBR, Lilly Demerits, Common Alerts), chemical group detection
  (hinge binders, Michael acceptors), molecular complexity metrics, property constraints,
  and a query language for composing filter logic. Built on RDKit and datamol. Use for
  hit-to-lead filtering, library design, and ADMET pre-screening. For molecular I/O and
  descriptors use rdkit-cheminformatics or datamol-cheminformatics instead.
license: Apache-2.0
---

# Medchem

## Overview

Medchem is a Python library for molecular filtering and prioritization in drug discovery. It provides hundreds of established medicinal chemistry rules, structural alerts, and chemical group detectors to triage compound libraries at scale. All filters support parallel execution and return structured results.

## When to Use

- Applying drug-likeness rules (Lipinski, Veber, Oprea, CNS, REOS) to compound libraries
- Filtering molecules by structural alerts (PAINS, NIBR, Lilly Demerits)
- Detecting specific chemical groups (hinge binders, Michael acceptors, reactive groups)
- Calculating molecular complexity metrics (Bertz, Whitlock, Barone)
- Applying custom property constraints (MW, LogP, TPSA, rotatable bonds)
- Composing complex multi-rule filter queries with Boolean logic
- For SMILES/SDF parsing, descriptors, and fingerprints use **rdkit-cheminformatics**
- For high-level molecular manipulation use **datamol-cheminformatics**

## Prerequisites

```bash
pip install medchem datamol
```

Medchem depends on RDKit and datamol. All molecule inputs are RDKit `Chem.Mol` objects; use `datamol.to_mol()` to convert from SMILES.

## Quick Start

```python
import datamol as dm
import medchem as mc

# Convert SMILES to molecules
smiles_list = ["CC(=O)OC1=CC=CC=C1C(=O)O", "c1ccccc1N", "O=C(O)c1ccccc1"]
mols = [dm.to_mol(s) for s in smiles_list]

# Apply Rule of Five + structural alerts in one pass
rule_filter = mc.rules.RuleFilters(rule_list=["rule_of_five"])
alert_filter = mc.structural.CommonAlertsFilters()

rule_results = rule_filter(mols=mols, n_jobs=-1)
alert_results = alert_filter(mols=mols, n_jobs=-1)

print(f"Rule results: {rule_results}")
print(f"Alert results: {[r['has_alerts'] for r in alert_results]}")
```

## Core API

### 1. Drug-Likeness Rules

Apply established medicinal chemistry rules via `mc.rules`. Individual rules return `bool`; `RuleFilters` applies multiple rules in batch.

```python
import medchem as mc

# Single rule on a SMILES string
passes = mc.rules.basic_rules.rule_of_five("CC(=O)OC1=CC=CC=C1C(=O)O")
print(f"Passes Ro5: {passes}")  # True

# Available individual rules:
# rule_of_five, rule_of_three, rule_of_oprea, rule_of_cns,
# rule_of_leadlike_soft, rule_of_leadlike_strict, rule_of_veber,
# rule_of_reos, rule_of_drug, golden_triangle, pains_filter
```

```python
import datamol as dm
import medchem as mc

# Batch application with RuleFilters
mols = [dm.to_mol(s) for s in smiles_list]
rfilter = mc.rules.RuleFilters(
    rule_list=["rule_of_five", "rule_of_oprea", "rule_of_cns"]
)
results = rfilter(mols=mols, n_jobs=-1, progress=True)
# Returns list of dicts: [{"rule_of_five": True, "rule_of_oprea": False, ...}, ...]
print(f"First molecule: {results[0]}")
```

### 2. Structural Alert Filters

Detect problematic structural patterns via `mc.structural`. Three filter sets cover different scope and stringency.

```python
import datamol as dm
import medchem as mc

mol = dm.to_mol("c1ccc(N)cc1")
mols = [dm.to_mol(s) for s in smiles_list]

# Common Alerts — general structural alerts from ChEMBL / literature
alert_filter = mc.structural.CommonAlertsFilters()
has_alerts, details = alert_filter.check_mol(mol)  # single molecule
batch_results = alert_filter(mols=mols, n_jobs=-1, progress=True)
# Each result: {"has_alerts": bool, "alert_details": [...], "num_alerts": int}
print(f"Alerts: {batch_results[0]}")
```

```python
import medchem as mc

# NIBR Filters — Novartis industrial filter set (returns bool list)
nibr_filter = mc.structural.NIBRFilters()
nibr_results = nibr_filter(mols=mols, n_jobs=-1)
print(f"NIBR pass: {nibr_results}")  # [True, False, ...]

# Lilly Demerits — 275 patterns, molecules rejected at >100 demerits
lilly_filter = mc.structural.LillyDemeritsFilters()
lilly_results = lilly_filter(mols=mols, n_jobs=-1)
# Each result: {"demerits": int, "passes": bool, "matched_patterns": [...]}
print(f"Lilly: {lilly_results[0]}")
```

### 3. Chemical Groups

Detect specific functional group motifs via `mc.groups.ChemicalGroup`.

Predefined groups: `hinge_binders`, `phosphate_binders`, `michael_acceptors`, `reactive_groups`.

```python
import medchem as mc

# Check for kinase hinge binders and Michael acceptors
group = mc.groups.ChemicalGroup(
    groups=["hinge_binders", "michael_acceptors"]
)

has_matches = group.has_match(mols)        # List[bool]
match_info = group.get_matches(mols[0])    # {group_name: [(atom_indices), ...]}
all_matches = group.get_all_matches(mols)  # List[Dict]
print(f"Has hinge binder: {has_matches}")

# Custom SMARTS patterns
custom = mc.groups.ChemicalGroup(
    groups=["reactive_groups"],
    custom_smarts={"trifluoromethyl_ketone": "[C;H0](=O)C(F)(F)F"}
)
```

### 4. Named Catalogs

Access curated chemical structure catalogs via `mc.catalogs`.

Available catalogs: `functional_groups`, `protecting_groups`, `reagents`, `fragments`.

```python
import medchem as mc

catalog = mc.catalogs.NamedCatalogs.get("functional_groups")
matches = catalog.get_matches(mol)
print(f"Functional group matches: {matches}")
```

### 5. Molecular Complexity

Calculate synthetic accessibility proxies via `mc.complexity`.

Methods: `bertz` (topological), `whitlock`, `barone`.

```python
import datamol as dm
import medchem as mc

mol = dm.to_mol("CC(=O)OC1=CC=CC=C1C(=O)O")

# Single molecule complexity
score = mc.complexity.calculate_complexity(mol, method="bertz")
print(f"Bertz complexity: {score:.1f}")

# Batch filtering by complexity threshold
cfilter = mc.complexity.ComplexityFilter(max_complexity=500, method="bertz")
results = cfilter(mols=mols, n_jobs=-1)
print(f"Passes complexity: {results}")  # List[bool]
```

### 6. Property Constraints

Apply custom property-based constraints via `mc.constraints.Constraints`.

```python
import medchem as mc

constraints = mc.constraints.Constraints(
    mw_range=(200, 500),
    logp_range=(-2, 5),
    tpsa_max=140,
    rotatable_bonds_max=10,
    hbd_max=5,
    hba_max=10,
    rings_range=(1, 5),
    aromatic_rings_max=3,
)
results = constraints(mols=mols, n_jobs=-1)
# Each result: {"passes": bool, "violations": ["mw_range", ...]}
print(f"Violations: {results[0]}")
```

### 7. Query Language

Compose complex filter logic with Boolean expressions via `mc.query`.

```python
import medchem as mc

# Parse a query combining rules, alerts, and property checks
query = mc.query.parse("rule_of_five AND NOT common_alerts")
results = query.apply(mols=mols, n_jobs=-1)  # List[bool]
print(f"Passing: {sum(results)}/{len(results)}")

# More complex queries
q2 = mc.query.parse("rule_of_cns AND complexity < 400")
q3 = mc.query.parse("(rule_of_five OR rule_of_oprea) AND NOT pains_filter")
q4 = mc.query.parse("mw > 200 AND mw < 500 AND logp < 5")
```

### 8. Functional API & Utilities

Shortcut functions in `mc.functional` and utilities in `mc.utils`.

```python
import medchem as mc

# Functional API — one-liner filters
nibr_ok = mc.functional.nibr_filter(mols=mols, n_jobs=-1)    # List[bool]
alerts = mc.functional.common_alerts_filter(mols=mols, n_jobs=-1)
lilly = mc.functional.lilly_demerits_filter(mols=mols, n_jobs=-1)

# Utilities
standardized = mc.utils.standardize_mol(mol)  # sanitize, neutralize charges
batch_out = mc.utils.batch_process(
    mols=mols, func=mc.complexity.calculate_complexity,
    n_jobs=-1, progress=True, batch_size=100
)
```

## Key Concepts

### Rule Thresholds Quick Reference

| Rule | MW | LogP | HBD | HBA | RotBonds | TPSA | Other |
|------|----|----- |-----|-----|----------|------|-------|
| Ro5 (Lipinski) | ≤500 | ≤5 | ≤5 | ≤10 | — | — | — |
| Veber | — | — | — | — | ≤10 | ≤140 | — |
| Oprea (lead) | 200-350 | -2 to 4 | — | — | ≤7 | — | Rings ≤4 |
| Leadlike Soft | 250-450 | -3 to 4 | — | — | ≤10 | — | — |
| Leadlike Strict | 200-350 | -2 to 3.5 | — | — | ≤7 | — | Rings 1-3 |
| CNS | ≤450 | -1 to 5 | ≤2 | — | — | ≤90 | — |
| REOS | 200-500 | -5 to 5 | 0-5 | 0-10 | — | — | — |
| Ro3 (fragment) | ≤300 | ≤3 | ≤3 | ≤3 | ≤3 | ≤60 | — |
| Golden Triangle | 200-50*LogP+400 | -2 to 5 | — | — | — | — | — |
| Rule of Drug | Ro5 + Veber + no PAINS | | | | | | |

### Filter Selection by Discovery Stage

| Stage | Recommended Filters | Rationale |
|-------|-------------------|-----------|
| Initial screening | Ro5, PAINS, Common Alerts | Broad triage, remove obvious liabilities |
| Hit-to-lead | Oprea or Leadlike Soft, NIBR, Lilly | Lead-like space, industrial filters |
| Lead optimization | Rule of Drug, Leadlike Strict, Complexity | Strict drug-likeness + synthetic feasibility |
| CNS targets | Rule of CNS, TPSA ≤90, HBD ≤2 | BBB permeability requirements |
| Fragment-based | Ro3, low complexity (≤250) | Fragments have "room to grow" |

### Rules Are Guidelines, Not Absolutes

~10% of marketed drugs violate Ro5. Exceptions are common for natural products, antibiotics, PROTACs, and prodrugs. Always combine rule-based filtering with domain expertise and target-class knowledge. Different modalities (oral, IV, topical) and target classes (kinases, GPCRs, ion channels) have distinct optimal property spaces.

## Common Workflows

### Workflow 1: Compound Library Triage

Full pipeline from raw SMILES to filtered drug-like candidates.

```python
import pandas as pd
import datamol as dm
import medchem as mc

# Load compound library
df = pd.read_csv("compounds.csv")
mols = [dm.to_mol(s) for s in df["smiles"]]
print(f"Input: {len(mols)} molecules")

# Step 1: Drug-likeness rules
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_veber"])
rule_results = rfilter(mols=mols, n_jobs=-1, progress=True)

# Step 2: Structural alerts
alert_filter = mc.structural.CommonAlertsFilters()
alert_results = alert_filter(mols=mols, n_jobs=-1, progress=True)

# Step 3: Combine results
df["passes_rules"] = [all(r.values()) for r in rule_results]
df["has_alerts"] = [r["has_alerts"] for r in alert_results]
df["drug_like"] = df["passes_rules"] & ~df["has_alerts"]

filtered = df[df["drug_like"]]
print(f"Output: {len(filtered)} drug-like molecules ({len(filtered)/len(df)*100:.1f}%)")
filtered.to_csv("filtered_compounds.csv", index=False)
```

### Workflow 2: Lead Optimization Filter Cascade

Apply progressively stricter filters with detailed reporting.

```python
import datamol as dm
import medchem as mc
import pandas as pd

mols = [dm.to_mol(s) for s in smiles_list]

# Cascade: rules → structural alerts → complexity → Lilly demerits
filters = [
    ("Leadlike Strict", mc.rules.RuleFilters(rule_list=["rule_of_leadlike_strict"])),
    ("NIBR Alerts", mc.structural.NIBRFilters()),
    ("Complexity ≤400", mc.complexity.ComplexityFilter(max_complexity=400)),
    ("Lilly Demerits", mc.structural.LillyDemeritsFilters()),
]

surviving = list(range(len(mols)))
for name, filt in filters:
    results = filt(mols=[mols[i] for i in surviving], n_jobs=-1)
    # Handle different result formats
    if isinstance(results[0], dict):
        passed = [i for i, r in zip(surviving, results)
                  if r.get("passes", not r.get("has_alerts", True))]
    else:
        passed = [i for i, r in zip(surviving, results) if r]
    print(f"{name}: {len(surviving)} → {len(passed)}")
    surviving = passed

print(f"Final candidates: {len(surviving)} / {len(mols)}")
```

## Key Parameters

| Parameter | Module | Default | Range | Effect |
|-----------|--------|---------|-------|--------|
| `rule_list` | `RuleFilters` | — | See rules table | Which drug-likeness rules to apply |
| `n_jobs` | All filters | `1` | `-1` to N | Parallel workers (-1 = all cores) |
| `progress` | All filters | `False` | bool | Show progress bar |
| `max_complexity` | `ComplexityFilter` | — | 0-1000+ | Bertz complexity threshold |
| `method` | `calculate_complexity` | `"bertz"` | bertz/whitlock/barone | Complexity metric |
| `mw_range` | `Constraints` | `None` | tuple(float, float) | Molecular weight range (Da) |
| `logp_range` | `Constraints` | `None` | tuple(float, float) | LogP range |
| `tpsa_max` | `Constraints` | `None` | 0-200+ | Max topological polar surface area |
| `groups` | `ChemicalGroup` | — | list of names | Predefined chemical groups to detect |
| `custom_smarts` | `ChemicalGroup` | `None` | dict | Custom SMARTS patterns {name: SMARTS} |

## Best Practices

1. **Start broad, then narrow**: Apply permissive filters first (Ro5, PAINS), then progressively tighten (NIBR, Lilly, complexity) as the pipeline narrows the candidate set.

2. **Always use parallelization**: For libraries >1000 molecules, set `n_jobs=-1` to use all CPU cores.

3. **Combine rules with structural alerts**: Rules check physicochemical properties; alerts check substructure patterns. Both are needed for robust triage.

4. **Anti-pattern — blind filtering**: Do not blindly reject everything that fails Ro5. Consider the target class and modality before filtering.

5. **Anti-pattern — ignoring prodrugs**: Prodrugs intentionally violate standard rules. Flag them as exceptions rather than filtering them out.

6. **Document filtering decisions**: Track which molecules were removed and why for reproducibility and regulatory compliance.

7. **Validate with known actives**: Run your filter cascade on known active compounds for your target to estimate false-positive rate.

## Common Recipes

### Recipe: DataFrame Integration

```python
import pandas as pd
import datamol as dm
import medchem as mc

df = pd.read_csv("molecules.csv")
df["mol"] = df["smiles"].apply(dm.to_mol)

rfilter = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_cns"])
results = rfilter(mols=df["mol"].tolist(), n_jobs=-1)

df["passes_ro5"] = [r["rule_of_five"] for r in results]
df["passes_cns"] = [r["rule_of_cns"] for r in results]
filtered = df[df["passes_ro5"] & df["passes_cns"]]
print(f"CNS drug-like: {len(filtered)}")
```

### Recipe: Combining with ML Scoring

```python
import medchem as mc

# Rule-based pre-filter
rule_results = mc.rules.RuleFilters(rule_list=["rule_of_five"])(mols, n_jobs=-1)
filtered_mols = [mol for mol, r in zip(mols, rule_results) if r["rule_of_five"]]

# ML model scoring on filtered set (reduces compute cost)
ml_scores = ml_model.predict(filtered_mols)
candidates = [mol for mol, score in zip(filtered_mols, ml_scores) if score > 0.8]
print(f"ML-scored candidates: {len(candidates)}")
```

### Recipe: Custom SMARTS Group Screening

```python
import medchem as mc

# Define project-specific warheads for covalent inhibitor screening
custom_warheads = {
    "acrylamide": "[C;H1](=O)[CH]=[CH2]",
    "vinyl_sulfonamide": "[NH]S(=O)(=O)[CH]=[CH2]",
    "chloroacetamide": "ClCC(=O)N",
}

group = mc.groups.ChemicalGroup(groups=[], custom_smarts=custom_warheads)
has_warhead = group.has_match(mols)
warhead_mols = [mol for mol, match in zip(mols, has_warhead) if match]
print(f"Covalent warhead candidates: {len(warhead_mols)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `None` in molecule list | Invalid SMILES in input | Pre-filter: `mols = [m for m in mols if m is not None]` |
| All molecules fail Ro5 | Library is fragment-like or PPI space | Use `rule_of_three` or `rule_of_leadlike_soft` instead |
| No PAINS alerts found | Molecules are simple/fragment-like | Expected — PAINS patterns target screening-hit-size molecules |
| Lilly demerits all >100 | Highly functionalized molecules | Check individual patterns; consider raising threshold or using NIBR instead |
| Slow processing | Large library without parallelization | Set `n_jobs=-1` for parallel execution |
| `ImportError: medchem` | Missing dependency | `pip install medchem datamol` (requires RDKit) |
| Query parse error | Invalid query syntax | Check operators: `AND`, `OR`, `NOT`, comparisons: `<`, `>`, `==` |
| Inconsistent result formats | Different filter classes return different types | Check docs: `RuleFilters` → dict, `NIBRFilters` → bool, `LillyDemeritsFilters` → dict |

## Bundled Resources

### references/rules_catalog.md

Complete catalog of all medicinal chemistry rules and structural alert filters with literature references, threshold criteria, chemical group patterns, custom SMARTS examples, and stage-specific filter selection guidelines. API function signatures were consolidated into Core API code blocks above. Agent meta-instructions and promotional sections omitted per migration rules.

## Related Skills

- **rdkit-cheminformatics** — Low-level cheminformatics: SMILES/SDF parsing, descriptors, fingerprints, substructure search
- **datamol-cheminformatics** — High-level molecular manipulation: standardization, scaffolds, fragmentation, 3D conformers
- **pubchem-compound-search** — Database queries: retrieve compound properties and bioactivity data for validation

## References

- Lipinski CA et al. Adv Drug Deliv Rev (1997) 23:3-25 — Rule of Five
- Veber DF et al. J Med Chem (2002) 45:2615-2623 — Veber rules
- Oprea TI et al. J Chem Inf Comput Sci (2001) 41:1308-1315 — Lead-likeness
- Baell JB & Holloway GA. J Med Chem (2010) 53:2719-2740 — PAINS filters
- Congreve M et al. Drug Discov Today (2003) 8:876-877 — Rule of Three
- Johnson TW et al. J Med Chem (2009) 52:5487-5500 — Golden Triangle
- Walters WP & Murcko MA. Adv Drug Deliv Rev (2002) 54:255-271 — REOS
- Official docs: https://medchem-docs.datamol.io/
- GitHub: https://github.com/datamol-io/medchem
