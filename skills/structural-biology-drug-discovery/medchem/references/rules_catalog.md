# Medchem Rules and Filters Catalog

Complete catalog of medicinal chemistry rules, structural alerts, and filter selection guidelines.

## Drug-Likeness Rules

### Rule of Five (Lipinski)

**Reference:** Lipinski et al., Adv Drug Deliv Rev (1997) 23:3-25

Predict oral bioavailability. ~90% of orally active drugs comply.

| Criterion | Threshold |
|-----------|-----------|
| Molecular Weight | ≤ 500 Da |
| LogP | ≤ 5 |
| H-bond Donors | ≤ 5 |
| H-bond Acceptors | ≤ 10 |

Exceptions: natural products, antibiotics, PROTACs.

### Rule of Veber

**Reference:** Veber et al., J Med Chem (2002) 45:2615-2623

Complements Ro5 — TPSA correlates with cell permeability.

| Criterion | Threshold |
|-----------|-----------|
| Rotatable Bonds | ≤ 10 |
| TPSA | ≤ 140 A² |

### Rule of Drug

Combined assessment: passes Ro5 + Veber + no PAINS substructures.

### REOS (Rapid Elimination Of Swill)

**Reference:** Walters & Murcko, Adv Drug Deliv Rev (2002) 54:255-271

| Criterion | Range |
|-----------|-------|
| Molecular Weight | 200-500 Da |
| LogP | -5 to 5 |
| H-bond Donors | 0-5 |
| H-bond Acceptors | 0-10 |

### Golden Triangle

**Reference:** Johnson et al., J Med Chem (2009) 52:5487-5500

Optimal physicochemical balance: `200 ≤ MW ≤ 50 × LogP + 400`, LogP -2 to 5.

## Lead-Likeness Rules

### Rule of Oprea

**Reference:** Oprea et al., J Chem Inf Comput Sci (2001) 41:1308-1315

Lead compounds should have "room to grow" during optimization.

| Criterion | Range |
|-----------|-------|
| Molecular Weight | 200-350 Da |
| LogP | -2 to 4 |
| Rotatable Bonds | ≤ 7 |
| Rings | ≤ 4 |

### Leadlike Soft

Permissive: MW 250-450, LogP -3 to 4, RotBonds ≤10.

### Leadlike Strict

Restrictive: MW 200-350, LogP -2 to 3.5, RotBonds ≤7, Rings 1-3.

## Fragment Rules

### Rule of Three

**Reference:** Congreve et al., Drug Discov Today (2003) 8:876-877

For fragment-based drug discovery. Fragments are grown into leads.

| Criterion | Threshold |
|-----------|-----------|
| Molecular Weight | ≤ 300 Da |
| LogP | ≤ 3 |
| H-bond Donors | ≤ 3 |
| H-bond Acceptors | ≤ 3 |
| Rotatable Bonds | ≤ 3 |
| PSA | ≤ 60 A² |

## CNS Rules

### Rule of CNS

BBB penetration requires specific properties — lower TPSA and HBD.

| Criterion | Range |
|-----------|-------|
| Molecular Weight | ≤ 450 Da |
| LogP | -1 to 5 |
| H-bond Donors | ≤ 2 |
| TPSA | ≤ 90 A² |

## Structural Alert Filters

### PAINS (Pan Assay INterference compoundS)

**Reference:** Baell & Holloway, J Med Chem (2010) 53:2719-2740

Identifies assay-interfering compounds. Categories: catechols, quinones, rhodanines, hydroxyphenylhydrazones, alkyl/aryl aldehydes, specific Michael acceptors.

Returns `True` if NO PAINS substructures found.

### Common Alerts Filters

Source: ChEMBL curation and literature. Categories:
- **Reactive Groups**: epoxides, aziridines, acid halides, isocyanates
- **Metabolic Liabilities**: hydrazines, thioureas, certain anilines
- **Aggregators**: polyaromatic systems, long aliphatic chains
- **Toxicophores**: nitro aromatics, aromatic N-oxides

