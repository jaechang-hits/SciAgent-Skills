---
name: "hmdb-database"
description: "Parse and query the Human Metabolome Database (HMDB) local XML for metabolite information, chemical properties, biological context, disease associations, spectral data, and cross-database mapping. No public REST API — primary access via downloaded XML (~6 GB). For drug-focused queries use drugbank-database-access; for live compound lookups use pubchem-compound-search."
license: "CC-BY-4.0"
---

# HMDB Database — Local XML Access

## Overview

Query the Human Metabolome Database (HMDB, 220,000+ metabolite entries) by parsing locally downloaded XML with Python's ElementTree. Covers metabolite lookup, chemical properties, biological context (pathways, enzymes, biofluids), disease/biomarker associations, spectral data for metabolite identification, and cross-database ID mapping to KEGG, PubChem, ChEBI, and DrugBank.

## When to Use

- Looking up metabolite information (description, chemical class, cellular location) by HMDB ID or name
- Retrieving chemical properties (molecular weight, formula, SMILES, InChI, logP, PSA) for metabolomics analysis
- Finding pathway associations and enzyme links for a set of metabolites
- Identifying biofluid/tissue locations of metabolites (blood, urine, CSF, saliva)
- Querying disease associations and normal/abnormal concentration ranges for biomarker discovery
- Extracting NMR or MS spectral peak lists for metabolite identification
- Mapping HMDB IDs to KEGG, PubChem, ChEBI, DrugBank, or other databases
- For drug-specific data (interactions, targets, pharmacology) use `drugbank-database-access` instead
- For live compound property queries without downloading use `pubchem-compound-search` instead

## Prerequisites

- **HMDB XML download**: Register at https://hmdb.ca/downloads — download `hmdb_metabolites.xml.zip` (~6 GB uncompressed)
- **Python packages**: `lxml` (faster XPath) or standard `xml.etree.ElementTree`, `pandas`
- **No public REST API**: HMDB has no programmatic REST API. All access is via local XML parsing or the web interface
- **R package** (optional): `hmdbQuery` on CRAN provides some query wrappers but is limited and outdated
- **Rate limits**: N/A for local XML parsing. The web interface has no documented rate limits but is not intended for scraping

```bash
pip install lxml pandas
```

## Quick Start

```python
import xml.etree.ElementTree as ET

NS = {'hmdb': 'http://www.hmdb.ca'}

tree = ET.parse('hmdb_metabolites.xml')  # 60-120s for full XML
root = tree.getroot()

# Build lookup index (HMDB ID + lowercase name -> element)
metabolite_index = {}
for met in root.findall('hmdb:metabolite', NS):
    accession = met.find('hmdb:accession', NS)
    name = met.find('hmdb:name', NS)
    if accession is not None and accession.text:
        metabolite_index[accession.text] = met
    if name is not None and name.text:
        metabolite_index[name.text.lower()] = met

def find_metabolite(query):
    """Find metabolite by HMDB ID or name (case-insensitive)."""
    return metabolite_index.get(query) or metabolite_index.get(query.lower())

met = find_metabolite('HMDB0000122')  # Glucose
name = met.find('hmdb:name', NS).text
formula = met.find('hmdb:chemical_formula', NS).text
print(f"{name}: {formula}")
# Glucose: C6H12O6
```

## Core API

### 1. XML Setup and Metabolite Lookup

```python
import xml.etree.ElementTree as ET

NS = {'hmdb': 'http://www.hmdb.ca'}
tree = ET.parse('hmdb_metabolites.xml')
root = tree.getroot()
print(f"Total metabolite entries: {len(root.findall('hmdb:metabolite', NS))}")
# Total metabolite entries: ~220000+
```

For memory-constrained environments, use iterparse:

```python
met_names = {}
for event, elem in ET.iterparse('hmdb_metabolites.xml', events=('end',)):
    if elem.tag == '{http://www.hmdb.ca}metabolite':
        acc = elem.find('{http://www.hmdb.ca}accession')
        name = elem.find('{http://www.hmdb.ca}name')
        if acc is not None and name is not None and acc.text and name.text:
            met_names[acc.text] = name.text
        elem.clear()
print(f"Parsed {len(met_names)} metabolites via iterparse")
```

### 2. Chemical Properties

