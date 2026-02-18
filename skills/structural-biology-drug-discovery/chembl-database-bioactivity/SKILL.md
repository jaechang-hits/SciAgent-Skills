---
name: chembl-database-bioactivity
description: Query ChEMBL bioactive molecules and drug discovery data using the Python SDK. Search compounds by structure/properties, retrieve bioactivity data (IC50, Ki, EC50), find inhibitors for targets, perform SAR studies, and access drug mechanism/indication data for medicinal chemistry research.
license: CC-BY-SA-3.0
---

# ChEMBL Database — Bioactivity Queries

## Overview

Query the ChEMBL bioactive molecule database (2M+ compounds, 19M+ bioactivity measurements, 13K+ targets) using the `chembl_webresource_client` Python SDK. Covers compound search, target lookup, bioactivity retrieval, structure-based search, and drug information access.

## When to Use

- Finding compounds by name, ChEMBL ID, or physicochemical properties
- Querying bioactivity data (IC50, Ki, EC50) for specific targets
- Performing similarity or substructure searches using SMILES
- Retrieving drug mechanisms of action and clinical indications
- Identifying inhibitors, agonists, or bioactive molecules for a target
- Analyzing structure-activity relationships (SAR) across compound series
- Filtering molecules by Lipinski rule-of-5 or other drug-likeness criteria
- For general cheminformatics (SMILES manipulation, fingerprints, descriptors) use rdkit-cheminformatics instead

## Prerequisites

```bash
uv pip install chembl_webresource_client
# Optional: pandas for tabular analysis
uv pip install pandas
```

**Rate limiting**: The SDK handles rate limiting internally via automatic retries and caching. No `time.sleep()` needed between queries. For large-scale data retrieval (100K+ records), consider ChEMBL bulk downloads instead of API queries.

## Quick Start

```python
from chembl_webresource_client.new_client import new_client

# Each entity type has its own client endpoint
molecule = new_client.molecule
target = new_client.target
activity = new_client.activity

# Retrieve a molecule by ChEMBL ID
aspirin = molecule.get('CHEMBL25')
print(f"{aspirin['pref_name']}: MW={aspirin['molecule_properties']['mw_freebase']}")

# Search targets by name
egfr_targets = target.filter(pref_name__icontains='EGFR', target_type='SINGLE PROTEIN')
print(f"Found {len(list(egfr_targets))} EGFR-related targets")

# Query bioactivities with filters
potent = activity.filter(
    target_chembl_id='CHEMBL203',  # EGFR
    standard_type='IC50',
    standard_value__lte=100,       # <= 100 nM
    standard_units='nM'
)
```

## Key Concepts

### Filter Operators

ChEMBL uses Django-style query filters on all endpoints:

| Operator | Meaning | Example |
|----------|---------|---------|
| `__exact` | Exact match (default) | `target_type__exact='SINGLE PROTEIN'` |
| `__iexact` | Case-insensitive exact | `pref_name__iexact='aspirin'` |
| `__contains` | Substring match | `pref_name__contains='kinase'` |
| `__icontains` | Case-insensitive substring | `pref_name__icontains='egfr'` |
| `__startswith` | Prefix match | `pref_name__startswith='Epi'` |
| `__endswith` | Suffix match | `pref_name__endswith='nib'` |
| `__gt` / `__gte` | Greater than (or equal) | `standard_value__gte=10` |
| `__lt` / `__lte` | Less than (or equal) | `standard_value__lte=100` |
| `__range` | Value in range | `mw_freebase__range=[300, 500]` |
| `__in` | Value in list | `target_chembl_id__in=['CHEMBL203', 'CHEMBL240']` |
| `__isnull` | Null check | `pchembl_value__isnull=False` |
| `__regex` | Regular expression | `pref_name__regex='^EGF.*kinase$'` |
| `__search` | Full-text search | `description__search='apoptosis'` |

### Core Endpoints

