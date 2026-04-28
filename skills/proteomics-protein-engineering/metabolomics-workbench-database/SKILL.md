---
name: "metabolomics-workbench-database"
description: "Query Metabolomics Workbench REST API (4,200+ NIH studies) for metabolite ID, study discovery, RefMet standardization, m/z precursor searches, MetStat filtering, gene/protein annotations. Use hmdb-database for local XML; pubchem-compound-search for compounds."
license: "Unknown"
---

# Metabolomics Workbench Database — REST API Access

## Overview

Query the Metabolomics Workbench (MW) REST API to access 4,200+ metabolomics studies hosted at UCSD under NIH Common Fund sponsorship. The API provides six query contexts: compound/metabolite lookups, study metadata and experimental data retrieval, RefMet standardized nomenclature, MetStat study filtering by species/disease/analysis type, m/z precursor ion searches for compound identification, and gene/protein annotation from the Metabolomics Gene/Protein (MGP) database.

## When to Use

- Searching for metabolite structures, identifiers, or chemical properties by PubChem CID, KEGG ID, InChI key, or formula
- Discovering metabolomics studies by species, disease, analysis type, or polarity
- Standardizing metabolite names to RefMet nomenclature for cross-study comparison
- Identifying unknown compounds from mass spectrometry m/z values with adduct type matching
- Retrieving experimental metabolomics data (concentrations, abundances) from published studies
- Querying gene or protein annotations linked to metabolomics pathways
- Downloading study data in mwTab format for local analysis
- For local metabolite database parsing (220K+ entries, NMR/MS spectra) use `hmdb-database` instead
- For live compound property searches (110M+ compounds) use `pubchem-compound-search` instead

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **No API key required**: MW REST API is publicly accessible without authentication
- **Rate limits**: MW does not enforce strict rate limits for reasonable use. For bulk queries (100+), add 0.5-1s delays between requests
- **Base URL**: `https://www.metabolomicsworkbench.org/rest`

```bash
pip install requests pandas
```

## Quick Start

```python
import requests
import time

BASE = "https://www.metabolomicsworkbench.org/rest"

def mw_query(context, input_item, input_value, output_item="all", fmt="json"):
    """Query Metabolomics Workbench REST API.

    URL pattern: /context/input_item/input_value/output_item/output_format
    """
    url = f"{BASE}/{context}/{input_item}/{input_value}/{output_item}/{fmt}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json() if fmt == "json" else resp.text

# Example: look up glucose by name
result = mw_query("compound", "name", "glucose")
print(result)
# {'regno': '...', 'formula': 'C6H12O6', 'exactmass': '180.063388...', ...}
```

## Core API

### Module 1: Compound Queries

Search metabolite records by various identifiers. Returns chemical properties, structure info, and cross-references.

```python
# Search by PubChem CID
compound = mw_query("compound", "pubchem_cid", "5793")
print(compound.get("name"), compound.get("formula"))
# Glucose C6H12O6

# Search by KEGG compound ID
compound = mw_query("compound", "kegg_id", "C00031")
print(compound.get("name"), compound.get("exactmass"))
# D-Glucose 180.06338810

# Search by InChI key
compound = mw_query("compound", "inchi_key", "WQZGKKKJIJFFOK-GASJEMHNSA-N")

# Search by molecular formula
matches = mw_query("compound", "formula", "C6H12O6")
# Returns all compounds with this formula

# Search by registry number (MW internal ID)
compound = mw_query("compound", "regno", "11")
# Available input_items: regno, formula, name, pubchem_cid, kegg_id, inchi_key, lm_id, hmdb_id, bmrb_id
```

### Module 2: Study Access

Retrieve study metadata, experimental factors, and data from deposited metabolomics studies.