```python
def get_chemical_properties(met_element):
    """Extract chemical properties from a metabolite entry."""
    def txt(path):
        el = met_element.find(path, NS)
        return el.text if el is not None and el.text else None
    # Fields: accession, name, chemical_formula, average_molecular_weight,
    # monisotopic_molecular_weight, smiles, inchi, inchikey, state, iupac_name
    return {tag: txt(f'hmdb:{tag}') for tag in [
        'accession', 'name', 'chemical_formula', 'average_molecular_weight',
        'monisotopic_molecular_weight', 'smiles', 'inchi', 'inchikey', 'state']}

props = get_chemical_properties(find_metabolite('HMDB0000158'))  # L-Tyrosine
print(f"{props['name']}: MW={props['average_molecular_weight']}, SMILES={props['smiles']}")
```

```python
# Extract taxonomy / chemical classification (ClassyFire ontology)
def get_classification(met_element):
    tax = met_element.find('hmdb:taxonomy', NS)
    if tax is None:
        return {}
    def txt(tag):
        el = tax.find(f'hmdb:{tag}', NS)
        return el.text if el is not None and el.text else None
    return {'kingdom': txt('kingdom'), 'super_class': txt('super_class'),
            'class': txt('class'), 'sub_class': txt('sub_class'),
            'direct_parent': txt('direct_parent')}

print(get_classification(find_metabolite('HMDB0000122')))
# {'kingdom': 'Organic compounds', 'super_class': 'Organooxygen compounds', ...}
```

### 3. Biological Context

```python
def get_pathways(met_element):
    """Extract metabolic pathway associations."""
    pathways = []
    for pw in met_element.findall('hmdb:pathways/hmdb:pathway', NS):
        name = pw.find('hmdb:name', NS)
        smpdb_id = pw.find('hmdb:smpdb_id', NS)
        kegg_id = pw.find('hmdb:kegg_map_id', NS)
        pathways.append({
            'name': name.text if name is not None else None,
            'smpdb_id': smpdb_id.text if smpdb_id is not None else None,
            'kegg_map_id': kegg_id.text if kegg_id is not None else None,
        })
    return pathways

for pw in get_pathways(find_metabolite('HMDB0000122'))[:5]:
    print(f"  {pw['smpdb_id']}: {pw['name']}")
```

```python
def get_biolocations(met_element):
    """Extract biofluid, tissue, and cellular locations."""
    bp = 'hmdb:biological_properties/hmdb:'
    def texts(path):
        return [el.text for el in met_element.findall(path, NS) if el.text]
    return {'biofluids': texts(f'{bp}biospecimen_locations/hmdb:biospecimen'),
            'tissues': texts(f'{bp}tissue_locations/hmdb:tissue'),
            'cellular': texts(f'{bp}cellular_locations/hmdb:cellular')}

locs = get_biolocations(find_metabolite('HMDB0000122'))
print(f"Glucose biofluids: {locs['biofluids']}")
```

```python
def get_enzymes(met_element):
    """Extract associated enzymes/proteins with UniProt IDs."""
    return [{'name': (p.find('hmdb:name', NS).text
                      if p.find('hmdb:name', NS) is not None else None),
             'uniprot_id': (p.find('hmdb:uniprot_id', NS).text
                            if p.find('hmdb:uniprot_id', NS) is not None else None),
             'gene_name': (p.find('hmdb:gene_name', NS).text
                           if p.find('hmdb:gene_name', NS) is not None else None)}
            for p in met_element.findall('hmdb:protein_associations/hmdb:protein', NS)]

enz = get_enzymes(find_metabolite('HMDB0000122'))
print(f"Glucose-associated proteins: {len(enz)}")
for e in enz[:3]:
    print(f"  {e['gene_name']} ({e['uniprot_id']}): {e['name']}")
```

### 4. Disease and Biomarker Queries

```python
def get_diseases(met_element):
    """Extract disease associations with OMIM IDs and PubMed references."""
    diseases = []
    for d in met_element.findall('hmdb:diseases/hmdb:disease', NS):
        name = d.find('hmdb:name', NS)
        omim = d.find('hmdb:omim_id', NS)
        pmids = [r.find('hmdb:pubmed_id', NS).text
                 for r in d.findall('hmdb:references/hmdb:reference', NS)
                 if r.find('hmdb:pubmed_id', NS) is not None and r.find('hmdb:pubmed_id', NS).text]
        diseases.append({'name': name.text if name is not None else None,
                         'omim_id': omim.text if omim is not None else None,
                         'pubmed_ids': pmids})
    return diseases

diseases = get_diseases(find_metabolite('HMDB0000122'))
print(f"Glucose disease associations: {len(diseases)}")
for d in diseases[:3]:
    print(f"  {d['name']} (OMIM: {d['omim_id']})")
```