| Endpoint | Access | Description |
|----------|--------|-------------|
| `molecule` | `new_client.molecule` | Compound structures, properties, synonyms |
| `target` | `new_client.target` | Protein and non-protein biological targets |
| `activity` | `new_client.activity` | Bioassay measurement results |
| `assay` | `new_client.assay` | Experimental assay details |
| `drug` | `new_client.drug` | Approved pharmaceutical information |
| `mechanism` | `new_client.mechanism` | Drug mechanism of action data |
| `drug_indication` | `new_client.drug_indication` | Drug therapeutic indications |
| `similarity` | `new_client.similarity` | Tanimoto similarity search |
| `substructure` | `new_client.substructure` | Substructure search |
| `image` | `new_client.image` | SVG molecular structure images |
| `molecule_form` | `new_client.molecule_form` | Parent/salt forms |
| `protein_class` | `new_client.protein_class` | Protein classification hierarchy |
| `target_component` | `new_client.target_component` | Target component details |
| `cell_line` | `new_client.cell_line` | Cell line information |
| `tissue` | `new_client.tissue` | Tissue type information |
| `compound_structural_alert` | `new_client.compound_structural_alert` | Structural alerts for toxicity |
| `document` | `new_client.document` | Literature source references |

### Molecular Properties

Properties accessible via `molecule['molecule_properties']`:

| Field | Description |
|-------|-------------|
| `mw_freebase` | Molecular weight (free base) |
| `full_mwt` | Full molecular weight (including salts) |
| `alogp` | Calculated LogP |
| `hba` | Hydrogen bond acceptors |
| `hbd` | Hydrogen bond donors |
| `psa` | Polar surface area |
| `rtb` | Rotatable bonds |
| `num_ro5_violations` | Lipinski rule-of-5 violations |
| `ro3_pass` | Rule of 3 compliance |
| `cx_most_apka` | Most acidic pKa |
| `cx_most_bpka` | Most basic pKa |

### Target Information Fields

Key fields in target records:

| Field | Description |
|-------|-------------|
| `target_chembl_id` | ChEMBL target identifier |
| `pref_name` | Preferred target name |
| `target_type` | Type: SINGLE PROTEIN, PROTEIN COMPLEX, ORGANISM |
| `organism` | Target organism (e.g., Homo sapiens) |
| `tax_id` | NCBI taxonomy ID |
| `target_components` | Component details (UniProt accession, etc.) |

### Bioactivity Data Fields

Key fields in activity records:

| Field | Description |
|-------|-------------|
| `standard_type` | Activity type: IC50, Ki, Kd, EC50, etc. |
| `standard_value` | Numerical activity value |
| `standard_units` | Units: nM, uM, etc. |
| `pchembl_value` | Normalized activity (-log10 scale, comparable across types) |
| `activity_comment` | Activity annotations |
| `data_validity_comment` | Data quality flags (check before analysis) |
| `potential_duplicate` | Duplicate flag |

## Core API

### 1. Molecule Queries

```python
molecule = new_client.molecule

# By ChEMBL ID
aspirin = molecule.get('CHEMBL25')

# By name (case-insensitive)
results = molecule.filter(pref_name__icontains='imatinib')

# By properties (Lipinski rule-of-5 compliant)
drug_like = molecule.filter(
    molecule_properties__mw_freebase__lte=500,
    molecule_properties__alogp__lte=5,
    molecule_properties__hba__lte=10,
    molecule_properties__hbd__lte=5
)

# By property range
mid_weight = molecule.filter(
    molecule_properties__mw_freebase__range=[300, 500]
)
```

### 2. Target Queries

```python
target = new_client.target

# By ChEMBL ID
egfr = target.get('CHEMBL203')
print(f"{egfr['pref_name']} ({egfr['organism']})")

# Search by name and type
kinases = target.filter(
    target_type='SINGLE PROTEIN',
    pref_name__icontains='kinase'
)

# By organism
human_targets = target.filter(organism='Homo sapiens')
```

