---
name: cellxgene-census
description: "Query CELLxGENE Census (61M+ cells). Search by cell type/tissue/disease/organism; get AnnData, stream out-of-core, train PyTorch models. For your own data use scanpy; for annotated data use anndata."
license: MIT
---

# CZ CELLxGENE Census

## Overview

CZ CELLxGENE Census provides programmatic access to 61+ million standardized single-cell RNA-seq observations from human and mouse. It enables population-scale queries by cell type, tissue, disease, and donor metadata, returning expression data as AnnData objects or PyTorch dataloaders for ML workflows.

## When to Use

- Querying single-cell expression data across tissues, diseases, or cell types from a curated atlas
- Building reference datasets for cell type classification or marker gene discovery
- Training ML models on large-scale single-cell data (PyTorch integration)
- Comparing gene expression across conditions (e.g., COVID-19 vs healthy) at population scale
- Exploring what single-cell datasets are available for a tissue or disease of interest
- For **analyzing your own scRNA-seq data**, use scanpy instead
- For **manipulating AnnData objects** (subsetting, concatenation), use anndata instead

## Prerequisites

```bash
pip install cellxgene-census
# For ML workflows
pip install cellxgene-census[experimental]
```

**API Rate Limits**: Census uses TileDB-SOMA cloud backend. No explicit rate limit, but large queries (>1M cells) should use out-of-core processing (Module 4) to avoid memory exhaustion. Always use context managers for proper resource cleanup.

## Quick Start

```python
import cellxgene_census

with cellxgene_census.open_soma() as census:
    # Get B cells from lung
    adata = cellxgene_census.get_anndata(
        census=census,
        organism="Homo sapiens",
        obs_value_filter="cell_type == 'B cell' and tissue_general == 'lung' and is_primary_data == True",
        obs_column_names=["cell_type", "disease", "donor_id"],
    )
    print(f"Retrieved {adata.n_obs} cells × {adata.n_vars} genes")
    # Retrieved ~15000 cells × 60664 genes
```

## Core API

### 1. Opening and Exploring the Census

Connect to Census and discover available data.

```python
import cellxgene_census

# Open latest stable version (always use context manager)
with cellxgene_census.open_soma() as census:
    # Summary statistics
    summary = census["census_info"]["summary"].read().concat().to_pandas()
    print(f"Total cells: {summary['total_cell_count'][0]:,}")

    # List all datasets
    datasets = census["census_info"]["datasets"].read().concat().to_pandas()
    print(f"Total datasets: {len(datasets)}")
    print(datasets[["dataset_title", "cell_count"]].head())
```

```python
# Open specific version for reproducibility
with cellxgene_census.open_soma(census_version="2023-07-25") as census:
    # Reproducible analysis code here
    pass
```

### 2. Cell Metadata Queries

Query cell-level metadata without downloading expression data.

```python
import cellxgene_census

with cellxgene_census.open_soma() as census:
    # Get unique cell types in brain
    cell_metadata = cellxgene_census.get_obs(
        census,
        "homo_sapiens",
        value_filter="tissue_general == 'brain' and is_primary_data == True",
        column_names=["cell_type", "disease", "assay"]
    )
    print(f"Total brain cells: {len(cell_metadata):,}")
    print(cell_metadata["cell_type"].value_counts().head(10))
```

```python
    # Gene metadata query
    gene_metadata = cellxgene_census.get_var(
        census,
        "homo_sapiens",
        value_filter="feature_name in ['CD4', 'CD8A', 'FOXP3']",
        column_names=["feature_id", "feature_name", "feature_length"]
    )
    print(gene_metadata)
    # Returns DataFrame with Ensembl IDs, gene symbols, and lengths
```

### 3. Expression Data Queries (Small-Medium Scale)

Retrieve expression matrices as AnnData objects for queries returning <100k cells.

```python
import cellxgene_census

with cellxgene_census.open_soma() as census:
    # Query by cell type + tissue + disease
    adata = cellxgene_census.get_anndata(
        census=census,
        organism="Homo sapiens",
        obs_value_filter="cell_type == 'T cell' and disease == 'COVID-19' and is_primary_data == True",
        var_value_filter="feature_name in ['CD4', 'CD8A', 'CD19', 'FOXP3']",
        obs_column_names=["cell_type", "tissue_general", "donor_id"],
    )
    print(f"Shape: {adata.shape}")  # (n_cells, 4)
    print(f"Metadata columns: {list(adata.obs.columns)}")
```

**Filter syntax reference**:
- Combine conditions: `and`, `or`
- Multiple values: `feature_name in ['CD4', 'CD8A']`
- Comparison: `cell_count > 1000`
- Always include `is_primary_data == True` to avoid duplicate cells

### 4. Large-Scale Out-of-Core Queries

Stream expression data in chunks for queries exceeding available RAM.

