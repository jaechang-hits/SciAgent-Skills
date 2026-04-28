---
name: uniprot-protein-database
description: "Query UniProt REST API: search by gene/protein name, fetch FASTA, map IDs (Ensembl, PDB, RefSeq), access Swiss-Prot annotations. Use bioservices for multi-DB access; alphafold-database for structures."
license: CC-BY-4.0
---

# UniProt — Protein Database

## Overview

UniProt is the most comprehensive protein sequence and functional annotation database, containing 250M+ entries. This skill covers programmatic access via the UniProt REST API for protein search, sequence retrieval, ID mapping, and annotation queries. Swiss-Prot entries are manually curated; TrEMBL entries are computationally predicted.

## When to Use

- Searching for proteins by gene name, accession, organism, or function keywords
- Retrieving protein sequences in FASTA format for downstream analysis
- Mapping identifiers between databases (UniProt ↔ Ensembl, PDB, RefSeq, KEGG)
- Accessing protein annotations: GO terms, domains, post-translational modifications
- Batch retrieving multiple protein entries for comparative analysis
- Downloading reviewed (Swiss-Prot) protein datasets for a specific organism
- For **unified access to 40+ databases**, use bioservices instead
- For **protein 3D structures**, use alphafold-database or pdb-database

## Prerequisites

```bash
pip install requests pandas
```

**API Rate Limits**: UniProt REST API has no strict rate limit but recommends adding `time.sleep(0.5)` between batch requests. For large queries (>10k results), use the streaming endpoint instead of paginated search. Maximum 100,000 IDs per ID mapping job.

## Quick Start

```python
import requests

# Search for human insulin proteins (reviewed/Swiss-Prot only)
url = "https://rest.uniprot.org/uniprotkb/search"
params = {"query": "insulin AND organism_id:9606 AND reviewed:true", "format": "tsv",
          "fields": "accession,gene_names,protein_name,length"}
response = requests.get(url, params=params)
print(response.text[:500])
# accession  gene_names  protein_name  length
# P01308     INS         Insulin       110
```

## Core API

### 1. Protein Search

Search UniProt with structured queries combining Boolean operators and field-specific filters.

```python
import requests
import time

BASE = "https://rest.uniprot.org/uniprotkb/search"

def search_uniprot(query, fields=None, format="json", size=25):
    """Search UniProt with query syntax."""
    params = {"query": query, "format": format, "size": size}
    if fields:
        params["fields"] = ",".join(fields)
    resp = requests.get(BASE, params=params)
    resp.raise_for_status()
    return resp.json() if format == "json" else resp.text

# Search by gene name
results = search_uniprot("gene:BRCA1 AND reviewed:true",
                         fields=["accession", "gene_names", "organism_name", "length"])
for entry in results["results"][:3]:
    print(f"{entry['primaryAccession']} | {entry.get('genes', [{}])[0].get('geneName', {}).get('value', 'N/A')} | {entry.get('organism', {}).get('scientificName', 'N/A')}")
```

**Query syntax reference**:
```
# Boolean operators
kinase AND organism_id:9606          # Human kinases
(diabetes OR insulin) AND reviewed:true
cancer NOT lung

# Field-specific
gene:BRCA1
accession:P12345
taxonomy_name:"Homo sapiens"
go:0005515                           # GO term: protein binding

# Range queries
length:[100 TO 500]
mass:[50000 TO 100000]

# Wildcards
gene:BRCA*
```

### 2. Protein Entry Retrieval

Retrieve individual protein entries by accession number.

```python
import requests

def get_protein(accession, format="json"):
    """Retrieve a single protein entry."""
    url = f"https://rest.uniprot.org/uniprotkb/{accession}"
    resp = requests.get(url, headers={"Accept": f"application/{format}"})
    resp.raise_for_status()
    return resp.json() if format == "json" else resp.text

# Get human insulin
entry = get_protein("P01308")
print(f"Protein: {entry['proteinDescription']['recommendedName']['fullName']['value']}")
print(f"Gene: {entry['genes'][0]['geneName']['value']}")
print(f"Length: {entry['sequence']['length']} aa")
print(f"Sequence: {entry['sequence']['value'][:50]}...")

# Get FASTA directly
fasta = requests.get("https://rest.uniprot.org/uniprotkb/P01308.fasta").text
print(fasta[:200])
```

### 3. ID Mapping

Map identifiers between UniProt and other databases.