### 3. Bioactivity Data

```python
activity = new_client.activity

# Potent inhibitors for a target
potent = activity.filter(
    target_chembl_id='CHEMBL203',
    standard_type='IC50',
    standard_value__lte=100,
    standard_units='nM'
)

# All activities for a compound (with pChEMBL values)
compound_acts = activity.filter(
    molecule_chembl_id='CHEMBL25',
    pchembl_value__isnull=False
)

# Multiple activity types
ki_data = activity.filter(
    target_chembl_id='CHEMBL240',
    standard_type__in=['IC50', 'Ki', 'Kd']
)
```

### 4. Structure-Based Search

```python
# Similarity search (Tanimoto)
similarity = new_client.similarity
similar = similarity.filter(
    smiles='CC(=O)Oc1ccccc1C(=O)O',  # aspirin
    similarity=85  # >=85% similarity
)

# Substructure search
substructure = new_client.substructure
benzimidazoles = substructure.filter(smiles='c1ccc2[nH]cnc2c1')
```

### 5. Drug and Mechanism Data

```python
drug = new_client.drug
mechanism = new_client.mechanism
drug_indication = new_client.drug_indication

# Drug details
drug_info = drug.get('CHEMBL25')

# Mechanisms of action
mechs = mechanism.filter(molecule_chembl_id='CHEMBL941')
for m in mechs:
    print(f"{m['mechanism_of_action']} → {m.get('target_chembl_id')}")

# Therapeutic indications
indications = drug_indication.filter(molecule_chembl_id='CHEMBL941')
for ind in indications:
    print(f"{ind.get('mesh_heading')} (Phase {ind.get('max_phase_for_ind')})")

# SVG molecular image
image = new_client.image
svg_data = image.get('CHEMBL25')
with open('aspirin.svg', 'w') as f:
    f.write(svg_data)
```

## Common Workflows

### Workflow 1: Find Inhibitors for a Target

```python
from chembl_webresource_client.new_client import new_client
import pandas as pd

# Step 1: Identify the target
targets = new_client.target.filter(pref_name__icontains='BRAF', target_type='SINGLE PROTEIN')
target_id = list(targets)[0]['target_chembl_id']

# Step 2: Query potent activities
activities = new_client.activity.filter(
    target_chembl_id=target_id,
    standard_type='IC50',
    standard_value__lte=100,
    standard_units='nM',
    pchembl_value__isnull=False
)

# Step 3: Convert to DataFrame for analysis
df = pd.DataFrame(list(activities))
df['standard_value'] = pd.to_numeric(df['standard_value'])
print(f"Found {len(df)} potent compounds")
print(df[['molecule_chembl_id', 'standard_value', 'pchembl_value']].head(10))
```

### Workflow 2: Analyze a Known Drug

```python
from chembl_webresource_client.new_client import new_client

chembl_id = 'CHEMBL941'  # Imatinib

# Drug information
drug_info = new_client.molecule.get(chembl_id)
print(f"Name: {drug_info['pref_name']}")
print(f"MW: {drug_info['molecule_properties']['mw_freebase']}")

# Mechanisms of action
mechs = list(new_client.mechanism.filter(molecule_chembl_id=chembl_id))
for m in mechs:
    print(f"Mechanism: {m['mechanism_of_action']}")

# Indications
indications = list(new_client.drug_indication.filter(molecule_chembl_id=chembl_id))
for ind in indications:
    print(f"Indication: {ind.get('mesh_heading')} (Phase {ind.get('max_phase_for_ind')})")

# All bioactivity data
activities = list(new_client.activity.filter(
    molecule_chembl_id=chembl_id, pchembl_value__isnull=False
))
print(f"Total bioactivity records: {len(activities)}")
```

### Workflow 3: SAR Study

