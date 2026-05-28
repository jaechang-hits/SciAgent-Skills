---
name: anndata-data-structure
description: "Annotated matrices for single-cell genomics. Stores X with obs/var metadata, layers, embeddings (obsm/varm), graphs (obsp/varp), uns. Use for .h5ad/.zarr I/O, concatenation, scverse integration. For analysis use scanpy; for probabilistic models use scvi-tools."
license: BSD-3-Clause
---

# AnnData — Annotated Data Matrices for Single-Cell Genomics

## Overview

AnnData provides the standard data structure for single-cell genomics in the scverse ecosystem. It stores an observations-by-variables matrix (X) alongside cell metadata (obs), gene metadata (var), layers, embeddings (obsm/varm), graphs (obsp/varp), and unstructured metadata (uns). Supports sparse matrices, H5AD/Zarr storage, backed mode for large files, and integration with Scanpy, scvi-tools, and Muon.

## When to Use

- Constructing annotated matrices from raw count data with cell/gene metadata
- Reading/writing `.h5ad` or `.zarr` files for single-cell experiments
- Subsetting cells by quality metrics, gene sets, or metadata conditions
- Concatenating multiple experimental batches with consistent metadata
- Storing multiple data layers (raw counts, normalized, scaled) in one object
- Working with large datasets exceeding RAM (backed mode, lazy concatenation)
- Preparing data for Scanpy or scvi-tools pipelines
- For single-cell **analysis** (clustering, DE, visualization), use `scanpy` instead
- For **probabilistic models**, use `scvi-tools` instead

## Prerequisites

- **Python packages**: `anndata`, `scipy`, `pandas`, `numpy`
- **Optional**: `scanpy` (analysis), `zarr` (cloud storage), `h5py` (HDF5 backend)
- **Data requirements**: count matrices (dense or sparse), cell/gene metadata tables

```bash
pip install "anndata>=0.10"
# Full ecosystem
pip install anndata scanpy zarr
```

## Quick Start

```python
import anndata as ad
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

counts = csr_matrix(np.random.poisson(0.5, (500, 2000)).astype(np.float32))
obs = pd.DataFrame({"cell_type": np.random.choice(["T", "B", "NK"], 500)},
                    index=[f"cell_{i}" for i in range(500)])
var = pd.DataFrame(index=[f"ENSG{i:05d}" for i in range(2000)])
adata = ad.AnnData(X=counts, obs=obs, var=var)
adata.layers["raw_counts"] = counts.copy()
adata.write_h5ad("example.h5ad", compression="gzip")
print(f"Created: {adata.n_obs} cells x {adata.n_vars} genes")
# Created: 500 cells x 2000 genes
```

## Core API

### 1. Object Creation

Build AnnData objects from arrays, DataFrames, and sparse matrices.

```python
import anndata as ad
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

# Minimal: just a matrix
adata_min = ad.AnnData(X=np.random.rand(100, 50).astype(np.float32))
print(f"Minimal: {adata_min.shape}")  # (100, 50)

# Full: sparse matrix + obs/var metadata
n_obs, n_vars = 300, 1000
X = csr_matrix(np.random.poisson(1, (n_obs, n_vars)).astype(np.float32))
obs = pd.DataFrame({"cell_type": np.random.choice(["T", "B", "Mono"], n_obs),
                     "batch": np.repeat(["ctrl", "stim"], n_obs // 2)},
                    index=[f"cell_{i}" for i in range(n_obs)])
var = pd.DataFrame({"gene_symbol": [f"Gene_{i}" for i in range(n_vars)],
                     "mt": [i < 13 for i in range(n_vars)]},
                    index=[f"ENSG{i:05d}" for i in range(n_vars)])
adata = ad.AnnData(X=X, obs=obs, var=var)
print(f"Full: {adata.shape}, obs cols: {list(adata.obs.columns)}")
# Full: (300, 1000), obs cols: ['cell_type', 'batch']

# From a pandas DataFrame (rows=obs, columns=vars)
df = pd.DataFrame(np.random.rand(50, 20),
                  index=[f"sample_{i}" for i in range(50)],
                  columns=[f"feature_{i}" for i in range(20)])
adata_df = ad.AnnData(df)
print(f"From DataFrame: {adata_df.shape}")  # (50, 20)
```

### 2. I/O Operations