```python
import requests
import time

def map_ids(ids, from_db, to_db):
    """Map identifiers between databases (async job)."""
    # Submit job
    resp = requests.post("https://rest.uniprot.org/idmapping/run",
                         data={"from": from_db, "to": to_db, "ids": ",".join(ids)})
    resp.raise_for_status()
    job_id = resp.json()["jobId"]

    # Poll for completion
    while True:
        status = requests.get(f"https://rest.uniprot.org/idmapping/status/{job_id}").json()
        if "results" in status or "failedIds" in status:
            break
        time.sleep(1)

    # Get results
    results = requests.get(f"https://rest.uniprot.org/idmapping/results/{job_id}").json()
    return results

# UniProt → PDB mapping
results = map_ids(["P01308", "P12345"], from_db="UniProtKB_AC-ID", to_db="PDB")
for r in results.get("results", []):
    print(f"{r['from']} → PDB: {r['to']}")

# UniProt → Ensembl mapping
results = map_ids(["P01308"], from_db="UniProtKB_AC-ID", to_db="Ensembl")
for r in results.get("results", []):
    print(f"{r['from']} → Ensembl: {r['to']}")
```

**Common database codes**: `UniProtKB_AC-ID`, `Ensembl`, `RefSeq_Protein`, `PDB`, `Gene_Name`, `GeneID`, `KEGG`

### 4. Batch Retrieval and Streaming

Retrieve large datasets efficiently.

```python
import requests
import time

def batch_retrieve(accessions, fields=None, format="tsv"):
    """Retrieve multiple proteins by accession."""
    query = " OR ".join(f"accession:{acc}" for acc in accessions)
    params = {"query": query, "format": format}
    if fields:
        params["fields"] = ",".join(fields)
    resp = requests.get("https://rest.uniprot.org/uniprotkb/search", params=params)
    resp.raise_for_status()
    return resp.text

# Batch retrieve
accessions = ["P01308", "P12345", "Q9Y6K9"]
tsv = batch_retrieve(accessions, fields=["accession", "gene_names", "protein_name", "length"])
print(tsv)

# Streaming for large queries (no pagination needed)
def stream_query(query, format="fasta"):
    """Stream large result sets."""
    url = f"https://rest.uniprot.org/uniprotkb/stream?query={query}&format={format}"
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size=8192, decode_unicode=True):
        yield chunk

# Stream all human kinases as FASTA
# for chunk in stream_query("kinase AND organism_id:9606 AND reviewed:true"):
#     print(chunk[:200])
```

### 5. Pagination and Cursor-Based Iteration

Handle large result sets with pagination using the `Link` header cursor.

```python
import requests

def paginate_search(query, fields=None, page_size=500):
    """Iterate all pages of a UniProt search using cursor pagination."""
    params = {"query": query, "format": "tsv", "size": page_size}
    if fields:
        params["fields"] = ",".join(fields)
    url = "https://rest.uniprot.org/uniprotkb/search"
    rows = []
    header = None
    while url:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        params = {}  # cursor is embedded in the next URL
        lines = resp.text.strip().split("\n")
        if header is None:
            header = lines[0]
        rows.extend(lines[1:])
        # Follow Link header for next page
        link = resp.headers.get("Link", "")
        url = link.split("<")[1].split(">")[0] if "<" in link else None
    return header, rows

header, rows = paginate_search(
    "kinase AND organism_id:9606 AND reviewed:true",
    fields=["accession", "gene_names", "length"]
)
print(f"Retrieved {len(rows)} proteins")
print(header)
print("\n".join(rows[:3]))
```

### 6. Field Selection and Annotations

Customize which data fields to retrieve.

```python
import requests
import pandas as pd
from io import StringIO

# Retrieve specific annotation fields
params = {
    "query": "gene:TP53 AND organism_id:9606 AND reviewed:true",
    "format": "tsv",
    "fields": "accession,gene_names,protein_name,go_p,go_f,go_c,cc_function,ft_domain",
}
resp = requests.get("https://rest.uniprot.org/uniprotkb/search", params=params)
df = pd.read_csv(StringIO(resp.text), sep="\t")
print(df.columns.tolist())
print(df.iloc[0])
```

**Common field groups**:
- Sequence: `accession`, `sequence`, `length`, `mass`
- Names: `gene_names`, `protein_name`, `organism_name`
- GO: `go_p` (process), `go_f` (function), `go_c` (component)
- Features: `ft_domain`, `ft_binding`, `ft_act_site`, `ft_mod_res`
- Comments: `cc_function`, `cc_interaction`, `cc_subcellular_location`

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `query` | `/search`, `/stream` | — | UniProt query syntax | Filter proteins by criteria |
| `format` | All endpoints | `json` | `json`, `tsv`, `fasta`, `xml`, `gff` | Output format |
| `fields` | `/search` | all | Comma-separated field names | Reduces response size |
| `size` | `/search` | 25 | 1–500 | Results per page |
| `from` / `to` | `/idmapping/run` | — | Database codes | ID mapping direction |
| `reviewed:true` | Query filter | — | `true`/`false` | Swiss-Prot (curated) only |
| `organism_id` | Query filter | — | NCBI taxonomy ID | Filter by species |