```python
def get_concentrations(met_element, biospecimen='Blood'):
    """Extract normal/abnormal concentration data filtered by biospecimen."""
    result = {'normal': [], 'abnormal': []}
    for ctype, key in [('normal_concentrations', 'normal'),
                       ('abnormal_concentrations', 'abnormal')]:
        for c in met_element.findall(f'hmdb:{ctype}/hmdb:concentration', NS):
            bio = c.find('hmdb:biospecimen', NS)
            if bio is None or bio.text != biospecimen:
                continue
            def txt(tag):
                el = c.find(f'hmdb:{tag}', NS)
                return el.text if el is not None else None
            result[key].append({'value': txt('concentration_value'),
                                'units': txt('concentration_units'),
                                'condition': txt('subject_condition')})
    return result

conc = get_concentrations(find_metabolite('HMDB0000122'), 'Blood')
print(f"Glucose blood: {len(conc['normal'])} normal, {len(conc['abnormal'])} abnormal")
```

### 5. Spectral Data

```python
def get_ms_spectra(met_element):
    """Extract MS/MS spectral peak lists (m/z + intensity)."""
    spectra = []
    for spec in met_element.findall('hmdb:spectra/hmdb:spectrum', NS):
        stype = spec.find('hmdb:type', NS)
        if stype is None or 'MS' not in (stype.text or ''):
            continue
        peaks = [{'mz': float(p.find('hmdb:mass_charge', NS).text),
                  'intensity': float(p.find('hmdb:intensity', NS).text or 0)}
                 for p in spec.findall('hmdb:ms_ms_peaks/hmdb:ms_ms_peak', NS)
                 if p.find('hmdb:mass_charge', NS) is not None
                 and p.find('hmdb:mass_charge', NS).text]
        spectra.append({'type': stype.text, 'num_peaks': len(peaks), 'peaks': peaks})
    return spectra

spectra = get_ms_spectra(find_metabolite('HMDB0000122'))
print(f"Glucose MS spectra: {len(spectra)}")
```

```python
def get_nmr_spectra(met_element):
    """Extract NMR spectral peak lists (1H, 13C). Same pattern as MS above."""
    spectra = []
    for spec in met_element.findall('hmdb:spectra/hmdb:spectrum', NS):
        stype = spec.find('hmdb:type', NS)
        if stype is None or 'NMR' not in (stype.text or ''):
            continue
        nucleus = spec.find('hmdb:nucleus', NS)
        shifts = [float(p.find('hmdb:chemical_shift', NS).text)
                  for p in spec.findall('hmdb:nmr_one_d_peaks/hmdb:nmr_one_d_peak', NS)
                  if p.find('hmdb:chemical_shift', NS) is not None
                  and p.find('hmdb:chemical_shift', NS).text]
        spectra.append({'type': stype.text,
                        'nucleus': nucleus.text if nucleus is not None else None,
                        'num_peaks': len(shifts), 'chemical_shifts': shifts})
    return spectra

nmr = get_nmr_spectra(find_metabolite('HMDB0000122'))
print(f"Glucose NMR spectra: {len(nmr)}")
```

### 6. Cross-Database Mapping

```python
def get_external_ids(met_element):
    """Extract cross-database identifiers (KEGG, PubChem, ChEBI, DrugBank, CAS, etc.)."""
    fields = {'kegg_id': 'KEGG', 'pubchem_compound_id': 'PubChem', 'chebi_id': 'ChEBI',
              'drugbank_id': 'DrugBank', 'chemspider_id': 'ChemSpider',
              'cas_registry_number': 'CAS', 'biocyc_id': 'BioCyc', 'pdb_id': 'PDB',
              'foodb_id': 'FooDB', 'metlin_id': 'METLIN'}
    ids = {}
    for tag, label in fields.items():
        el = met_element.find(f'hmdb:{tag}', NS)
        if el is not None and el.text:
            ids[label] = el.text
    return ids

ids = get_external_ids(find_metabolite('HMDB0000122'))
print(f"Glucose cross-refs: {ids}")
# {'KEGG': 'C00031', 'PubChem': '5793', 'ChEBI': '17234', ...}
```