```python
# Get study summary by study ID
study = mw_query("study", "study_id", "ST000001", "summary")
print(study.get("study_title"), study.get("institute"))

# Get study metadata (species, analysis type, etc.)
study_meta = mw_query("study", "study_id", "ST000001")
print(study_meta.get("species"), study_meta.get("analysis_type"))

# Get study factors (experimental conditions)
factors = mw_query("study", "study_id", "ST000001", "factors")
# Returns factor names and levels for the study

# Get study data (metabolite measurements)
data = mw_query("study", "study_id", "ST000001", "data")
# Returns concentration/abundance values per sample

# Get analysis details
analysis = mw_query("study", "study_id", "ST000001", "analysis")
print(analysis.get("analysis_type"), analysis.get("instrument_name"))

# Download mwTab file (tab-delimited study format)
mwtab_text = mw_query("study", "study_id", "ST000001", "mwtab", fmt="txt")
# Returns full mwTab formatted text
```

### Module 3: RefMet Nomenclature

Standardize metabolite names using RefMet (Reference Metabolomics) classification. RefMet provides a hierarchical nomenclature: super_class > main_class > sub_class.

```python
# Standardize a metabolite name to RefMet
refmet = mw_query("refmet", "name", "Palmitic acid")
print(refmet.get("refmet_name"), refmet.get("super_class"))
# Palmitic acid Fatty Acyls

# Get all metabolites in a main_class
fatty_acids = mw_query("refmet", "main_class", "Fatty acids")
print(f"Found {len(fatty_acids) if isinstance(fatty_acids, list) else 1} entries")

# Get all metabolites in a sub_class
lg_fa = mw_query("refmet", "sub_class", "Long-chain fatty acids")

# Search by exact mass (with tolerance)
# Use match="name" for name matching
refmet_match = mw_query("refmet", "match", "Palmitic acid")
print(refmet_match.get("formula"), refmet_match.get("exactmass"))
# C16H32O2 256.24023
```

### Module 4: MetStat Filtering

Filter studies using semicolon-delimited filter strings. MetStat queries enable discovery of studies by analysis type, polarity, species, and disease.

```python
# MetStat filter format: "analysis_type:value;polarity:value;species:value;disease:value"
# Each field is optional; separate multiple filters with semicolons

# Find all LC-MS studies in human
results = mw_query("metstat", "filter", "analysis_type:LC-MS;species:Human")
print(f"Found {len(results) if isinstance(results, list) else 1} studies")

# Filter by disease
diabetes_studies = mw_query("metstat", "filter", "disease:Diabetes;species:Human")

# Filter by polarity
pos_studies = mw_query("metstat", "filter", "analysis_type:LC-MS;polarity:positive")

# Combined multi-field filter
filtered = mw_query("metstat", "filter",
    "analysis_type:LC-MS;polarity:positive;species:Human;disease:Cancer")

# Available filter fields and common values:
# analysis_type: LC-MS, GC-MS, CE-MS, NMR
# polarity: positive, negative
# species: Human, Mouse, Rat, etc.
# disease: Cancer, Diabetes, Obesity, etc.
```

### Module 5: m/z Search (Moverz)

Search for metabolites by precursor ion m/z value. Essential for compound identification from mass spectrometry data.

```python
# Search by m/z with adduct type and tolerance
# Format: moverz/mz_value/tolerance/ion_type/...
mz_results = mw_query("moverz", "mz", "180.063/0.005/M+H")
# Returns candidate compounds matching the m/z within tolerance

# Negative mode search
mz_neg = mw_query("moverz", "mz", "179.056/0.005/M-H")

# Sodium adduct search
mz_na = mw_query("moverz", "mz", "203.053/0.01/M+Na")

# Search with wider tolerance for low-resolution instruments
mz_wide = mw_query("moverz", "mz", "180.063/0.5/M+H")
print("Candidates:", mz_results)
# Returns: compound name, formula, exact mass, delta (mass error)
```

### Module 6: Gene Information

Query gene annotations from the Metabolomics Gene/Protein (MGP) database.

