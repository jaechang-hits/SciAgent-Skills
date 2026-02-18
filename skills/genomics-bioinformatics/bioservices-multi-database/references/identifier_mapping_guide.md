# BioServices: Identifier Mapping Guide

Comprehensive guide to cross-database identifier conversion using bioservices. For basic mapping code, see SKILL.md Core API section 5.

## Overview

Biological databases use different identifier systems. BioServices provides four mapping approaches:

| Approach | Service | Best For |
|----------|---------|----------|
| UniProt Mapping | `UniProt.mapping()` | Protein/gene ID conversion (100+ database pairs) |
| UniChem | `UniChem` | Chemical compound ID mapping |
| KEGG cross-refs | `KEGG.get()` + parse | Extracting linked IDs from KEGG entries |
| PICR | `PICR` | Protein identifier cross-reference (legacy) |

## UniProt Mapping Service

### Basic Usage

```python
from bioservices import UniProt
u = UniProt(verbose=False)

# Single ID mapping
result = u.mapping(fr="UniProtKB_AC-ID", to="KEGG", query="P43403")
for r in result.get('results', []):
    print(f"{r['from']} → {r['to']}")

# Batch mapping (space-separated)
result = u.mapping(fr="UniProtKB_AC-ID", to="PDB", query="P43403 P04637 P53779")
for r in result.get('results', []):
    print(f"{r['from']} → {r['to']}")
```

### Supported Database Pairs

UniProt supports 100+ database pairs. Key mappings organized by category:

#### Protein/Gene Databases

| From | Code | To | Code |
|------|------|----|------|
| UniProtKB | `UniProtKB_AC-ID` | KEGG | `KEGG` |
| UniProtKB | `UniProtKB_AC-ID` | Ensembl gene | `Ensembl` |
| UniProtKB | `UniProtKB_AC-ID` | Ensembl protein | `Ensembl_Protein` |
| UniProtKB | `UniProtKB_AC-ID` | Ensembl transcript | `Ensembl_Transcript` |
| UniProtKB | `UniProtKB_AC-ID` | RefSeq protein | `RefSeq_Protein` |
| UniProtKB | `UniProtKB_AC-ID` | RefSeq nucleotide | `RefSeq_Nucleotide` |
| UniProtKB | `UniProtKB_AC-ID` | GeneID (Entrez) | `GeneID` |
| UniProtKB | `UniProtKB_AC-ID` | Gene Name | `Gene_Name` |
| KEGG | `KEGG` | UniProtKB | `UniProtKB` |
| Ensembl | `Ensembl` | UniProtKB | `UniProtKB` |
| GeneID | `GeneID` | UniProtKB | `UniProtKB` |
| Gene Name | `Gene_Name` | UniProtKB_AC-ID | `UniProtKB_AC-ID` |

#### Gene Nomenclature Databases

| Code | Database | Organism |
|------|----------|----------|
| `HGNC` | Human Gene Nomenclature Committee | Human |
| `MGI` | Mouse Genome Informatics | Mouse |
| `RGD` | Rat Genome Database | Rat |
| `SGD` | Saccharomyces Genome Database | Yeast |
| `FlyBase` | FlyBase | Drosophila |
| `WormBase` | WormBase | C. elegans |
| `ZFIN` | Zebrafish Information Network | Zebrafish |

#### Structure & Domain Databases

| Code | Database | Example ID |
|------|----------|-----------|
| `PDB` | Protein Data Bank | 2HYY |
| `Pfam` | Protein families | PF00069 |
| `InterPro` | Protein domains | IPR000719 |
| `SUPFAM` | Superfamily | SSF56112 |
| `PROSITE` | Protein motifs | PS00107 |

#### Pathway & Network Databases

| Code | Database | Example ID |
|------|----------|-----------|
| `Reactome` | Reactome pathways | R-HSA-109582 |
| `STRING` | Protein networks | 9606.ENSP00000264657 |
| `BioGRID` | Interaction database | 107422 |
| `GO` | Gene Ontology | GO:0006468 |
| `OMA` | Orthologous groups | — |

