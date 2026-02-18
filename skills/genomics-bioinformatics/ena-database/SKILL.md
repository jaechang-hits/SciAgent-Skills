---
name: ena-database
description: "European Nucleotide Archive (ENA) REST API access for genomic sequences, raw reads, assemblies, and annotations. Portal API search with query syntax, Browser API retrieval (XML/FASTA/EMBL), file reports for FASTQ/BAM download URLs, taxonomy queries, cross-references. For multi-database Python queries prefer bioservices; for NCBI-specific queries use pubmed-database or Biopython Entrez."
license: Unknown
---

# ENA Database — European Nucleotide Archive Programmatic Access

## Overview

The European Nucleotide Archive (ENA) is EMBL-EBI's comprehensive nucleotide sequence database, encompassing raw sequencing reads, genome assemblies, annotated sequences, and associated metadata. It mirrors and extends INSDC data (GenBank, DDBJ). All access is via REST APIs with no authentication required.

## When to Use

- Searching for sequencing studies, samples, or experiments by organism, project, or keyword
- Downloading raw FASTQ/BAM files for reanalysis of public sequencing datasets
- Retrieving genome assemblies with quality statistics (N50, contig count, genome size)
- Fetching nucleotide sequences in FASTA or EMBL flat-file format by accession
- Exploring taxonomic lineage and finding organisms by partial name
- Cross-referencing ENA records with external databases (ArrayExpress, UniProt, PDB)
- Building bulk download lists for large-scale sequencing projects
- For **multi-database Python queries** (ENA + UniProt + KEGG), prefer `bioservices` instead
- For **NCBI-specific queries** (PubMed literature, GenBank records), use `pubmed-database` or Biopython Entrez

## Prerequisites

```bash
pip install requests
```

**API constraints**:
- **Rate limit**: 50 requests per second across all ENA APIs
- **No authentication** required
- **Large result sets**: use pagination (`limit` + `offset`) or streaming (`limit=0` for TSV download)
- Portal API base: `https://www.ebi.ac.uk/ena/portal/api`
- Browser API base: `https://www.ebi.ac.uk/ena/browser/api`
- Taxonomy API base: `https://www.ebi.ac.uk/ena/taxonomy/rest`
- Cross-ref API base: `https://www.ebi.ac.uk/ena/xref/rest`

## Quick Start

```python
import requests
import time

BASE_PORTAL = "https://www.ebi.ac.uk/ena/portal/api"
BASE_BROWSER = "https://www.ebi.ac.uk/ena/browser/api"
BASE_TAXONOMY = "https://www.ebi.ac.uk/ena/taxonomy/rest"
BASE_XREF = "https://www.ebi.ac.uk/ena/xref/rest"

def ena_query(endpoint, params=None, base=BASE_PORTAL):
    """Reusable ENA API caller with rate-limit compliance."""
    resp = requests.get(f"{base}/{endpoint}", params=params)
    resp.raise_for_status()
    time.sleep(0.02)  # 50 req/sec limit
    return resp

# Search for human RNA-seq studies
resp = ena_query("search", params={
    "result": "study",
    "query": 'tax_tree(9606) AND library_strategy="RNA-Seq"',
    "fields": "study_accession,study_title",
    "format": "json",
    "limit": 3,
})
studies = resp.json()
for s in studies:
    print(f"{s['study_accession']}: {s['study_title'][:60]}")
# PRJEB12345: Transcriptome analysis of human liver tissue...
```

## Core API

### Module 1: Portal API Search

The Portal API provides advanced metadata search across all ENA data types with boolean query syntax, field selection, and pagination.

```python
# Search read runs for a specific study
resp = ena_query("search", params={
    "result": "read_run",
    "query": 'study_accession="PRJEB1787"',
    "fields": "run_accession,sample_accession,instrument_model,read_count,base_count",
    "format": "json",
    "limit": 5,
})
runs = resp.json()
for r in runs:
    print(f"{r['run_accession']} — {r.get('instrument_model', 'N/A')}, "
          f"{int(r.get('read_count', 0)):,} reads")
# ERR123456 — Illumina HiSeq 2000, 45,231,890 reads

# Count total results without fetching data
count_resp = ena_query("count", params={
    "result": "read_run",
    "query": 'study_accession="PRJEB1787"',
})
print(f"Total runs: {count_resp.text.strip()}")
# Total runs: 142
```

### Module 2: Browser API Retrieval

