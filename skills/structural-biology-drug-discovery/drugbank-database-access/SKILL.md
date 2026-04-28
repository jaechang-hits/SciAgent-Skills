---
name: "drugbank-database-access"
description: "Parse local DrugBank XML for drug info, interactions, targets, and properties. Search by ID/name/CAS, extract DDIs with severity, map targets/enzymes/transporters, compute SMILES similarity. Primary via local XML; REST API rate-limited (3k/month dev). For live bioactivity use chembl-database-bioactivity; for compound properties use pubchem-compound-search."
license: "Unknown"
---

# DrugBank Database — Local XML Access

## Overview

Query the DrugBank comprehensive drug database (14,000+ drug entries, 5,000+ protein targets, 17,000+ drug interactions) by parsing the locally downloaded XML file with Python's ElementTree. Covers drug lookups, interaction checking, target/pathway extraction, chemical property analysis, and cross-database identifier mapping.

## When to Use

- Looking up drug information (description, indication, mechanism, pharmacology) by DrugBank ID, name, or CAS number
- Checking drug-drug interactions and severity classifications for polypharmacy safety
- Extracting drug targets, enzymes, transporters, and carriers with UniProt accessions
- Retrieving chemical properties (SMILES, InChI, molecular weight) for cheminformatics analysis
- Mapping DrugBank entries to external databases (PubChem, ChEMBL, UniProt, KEGG)
- Building drug similarity matrices from molecular fingerprints
- For live bioactivity data (IC50, Ki, EC50) use `chembl-database-bioactivity` instead
- For compound property lookups without downloading a database use `pubchem-compound-search` instead

## Prerequisites

- **DrugBank account**: Register at https://go.drugbank.com/ (free academic license)
- **XML download**: Download `drugbank_all_full_database.xml.zip` after registration (~1.5 GB uncompressed)
- **Python packages**: `lxml`, `rdkit` (similarity), `pandas` (tabular analysis)
- **REST API** (optional): 3,000 req/month dev tier; use local XML for batch work

```bash
pip install lxml pandas
pip install rdkit-pypi          # chemical similarity
pip install drugbank-downloader  # programmatic XML download
```

## Quick Start

```python
import xml.etree.ElementTree as ET

NS = {'db': 'http://www.drugbank.ca'}  # Required for ALL XPath queries

tree = ET.parse('drugbank_all_full_database.xml')  # 30-60s for full XML
root = tree.getroot()

# Build lookup index (DrugBank ID + lowercase name → element)
drug_index = {}
for drug in root.findall('db:drug', NS):
    db_id = drug.find('db:drugbank-id[@primary="true"]', NS)
    name = drug.find('db:name', NS)
    if db_id is not None and name is not None:
        drug_index[db_id.text] = drug
        drug_index[name.text.lower()] = drug

def find_drug(query):
    """Find drug by DrugBank ID, name (case-insensitive), or CAS number."""
    result = drug_index.get(query) or drug_index.get(query.lower())
    if result is not None:
        return result
    for drug in root.findall('db:drug', NS):  # CAS fallback
        cas = drug.find('db:cas-number', NS)
        if cas is not None and cas.text == query:
            return drug
    return None

drug = find_drug('DB00945')  # Aspirin
name = drug.find('db:name', NS).text
print(f"{name}: {drug.find('db:description', NS).text[:100]}...")
```

## Core API

### 1. Data Access and Setup

```python
import xml.etree.ElementTree as ET

NS = {'db': 'http://www.drugbank.ca'}
tree = ET.parse('drugbank_all_full_database.xml')
root = tree.getroot()
print(f"Total drug entries: {len(root.findall('db:drug', NS))}")
```

For memory-constrained environments, use iterparse:

```python
drug_names = {}
for event, elem in ET.iterparse('drugbank_all_full_database.xml', events=('end',)):
    if elem.tag == '{http://www.drugbank.ca}drug':
        db_id = elem.find('{http://www.drugbank.ca}drugbank-id[@primary="true"]')
        name = elem.find('{http://www.drugbank.ca}name')
        if db_id is not None and name is not None:
            drug_names[db_id.text] = name.text
        elem.clear()  # Free memory
print(f"Parsed {len(drug_names)} drugs via iterparse")
```