```python
# Build cross-reference table for a metabolite list
import pandas as pd

queries = ['HMDB0000122', 'HMDB0000158', 'HMDB0000167', 'HMDB0000148']
rows = []
for q in queries:
    m = find_metabolite(q)
    if m is None: continue
    ids = get_external_ids(m)
    rows.append({'name': m.find('hmdb:name', NS).text, 'hmdb_id': q,
                 'kegg': ids.get('KEGG'), 'pubchem': ids.get('PubChem'),
                 'chebi': ids.get('ChEBI')})
print(pd.DataFrame(rows).to_string(index=False))
```

## Key Concepts

### HMDB XML Entry Structure

| Section | XPath | Content |
|---------|-------|---------|
| Identity | `hmdb:accession`, `hmdb:name`, `hmdb:iupac_name` | Primary identifiers |
| Chemical | `hmdb:chemical_formula`, `hmdb:smiles`, `hmdb:inchi` | Structure descriptors |
| Properties | `hmdb:average_molecular_weight`, `hmdb:state` | Physical properties |
| Taxonomy | `hmdb:taxonomy/hmdb:kingdom`, `class`, etc. | Chemical classification |
| Biological | `hmdb:biological_properties` | Biofluids, tissues, cellular locations |
| Pathways | `hmdb:pathways/hmdb:pathway` | SMPDB + KEGG pathway links |
| Enzymes | `hmdb:protein_associations/hmdb:protein` | Associated proteins/enzymes |
| Diseases | `hmdb:diseases/hmdb:disease` | Disease associations + OMIM IDs |
| Concentrations | `hmdb:normal_concentrations`, `hmdb:abnormal_concentrations` | Biomarker reference ranges |
| Spectra | `hmdb:spectra/hmdb:spectrum` | NMR, MS/MS peak lists |
| External IDs | `hmdb:kegg_id`, `hmdb:pubchem_compound_id`, etc. | Cross-database identifiers |
| Ontology | `hmdb:ontology` | Physiological/disposition/process roles |

### Data Field Completeness

Not all entries have all fields populated. Coverage varies by metabolite class:

| Field Category | Approximate Coverage | Notes |
|---------------|---------------------|-------|
| Accession, name, formula | ~100% | Always present |
| SMILES, InChI, MW | ~90% | Missing for some lipids and complex metabolites |
| Taxonomy/classification | ~85% | Chemical ontology from ClassyFire |
| Biofluid locations | ~60% | Best for common human metabolites |
| Pathways | ~40% | Curated SMPDB + KEGG links |
| Protein associations | ~35% | Enzyme-metabolite relationships |
| Disease associations | ~25% | Primarily for biomarker metabolites |
| Normal concentrations | ~20% | Reference ranges for clinical metabolites |
| MS/MS spectra | ~15% | Experimental spectral libraries |
| NMR spectra | ~10% | 1H and 13C chemical shift data |

### File Format Comparison

| Format | File | Size | Best For |
|--------|------|------|----------|
| Full XML | `hmdb_metabolites.xml` | ~6 GB | Complete data access (all fields) |
| SDF | `structures.sdf` | ~200 MB | Chemical structures + basic properties |
| CSV | Various exports | ~50-500 MB | Tabular data (properties, concentrations) |
| FASTA | `hmdb_proteins.fasta` | ~50 MB | Protein sequence lookups |

## Common Workflows

### Workflow 1: Metabolite Identification from Mass Spec

**Goal**: Match an observed m/z value to candidate metabolites using molecular weight. Assumes `root`, `NS` from Quick Start.

```python
import pandas as pd

observed_mz = 180.063  # [M+H]+ for glucose
adduct_mass = 1.00728  # H+ adduct
target_mw = observed_mz - adduct_mass
tolerance_da = 0.01

candidates = []
for met in root.findall('hmdb:metabolite', NS):
    mw_el = met.find('hmdb:monisotopic_molecular_weight', NS)
    if mw_el is None or not mw_el.text:
        continue
    mw = float(mw_el.text)
    if abs(mw - target_mw) <= tolerance_da:
        candidates.append({
            'hmdb_id': met.find('hmdb:accession', NS).text,
            'name': met.find('hmdb:name', NS).text,
            'mw': mw, 'delta_da': abs(mw - target_mw),
            'formula': (met.find('hmdb:chemical_formula', NS).text
                        if met.find('hmdb:chemical_formula', NS) is not None else None),
        })

df = pd.DataFrame(candidates).sort_values('delta_da')
print(f"Candidates within {tolerance_da} Da of {target_mw:.3f}: {len(df)}")
print(df.head(10).to_string(index=False))
```