Fetch individual records by accession in multiple formats: XML, FASTA, EMBL flat-file, or plain text.

```python
# Retrieve XML metadata for a study
resp = ena_query("xml/PRJEB1787", base=BASE_BROWSER)
print(resp.text[:300])
# <?xml version="1.0" encoding="UTF-8"?><PROJECT_SET>...

# Retrieve FASTA sequence for a coding sequence
resp = ena_query("fasta/M10051.1", base=BASE_BROWSER)
print(resp.text[:200])
# >ENA|M10051|M10051.1 Human insulin mRNA, complete cds.
# AGCCCTCCAGGACAGGCTGCAT...

# Retrieve EMBL flat-file format
resp = ena_query("embl/M10051.1", base=BASE_BROWSER)
print(resp.text[:300])
# ID   M10051; SV 1; linear; mRNA; STD; HUM; 786 BP.
# ...
```

### Module 3: File Reports and Downloads

Get download URLs for FASTQ, submitted, and analysis files. File reports return FTP and Aspera paths.

```python
# Get FASTQ file URLs for specific runs
resp = ena_query("filereport", params={
    "accession": "ERR000589",
    "result": "read_run",
    "fields": "run_accession,fastq_ftp,fastq_bytes,fastq_md5",
    "format": "json",
})
files = resp.json()
for f in files:
    ftp_urls = f.get("fastq_ftp", "").split(";")
    sizes = f.get("fastq_bytes", "").split(";")
    for url, size in zip(ftp_urls, sizes):
        if url:
            print(f"ftp://{url}  ({int(size)/1e6:.1f} MB)")
# ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR000/ERR000589/ERR000589_1.fastq.gz  (234.5 MB)
# ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR000/ERR000589/ERR000589_2.fastq.gz  (241.2 MB)
```

### Module 4: Taxonomy Queries

Look up organisms by taxonomy ID, scientific name, or partial name match.

```python
# Lookup by taxonomy ID
resp = ena_query("tax-id/9606", base=BASE_TAXONOMY)
tax = resp.json()
print(f"{tax['scientificName']} (taxId: {tax['taxId']}, rank: {tax['rank']})")
# Homo sapiens (taxId: 9606, rank: species)
print(f"Lineage: {tax['lineage'][:80]}...")

# Search by scientific name
resp = ena_query("scientific-name/Arabidopsis thaliana", base=BASE_TAXONOMY)
result = resp.json()
print(f"Tax ID: {result['taxId']}, Common: {result.get('commonName', 'N/A')}")
# Tax ID: 3702, Common: thale cress

# Suggest organisms by partial name
resp = ena_query("suggest-for-search/salmo", base=BASE_TAXONOMY)
suggestions = resp.json()
for s in suggestions[:3]:
    print(f"  {s['scientificName']} (taxId: {s['taxId']})")
# Salmo salar (taxId: 8030)
# Salmo trutta (taxId: 8032)
# Salmonella enterica (taxId: 28901)
```

### Module 5: Cross-Reference Service

Find links between ENA records and external databases (ArrayExpress, UniProt, PDB, etc.).

```python
# Find cross-references for an ENA accession
resp = ena_query("json/search", base=BASE_XREF, params={
    "accession": "M10051",
})
xrefs = resp.json()
for x in xrefs[:5]:
    print(f"  {x['Source']} → {x['Source Primary Accession']} "
          f"({x.get('Source Description', '')[:50]})")
# UniProt → P01308 (Insulin precursor)
# PDB → 1A7F (Crystal structure of human insulin)

# Search cross-references by external database
resp = ena_query("json/search", base=BASE_XREF, params={
    "source": "UniProt",
    "accession": "P01308",
})
xrefs = resp.json()
for x in xrefs[:3]:
    print(f"  ENA: {x['Target Primary Accession']} — {x.get('Target Description', '')[:60]}")
```

### Module 6: CRAM Reference Registry

Retrieve reference sequences used in CRAM files by MD5 or SHA1 checksum. Essential for CRAM decompression.

```python
# Look up reference by MD5 checksum
md5 = "aef131c3b4b05d8e2b3f907faba5af9b"  # example
try:
    resp = ena_query(
        f"cram/md5/{md5}",
        base="https://www.ebi.ac.uk/ena/cram"
    )
    print(f"Reference found: {len(resp.content)} bytes")
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("Reference not found — check MD5 checksum")
    else:
        raise
```

## Key Concepts

### ENA Data Hierarchy