```python
# Search by gene symbol
gene = mw_query("gene", "gene_symbol", "HMGCR")
print(gene.get("gene_name"), gene.get("taxonomy"))
# 3-hydroxy-3-methylglutaryl-CoA reductase Homo sapiens

# Search by gene ID
gene_by_id = mw_query("gene", "gene_id", "3156")
print(gene_by_id.get("gene_symbol"))

# Search by taxonomy
human_genes = mw_query("gene", "taxonomy", "Homo sapiens")
```

### Module 7: Protein Data

Retrieve protein sequence and annotation data from the MGP database.

```python
# Search by UniProt ID
protein = mw_query("protein", "uniprot_id", "P04035")
print(protein.get("protein_name"), protein.get("gene_symbol"))

# Search by gene symbol for protein info
protein_by_gene = mw_query("protein", "gene_symbol", "HMGCR")
print(protein_by_gene.get("sequence")[:50] if protein_by_gene.get("sequence") else "No seq")

# Search by MGP ID
protein_mgp = mw_query("protein", "mgp_id", "MGP000001")
```

## Key Concepts

### API URL Structure

All MW REST API endpoints follow the same pattern:

```
https://www.metabolomicsworkbench.org/rest/{context}/{input_item}/{input_value}/{output_item}/{format}
```

| Component | Description | Example Values |
|-----------|-------------|----------------|
| `context` | Query domain | `compound`, `study`, `refmet`, `metstat`, `moverz`, `gene`, `protein` |
| `input_item` | Search field | `name`, `pubchem_cid`, `study_id`, `mz`, `gene_symbol` |
| `input_value` | Search term | `glucose`, `5793`, `ST000001` |
| `output_item` | Data to return | `all`, `summary`, `factors`, `data`, `analysis`, `mwtab` |
| `format` | Response format | `json`, `txt` |

### RefMet Classification Hierarchy

RefMet standardizes metabolite naming with three classification levels:

| Super Class | Main Class (examples) | Sub Class (examples) |
|-------------|----------------------|---------------------|
| Fatty Acyls | Fatty acids, Eicosanoids | Short/Medium/Long/Very long-chain FA |
| Glycerolipids | Monoradylglycerols, Diradylglycerols | Monoacylglycerols, Diacylglycerols |
| Glycerophospholipids | Glycerophosphocholines, -ethanolamines | Lysophosphatidylcholines |
| Sphingolipids | Sphingoid bases, Ceramides | Ceramide phosphocholines |
| Steroids | Cholesterol esters, Bile acids | C18/C19/C21 steroids |
| Prenol Lipids | Isoprenoids, Quinones | Ubiquinones, Terpenes |
| Organic acids | Amino acids, Carboxylic acids | Alpha amino acids |
| Nucleosides | Purine nucleosides, Pyrimidine | Adenosine, Cytidine |
| Carbohydrates | Monosaccharides, Disaccharides | Hexoses, Pentoses |

### Ion Adduct Types (Moverz)

Common adduct types for m/z searches (mass spectrometry):

| Adduct | Mode | Mass Shift | Use When |
|--------|------|-----------|----------|
| M+H | Positive | +1.0073 | Default positive mode |
| M+Na | Positive | +22.9892 | Sodium adducts (common in ESI) |
| M+K | Positive | +38.9632 | Potassium adducts |
| M+NH4 | Positive | +18.0338 | Ammonium adducts (lipids) |
| M-H | Negative | -1.0073 | Default negative mode |
| M-H-H2O | Negative | -19.0178 | Dehydrated anions |
| M+Cl | Negative | +34.9689 | Chloride adducts |
| M+FA-H | Negative | +44.9982 | Formate adducts (LC-MS) |
| M+2H | Positive | +1.0073 (z=2) | Doubly charged ions |
| M-2H | Negative | -1.0073 (z=2) | Doubly charged negative |

### MetStat Filter Syntax

MetStat uses semicolon-delimited key:value pairs. All fields are optional:

```
analysis_type:{value};polarity:{value};species:{value};disease:{value}
```

- Omit any field to leave it unfiltered
- Values are case-sensitive (use exact values: `Human` not `human`)
- Combine as many fields as needed

## Common Workflows

### Workflow 1: Metabolite Identification Pipeline

Standardize a metabolite name, find related studies, and retrieve experimental data.

```python
import pandas as pd

# Step 1: Standardize name via RefMet
refmet = mw_query("refmet", "name", "Palmitic acid")
std_name = refmet.get("refmet_name", "Palmitic acid")
formula = refmet.get("formula")
print(f"Standardized: {std_name}, Formula: {formula}")

# Step 2: Search compound database for cross-references
compound = mw_query("compound", "name", std_name)
print(f"PubChem CID: {compound.get('pubchem_cid')}, "
      f"KEGG: {compound.get('kegg_id')}, HMDB: {compound.get('hmdb_id')}")

# Step 3: Find studies containing this metabolite via MetStat
studies = mw_query("metstat", "filter", "species:Human")
# Filter client-side for studies with the metabolite of interest
if isinstance(studies, list):
    print(f"Found {len(studies)} human metabolomics studies")

# Step 4: Get data from a specific study
study_data = mw_query("study", "study_id", "ST000001", "data")
if isinstance(study_data, list):
    df = pd.DataFrame(study_data)
    print(f"Data shape: {df.shape}")
    print(df.head())
```

### Workflow 2: MS Compound Identification

Identify unknown compounds from mass spectrometry m/z values.

```python
# Step 1: Search positive mode m/z
target_mz = "256.240"
tolerance = "0.01"
candidates_pos = mw_query("moverz", "mz", f"{target_mz}/{tolerance}/M+H")

# Step 2: Also check sodium adduct
candidates_na = mw_query("moverz", "mz", f"{target_mz}/{tolerance}/M+Na")
time.sleep(0.5)

# Step 3: For each candidate, get full compound info
if isinstance(candidates_pos, list):
    for candidate in candidates_pos[:5]:  # Top 5 candidates
        name = candidate.get("name", "Unknown")
        delta = candidate.get("delta", "N/A")
        print(f"Candidate: {name}, Mass error: {delta}")

        # Get detailed compound info
        detail = mw_query("compound", "name", name)
        print(f"  Formula: {detail.get('formula')}, "
              f"KEGG: {detail.get('kegg_id')}")
        time.sleep(0.5)

# Step 4: Standardize top candidate via RefMet
if candidates_pos:
    top_name = candidates_pos[0].get("name", "")
    refmet = mw_query("refmet", "name", top_name)
    print(f"RefMet class: {refmet.get('super_class')} > "
          f"{refmet.get('main_class')} > {refmet.get('sub_class')}")
```

### Workflow 3: Disease Metabolomics Exploration

Discover metabolomics studies for a disease and extract experimental data.

```python
import pandas as pd

# Step 1: Filter studies by disease and analysis type
diabetes_lc = mw_query("metstat", "filter",
    "disease:Diabetes;analysis_type:LC-MS;species:Human")
print(f"Found {len(diabetes_lc) if isinstance(diabetes_lc, list) else 1} studies")

# Step 2: Get study details for top results
if isinstance(diabetes_lc, list):
    for study_entry in diabetes_lc[:3]:
        sid = study_entry.get("study_id", "")
        if sid:
            summary = mw_query("study", "study_id", sid, "summary")
            print(f"\n{sid}: {summary.get('study_title', 'N/A')}")
            print(f"  Institute: {summary.get('institute', 'N/A')}")
            time.sleep(0.5)

# Step 3: Get experimental factors and data from one study
target_study = "ST000001"
factors = mw_query("study", "study_id", target_study, "factors")
print(f"\nFactors for {target_study}:", factors)

data = mw_query("study", "study_id", target_study, "data")
if isinstance(data, list):
    df = pd.DataFrame(data)
    print(f"Dataset: {df.shape[0]} rows x {df.shape[1]} columns")
    print(df.describe())
```