```python
import cellxgene_census
import tiledbsoma as soma

with cellxgene_census.open_soma() as census:
    # Estimate query size first
    metadata = cellxgene_census.get_obs(
        census, "homo_sapiens",
        value_filter="tissue_general == 'brain' and is_primary_data == True",
        column_names=["soma_joinid"]
    )
    n_cells = len(metadata)
    print(f"Query will return {n_cells:,} cells")

    # If >100k cells, use streaming
    query = census["census_data"]["homo_sapiens"].axis_query(
        measurement_name="RNA",
        obs_query=soma.AxisQuery(
            value_filter="tissue_general == 'brain' and is_primary_data == True"
        ),
        var_query=soma.AxisQuery(
            value_filter="feature_name in ['FOXP2', 'TBR1', 'SATB2']"
        )
    )

    # Incremental statistics
    n_obs, total = 0, 0.0
    for batch in query.X("raw").tables():
        values = batch["soma_data"].to_numpy()
        n_obs += len(values)
        total += values.sum()

    print(f"Processed {n_obs:,} non-zero entries, mean={total/n_obs:.4f}")
```

### 5. Dataset Presence Matrix

Check which datasets measured specific genes (not all genes are in all datasets).

```python
import cellxgene_census

with cellxgene_census.open_soma() as census:
    presence = cellxgene_census.get_presence_matrix(
        census,
        "homo_sapiens",
        var_value_filter="feature_name in ['CD4', 'CD8A', 'PTPRC']"
    )
    print(f"Presence matrix shape: {presence.shape}")
    # (n_datasets, n_genes) — True if gene measured in dataset
```

### 6. PyTorch ML Integration

Train models directly on Census data using the experimental dataloader.

```python
from cellxgene_census.experimental.ml import experiment_dataloader
import cellxgene_census

with cellxgene_census.open_soma() as census:
    dataloader = experiment_dataloader(
        census["census_data"]["homo_sapiens"],
        measurement_name="RNA",
        X_name="raw",
        obs_value_filter="tissue_general == 'liver' and is_primary_data == True",
        obs_column_names=["cell_type"],
        batch_size=128,
        shuffle=True,
    )

    for batch in dataloader:
        X = batch["X"]           # Gene expression tensor
        labels = batch["obs"]    # Cell metadata
        print(f"Batch X shape: {X.shape}, labels: {list(labels.columns)}")
        break  # Show first batch only
```

## Key Concepts

### Census Data Model

The Census is organized as a SOMA (Stack of Matrices, Annotated) collection:

```
census/
├── census_info/
│   ├── summary          # Total cell counts
│   └── datasets         # Dataset metadata
└── census_data/
    ├── homo_sapiens/
    │   └── ms_RNA/
    │       ├── obs      # Cell metadata (61M+ rows)
    │       ├── var      # Gene metadata (~60k rows)
    │       └── X/raw    # Expression matrix (sparse)
    └── mus_musculus/
        └── ...
```

### Key Metadata Fields

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `cell_type` | str | Cell Ontology label | "B cell", "neuron", "macrophage" |
| `tissue_general` | str | Coarse tissue grouping | "brain", "lung", "blood" |
| `tissue` | str | Specific tissue | "prefrontal cortex", "alveolar tissue" |
| `disease` | str | Disease state | "normal", "COVID-19", "lung adenocarcinoma" |
| `assay` | str | Sequencing assay | "10x 3' v3", "Smart-seq2" |
| `is_primary_data` | bool | True = unique cell | Always filter `True` |
| `donor_id` | str | Donor identifier | Used for batch effects |

### `tissue_general` vs `tissue`

Use `tissue_general` for broad cross-tissue analyses and `tissue` for specific tissue queries:
```python
# Broad: all immune system cells
obs_value_filter = "tissue_general == 'immune system'"
# Specific: only PBMCs
obs_value_filter = "tissue == 'peripheral blood mononuclear cell'"
```

## Common Workflows

### Workflow 1: Cross-Tissue Cell Type Comparison

**Goal**: Compare macrophage gene expression across tissues.

```python
import cellxgene_census
import scanpy as sc

with cellxgene_census.open_soma() as census:
    adata = cellxgene_census.get_anndata(
        census=census,
        organism="Homo sapiens",
        obs_value_filter=(
            "cell_type == 'macrophage' and "
            "tissue_general in ['lung', 'liver', 'brain'] and "
            "is_primary_data == True"
        ),
        obs_column_names=["cell_type", "tissue_general", "donor_id", "disease"],
    )
    print(f"Macrophages: {adata.n_obs} cells from {adata.obs['tissue_general'].nunique()} tissues")

    # Standard scanpy analysis
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, n_top_genes=2000)
    sc.pp.pca(adata, n_comps=50)
    sc.pp.neighbors(adata)
    sc.tl.umap(adata)

    # Differential expression across tissues
    sc.tl.rank_genes_groups(adata, groupby="tissue_general")
    sc.pl.umap(adata, color=["tissue_general", "disease"])
```

### Workflow 2: Disease-Associated Gene Expression

