---
name: bioservices-multi-database
description: >
  Unified Python interface to 40+ bioinformatics web services via bioservices library. Query
  UniProt proteins, KEGG pathways, ChEMBL/ChEBI/PubChem compounds, run BLAST searches, map
  identifiers across databases, retrieve GO annotations, and find protein-protein interactions.
  For single-database deep queries use dedicated tools (gget for Ensembl, pubchempy for PubChem);
  bioservices excels at cross-database integration workflows.
license: GPLv3
---

# BioServices Multi-Database Access

## Overview

BioServices provides a unified Python interface to 40+ bioinformatics web services including UniProt, KEGG, ChEMBL, ChEBI, PubChem, UniChem, PSICQUIC, QuickGO, and BLAST. Each service is accessed through a consistent object-oriented API with built-in caching, rate limiting, and output format handling.

## When to Use

- Querying protein information from UniProt (search, retrieve, ID mapping)
- Discovering KEGG pathways and extracting gene/interaction networks
- Cross-referencing compounds across ChEMBL, ChEBI, PubChem, and KEGG
- Running BLAST sequence similarity searches against UniProtKB
- Mapping identifiers between biological databases (UniProt, Ensembl, KEGG, RefSeq, PDB)
- Retrieving Gene Ontology annotations via QuickGO
- Finding protein-protein interactions via PSICQUIC (IntAct, MINT, BioGRID)
- Batch converting thousands of biological identifiers with error handling
- For single-database deep queries → use gget (Ensembl), pubchempy (PubChem), or chembl-database skill
- For pathway visualization → use pathway analysis tools (Cytoscape, NetworkX) after retrieving data with bioservices

## Prerequisites

```bash
pip install bioservices
# Optional: pandas for tabular output, matplotlib for visualization
pip install pandas matplotlib
```

**API Rate Limits**: Most services have rate limits. bioservices handles basic throttling internally, but for batch operations add explicit delays:
- UniProt mapping: ~1 request/second for batch jobs
- KEGG: 10 requests/second (be conservative with pathway parsing)
- ChEMBL/ChEBI: 5-10 requests/second
- BLAST: 1 job at a time (async polling, ~30-300s per job)

## Quick Start

```python
from bioservices import UniProt, KEGG
import time

# Protein lookup
u = UniProt(verbose=False)
result = u.search("ABL1_HUMAN", frmt="tsv", columns="accession,gene_names,organism_name,length")
print(result[:200])

# Pathway discovery
k = KEGG(verbose=False)
pathways = k.get_pathway_by_gene("hsa:25", "hsa")  # ABL1
print(f"ABL1 participates in {len(pathways)} pathways")
for pid, name in list(pathways.items())[:3]:
    print(f"  {pid}: {name}")
```

## Core API

### 1. Protein Analysis (UniProt)

```python
from bioservices import UniProt
u = UniProt(verbose=False)

# Search by protein name or gene
result = u.search("BRCA1 AND organism_id:9606", frmt="tsv",
                  columns="accession,gene_names,protein_name,length,go_p")
print(result[:300])

# Retrieve full entry
entry = u.retrieve("P38398", frmt="txt")  # Swiss-Prot flat file
fasta = u.retrieve("P38398", frmt="fasta")
print(fasta[:200])
```

```python
# ID mapping: gene names → UniProt accessions
result = u.mapping(fr="Gene_Name", to="UniProtKB", query="BRCA1 TP53 ABL1", taxId=9606)
print(f"Mapped {len(result['results'])} entries")
for r in result['results']:
    print(f"  {r['from']} → {r['to']['primaryAccession']}")
```

### 2. Pathway Discovery (KEGG)

```python
from bioservices import KEGG
k = KEGG(verbose=False)

# List pathways for an organism
pathways = k.pathwayIds  # All reference pathways
human_pathways = k.list("pathway", "hsa")
print(f"Human pathways: {len(human_pathways.strip().splitlines())}")

# Get pathway details
pathway_data = k.get("hsa04110")  # Cell cycle
parsed = k.parse(pathway_data)
print(f"Pathway: {parsed.get('NAME', 'Unknown')}")
print(f"Genes: {len(parsed.get('GENE', {}))}")
```