## Best Practices

1. **Filter `reviewed:true` for curated data**: Swiss-Prot entries are manually reviewed; TrEMBL entries are computationally predicted. Use Swiss-Prot for high-confidence annotations.

2. **Use TSV format with `fields` for tabular analysis**: Requesting only needed fields as TSV is faster and easier to parse than full JSON entries.

3. **Use streaming for large downloads**: The `/stream` endpoint returns all results without pagination, avoiding the need for multi-page iteration.

4. **Add `time.sleep(0.5)` between batch requests**: Respect API resources, especially when making many sequential requests.

5. **Cache frequently accessed entries locally**: UniProt updates monthly; cache results and re-fetch only when needed.

6. **Anti-pattern — querying without `organism_id`**: Broad queries like `gene:INS` return thousands of entries across all species. Always filter by organism for targeted results.

## Common Recipes

### Recipe: Download All Human Kinases as DataFrame

```python
import requests
import pandas as pd
from io import StringIO

url = "https://rest.uniprot.org/uniprotkb/stream"
params = {
    "query": "ec:2.7.* AND organism_id:9606 AND reviewed:true",
    "format": "tsv",
    "fields": "accession,gene_names,protein_name,length,go_f",
}
resp = requests.get(url, params=params)
df = pd.read_csv(StringIO(resp.text), sep="\t")
print(f"Human kinases (Swiss-Prot): {len(df)}")
print(df.head())
```

### Recipe: Extract GO Annotations for a Gene Set

```python
import requests
import pandas as pd
from io import StringIO

gene_list = ["BRCA1", "BRCA2", "TP53", "ATM", "CHEK2"]
query = " OR ".join(f"gene:{g}" for g in gene_list)
query += " AND organism_id:9606 AND reviewed:true"

params = {
    "query": query,
    "format": "tsv",
    "fields": "accession,gene_names,go_p,go_f,go_c",
}
resp = requests.get("https://rest.uniprot.org/uniprotkb/search", params=params)
df = pd.read_csv(StringIO(resp.text), sep="\t")
print(df[["Accession", "Gene Names", "Gene Ontology (biological process)"]].head())
```

### Recipe: Cross-Reference UniProt to PDB Structures

```python
import requests
import time

accessions = ["P53_HUMAN", "P01308", "P00533"]  # TP53, Insulin, EGFR
resp = requests.post("https://rest.uniprot.org/idmapping/run",
                     data={"from": "UniProtKB_AC-ID", "to": "PDB", "ids": ",".join(accessions)})
job_id = resp.json()["jobId"]
time.sleep(2)
results = requests.get(f"https://rest.uniprot.org/idmapping/results/{job_id}").json()
for r in results.get("results", []):
    print(f"{r['from']} → PDB: {r['to']}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `400 Bad Request` | Invalid query syntax | Check Boolean operators, field names, bracket matching; use UniProt query syntax docs |
| Too many results (slow) | No organism or review filter | Add `AND organism_id:9606 AND reviewed:true` to narrow results |
| ID mapping returns empty | Wrong database code | Verify `from`/`to` codes: use `UniProtKB_AC-ID` (not `UniProtKB` alone) |
| Pagination missing entries | Large result set | Use `/stream` endpoint instead of paginated `/search` |
| `429 Too Many Requests` | Excessive API calls | Add `time.sleep(0.5)` between requests; batch accessions in single queries |
| FASTA has no gene name | TrEMBL entry with minimal annotation | Filter `reviewed:true` for Swiss-Prot entries with full annotations |

## Related Skills

- **biopython-molecular-biology** — parse FASTA sequences returned by UniProt; run BLAST with retrieved sequences
- **alphafold-database** — retrieve predicted 3D structures using UniProt accessions
- **esm-protein-language-model** — generate embeddings from UniProt protein sequences
- **gget-genomic-databases** — alternative interface for quick gene/protein lookups across databases

## References

- [UniProt REST API documentation](https://www.uniprot.org/help/api) — official API reference
- [UniProt query syntax](https://www.uniprot.org/help/query-fields) — field-specific search operators
- [UniProt Consortium (2023)](https://doi.org/10.1093/nar/gkac1052) — "UniProt: the Universal Protein Knowledgebase in 2023" — Nucleic Acids Research