### 2. Drug Information Queries

```python
def get_drug_info(drug_element):
    """Extract comprehensive drug information."""
    def txt(path):
        el = drug_element.find(path, NS)
        return el.text if el is not None and el.text else None

    return {
        'drugbank_id': txt('db:drugbank-id[@primary="true"]'),
        'name': txt('db:name'),
        'type': drug_element.get('type'),
        'description': txt('db:description'),
        'indication': txt('db:indication'),
        'mechanism_of_action': txt('db:mechanism-of-action'),
        'cas_number': txt('db:cas-number'),
        'groups': [g.text for g in drug_element.findall('db:groups/db:group', NS)],
    }

info = get_drug_info(find_drug('Metformin'))
print(f"{info['name']} ({info['type']}): Groups={info['groups']}")
```

```python
# Search by name pattern (partial match)
def search_by_name(pattern):
    pattern_lower = pattern.lower()
    return [d for d in root.findall('db:drug', NS)
            if d.find('db:name', NS) is not None
            and pattern_lower in d.find('db:name', NS).text.lower()]

statins = search_by_name('statin')
print(f"Found {len(statins)} drugs matching 'statin'")
```

### 3. Drug-Drug Interactions

```python
def get_interactions(drug_element):
    """Extract all drug-drug interactions."""
    return [{
        'drugbank_id': i.find('db:drugbank-id', NS).text,
        'name': i.find('db:name', NS).text,
        'description': i.find('db:description', NS).text,
    } for i in drug_element.findall('db:drug-interactions/db:drug-interaction', NS)]

def classify_severity(description):
    """Classify severity from interaction description text."""
    if not description:
        return 'unknown'
    dl = description.lower()
    if any(w in dl for w in ['contraindicated', 'avoid', 'fatal', 'life-threatening']):
        return 'major'
    if any(w in dl for w in ['increase', 'decrease', 'enhance', 'reduce', 'alter']):
        return 'moderate'
    return 'minor'

interactions = get_interactions(find_drug('Aspirin'))
print(f"Aspirin has {len(interactions)} interactions")
for i in interactions[:3]:
    print(f"  [{classify_severity(i['description'])}] {i['name']}")
```

```python
# Check pairwise interaction between two drugs
def check_interaction(drug1_elem, drug2_elem):
    id2 = drug2_elem.find('db:drugbank-id[@primary="true"]', NS).text
    for inter in get_interactions(drug1_elem):
        if inter['drugbank_id'] == id2:
            inter['severity'] = classify_severity(inter['description'])
            return inter
    return None

result = check_interaction(find_drug('Warfarin'), find_drug('Aspirin'))
if result:
    print(f"[{result['severity']}] {result['description'][:150]}")
```

### 4. Drug Targets and Pathways

```python
def get_targets(drug_element, target_type='targets'):
    """Extract targets/enzymes/transporters/carriers.
    target_type: 'targets', 'enzymes', 'transporters', or 'carriers'
    """
    results = []
    for target in drug_element.findall(f'db:{target_type}/db:{target_type[:-1]}', NS):
        t = {
            'name': (target.find('db:name', NS).text
                     if target.find('db:name', NS) is not None else None),
            'actions': [a.text for a in target.findall('db:actions/db:action', NS) if a.text],
        }
        poly = target.find('db:polypeptide', NS)
        if poly is not None:
            t['uniprot_id'] = poly.get('id')
            gene = poly.find('db:gene-name', NS)
            t['gene_name'] = gene.text if gene is not None else None
        results.append(t)
    return results

drug = find_drug('Imatinib')
targets = get_targets(drug, 'targets')
enzymes = get_targets(drug, 'enzymes')
print(f"Imatinib — Targets: {len(targets)}, Enzymes: {len(enzymes)}")
for t in targets[:3]:
    print(f"  {t['name']} (UniProt: {t.get('uniprot_id', 'N/A')}) — {t['actions']}")
```

