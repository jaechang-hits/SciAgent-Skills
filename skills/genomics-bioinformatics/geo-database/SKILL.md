---
name: "geo-database"
description: "Query NCBI Gene Expression Omnibus (GEO) for gene expression datasets and sample metadata via GEOparse Python library and E-utilities. Search datasets by keyword/organism/platform, download GSE series matrices, parse GPL platform annotations, extract GSM sample metadata, and load expression matrices into pandas. For single-cell data use cellxgene-census; for programmatic multi-DB access use gget-genomic-databases."
license: "MIT"
---

# GEO Gene Expression Omnibus Database

## Overview

GEO (Gene Expression Omnibus) is NCBI's public repository for high-throughput functional genomics data, containing 200,000+ datasets (series) from microarrays, RNA-seq, ChIP-seq, methylation, and proteomics experiments. GEOparse provides a Python interface for downloading and parsing GEO records (GSE series, GPL platforms, GSM samples) while NCBI E-utilities enables programmatic search across GEO's metadata.

## When to Use

- Searching for publicly available gene expression datasets by organism, tissue, disease, or experimental condition
- Downloading and parsing a specific GEO series (GSE) with its expression matrix and sample metadata
- Extracting sample annotation tables (e.g., treatment groups, clinical covariates) for meta-analysis
- Loading microarray expression data (GPL platform-annotated probes) into a tidy DataFrame
- Retrieving all GEO experiments associated with a gene or pathway of interest
- Building automated pipelines that download and process GEO datasets for downstream analysis
- For single-cell RNA-seq data at scale, use `cellxgene-census`; for aligned reads, download FASTQ from ENA/SRA instead

## Prerequisites

- **Python packages**: `GEOparse`, `requests`, `pandas`
- **Data requirements**: GSE/GPL/GSM accession numbers, or search terms
- **Environment**: internet connection; write access to local directory for downloads
- **Rate limits**: E-utilities: 3 req/s unauthenticated, 10 req/s with API key; GEO FTP is unlimited

```bash
pip install GEOparse requests pandas
```

## Quick Start

```python
import GEOparse

# Download a GEO series (caches in current directory)
gse = GEOparse.get_GEO("GSE2553", destdir="./geo_data/")
print(f"Title: {gse.metadata['title'][0]}")
print(f"Samples: {len(gse.gsms)}")
print(f"Platform: {list(gse.gpls.keys())}")

# Sample metadata
meta = gse.phenotype_data
print(meta.head())
```

## Core API

### Query 1: Search GEO Datasets via E-utilities