```python
from chembl_webresource_client.new_client import new_client
import pandas as pd

# Step 1: Find similar compounds to lead
similar = new_client.similarity.filter(
    smiles='c1ccc2c(c1)cc(nc2N)c3ccc(cc3)NC(=O)c4ccccc4',  # lead compound
    similarity=80
)
analogs = list(similar)

# Step 2: Collect activities for each analog
records = []
for compound in analogs[:20]:  # limit for demo
    cid = compound['molecule_chembl_id']
    acts = list(new_client.activity.filter(
        molecule_chembl_id=cid,
        standard_type='IC50',
        pchembl_value__isnull=False
    ))
    for act in acts:
        records.append({
            'chembl_id': cid,
            'target': act.get('target_pref_name'),
            'IC50_nM': act.get('standard_value'),
            'pchembl': act.get('pchembl_value'),
            'mw': compound.get('molecule_properties', {}).get('mw_freebase'),
            'alogp': compound.get('molecule_properties', {}).get('alogp')
        })

# Step 3: Analyze property-activity relationships
df = pd.DataFrame(records)
if not df.empty:
    df['IC50_nM'] = pd.to_numeric(df['IC50_nM'])
    print(df.groupby('target')['IC50_nM'].describe())
```

## Common Recipes

### Recipe: Virtual Screening Filter (Lipinski + Activity)

```python
from chembl_webresource_client.new_client import new_client

candidates = new_client.molecule.filter(
    molecule_properties__mw_freebase__range=[300, 500],
    molecule_properties__alogp__lte=5,
    molecule_properties__hba__lte=10,
    molecule_properties__hbd__lte=5,
    molecule_properties__num_ro5_violations=0
)
print(f"Drug-like candidates: {len(list(candidates))}")
```

### Recipe: Client Configuration

```python
from chembl_webresource_client.settings import Settings

Settings.Instance().CACHING = True           # enable/disable cache
Settings.Instance().CACHE_EXPIRE = 86400     # cache duration (seconds)
Settings.Instance().TIMEOUT = 30             # request timeout (seconds)
Settings.Instance().TOTAL_RETRIES = 3        # retry count on failure
```

### Recipe: Export Activities to CSV

```python
import pandas as pd
from chembl_webresource_client.new_client import new_client

activities = new_client.activity.filter(
    target_chembl_id='CHEMBL203',
    standard_type='IC50',
    pchembl_value__isnull=False
)
df = pd.DataFrame(list(activities))
df.to_csv('egfr_activities.csv', index=False)
print(f"Exported {len(df)} records")
```

## Key Parameters

| Parameter | Endpoint | Default | Description |
|-----------|----------|---------|-------------|
| `similarity` | `similarity.filter()` | — | Tanimoto threshold (0-100), typically 70-90 |
| `standard_type` | `activity.filter()` | — | Activity type: IC50, Ki, Kd, EC50 |
| `standard_value__lte` | `activity.filter()` | — | Max activity value (nM) |
| `pchembl_value` | `activity.filter()` | — | Normalized -log10 activity (>6 = potent) |
| `target_type` | `target.filter()` | — | SINGLE PROTEIN, PROTEIN COMPLEX, ORGANISM |
| `CACHING` | `Settings` | `True` | Enable HTTP response caching |
| `CACHE_EXPIRE` | `Settings` | `86400` | Cache TTL in seconds |
| `TIMEOUT` | `Settings` | `30` | HTTP request timeout in seconds |
| `TOTAL_RETRIES` | `Settings` | `3` | Auto-retry count on failure |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty results from filter | No matches or too strict filters | Relax filters; verify IDs exist with `.get()` first |
| `KeyError` on molecule properties | Not all molecules have full property data | Use `.get('molecule_properties', {}).get('field')` |
| Query returns unexpectedly few results | Lazy evaluation not consumed | Convert to `list()` before checking length |
| Slow queries | Large result sets paginated automatically | Add more filters to narrow results; use `__range` |
| `404` on `.get()` | Invalid ChEMBL ID | Verify ID format (e.g., CHEMBL25, not 25) |
| Stale data | Aggressive caching | Set `Settings.Instance().CACHING = False` or clear cache |
| Timeout errors | Server overload or large query | Increase `TIMEOUT`; split into smaller queries |
| Mixed units in activity data | Different assays use different units | Filter by `standard_units='nM'` or use `pchembl_value` |
| Duplicate activity records | Same measurement from different sources | Check `potential_duplicate` and `data_validity_comment` |

