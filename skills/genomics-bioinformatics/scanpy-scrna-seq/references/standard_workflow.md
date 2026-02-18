# Standard Scanpy Workflow — Detailed Reference

Step-by-step reference for the complete scRNA-seq analysis pipeline. Read this when performing a full analysis from scratch. Each step includes detailed parameter explanations and decision points.

## 1. Data Loading

```python
import scanpy as sc
import numpy as np
import pandas as pd

sc.settings.verbosity = 3
sc.settings.set_figure_params(dpi=80, facecolor="white")

# 10X Cell Ranger output (most common)
adata = sc.read_10x_mtx(
    "path/to/filtered_feature_bc_matrix/",
    var_names="gene_symbols",  # Use gene symbols instead of Ensembl IDs
    cache=True,                # Cache for faster re-reading
)

# Other formats
# adata = sc.read_h5ad("data.h5ad")
# adata = sc.read_10x_h5("data.h5")  # Single HDF5 from Cell Ranger
# adata = sc.read_csv("counts.csv").T  # CSV (transpose if genes=rows)

adata.var_names_make_unique()  # Append suffix to duplicate gene names
```

**Decision point**: If merging multiple samples, concatenate AnnData objects first:
```python
adatas = [sc.read_10x_mtx(f"sample_{i}/") for i in range(1, 4)]
adata = adatas[0].concatenate(adatas[1:], batch_key="sample")
```

## 2. Quality Control

### Annotate Gene Groups

```python
# Human mitochondrial genes
adata.var["mt"] = adata.var_names.str.startswith("MT-")

# Ribosomal genes (optional but useful)
adata.var["ribo"] = adata.var_names.str.startswith(("RPS", "RPL"))

# Hemoglobin genes (optional, for blood contamination)
adata.var["hb"] = adata.var_names.str.contains("^HB[^(P)]", case=False)

sc.pp.calculate_qc_metrics(adata, qc_vars=["mt", "ribo", "hb"],
                            percent_top=None, log1p=False, inplace=True)
```

**For mouse data**: Use `mt-` (lowercase), `Rps`/`Rpl`, `Hb`.

### Visualize and Filter

```python
# Visualize distributions
sc.pl.violin(adata, ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
             jitter=0.4, multi_panel=True)

# Decide thresholds from plots — common starting points:
#   min_genes: 200 (removes empty droplets)
#   max_genes: 5000 (removes potential doublets)
#   pct_mt: 20% for tumors, 5% for PBMCs, 10% general

sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
adata = adata[adata.obs.n_genes_by_counts < 5000, :]
adata = adata[adata.obs.pct_counts_mt < 20, :]
```

**MAD-based filtering** (more data-driven alternative):
```python
from scipy.stats import median_abs_deviation

def is_outlier(adata, metric, nmads=5):
    M = adata.obs[metric]
    return (M < np.median(M) - nmads * median_abs_deviation(M)) | \
           (M > np.median(M) + nmads * median_abs_deviation(M))

adata.obs["outlier"] = (
    is_outlier(adata, "log1p_total_counts", 5)
    | is_outlier(adata, "log1p_n_genes_by_counts", 5)
    | is_outlier(adata, "pct_counts_in_top_20_genes", 5)
)
adata.obs["mt_outlier"] = is_outlier(adata, "pct_counts_mt", 3)
adata = adata[(~adata.obs.outlier) & (~adata.obs.mt_outlier)].copy()
```

## 3. Normalization

```python
# Store raw counts
adata.layers["counts"] = adata.X.copy()

# Standard normalization: library-size + log
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Save for later use in DE and visualization
adata.raw = adata
```

**Alternative**: scran pooling normalization (requires R interop) or `sc.pp.normalize_total(adata, target_sum=None)` for median-based.

## 4. Highly Variable Gene Selection

```python
# seurat_v3 flavor (recommended, works on raw counts)
sc.pp.highly_variable_genes(adata, n_top_genes=2000, flavor="seurat_v3", layer="counts")

# seurat flavor (works on normalized data)
# sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)

sc.pl.highly_variable_genes(adata)
adata = adata[:, adata.var.highly_variable]
```

**How to choose n_top_genes**:
- 2000: standard for most analyses
- 3000-5000: when you need more resolution (rare cell types)
- 1000: for very heterogeneous data to reduce noise

## 5. Scaling

```python
# Optional: regress out confounders (slow for large datasets)
sc.pp.regress_out(adata, ["total_counts", "pct_counts_mt"])

# Scale to unit variance
sc.pp.scale(adata, max_value=10)
```

**When to skip regress_out**:
- Large datasets (>100k cells): too slow
- When using scVI or Harmony for batch correction
- When confounders are minimal

## 6. PCA

```python
sc.tl.pca(adata, svd_solver="arpack", n_comps=50)
sc.pl.pca_variance_ratio(adata, log=True, n_pcs=50)
```

**Choosing n_pcs**: Look at the elbow plot. Typically 30-50 PCs capture most biological variation. Using too few loses signal; too many adds noise. When in doubt, use 40.

## 7. Neighborhood Graph

```python
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=40)
```

**n_neighbors effects**:
- Low (5-10): fine-grained structure, may split real populations
- Medium (15-20): balanced (default)
- High (30-50): smoother, may merge distinct populations

## 8. UMAP

```python
sc.tl.umap(adata)

# Alternative: initialize with PAGA for trajectory data
# sc.tl.paga(adata, groups="leiden")
# sc.tl.umap(adata, init_pos="paga")
```

## 9. Clustering

```python
# Try multiple resolutions
for res in [0.3, 0.5, 0.8, 1.0, 1.2]:
    sc.tl.leiden(adata, resolution=res, key_added=f"leiden_res{res}",
                 flavor="igraph", n_iterations=2)

sc.pl.umap(adata, color=[f"leiden_res{r}" for r in [0.3, 0.5, 0.8, 1.0]], ncols=2)
```

**Choosing resolution**: Compare with known biology. More clusters isn't always better — only split when biological markers support it.

## 10. Marker Genes

```python
sc.tl.rank_genes_groups(adata, groupby="leiden", method="wilcoxon", use_raw=True)
markers_df = sc.get.rank_genes_groups_df(adata, group=None)
```

**Method comparison**:
- `wilcoxon`: recommended for publications, non-parametric
- `t-test`: fast, parametric, good for exploratory analysis
- `logreg`: multivariate, identifies most discriminative genes

## 11. Cell Type Annotation

Map clusters to cell types based on canonical markers and DE results:

```python
# Inspect marker expression per cluster
sc.pl.dotplot(adata, var_names=marker_dict, groupby="leiden", use_raw=True)

# Assign
cluster_map = {"0": "CD4 T cells", "1": "Monocytes", ...}
adata.obs["cell_type"] = adata.obs["leiden"].map(cluster_map).fillna("Unknown")
```

**Automated annotation tools** (alternatives):
- `celltypist`: pre-trained models for immune cells
- `sc.tl.ingest()`: project onto a reference dataset
- `scvi-tools` + `scANVI`: deep-learning-based annotation

## 12. Save

```python
adata.write("results/annotated.h5ad", compression="gzip")
adata.obs.to_csv("results/cell_metadata.csv")
markers_df.to_csv("results/markers.csv", index=False)
```
