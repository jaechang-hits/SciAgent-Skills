# BioServices: Services Catalog

Catalog of 20+ bioinformatics web services accessible through bioservices, organized by category. For services covered in Core API (UniProt, KEGG, ChEMBL, ChEBI, NCBIblast, PSICQUIC, QuickGO), see SKILL.md for usage code.

## Protein & Gene Resources

### UniProt

Protein sequence and functional information (comprehensive protein database).

```python
from bioservices import UniProt
u = UniProt(verbose=False)
```

**Key Methods:**
| Method | Parameters | Returns |
|--------|-----------|---------|
| `search(query, frmt, columns, limit)` | `frmt`: tsv/fasta/xml/json/txt; `columns`: comma-separated field list | Formatted string |
| `retrieve(uniprot_id, frmt)` | `frmt`: txt/fasta/xml/rdf/gff | Entry in requested format |
| `mapping(fr, to, query, taxId)` | `fr`/`to`: database codes; `query`: space-separated IDs | Dict with `results` list |
| `searchUniProtId(pattern, columns, limit)` | Convenience for ID-based search | Tab-separated values |

**Common columns**: accession, gene_names, organism_name, protein_name, length, sequence, go_id, ec, pathway, cc_interaction

### KEGG

Metabolic pathways, genes, organisms, compounds, and diseases.

```python
from bioservices import KEGG
k = KEGG(verbose=False)
k.organism = "hsa"  # Set default organism
```

**Key Methods:**
| Method | Parameters | Returns |
|--------|-----------|---------|
| `list(database)` | `database`: organism/pathway/module/disease/drug/compound | Multi-line entry string |
| `find(database, query)` | Search by keywords | Matching entries with IDs |
| `get(entry_id)` | Genes, pathways, compounds, etc. | Raw entry text |
| `parse(data)` | Raw text from `get()` | Structured dict |
| `lookfor_organism(name)` | Name pattern | Matching organism codes |
| `get_pathway_by_gene(gene_id, organism)` | KEGG gene ID, organism code | Dict of pathway_id → name |
| `parse_kgml_pathway(pathway_id)` | Pathway ID | Dict with entries and relations |
| `pathway2sif(pathway_id)` | Pathway ID | List of (source, type, target) tuples |

### HGNC

Official human gene naming authority.

```python
from bioservices import HGNC
h = HGNC()
# h.search("ZAP70")  — search gene symbols/names
# h.fetch("symbol", "ZAP70")  — retrieve gene information
```

### MyGeneInfo

Gene annotation and batch query service.

```python
from bioservices import MyGeneInfo
m = MyGeneInfo()
# m.querymany(ids, scopes="symbol", fields="entrezgene,ensembl.gene", species="human")
# m.getgene(geneid)  — single gene annotation
```

## Chemical Compound Resources

### ChEBI

Chemical Entities of Biological Interest — dictionary of molecular entities.

```python
from bioservices import ChEBI
c = ChEBI(verbose=False)
# c.getCompleteEntity("CHEBI:15365")  — full compound info (SOAP response)
# c.getLiteEntity("aspirin", searchCategory="ALL NAMES", maximumResults=5)
# c.getCompleteEntityByList(["CHEBI:15365", "CHEBI:17234"])  — batch
```

### ChEMBL

Bioactive drug-like compound database with bioactivity data.

```python
from bioservices import ChEMBL
c = ChEMBL(verbose=False)
# c.get_molecule("CHEMBL25")  — compound details (JSON dict)
# c.get_target("CHEMBL2093863")  — target information
# c.get_similarity("CHEMBL25", similarity=85)  — similar compounds
# c.get_molecule_form("CHEMBL25")  — parent/salt forms
```

### UniChem

Chemical identifier mapping across databases.

```python
from bioservices import UniChem
u = UniChem()
# u.get_compound_id_from_kegg("C11222")  — KEGG → ChEMBL
# u.get_all_compound_ids("CHEMBL278315", src_id=1)  — all database IDs
# u.get_src_compound_ids("C11222", from_src_id=6, to_src_id=1)  — specific conversion
```

**Source Database IDs:**

| ID | Database | ID | Database |
|----|----------|----|----------|
| 1 | ChEMBL | 6 | KEGG |
| 2 | DrugBank | 7 | ChEBI |
| 3 | PDB | 8 | NIH Clinical Collection |
| 4 | IUPHAR/BPS | 14 | FDA/SRS |
| 5 | PubChem (BioAssay) | 22 | PubChem (Compound) |

### PubChem

NIH chemical compound database.

```python
from bioservices import PubChem
p = PubChem()
# p.get_compounds("aspirin", namespace="name")
# p.get_properties("MolecularWeight,XLogP", "aspirin", namespace="name")
```

## Sequence Analysis

### NCBIblast

Sequence similarity searching (asynchronous job submission).

```python
from bioservices import NCBIblast
s = NCBIblast(verbose=False)
```

**Key Methods:**
| Method | Parameters | Returns |
|--------|-----------|---------|
| `run(program, sequence, stype, database, email)` | `program`: blastp/blastn/blastx/tblastn/tblastx; `stype`: protein/dna; `database`: uniprotkb_swissprot/nr/pdb/etc | Job ID (string) |
| `getStatus(jobid)` | Job ID | "RUNNING"/"FINISHED"/"ERROR" |
| `getResultTypes(jobid)` | Job ID | Available result formats |
| `getResult(jobid, result_type)` | `result_type`: out/ids/xml/json | Result string |

