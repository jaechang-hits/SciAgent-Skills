---
name: "gene-database"
description: "NCBI Gene via E-utilities: curated records across 1M+ taxa. Official symbols, aliases, RefSeq IDs, summaries, coordinates, GO, interactions. Use for gene ID resolution and cross-species function queries. For sequences use Ensembl; for expression use geo-database."
license: "CC0-1.0"
---

# NCBI Gene Database

## Overview

NCBI Gene is the authoritative curated database for gene-centric information, covering 1M+ genes across hundreds of thousands of taxa. Each gene record includes the official symbol, aliases, full name, functional summary, genomic coordinates (GRCh38/GRCh37), RefSeq accessions, GO annotations, interaction partners, and links to related databases. Access is free via E-utilities REST API (no API key required, though recommended).

## When to Use

- Resolving gene aliases and synonyms to the current official HGNC/NCBI symbol
- Fetching the NCBI Gene ID (integer) for a gene symbol for downstream API calls (e.g., dbSNP, ClinVar, GEO)
- Retrieving curated gene summaries and function descriptions programmatically
- Pulling RefSeq mRNA (NM_) and protein (NP_) accessions associated with a gene
- Querying GO functional annotations (Biological Process, Molecular Function, Cellular Component)
- Cross-species gene queries using the same Gene ID space
- For expression profiles across conditions use `geo-database`; for variant annotations use `clinvar-database` or `ensembl-database`

## Prerequisites

- **Python packages**: `requests`, `xml.etree.ElementTree` (stdlib), `pandas` (optional)
- **Data requirements**: gene symbols, NCBI Gene IDs, or tax IDs
- **Environment**: internet connection; NCBI email required (set `email` parameter)
- **Rate limits**: 3 req/s unauthenticated; 10 req/s with free NCBI API key

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def gene_search(query, retmax=5):
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "gene", "term": query,
                             "retmax": retmax, "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]

# Find human BRCA1 gene ID
ids = gene_search("BRCA1[sym] AND Homo sapiens[orgn]")
print(f"Gene IDs for BRCA1: {ids}")  # → ['672']
```

## Core API

### Query 1: Search by Symbol, Name, or Function

Use ESearch with field tags for precise queries.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Exact symbol match for human gene
r = requests.get(f"{BASE}/esearch.fcgi",
                 params={"db": "gene", "email": EMAIL, "retmode": "json",
                         "term": "TP53[sym] AND Homo sapiens[orgn] AND alive[prop]"})
ids = r.json()["esearchresult"]["idlist"]
print(f"TP53 Gene ID: {ids}")  # → ['7157']
```

```python
# Search by function keyword
r = requests.get(f"{BASE}/esearch.fcgi",
                 params={"db": "gene", "email": EMAIL, "retmode": "json",
                         "term": "CRISPR[title] AND Homo sapiens[orgn]", "retmax": 5})
ids = r.json()["esearchresult"]["idlist"]
print(f"CRISPR-related gene IDs: {ids}")
```

### Query 2: Fetch Gene Summary (JSON/ESummary)