```python
def get_pathways(drug_element):
    """Extract SMPDB pathway associations."""
    pathways = []
    for pw in drug_element.findall('db:pathways/db:pathway', NS):
        name = pw.find('db:name', NS)
        smpdb = pw.find('db:smpdb-id', NS)
        pathways.append({
            'smpdb_id': smpdb.text if smpdb is not None else None,
            'name': name.text if name is not None else None,
        })
    return pathways

for pw in get_pathways(find_drug('Metformin')):
    print(f"  {pw['smpdb_id']}: {pw['name']}")
```

### 5. Chemical Properties and Similarity

```python
def get_property(drug_element, kind_name, section='calculated'):
    """Get a single property value by kind name."""
    prefix = f'db:{section}-properties/db:property'
    for prop in drug_element.findall(prefix, NS):
        kind = prop.find('db:kind', NS)
        if kind is not None and kind.text == kind_name:
            return prop.find('db:value', NS).text
    return None

def get_all_properties(drug_element):
    """Extract all calculated and experimental properties as a dict."""
    props = {}
    for section in ('calculated', 'experimental'):
        for prop in drug_element.findall(f'db:{section}-properties/db:property', NS):
            kind = prop.find('db:kind', NS)
            value = prop.find('db:value', NS)
            if kind is not None and value is not None:
                key = f'{section}_{kind.text}' if section == 'experimental' else kind.text
                props[key] = value.text
    return props

drug = find_drug('Aspirin')
print(f"SMILES: {get_property(drug, 'SMILES')}")
print(f"MW: {get_property(drug, 'Molecular Weight')}")
print(f"LogP: {get_property(drug, 'logP')}")
```

```python
# Tanimoto similarity between drugs using RDKit Morgan fingerprints
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs

def drug_similarity(drug1_elem, drug2_elem, radius=2, nbits=2048):
    smi1, smi2 = get_property(drug1_elem, 'SMILES'), get_property(drug2_elem, 'SMILES')
    if not smi1 or not smi2:
        return None
    mol1, mol2 = Chem.MolFromSmiles(smi1), Chem.MolFromSmiles(smi2)
    if mol1 is None or mol2 is None:
        return None
    fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, radius, nBits=nbits)
    fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, radius, nBits=nbits)
    return DataStructs.TanimotoSimilarity(fp1, fp2)

sim = drug_similarity(find_drug('Aspirin'), find_drug('Ibuprofen'))
print(f"Aspirin vs Ibuprofen: {sim:.3f}")
```

### 6. Cross-Database Integration

```python
def get_external_ids(drug_element):
    """Extract all external database identifiers."""
    ids = {}
    for ident in drug_element.findall('db:external-identifiers/db:external-identifier', NS):
        resource = ident.find('db:resource', NS)
        identifier = ident.find('db:identifier', NS)
        if resource is not None and identifier is not None:
            ids[resource.text] = identifier.text
    return ids

ids = get_external_ids(find_drug('Imatinib'))
print(f"PubChem: {ids.get('PubChem Compound')}, ChEMBL: {ids.get('ChEMBL')}, "
      f"KEGG: {ids.get('KEGG Drug')}, UniProt: {ids.get('UniProtKB')}")
```

```python
# Build cross-reference table for multiple drugs
import pandas as pd

def build_crossref_table(names):
    rows = []
    for name in names:
        d = find_drug(name)
        if d is None: continue
        ids = get_external_ids(d)
        rows.append({'drug': name,
                     'drugbank_id': d.find('db:drugbank-id[@primary="true"]', NS).text,
                     'pubchem': ids.get('PubChem Compound'),
                     'chembl': ids.get('ChEMBL'),
                     'kegg': ids.get('KEGG Drug')})
    return pd.DataFrame(rows)

print(build_crossref_table(['Aspirin', 'Metformin', 'Imatinib', 'Warfarin']).to_string(index=False))
```

## Key Concepts

### XML Namespace Handling

All DrugBank XML queries require the namespace prefix. Without it, XPath returns no results.