| Level | Accession Prefix | Description | Contains |
|-------|-----------------|-------------|----------|
| Study | PRJEB/ERP | Research project | Samples, Experiments |
| Sample | ERS/SAMEA | Biological sample | Metadata, taxonomy |
| Experiment | ERX | Library/sequencing setup | Runs |
| Run | ERR | Sequencing run | Raw read files (FASTQ) |
| Analysis | ERZ | Derived analysis | Assemblies, alignments |
| Assembly | GCA | Genome assembly | Contigs, scaffolds |
| Sequence | Accession.version | Annotated sequence | Features, coding seqs |

### Query Syntax Operators

| Operator | Example | Description |
|----------|---------|-------------|
| Equality | `instrument_model="Illumina NovaSeq 6000"` | Exact match |
| Wildcard | `study_title="*melanoma*"` | Partial match |
| Range | `base_count>=1000000` | Numeric comparison |
| Taxonomy tree | `tax_tree(9606)` | Taxon and all descendants |
| Exact taxon | `tax_eq(9606)` | Exact taxon only |
| Date range | `first_public>=2023-01-01` | Date filtering |
| Boolean | `AND`, `OR`, `NOT` | Combine conditions |
| Grouping | `(A OR B) AND C` | Parenthetical grouping |

### Result Types

| Result Type | Description | Key Fields |
|------------|-------------|------------|
| `study` | Research projects | study_accession, study_title, center_name |
| `sample` | Biological samples | sample_accession, tax_id, scientific_name |
| `read_run` | Sequencing runs | run_accession, read_count, base_count, fastq_ftp |
| `read_experiment` | Experiments | experiment_accession, library_strategy, instrument_model |
| `analysis` | Derived analyses | analysis_accession, analysis_type |
| `assembly` | Genome assemblies | assembly_accession, assembly_level, genome_representation |
| `sequence` | Annotated sequences | accession, sequence_length, mol_type |
| `wgs_set` | WGS scaffold sets | set_accession, set_size |
| `tsa_set` | Transcriptome assemblies | set_accession, set_size |
| `coding` | Coding sequences | accession, gene, product |
| `noncoding` | Non-coding features | accession, description |
| `taxon` | Taxonomy entries | tax_id, scientific_name, lineage |

### Discoverable Fields

Use the `returnFields` endpoint to discover available fields for any result type:

```python
resp = ena_query("returnFields", params={"result": "read_run"})
fields = resp.text.strip().split("\n")
print(f"Available fields for read_run: {len(fields)}")
print(fields[:10])
# ['accession', 'altitude', 'assembly_quality', 'assembly_software', ...]
```

## Common Workflows

### Workflow 1: Study Exploration Pipeline

Search for a study, list its samples, then retrieve run metadata.

```python
import json

# Step 1: Find studies by keyword
resp = ena_query("search", params={
    "result": "study",
    "query": 'study_title="*SARS-CoV-2*" AND first_public>=2023-01-01',
    "fields": "study_accession,study_title,center_name",
    "format": "json",
    "limit": 3,
})
studies = resp.json()
study_acc = studies[0]["study_accession"]
print(f"Selected: {study_acc} — {studies[0]['study_title'][:60]}")

# Step 2: List samples in the study
resp = ena_query("search", params={
    "result": "sample",
    "query": f'study_accession="{study_acc}"',
    "fields": "sample_accession,scientific_name,collection_date",
    "format": "json",
    "limit": 5,
})
samples = resp.json()
print(f"Found {len(samples)} samples (showing first 5)")
for s in samples:
    print(f"  {s['sample_accession']} — {s.get('scientific_name', 'N/A')}")

# Step 3: Get run metadata for each sample
for s in samples[:2]:
    resp = ena_query("search", params={
        "result": "read_run",
        "query": f'sample_accession="{s["sample_accession"]}"',
        "fields": "run_accession,instrument_model,read_count,library_strategy",
        "format": "json",
    })
    runs = resp.json()
    for r in runs:
        print(f"  {r['run_accession']}: {r.get('library_strategy','N/A')}, "
              f"{int(r.get('read_count',0)):,} reads")
    time.sleep(0.02)
```

### Workflow 2: Bulk FASTQ Download URL Collection

Search for runs matching criteria and collect download URLs.