**Important**: BLAST is async — submit → poll `getStatus()` → retrieve results.

## Pathway & Interaction Resources

### Reactome

Curated pathway database (human-focused).

```python
from bioservices import Reactome
r = Reactome(verbose=False)
# r.get_pathway_by_id("R-HSA-109582")  — pathway details
# r.search_pathway("apoptosis")  — search pathways
```

### PSICQUIC

Federated protein interaction query service (30+ databases).

```python
from bioservices import PSICQUIC
s = PSICQUIC(verbose=False)
# s.activeDBs  — list available databases
# s.query("intact", "identifier:P00520", frmt="tab25")
# Query syntax: "ZAP70 AND species:9606", "identifier:P43403 AND identifier:P04637"
```

**Available databases**: IntAct, MINT, BioGRID, DIP, InnateDB, MatrixDB, MPIDB, UniProt, and 25+ more.

**Output formats**: `tab25` (PSI-MI TAB 2.5), `tab27` (2.7), `xml25` (PSI-MI XML), `count` (hit count only).

### IntactComplex

Protein complex database from EBI.

```python
from bioservices import IntactComplex
i = IntactComplex(verbose=False)
# i.search("kinase")  — search complexes
# i.details("EBI-123456")  — complex composition details
```

### OmniPath

Integrated signaling pathway and regulatory network database.

```python
from bioservices import OmniPath
o = OmniPath()
# o.interactions(datasets="omnipath", organisms=9606)  — signaling interactions
# o.ptms(datasets="omnipath", organisms=9606)  — post-translational modifications
```

## Gene Ontology

### QuickGO

EBI Gene Ontology annotation service.

```python
from bioservices import QuickGO
g = QuickGO(verbose=False)
```

**Key Methods:**
| Method | Parameters | Returns |
|--------|-----------|---------|
| `Term(go_id, frmt)` | `go_id`: GO term; `frmt`: obo/json | Term definition and metadata |
| `Annotation(geneProductId, taxonId, goId)` | Filter by protein/taxon/GO | DataFrame of annotations |

**GO aspects**: Biological Process (BP), Molecular Function (MF), Cellular Component (CC).

## Genomic Resources

### BioMart

Data mining tool for genomic data (Ensembl-backed).

```python
from bioservices import BioMart
b = BioMart()
# b.datasets("default")  — list available datasets
# b.attributes("hsapiens_gene_ensembl")  — list queryable attributes
# b.query(query_xml)  — execute XML-formatted query
```

### ArrayExpress

Gene expression experiment database (EBI).

```python
from bioservices import ArrayExpress
a = ArrayExpress()
# a.queryExperiments(keywords="cancer AND breast", species="Homo sapiens")
# a.retrieveExperiment("E-MTAB-1234")
```

### ENA (European Nucleotide Archive)

Nucleotide sequence database.

```python
from bioservices import ENA
e = ENA()
# e.search_data("tax_tree(9606) AND mol_type=mRNA")
# e.retrieve_data("M10051", format="fasta")
```

## Structural Biology

### PDB

Protein Data Bank — experimental 3D structures.

```python
from bioservices import PDB
p = PDB()
# p.get_file("1A1U", file_format="pdb")  — download structure
# p.search(query)  — search structures
# File formats: pdb, cif, xml
```

### Pfam

Protein family and domain database.

```python
from bioservices import Pfam
p = Pfam()
# p.searchSequence(sequence)  — find domains in protein sequence
# p.getPfamEntry("PF00069")  — domain information
```

## Specialized Resources

### BioModels

Systems biology model repository (SBML format).

```python
from bioservices import BioModels
b = BioModels()
# b.get_model_by_id("BIOMD0000000012")  — retrieve SBML model
```

### COG (Clusters of Orthologous Genes)

Orthologous gene classification for comparative genomics.

```python
from bioservices import COG
c = COG()
# Orthology analysis and functional classification
```

### BiGG Models

Genome-scale metabolic network models.

```python
from bioservices import BiGG
b = BiGG()
# b.list_models()  — available metabolic models
# b.get_model("iJO1366")  — E. coli model details
```

## General Patterns

### Error Handling

```python
try:
    result = service.method(params)
    if result and not isinstance(result, int):  # KEGG returns 404 as int
        # Process result
        pass
except Exception as e:
    print(f"Service error: {e}")
```

### Timeout and Rate Control

```python
service = Service(verbose=False)
service.TIMEOUT = 30   # HTTP request timeout (seconds)
# For batch operations, add explicit time.sleep() between requests
```

### Caching

```python
service.CACHE = True    # Enable HTTP response caching
service.clear_cache()   # Clear cached responses
```

Condensed from original: services_reference.md (636 lines). Retained: all 20+ services organized by category (protein/gene, chemical compound, sequence analysis, pathway/interaction, gene ontology, genomic, structural, specialized), method signatures with key parameters for each service, UniChem source database ID table, PSICQUIC database list and output formats, GO aspects, general patterns (error handling, timeout, caching). Original UniProt/KEGG/ChEMBL/ChEBI/NCBIblast/PSICQUIC/QuickGO detailed code examples relocated to SKILL.md Core API sections 1-6. Omitted: use case bullet lists per service (covered in SKILL.md "When to Use"), verbose output format documentation (consolidated into SKILL.md Key Concepts "Output Format Handling" table), additional resources links (in SKILL.md References).