## Key Parameters

| Function/Endpoint | Parameter | Description | Example Values |
|-------------------|-----------|-------------|----------------|
| `compound` | `input_item` | Search field | `name`, `pubchem_cid`, `kegg_id`, `formula`, `inchi_key`, `hmdb_id`, `lm_id`, `bmrb_id`, `regno` |
| `study` | `output_item` | Data to retrieve | `summary`, `factors`, `data`, `analysis`, `mwtab`, `all` |
| `refmet` | `input_item` | Classification level | `name`, `main_class`, `sub_class`, `super_class`, `match` |
| `metstat` | filter string | Semicolon-delimited | `analysis_type:LC-MS;species:Human;disease:Cancer` |
| `moverz` | `mz` value | m/z / tolerance / adduct | `180.063/0.005/M+H` |
| `gene` | `input_item` | Gene search field | `gene_symbol`, `gene_id`, `taxonomy` |
| `protein` | `input_item` | Protein search field | `uniprot_id`, `gene_symbol`, `mgp_id` |
| All | `fmt` | Response format | `json` (default), `txt` |

## Best Practices

1. **Use RefMet for standardization**: Always standardize metabolite names through RefMet before cross-study comparisons. Different studies may use synonyms for the same compound
2. **Add delays for bulk queries**: Insert `time.sleep(0.5)` between requests when querying >100 endpoints to avoid overloading the server
3. **Check response types**: The API may return a dict (single result) or list (multiple results). Always handle both: `results if isinstance(results, list) else [results]`
4. **Use specific output_items**: Request `summary`, `factors`, or `data` individually rather than `all` to reduce response size and parse time
5. **Validate m/z tolerance**: Use tight tolerance (0.005 Da) for high-resolution instruments (Orbitrap, TOF) and wider tolerance (0.5 Da) for low-resolution instruments
6. **MetStat values are case-sensitive**: Use exact values (`Human` not `human`, `LC-MS` not `lc-ms`). Check available values via the MW web interface if unsure
7. **Cache compound lookups**: Compound data changes infrequently. Cache results locally to avoid redundant API calls during iterative analysis

## Common Recipes

### Recipe: Batch Metabolite Standardization via RefMet

```python
metabolite_names = ["palmitic acid", "oleic acid", "stearic acid",
                    "linoleic acid", "arachidonic acid"]
standardized = []
for name in metabolite_names:
    result = mw_query("refmet", "name", name)
    standardized.append({
        "original": name,
        "refmet_name": result.get("refmet_name", name),
        "super_class": result.get("super_class", ""),
        "main_class": result.get("main_class", ""),
        "formula": result.get("formula", "")
    })
    time.sleep(0.5)
df_std = pd.DataFrame(standardized)
print(df_std.to_string(index=False))
```

### Recipe: Cross-Database ID Mapping

```python
# Map a compound across PubChem, KEGG, HMDB
compound = mw_query("compound", "name", "L-Alanine")
id_map = {
    "MW_regno": compound.get("regno"),
    "PubChem_CID": compound.get("pubchem_cid"),
    "KEGG_ID": compound.get("kegg_id"),
    "HMDB_ID": compound.get("hmdb_id"),
    "LipidMaps_ID": compound.get("lm_id"),
    "Formula": compound.get("formula"),
    "Exact_Mass": compound.get("exactmass")
}
for db, val in id_map.items():
    print(f"  {db}: {val}")
```

### Recipe: Export Study Data to DataFrame