#### Expression & Proteomics

| Code | Database |
|------|----------|
| `PRIDE` | Proteomics data |
| `ProteomicsDB` | Protein expression |
| `PaxDb` | Protein abundance |

### Mapping Examples

```python
from bioservices import UniProt
u = UniProt(verbose=False)

# UniProt → KEGG
result = u.mapping(fr="UniProtKB_AC-ID", to="KEGG", query="P43403")
# → hsa:7535

# KEGG → UniProt (reverse)
result = u.mapping(fr="KEGG", to="UniProtKB", query="hsa:7535")

# UniProt → Ensembl (gene and protein)
result = u.mapping(fr="UniProtKB_AC-ID", to="Ensembl", query="P43403")
# → ENSG00000115085
result = u.mapping(fr="UniProtKB_AC-ID", to="Ensembl_Protein", query="P43403")
# → ENSP00000381359

# UniProt → PDB (often returns multiple structures)
result = u.mapping(fr="UniProtKB_AC-ID", to="PDB", query="P04637")
# → ['1A1U', '1AIE', '1C26', ...]

# UniProt → RefSeq
result = u.mapping(fr="UniProtKB_AC-ID", to="RefSeq_Protein", query="P43403")
# → NP_001070.2

# Gene Name → UniProt (with organism filter)
result = u.mapping(fr="Gene_Name", to="UniProtKB_AC-ID", query="ZAP70", taxId=9606)
```

## UniChem Compound Mapping

### Source Database IDs

| Source ID | Database | Source ID | Database |
|-----------|----------|-----------|----------|
| 1 | ChEMBL | 7 | ChEBI |
| 2 | DrugBank | 8 | NIH Clinical Collection |
| 3 | PDB | 14 | FDA/SRS |
| 4 | IUPHAR/BPS | 22 | PubChem (Compound) |
| 5 | PubChem (BioAssay) | 6 | KEGG |

### Usage Patterns

```python
from bioservices import UniChem
uc = UniChem()

# KEGG → ChEMBL (convenience method)
chembl_id = uc.get_compound_id_from_kegg("C11222")
print(f"ChEMBL: {chembl_id}")  # CHEMBL278315

# Get all database IDs for a compound
all_ids = uc.get_all_compound_ids("CHEMBL278315", src_id=1)  # 1=ChEMBL
for m in all_ids:
    print(f"  {m['src_name']}: {m['src_compound_id']}")

# Specific database conversion: ChEMBL → PubChem
result = uc.get_src_compound_ids("CHEMBL278315", from_src_id=1, to_src_id=22)
if result:
    print(f"PubChem: {result[0]['src_compound_id']}")

# ChEBI → DrugBank
result = uc.get_src_compound_ids("5292", from_src_id=7, to_src_id=2)
if result:
    print(f"DrugBank: {result[0]['src_compound_id']}")
```

## KEGG Identifier Conversions

KEGG entries contain cross-references that can be extracted via parsing.

### Extract Database Links

```python
from bioservices import KEGG
k = KEGG(verbose=False)

# From compound entry
entry = k.get("cpd:C11222")
parsed = k.parse(entry)
dblinks = parsed.get('DBLINKS', {})
# DBLINKS may contain: ChEBI, PubChem, CAS, etc.
print(f"Cross-references: {dblinks}")

# From gene entry
gene_entry = k.get("hsa:7535")
gene_parsed = k.parse(gene_entry)
# Extract specific links
for key in ['DBLINKS', 'PATHWAY', 'DISEASE']:
    if key in gene_parsed:
        print(f"{key}: {gene_parsed[key]}")
```

### KEGG Gene ID Format

```python
kegg_id = "hsa:7535"
organism, gene_id = kegg_id.split(":")
# organism = "hsa" (Homo sapiens), gene_id = "7535" (NCBI GeneID)
```