Find GEO series (GSE) by keyword, organism, or dataset type.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def geo_search(query, retmax=20):
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params={"db": "gds", "term": query,
                             "retmax": retmax, "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    return r.json()["esearchresult"]

# Search for human breast cancer RNA-seq datasets
result = geo_search(
    "breast cancer[title] AND Homo sapiens[organism] AND gse[entry type]",
    retmax=10
)
print(f"Found {result['count']} matching GEO datasets")
print(f"First accessions (UIDs): {result['idlist']}")
```

```python
# Search for specific platform (e.g., Illumina HumanHT-12)
result = geo_search(
    "Illumina HumanHT-12[platform] AND Homo sapiens[organism] AND gse[entry type]",
    retmax=5
)
print(f"Illumina HumanHT-12 human datasets: {result['count']}")
```

### Query 2: Fetch Dataset Summary Metadata

Retrieve title, accession, and organism for search results.

```python
import requests

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def geo_summary(uids):
    r = requests.post(f"{BASE}/esummary.fcgi",
                      data={"db": "gds", "id": ",".join(uids),
                            "retmode": "json", "email": EMAIL})
    r.raise_for_status()
    return r.json()["result"]

# Get metadata for search results
result = geo_search_func = lambda q: requests.get(
    f"{BASE}/esearch.fcgi",
    params={"db": "gds", "term": q, "retmax": 3, "retmode": "json", "email": EMAIL}
).json()["esearchresult"]["idlist"]

uids = requests.get(
    f"{BASE}/esearch.fcgi",
    params={"db": "gds", "term": "lung cancer[title] AND gse[entry type]",
            "retmax": 3, "retmode": "json", "email": EMAIL}
).json()["esearchresult"]["idlist"]

summaries = geo_summary(uids)
for uid in summaries.get("uids", []):
    s = summaries[uid]
    print(f"\nAccession: {s.get('accession')} | {s.get('title')}")
    print(f"  Organism: {s.get('taxon')}")
    print(f"  Samples: {s.get('n_samples')}")
    print(f"  Type: {s.get('gdstype')}")
```

### Query 3: Download and Parse a GEO Series

Use GEOparse to download a full GSE record with expression matrix and sample metadata.

```python
import GEOparse

# Download GSE (auto-caches; skip download if already present)
gse = GEOparse.get_GEO("GSE2553", destdir="./geo_data/", silent=True)

# Series metadata
print(f"Title   : {gse.metadata['title'][0]}")
print(f"Summary : {gse.metadata['summary'][0][:200]}...")
print(f"Samples : {len(gse.gsms)} GSMs")
print(f"Platforms: {list(gse.gpls.keys())}")
```

```python
# Sample metadata table (phenotype data)
meta = gse.phenotype_data
print(f"Metadata columns: {list(meta.columns)}")
print(meta.head())
```

### Query 4: Extract Expression Matrix

Parse probe-level expression data and optionally merge with platform gene annotations.

```python
import GEOparse, pandas as pd

gse = GEOparse.get_GEO("GSE2553", destdir="./geo_data/", silent=True)

# Pivot to gene expression matrix (probes × samples)
gpl_id = list(gse.gpls.keys())[0]
pivot = gse.pivot_samples("VALUE", gpl_id)
print(f"Expression matrix shape: {pivot.shape}")  # (probes, samples)
print(pivot.iloc[:5, :3])
```

```python
# Annotate probes with gene symbols from the GPL platform
gpl = gse.gpls[gpl_id]
annot = gpl.table[["ID", "Gene Symbol", "Gene Title"]].copy()
annot.columns = ["ID", "gene_symbol", "gene_title"]
annot = annot.dropna(subset=["gene_symbol"])
annot = annot[annot["gene_symbol"] != ""]

expr_annotated = pivot.join(annot.set_index("ID"), how="inner")
print(f"Annotated expression matrix: {expr_annotated.shape}")
print(expr_annotated[["gene_symbol", "gene_title"]].head())
```

### Query 5: Download Individual Sample (GSM)

Retrieve expression values and metadata for a single sample.

```python
import GEOparse

gsm = GEOparse.get_GEO("GSM45553", destdir="./geo_data/", silent=True)

print(f"Title   : {gsm.metadata['title'][0]}")
print(f"Source  : {gsm.metadata.get('source_name_ch1', ['n/a'])[0]}")
print(f"Organism: {gsm.metadata.get('organism_ch1', ['n/a'])[0]}")
print(f"Data rows: {len(gsm.table)}")
print(gsm.table.head())
```

### Query 6: Direct FTP Download for Large Series

For large datasets, download the series matrix file directly from GEO FTP.

```python
import urllib.request, gzip, io, pandas as pd

# GEO series matrix file URL pattern
accession = "GSE2553"
series_num = accession[3:]  # strip "GSE"
folder = f"GSE{series_num[:-3]}nnn" if len(series_num) > 3 else f"GSE{series_num[:-2]}nn"

url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{folder}/{accession}/matrix/{accession}_series_matrix.txt.gz"

with urllib.request.urlopen(url) as resp:
    with gzip.open(resp, "rt", encoding="utf-8") as f:
        lines = f.readlines()

# Find metadata lines (start with !) and data table
meta_lines = [l for l in lines if l.startswith("!")]
data_start = next(i for i, l in enumerate(lines) if l.startswith('"ID_REF"'))
df = pd.read_csv(
    io.StringIO("".join(lines[data_start:])),
    sep="\t", index_col=0
)
print(f"Matrix shape: {df.shape}")
print(df.iloc[:3, :3])
```

## Key Concepts

### GEO Record Types

- **GSE** (Series): A complete experiment with all samples and metadata
- **GPL** (Platform): The microarray or sequencing platform definition (probe/gene mapping)
- **GSM** (Sample): A single hybridization or sequencing run
- **GDS** (Dataset): Curated, normalized subset of a series (fewer than GSE records)

### Soft vs. MiniML Format

GEOparse downloads SOFT-format files (plain text). For XML-based access, use MiniML format via E-utilities. Series Matrix files (tab-delimited) are the most compact format for expression data.

## Common Workflows

### Workflow 1: Download and Prepare Expression Data for DE Analysis

**Goal**: Download a GEO dataset, extract the expression matrix and group labels, and save for downstream differential expression analysis.

```python
import GEOparse, pandas as pd

# Download series
gse = GEOparse.get_GEO("GSE2553", destdir="./geo_data/", silent=True)

# 1. Extract expression matrix
gpl_id = list(gse.gpls.keys())[0]
expr = gse.pivot_samples("VALUE", gpl_id)

# 2. Extract sample groups from characteristics
meta = gse.phenotype_data
print("Available metadata columns:", list(meta.columns))

# 3. Annotate probes with gene symbols
gpl = gse.gpls[gpl_id]
gene_col = "Gene Symbol" if "Gene Symbol" in gpl.table.columns else gpl.table.columns[1]
annot = gpl.table[["ID", gene_col]].dropna()
annot.columns = ["probe_id", "gene_symbol"]
annot = annot[annot["gene_symbol"].str.strip() != ""]

expr_genes = expr.join(annot.set_index("probe_id")[["gene_symbol"]], how="inner")
expr_genes = expr_genes.groupby("gene_symbol").mean()  # average duplicate probes

print(f"Genes × Samples: {expr_genes.shape}")
expr_genes.to_csv("expression_matrix.csv")
meta.to_csv("sample_metadata.csv")
print("Saved: expression_matrix.csv, sample_metadata.csv")
```

### Workflow 2: Search and Build a Dataset Inventory

**Goal**: Search GEO for studies matching a topic and build a curated inventory CSV.

```python
import requests, time, pandas as pd

EMAIL = "your@email.com"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

topic = "Alzheimer disease"
r = requests.get(f"{BASE}/esearch.fcgi",
                 params={"db": "gds", "email": EMAIL, "retmode": "json", "retmax": 50,
                         "term": f"{topic}[title] AND Homo sapiens[organism] AND gse[entry type]"})
uids = r.json()["esearchresult"]["idlist"]
print(f"Found {len(uids)} GSE datasets for '{topic}'")

rows = []
for i in range(0, len(uids), 20):
    batch = uids[i:i+20]
    r2 = requests.post(f"{BASE}/esummary.fcgi",
                       data={"db": "gds", "id": ",".join(batch),
                             "retmode": "json", "email": EMAIL})
    result = r2.json()["result"]
    for uid in result.get("uids", []):
        s = result[uid]
        rows.append({
            "accession": s.get("accession"),
            "title": s.get("title"),
            "n_samples": s.get("n_samples"),
            "organism": s.get("taxon"),
            "gds_type": s.get("gdstype"),
            "pub_date": s.get("pdat"),
        })
    time.sleep(0.4)

df = pd.DataFrame(rows).sort_values("n_samples", ascending=False)
df.to_csv(f"{topic.replace(' ', '_')}_geo_datasets.csv", index=False)
print(df[["accession", "title", "n_samples"]].head(10).to_string(index=False))
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `destdir` | GEOparse.get_GEO | `"./"` | any directory path | Where to save downloaded files |
| `silent` | GEOparse.get_GEO | `False` | `True`/`False` | Suppress download progress output |
| `retmax` | ESearch | `20` | `1`–`10000` | Max dataset records returned |
| `entry type` query | ESearch | — | `"gse"`, `"gds"`, `"gpl"`, `"gsm"` | Filter by GEO record type |
| `VALUE` column | pivot_samples | — | column name in GSM table | Expression value column to pivot |
| `email` | E-utilities | required | valid email | NCBI rate-limit attribution |

## Best Practices

1. **Use `silent=True` in GEOparse**: Suppresses verbose download progress; add your own print statement to confirm download.

2. **Cache downloads**: GEOparse skips re-downloading if the `.soft.gz` file already exists in `destdir`. Set a shared `destdir` across sessions to avoid redundant downloads.

3. **Prefer Series Matrix for large datasets**: For series with 100+ samples, download the `_series_matrix.txt.gz` directly from FTP rather than parsing individual GSM soft files—it's orders of magnitude faster.

4. **Handle probe-to-gene mapping carefully**: Many probes map to multiple genes or no gene. Decide how to handle multi-gene probes (drop, split, or keep) before analysis. Use `gene_symbol.str.split(" /// ")` for Affymetrix arrays.

5. **Check platform column names**: GPL annotation table column names vary by platform (e.g., `"Gene Symbol"` vs `"GENE_SYMBOL"` vs `"gene_id"`). Always inspect `gpl.table.columns` before assuming field names.

## Common Recipes

### Recipe: Quick GSE Metadata Peek

When to use: Get series title, sample count, and platform for any GSE accession.

```python
import GEOparse

gse = GEOparse.get_GEO("GSE2553", destdir="./geo_data/", silent=True)
print(f"Title : {gse.metadata['title'][0]}")
print(f"Samples: {len(gse.gsms)}")
print(f"Platform: {list(gse.gpls.keys())}")
print(f"Summary: {gse.metadata['summary'][0][:300]}")
```

### Recipe: Extract Sample Characteristics

When to use: Parse GEO sample characteristics into a tidy DataFrame for grouping.

```python
import GEOparse, pandas as pd, re

gse = GEOparse.get_GEO("GSE2553", destdir="./geo_data/", silent=True)
meta = gse.phenotype_data

# Parse "characteristics_ch1" columns
ch_cols = [c for c in meta.columns if "characteristics" in c.lower()]
print(f"Characteristic columns: {ch_cols}")
print(meta[ch_cols].head())
```

### Recipe: List All GSMs in a Series

When to use: Enumerate sample accessions for download or metadata collection.

```python
import GEOparse

gse = GEOparse.get_GEO("GSE2553", destdir="./geo_data/", silent=True)
gsm_ids = list(gse.gsms.keys())
print(f"Total samples: {len(gsm_ids)}")
print("First 5:", gsm_ids[:5])
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `FileNotFoundError` during download | Incorrect `destdir` | Create directory first: `os.makedirs("geo_data/", exist_ok=True)` |
| `pivot_samples` returns empty DataFrame | GPL annotation table missing `ID` | Check `gpl.table.columns`; use correct probe ID column name |
| `KeyError` for `"Gene Symbol"` | Platform uses different column name | Inspect `gpl.table.columns` and use the correct annotation column |
| Download hangs for large series | Large SOFT file (GB range) | Use FTP Series Matrix download instead of GEOparse for large series |
| ESearch returns 0 results | Wrong `entry type` or field tag | Switch `gse[entry type]` to `gds[entry type]`; verify query syntax |
| Numeric sample columns contain `null` | Missing/absent expression values | Fill with `df.fillna(0)` or drop columns with high missingness |

## Related Skills

- `cellxgene-census` — Single-cell RNA-seq data at scale (61M+ cells) as an alternative to GEO for scRNA-seq
- `gene-database` — NCBI Gene records with curated annotations for genes found in GEO studies
- `pubmed-database` — Retrieve publications linked to GEO datasets via NCBI ELink
- `pydeseq2-differential-expression` — Downstream differential expression analysis after loading GEO count data

## References

- [GEO database home](https://www.ncbi.nlm.nih.gov/geo/) — Browse and search GEO datasets
- [GEOparse GitHub](https://github.com/guma44/GEOparse) — Python library documentation and examples
- [GEO FTP server](https://ftp.ncbi.nlm.nih.gov/geo/) — Direct file access for series, samples, and platforms
- [NCBI E-utilities for GEO](https://www.ncbi.nlm.nih.gov/books/NBK25499/) — ESearch/ESummary API reference for the `gds` database