Read and write in multiple formats including backed mode for large files.

```python
import anndata as ad

# H5AD (native format, recommended for most use cases)
adata = ad.read_h5ad("data.h5ad")
adata.write_h5ad("output.h5ad", compression="gzip")  # gzip: smaller files

# 10X Genomics formats
adata_10x = ad.read_10x_h5("filtered_feature_bc_matrix.h5")
# adata_mtx = ad.read_10x_mtx("filtered_feature_bc_matrix/")

# Zarr format (cloud-friendly, parallel I/O)
adata.write_zarr("output.zarr")
adata_zarr = ad.read_zarr("output.zarr")

# Other formats
# adata = ad.read_csv("expression.csv")
# adata = ad.read_loom("data.loom")

print(f"Loaded: {adata.n_obs} obs x {adata.n_vars} vars")
```

```python
import anndata as ad

# Backed mode: lazy loading for files larger than RAM
adata_backed = ad.read_h5ad("large_data.h5ad", backed="r")  # read-only
print(f"Backed: {adata_backed.n_obs} obs, isbacked={adata_backed.isbacked}")

# Filter on metadata (no data loaded), then load subset into memory
subset = adata_backed[adata_backed.obs["tissue"] == "brain"].to_memory()
print(f"Loaded subset: {subset.n_obs} cells")

# Read-write backed mode: adata_rw = ad.read_h5ad("data.h5ad", backed="r+")
# Format conversion: ad.read_loom("data.loom").write_h5ad("out.h5ad", compression="gzip")
```

### 3. Subsetting and Views

Select cells and genes by indices, names, boolean masks, or metadata conditions.

```python
import anndata as ad

adata = ad.read_h5ad("data.h5ad")

# Boolean mask (most common)
t_cells = adata[adata.obs["cell_type"] == "T_cell"]
print(f"T cells: {t_cells.n_obs}, is_view: {t_cells.is_view}")  # is_view: True

# Integer index / name-based / combined axis
first_100 = adata[:100, :500]
selected = adata[["cell_0", "cell_1"], ["ENSG00000", "ENSG00001"]]

# Combined metadata conditions
high_quality = adata[
    (adata.obs["n_genes"] > 200) & (adata.obs["pct_mito"] < 0.2)
]
print(f"QC filter: {high_quality.n_obs} / {adata.n_obs} cells")

# Views vs copies: subsetting returns a view (lightweight, shares data)
# .copy() creates an independent object (REQUIRED before modification)
independent = adata[adata.obs["batch"] == "ctrl"].copy()
print(f"Is view: {independent.is_view}")  # False
```

### 4. Layers, Embeddings, and Graphs

Store multiple data representations, dimensionality reductions, and cell-cell graphs.

```python
import anndata as ad
import numpy as np
from scipy.sparse import csr_matrix

adata = ad.read_h5ad("data.h5ad")

# Layers: alternative representations of X (same shape as X)
adata.layers["raw_counts"] = adata.X.copy()
adata.layers["normalized"] = adata.X.copy()
print(f"Layers: {list(adata.layers.keys())}")
# Layers: ['raw_counts', 'normalized']

# Embeddings in obsm (n_obs x n_components)
adata.obsm["X_pca"] = np.random.randn(adata.n_obs, 50).astype(np.float32)
adata.obsm["X_umap"] = np.random.randn(adata.n_obs, 2).astype(np.float32)
print(f"obsm keys: {list(adata.obsm.keys())}")

# Variable loadings in varm (n_vars x n_components)
adata.varm["PCs"] = np.random.randn(adata.n_vars, 50).astype(np.float32)

# Pairwise graphs in obsp (n_obs x n_obs, sparse)
adata.obsp["connectivities"] = csr_matrix(
    np.random.rand(adata.n_obs, adata.n_obs) > 0.99)
adata.obsp["distances"] = adata.obsp["connectivities"].copy()

# Unstructured metadata in uns (arbitrary dict)
adata.uns["experiment"] = {"date": "2024-06-01", "protocol": "10x_v3"}
adata.uns["neighbors"] = {"params": {"n_neighbors": 15, "method": "umap"}}
adata.uns["cell_type_colors"] = ["#1f77b4", "#ff7f0e", "#2ca02c"]
print(f"uns keys: {list(adata.uns.keys())}")
```

### 5. Concatenation

