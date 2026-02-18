---
name: kegg-database
description: "Direct REST API access to KEGG (academic use only). Query pathways, genes, compounds, enzymes, diseases, drugs. Seven operations: info, list, find, get, conv, link, ddi. ID conversion (NCBI, UniProt, PubChem). For Python workflows with multiple databases, prefer bioservices."
license: Non-academic use of KEGG requires a commercial license
---

# KEGG Database — Biological Pathway & Molecular Network Queries

## Overview

KEGG (Kyoto Encyclopedia of Genes and Genomes) is a comprehensive bioinformatics resource for biological pathway analysis, molecular interaction networks, and cross-database ID conversion. Access is via a direct REST API with no authentication — all operations use simple HTTP GET requests returning tab-delimited text.

## When to Use

- Mapping genes to biological pathways (e.g., "which pathways involve TP53?")
- Retrieving metabolic pathway details, gene lists, or compound structures
- Converting identifiers between KEGG, NCBI Gene, UniProt, and PubChem
- Checking drug-drug interactions from KEGG's pharmacological database
- Building pathway enrichment context (all genes per pathway for an organism)
- Cross-referencing compounds, reactions, enzymes, and pathways
- For **Python-native multi-database queries** (KEGG + UniProt + Ensembl in one script), prefer `bioservices` instead
- For **pathway visualization**, use KEGG Mapper (https://www.kegg.jp/kegg/mapper/) directly

## Prerequisites

```bash
pip install requests
```

**API constraints**:
- **Academic use only** — commercial use requires a separate KEGG license
- **Max 10 entries** per `get`/`list`/`conv`/`link`/`ddi` call (image/kgml/json: 1 entry only)
- **No explicit rate limit**, but add `time.sleep(0.5)` between batch requests to avoid server-side throttling
- Base URL: `https://rest.kegg.jp/`

## Quick Start

```python
import requests
import time

BASE = "https://rest.kegg.jp"

def kegg_get(operation, *args):
    """Generic KEGG REST API caller."""
    url = f"{BASE}/{operation}/{'/'.join(args)}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

# Find pathways linked to human gene TP53
pathways = kegg_get("link", "pathway", "hsa:7157")
print(pathways[:200])
# hsa:7157	path:hsa04010
# hsa:7157	path:hsa04110
# ...

# Get pathway details
detail = kegg_get("get", "hsa04110")
print(detail[:300])
```

## Core API

### 1. Database Information — `kegg_info`

Retrieve metadata and statistics about KEGG databases.

```python
import requests

BASE = "https://rest.kegg.jp"

# Database-level info
info = requests.get(f"{BASE}/info/pathway").text
print(info[:200])
# pathway          Pathway
#                  Release 112.0, Dec 2025
#                  Kanehisa Laboratories
#                  ...

# Organism-level info
hsa_info = requests.get(f"{BASE}/info/hsa").text
print(hsa_info[:200])
```

**Common databases**: `kegg`, `pathway`, `module`, `brite`, `genes`, `genome`, `compound`, `glycan`, `reaction`, `enzyme`, `disease`, `drug`

### 2. Listing Entries — `kegg_list`

List entry identifiers and names from any KEGG database.

```python
import requests

BASE = "https://rest.kegg.jp"

# All human pathways
hsa_pathways = requests.get(f"{BASE}/list/pathway/hsa").text
for line in hsa_pathways.strip().split("\n")[:5]:
    pathway_id, name = line.split("\t")
    print(f"{pathway_id}: {name}")
# path:hsa00010: Glycolysis / Gluconeogenesis - Homo sapiens (human)
# ...

# Specific entries (max 10, joined with +)
genes = requests.get(f"{BASE}/list/hsa:10458+hsa:10459").text
print(genes)
```

**Common organism codes**: `hsa` (human), `mmu` (mouse), `dme` (fruit fly), `sce` (yeast), `eco` (E. coli)

### 3. Keyword Search — `kegg_find`

Search databases by keywords or molecular properties.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Keyword search in genes
results = requests.get(f"{BASE}/find/genes/p53").text
print(f"Found {len(results.strip().split(chr(10)))} entries")
time.sleep(0.5)

# Chemical formula search (exact match)
compounds = requests.get(f"{BASE}/find/compound/C7H10N4O2/formula").text
print(compounds[:200])
time.sleep(0.5)

# Molecular weight range search
drugs = requests.get(f"{BASE}/find/drug/300-310/exact_mass").text
print(drugs[:200])
```

**Search options**: append `/formula` (exact match), `/exact_mass` (range), `/mol_weight` (range) to compound/drug queries.

### 4. Entry Retrieval — `kegg_get`

Retrieve complete database entries or specific data formats.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Full pathway entry (text format)
pathway = requests.get(f"{BASE}/get/hsa00010").text
print(pathway[:500])
time.sleep(0.5)

# Multiple entries (max 10, joined with +)
genes = requests.get(f"{BASE}/get/hsa:10458+hsa:10459").text

# Protein sequence (FASTA)
fasta = requests.get(f"{BASE}/get/hsa:10458/aaseq").text
print(fasta[:200])
time.sleep(0.5)

# Compound structure (MOL format)
mol = requests.get(f"{BASE}/get/cpd:C00002/mol").text  # ATP

# Pathway image (PNG, single entry only)
img_resp = requests.get(f"{BASE}/get/hsa05130/image")
with open("pathway.png", "wb") as f:
    f.write(img_resp.content)
print(f"Saved pathway image: {len(img_resp.content)} bytes")
```

**Output formats**: `aaseq` (protein FASTA), `ntseq` (nucleotide FASTA), `mol` (MOL), `kcf` (KCF), `image` (PNG), `kgml` (XML), `json` (pathway JSON). Image/KGML/JSON accept **one entry only**.

### 5. ID Conversion — `kegg_conv`

Convert identifiers between KEGG and external databases.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# KEGG gene → NCBI Gene ID (specific gene)
ncbi = requests.get(f"{BASE}/conv/ncbi-geneid/hsa:10458").text
print(ncbi.strip())
# hsa:10458	ncbi-geneid:10458
time.sleep(0.5)

# KEGG gene → UniProt
uniprot = requests.get(f"{BASE}/conv/uniprot/hsa:10458").text
print(uniprot.strip())
time.sleep(0.5)

# Bulk conversion: all human genes → NCBI Gene IDs
all_conv = requests.get(f"{BASE}/conv/ncbi-geneid/hsa").text
lines = all_conv.strip().split("\n")
print(f"Total conversions: {len(lines)}")

# Reverse: NCBI Gene ID → KEGG
reverse = requests.get(f"{BASE}/conv/hsa/ncbi-geneid:7157").text
print(reverse.strip())  # TP53
```

**Supported external databases**: `ncbi-geneid`, `ncbi-proteinid`, `uniprot`, `pubchem`, `chebi`

### 6. Cross-Referencing — `kegg_link`

Find related entries within and between KEGG databases.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Genes in glycolysis pathway
genes = requests.get(f"{BASE}/link/genes/hsa00010").text
gene_list = [line.split("\t")[1] for line in genes.strip().split("\n") if line]
print(f"Glycolysis genes: {len(gene_list)}")
time.sleep(0.5)

# Pathways containing a specific gene
pathways = requests.get(f"{BASE}/link/pathway/hsa:7157").text  # TP53
print(pathways[:300])
time.sleep(0.5)

# Compounds in a pathway
compounds = requests.get(f"{BASE}/link/compound/hsa00010").text
print(f"Compounds in glycolysis: {len(compounds.strip().split(chr(10)))}")

# Map genes to KO (orthology) groups
ko = requests.get(f"{BASE}/link/ko/hsa:10458").text
print(ko.strip())
```

**Common links**: genes ↔ pathway, pathway ↔ compound, pathway ↔ enzyme, genes ↔ ko (orthology)

### 7. Drug-Drug Interactions — `kegg_ddi`

Check pharmacological interactions between drugs.

```python
import requests

BASE = "https://rest.kegg.jp"

# Single drug — all known interactions
interactions = requests.get(f"{BASE}/ddi/D00001").text
print(f"Interactions: {len(interactions.strip().split(chr(10)))}")

# Pairwise check (max 10 drugs, joined with +)
pair = requests.get(f"{BASE}/ddi/D00001+D00002+D00003").text
print(pair[:300])
```

## Key Concepts

### Identifier Formats

| Type | Format | Example |
|------|--------|---------|
| Reference pathway | `map#####` | `map00010` (Glycolysis, generic) |
| Organism pathway | `{org}#####` | `hsa00010` (Glycolysis, human) |
| Gene | `{org}:{number}` | `hsa:7157` (TP53) |
| Compound | `cpd:C#####` | `cpd:C00002` (ATP) |
| Drug | `dr:D#####` | `dr:D00001` |
| Enzyme | `ec:{EC_number}` | `ec:1.1.1.1` |
| KO (orthology) | `ko:K#####` | `ko:K00001` |

### Pathway Categories

KEGG organizes pathways into seven major categories:

1. **Metabolism** — `map001xx` (Glycolysis, TCA cycle, amino acid metabolism)
2. **Genetic Information Processing** — `map030xx` (Ribosome, Spliceosome, DNA repair)
3. **Environmental Information Processing** — `map040xx` (MAPK signaling, ABC transporters)
4. **Cellular Processes** — `map041xx` (Autophagy, Apoptosis, Cell cycle)
5. **Organismal Systems** — `map046xx` (Immune, Endocrine, Nervous)
6. **Human Diseases** — `map052xx` (Cancer, Neurodegenerative, Infectious)
7. **Drug Development** — Chronological and target-based classifications

## Common Workflows

### Workflow: Gene to Pathway Mapping

Find all pathways associated with a gene of interest.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Step 1: Find gene by keyword
results = requests.get(f"{BASE}/find/genes/BRCA1+homo+sapiens").text
print("Gene search results:")
for line in results.strip().split("\n")[:5]:
    print(f"  {line}")
time.sleep(0.5)

# Step 2: Get pathways linked to BRCA1
pathways = requests.get(f"{BASE}/link/pathway/hsa:672").text
pathway_ids = [line.split("\t")[1].replace("path:", "") for line in pathways.strip().split("\n") if line]
print(f"\nBRCA1 is in {len(pathway_ids)} pathways:")
time.sleep(0.5)

# Step 3: Get pathway names
for pid in pathway_ids[:5]:
    info = requests.get(f"{BASE}/get/{pid}").text
    # Extract NAME field
    for line in info.split("\n"):
        if line.startswith("NAME"):
            print(f"  {pid}: {line.replace('NAME', '').strip()}")
            break
    time.sleep(0.5)
```

### Workflow: Pathway Enrichment Context

Build a gene-set collection for all pathways of an organism.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Step 1: List all human pathways
pathways_text = requests.get(f"{BASE}/list/pathway/hsa").text
pathways = {}
for line in pathways_text.strip().split("\n"):
    pid, name = line.split("\t", 1)
    pathways[pid.replace("path:", "")] = name
print(f"Total human pathways: {len(pathways)}")
time.sleep(0.5)

# Step 2: Get genes for each pathway (sample first 3 for demo)
gene_sets = {}
for pid in list(pathways.keys())[:3]:
    genes_text = requests.get(f"{BASE}/link/genes/{pid}").text
    gene_ids = [line.split("\t")[1] for line in genes_text.strip().split("\n") if line]
    gene_sets[pid] = gene_ids
    print(f"  {pid}: {len(gene_ids)} genes")
    time.sleep(0.5)

# Step 3: Convert to NCBI Gene IDs for enrichment tools
# (use kegg_conv for bulk conversion)
```

### Workflow: Compound-Pathway-Reaction Analysis

Trace a compound through metabolic reactions and pathways.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Step 1: Search for compound
results = requests.get(f"{BASE}/find/compound/glucose").text
print("Compound search:")
for line in results.strip().split("\n")[:3]:
    print(f"  {line}")
time.sleep(0.5)

# Step 2: Find reactions involving glucose (C00031)
reactions = requests.get(f"{BASE}/link/reaction/cpd:C00031").text
rxn_ids = [line.split("\t")[1] for line in reactions.strip().split("\n") if line]
print(f"\nReactions involving glucose: {len(rxn_ids)}")
time.sleep(0.5)

# Step 3: Find pathways for a specific reaction
pathways = requests.get(f"{BASE}/link/pathway/rn:R00299").text
print(f"\nPathways for R00299:")
print(pathways[:300])
time.sleep(0.5)

# Step 4: Get pathway detail
detail = requests.get(f"{BASE}/get/map00010").text
print(f"\nGlycolysis pathway detail (first 500 chars):")
print(detail[:500])
```

### Workflow: Cross-Database ID Integration

Map KEGG identifiers to UniProt, NCBI, and PubChem for multi-database workflows.

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Step 1: Convert gene to multiple external IDs
gene = "hsa:7157"  # TP53

uniprot = requests.get(f"{BASE}/conv/uniprot/{gene}").text.strip()
print(f"UniProt: {uniprot}")
time.sleep(0.5)

ncbi = requests.get(f"{BASE}/conv/ncbi-geneid/{gene}").text.strip()
print(f"NCBI Gene: {ncbi}")
time.sleep(0.5)

# Step 2: Get protein sequence from KEGG
fasta = requests.get(f"{BASE}/get/{gene}/aaseq").text
print(f"\nProtein sequence (first 200 chars):\n{fasta[:200]}")
time.sleep(0.5)

# Step 3: Convert compounds to PubChem CIDs
cpd_conv = requests.get(f"{BASE}/conv/pubchem/cpd:C00002").text.strip()  # ATP
print(f"\nATP PubChem: {cpd_conv}")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Options | Effect |
|-----------|-------------------|---------|---------|--------|
| `organism` | `list`, `link`, `conv` | None | 3-4 letter code | Filter by organism (e.g., `hsa`, `mmu`) |
| `option` | `find` | None | `formula`, `exact_mass`, `mol_weight` | Search mode for compounds/drugs |
| `format` | `get` | text | `aaseq`, `ntseq`, `mol`, `kcf`, `image`, `kgml`, `json` | Output format |
| `+` separator | `get`, `list`, `ddi` | — | Max 10 entries | Batch query (join IDs with `+`) |
| `target_db` | `conv` | — | `ncbi-geneid`, `uniprot`, `pubchem`, `chebi` | External database for ID conversion |
| `target_db` | `link` | — | `pathway`, `genes`, `compound`, `ko`, `enzyme` | Related KEGG database |

## Best Practices

1. **Add delays between batch requests**: No explicit rate limit, but `time.sleep(0.5)` between requests prevents throttling and is courteous to the shared academic resource.

2. **Anti-pattern — fetching all entries without filtering**: Use `kegg_list` to enumerate IDs first, then `kegg_get` for specific entries. Avoid downloading entire databases when you need a subset.

3. **Parse tab-delimited output consistently**: All KEGG responses use `\t` as field separator and `\n` as record separator. Always `.strip()` before splitting.

4. **Respect the 10-entry batch limit**: `kegg_get`, `kegg_list`, `kegg_conv`, `kegg_link`, `kegg_ddi` accept max 10 entries (joined with `+`). Image/KGML/JSON formats accept only 1.

5. **Use organism-specific pathway IDs**: `hsa00010` (human glycolysis) returns organism-specific gene mappings; `map00010` (reference) returns generic entries. Always prefer organism-specific when analyzing a known organism.

6. **Cache frequently-used conversions**: Full organism ID conversions (`kegg_conv('ncbi-geneid', 'hsa')`) return large results. Cache locally rather than repeating.

## Common Recipes

### Recipe: Parse KEGG Flat-File Entry

```python
def parse_kegg_entry(text):
    """Parse a KEGG flat-file entry into a dictionary."""
    entry = {}
    current_key = None
    for line in text.split("\n"):
        if line.startswith("///"):
            break
        if line[:12].strip():  # New field
            current_key = line[:12].strip()
            entry[current_key] = line[12:].strip()
        elif current_key:  # Continuation
            entry[current_key] += "\n" + line[12:].strip()
    return entry

import requests
pathway = requests.get("https://rest.kegg.jp/get/hsa00010").text
parsed = parse_kegg_entry(pathway)
print(f"Name: {parsed.get('NAME', 'N/A')}")
print(f"Description: {parsed.get('DESCRIPTION', 'N/A')[:200]}")
```

### Recipe: Organism Comparison

```python
import requests
import time

BASE = "https://rest.kegg.jp"

organisms = {"hsa": "Human", "mmu": "Mouse", "sce": "Yeast"}
pathway = "00010"  # Glycolysis

for org, name in organisms.items():
    genes = requests.get(f"{BASE}/link/genes/{org}{pathway}").text
    count = len([l for l in genes.strip().split("\n") if l])
    print(f"{name} ({org}): {count} genes in Glycolysis")
    time.sleep(0.5)
# Human (hsa): 68 genes in Glycolysis
# Mouse (mmu): 67 genes in Glycolysis
# Yeast (sce): 31 genes in Glycolysis
```

### Recipe: Build Gene-to-Pathway Mapping Table

```python
import requests
import time

BASE = "https://rest.kegg.jp"

# Get all human gene-pathway links
links = requests.get(f"{BASE}/link/pathway/hsa").text
gene_pathways = {}
for line in links.strip().split("\n"):
    if not line:
        continue
    gene, pathway = line.split("\t")
    gene_pathways.setdefault(gene, []).append(pathway.replace("path:", ""))

print(f"Genes with pathway annotations: {len(gene_pathways)}")
# Show top genes by pathway count
top = sorted(gene_pathways.items(), key=lambda x: -len(x[1]))[:5]
for gene, paths in top:
    print(f"  {gene}: {len(paths)} pathways")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `404 Not Found` | Entry or database doesn't exist | Verify ID format and organism code; use `kegg_list` to check valid IDs |
| `400 Bad Request` | Malformed API URL | Check URL path: `/{operation}/{arg1}/{arg2}`; no query params |
| Empty response | Search term too specific or no matches | Broaden keywords; try partial matches; check organism code |
| Image/KGML returns error | Batch query with image/kgml/json format | These formats accept **one entry only** — remove `+` joins |
| `403 Forbidden` | Server-side rate limiting | Add `time.sleep(1)` between requests; reduce batch frequency |
| Wrong gene IDs returned | Using reference pathway (`map`) instead of organism-specific | Use organism prefix: `hsa00010` not `map00010` for gene links |
| ID conversion returns empty | External DB doesn't cover that entry | Not all KEGG entries have UniProt/NCBI mappings; check with `kegg_list` first |
| Response encoding issues | Non-ASCII characters in compound names | Use `resp.encoding = 'utf-8'` or `resp.text` (requests auto-detects) |

## Related Skills

- **gget-genomic-databases** — unified Python interface to Ensembl, NCBI, UniProt; use for gene-level queries when KEGG pathway context isn't needed
- **biopython-molecular-biology** — BioPython's `Bio.KEGG` module provides an alternative Python API for KEGG parsing
- **pubchem-compound-search** — for compound property lookups beyond KEGG's structural data; use `kegg_conv('pubchem', ...)` to bridge IDs

## References

- [KEGG REST API documentation](https://www.kegg.jp/kegg/rest/keggapi.html) — official API specification
- [KEGG website](https://www.kegg.jp/) — pathway browser, KEGG Mapper, BlastKOALA
- [KEGG organism codes](https://www.kegg.jp/kegg/catalog/org_list.html) — full list of 3-4 letter organism codes
- Kanehisa, M. et al. (2023) "KEGG for taxonomy-based analysis of pathways and genomes" *Nucleic Acids Research* 51:D483-D489