```python
NS = {'db': 'http://www.drugbank.ca'}
name = drug.find('db:name', NS).text     # CORRECT
name = drug.find('name')                  # WRONG — returns None!
# For iterparse, use full URI: '{http://www.drugbank.ca}drug'
```

### Drug Entry Structure

| Section | XPath | Content |
|---------|-------|---------|
| Identity | `db:drugbank-id`, `db:name`, `db:cas-number` | Primary identifiers |
| Pharmacology | `db:description`, `db:indication`, `db:mechanism-of-action` | Clinical text, mechanism, PD/PK |
| Interactions | `db:drug-interactions/db:drug-interaction` | Interacting drugs with descriptions |
| Targets | `db:targets/db:target` | Protein targets with actions |
| Enzymes/Transporters/Carriers | `db:enzymes/db:enzyme`, etc. | CYP450, P-gp, binding proteins |
| Pathways | `db:pathways/db:pathway` | SMPDB pathway associations |
| Properties | `db:calculated-properties`, `db:experimental-properties` | SMILES, MW, logP, etc. |
| External IDs | `db:external-identifiers` | PubChem, ChEMBL, KEGG, UniProt cross-refs |

### External Identifier Mapping

| Resource Name in XML | Database | Example |
|----------------------|----------|---------|
| `PubChem Compound` | PubChem CID | `2244` |
| `ChEMBL` | ChEMBL | `CHEMBL25` |
| `KEGG Drug` / `KEGG Compound` | KEGG | `D00109` / `C01405` |
| `UniProtKB` | UniProt | `P23219` |
| `PharmGKB` | PharmGKB | `PA452615` |
| `ChEBI` | ChEBI | `15365` |

### Calculated Property Kinds

Common `kind` values: `SMILES`, `InChI`, `InChIKey`, `Molecular Weight`, `Molecular Formula`, `logP`, `logS`, `Polar Surface Area (PSA)`, `Rotatable Bond Count`, `H Bond Acceptor Count`, `H Bond Donor Count`, `pKa (strongest acidic)`, `pKa (strongest basic)`, `Rule of Five`, `Bioavailability`.

## Common Workflows

### Workflow 1: Drug Discovery Target Analysis

**Goal**: Find all drugs targeting a specific gene and analyze their properties.

```python
import xml.etree.ElementTree as ET
import pandas as pd

NS = {'db': 'http://www.drugbank.ca'}
tree = ET.parse('drugbank_all_full_database.xml')
root = tree.getroot()

target_gene = 'EGFR'
records = []
for drug in root.findall('db:drug', NS):
    for target in drug.findall('db:targets/db:target', NS):
        poly = target.find('db:polypeptide', NS)
        if poly is None:
            continue
        gene = poly.find('db:gene-name', NS)
        if gene is not None and gene.text == target_gene:
            actions = [a.text for a in target.findall('db:actions/db:action', NS) if a.text]
            records.append({
                'drugbank_id': drug.find('db:drugbank-id[@primary="true"]', NS).text,
                'name': drug.find('db:name', NS).text,
                'groups': ', '.join(g.text for g in drug.findall('db:groups/db:group', NS)),
                'actions': ', '.join(actions),
            })

df = pd.DataFrame(records)
print(f"Drugs targeting {target_gene}: {len(df)}")
print(df.to_string(index=False))
```

### Workflow 2: Polypharmacy Safety Screening

**Goal**: Screen a medication list for all pairwise interactions with severity ranking.

