# AnnData — Data Structure & I/O Reference

## Detailed Slot-by-Slot API

### The `raw` Attribute

Stores a frozen snapshot before gene filtering, preserving the full variable space for DE and plotting.

```python
import anndata as ad

adata = ad.read_h5ad("data.h5ad")
adata.raw = adata.copy()  # freeze BEFORE HVG filtering

hvg_mask = adata.var["highly_variable"]
adata = adata[:, hvg_mask].copy()
print(f"Filtered: {adata.n_vars} genes, raw preserved: {adata.raw.n_vars} genes")

# Access raw expression (for genes removed from filtered adata)
raw_df = adata.raw.to_adata().to_df()
# Scanpy uses raw automatically: sc.pl.umap(adata, color="CD3D") looks in raw
```

**Gotcha**: `adata.raw = adata` captures a *reference* at that moment. Subsequent in-place changes to `adata.X` do NOT propagate. Always assign raw *before* normalization/scaling.

### obsm Element Access Patterns

```python
import anndata as ad, numpy as np, pandas as pd

adata = ad.read_h5ad("data.h5ad")
pca = adata.obsm["X_pca"]              # (n_obs, 50) numpy array
pca_10 = adata.obsm["X_pca"][:, :10]   # first 10 PCs

for key in adata.obsm.keys():  # iterate all embeddings
    print(f"  {key}: shape={adata.obsm[key].shape}, dtype={adata.obsm[key].dtype}")

# obsm can hold DataFrames (named columns for protein/ADT data)
adata.obsm["protein"] = pd.DataFrame(
    np.random.rand(adata.n_obs, 5), index=adata.obs_names,
    columns=["CD3", "CD4", "CD8", "CD19", "CD56"])

subset = adata[:100]  # subsetting preserves obsm alignment
print(f"Subset obsm: {subset.obsm['X_pca'].shape}")  # (100, 50)
```

### uns Nested Structure Conventions

```python
adata = ad.read_h5ad("processed.h5ad")

# Neighbors params (written by sc.pp.neighbors)
# {"connectivities_key": "connectivities", "distances_key": "distances",
#  "params": {"n_neighbors": 15, "method": "umap", "metric": "euclidean"}}
print(f"Neighbor params: {adata.uns.get('neighbors', {}).get('params', {})}")

# Color palettes (written by sc.pl.* for categorical columns)
# Key format: "{column_name}_colors" -> list of hex strings
print(f"Palette: {adata.uns.get('cell_type_colors', [])}")
# Override: adata.uns["cell_type_colors"] = ["#e41a1c", "#377eb8", "#4daf4a"]

# Ranking results (written by sc.tl.rank_genes_groups)
# Keys: "params", "names", "scores", "pvals", "pvals_adj", "logfoldchanges"
# Each (except params) is a structured array with group names as fields

# Custom metadata (nested dicts serialize to HDF5 groups)
adata.uns["experiment"] = {"date": "2024-06-01", "protocol": "10x_v3",
                           "sequencing": {"platform": "NovaSeq"}}
```

**Serialization rules**: H5AD supports dicts, numpy arrays, strings, numbers, pandas categoricals. Arbitrary Python objects (sklearn models, lambdas) raise `IORegistryError` on save.

### varp Usage Patterns

Stores gene-gene pairwise relationships (regulatory networks, co-expression).

```python
import numpy as np
from scipy.sparse import csr_matrix

adata = ad.read_h5ad("data.h5ad")
corr = np.corrcoef(adata.X.toarray().T if hasattr(adata.X, 'toarray') else adata.X.T)
corr[np.abs(corr) < 0.5] = 0  # sparsify: keep strong correlations
adata.varp["gene_correlations"] = csr_matrix(corr.astype(np.float32))
print(f"varp shape: {adata.varp['gene_correlations'].shape}")  # (n_vars, n_vars)
```

---

## Advanced I/O Patterns

### Chunked Reading for Very Large Files