### Pathway → Genes Extraction

```python
k = KEGG(verbose=False)
pathway = k.get("path:hsa04660")
parsed = k.parse(pathway)
genes = parsed.get('GENE', {})
print(f"Found {len(genes)} genes in pathway")
for gene_id, desc in list(genes.items())[:5]:
    print(f"  hsa:{gene_id} — {desc}")
```

## Common Mapping Patterns

### Pattern 1: Gene Symbol → Multiple Database IDs

```python
from bioservices import UniProt
import time

def gene_to_all_ids(gene_symbol, organism=9606):
    """Map gene symbol to IDs in multiple databases."""
    u = UniProt(verbose=False)
    result = u.mapping(fr="Gene_Name", to="UniProtKB_AC-ID", query=gene_symbol, taxId=organism)
    if not result.get('results'):
        return None
    uniprot_id = result['results'][0]['to']['primaryAccession']

    ids = {'uniprot': uniprot_id}
    for db_name, db_code in [('kegg', 'KEGG'), ('ensembl', 'Ensembl'),
                              ('refseq', 'RefSeq_Protein'), ('pdb', 'PDB')]:
        try:
            r = u.mapping(fr="UniProtKB_AC-ID", to=db_code, query=uniprot_id)
            ids[db_name] = [x['to'] for x in r.get('results', [])]
        except Exception:
            ids[db_name] = []
        time.sleep(0.3)
    return ids

ids = gene_to_all_ids("ZAP70")
for db, values in ids.items():
    print(f"  {db}: {values}")
```

### Pattern 2: Compound Name → Cross-Database IDs

```python
from bioservices import KEGG, UniChem

def compound_to_all_ids(name):
    """Search compound by name and get all database IDs."""
    k = KEGG(verbose=False)
    results = k.find("compound", name)
    if not results:
        return None
    kegg_id = results.strip().split("\n")[0].split("\t")[0].replace("cpd:", "")

    # Get ChEBI from KEGG entry
    parsed = k.parse(k.get(f"cpd:{kegg_id}"))
    dblinks = parsed.get('DBLINKS', {})

    # Get all IDs from UniChem
    uc = UniChem()
    try:
        all_ids = uc.get_all_compound_ids(kegg_id, src_id=6)  # 6=KEGG
        return {'kegg': kegg_id, 'kegg_dblinks': dblinks,
                'unichem': {m['src_name']: m['src_compound_id'] for m in all_ids}}
    except Exception:
        return {'kegg': kegg_id, 'kegg_dblinks': dblinks}

ids = compound_to_all_ids("Geldanamycin")
print(ids)
```

### Pattern 3: Batch ID Conversion with Error Handling

```python
from bioservices import UniProt
import time

def safe_batch_mapping(ids, from_db, to_db, chunk_size=50):
    """Map IDs with chunking, error handling, and individual retry."""
    u = UniProt(verbose=False)
    all_results, failed = [], []

    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i+chunk_size]
        try:
            result = u.mapping(fr=from_db, to=to_db, query=" ".join(chunk))
            all_results.extend(result.get('results', []))
            print(f"  Chunk {i//chunk_size+1}: {len(result.get('results', []))} mapped")
        except Exception as e:
            print(f"  Chunk {i//chunk_size+1} failed: {e}")
            # Retry individually
            for single_id in chunk:
                try:
                    r = u.mapping(fr=from_db, to=to_db, query=single_id)
                    all_results.extend(r.get('results', []))
                except Exception:
                    failed.append(single_id)
        time.sleep(1)

    print(f"Total: {len(all_results)} mapped, {len(failed)} failed")
    return all_results, failed

results, failures = safe_batch_mapping(
    ["P43403", "P04637", "P53779", "INVALID123"],
    "UniProtKB_AC-ID", "KEGG"
)
```

### Pattern 4: Multi-Hop Mapping (Gene → UniProt → KEGG → Pathways)