```python
# KGML parsing for interaction networks
from bioservices import KEGG
k = KEGG(verbose=False)

kgml = k.get("hsa04110", "kgml")  # XML pathway representation
# Parse KGML for entries and relations
import xml.etree.ElementTree as ET
root = ET.fromstring(kgml)
entries = root.findall("entry")
relations = root.findall("relation")
print(f"Entries: {len(entries)}, Relations: {len(relations)}")

# Extract interaction types
from collections import Counter
rel_types = Counter()
for rel in relations:
    for subtype in rel.findall("subtype"):
        rel_types[subtype.get("name")] += 1
print(f"Interaction types: {dict(rel_types)}")
```

### 3. Compound Databases (ChEMBL, ChEBI, UniChem, PubChem)

```python
from bioservices import ChEMBL, ChEBI, UniChem
import time

# ChEMBL compound lookup
chembl = ChEMBL(verbose=False)
result = chembl.get_molecule("CHEMBL25")  # Aspirin
print(f"Name: {result['pref_name']}")
print(f"MW: {result['molecule_properties']['full_mwt']}")
print(f"SMILES: {result['molecule_structures']['canonical_smiles']}")

time.sleep(0.2)

# ChEBI entity lookup
chebi = ChEBI(verbose=False)
entity = chebi.getCompleteEntity("CHEBI:15365")  # Aspirin
print(f"ChEBI Name: {entity.chebiAsciiName}")
print(f"Formula: {entity.formulae[0].data if entity.formulae else 'N/A'}")
```

```python
# Cross-database compound mapping via UniChem
from bioservices import UniChem
uc = UniChem()

# Map ChEMBL ID to other databases
# Source IDs: 1=ChEMBL, 2=DrugBank, 3=PDB, 4=IUPHAR, 7=ChEBI, 22=PubChem
mappings = uc.get_mapping("CHEMBL25", 1)  # From ChEMBL
for m in mappings[:5]:
    print(f"  Source {m['src_id']}: {m['src_compound_id']}")
```

### 4. Sequence Analysis (BLAST)

```python
from bioservices import NCBIblast
import time

blast = NCBIblast(verbose=False)

sequence = ">query\nMKTAYIAKQRQISFVKSHFSRQLE..."  # Truncated for brevity
job_id = blast.run(
    program="blastp",
    database="uniprotkb_swissprot",
    sequence=sequence,
    stype="protein",
    email="user@example.com"  # Required by NCBI
)
print(f"Job submitted: {job_id}")

# Poll for results (async)
while blast.getStatus(job_id) == "RUNNING":
    time.sleep(10)
    print("Waiting...")

result_types = blast.getResultTypes(job_id)
alignment = blast.getResult(job_id, "out")  # Text alignment
print(alignment[:500])
```

### 5. Identifier Mapping

```python
from bioservices import UniProt
u = UniProt(verbose=False)

# Batch mapping: UniProt → multiple databases
accessions = "P00520 P12931 P04637 P38398"

# UniProt → PDB
result = u.mapping(fr="UniProtKB_AC-ID", to="PDB", query=accessions)
for r in result.get('results', []):
    print(f"  {r['from']} → {r['to']}")

# UniProt → Ensembl
result = u.mapping(fr="UniProtKB_AC-ID", to="Ensembl", query=accessions)
print(f"Mapped {len(result.get('results', []))} entries to Ensembl")
```

```python
# KEGG-based identifier extraction
from bioservices import KEGG
k = KEGG(verbose=False)

# Get cross-references from a KEGG entry
entry = k.get("hsa:25")  # ABL1
parsed = k.parse(entry)
# Extract database links
for key in ['DBLINKS', 'PATHWAY']:
    if key in parsed:
        print(f"{key}: {parsed[key]}")
```

### 6. Gene Ontology & Protein Interactions

```python
from bioservices import QuickGO
go = QuickGO(verbose=False)

# Get GO annotations for a protein
annotations = go.Annotation(geneProductId="UniProtKB:P00520", taxonId="9606")
if hasattr(annotations, 'shape'):  # DataFrame
    print(f"Annotations: {len(annotations)}")
    for aspect in ['biological_process', 'molecular_function', 'cellular_component']:
        subset = annotations[annotations['goAspect'] == aspect]
        print(f"  {aspect}: {len(subset)} terms")
```

```python
# Protein-protein interactions via PSICQUIC
from bioservices import PSICQUIC
psicquic = PSICQUIC(verbose=False)

# Query IntAct for interactions
interactions = psicquic.query("intact", "identifier:P00520", frmt="tab25")
lines = interactions.strip().split("\n") if interactions else []
print(f"Interactions found: {len(lines)}")
for line in lines[:3]:
    fields = line.split("\t")
    print(f"  {fields[0]} <-> {fields[1]}")  # Interactor A <-> Interactor B
```