```python
# Step 1: Search for Illumina RNA-Seq runs from a specific organism
resp = ena_query("search", params={
    "result": "read_run",
    "query": ('tax_tree(10090) AND library_strategy="RNA-Seq" '
              'AND instrument_platform="ILLUMINA" AND read_count>=10000000'),
    "fields": "run_accession,study_accession,read_count",
    "format": "json",
    "limit": 10,
})
runs = resp.json()
print(f"Found {len(runs)} runs meeting criteria")

# Step 2: Get file reports with download URLs
download_list = []
for run in runs[:5]:
    acc = run["run_accession"]
    resp = ena_query("filereport", params={
        "accession": acc,
        "result": "read_run",
        "fields": "run_accession,fastq_ftp,fastq_bytes,fastq_md5",
        "format": "json",
    })
    for f in resp.json():
        urls = f.get("fastq_ftp", "").split(";")
        md5s = f.get("fastq_md5", "").split(";")
        for url, md5 in zip(urls, md5s):
            if url:
                download_list.append({"url": f"ftp://{url}", "md5": md5, "run": acc})
    time.sleep(0.02)

print(f"\nDownload list: {len(download_list)} files")
for d in download_list[:4]:
    print(f"  {d['run']}: {d['url'].split('/')[-1]}")
```

### Workflow 3: Taxonomic Assembly Exploration

Find organisms, search their assemblies, and check quality statistics.

```python
# Step 1: Find organism by partial name
resp = ena_query("suggest-for-search/drosophila", base=BASE_TAXONOMY)
taxa = resp.json()
target_tax = None
for t in taxa[:5]:
    print(f"  {t['scientificName']} (taxId: {t['taxId']})")
    if t["scientificName"] == "Drosophila melanogaster":
        target_tax = t["taxId"]
print(f"\nSelected: taxId={target_tax}")

# Step 2: Search assemblies for this organism
resp = ena_query("search", params={
    "result": "assembly",
    "query": f'tax_eq({target_tax}) AND assembly_level="chromosome"',
    "fields": ("assembly_accession,assembly_name,assembly_level,"
               "genome_representation,n50,total_length"),
    "format": "json",
    "limit": 5,
})
assemblies = resp.json()
for a in assemblies:
    n50 = int(a.get("n50", 0))
    size = int(a.get("total_length", 0))
    print(f"  {a['assembly_accession']}: {a.get('assembly_name','N/A')}, "
          f"N50={n50:,}, Size={size/1e6:.1f} Mb")
# GCA_000001215.4: Release 6 plus ISO1 MT, N50=25,286,936, Size=143.7 Mb
```

## Key Parameters

| Endpoint | Parameter | Default | Description |
|----------|-----------|---------|-------------|
| `search` | `result` | (required) | Result type: study, sample, read_run, assembly, etc. |
| `search` | `query` | (required) | Boolean query string with field operators |
| `search` | `fields` | all | Comma-separated field names to return |
| `search` | `format` | tsv | Output format: json, tsv, xml |
| `search` | `limit` | 100000 | Max results (0 = unlimited streaming) |
| `search` | `offset` | 0 | Skip first N results (pagination) |
| `search` | `sortFields` | — | Field(s) to sort by |
| `filereport` | `accession` | (required) | Study, sample, or run accession |
| `filereport` | `result` | (required) | read_run, analysis, etc. |
| `xml/` | accession path | (required) | Any ENA accession (Browser API) |
| `fasta/` | accession path | (required) | Sequence accession (Browser API) |

## Best Practices

1. **Use `tax_tree()` over `tax_eq()`** for organism queries — it includes subspecies and strains automatically
2. **Request only needed fields** — reduces response size and server load significantly
3. **Prefer JSON format** for programmatic access; TSV for large bulk exports (lower overhead)
4. **Use `limit=0`** for streaming large result sets directly to file, avoiding memory issues
5. **Check `fastq_ftp` and `submitted_ftp`** — some runs have submitted files but no processed FASTQ
6. **Verify downloads with MD5** — file reports include `fastq_md5` for integrity checking
7. **Anti-pattern**: Do not fetch all fields then filter client-side — use query syntax server-side

## Common Recipes

### Recipe: Assembly Quality Filtering

```python
# Find high-quality chromosome-level assemblies
resp = ena_query("search", params={
    "result": "assembly",
    "query": ('tax_tree(7742) AND assembly_level="chromosome" '
              'AND genome_representation="full"'),
    "fields": "assembly_accession,scientific_name,n50,total_length,assembly_level",
    "format": "json",
    "limit": 10,
})
for a in resp.json():
    n50 = int(a.get("n50", 0))
    if n50 > 1_000_000:  # N50 > 1 Mb
        print(f"{a['assembly_accession']}: {a['scientific_name']}, N50={n50:,}")
```