**Goal**: Compare marker gene expression between COVID-19 and healthy controls.

1. Query metadata to identify available cell types in COVID-19 data (Core API module 2)
2. Retrieve expression data for selected cell types and marker genes (Core API module 3)
3. Compute mean expression per cell type per condition
4. Visualize with scanpy `dotplot` or `matrixplot`

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `organism` | `get_anndata`, `get_obs` | — | `"Homo sapiens"`, `"Mus musculus"` | Species selection |
| `census_version` | `open_soma` | latest stable | Date string `"YYYY-MM-DD"` | Pin to specific data release |
| `obs_value_filter` | `get_anndata`, `get_obs` | None | SOMA filter expression | Cell-level filtering |
| `var_value_filter` | `get_anndata`, `get_var` | None | SOMA filter expression | Gene-level filtering |
| `obs_column_names` | `get_anndata`, `get_obs` | all columns | list of field names | Reduces data transfer |
| `batch_size` | `experiment_dataloader` | 128 | 32–512 | PyTorch batch size |
| `shuffle` | `experiment_dataloader` | False | True/False | Randomize training order |

## Best Practices

1. **Always filter `is_primary_data == True`**: Without this filter, duplicate cells across datasets inflate counts and bias analyses.

2. **Estimate query size before loading**: Call `get_obs()` with `column_names=["soma_joinid"]` to count cells before downloading expression data. Use out-of-core processing for >100k cells.

3. **Pin `census_version` for reproducibility**: The default "latest stable" changes periodically. Always specify the version for published analyses.

4. **Select only needed metadata columns**: Passing `obs_column_names` reduces data transfer and memory usage significantly for large queries.

5. **Use `tissue_general` for cross-tissue analyses**: The `tissue` field has hundreds of specific values; `tissue_general` provides ~30 coarse groupings suitable for comparative analyses.

6. **Anti-pattern — querying all genes when you need a few**: Specify `var_value_filter` to retrieve only genes of interest. Downloading the full ~60k gene matrix for 3 marker genes wastes bandwidth and memory.

## Common Recipes

### Recipe: Multi-Tissue Dataset Summary

```python
import cellxgene_census
import pandas as pd

with cellxgene_census.open_soma() as census:
    metadata = cellxgene_census.get_obs(
        census, "homo_sapiens",
        value_filter="is_primary_data == True",
        column_names=["tissue_general", "cell_type", "disease"]
    )
    summary = metadata.groupby("tissue_general").agg(
        n_cells=("cell_type", "size"),
        n_cell_types=("cell_type", "nunique"),
        n_diseases=("disease", "nunique"),
    ).sort_values("n_cells", ascending=False)
    print(summary.head(10))
```

### Recipe: Export Census Subset to h5ad

```python
import cellxgene_census

with cellxgene_census.open_soma() as census:
    adata = cellxgene_census.get_anndata(
        census=census,
        organism="Homo sapiens",
        obs_value_filter="tissue_general == 'heart' and is_primary_data == True",
        obs_column_names=["cell_type", "disease", "donor_id", "assay"],
    )
    adata.write_h5ad("heart_cells.h5ad")
    print(f"Saved {adata.n_obs} cells to heart_cells.h5ad")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `MemoryError` on `get_anndata()` | Query returns too many cells | Check count with `get_obs()` first; use out-of-core `axis_query()` for >100k cells |
| Duplicate cells in results | Missing `is_primary_data == True` filter | Add `is_primary_data == True` to all `obs_value_filter` queries |
| Gene not found | Wrong gene name or gene not in Census | Check spelling (case-sensitive); try Ensembl ID via `feature_id`; verify with `get_presence_matrix()` |
| `ConnectionError` / timeout | Census backend temporarily unavailable | Retry after 1-2 minutes; pin a specific `census_version` for reliability |
| Version inconsistencies | Using default "latest" across sessions | Always specify `census_version` in production code |
| Slow query performance | Downloading all metadata columns | Specify only needed columns via `obs_column_names` |
| `ImportError: cellxgene_census` | Package not installed | `pip install cellxgene-census` (note the hyphen) |

## Related Skills

- **scanpy-scrna-seq** — downstream analysis of Census data (clustering, DEG, visualization)
- **anndata-annotated-data** — manipulating AnnData objects returned by Census queries
- **esm-protein-language-model** — protein embeddings from sequences; complementary to Census gene expression data

## References

- [CELLxGENE Census documentation](https://chanzuckerberg.github.io/cellxgene-census/) — official API reference
- [CELLxGENE Discover](https://cellxgene.cziscience.com/) — web browser for Census data
- [TileDB-SOMA](https://github.com/single-cell-data/TileDB-SOMA) — underlying data access layer
- CZI (2023) "CZ CELLxGENE Discover: A single-cell data platform for scalable exploration, analysis and modeling of aggregated data" — [bioRxiv](https://doi.org/10.1101/2023.10.30.563174)