## Key Concepts

### Service Initialization & Verbosity

All services share a common pattern: `Service(verbose=False)` suppresses HTTP request logging. Set `verbose=True` during debugging to see full request/response details.

### Output Format Handling

| Service | Default Format | Available Formats | Notes |
|---------|---------------|-------------------|-------|
| UniProt | XML | `tsv`, `fasta`, `json`, `txt`, `xml`, `gff` | Use `tsv` with `columns=` for tabular |
| KEGG | Text | `kgml`, `image` | Parse text with `k.parse()` |
| ChEMBL | JSON | JSON only | Dict access on response |
| ChEBI | SOAP XML | Object attributes | Access via `.chebiAsciiName` etc. |
| NCBIblast | Text | `out`, `xml`, `json`, `ids` | Async: submit → poll → retrieve |
| PSICQUIC | PSI-MI TAB | `tab25`, `tab27`, `xml25`, `count` | Tab-separated interaction records |
| QuickGO | DataFrame | `tsv`, `json` | Pandas DataFrame when available |

### Common Organism Codes (KEGG)

| Code | Organism | Taxonomy ID |
|------|----------|-------------|
| `hsa` | Homo sapiens | 9606 |
| `mmu` | Mus musculus | 10090 |
| `rno` | Rattus norvegicus | 10116 |
| `dme` | Drosophila melanogaster | 7227 |
| `sce` | Saccharomyces cerevisiae | 559292 |
| `eco` | Escherichia coli K-12 | 83333 |
| `ath` | Arabidopsis thaliana | 3702 |

### UniProt Mapping Database Codes

Common database pairs for `u.mapping(fr=, to=)`:

| Category | Database Code | Example |
|----------|--------------|---------|
| Protein | `UniProtKB_AC-ID` | P00520 |
| Gene | `Gene_Name`, `GeneID` | ABL1, 25 |
| Structure | `PDB` | 2HYY |
| Sequence | `RefSeq_Protein`, `Ensembl` | NP_005148, ENSG00000097007 |
| Pathway | `KEGG`, `Reactome` | hsa:25, R-HSA-123 |
| Ontology | `GO` | GO:0006468 |

Full mapping database list: see references/identifier_mapping_guide.md.

## Common Workflows

### Workflow 1: Complete Protein Analysis Pipeline

```python
from bioservices import UniProt, KEGG, QuickGO, PSICQUIC
import time

def analyze_protein(uniprot_id):
    """End-to-end protein analysis: metadata → pathways → GO → interactions."""
    results = {}

    # Step 1: UniProt metadata
    u = UniProt(verbose=False)
    entry = u.retrieve(uniprot_id, frmt="tsv",
                       columns="accession,gene_names,protein_name,length,organism_name")
    results['uniprot'] = entry
    print(f"[1] UniProt entry retrieved")

    # Step 2: KEGG pathways
    k = KEGG(verbose=False)
    mapping = u.mapping(fr="UniProtKB_AC-ID", to="KEGG", query=uniprot_id)
    kegg_ids = [r['to'] for r in mapping.get('results', [])]
    if kegg_ids:
        pathways = k.get_pathway_by_gene(kegg_ids[0], kegg_ids[0][:3])
        results['pathways'] = pathways or {}
        print(f"[2] Found {len(results['pathways'])} pathways")
    time.sleep(0.3)

    # Step 3: GO annotations
    go = QuickGO(verbose=False)
    annotations = go.Annotation(geneProductId=f"UniProtKB:{uniprot_id}")
    results['go_annotations'] = annotations
    print(f"[3] GO annotations retrieved")
    time.sleep(0.3)

    # Step 4: Protein interactions
    psicquic = PSICQUIC(verbose=False)
    interactions = psicquic.query("intact", f"identifier:{uniprot_id}", frmt="tab25")
    lines = interactions.strip().split("\n") if interactions else []
    results['interactions'] = len(lines)
    print(f"[4] Found {len(lines)} interactions")

    return results

# Usage
results = analyze_protein("P00520")  # ABL1
```

### Workflow 2: Cross-Database Compound Search