Merge datasets along observations or variables with flexible join and merge strategies.

```python
import anndata as ad
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

# Create sample datasets
def make_adata(n, genes, batch_name):
    X = csr_matrix(np.random.poisson(1, (n, len(genes))).astype(np.float32))
    obs = pd.DataFrame({"sample": batch_name}, index=[f"{batch_name}_{i}" for i in range(n)])
    return ad.AnnData(X=X, obs=obs, var=pd.DataFrame(index=genes))

shared = [f"Gene_{i}" for i in range(100)]
adata1 = make_adata(200, shared + ["GeneA"], "batch1")
adata2 = make_adata(300, shared + ["GeneB"], "batch2")

# Along observations (axis=0): stack cells
combined = ad.concat(
    [adata1, adata2], axis=0, join="inner",
    label="batch", keys=["B1", "B2"], merge="same",
)
print(f"Inner join: {combined.n_obs} cells, {combined.n_vars} genes")
# Inner join: 500 cells, 100 genes

# Outer join: keeps all genes, fills missing with NaN/0
combined_outer = ad.concat([adata1, adata2], join="outer")
print(f"Outer join: {combined_outer.n_vars} genes")  # 102 genes

# Along variables (axis=1): multi-modal
n = 100
obs = pd.DataFrame(index=[f"cell_{i}" for i in range(n)])
rna = ad.AnnData(X=csr_matrix(np.random.poisson(1, (n, 500)).astype(np.float32)),
                 obs=obs, var=pd.DataFrame(index=[f"RNA_{i}" for i in range(500)]))
protein = ad.AnnData(X=csr_matrix(np.random.rand(n, 50).astype(np.float32)),
                     obs=obs, var=pd.DataFrame(index=[f"ADT_{i}" for i in range(50)]))
multimodal = ad.concat([rna, protein], axis=1)
print(f"Multimodal: {multimodal.shape}")  # (100, 550)
```

```python
# Lazy concatenation for very large datasets (no data copying)
from anndata.experimental import AnnCollection

collection = AnnCollection(
    {"batch1": adata1, "batch2": adata2},
    join_obs="inner",
)
print(f"Lazy collection: {collection.n_obs} total obs")
# On-disk concat (writes directly to disk without loading all into memory)
# ad.experimental.concat_on_disk({"b1": "batch1.h5ad", "b2": "batch2.h5ad"}, "combined.h5ad")
```

### 6. Data Manipulation

Type conversions, metadata management, renaming, and quality control filtering.

```python
import anndata as ad
import numpy as np
from scipy.sparse import csr_matrix, issparse

adata = ad.read_h5ad("data.h5ad")

# Type conversions
adata.strings_to_categoricals()  # string cols -> categorical (saves memory)
if not issparse(adata.X):
    adata.X = csr_matrix(adata.X)  # dense -> sparse
dense_X = adata.X.toarray() if issparse(adata.X) else adata.X  # sparse -> dense

# Adding/removing metadata columns
adata.obs["log_counts"] = np.log1p(np.array(adata.X.sum(axis=1)).flatten())
adata.var["mean_expr"] = np.array(adata.X.mean(axis=0)).flatten()
del adata.obs["unwanted_column"]  # remove

# Renaming observations/variables/categories
adata.obs_names_make_unique()  # add suffixes to duplicate names
adata.var_names_make_unique()
adata.obs["cell_type"] = adata.obs["cell_type"].cat.rename_categories(
    {"T": "T_cell", "B": "B_cell"})

# Quality control filtering (always .copy() after subsetting)
adata.obs["n_genes"] = np.array((adata.X > 0).sum(axis=1)).flatten()
mito_mask = adata.var_names.str.startswith("MT-")
adata.obs["pct_mito"] = (np.array(adata[:, mito_mask].X.sum(axis=1)).flatten()
                          / np.array(adata.X.sum(axis=1)).flatten())
adata_qc = adata[(adata.obs["n_genes"] > 200) & (adata.obs["pct_mito"] < 0.2)].copy()
print(f"After QC: {adata_qc.n_obs} / {adata.n_obs} cells")
```

## Key Concepts

### AnnData Object Architecture

The AnnData object is an annotated matrix with the following slots:

| Slot | Type | Shape | Description | Common Keys |
|------|------|-------|-------------|-------------|
| `X` | matrix (sparse/dense) | (n_obs, n_vars) | Primary data (expression counts) | -- |
| `obs` | DataFrame | (n_obs, _) | Cell/observation metadata | cell_type, sample, n_genes, batch |
| `var` | DataFrame | (n_vars, _) | Gene/variable metadata | gene_name, highly_variable, mt |
| `layers` | dict of matrices | same as X | Alternative representations | raw_counts, normalized, scaled |
| `obsm` | dict of arrays | (n_obs, _) | Embeddings per observation | X_pca, X_umap, X_tsne |
| `varm` | dict of arrays | (n_vars, _) | Loadings per variable | PCs |
| `obsp` | dict of sparse | (n_obs, n_obs) | Pairwise observation graphs | connectivities, distances |
| `varp` | dict of sparse | (n_vars, n_vars) | Pairwise variable relationships | -- |
| `uns` | dict | unstructured | Analysis parameters and metadata | neighbors, colors, experiment |
| `raw` | AnnData | original shape | Snapshot before gene filtering | -- |

### Views vs Copies

Subsetting returns a **view** (lightweight reference sharing data with parent). Always `.copy()` before modification to avoid `ImplicitModificationWarning`.

```python
view = adata[adata.obs["cell_type"] == "T_cell"]
print(f"is_view: {view.is_view}")        # True -- shares memory
independent = view.copy()
print(f"is_view: {independent.is_view}")  # False -- independent
```

### Storage Formats

| Format | Extension | Best For | Backed Mode | Notes |
|--------|-----------|----------|-------------|-------|
| H5AD | `.h5ad` | Default storage, random access | Yes (`"r"`, `"r+"`) | Based on HDF5; supports compression |
| Zarr | `.zarr` | Cloud storage, parallel I/O | No | Directory-based; good for S3/GCS |
| 10X H5 | `.h5` | 10X Genomics CellRanger output | No | Read-only via `read_10x_h5` |
| Loom | `.loom` | Legacy format (HDF5-based) | No | Deprecated in favor of H5AD |
| CSV | `.csv` | Interoperability, small datasets | No | No sparse/metadata support |

## Common Workflows

### Workflow 1: Single-cell RNA-seq Data Preparation

**Goal**: Load raw data, QC filter, normalize, and save for downstream Scanpy/scvi-tools analysis.

```python
import anndata as ad
import numpy as np
from scipy.sparse import issparse

# 1. Load and QC filter (see Core API 6 for metric computation details)
adata = ad.read_h5ad("raw_counts.h5ad")
adata.obs["n_genes"] = np.array((adata.X > 0).sum(axis=1)).flatten()
adata.obs["total_counts"] = np.array(adata.X.sum(axis=1)).flatten()
mito = adata.var_names.str.startswith("MT-")
adata.obs["pct_mito"] = (np.array(adata[:, mito].X.sum(axis=1)).flatten()
                          / np.array(adata.X.sum(axis=1)).flatten())
adata = adata[(adata.obs["n_genes"].between(200, 5000)) &
              (adata.obs["pct_mito"] < 0.2)].copy()
adata = adata[:, np.array((adata.X > 0).sum(axis=0)).flatten() >= 3].copy()

# 2. Store raw counts, then normalize (total-count + log1p)
adata.layers["counts"] = adata.X.copy()
totals = np.array(adata.X.sum(axis=1)).flatten()
if issparse(adata.X):
    adata.X = np.log1p(adata.X.multiply(1.0 / totals[:, None]).toarray() * 1e4)
else:
    adata.X = np.log1p(adata.X / totals[:, None] * 1e4)

# 3. Save
adata.strings_to_categoricals()
adata.write_h5ad("processed.h5ad", compression="gzip")
print(f"Saved: {adata.n_obs} cells x {adata.n_vars} genes, layers: {list(adata.layers.keys())}")
```

### Workflow 2: Multi-batch Integration

**Goal**: Load multiple batches, harmonize genes, concatenate with labels, and save.