Returns: `{"has_alerts": bool, "alert_details": [...], "num_alerts": int}`

### NIBR Filters

Source: Novartis Institutes for BioMedical Research. Industrial filter set balancing drug-likeness with practical medchem. Returns boolean pass/fail.

### Lilly Demerits Filter

Source: Eli Lilly, 275 structural patterns (18 years of medchem experience). Demerit-based: molecules rejected at >100 total demerits.

| Demerit Level | Score Range | Examples |
|---------------|-------------|---------|
| High | >50 | Known toxic groups, highly reactive |
| Medium | 20-50 | Metabolic liabilities, aggregation-prone |
| Low | 5-20 | Minor concerns, context-dependent |

Returns: `{"demerits": int, "passes": bool, "matched_patterns": [{"pattern": str, "demerits": int}]}`

## Chemical Group Patterns

### Hinge Binders

Kinase hinge-binding motifs: aminopyridines, aminopyrimidines, indazoles, benzimidazoles. Application: kinase inhibitor design.

### Phosphate Binders

Phosphate-binding groups: basic amines in specific geometries, guanidinium groups, arginine mimetics. Application: kinase/phosphatase inhibitors.

### Michael Acceptors

Electrophilic motifs: alpha,beta-unsaturated carbonyls/nitriles, vinyl sulfones, acrylamides. Can be desirable for covalent inhibitors but flagged as alerts in screening.

### Reactive Groups

General reactive functionalities: epoxides, aziridines, acyl halides, isocyanates, sulfonyl chlorides.

### Custom SMARTS Patterns

```python
custom_patterns = {
    "my_warhead": "[C;H0](=O)C(F)(F)F",       # Trifluoromethyl ketone
    "my_scaffold": "c1ccc2c(c1)ncc(n2)N",      # Aminobenzimidazole
}
group = mc.groups.ChemicalGroup(groups=["hinge_binders"], custom_smarts=custom_patterns)
```

## Filter Selection Guidelines

### By Discovery Stage

**Initial Screening (HTS):**
```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_five", "pains_filter"])
alert_filter = mc.structural.CommonAlertsFilters()
```

**Hit-to-Lead:**
```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_oprea"])
nibr_filter = mc.structural.NIBRFilters()
lilly_filter = mc.structural.LillyDemeritsFilters()
```

**Lead Optimization:**
```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_drug", "rule_of_leadlike_strict"])
complexity_filter = mc.complexity.ComplexityFilter(max_complexity=400)
```

**CNS Targets:**
```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_cns"])
constraints = mc.constraints.Constraints(tpsa_max=90, hbd_max=2, mw_range=(300, 450))
```

**Fragment-Based Drug Discovery:**
```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_three"])
complexity_filter = mc.complexity.ComplexityFilter(max_complexity=250)
```

## Important Considerations

- **False positives**: ~10% of marketed drugs fail Ro5; natural products and antibiotics frequently non-compliant
- **False negatives**: Passing filters does not guarantee success; target-specific issues are not captured
- **Context matters**: kinases vs GPCRs vs ion channels have different optimal property spaces
- **Modality**: small molecules vs PROTACs vs molecular glues require different criteria

## References

1. Lipinski CA et al. Adv Drug Deliv Rev (1997) 23:3-25
2. Veber DF et al. J Med Chem (2002) 45:2615-2623
3. Oprea TI et al. J Chem Inf Comput Sci (2001) 41:1308-1315
4. Congreve M et al. Drug Discov Today (2003) 8:876-877
5. Baell JB & Holloway GA. J Med Chem (2010) 53:2719-2740
6. Johnson TW et al. J Med Chem (2009) 52:5487-5500
7. Walters WP & Murcko MA. Adv Drug Deliv Rev (2002) 54:255-271

Condensed from original: references/rules_catalog.md (605 lines). Retained: all rule thresholds, structural alert categories, Lilly demerit tiers, chemical group patterns, custom SMARTS example, filter selection guidelines by stage, important considerations. Omitted: verbose prose explanations already covered in SKILL.md Core API; redundant code examples duplicating SKILL.md patterns.