```python
from bioservices import KEGG, ChEMBL, ChEBI, UniChem
import time

def search_compound(compound_name):
    """Search compound across KEGG → ChEBI → ChEMBL with cross-references."""
    k = KEGG(verbose=False)

    # Step 1: KEGG compound search
    kegg_results = k.find("compound", compound_name)
    if not kegg_results:
        print(f"No KEGG results for '{compound_name}'")
        return None
    kegg_id = kegg_results.strip().split("\t")[0]  # First hit
    kegg_entry = k.parse(k.get(kegg_id))
    print(f"[1] KEGG: {kegg_id} — {kegg_entry.get('NAME', ['Unknown'])[0]}")
    print(f"    Formula: {kegg_entry.get('FORMULA', 'N/A')}")
    time.sleep(0.2)

    # Step 2: ChEBI cross-reference
    dblinks = kegg_entry.get('DBLINKS', {})
    chebi_id = dblinks.get('ChEBI', [''])[0] if isinstance(dblinks, dict) else None
    if chebi_id:
        chebi = ChEBI(verbose=False)
        entity = chebi.getCompleteEntity(f"CHEBI:{chebi_id}")
        print(f"[2] ChEBI: {entity.chebiId} — {entity.chebiAsciiName}")
        time.sleep(0.2)

    # Step 3: ChEMBL via UniChem
    uc = UniChem()
    try:
        chembl_mappings = uc.get_mapping(kegg_id.replace("cpd:", ""), 6)  # 6=KEGG
        if chembl_mappings:
            chembl_id = [m for m in chembl_mappings if m['src_id'] == '1']
            if chembl_id:
                chembl = ChEMBL(verbose=False)
                mol = chembl.get_molecule(chembl_id[0]['src_compound_id'])
                print(f"[3] ChEMBL: {mol['molecule_chembl_id']} — MW: {mol['molecule_properties']['full_mwt']}")
    except Exception as e:
        print(f"[3] ChEMBL mapping failed: {e}")

    return kegg_entry

result = search_compound("aspirin")
```

### Workflow 3: Batch Identifier Conversion

```python
from bioservices import UniProt
import time

def batch_convert_ids(ids, from_db, to_db, chunk_size=100):
    """Convert biological IDs in chunks with error handling."""
    u = UniProt(verbose=False)
    all_results = []
    failed = []

    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i+chunk_size]
        query = " ".join(chunk)
        try:
            result = u.mapping(fr=from_db, to=to_db, query=query)
            mapped = result.get('results', [])
            all_results.extend(mapped)
            print(f"  Chunk {i//chunk_size + 1}: {len(mapped)} mapped")
        except Exception as e:
            print(f"  Chunk {i//chunk_size + 1} failed: {e}")
            failed.extend(chunk)
        time.sleep(1)  # Rate limit between chunks

    print(f"\nTotal mapped: {len(all_results)}, Failed: {len(failed)}")
    return all_results, failed

# Usage: Gene names → UniProt accessions
gene_list = ["BRCA1", "TP53", "ABL1", "EGFR", "BRAF", "KRAS", "MYC", "PTEN"]
results, failed = batch_convert_ids(gene_list, "Gene_Name", "UniProtKB_AC-ID")
for r in results[:5]:
    print(f"  {r['from']} → {r['to']['primaryAccession']}")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range | Effect |
|-----------|------------------|---------|-------|--------|
| `verbose` | All services | `True` | bool | HTTP request logging |
| `frmt` | UniProt search/retrieve | `xml` | tsv/fasta/json/txt | Output format |
| `columns` | UniProt search | — | comma-separated | TSV columns to return |
| `taxId` | UniProt mapping | — | NCBI taxonomy ID | Organism filter for mapping |
| `program` | NCBIblast | — | blastp/blastn/blastx/tblastn | BLAST program type |
| `database` | NCBIblast | — | uniprotkb_swissprot/nr/etc | Target database |
| `email` | NCBIblast | — | email address | Required by NCBI policy |
| `chunk_size` | Batch operations | 100 | 10-500 | IDs per batch request |
| `frmt` | PSICQUIC query | `tab25` | tab25/tab27/xml25/count | Interaction output format |

## Best Practices

1. **Always set `verbose=False` in production** — default `True` floods stdout with HTTP details. Use `True` only for debugging failed requests

2. **Handle None/empty results gracefully** — web services frequently return None, empty strings, or partial data. Always check before parsing:
   ```python
   result = k.get("hsa04110")
   if result and not isinstance(result, int):  # KEGG returns 404 as int
       parsed = k.parse(result)
   ```

3. **Use explicit `time.sleep()` between batch requests** — even though bioservices has internal throttling, batch operations benefit from explicit delays (0.2-1.0s) to avoid 429 errors

4. **Cache service objects, not results** — create one `UniProt()` instance and reuse it across calls. Each constructor call initializes a new HTTP session

5. **Anti-pattern — parsing KEGG text manually**: Always use `k.parse()` to parse KEGG entry text into structured dicts. Manual string splitting breaks on multi-line fields

6. **Specify organism in UniProt searches** — unfiltered searches return results across all species. Add `AND organism_id:9606` for human-specific results

## Common Recipes

### Recipe 1: Pathway Network Statistics

```python
from bioservices import KEGG
import xml.etree.ElementTree as ET
from collections import Counter