```python
import anndata as ad, numpy as np

adata_backed = ad.read_h5ad("huge_atlas.h5ad", backed="r")
chunk_size = 10000
results = []
for start in range(0, adata_backed.n_obs, chunk_size):
    end = min(start + chunk_size, adata_backed.n_obs)
    chunk = adata_backed[start:end].to_memory()
    results.append(np.array(chunk.X.sum(axis=1)).flatten())
all_totals = np.concatenate(results)
print(f"Processed {len(all_totals)} cells in {len(results)} chunks")

# Metadata-guided chunking (process by batch, avoids loading full dataset)
for batch in adata_backed.obs["batch"].unique():
    batch_data = adata_backed[adata_backed.obs["batch"] == batch].to_memory()
    print(f"  Batch {batch}: {batch_data.n_obs} cells")
```

### Backed Mode Write-Back (r+ Mode)

Allows in-place modification of the underlying HDF5 file. Changes to X are written immediately to disk with no extra memory cost.

```python
adata = ad.read_h5ad("data.h5ad", backed="r+")
# Modify X element-wise (writes directly to disk, no extra memory)
# adata.X[0, :] = 0  # written to file immediately

# Modify obs metadata (in-memory until file close)
adata.obs["processed"] = True

# LIMITATIONS: cannot change X shape, sparse format, or add new layers/obsm
# For structural changes: load subset to memory, modify, write new file
adata.file.close()
```

### Format Conversion Gotchas

```python
# Loom -> H5AD: row_attrs->var, col_attrs->obs, layers preserved
# row_graphs/col_graphs NOT mapped to obsp/varp; nested globals lost
adata = ad.read_loom("data.loom")
adata.write_h5ad("converted.h5ad", compression="gzip")

# CSV round-trip loses: sparse format, layers, obsm, obsp, uns, dtypes
# adata.to_df().to_csv("expr.csv")  # only X + index names

# 10X H5 -> H5AD: gene IDs in var_names, symbols in var["gene_symbols"]
adata = ad.read_10x_h5("filtered_feature_bc_matrix.h5")
adata.var_names = adata.var["gene_symbols"]
adata.var_names_make_unique()  # handle duplicate symbols
adata.write_h5ad("from_10x.h5ad", compression="gzip")
```

### Compression Comparison

```python
import anndata as ad, time, os

adata = ad.read_h5ad("data.h5ad")
for comp in ["gzip", "lzf", None]:
    t0 = time.time()
    fname = f"out_{comp or 'none'}.h5ad"
    adata.write_h5ad(fname, compression=comp)
    print(f"{comp or 'none':5s}: {os.path.getsize(fname)/1e6:.1f} MB, {time.time()-t0:.1f}s")
# Typical sparse scRNA-seq (50k x 20k):
# gzip: ~200 MB, ~15s | lzf: ~350 MB, ~5s | none: ~600 MB, ~3s
```

Use `gzip` for archival/sharing, `lzf` for iterative analysis, no compression for temp files. Read speed is similar across all three -- the bottleneck is decompression, which is fast for both gzip and lzf.

### H5AD Internal Structure (HDF5 Layout)

```python
import h5py

with h5py.File("data.h5ad", "r") as f:
    def show(name, obj):
        kind = "dataset" if isinstance(obj, h5py.Dataset) else "group"
        extra = f" {obj.shape} {obj.dtype}" if kind == "dataset" else ""
        print(f"  {name} ({kind}){extra}")
    f.visititems(show)

# Typical layout:
# X/data (nnz,) float32       <- sparse nonzero values
# X/indices (nnz,) int32      <- column indices (CSR)
# X/indptr (n_obs+1,) int32
# obs/cell_type (n_obs,)      <- categorical: codes + categories
# var/                         <- gene metadata
# layers/raw_counts/           <- same sparse structure as X
# obsm/X_pca (n_obs, 50)      <- dense embeddings
# obsp/connectivities/         <- sparse graphs
# uns/neighbors/params/        <- nested groups for dicts
```

---

## Zarr Advanced Patterns

### Cloud Storage (S3/GCS)

Zarr's directory-based format enables direct cloud read/write without downloading entire files.

```python
import anndata as ad

adata = ad.read_h5ad("data.h5ad")
adata.write_zarr("output.zarr")

# S3 (requires s3fs): store = s3fs.S3Map("s3://bucket/data.zarr", s3=s3fs.S3FileSystem())
# GCS (requires gcsfs): store = gcsfs.GCSMap("gs://bucket/data.zarr", gcs=gcsfs.GCSFileSystem())
# Then: adata = ad.read_zarr(store) / adata.write_zarr(store)
# Authenticated: s3 = s3fs.S3FileSystem(key="...", secret="...", endpoint_url="...")
```