```python
from bioservices import UniProt, KEGG
import time

def gene_to_pathways(gene_symbol, organism=9606):
    """Multi-hop: gene name → UniProt → KEGG → pathways."""
    u = UniProt(verbose=False)
    k = KEGG(verbose=False)

    # Hop 1: Gene → UniProt
    result = u.mapping(fr="Gene_Name", to="UniProtKB_AC-ID", query=gene_symbol, taxId=organism)
    if not result.get('results'):
        return None
    uniprot_id = result['results'][0]['to']['primaryAccession']
    time.sleep(0.3)

    # Hop 2: UniProt → KEGG
    kegg_result = u.mapping(fr="UniProtKB_AC-ID", to="KEGG", query=uniprot_id)
    kegg_ids = [r['to'] for r in kegg_result.get('results', [])]
    if not kegg_ids:
        return None
    kegg_id = kegg_ids[0]
    time.sleep(0.3)

    # Hop 3: KEGG gene → pathways
    org_code = kegg_id.split(":")[0]
    pathways = k.get_pathway_by_gene(kegg_id, org_code)

    return {'gene': gene_symbol, 'uniprot': uniprot_id,
            'kegg': kegg_id, 'pathways': pathways or {}}

result = gene_to_pathways("TP53")
if result:
    print(f"TP53 → {result['uniprot']} → {result['kegg']}")
    for pid, name in list(result['pathways'].items())[:5]:
        print(f"  {pid}: {name}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Mapping returns empty | ID not in target database | Verify source ID exists: `u.retrieve(id)`. Not all proteins have KEGG annotations |
| Batch mapping timeout | Too many IDs per request | Chunk into 50-100 IDs per request with `time.sleep(1)` between |
| Multiple target IDs | One-to-many mapping (e.g., UniProt → PDB) | Handle as list: `[r['to'] for r in result['results']]` |
| Organism ambiguity | Gene symbol shared across species | Always specify `taxId=9606` in `u.mapping()` or use `AND organism_id:9606` in search |
| Deprecated IDs fail | Old accessions retired | Retrieve entry to find secondary accessions: check `AC` lines in `u.retrieve(id, frmt="txt")` |
| Wrong database code | Codes are case-sensitive | Use exact codes: `UniProtKB_AC-ID` (not `uniprot`), `Gene_Name` (not `gene_name`) |

## Best Practices

1. **Always validate before batch** — verify a few IDs individually before batch processing thousands
2. **Handle None/empty gracefully** — web services return None, empty strings, or error codes (KEGG returns int 404)
3. **Chunk large batches** — 50-100 IDs per request prevents timeouts; add `time.sleep(0.5-1.0)` between chunks
4. **Cache results** — ID mappings rarely change; save results to CSV/dict for reuse
5. **Specify organism** — always include `taxId` or organism filter to avoid cross-species ambiguity
6. **Log failures for retry** — in batch operations, track failed IDs separately for later retry
7. **Prefer canonical entries** — filter for reviewed (Swiss-Prot) entries to get canonical protein IDs

Condensed from original: identifier_mapping.md (685 lines). Retained: all 4 mapping approaches (UniProt, UniChem, KEGG, PICR), complete database code tables (protein/gene, nomenclature, structure/domain, pathway/network, expression/proteomics), UniChem source database ID table, KEGG cross-reference extraction, all 4 common mapping patterns with full code (gene→multi-DB, compound→all-IDs, batch-with-retry, multi-hop), troubleshooting table, best practices. Original basic mapping code (single ID, batch) relocated to SKILL.md Core API section 5; multi-hop pattern relocated to SKILL.md Recipe 3. Omitted: individual mapping examples per database pair (UniProt→KEGG, KEGG→UniProt, UniProt→Ensembl, UniProt→PDB, UniProt→RefSeq — covered by Mapping Examples section with condensed inline comments), KEGG manual text parsing (replaced with k.parse()), verbose code for getting complete database code list (runtime API documentation).