def pathway_stats(organism="hsa", limit=10):
    """Analyze pathway network statistics for an organism."""
    k = KEGG(verbose=False)
    pathway_list = k.list("pathway", organism).strip().split("\n")
    stats = []
    for line in pathway_list[:limit]:
        pid = line.split("\t")[0]
        kgml = k.get(pid, "kgml")
        if not kgml or isinstance(kgml, int):
            continue
        root = ET.fromstring(kgml)
        genes = len([e for e in root.findall("entry") if e.get("type") == "gene"])
        rels = len(root.findall("relation"))
        stats.append({"pathway": pid, "genes": genes, "relations": rels})
    return sorted(stats, key=lambda x: x['relations'], reverse=True)

top = pathway_stats("hsa", limit=5)
for s in top:
    print(f"  {s['pathway']}: {s['genes']} genes, {s['relations']} interactions")
```

### Recipe 2: GO Term Enrichment Preparation

```python
from bioservices import QuickGO, UniProt
import time

def get_go_terms(uniprot_ids, aspect="biological_process"):
    """Collect GO annotations for a list of proteins."""
    go = QuickGO(verbose=False)
    all_terms = {}
    for uid in uniprot_ids:
        try:
            annot = go.Annotation(geneProductId=f"UniProtKB:{uid}", taxonId="9606")
            if hasattr(annot, 'shape') and len(annot) > 0:
                subset = annot[annot['goAspect'] == aspect]
                all_terms[uid] = list(subset['goId'].unique())
        except Exception:
            all_terms[uid] = []
        time.sleep(0.3)
    return all_terms

terms = get_go_terms(["P00520", "P12931", "P04637"])
for uid, go_ids in terms.items():
    print(f"  {uid}: {len(go_ids)} {go_ids[:3]}")
```

### Recipe 3: Multi-Hop Identifier Mapping

```python
from bioservices import UniProt, KEGG
import time

def gene_to_pathways(gene_name, organism="hsa"):
    """Map gene name → UniProt → KEGG → pathways (multi-hop)."""
    u = UniProt(verbose=False)

    # Hop 1: Gene name → UniProt
    result = u.mapping(fr="Gene_Name", to="UniProtKB_AC-ID", query=gene_name, taxId=9606)
    if not result.get('results'):
        return None
    uniprot_id = result['results'][0]['to']['primaryAccession']
    print(f"  {gene_name} → UniProt: {uniprot_id}")
    time.sleep(0.3)

    # Hop 2: UniProt → KEGG
    kegg_result = u.mapping(fr="UniProtKB_AC-ID", to="KEGG", query=uniprot_id)
    if not kegg_result.get('results'):
        return None
    kegg_id = kegg_result['results'][0]['to']
    print(f"  UniProt: {uniprot_id} → KEGG: {kegg_id}")
    time.sleep(0.3)

    # Hop 3: KEGG gene → pathways
    k = KEGG(verbose=False)
    pathways = k.get_pathway_by_gene(kegg_id, organism)
    print(f"  KEGG: {kegg_id} → {len(pathways or {})} pathways")
    return pathways