### Recipe: Cross-Database Linking

```python
# Find UniProt/PDB cross-references for an ENA sequence
resp = ena_query("json/search", base=BASE_XREF, params={
    "accession": "M10051",
})
xrefs = resp.json()
by_source = {}
for x in xrefs:
    src = x.get("Source", "unknown")
    by_source.setdefault(src, []).append(x["Source Primary Accession"])
for src, accs in by_source.items():
    print(f"  {src}: {', '.join(accs[:5])}")
# UniProt: P01308
# PDB: 1A7F, 1AI0, 1BEN
```

### Recipe: Retry Session with Exponential Backoff

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def ena_session():
    """Create a requests session with retry logic for ENA APIs."""
    session = requests.Session()
    retry = Retry(
        total=3, backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

session = ena_session()
resp = session.get(f"{BASE_PORTAL}/search", params={
    "result": "study",
    "query": 'tax_tree(9606)',
    "fields": "study_accession",
    "format": "json",
    "limit": 5,
})
print(f"Status: {resp.status_code}, results: {len(resp.json())}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `400 Bad Request` on search | Invalid query syntax or unknown field name | Use `returnFields` endpoint to verify field names; check query operator syntax |
| `400` with `result` param | Invalid result type | Check result types table above; common: `read_run` not `run` |
| Empty results for known data | Wrong taxonomy operator | Use `tax_tree()` (includes descendants) not `tax_eq()` (exact only) |
| `fastq_ftp` field is empty | Submitted files not processed to FASTQ | Check `submitted_ftp` field instead; some datasets only have BAM/CRAM |
| `429 Too Many Requests` | Exceeded 50 req/sec rate limit | Add `time.sleep(0.02)` between requests; use retry session with backoff |
| Timeout on large queries | Result set too large for single request | Use `limit` + `offset` pagination, or `limit=0` with streaming to file |
| XML parsing errors | Malformed XML for some records | Use JSON format instead (`format=json`) when available |
| Wrong sequence version | Accession without version suffix | Always use versioned accessions (e.g., `M10051.1` not `M10051`) for Browser API |
| CRAM reference not found | MD5 checksum mismatch or non-INSDC reference | Verify MD5; check if reference is from a custom genome (not in registry) |

## Bundled Resources

This skill is self-contained. The original entry had a separate `references/api_reference.md` (490 lines) covering all 6 API endpoints in detail. That content has been fully consolidated inline:

- **Portal API** (search, count, returnFields, filereport) — Core API Modules 1 and 3, Key Parameters table
- **Browser API** (XML, FASTA, EMBL retrieval) — Core API Module 2
- **Taxonomy REST API** (tax-id, scientific-name, suggest-for-search) — Core API Module 4
- **Cross-Reference Service** (json/search) — Core API Module 5
- **CRAM Reference Registry** (md5/sha1 lookup) — Core API Module 6
- **Rate limiting and error handling** — Prerequisites, Troubleshooting, Recipe 3 (retry session)
- **Query syntax and result types** — Key Concepts section (3 tables)
- **Pagination and bulk download** — Key Parameters, Best Practices, Workflow 2
- **Omitted**: detailed EMBL format field-by-field breakdown (rarely needed programmatically); Aspera download command examples (tool-specific, not requests-based)

## Related Skills

- **bioservices-multi-database** — unified Python interface covering ENA via bioservices; prefer for multi-database workflows
- **pubmed-database** — PubMed literature search via NCBI E-utilities
- **pysam-genomic-files** — downstream processing of FASTQ/BAM/CRAM files retrieved from ENA
- **biopython-molecular-biology** — NCBI Entrez access and sequence parsing (GenBank/FASTA)
- **ncbi-blast (planned)** — BLAST sequence similarity search

## References

- ENA Portal API docs: https://www.ebi.ac.uk/ena/portal/api/doc
- ENA Browser API docs: https://www.ebi.ac.uk/ena/browser/api/doc
- ENA Taxonomy REST API: https://www.ebi.ac.uk/ena/taxonomy/rest/
- ENA Cross-Reference Service: https://www.ebi.ac.uk/ena/xref/rest/
- ENA data model guide: https://ena-docs.readthedocs.io/en/latest/submit/general-guide/data-model.html
- INSDC standards: https://www.insdc.org/
