---
name: "harmony-batch-correction"
description: "Harmony batch correction for scRNA-seq and other omics. Removes batch effects from PCA embeddings while preserving biology. Run after PCA, before UMAP. Scales to millions of cells. Python (harmonypy, scanpy) and R (Seurat)."
license: "MIT"
---

# Harmony Batch Correction

## Overview

Harmony is a fast, scalable algorithm for batch integration in single-cell data. It takes a PCA embedding (cells × PCs) as input and returns a corrected embedding from which batch effects have been regressed out via iterative soft-clustering and per-cluster linear regression. The corrected embedding is then used to compute neighbors, UMAP, and downstream clustering — the raw count matrix is never modified. Harmony works for single-cell RNA-seq, ATAC-seq, and other omics modalities where a PCA-like embedding is available.

## When to Use

- Integrating scRNA-seq datasets from different samples, donors, sequencing runs, or experimental batches that should contain the same cell types
- Removing technical variation (library preparation protocol, 10x chemistry version, sequencing depth, sequencing platform) while preserving biological differences between cell types and conditions
- Performing fast, scalable batch correction on datasets with millions of cells where deep generative model training would be prohibitively slow
- Correcting for multiple confounding variables simultaneously (batch, donor, sequencing platform, tissue processing protocol)
- Preparing a corrected embedding for UMAP visualization, Leiden clustering, or label transfer without modifying the gene expression count matrix
- Use **scVI/scvi-tools** instead when you need probabilistic batch correction with a variational autoencoder (deep learning), differential expression with uncertainty estimates, or multi-modal integration (RNA + protein)
- Use **BBKNN** instead when you want graph-based integration that avoids constructing a corrected embedding altogether and directly builds a cross-batch nearest-neighbor graph
- Use **Seurat Integration / CCA** (R) instead when you are already in a Seurat workflow and prefer anchor-based integration methods

## Prerequisites

- **Python packages**: `harmonypy`, `scanpy>=1.10`, `leidenalg`, `igraph`, `anndata`, `pandas`, `matplotlib`
- **R packages** (optional): `harmony`, `Seurat>=4.0` (for R workflow in Step 7)
- **Data requirements**: AnnData object with raw counts, batch/sample metadata in `adata.obs`, and PCA embedding already computed (`adata.obsm["X_pca"]`)
- **Environment**: Python 3.9+; 8 GB RAM sufficient for up to ~500k cells; linear memory scaling

```bash
pip install harmonypy "scanpy[leiden]" anndata pandas matplotlib
```

```r
# R installation (for Step 7 / Seurat integration)
install.packages("harmony")
# If using Seurat:
install.packages("Seurat")
```

## Quick Start

Minimal pipeline — load preprocessed data, run Harmony via scanpy, produce UMAP:

```python
import scanpy as sc

# Load preprocessed AnnData (counts normalized, HVGs selected, PCA run)
adata = sc.read_h5ad("preprocessed.h5ad")   # must have adata.obs["batch"]

# Run Harmony batch correction (corrects adata.obsm["X_pca"] → "X_pca_harmony")
sc.external.pp.harmony_integrate(adata, key="batch")

# Build neighborhood graph on corrected embedding, then UMAP
sc.pp.neighbors(adata, use_rep="X_pca_harmony")
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.5)

# Visualize
sc.pl.umap(adata, color=["batch", "leiden"], ncols=2)
print(f"Clusters: {adata.obs['leiden'].nunique()} | Cells: {adata.n_obs}")
```

## Workflow

### Step 1: Quality Control and Preprocessing

Filter, normalize, select highly variable genes (HVGs), and run PCA. Harmony is applied to the PCA embedding produced here.