pathways = gene_to_pathways("BRCA1")
if pathways:
    for pid, name in list(pathways.items())[:5]:
        print(f"    {pid}: {name}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ConnectionError` on service init | Network/firewall blocking | Check internet; some services need port 443 |
| UniProt search returns empty | Query syntax error | Use `AND`/`OR` operators; check field names in UniProt docs |
| KEGG `get()` returns `404` (int) | Invalid pathway/gene ID | Verify ID format: `hsa:25` (gene), `hsa04110` (pathway), `cpd:C00001` (compound) |
| BLAST job timeout | Large sequence or busy server | Increase polling interval; try `uniprotkb_swissprot` (smaller than `nr`) |
| UniProt mapping returns no results | Wrong database codes | Use exact codes: `UniProtKB_AC-ID`, `Gene_Name`, `PDB`, `Ensembl` (case-sensitive) |
| `AttributeError` on ChEBI entity | SOAP response parsing | Check `entity is not None`; some ChEBI IDs lack certain fields |
| PSICQUIC returns empty string | No interactions in database | Try multiple databases: `intact`, `mint`, `biogrid` |
| `429 Too Many Requests` | Rate limit exceeded | Add `time.sleep(0.5)` between requests; reduce batch size |
| Inconsistent mapping results | Multiple isoforms/entries | Filter by `isReviewed=true` for canonical UniProt entries |

## Bundled Resources

### references/services_catalog.md

Catalog of 20+ bioservices-accessible services organized by category: protein/gene resources (UniProt, KEGG, HGNC, MyGeneInfo), chemical compound resources (ChEBI, ChEMBL, UniChem, PubChem), sequence analysis (NCBIblast), pathway/interaction resources (Reactome, PSICQUIC, IntactComplex, OmniPath), gene ontology (QuickGO), genomic resources (BioMart, ArrayExpress, ENA), structural biology (PDB, Pfam), and specialized resources (BioModels, COG, BiGG). Includes method signatures, key parameters, and output formats for each service. General patterns (error handling, verbosity, caching) relocated to SKILL.md Best Practices. Original services_reference.md content partially relocated to Core API (UniProt, KEGG, ChEMBL, ChEBI, BLAST, PSICQUIC, QuickGO sections); remaining services retained in catalog.

### references/identifier_mapping_guide.md

Comprehensive guide to cross-database identifier conversion: UniProt mapping service (100+ database pairs with database code tables), UniChem compound mapping (source database IDs), KEGG identifier conversions, 4 common mapping patterns with code, and troubleshooting. Original identifier_mapping.md content partially relocated to Core API section 5 (basic mapping examples); advanced patterns, full database code tables, and multi-hop strategies retained in guide.

**Scripts disposition** (4 original scripts, 1,444 lines total):
- `protein_analysis_workflow.py` (409 lines, 7 functions: search_protein, retrieve_sequence, run_blast, discover_pathways, find_interactions, get_go_annotations, main): End-to-end pipeline → Common Workflow 1 "Complete Protein Analysis Pipeline"
- `compound_cross_reference.py` (379 lines, 7 functions: search_kegg_compound, get_kegg_info, get_chembl_id, get_chebi_info, get_chembl_info, save_results, main): Multi-DB compound search → Common Workflow 2 "Cross-Database Compound Search"
- `batch_id_converter.py` (348 lines, 8 functions: normalize_database_code, read_ids_from_file, batch_convert, save_mapping_csv, save_failed_ids, print_mapping_summary, list_common_databases, main): Batch conversion → Common Workflow 3 "Batch Identifier Conversion" + Core API section 5
- `pathway_analysis.py` (310 lines, 8 functions: get_all_pathways, analyze_pathway, analyze_all_pathways, save_pathway_summary, save_interactions_sif, save_detailed_pathway_info, print_statistics, main): KGML network analysis → Core API section 2 (KGML parsing) + Recipe 1 "Pathway Network Statistics"
- CLI argument parsing, CSV/SIF file I/O, and summary printing utilities from all scripts: omitted — trivial boilerplate not essential for API understanding

**Omitted original content**: workflow_patterns.md (811 lines, 7 detailed workflows) — 4 workflows consolidated into Common Workflows 1-3 and Recipe 3; remaining 3 workflows (gene annotation pipeline, interaction network analysis, comparative species analysis) omitted as they combine patterns already shown in Core API modules without introducing new API calls.

## Related Skills

- **gget-genomic-data** — deeper Ensembl/BLAST/enrichment queries via gget (simpler API for single-database access)
- **chembl-database** — dedicated ChEMBL bioactivity queries beyond compound lookup
- **pubchem-database** — dedicated PubChem compound/assay queries with similarity search

## References

- BioServices documentation: https://bioservices.readthedocs.io/
- BioServices source: https://github.com/cokelaer/bioservices
- Cokelaer et al. (2013) BioServices: a common Python package to access biological Web Services programmatically. *Bioinformatics* 29(24): 3241-3242
- UniProt REST API: https://www.uniprot.org/help/api
- KEGG API: https://www.kegg.jp/kegg/rest/keggapi.html
- QuickGO API: https://www.ebi.ac.uk/QuickGO/api/index.html
