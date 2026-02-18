---
name: "archs4-database"
description: "Query uniformly processed RNA-seq gene expression profiles, tissue-specific expression patterns, and co-expression networks from the ARCHS4 database REST API. Retrieve z-score normalized expression across 1M+ human and mouse samples, find co-expressed genes, search samples by metadata, and download HDF5 expression matrices. For variant-level population genetics use gnomad-database; for pathway enrichment from gene lists use gget-genomic-databases (Enrichr)."
license: "CC-BY-4.0"
---

# ARCHS4 Database

## Overview

ARCHS4 (All RNA-seq and ChIP-seq Sample and Signature Search) is a resource of uniformly aligned and processed human and mouse RNA-seq data from NCBI GEO and SRA, covering 1 million+ samples. The REST API at `https://maayanlab.cloud/archs4/api/` provides gene-level expression profiles, z-score normalized tissue expression, co-expression networks, and sample metadata search — all without authentication. Large-scale bulk queries can also use the downloadable HDF5 expression matrices.

## When to Use

- Retrieving tissue-specific or cell-type-specific expression z-scores for a gene of interest across hundreds of tissue types
- Finding genes co-expressed with a query gene (co-expression network construction or guilt-by-association analysis)
- Searching for RNA-seq samples by tissue, disease, or metadata keyword to identify candidate datasets for reanalysis
- Comparing expression profiles of multiple genes across tissues to prioritize candidates for wet-lab follow-up
- Accessing uniformly processed gene expression matrices (HDF5 format) for large-scale cross-study analysis
- Validating differential expression results by checking whether a gene's expression direction matches population-level tissue profiles
- For variant-level population allele frequencies use `gnomad-database`; ARCHS4 provides expression evidence only
- For Enrichr pathway enrichment from a gene list use `gget-genomic-databases` (`gget enrichr`); ARCHS4 is for expression lookups

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`, `seaborn`
- **Data requirements**: gene symbols (HGNC format, e.g., `TP53`, `BRCA1`); sample GEO/SRA IDs for direct sample queries
- **Environment**: internet connection; no API key or account required
- **Rate limits**: ~10 requests/second; add `time.sleep(0.1)` between sequential gene queries to avoid throttling

```bash
pip install requests pandas matplotlib seaborn
```

## Quick Start

```python
import requests

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def archs4_get(endpoint: str, params: dict = None) -> dict:
    """Send a GET request to the ARCHS4 API and return parsed JSON."""
    r = requests.get(f"{ARCHS4_BASE}/{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Quick check: top tissues expressing TP53
data = archs4_get("meta/genes/TP53/zscore")
tissues = data.get("values", [])
print(f"TP53 tissue expression entries: {len(tissues)}")
top5 = sorted(tissues, key=lambda x: x.get("zscore", 0), reverse=True)[:5]
for t in top5:
    print(f"  {t['tissue']:<40}  z={t['zscore']:.2f}")
# TP53 tissue expression entries: 200
#   thymus                                   z=2.81
#   testis                                   z=2.44
```

## Core API

### Query 1: Gene Expression Z-Scores Across Tissues

Retrieve z-score normalized expression for a gene across all available tissue types. Z-scores are computed per-sample relative to the population distribution; positive values indicate above-average expression.

```python
import requests
import pandas as pd

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def get_gene_tissue_zscore(gene_symbol: str, species: str = "human") -> pd.DataFrame:
    """Return tissue z-score expression profile for a gene.

    Parameters
    ----------
    gene_symbol : str
        HGNC gene symbol (e.g., 'TP53').
    species : str
        'human' or 'mouse' (default: 'human').
    """
    endpoint = f"meta/genes/{gene_symbol}/zscore"
    r = requests.get(
        f"{ARCHS4_BASE}/{endpoint}",
        params={"species": species},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    records = data.get("values", [])
    df = pd.DataFrame(records)
    return df.sort_values("zscore", ascending=False).reset_index(drop=True)

df = get_gene_tissue_zscore("MYC")
print(f"MYC tissue z-scores: {len(df)} tissue types")
print(df[["tissue", "zscore"]].head(10).to_string(index=False))
# MYC tissue z-scores: 200
#                     tissue  zscore
#                      colon    3.12
#             small intestine    2.98
#                    placenta    2.74
```

```python
# Query mouse tissues for a gene
df_mouse = get_gene_tissue_zscore("Myc", species="mouse")
print(f"Mouse Myc: top 5 tissues")
print(df_mouse[["tissue", "zscore"]].head(5).to_string(index=False))
```

### Query 2: Co-expressed Genes

Find genes whose expression is most correlated with a query gene across all ARCHS4 samples. Useful for identifying pathway partners, regulators, or candidate targets.

```python
import requests
import pandas as pd

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def get_coexpressed_genes(gene_symbol: str, top_n: int = 50,
                           species: str = "human") -> pd.DataFrame:
    """Return genes co-expressed with the query gene.

    Parameters
    ----------
    gene_symbol : str
        HGNC gene symbol.
    top_n : int
        Number of correlated genes to return (default: 50).
    species : str
        'human' or 'mouse' (default: 'human').
    """
    r = requests.get(
        f"{ARCHS4_BASE}/meta/genes/{gene_symbol}/correlations",
        params={"species": species, "limit": top_n},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    records = data.get("values", [])
    df = pd.DataFrame(records)
    return df.sort_values("correlation", ascending=False).reset_index(drop=True)

coexp = get_coexpressed_genes("PCNA", top_n=20)
print(f"Top co-expressed genes with PCNA (n={len(coexp)}):")
print(coexp[["gene", "correlation"]].head(10).to_string(index=False))
# Top co-expressed genes with PCNA (n=20):
#   gene  correlation
#   RFC4         0.91
#   RFC2         0.89
#   MCM6         0.87
```

```python
# Extract gene list for downstream enrichment
gene_list = coexp["gene"].tolist()
print(f"Co-expression gene list: {gene_list[:10]}")
# Pass gene_list to Enrichr or pathway analysis tools
```

### Query 3: Sample Search

Search for RNA-seq samples by metadata keyword (tissue, disease condition, cell type, treatment). Returns GEO/SRA sample identifiers with metadata fields.

```python
import requests
import pandas as pd

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def search_samples(keyword: str, species: str = "human",
                   limit: int = 100) -> pd.DataFrame:
    """Search ARCHS4 samples by metadata keyword.

    Parameters
    ----------
    keyword : str
        Search term (e.g., 'breast cancer', 'liver', 'HeLa').
    species : str
        'human' or 'mouse'.
    limit : int
        Maximum number of samples to return.
    """
    r = requests.get(
        f"{ARCHS4_BASE}/samples/search",
        params={"query": keyword, "species": species, "limit": limit},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    records = data.get("samples", [])
    return pd.DataFrame(records)

samples = search_samples("pancreatic cancer", limit=50)
print(f"Samples matching 'pancreatic cancer': {len(samples)}")
if len(samples) > 0:
    print(samples[["sample_id", "series_id", "title"]].head(5).to_string(index=False))
# Samples matching 'pancreatic cancer': 50
#   sample_id  series_id  title
#   GSM2345678  GSE123456  Pancreatic ductal adenocarcinoma - sample 1
```

### Query 4: Gene-Level Metadata Summary

Retrieve summary statistics and metadata for a gene including the number of samples expressing it, expression percentile, and available annotation.

```python
import requests

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def get_gene_metadata(gene_symbol: str, species: str = "human") -> dict:
    """Return metadata and expression summary for a gene."""
    r = requests.get(
        f"{ARCHS4_BASE}/meta/genes/{gene_symbol}",
        params={"species": species},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

meta = get_gene_metadata("GAPDH")
print(f"Gene: {meta.get('gene_symbol', 'N/A')}")
print(f"Species: {meta.get('species', 'N/A')}")
print(f"Ensembl ID: {meta.get('ensembl_gene_id', 'N/A')}")
print(f"Description: {meta.get('description', 'N/A')[:80]}")
```

```python
# Compare metadata for a panel of housekeeping genes
import time

housekeeping = ["GAPDH", "ACTB", "B2M", "HPRT1", "RPLP0"]
for gene in housekeeping:
    meta = get_gene_metadata(gene)
    print(f"  {gene:<8}  {meta.get('ensembl_gene_id', 'N/A')}")
    time.sleep(0.1)
```

### Query 5: Visualization — Tissue Expression Barplot

Generate a publication-ready barplot of z-score expression across the top tissues for a gene.

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def plot_tissue_expression(gene_symbol: str, top_n: int = 20,
                            species: str = "human",
                            output_file: str = None) -> None:
    """Plot top tissue z-score expression for a gene.

    Parameters
    ----------
    gene_symbol : str
        HGNC gene symbol.
    top_n : int
        Number of top tissues to display.
    species : str
        'human' or 'mouse'.
    output_file : str
        If provided, save figure to this path.
    """
    r = requests.get(
        f"{ARCHS4_BASE}/meta/genes/{gene_symbol}/zscore",
        params={"species": species},
        timeout=30
    )
    r.raise_for_status()
    records = r.json().get("values", [])
    df = pd.DataFrame(records).sort_values("zscore", ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#D73027" if z > 0 else "#4575B4" for z in df["zscore"]]
    bars = ax.barh(df["tissue"][::-1], df["zscore"][::-1], color=colors[::-1])
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Expression Z-Score")
    ax.set_title(f"ARCHS4 Tissue Expression: {gene_symbol} ({species})\nTop {top_n} tissues")
    ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=8)
    plt.tight_layout()
    fname = output_file or f"{gene_symbol}_tissue_expression.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    print(f"Saved {fname}  ({len(df)} tissues plotted)")

plot_tissue_expression("BRCA1", top_n=15, output_file="BRCA1_tissue_expression.png")
```

### Query 6: HDF5 Bulk Data Access

Download or stream from ARCHS4's precomputed HDF5 expression matrices for large-scale cross-sample analysis. The HDF5 files contain gene × sample count matrices for human and mouse.

```python
import requests

# HDF5 files are available for bulk download from the ARCHS4 data portal
# URL pattern: https://maayanlab.cloud/archs4/download#expression
# Human gene-level: human_gene_v2.6.h5
# Mouse gene-level: mouse_gene_v2.6.h5

def get_h5_download_urls() -> dict:
    """Return download URLs for ARCHS4 HDF5 expression matrices."""
    base = "https://maayanlab.cloud/archs4"
    return {
        "human_gene": f"{base}/files/human_gene_v2.6.h5",
        "mouse_gene": f"{base}/files/mouse_gene_v2.6.h5",
        "human_transcript": f"{base}/files/human_transcript_v2.6.h5",
        "mouse_transcript": f"{base}/files/mouse_transcript_v2.6.h5",
    }

urls = get_h5_download_urls()
for key, url in urls.items():
    print(f"  {key:<22}  {url}")

# To work with a downloaded HDF5 file:
try:
    import h5py
    import numpy as np

    h5_path = "human_gene_v2.6.h5"   # after download

    def extract_gene_from_h5(h5_path: str, gene_symbol: str,
                              n_samples: int = 1000) -> dict:
        """Extract expression values for a gene from the HDF5 matrix."""
        with h5py.File(h5_path, "r") as f:
            genes = [g.decode() for g in f["meta"]["genes"]["gene_symbol"][:]]
            if gene_symbol not in genes:
                raise ValueError(f"{gene_symbol} not found in HDF5")
            idx = genes.index(gene_symbol)
            expr = f["data"]["expression"][idx, :n_samples]
            sample_ids = [s.decode() for s in f["meta"]["samples"]["geo_accession"][:n_samples]]
        return {"gene": gene_symbol, "expression": expr, "sample_ids": sample_ids}

    result = extract_gene_from_h5(h5_path, "TP53", n_samples=500)
    print(f"TP53 expression: mean={result['expression'].mean():.2f},"
          f" max={result['expression'].max():.2f} (n={len(result['expression'])} samples)")
except ImportError:
    print("h5py not installed. Install with: pip install h5py")
except FileNotFoundError:
    print("HDF5 file not downloaded yet. Use the URLs above to download first.")
```

## Key Concepts

### Z-Score Normalization

ARCHS4 reports gene expression as z-scores computed relative to all samples for that gene. A z-score of 0 means expression at the population mean; a z-score of 2.0 means expression 2 standard deviations above the mean. Z-scores are more interpretable across datasets than raw counts because they account for library size differences and batch effects introduced by uniform alignment across studies.

```python
# Example: Positive z-score = above-average expression for that gene
# z > 2.0 → top ~2.5% of samples for that gene
# z < -2.0 → bottom ~2.5% of samples for that gene
# Use absolute z-score thresholds consistently when comparing across genes
```

### HDF5 vs REST API

| Access method | Best for | Limitations |
|---------------|----------|-------------|
| REST API (`/zscore`, `/correlations`) | Quick single-gene queries, exploration | Aggregated profiles only, no per-sample access |
| REST API (`/samples/search`) | Discovering relevant datasets | Returns metadata, not expression values |
| HDF5 download | Bulk analysis, custom co-expression, ML | Requires 30–60 GB disk; download once |

### Species and Gene Symbol Conventions

ARCHS4 indexes human samples using HGNC gene symbols (uppercase, e.g., `TP53`) and mouse samples using MGI symbols (first letter uppercase, e.g., `Trp53`). The `species` parameter accepts `"human"` or `"mouse"`. Mixed-case or ensemble IDs will return empty results.

## Common Workflows

### Workflow 1: Multi-Gene Tissue Expression Heatmap

**Goal**: Compare tissue expression profiles of a gene panel and visualize as a heatmap to identify tissue-specific vs ubiquitous expression patterns.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

gene_panel = ["MYC", "TP53", "BRCA1", "EGFR", "KRAS", "CDK4"]
top_n_tissues = 25

def get_tissue_zscores(gene: str) -> pd.Series:
    r = requests.get(
        f"{ARCHS4_BASE}/meta/genes/{gene}/zscore",
        params={"species": "human"},
        timeout=30
    )
    r.raise_for_status()
    records = r.json().get("values", [])
    df = pd.DataFrame(records).set_index("tissue")["zscore"]
    return df

# Build expression matrix (genes × tissues)
all_data = {}
for gene in gene_panel:
    try:
        all_data[gene] = get_tissue_zscores(gene)
        print(f"  Fetched {gene}")
    except Exception as e:
        print(f"  Warning: {gene} failed — {e}")
    time.sleep(0.1)

matrix = pd.DataFrame(all_data).T   # genes × tissues
# Select top tissues by max absolute z-score
tissue_importance = matrix.abs().max(axis=0).sort_values(ascending=False)
top_tissues = tissue_importance.head(top_n_tissues).index
matrix_subset = matrix[top_tissues]

# Plot heatmap
fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap(
    matrix_subset,
    cmap="RdBu_r",
    center=0,
    vmin=-3,
    vmax=3,
    ax=ax,
    cbar_kws={"label": "Z-Score"},
    linewidths=0.5
)
ax.set_title("ARCHS4 Tissue Expression Profiles — Gene Panel")
ax.set_xlabel("Tissue")
ax.set_ylabel("Gene")
plt.xticks(rotation=45, ha="right", fontsize=8)
plt.tight_layout()
plt.savefig("archs4_panel_heatmap.png", dpi=150, bbox_inches="tight")
print(f"Saved archs4_panel_heatmap.png  ({matrix_subset.shape})")
```

### Workflow 2: Co-expression Network Seed Expansion

**Goal**: Start from a seed gene, retrieve co-expressed partners, then query their co-expressed genes in turn to build a two-hop co-expression neighborhood.

```python
import requests, time
import pandas as pd

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def get_coexp(gene: str, top_n: int = 20, species: str = "human") -> list:
    r = requests.get(
        f"{ARCHS4_BASE}/meta/genes/{gene}/correlations",
        params={"species": species, "limit": top_n},
        timeout=30
    )
    r.raise_for_status()
    return [rec["gene"] for rec in r.json().get("values", [])]

seed_gene = "PCNA"
min_correlation = 0.80

# Hop 1: direct co-expressed partners
hop1_genes = get_coexp(seed_gene, top_n=30)
print(f"Hop 1 partners of {seed_gene}: {len(hop1_genes)}")
time.sleep(0.1)

# Hop 2: co-expressed genes of each partner
edges = set()
for gene in hop1_genes[:10]:   # limit for demonstration
    partners = get_coexp(gene, top_n=20)
    for partner in partners:
        if partner != seed_gene:
            edges.add((gene, partner))
    time.sleep(0.1)

# Summarize the network
network_df = pd.DataFrame(list(edges), columns=["source", "target"])
hub_counts = network_df["source"].value_counts()
print(f"\nTwo-hop network: {len(edges)} edges")
print(f"Top hub genes:")
print(hub_counts.head(5))

network_df.to_csv(f"{seed_gene}_coexp_network.csv", index=False)
print(f"\nSaved {seed_gene}_coexp_network.csv")
```

### Workflow 3: Sample Discovery and Dataset Summary

**Goal**: Search for samples by disease keyword, summarize how many GEO series are available, and export sample metadata for downstream reanalysis selection.

```python
import requests, time
import pandas as pd

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def search_and_summarize(keyword: str, species: str = "human",
                          limit: int = 200) -> pd.DataFrame:
    """Search samples and return a tidy metadata DataFrame."""
    r = requests.get(
        f"{ARCHS4_BASE}/samples/search",
        params={"query": keyword, "species": species, "limit": limit},
        timeout=30
    )
    r.raise_for_status()
    records = r.json().get("samples", [])
    return pd.DataFrame(records)

keyword = "colorectal cancer"
df = search_and_summarize(keyword, limit=150)
print(f"Samples matching '{keyword}': {len(df)}")

if len(df) > 0:
    # Summarize by GEO series
    series_counts = df["series_id"].value_counts()
    print(f"\nTop GEO series (by sample count):")
    print(series_counts.head(8).to_string())

    # Export sample list
    df.to_csv(f"{keyword.replace(' ', '_')}_samples.csv", index=False)
    print(f"\nSaved {keyword.replace(' ', '_')}_samples.csv ({len(df)} samples)")
    print(f"Unique GEO series: {df['series_id'].nunique()}")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `species` | All gene endpoints | `"human"` | `"human"`, `"mouse"` | Selects the species-specific sample index |
| `limit` | `/correlations`, `/samples/search` | `100` | `1`–`500` | Number of results returned |
| `gene_symbol` (path) | `/meta/genes/{gene}/zscore`, `/correlations` | — | HGNC symbol (human) or MGI symbol (mouse) | Query gene; case-sensitive |
| `query` | `/samples/search` | — | free-text string | Metadata keyword search across title, tissue, source fields |
| `offset` | `/samples/search` | `0` | integer | Pagination offset for large result sets |
| `correlation` (response field) | `/correlations` | — | `-1.0`–`1.0` | Pearson correlation coefficient; filter `> 0.7` for high co-expression |
| `zscore` (response field) | `/zscore` | — | continuous float | Expression z-score; `> 2.0` = high expression |
| `page_size` (HDF5) | HDF5 slice | all | any integer | Number of samples to extract per read from HDF5 |

## Best Practices

1. **Use z-score thresholds consistently**: Because z-scores are gene-specific, a z-score of 2.0 for a ubiquitous gene (GAPDH) and a tissue-restricted gene (TTR, liver) have different interpretive meaning. Always annotate which gene you are comparing and the tissue background.

2. **Sleep between batch queries**: ARCHS4 enforces a soft rate limit of ~10 requests/second. Add `time.sleep(0.1)` between sequential gene queries to avoid `429 Too Many Requests` errors.

3. **Download HDF5 for large-scale analyses**: For queries covering 50+ genes or requiring per-sample expression values, the REST API is impractical. Download the HDF5 file once and use `h5py` slicing for fast matrix access; this avoids hitting rate limits and is 100× faster for bulk extraction.

4. **Match gene symbol conventions by species**: Human queries require HGNC uppercase symbols (e.g., `TP53`); mouse queries require MGI-style symbols (e.g., `Trp53`). Using the wrong case returns empty results without an error.

5. **Validate co-expression findings across datasets**: ARCHS4 co-expression aggregates across all tissue types. A high correlation may be driven by a single tissue or study. Cross-check with tissue-specific queries or manually inspect the top contributing GEO series.

## Common Recipes

### Recipe: Quick Tissue Specificity Check

When to use: Rapidly determine whether a gene is broadly expressed (housekeeping) or tissue-restricted before designing experiments.

```python
import requests

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def tissue_specificity_summary(gene_symbol: str) -> None:
    """Print a summary of high and low expression tissues for a gene."""
    r = requests.get(
        f"{ARCHS4_BASE}/meta/genes/{gene_symbol}/zscore",
        params={"species": "human"},
        timeout=30
    )
    r.raise_for_status()
    records = r.json().get("values", [])
    zscores = [rec["zscore"] for rec in records if rec.get("zscore") is not None]
    top_high = sorted(records, key=lambda x: x.get("zscore", 0), reverse=True)[:5]
    top_low = sorted(records, key=lambda x: x.get("zscore", float("inf")))[:3]
    print(f"\n{gene_symbol} — {len(zscores)} tissues")
    print(f"  Range: [{min(zscores):.2f}, {max(zscores):.2f}]  "
          f"Mean: {sum(zscores)/len(zscores):.2f}")
    print("  High expression:")
    for t in top_high:
        print(f"    {t['tissue']:<35}  z={t['zscore']:.2f}")
    print("  Low expression:")
    for t in top_low:
        print(f"    {t['tissue']:<35}  z={t['zscore']:.2f}")

tissue_specificity_summary("TTR")   # Transthyretin — liver-specific
```

### Recipe: Batch Gene Co-Expression Table

When to use: Generate a pairwise correlation table for a gene panel from a list of differentially expressed genes.

```python
import requests, time
import pandas as pd

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

def batch_coexpr_table(gene_list: list, top_n: int = 10) -> pd.DataFrame:
    """For each gene in gene_list, return its top co-expressed genes."""
    rows = []
    for gene in gene_list:
        try:
            r = requests.get(
                f"{ARCHS4_BASE}/meta/genes/{gene}/correlations",
                params={"species": "human", "limit": top_n},
                timeout=30
            )
            r.raise_for_status()
            for rec in r.json().get("values", []):
                rows.append({
                    "query_gene": gene,
                    "coexp_gene": rec.get("gene"),
                    "correlation": rec.get("correlation"),
                })
            time.sleep(0.1)
        except Exception as e:
            print(f"Warning: {gene} skipped — {e}")
    return pd.DataFrame(rows)

deg_list = ["MYC", "CCND1", "CDK4", "RB1", "E2F1"]
coexp_table = batch_coexpr_table(deg_list, top_n=10)
print(f"Co-expression entries: {len(coexp_table)}")
print(coexp_table.groupby("query_gene")["coexp_gene"].count())
coexp_table.to_csv("deg_coexpression_table.csv", index=False)
print("Saved deg_coexpression_table.csv")
```

### Recipe: Export Sample IDs for GEO Download

When to use: Identify relevant GEO accessions to download raw count matrices for a meta-analysis.

```python
import requests
import pandas as pd

ARCHS4_BASE = "https://maayanlab.cloud/archs4/api/v1"

keyword = "glioblastoma"
r = requests.get(
    f"{ARCHS4_BASE}/samples/search",
    params={"query": keyword, "species": "human", "limit": 200},
    timeout=30
)
r.raise_for_status()
samples = pd.DataFrame(r.json().get("samples", []))
if len(samples) > 0:
    # Get unique GEO series accessions
    series = samples["series_id"].dropna().unique()
    print(f"Unique GEO series for '{keyword}': {len(series)}")
    for s in series[:10]:
        n = (samples["series_id"] == s).sum()
        print(f"  {s}  ({n} samples)")
    # Export series list for GEO download script
    pd.Series(series, name="geo_series").to_csv(
        f"{keyword}_geo_series.txt", index=False
    )
    print(f"\nSaved {keyword}_geo_series.txt")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 404` for gene query | Gene symbol not found in ARCHS4 index | Verify HGNC symbol spelling; check `species` parameter matches gene convention (human: uppercase, mouse: first-letter-upper) |
| `HTTP 429 Too Many Requests` | Exceeded ~10 req/s rate limit | Add `time.sleep(0.1)` between requests; for batch queries use a 0.5 s delay |
| Empty `values` list in z-score response | Gene is not expressed in any indexed tissue, or wrong species | Switch species; verify gene is protein-coding and has GEO coverage |
| Empty `samples` list from search | Keyword not matched in metadata fields | Try broader or alternative keywords (e.g., `"liver"` instead of `"hepatic"`) |
| HDF5 gene not found | Symbol mismatch between HDF5 version and query | Check available genes in `f["meta"]["genes"]["gene_symbol"][:]`; try Ensembl ID or alias |
| `requests.exceptions.Timeout` | Slow API response under load | Increase `timeout=60`; retry with exponential backoff |
| Z-scores all near zero | Gene has very low or absent expression across tissues | Check the gene's expression in raw counts; the gene may be non-coding or very lowly expressed |

## Related Skills

- `gnomad-database` — Population variant frequencies; use after ARCHS4 to identify variants in highly expressed genes
- `gget-genomic-databases` — Enrichr pathway enrichment for ARCHS4 co-expression gene lists (`gget enrichr`)
- `pydeseq2-differential-expression` — Differential expression analysis on bulk RNA-seq; ARCHS4 HDF5 matrices can serve as reference cohorts

## References

- [ARCHS4 web portal](https://maayanlab.cloud/archs4/) — Interactive expression browser and dataset download
- [ARCHS4 REST API documentation](https://maayanlab.cloud/archs4/api/) — Endpoint reference and parameters
- [Lachmann et al., Nature Communications 2018](https://doi.org/10.1038/s41467-018-03751-6) — ARCHS4 original publication describing uniform alignment pipeline
- [ARCHS4 GitHub](https://github.com/MaayanLab/archs4) — Source code and HDF5 schema documentation