```python
import scanpy as sc
import numpy as np

sc.settings.set_figure_params(dpi=80, facecolor="white")

# Load multi-batch data — adata.obs must contain a batch column
adata = sc.read_h5ad("multi_batch_counts.h5ad")
# Alternatively, concatenate multiple AnnData objects:
# adata = sc.concat([adata1, adata2, adata3], label="batch",
#                   keys=["batch1", "batch2", "batch3"])

print(f"Loaded: {adata.n_obs} cells × {adata.n_vars} genes")
print(f"Batches: {adata.obs['batch'].value_counts().to_dict()}")

# QC: annotate mitochondrial genes and filter low-quality cells
adata.var["mt"] = adata.var_names.str.startswith("MT-")
sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True)
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_cells(adata, max_genes=6000)
sc.pp.filter_genes(adata, min_cells=3)
adata = adata[adata.obs["pct_counts_mt"] < 20].copy()
print(f"After QC: {adata.n_obs} cells × {adata.n_vars} genes")

# Normalize and log-transform (store raw counts first)
adata.layers["counts"] = adata.X.copy()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Select HVGs and compute PCA
sc.pp.highly_variable_genes(adata, n_top_genes=3000, batch_key="batch")
sc.pp.pca(adata, n_comps=50, use_highly_variable=True)
print(f"PCA shape: {adata.obsm['X_pca'].shape}")  # (n_cells, 50)
```

### Step 2: Run Harmony via Scanpy Integration

The scanpy wrapper calls `harmonypy` under the hood and stores the corrected embedding in `adata.obsm["X_pca_harmony"]`.

```python
import scanpy as sc

# Run Harmony — corrects adata.obsm["X_pca"] in-place and stores result as "X_pca_harmony"
sc.external.pp.harmony_integrate(
    adata,
    key="batch",           # obs column with batch labels
    basis="X_pca",         # source embedding (default)
    adjusted_basis="X_pca_harmony",  # destination key (default)
    max_iter_harmony=20,   # maximum Harmony iterations (default 10; increase for complex batches)
    theta=2.0,             # diversity penalty per batch variable (default 2)
    sigma=0.1,             # width of soft-clustering Gaussian kernel
    random_state=42,
)

print(f"Corrected embedding: {adata.obsm['X_pca_harmony'].shape}")
# Expected: (n_cells, 50) — same shape as X_pca
```

### Step 3: Run Harmony via harmonypy Directly

Use the lower-level `harmonypy` API when you need finer control, access to the HarmonyObject, or integration outside of scanpy.

```python
import harmonypy
import pandas as pd
import numpy as np

# Extract PCA embedding and metadata
pca_embeddings = adata.obsm["X_pca"]                  # numpy array (n_cells, n_PCs)
meta_data = adata.obs[["batch", "donor"]].copy()       # DataFrame with batch variables

# Run Harmony
ho = harmonypy.run_harmony(
    pca_embeddings,
    meta_data,
    vars_use=["batch"],        # list of columns to correct for
    theta=2.0,                 # diversity penalty strength (per variable)
    sigma=0.1,                 # soft-clustering bandwidth
    nclust=None,               # number of clusters; None → auto (min(100, n_cells/30))
    tau=0,                     # protection against over-clustering small clusters
    block_size=0.05,           # fraction of cells per mini-batch
    max_iter_harmony=20,
    max_iter_kmeans=20,
    epsilon_cluster=1e-5,
    epsilon_harmony=1e-4,
    random_state=42,
    verbose=True,
)

corrected = ho.Z_corr.T   # (n_cells, n_PCs) corrected embedding
adata.obsm["X_pca_harmony"] = corrected
print(f"Harmony converged. Corrected embedding shape: {corrected.shape}")
```

### Step 4: Compute Neighbors and UMAP on Harmony Embedding

Always use `use_rep="X_pca_harmony"` so that downstream graph construction is based on the corrected embedding, not the original PCA.

```python
import scanpy as sc

# Build k-nearest neighbor graph using corrected embedding
sc.pp.neighbors(
    adata,
    n_neighbors=15,          # number of neighbors (15-30 typical for scRNA-seq)
    n_pcs=None,              # use all PCs in the embedding
    use_rep="X_pca_harmony", # IMPORTANT: use corrected embedding
    random_state=42,
)

# Compute UMAP for visualization
sc.tl.umap(adata, min_dist=0.3, spread=1.0, random_state=42)

print(f"UMAP computed: {adata.obsm['X_umap'].shape}")  # (n_cells, 2)
```

### Step 5: Leiden Clustering on Harmony-Corrected Graph

Clustering is performed on the neighbor graph built from the Harmony-corrected embedding in Step 4.