### Chunk Size Selection

```python
adata.write_zarr("chunked.zarr", chunks=(1000, adata.n_vars))

# Chunk selection guide:
# Access pattern       | Recommended chunks          | Rationale
# Cell-wise iteration  | (1000-5000, n_vars)         | Full gene profile per read
# Gene-wise iteration  | (n_obs, 500-2000)           | Full cell vector per read
# Random subsets       | (500-1000, 500-1000)        | Balanced for either axis
# Cloud streaming      | Target ~1-10 MB per chunk   | Network transfer overhead
# Very sparse data     | Larger chunks (5000+)       | Sparse overhead per chunk

import zarr
z = zarr.open("chunked.zarr", "r")
if "X" in z and hasattr(z["X"], 'chunks'):
    print(f"Chunk shape: {z['X'].chunks}")
```

---

## Data Type Handling in I/O

### Sparse Format Preservation

```python
from scipy.sparse import csr_matrix, csc_matrix, issparse

adata = ad.read_h5ad("data.h5ad")
print(f"X type: {type(adata.X)}")  # e.g., csr_matrix

# H5AD preserves sparse format across read/write (CSR stays CSR, CSC stays CSC)
adata.write_h5ad("roundtrip.h5ad", compression="gzip")
adata_rt = ad.read_h5ad("roundtrip.h5ad")
print(f"After roundtrip: {type(adata_rt.X)}")  # csr_matrix preserved

# CSR = efficient for row (cell) slicing; CSC = efficient for column (gene) slicing
# Layers preserve sparse format independently (counts can be CSR while X is CSC)
# Zarr also preserves sparse format (stored as data/indices/indptr arrays)
# Force sparse on load: ad.read_h5ad("data.h5ad", as_sparse={"X": "csr"})
```

### Categorical and dtype Preservation

```python
import pandas as pd, numpy as np
from scipy.sparse import issparse

adata = ad.read_h5ad("data.h5ad")

# Categoricals preserved through I/O (stored as codes + categories in HDF5)
adata.strings_to_categoricals()  # convert before save (5-10x memory savings)
adata.obs["stage"] = pd.Categorical(["early", "mid", "late"] * (adata.n_obs // 3),
                                     categories=["early", "mid", "late"], ordered=True)
# Ordered categoricals, booleans, int32/64, float32/64 all preserved

# dtype casting: float64 -> float32 halves memory (no analytical benefit for scRNA-seq)
for slot_name, slot in [("X", adata.X)] + [(k, adata.layers[k]) for k in adata.layers]:
    if hasattr(slot, 'dtype') and slot.dtype == np.float64:
        if slot_name == "X":
            adata.X = adata.X.astype(np.float32)
        else:
            adata.layers[slot_name] = adata.layers[slot_name].astype(np.float32)

for key in adata.obsm:  # PCA/UMAP from sklearn are often float64
    if hasattr(adata.obsm[key], 'dtype') and adata.obsm[key].dtype == np.float64:
        adata.obsm[key] = adata.obsm[key].astype(np.float32)

# Integer counts: use int32 (max ~2B, sufficient for UMI). Avoid int8/int16 (overflow)
print(f"Memory: ~{adata.X.data.nbytes / 1e6:.1f} MB (X nonzeros)")
```

*Condensed from data_structure.md (315 lines) and io_operations.md (405 lines). Retained: raw attribute API and gotchas, obsm access/iteration/DataFrame patterns, uns conventions (neighbors, colors, rankings, serialization rules), varp gene-gene usage, chunked reading, backed r+ write-back with limitations, format conversion gotchas (loom/CSV/10X metadata mapping), compression benchmarks (gzip vs lzf), H5AD internal HDF5 layout, Zarr cloud storage (S3/GCS), chunk size selection guide, sparse format preservation (CSR/CSC roundtrip), categorical/ordered preservation, dtype casting patterns. Omitted: introductory prose on what AnnData is (redundant with SKILL.md Overview), basic slot descriptions (in SKILL.md Key Concepts table), simple read/write examples (in SKILL.md Core API Module 2), basic backed mode open/filter/to_memory (in SKILL.md Core API Module 2 second block), format comparison table (in SKILL.md Key Concepts Storage Formats). Relocated to SKILL.md: core slot table, basic I/O patterns, format comparison, backed mode basics.*