Retrieve key metadata fields for a list of Gene IDs.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def esummary_gene(gene_ids):
    r = requests.post(f"{BASE}/esummary.fcgi",
                      data={"db": "gene", "id": ",".join(gene_ids),
                            "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    return r.json()["result"]

result = esummary_gene(["672", "675", "7157"])  # BRCA1, BRCA2, TP53

for uid in result.get("uids", []):
    g = result[uid]
    print(f"\n{g.get('name')} (ID {uid})")
    print(f"  Official symbol : {g.get('nomenclaturesymbol', g.get('name'))}")
    print(f"  Chr location    : {g.get('maplocation')}")
    print(f"  Summary (first 100): {g.get('summary', '')[:100]}...")
    print(f"  Aliases: {g.get('otheraliases', 'none')}")
```

### Query 3: Fetch Full Gene Record (XML)

Retrieve the complete gene record in XML for RefSeq accessions, GO terms, and interaction data.

```python
import requests
import xml.etree.ElementTree as ET

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def efetch_gene_xml(gene_id):
    r = requests.get(f"{BASE}/efetch.fcgi",
                     params={"db": "gene", "id": gene_id,
                             "rettype": "gene_table", "retmode": "text", "email": EMAIL})
    r.raise_for_status()
    return r.text

# Get gene table (tab-delimited overview)
table = efetch_gene_xml("672")
print(table[:500])
```

```python
# XML for RefSeq accession extraction
r = requests.get(f"{BASE}/efetch.fcgi",
                 params={"db": "gene", "id": "672",
                         "rettype": "xml", "retmode": "xml", "email": EMAIL})
root = ET.fromstring(r.text)

# Extract RefSeq mRNA accessions
for ref in root.iter("Gene-commentary"):
    acc = ref.find("Gene-commentary_accession")
    ver = ref.find("Gene-commentary_version")
    typ = ref.find("Gene-commentary_type")
    if acc is not None and acc.text and acc.text.startswith("NM_"):
        print(f"RefSeq mRNA: {acc.text}.{ver.text if ver is not None else ''}")
```

### Query 4: Batch Symbol-to-ID Mapping

Map a list of gene symbols to NCBI Gene IDs efficiently.

```python
import requests, time

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def symbols_to_ids(symbols, organism="Homo sapiens"):
    """Map gene symbols to NCBI Gene IDs. Returns dict {symbol: gene_id}."""
    mapping = {}
    for sym in symbols:
        r = requests.get(f"{BASE}/esearch.fcgi",
                         params={"db": "gene", "email": EMAIL, "retmode": "json",
                                 "term": f"{sym}[sym] AND {organism}[orgn] AND alive[prop]"})
        ids = r.json()["esearchresult"]["idlist"]
        mapping[sym] = ids[0] if ids else None
        time.sleep(0.1)
    return mapping

genes = ["EGFR", "KRAS", "BRAF", "PIK3CA", "PTEN"]
id_map = symbols_to_ids(genes)
for sym, gid in id_map.items():
    print(f"{sym:10s} → Gene ID {gid}")
```

### Query 5: GO Annotation Retrieval

Parse GO terms from the gene XML record.

```python
import requests
import xml.etree.ElementTree as ET

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

r = requests.get(f"{BASE}/efetch.fcgi",
                 params={"db": "gene", "id": "7157",
                         "rettype": "xml", "retmode": "xml", "email": EMAIL})
root = ET.fromstring(r.text)

# Extract GO annotations
go_terms = []
for ref in root.iter("Gene-commentary"):
    heading = ref.find("Gene-commentary_heading")
    label = ref.find("Gene-commentary_label")
    if heading is not None and "Gene Ontology" in heading.text:
        if label is not None:
            go_terms.append(label.text)

print(f"TP53 GO terms ({len(go_terms)} found):")
for term in go_terms[:10]:
    print(f"  {term}")
```

### Query 6: Cross-Species Gene Query

Find orthologs across species using NCBI Gene IDs.

```python
import requests, time

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def find_ortholog(human_gene_id, target_organism):
    """Find ortholog Gene ID in target species via NCBI Gene homologs."""
    r = requests.get(f"{BASE}/elink.fcgi",
                     params={"dbfrom": "gene", "db": "gene",
                             "id": human_gene_id, "linkname": "gene_gene_homolog",
                             "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    linksets = r.json().get("linksets", [])
    if not linksets:
        return []
    homolog_ids = [str(l["id"]) for l in linksets[0].get("linksetdbs", [{}])[0].get("links", [])]
    return homolog_ids[:10]

# Human TP53 (7157) homologs
homolog_ids = find_ortholog("7157", "Mus musculus")
print(f"Homolog Gene IDs for TP53: {homolog_ids}")
```

## Key Concepts

### NCBI Gene ID vs. HGNC ID vs. Ensembl ID

NCBI Gene IDs are integers assigned per gene per organism (e.g., human TP53 = 7157). These are distinct from HGNC IDs (e.g., HGNC:11998) and Ensembl IDs (ENSG00000141510). Many downstream NCBI databases (ClinVar, dbSNP, GEO) use NCBI Gene IDs internally.

### `alive[prop]` Filter

NCBI Gene records for discontinued genes have `status=discontinued`. Always add `AND alive[prop]` to symbol queries to exclude retired entries and avoid retrieving stale data.

## Common Workflows

### Workflow 1: Build a Gene Annotation Table

**Goal**: For a list of gene symbols, retrieve Gene ID, official name, chromosomal location, and description.

```python
import requests, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_gene(sym, organism="Homo sapiens"):
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "gene", "email": EMAIL, "retmode": "json",
                             "term": f"{sym}[sym] AND {organism}[orgn] AND alive[prop]"})
    ids = r.json()["esearchresult"]["idlist"]
    return ids[0] if ids else None

def batch_summary(gene_ids):
    r = requests.post(f"{BASE}/esummary.fcgi",
                      data={"db": "gene", "id": ",".join(gene_ids),
                            "retmode": "json", "email": EMAIL})
    return r.json()["result"]

symbols = ["BRCA1", "BRCA2", "TP53", "EGFR", "MYC", "KRAS", "PTEN"]

# Step 1: Symbol → Gene ID
id_map = {}
for sym in symbols:
    gid = search_gene(sym)
    id_map[sym] = gid
    time.sleep(0.12)

# Step 2: Batch summary
valid_ids = [v for v in id_map.values() if v]
result = batch_summary(valid_ids)

rows = []
sym_to_id = {v: k for k, v in id_map.items() if v}
for uid in result.get("uids", []):
    g = result[uid]
    rows.append({
        "symbol": sym_to_id.get(uid, g.get("name")),
        "gene_id": uid,
        "full_name": g.get("description"),
        "chr_location": g.get("maplocation"),
        "summary": g.get("summary", "")[:200],
    })

df = pd.DataFrame(rows)
df.to_csv("gene_annotations.csv", index=False)
print(df[["symbol", "gene_id", "full_name", "chr_location"]].to_string(index=False))
```

### Workflow 2: Find All Genes in a Pathway Keyword

**Goal**: Retrieve all human genes associated with a biological keyword from the NCBI Gene summary field.

```python
import requests, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

keyword = "DNA mismatch repair"
r = requests.get(f"{BASE}/esearch.fcgi",
                 params={"db": "gene", "email": EMAIL, "retmode": "json",
                         "retmax": 50,
                         "term": f"{keyword}[title/abstract] AND Homo sapiens[orgn] AND alive[prop]"})
ids = r.json()["esearchresult"]["idlist"]
print(f"Found {len(ids)} genes related to '{keyword}'")

# Fetch summaries
r2 = requests.post(f"{BASE}/esummary.fcgi",
                   data={"db": "gene", "id": ",".join(ids), "retmode": "json", "email": EMAIL})
result = r2.json()["result"]

rows = []
for uid in result.get("uids", []):
    g = result[uid]
    rows.append({"gene_id": uid, "symbol": g.get("name"),
                 "description": g.get("description"),
                 "location": g.get("maplocation")})

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv(f"{keyword.replace(' ', '_')}_genes.csv", index=False)
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `retmax` | ESearch | `20` | `1`–`10000` | Max records returned |
| `retmode` | ESearch/ESummary | `"xml"` | `"json"`, `"xml"` | Response format |
| `rettype` | EFetch | depends | `"xml"`, `"gene_table"`, `"text"` | Record format for full fetch |
| `[sym]` field tag | ESearch | — | gene symbol | Match exact official symbol only |
| `[orgn]` field tag | ESearch | — | organism name or tax ID | Filter by taxonomy |
| `alive[prop]` | ESearch | — | boolean flag | Exclude discontinued gene records |

## Best Practices

1. **Always add `alive[prop]`**: Discontinued gene records remain in the database. Without this filter, symbol searches may return outdated records.

2. **Use Gene IDs in pipelines**: Downstream NCBI databases (ClinVar, dbSNP, GEO) accept Gene IDs; avoid re-searching by symbol in each call.

3. **Use ESummary for metadata, EFetch for full records**: ESummary returns JSON with all common fields; EFetch XML is needed only for RefSeq accessions, GO terms, or interaction links.

4. **Register for a free API key**: Triple your rate limit (3 → 10 req/s) at https://www.ncbi.nlm.nih.gov/account/. Pass as `api_key` parameter.

5. **Batch with ESummary**: POST up to 200 Gene IDs per call to ESummary instead of querying one at a time.

## Common Recipes

### Recipe: Gene ID to RefSeq NM Accession

When to use: Get the canonical mRNA accession for a protein-coding gene.

```python
import requests, re

EMAIL = "your@email.com"
GENE_ID = "672"  # BRCA1

r = requests.get(
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
    params={"db": "gene", "id": GENE_ID, "rettype": "gene_table",
            "retmode": "text", "email": EMAIL}
)
nm_accessions = re.findall(r"NM_\d+\.\d+", r.text)
print(f"RefSeq mRNA accessions: {list(set(nm_accessions))}")
```

### Recipe: Retrieve Gene Aliases

When to use: Resolve legacy/alias symbols to the current official NCBI symbol.

```python
import requests

EMAIL = "your@email.com"

# P53 is an alias for TP53
r = requests.get(
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
    params={"db": "gene", "email": EMAIL, "retmode": "json",
            "term": "p53[sym] AND Homo sapiens[orgn] AND alive[prop]"}
)
ids = r.json()["esearchresult"]["idlist"]

r2 = requests.post("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                   data={"db": "gene", "id": ",".join(ids[:1]),
                         "retmode": "json", "email": EMAIL})
g = r2.json()["result"][ids[0]]
print(f"Official symbol : {g.get('nomenclaturesymbol', g.get('name'))}")
print(f"Other aliases   : {g.get('otheraliases')}")
print(f"Designations    : {g.get('otherdesignations', '')[:100]}")
```

### Recipe: List All Genes on a Chromosome

When to use: Get all protein-coding genes on a specific human chromosome.

```python
import requests

EMAIL = "your@email.com"

r = requests.get(
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
    params={"db": "gene", "email": EMAIL, "retmode": "json", "retmax": 5,
            "term": "17[chr] AND Homo sapiens[orgn] AND protein coding[filter] AND alive[prop]"}
)
result = r.json()["esearchresult"]
print(f"Protein-coding genes on chr17: {result['count']} total")
print(f"Sample IDs: {result['idlist']}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `idlist` for known symbol | Symbol is an alias, not the official term | Use `[gene name]` or `[title]` field tag; check aliases via ESummary |
| Wrong species returned | Missing organism filter | Add `AND Homo sapiens[orgn]` or target tax ID (`9606[taxid]`) |
| Discontinued gene returned | Missing `alive[prop]` filter | Append `AND alive[prop]` to all symbol queries |
| `HTTP 429` rate limit | Too many requests | Add `time.sleep(0.35)` between calls; use NCBI API key |
| ESummary missing `uids` key | All IDs invalid/absent | Check `id` values are valid integers, not empty strings |
| XML parse error | Malformed XML for rare genes | Wrap ET.fromstring in try/except; retry with `rettype=text` |

## Related Skills

- `geo-database` — Gene Expression Omnibus for retrieving expression data linked to genes found here
- `clinvar-database` — Clinical variant data indexed by NCBI Gene IDs
- `ensembl-database` — Complementary gene annotations with VEP and comparative genomics
- `biopython-molecular-biology` — Biopython Entrez module wraps E-utilities with typed return values

## References

- [NCBI Gene database](https://www.ncbi.nlm.nih.gov/gene/) — Official homepage and search interface
- [E-utilities documentation](https://www.ncbi.nlm.nih.gov/books/NBK25499/) — Complete API reference for ESearch, ESummary, EFetch
- [NCBI Gene field tags](https://www.ncbi.nlm.nih.gov/books/NBK3840/) — Field tag reference for constructing Entrez queries
- [NCBI API Key registration](https://www.ncbi.nlm.nih.gov/account/) — Free registration for 10 req/s rate limit