### Workflow 2: Biomarker Discovery for a Disease

**Goal**: Find all metabolites associated with a disease and their concentration changes. Assumes `root`, `NS` from Quick Start.

```python
import pandas as pd

disease_query = 'diabetes'
biomarkers = []
for met in root.findall('hmdb:metabolite', NS):
    for d in met.findall('hmdb:diseases/hmdb:disease', NS):
        dname = d.find('hmdb:name', NS)
        if dname is None or not dname.text:
            continue
        if disease_query.lower() not in dname.text.lower():
            continue
        abnormal = [c for c in met.findall(
            'hmdb:abnormal_concentrations/hmdb:concentration', NS)
            if c.find('hmdb:subject_condition', NS) is not None
            and disease_query.lower() in
            (c.find('hmdb:subject_condition', NS).text or '').lower()]
        biomarkers.append({
            'hmdb_id': met.find('hmdb:accession', NS).text,
            'metabolite': met.find('hmdb:name', NS).text,
            'disease': dname.text,
            'abnormal_measurements': len(abnormal),
        })

df = pd.DataFrame(biomarkers).drop_duplicates(['hmdb_id', 'disease'])
print(f"Metabolites linked to '{disease_query}': {len(df)}")
print(df.sort_values('abnormal_measurements', ascending=False).head(15).to_string(index=False))
```

### Workflow 3: Pathway Enrichment from Metabolite List

**Goal**: Given a list of identified metabolites, find over-represented pathways. Assumes `metabolite_index` from Quick Start.

```python
from collections import Counter
import pandas as pd

hit_ids = ['HMDB0000122', 'HMDB0000158', 'HMDB0000167',
           'HMDB0000148', 'HMDB0000064', 'HMDB0000161']

hit_pathways = Counter()
for hid in hit_ids:
    met = metabolite_index.get(hid)
    if met is None:
        continue
    for pw in met.findall('hmdb:pathways/hmdb:pathway', NS):
        pw_name = pw.find('hmdb:name', NS)
        if pw_name is not None and pw_name.text:
            hit_pathways[pw_name.text] += 1

enriched = [(pw, count) for pw, count in hit_pathways.most_common() if count >= 2]
df = pd.DataFrame(enriched, columns=['Pathway', 'Hit_Count'])
print(f"Pathways with 2+ hits from {len(hit_ids)} metabolites:")
print(df.to_string(index=False))
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Description |
|-----------|-------------------|---------|-------------|
| `NS` (namespace dict) | All XPath queries | `{'hmdb': 'http://www.hmdb.ca'}` | Required for all `find`/`findall` calls |
| `tolerance_da` | MW matching | `0.01` | Mass tolerance in Daltons for metabolite ID |
| `biospecimen` | `get_concentrations()` | `'Blood'` | Filter: `Blood`, `Urine`, `Cerebrospinal Fluid (CSF)`, `Saliva`, etc. |
| `events` | `ET.iterparse()` | `('end',)` | Parse events; use `('end',)` to fire on closing tags |
| adduct mass | MS identification | varies | `1.00728` [M+H]+, `22.9892` [M+Na]+, `-1.00728` [M-H]- |
| `target_type` | Spectral queries | `'MS'` or `'NMR'` | Filter spectra by type string |

## Best Practices

1. **Build an in-memory index on startup**: Parse once (60-120s), build dict by HMDB ID + lowercase name. Never re-parse inside a loop
2. **Always pass the namespace dict**: Every `find()`/`findall()` needs `NS = {'hmdb': 'http://www.hmdb.ca'}`. Omitting it returns empty results
3. **Use iterparse for memory constraints**: Full XML requires ~8-12 GB RAM. Use `elem.clear()` in iterparse to process incrementally
4. **Guard against None and empty text**: Many optional fields are absent. Always check `el is not None and el.text` before accessing
5. **Use monoisotopic weight for MS matching**: `monisotopic_molecular_weight` is correct for mass spec; `average_molecular_weight` for other calculations
6. **Pre-filter by chemical class for large searches**: Use taxonomy/classification to narrow searches before iterating all 220K+ entries

## Common Recipes

### Recipe: Export All Metabolite Properties to CSV

When to use: Create a flat table of all metabolites with key properties.

```python
import pandas as pd
records = []
for met in root.findall('hmdb:metabolite', NS):
    def txt(p):
        el = met.find(p, NS)
        return el.text if el is not None and el.text else None
    records.append({'hmdb_id': txt('hmdb:accession'), 'name': txt('hmdb:name'),
                    'formula': txt('hmdb:chemical_formula'),
                    'avg_mw': txt('hmdb:average_molecular_weight'),
                    'smiles': txt('hmdb:smiles')})