```python
import pandas as pd

study_id = "ST000001"
# Get study data and convert to DataFrame
raw_data = mw_query("study", "study_id", study_id, "data")
if isinstance(raw_data, list):
    df = pd.DataFrame(raw_data)
elif isinstance(raw_data, dict):
    df = pd.DataFrame([raw_data])
else:
    df = pd.DataFrame()

# Get study metadata for context
meta = mw_query("study", "study_id", study_id, "summary")
print(f"Study: {meta.get('study_title', study_id)}")
print(f"Species: {meta.get('species')}, Analysis: {meta.get('analysis_type')}")
print(f"Data shape: {df.shape}")
print(df.head())
# Export to CSV
df.to_csv(f"{study_id}_data.csv", index=False)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty JSON response `{}` | Invalid input_item or input_value | Verify the context/input_item combination is valid (see Key Parameters table). Check spelling and case |
| `ConnectionError` or timeout | MW server temporarily unavailable | Retry after 30s. MW occasionally has maintenance windows. Add `timeout=30` to requests |
| MetStat returns no results | Case-sensitive filter values | Use exact case: `Human` not `human`, `LC-MS` not `lc-ms`. Check available values on MW website |
| m/z search returns too many hits | Tolerance too wide | Reduce tolerance from 0.5 to 0.01 or 0.005 Da for high-resolution instruments |
| m/z search returns no hits | Wrong adduct type or too-tight tolerance | Try alternative adducts (M+H, M+Na, M-H). Widen tolerance. Verify the m/z value is correct |
| `JSONDecodeError` on response | Endpoint returns text, not JSON | Some endpoints (e.g., `mwtab` output) return plain text. Use `fmt="txt"` instead of `"json"` |
| Study data missing columns | Study uses different data format | Check `analysis` output first to understand the study's data structure. Not all studies have uniform column names |
| RefMet name not found | Metabolite not in RefMet database | Try alternative names or synonyms. RefMet covers ~120K standardized names but some rare metabolites may be absent |

## Bundled Resources

This entry is self-contained. The original `references/api_reference.md` (494 lines) covering all 7 API contexts (Compound, Study, RefMet, MetStat, Moverz, Gene, Protein) has been fully consolidated inline:
- **Compound endpoint**: input_items and output fields consolidated into Core API Module 1 + Key Parameters table
- **Study endpoint**: output_items (summary, factors, data, analysis, mwtab) consolidated into Core API Module 2
- **RefMet endpoint**: classification hierarchy consolidated into Core API Module 3 + Key Concepts RefMet table
- **MetStat endpoint**: filter syntax consolidated into Core API Module 4 + Key Concepts MetStat section
- **Moverz endpoint**: adduct types consolidated into Core API Module 5 + Key Concepts Ion Adduct table
- **Gene/Protein endpoints**: consolidated into Core API Modules 6 and 7
- Omitted: raw curl examples (replaced with Python helper function), HTML output format examples (rarely used programmatically)

## Related Skills

- **hmdb-database** -- local XML parsing for 220K+ metabolites with NMR/MS spectral data; use when MW does not have the metabolite or you need spectral peak lists
- **pubchem-compound-search** -- broader compound property lookups (110M+ compounds) via PubChemPy; use for general chemistry queries beyond metabolomics
- **matchms-spectral-matching** -- spectral similarity scoring for metabolite identification from MS/MS data; complementary to MW m/z searches
- **pyopenms-mass-spectrometry** -- full LC-MS/MS data processing pipeline; use for raw spectra processing before querying MW for identification
- **kegg-database** -- pathway and compound queries; use KEGG IDs from MW compound lookups for pathway context

## References

- Metabolomics Workbench REST API: https://www.metabolomicsworkbench.org/tools/MWRestAPIv1.0.pdf
- MW REST Interactive URL Creator: https://www.metabolomicsworkbench.org/databases/metabolites/mw-rest.php
- Sud et al. "Metabolomics Workbench: An international repository for metabolomics data" Nucleic Acids Research (2016) https://doi.org/10.1093/nar/gkv1042
- RefMet nomenclature: https://www.metabolomicsworkbench.org/databases/refmet/index.php