```python
import scanpy as sc

# Run Leiden community detection at multiple resolutions
for resolution in [0.3, 0.5, 0.8]:
    sc.tl.leiden(adata, resolution=resolution, key_added=f"leiden_{resolution}")

# Select final resolution
adata.obs["leiden"] = adata.obs["leiden_0.5"]

print(f"Clusters at resolution 0.5: {adata.obs['leiden'].nunique()}")
print(adata.obs["leiden"].value_counts().head())

# Find marker genes per cluster
sc.tl.rank_genes_groups(adata, groupby="leiden", method="wilcoxon", n_genes=50)
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5, groupby="leiden")
```

### Step 6: Evaluate Batch Correction

Plot UMAP colored by batch and by cell type / cluster to visually confirm batch effects are removed while biological structure is preserved.

```python
import scanpy as sc
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Before correction: color by batch using uncorrected PCA-based UMAP
sc.pp.neighbors(adata, use_rep="X_pca", key_added="uncorrected_neighbors", random_state=42)
sc.tl.umap(adata, neighbors_key="uncorrected_neighbors", random_state=42)
adata.obsm["X_umap_uncorrected"] = adata.obsm["X_umap"].copy()

# Restore Harmony UMAP
sc.pp.neighbors(adata, use_rep="X_pca_harmony", random_state=42)
sc.tl.umap(adata, random_state=42)

# Panel 1: Corrected UMAP colored by batch
sc.pl.umap(adata, color="batch", title="Harmony: colored by batch",
           ax=axes[0], show=False)

# Panel 2: Corrected UMAP colored by leiden cluster
sc.pl.umap(adata, color="leiden", title="Harmony: Leiden clusters",
           ax=axes[1], show=False)

# Panel 3: Uncorrected UMAP colored by batch (for comparison)
sc.pl.embedding(adata, basis="X_umap_uncorrected", color="batch",
                title="Uncorrected PCA: batch separation",
                ax=axes[2], show=False)

plt.tight_layout()
plt.savefig("harmony_batch_evaluation.png", dpi=150, bbox_inches="tight")
plt.show()
print("Batch evaluation figure saved to harmony_batch_evaluation.png")
```

### Step 7: R Integration with Seurat

For users working in R, Harmony integrates directly with Seurat via `RunHarmony()`.

```r
library(Seurat)
library(harmony)

# Load Seurat object with batch metadata in metadata column "batch"
seurat_obj <- readRDS("multi_batch_seurat.rds")

# Ensure PCA is computed
seurat_obj <- NormalizeData(seurat_obj)
seurat_obj <- FindVariableFeatures(seurat_obj, nfeatures = 3000)
seurat_obj <- ScaleData(seurat_obj)
seurat_obj <- RunPCA(seurat_obj, npcs = 50)

# Run Harmony — corrects the "pca" reduction and adds "harmony" reduction
seurat_obj <- RunHarmony(
  seurat_obj,
  group.by.vars = "batch",   # metadata column(s) to correct for
  dims.use = 1:30,           # number of PCs to use
  theta = 2,                 # diversity penalty
  sigma = 0.1,               # soft-clustering bandwidth
  max.iter.harmony = 20,
  plot_convergence = TRUE,   # plot objective function convergence
  verbose = TRUE
)

# Build neighbor graph and UMAP using Harmony embedding
seurat_obj <- FindNeighbors(seurat_obj, reduction = "harmony", dims = 1:30)
seurat_obj <- FindClusters(seurat_obj, resolution = 0.5)
seurat_obj <- RunUMAP(seurat_obj, reduction = "harmony", dims = 1:30)

# Visualize
DimPlot(seurat_obj, reduction = "umap", group.by = "batch")
DimPlot(seurat_obj, reduction = "umap", group.by = "seurat_clusters")

cat(sprintf("Clusters: %d | Cells: %d\n",
            length(unique(seurat_obj$seurat_clusters)),
            ncol(seurat_obj)))
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `theta` | `2.0` | `0`–`10` | Diversity penalty per batch variable. Higher values force more mixing; set to 0 to disable penalty. Increase to `4`–`6` for very uneven batch sizes. |
| `sigma` | `0.1` | `0.01`–`0.5` | Bandwidth of the soft-clustering Gaussian kernel. Smaller values → sharper cluster assignments; larger values → smoother. Rarely needs changing. |
| `nclust` | `None` (auto) | `5`–`200` | Number of soft clusters used for correction. Auto-set to `min(100, n_cells/30)`. Increase for datasets with many rare cell types. |
| `max_iter_harmony` | `10` | `5`–`50` | Maximum Harmony iterations. Increase to `20`–`30` for datasets with strong or complex batch effects where convergence is slow. |
| `tau` | `0` | `0`–`10` | Overclustering protection. Positive values penalize very small clusters; use `tau=5` when tiny populations are over-splitting. |
| `n_neighbors` (scanpy) | `15` | `5`–`50` | Number of nearest neighbors for the post-Harmony graph. Increase for larger datasets (>100k cells) to stabilize clusters. |
| `block_size` | `0.05` | `0.01`–`0.1` | Fraction of cells per mini-batch for the K-means step. Smaller values are faster but less stable; default is usually appropriate. |

## Key Concepts

### How Harmony Works

Harmony correction proceeds in three repeated phases until convergence:

1. **Soft K-means assignment**: Each cell is softly assigned to `K` clusters based on Euclidean distance in PC space, weighted by the batch-diversity penalty `theta`.
2. **Per-cluster linear regression**: Within each cluster, a linear correction is estimated for each batch variable and applied to the cluster's cells.
3. **Convergence check**: The objective function (mixture model likelihood + diversity penalty) is evaluated; iterations stop when improvement < `epsilon_harmony`.

The corrected embedding lives in the same PC space as the input PCA but with batch-specific directions subtracted. The raw count matrix (`adata.X`) and all gene-level information are untouched.

### PCA Before Harmony

Harmony assumes the input PCA was computed with `batch_key` awareness. In scanpy, always pass `batch_key="batch"` to `sc.pp.highly_variable_genes()` before PCA so that HVGs are selected independently per batch and then intersected, preventing batch-specific HVGs from dominating the embedding.

### Embedding Not Counts

Harmony corrects the embedding, not the count matrix. Differential expression analysis should still use the raw or normalized counts (stored in `adata.layers["counts"]` or `adata.raw`), not the corrected PCs.

## Common Recipes

### Recipe: Multi-Variable Correction (Batch + Donor + Platform)

Correct for multiple confounding variables simultaneously by passing a list to `vars_use`. Each variable gets its own diversity penalty `theta`.

```python
import harmonypy
import pandas as pd