```python
import anndata as ad
from pathlib import Path

# 1. Load all batches
batches = {}
for h5 in sorted(Path("batches/").glob("*.h5ad")):
    batches[h5.stem] = ad.read_h5ad(str(h5))
    print(f"  {h5.stem}: {batches[h5.stem].n_obs} cells")

# 2. Harmonize genes and concatenate
shared = set.intersection(*[set(a.var_names) for a in batches.values()])
batches = {k: v[:, list(shared)].copy() for k, v in batches.items()}
combined = ad.concat(batches, label="batch", join="inner", merge="same")

# 3. Clean up and save
combined.obs_names_make_unique()
combined.strings_to_categoricals()
combined.write_h5ad("combined_batches.h5ad", compression="gzip")
print(f"Combined: {combined.n_obs} cells x {combined.n_vars} genes, "
      f"{combined.obs['batch'].nunique()} batches")
```

### Workflow 3: Large Dataset Processing (Backed Mode)

**Goal**: Process datasets too large for memory using lazy loading.

1. Open file in backed mode: `adata = ad.read_h5ad("huge.h5ad", backed="r")`
2. Inspect metadata without loading data: check `adata.obs`, `adata.var`
3. Filter on metadata conditions: `mask = adata.obs["tissue"] == "brain"`
4. Load filtered subset into memory: `subset = adata[mask].to_memory()`
5. Process the in-memory subset normally (normalize, filter genes)
6. For chunked processing: iterate `adata[i:i+chunk_size].to_memory()` (uses Core API modules 2 and 3)

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `backed` | `read_h5ad` | `None` | `None`, `"r"`, `"r+"` | Lazy loading; `"r"` read-only, `"r+"` read-write |
| `compression` | `write_h5ad` | `None` | `None`, `"gzip"`, `"lzf"` | File compression; gzip=smaller, lzf=faster |
| `axis` | `concat` | `0` | `0`, `1` | 0=stack observations, 1=stack variables |
| `join` | `concat` | `"inner"` | `"inner"`, `"outer"` | inner=shared features, outer=union with fill |
| `merge` | `concat` | `None` | `"same"`, `"unique"`, `"first"`, `"only"` | Strategy for non-concatenated annotations |
| `label` | `concat` | `None` | Any string | Column name added to obs tracking source |
| `keys` | `concat` | `None` | list of strings | Labels for each dataset in the label column |
| `chunks` | `write_zarr` | `None` | Tuple of ints | Chunk dimensions for Zarr arrays |
| `as_sparse` | `read_h5ad` | `{}` | Dict mapping slot to format | Convert dense arrays to sparse on read |

## Best Practices

1. **Use sparse matrices for count data**: Single-cell count matrices are typically 90%+ zeros. Use `scipy.sparse.csr_matrix` to reduce memory by ~10x.
   ```python
   from scipy.sparse import csr_matrix
   adata.X = csr_matrix(adata.X)
   ```

2. **Convert strings to categoricals before saving**: Repeated string columns (cell_type, batch, sample) waste memory. Call `adata.strings_to_categoricals()` before `.write_h5ad()`.

3. **Use backed mode for files larger than RAM**: Open with `backed="r"`, filter on obs/var metadata, then `.to_memory()` only the subset you need. Never try to load a 50GB file directly.

4. **Always copy views before modifying**: Subsetting returns a view. Modifying triggers `ImplicitModificationWarning`. Use `adata[mask].copy()` before any modification.

5. **Store raw counts in layers before normalization**: `adata.layers["counts"] = adata.X.copy()` before any transformation -- raw counts cannot be recovered from normalized data.

6. **Use gzip compression for long-term storage**: `adata.write_h5ad("f.h5ad", compression="gzip")` reduces size 2-5x. Use `lzf` for speed-critical workflows.

7. **Align external data on index**: Pandas index alignment silently inserts NaN. Always use `external_series.reindex(adata.obs_names).values` when assigning external data to obs/var.

## Common Recipes

### Recipe: PyTorch DataLoader Integration

When to use: Training deep learning models on single-cell data.

```python
import anndata as ad
from anndata.experimental.pytorch import AnnLoader

adata = ad.read_h5ad("data.h5ad")

# Create PyTorch DataLoader directly from AnnData
dataloader = AnnLoader(adata, batch_size=128, shuffle=True)

for batch in dataloader:
    X_batch = batch.X  # torch.Tensor, shape (128, n_vars)
    obs_batch = batch.obs  # DataFrame with batch metadata
    print(f"Batch shape: {X_batch.shape}")
    break  # demo: process first batch only
```

### Recipe: Pandas DataFrame Conversion