```python
import xml.etree.ElementTree as ET
import pandas as pd

NS = {'db': 'http://www.drugbank.ca'}
tree = ET.parse('drugbank_all_full_database.xml')
root = tree.getroot()

# Build index and interaction maps
idx = {}
inter_map = {}  # drugbank_id → {interacting_id: description}
for drug in root.findall('db:drug', NS):
    name = drug.find('db:name', NS)
    db_id = drug.find('db:drugbank-id[@primary="true"]', NS)
    if name is None or db_id is None:
        continue
    idx[name.text.lower()] = db_id.text
    imap = {}
    for i in drug.findall('db:drug-interactions/db:drug-interaction', NS):
        imap[i.find('db:drugbank-id', NS).text] = i.find('db:description', NS).text
    inter_map[db_id.text] = imap

medications = ['Warfarin', 'Aspirin', 'Omeprazole', 'Atorvastatin', 'Metformin']
report = []
med_ids = [(m, idx.get(m.lower())) for m in medications]
for i, (n1, id1) in enumerate(med_ids):
    if not id1: continue
    for n2, id2 in med_ids[i+1:]:
        if not id2: continue
        desc = inter_map.get(id1, {}).get(id2)
        if desc:
            dl = desc.lower()
            sev = ('MAJOR' if any(w in dl for w in ['contraindicated','avoid','fatal'])
                   else 'MODERATE' if any(w in dl for w in ['increase','decrease','enhance','reduce'])
                   else 'MINOR')
            report.append({'Drug 1': n1, 'Drug 2': n2, 'Severity': sev,
                           'Description': desc[:120]})

df = pd.DataFrame(report)
print(f"=== Polypharmacy Report: {len(medications)} medications, {len(df)} interactions ===")
if not df.empty:
    print(df.sort_values('Severity').to_string(index=False))
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Description |
|-----------|-------------------|---------|-------------|
| `NS` (namespace dict) | All XPath queries | `{'db': 'http://www.drugbank.ca'}` | Required for all `find`/`findall` calls |
| `@primary="true"` | `db:drugbank-id` | — | Selects the primary DrugBank ID (DB00XXX) vs secondary IDs |
| `target_type` | `get_targets()` | `'targets'` | One of: `targets`, `enzymes`, `transporters`, `carriers` |
| `radius` | Morgan fingerprint | `2` | Fingerprint radius; 2 = ECFP4, 3 = ECFP6 |
| `nbits` | Morgan fingerprint | `2048` | Bit vector length; higher = fewer hash collisions |
| `events` | `ET.iterparse()` | — | Parse events; use `('end',)` to fire on closing tags |

## Best Practices

1. **Build an in-memory index on startup**: Parse once (30-60s), build dict by ID + lowercase name. Never re-parse inside a loop
2. **Always pass the namespace dict**: Every `find()`/`findall()` needs `NS`. Omitting it is the #1 source of empty results
3. **Use `iterparse` for memory constraints**: With `elem.clear()`, avoids loading the full 1.5 GB tree
4. **Guard against None**: Not all drugs have all fields. Always check `el is not None` before `.text`
5. **Prefer calculated over experimental properties**: Calculated (SMILES, logP, MW) available for nearly all drugs
6. **Cache interaction maps for polypharmacy**: Pre-build `{drug_id: {interacting_id: desc}}` once

## Common Recipes

### Recipe: Export All Drug Properties to CSV

```python
import pandas as pd
records = []
for drug in root.findall('db:drug', NS):
    row = {'drugbank_id': drug.find('db:drugbank-id[@primary="true"]', NS).text,
           'name': drug.find('db:name', NS).text, 'type': drug.get('type')}
    for prop in drug.findall('db:calculated-properties/db:property', NS):
        row[prop.find('db:kind', NS).text] = prop.find('db:value', NS).text
    records.append(row)
pd.DataFrame(records).to_csv('drugbank_properties.csv', index=False)
print(f"Exported {len(records)} drugs")
```

### Recipe: Lipinski Rule-of-5 Filter

```python
def check_lipinski(drug_element):
    props = get_all_properties(drug_element)
    try:
        mw = float(props.get('Molecular Weight', 9999))
        logp = float(props.get('logP', 99))
        hba = int(props.get('H Bond Acceptor Count', 99))
        hbd = int(props.get('H Bond Donor Count', 99))
    except (ValueError, TypeError):
        return None
    violations = sum([mw > 500, logp > 5, hba > 10, hbd > 5])
    return {'MW': mw, 'logP': logp, 'HBA': hba, 'HBD': hbd,
            'violations': violations, 'passes': violations <= 1}