# Prepare metadata with multiple batch variables
meta_data = adata.obs[["batch", "donor", "platform"]].copy()

# Run Harmony correcting for all three variables
ho = harmonypy.run_harmony(
    adata.obsm["X_pca"],
    meta_data,
    vars_use=["batch", "donor", "platform"],  # correct for all three
    theta=[2.0, 1.0, 2.0],  # per-variable diversity penalty
    # theta can also be a scalar (same for all variables)
    max_iter_harmony=30,
    random_state=42,
    verbose=True,
)

adata.obsm["X_pca_harmony"] = ho.Z_corr.T
print(f"Multi-variable correction complete. Shape: {adata.obsm['X_pca_harmony'].shape}")

# Verify batch mixing improved for all variables
import scanpy as sc
sc.pp.neighbors(adata, use_rep="X_pca_harmony")
sc.tl.umap(adata, random_state=42)
sc.pl.umap(adata, color=["batch", "donor", "platform"], ncols=3)
```

### Recipe: Diagnose Over-Correction with Marker Genes

If Harmony over-corrects (merges biologically distinct populations), canonical marker genes will lose cell-type specificity on the UMAP. Check this before downstream analysis.

```python
import scanpy as sc
import matplotlib.pyplot as plt

# Define known canonical marker genes for your tissue
marker_genes = {
    "T cells": ["CD3D", "CD3E", "TRAC"],
    "B cells": ["MS4A1", "CD79A", "CD19"],
    "NK cells": ["GNLY", "NKG7", "KLRD1"],
    "Monocytes": ["LYZ", "CD14", "CST3"],
    "Dendritic cells": ["FCER1A", "CLEC10A"],
}

# Plot canonical markers on the Harmony-corrected UMAP
all_markers = [g for genes in marker_genes.values() for g in genes
               if g in adata.var_names]

sc.pl.umap(
    adata,
    color=all_markers[:6],    # plot first 6 markers
    ncols=3,
    vmax="p99",               # clip color scale at 99th percentile
    frameon=False,
    save="_marker_genes.png",
)