## Best Practices

- **Use `pchembl_value`** for cross-study comparisons — it normalizes IC50/Ki/EC50 to a comparable -log10 scale
- **Always check `data_validity_comment`** before using activity values — flags data quality issues
- **Filter by `standard_units`** to ensure consistent units across results
- **Pagination is automatic**: the SDK handles pagination transparently — iterate directly over query results without manual page handling. Convert to `list()` only when you need all results in memory
- **Use lazy evaluation**: queries execute only when iterated — convert to `list()` only when needed
- **Cache results**: the SDK caches for 24h by default — leverage this for repeated queries
- **For bulk data** (>100K records): use ChEMBL FTP downloads rather than API queries

## Related Skills

- `rdkit-cheminformatics` — SMILES manipulation, molecular descriptors, fingerprints
- `datamol-cheminformatics` — Molecular preprocessing and featurization
- `pubchem-compound-search` — Alternative compound database (NIH)

## References

- ChEMBL website: https://www.ebi.ac.uk/chembl/
- API documentation: https://www.ebi.ac.uk/chembl/api/data/docs
- Python client: https://github.com/chembl/chembl_webresource_client
- Interface docs: https://chembl.gitbook.io/chembl-interface-documentation/
- Example notebooks: https://github.com/chembl/notebooks

## Bundled Resources

**Self-contained entry** (no `references/` directory). Original total: 662 lines (SKILL.md 389 + api_reference.md 273). Scripts: 279 lines (example_queries.py).

**Original file disposition**:
- `SKILL.md` (389 lines) → Core API, Workflows, Quick Start. Promotional section stripped (rule 4). "Common Use Cases" consolidated (rule 7b): Find Kinase Inhibitors → Workflow 1 pattern, Virtual Screening → Recipe, Drug Repurposing → omitted (trivial loop over drug endpoint, not a distinct analytical workflow). "Important Notes" section routed to Best Practices and Troubleshooting (rule 9)
- `references/api_reference.md` (273 lines) → Consolidated inline. Filter Operators → Key Concepts table. Core Endpoints listing → Key Concepts table (all endpoints). Molecular Properties → Key Concepts table. Bioactivity Data Fields → Key Concepts table. Target Information Fields → Key Concepts table. Configuration/Settings → Common Recipes. Error handling/rate limiting → Troubleshooting + Best Practices. Response formats (JSON/XML/YAML) → omitted (JSON is default and only format used via Python SDK). Advanced query examples already covered in Core API
- `scripts/example_queries.py` (279 lines) → Thin-wrapper functions absorbed into Core API modules: `get_molecule_info` / `search_molecules_by_name` / `find_molecules_by_properties` → Module 1 (Molecule Queries); `get_target_info` / `search_targets_by_name` → Module 2 (Target Queries); `get_bioactivity_data` / `get_compound_bioactivities` → Module 3 (Bioactivity Data); `find_similar_compounds` / `substructure_search` → Module 4 (Structure-Based Search); `get_drug_info` → Module 5 (Drug and Mechanism Data); `find_kinase_inhibitors` → Workflow 1; `export_to_dataframe` → Workflow 1 + Recipe (Export)

**Retention**: ~460 lines / 662 original = ~69%. Vendor metadata stripped (rule 13). Agent-behavior section stripped (rule 4).