When to use: Interoperating with non-scverse tools that expect DataFrames.

```python
import anndata as ad
import pandas as pd
import numpy as np

adata = ad.read_h5ad("data.h5ad")

# AnnData to DataFrame (dense, uses var_names as columns)
df = adata.to_df()
print(f"DataFrame: {df.shape}")  # (n_obs, n_vars)

# Include a specific layer instead of X
df_raw = adata.to_df(layer="raw_counts")

# DataFrame back to AnnData
new_adata = ad.AnnData(df)
print(f"Back to AnnData: {new_adata.shape}")
```

### Recipe: Optimized File Saving

When to use: Minimizing file size and save time for large datasets.

```python
import anndata as ad
from scipy.sparse import issparse, csr_matrix

adata = ad.read_h5ad("data.h5ad")
if not issparse(adata.X):
    adata.X = csr_matrix(adata.X)  # ensure sparse
adata.strings_to_categoricals()     # compress string columns
for key in ["temp_results"]:
    adata.uns.pop(key, None)        # remove bulky items
adata.write_h5ad("optimized.h5ad", compression="gzip")
print(f"Saved: {adata.n_obs} x {adata.n_vars}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `MemoryError` when reading H5AD | File too large for RAM | Use `ad.read_h5ad(path, backed="r")` for lazy loading |
| Slow `.write_h5ad()` | Large dense matrix | Convert to sparse: `adata.X = csr_matrix(adata.X)`; use `compression="gzip"` |
| `ValueError` on `ad.concat()` | Mismatched var indices | Use `join="inner"` for shared genes, or harmonize var_names before concat |
| NaN values after adding obs column | Pandas index misalignment | Use `.reindex(adata.obs_names).values` when assigning external data |
| `ImplicitModificationWarning` | Modifying a view in-place | Call `.copy()` on the subset before modification |
| `IORegistryError` on save | Unsupported dtype in uns/obsm | Convert complex objects to strings/arrays; remove non-serializable items from `uns` |
| Duplicated obs_names after concat | Same barcodes across batches | Use `adata.obs_names_make_unique()` after concatenation |
| `KeyError` accessing layer/obsm | Key doesn't exist | Check available keys: `list(adata.layers.keys())`, `list(adata.obsm.keys())` |

## Ecosystem Integration

```python
# Scanpy: preprocessing, clustering, visualization (operates on AnnData in-place)
import scanpy as sc
adata = ad.read_h5ad("data.h5ad")
sc.pp.normalize_total(adata); sc.tl.pca(adata); sc.pl.umap(adata, color="cell_type")

# Muon: multimodal data -- mu.MuData({"rna": adata_rna, "atac": adata_atac})
# scvi-tools: scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
```

## Bundled Resources

Two reference files consolidate the original 5 reference files:

1. **`references/data_structure_io.md`** -- Consolidates data_structure.md + io_operations.md. Covers: detailed slot-by-slot API, all I/O format parameters, backed mode advanced patterns (chunked iteration, write-back). Relocated inline: core slot table (Key Concepts), basic I/O (Core API 2), format comparison (Key Concepts). Omitted: introductory prose redundant with Core API.

2. **`references/manipulation_concatenation.md`** -- Consolidates manipulation.md + concatenation.md + best_practices.md. Covers: advanced merge behaviors (same/unique/first/only edge cases), on-disk concat, AnnCollection API, bulk renaming, memory optimization. Relocated inline: QC filtering (Core API 6), basic concat (Core API 5), best practices (Best Practices). Omitted: generic Python advice not AnnData-specific.

## Related Skills

- **scanpy-scrna-seq** -- downstream analysis: preprocessing, clustering, DE testing, visualization using AnnData objects
- **scvi-tools-single-cell** -- probabilistic latent variable models (scVI, scANVI, TOTALVI) consuming AnnData
- **cellxgene-census** -- querying the CZ CELLxGENE Census database, returns AnnData objects

## References

- [AnnData documentation](https://anndata.readthedocs.io/) -- official API reference and tutorials
- [scverse ecosystem](https://scverse.org/) -- coordinated single-cell analysis tools
- [AnnData GitHub](https://github.com/scverse/anndata) -- source code and issue tracker
- Virshup et al. (2024) "anndata: Access and store annotated data matrices" -- [JOSS](https://doi.org/10.21105/joss.04371)