pd.DataFrame(records).to_csv('hmdb_properties.csv', index=False)
print(f"Exported {len(records)} metabolites")
```

### Recipe: Find Metabolites by Biofluid

When to use: Get all metabolites detected in a specific biofluid (e.g., urine for clinical screening).

```python
biofluid = 'Urine'
urine_mets = []
for met in root.findall('hmdb:metabolite', NS):
    for bf in met.findall(
            'hmdb:biological_properties/hmdb:biospecimen_locations/hmdb:biospecimen', NS):
        if bf.text and bf.text == biofluid:
            urine_mets.append({
                'hmdb_id': met.find('hmdb:accession', NS).text,
                'name': met.find('hmdb:name', NS).text,
            })
            break
print(f"Metabolites in {biofluid}: {len(urine_mets)}")
```

### Recipe: Chemical Class Distribution

When to use: Summarize metabolite chemical classes for a hit list or the full database.

```python
from collections import Counter
class_counts = Counter()
for met in root.findall('hmdb:metabolite', NS):
    tax = met.find('hmdb:taxonomy', NS)
    if tax is not None:
        sc = tax.find('hmdb:super_class', NS)
        if sc is not None and sc.text:
            class_counts[sc.text] += 1
print(dict(class_counts.most_common(10)))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `find()` returns `None` for known elements | Missing XML namespace | Always pass `NS = {'hmdb': 'http://www.hmdb.ca'}` |
| `MemoryError` parsing full XML | ~8-12 GB needed in memory | Use `ET.iterparse()` with `elem.clear()` |
| Slow startup (>120s) | Parsing 6 GB XML | Parse once, build index dict; avoid re-parsing |
| Metabolite not found by name | Case sensitivity or synonym | Normalize to lowercase; try HMDB ID directly |
| Empty spectra for a metabolite | Not all entries have spectra (~10-15% coverage) | Check coverage table; use METLIN or MassBank for more spectra |
| Missing concentration data | Limited to well-studied clinical metabolites (~20%) | Cross-reference with MetaboAnalyst or literature |
| Duplicate entries for same compound | Secondary accessions (HMDB00XXXXX vs HMDB0000XXXX) | Use `accession` (primary), not `secondary_accessions` |
| `ET.iterparse` missing data | Premature `elem.clear()` | Only clear after extracting all needed fields from the element |

## Bundled Resources

Self-contained entry. The original reference file `hmdb_data_fields.md` (268 lines, field catalog with XML element names and descriptions) is consolidated into the Key Concepts "HMDB XML Entry Structure" table and the "Data Field Completeness" table above. The field catalog's per-element XML tag names are demonstrated in Core API code blocks. Omitted from original: web interface descriptions (not programmatic), promotional content.

## Related Skills

- **drugbank-database-access** -- Drug-specific data (interactions, targets, pharmacology) with similar local XML parsing pattern
- **pubchem-compound-search** -- Live compound property lookups without downloading; PubChemPy REST API
- **kegg-database** -- Pathway and compound database with REST API for cross-referencing HMDB pathway hits
- **matchms-spectral-matching** -- Spectral similarity matching against reference libraries; complementary to HMDB spectral data
- **pyopenms-mass-spectrometry** -- Full LC-MS/MS processing pipeline; use HMDB for metabolite identification step

## References

- HMDB website and downloads: https://hmdb.ca/
- Wishart DS et al. (2022). HMDB 5.0: the Human Metabolome Database for 2022. *Nucleic Acids Res.* 50(D1):D801-D816. https://doi.org/10.1093/nar/gkab1062
- HMDB data download page: https://hmdb.ca/downloads
- MetaboAnalyst (complementary tool): https://www.metaboanalyst.ca/