print(check_lipinski(find_drug('Imatinib')))
```

### Recipe: Find CYP450 Substrates

```python
cyp = 'CYP3A4'
substrates = []
for drug in root.findall('db:drug', NS):
    for enz in drug.findall('db:enzymes/db:enzyme', NS):
        n = enz.find('db:name', NS)
        if n is not None and n.text and cyp.lower() in n.text.lower():
            actions = [a.text.lower() for a in enz.findall('db:actions/db:action', NS) if a.text]
            if 'substrate' in actions:
                substrates.append(drug.find('db:name', NS).text)
print(f"{cyp} substrates: {len(substrates)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `find()` returns `None` for known elements | Missing XML namespace | Always pass `NS = {'db': 'http://www.drugbank.ca'}` to `find()`/`findall()` |
| `MemoryError` parsing full XML | ~2-3 GB in memory | Use `ET.iterparse()` with `elem.clear()` |
| Slow startup (>60s) | Parsing 1.5 GB XML | Parse once, build index dict; avoid re-parsing |
| Drug not found by name | Case sensitivity or alternate name | Normalize to lowercase; try CAS or DrugBank ID |
| Empty `calculated-properties` | Biotech/protein drugs lack SMILES | Check `drug.get('type')` — biotech drugs have no small-molecule properties |
| `AttributeError: 'NoneType'` | Optional XML element absent | Guard with `el is not None` before `.text` |
| Asymmetric interaction counts | Interactions not symmetric in XML | Check both directions or build symmetric index |
| `drugbank-downloader` auth failure | Invalid credentials | Verify account at https://go.drugbank.com/ |
| REST API `429` | Exceeded rate limit | Switch to local XML for batch queries |

## Bundled Resources

**`references/interactions_targets.md`** — Consolidates interactions (severity heuristics, batch screening, description parsing) and targets/pathways (polypeptide details, action catalogs, enzyme/transporter coverage, pathway enrichment). Relocated inline: basic extraction (Core API 3-4). Omitted: verbose per-field parsing duplicating Core API.

**`references/chemical_analysis.md`** — Property extraction, descriptor computation, fingerprint similarity, drug-likeness filtering. Covers: full property catalog, similarity matrices, substructure search. Relocated inline: SMILES/InChI extraction + Tanimoto (Core API 5), Lipinski (Recipe). Omitted: 3D conformers (use rdkit-cheminformatics).

**Original disposition** (2,717 lines: SKILL.md 190 + 5 refs 2,166 + script 351):
- `SKILL.md` (190) — Stub rewritten with 6 Core API modules
- `data-access.md` (243) → Core API 1 + Quick Start
- `drug-queries.md` (387) → Core API 2
- `interactions.md` (426) → `references/interactions_targets.md` + Core API 3
- `targets-pathways.md` (519) → `references/interactions_targets.md` + Core API 4
- `chemical-analysis.md` (591) → `references/chemical_analysis.md` + Core API 5
- `drugbank_helper.py` (351) — Thin wrappers: `find_drug` → Quick Start; `get_drug_info`/`search_by_name` → Core API 2; `get_interactions`/`check_interaction`/`check_polypharmacy` → Core API 3; `get_targets` → Core API 4; `get_properties`/`get_smiles`/`get_inchi` → Core API 5

**Retention**: ~550 lines SKILL.md. With references (~600), aggregate ~1,150 / 2,717 = ~42%. Stub original; 5 refs → 2 via ceil(5/3)=2.
## Related Skills

- **chembl-database-bioactivity** — Live bioactivity database (IC50, Ki, EC50); complements DrugBank's static drug catalog
- **pubchem-compound-search** — Public compound property lookups without downloading a database
- **rdkit-cheminformatics** — Full cheminformatics toolkit for 3D conformers, advanced fingerprints, descriptors beyond DrugBank properties

## References

- DrugBank website: https://go.drugbank.com/
- DrugBank XML schema: https://docs.drugbank.com/xml/
- drugbank-downloader: https://pypi.org/project/drugbank-downloader/
- Wishart DS et al. (2018). DrugBank 5.0. *Nucleic Acids Res.* 46(D1):D1074-D1082. https://doi.org/10.1093/nar/gkx1037