# If markers look diffuse or don't separate cell types cleanly,
# reduce theta (e.g., from 2.0 to 1.0) or reduce max_iter_harmony
print("If marker gene expression is diffuse across clusters, reduce theta.")
print("If batch effects remain visible, increase theta or max_iter_harmony.")
```

### Recipe: Save and Reload Harmony-Corrected AnnData

Save the corrected object with all embeddings for downstream analysis without re-running Harmony.

```python
import scanpy as sc

# Save with all embeddings
adata.write_h5ad("harmony_corrected.h5ad", compression="gzip")
print(f"Saved to harmony_corrected.h5ad ({adata.n_obs} cells)")

# Reload and verify
adata_loaded = sc.read_h5ad("harmony_corrected.h5ad")
print(f"Loaded. Keys in obsm: {list(adata_loaded.obsm.keys())}")
# Expected: ['X_pca', 'X_pca_harmony', 'X_umap']
```

## Expected Outputs

| Output | Type | Description |
|--------|------|-------------|
| `adata.obsm["X_pca_harmony"]` | `np.ndarray` (cells × PCs) | Harmony-corrected PCA embedding; input for neighbors/UMAP/clustering |
| `adata.obsm["X_umap"]` | `np.ndarray` (cells × 2) | 2D UMAP coordinates from corrected embedding |
| `adata.obs["leiden"]` | `pd.Categorical` | Leiden cluster labels |
| `adata.uns["neighbors"]` | `dict` | KNN graph metadata (`connectivities`, `distances`) |
| `adata.uns["rank_genes_groups"]` | `dict` | Per-cluster marker gene statistics (scores, p-values, log fold changes) |
| `harmony_batch_evaluation.png` | PNG figure | Side-by-side UMAP panels: batch labels, cluster labels, uncorrected comparison |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Harmony does not converge (max iterations reached) | Strong batch effects or too few iterations | Increase `max_iter_harmony` to 30–50; check that PCA was computed with `batch_key` HVG selection |
| Batches still separate on UMAP after correction | `theta` too low or too few PCs | Increase `theta` to 3–4; use more PCs (40–50); ensure `use_rep="X_pca_harmony"` is set in `sc.pp.neighbors()` |
| Over-correction: biologically distinct populations merge | `theta` too high or too many iterations | Reduce `theta` to 1.0; reduce `max_iter_harmony`; verify marker gene expression is cell-type-specific |
| `KeyError: 'X_pca_harmony'` in `sc.pp.neighbors()` | Step 2 (harmony_integrate) not run yet | Run `sc.external.pp.harmony_integrate(adata, key="batch")` before calling `sc.pp.neighbors()` |
| `AttributeError` or import error for `sc.external.pp.harmony_integrate` | `harmonypy` not installed | Run `pip install harmonypy`; verify `import harmonypy` succeeds |
| `ValueError: vars_use not in meta_data columns` | Batch column name mismatch | Check `adata.obs.columns` and confirm the column name passed to `key=` exists |
| Memory error on large datasets (>1M cells) | Full PCA matrix loaded into memory | Use harmonypy directly with chunked PCA; consider subsampling to 200k cells for parameter tuning first |
| Clusters appear identical before and after correction | PCA was not computed with HVGs selected per batch | Re-run `sc.pp.highly_variable_genes(adata, batch_key="batch")` and `sc.pp.pca()` before Harmony |

## References

- [Harmony paper — Korsunsky et al., Nature Methods 2019](https://doi.org/10.1038/s41592-019-0619-0) — original algorithm, benchmarks against MNN, Seurat, BBKNN, Scanorama
- [harmonypy (Python) — GitHub](https://github.com/slowkow/harmonypy) — Python port by Kamil Slowikowski
- [harmony (R) — GitHub](https://github.com/immunogenomics/harmony) — original R implementation by Immunogenomics Lab
- [Harmony documentation — Broad Institute](https://portals.broadinstitute.org/harmony/) — tutorials and parameter guidance
- [Scanpy external API — harmony_integrate](https://scanpy.readthedocs.io/en/stable/generated/scanpy.external.pp.harmony_integrate.html) — scanpy wrapper documentation
- [Single-cell best practices — batch correction chapter](https://www.sc-best-practices.org/preprocessing_visualization/batch_correction.html) — benchmarks and when to use each method
