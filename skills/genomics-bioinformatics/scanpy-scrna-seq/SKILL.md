---
name: "scanpy-scrna-seq"
description: "Single-cell RNA-seq analysis with Scanpy. QC filtering, normalization, HVG selection, PCA, neighborhood graph, UMAP/t-SNE, Leiden clustering, marker gene identification, cell type annotation, and trajectory inference. Use for standard scRNA-seq exploratory workflows."
license: "CC-BY-4.0"
---

# Scanpy Single-Cell RNA-seq Analysis

## Overview

Scanpy is a scalable Python toolkit for analyzing single-cell RNA-seq data built on the AnnData format. This skill covers the end-to-end standard workflow: quality control, normalization, highly variable gene selection, dimensionality reduction, clustering, marker gene identification, and cell type annotation. It produces annotated datasets and publication-quality visualizations.

## When to Use

- Analyzing single-cell RNA-seq count matrices (10X Genomics, h5ad, CSV, loom)
- Performing quality control filtering on scRNA-seq datasets (mitochondrial %, gene counts)
- Running dimensionality reduction: PCA, UMAP, t-SNE
- Identifying cell clusters via Leiden community detection
- Finding differentially expressed marker genes per cluster (Wilcoxon, t-test, logistic regression)
- Annotating cell types from known marker gene panels
- Conducting trajectory inference and pseudotime analysis (PAGA, diffusion pseudotime)
- Generating publication-quality single-cell plots (dot plots, heatmaps, stacked violins)
- Comparing gene expression across experimental conditions within cell types

## Prerequisites

- **Python packages**: `scanpy>=1.10`, `leidenalg`, `igraph`, `anndata`
- **Data requirements**: Gene expression count matrix (cells x genes). Common formats: 10X Cell Ranger output (`filtered_feature_bc_matrix/`), `.h5ad`, `.h5`, `.csv`
- **Environment**: Python 3.9+; 16GB+ RAM recommended for >50k cells

```bash
pip install "scanpy[leiden]" anndata
```

## Workflow

### Step 1: Setup and Data Loading

Configure scanpy settings and read the count matrix into an AnnData object. Ensure gene names are unique.

```python
import scanpy as sc
import numpy as np
import pandas as pd

# Configure settings
sc.settings.verbosity = 3  # errors=0, warnings=1, info=2, hints=3
sc.settings.set_figure_params(dpi=80, facecolor="white")

# Load data — pick the reader matching your format
adata = sc.read_10x_mtx(
    "path/to/filtered_feature_bc_matrix/",
    var_names="gene_symbols",
    cache=True,
)
# Alternatives:
# adata = sc.read_h5ad("data.h5ad")
# adata = sc.read_10x_h5("data.h5")

adata.var_names_make_unique()
print(f"Loaded: {adata.n_obs} cells x {adata.n_vars} genes")
print(f"Sparsity: {1 - adata.X.nnz / (adata.n_obs * adata.n_vars):.1%}")
```

### Step 2: Quality Control

Annotate mitochondrial/ribosomal genes, compute QC metrics, visualize distributions, and filter low-quality cells.

```python
# Annotate gene groups
adata.var["mt"] = adata.var_names.str.startswith("MT-")    # human; use "mt-" for mouse
adata.var["ribo"] = adata.var_names.str.startswith(("RPS", "RPL"))

# Calculate QC metrics
sc.pp.calculate_qc_metrics(
    adata, qc_vars=["mt", "ribo"], percent_top=None, log1p=False, inplace=True
)

# Visualize QC distributions
sc.pl.violin(
    adata,
    ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
    jitter=0.4,
    multi_panel=True,
)
sc.pl.scatter(adata, x="total_counts", y="pct_counts_mt")
sc.pl.scatter(adata, x="total_counts", y="n_genes_by_counts")

# Filter — adjust thresholds based on the QC plots above
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
adata = adata[adata.obs.n_genes_by_counts < 5000, :]  # remove potential doublets
adata = adata[adata.obs.pct_counts_mt < 20, :]         # remove dying cells

print(f"After QC: {adata.n_obs} cells x {adata.n_vars} genes")
```

### Step 3: Normalization and Feature Selection

Normalize library sizes, log-transform, and identify highly variable genes (HVGs). Store raw counts for later differential expression.

```python
# Preserve raw counts in a layer
adata.layers["counts"] = adata.X.copy()

# Normalize to 10,000 counts per cell, then log-transform
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Save normalized data as .raw for visualization
adata.raw = adata

# Identify highly variable genes
sc.pp.highly_variable_genes(adata, n_top_genes=2000, flavor="seurat_v3", layer="counts")
sc.pl.highly_variable_genes(adata)

# Subset to HVGs
adata = adata[:, adata.var.highly_variable]
print(f"HVG subset: {adata.n_obs} cells x {adata.n_vars} genes")
```

### Step 4: Scaling and Regression

Regress out confounders and scale gene expression values. This prepares data for PCA.

```python
# Regress out unwanted sources of variation
sc.pp.regress_out(adata, ["total_counts", "pct_counts_mt"])

# Scale to unit variance, clip extreme values
sc.pp.scale(adata, max_value=10)

print(f"Scaled matrix: mean={adata.X.mean():.4f}, std={adata.X.std():.4f}")
```

### Step 5: Dimensionality Reduction

Compute PCA, inspect the variance ratio elbow plot, then build a neighborhood graph and embed with UMAP.

```python
# PCA
sc.tl.pca(adata, svd_solver="arpack", n_comps=50)
sc.pl.pca_variance_ratio(adata, log=True, n_pcs=50)

# Determine n_pcs from elbow plot (typically 30-50)
n_pcs = 40

# Compute k-nearest neighbor graph
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=n_pcs)

# UMAP embedding
sc.tl.umap(adata)
sc.pl.umap(adata, color=["n_genes_by_counts", "total_counts", "pct_counts_mt"])

print(f"UMAP shape: {adata.obsm['X_umap'].shape}")
```

### Step 6: Clustering

Run Leiden clustering at multiple resolutions and select the best granularity by visual inspection.

```python
# Test multiple resolutions
for res in [0.3, 0.5, 0.8, 1.0, 1.2]:
    sc.tl.leiden(adata, resolution=res, key_added=f"leiden_res{res}", flavor="igraph", n_iterations=2)

# Compare resolutions side-by-side
sc.pl.umap(
    adata,
    color=["leiden_res0.3", "leiden_res0.5", "leiden_res0.8", "leiden_res1.0"],
    ncols=2,
    legend_loc="on data",
)

# Pick final resolution based on biological plausibility
adata.obs["leiden"] = adata.obs["leiden_res0.5"]
n_clusters = adata.obs["leiden"].nunique()
print(f"Selected resolution=0.5: {n_clusters} clusters")
```

### Step 7: Marker Gene Identification

Find differentially expressed genes per cluster using Wilcoxon rank-sum test on raw counts.

```python
# Rank genes per cluster
sc.tl.rank_genes_groups(adata, groupby="leiden", method="wilcoxon", use_raw=True)

# Visualization
sc.pl.rank_genes_groups(adata, n_genes=20, sharey=False)
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5)
sc.pl.rank_genes_groups_heatmap(adata, n_genes=10, use_raw=True, show_gene_labels=True)

# Extract as DataFrame
markers_df = sc.get.rank_genes_groups_df(adata, group=None)
top_markers = markers_df[markers_df["pvals_adj"] < 0.05].groupby("group").head(10)
print(f"Significant markers: {len(top_markers)} genes across {top_markers['group'].nunique()} clusters")
print(top_markers[["group", "names", "logfoldchanges", "pvals_adj"]].head(15))
```

### Step 8: Cell Type Annotation and Export

Assign cell types based on canonical marker genes, visualize, and save all results.

```python
# Define canonical markers (example: human PBMC)
marker_genes = {
    "CD4 T cells":      ["CD3D", "CD3E", "IL7R"],
    "CD8 T cells":      ["CD8A", "CD8B", "GZMK"],
    "B cells":          ["MS4A1", "CD79A", "CD79B"],
    "NK cells":         ["NKG7", "GNLY", "KLRD1"],
    "CD14+ Monocytes":  ["CD14", "LYZ", "S100A9"],
    "FCGR3A+ Monocytes":["FCGR3A", "MS4A7"],
    "Dendritic cells":  ["FCER1A", "CST3"],
    "Platelets":        ["PPBP", "PF4"],
}

# Dot plot — rows = clusters, columns = markers
sc.pl.dotplot(adata, var_names=marker_genes, groupby="leiden", use_raw=True)

# Map clusters → cell types (adjust based on your dot plot)
cluster_to_celltype = {
    "0": "CD4 T cells",
    "1": "CD14+ Monocytes",
    "2": "B cells",
    "3": "CD8 T cells",
    "4": "NK cells",
    "5": "FCGR3A+ Monocytes",
    "6": "Dendritic cells",
    "7": "Platelets",
}
adata.obs["cell_type"] = adata.obs["leiden"].map(cluster_to_celltype).fillna("Unknown")
sc.pl.umap(adata, color="cell_type", legend_loc="on data", frameon=False)

# Save results
adata.write("results/annotated_data.h5ad", compression="gzip")
adata.obs.to_csv("results/cell_metadata.csv")
markers_df.to_csv("results/marker_genes.csv", index=False)
print(f"Saved: {adata.n_obs} cells with {adata.obs['cell_type'].nunique()} cell types")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `min_genes` (filter_cells) | `200` | `100`-`500` | Minimum genes detected per cell; lower keeps more cells |
| `min_cells` (filter_genes) | `3` | `3`-`10` | Minimum cells expressing a gene; higher is stricter |
| `pct_counts_mt` threshold | `20` | `5`-`30` | Max mitochondrial %; tissue-dependent (5% for PBMCs, 20% for tumors) |
| `n_top_genes` (HVG) | `2000` | `1000`-`5000` | Number of highly variable genes; more captures subtle variation |
| `flavor` (HVG) | `"seurat_v3"` | `"seurat"`, `"seurat_v3"`, `"cell_ranger"` | HVG detection algorithm |
| `n_pcs` (neighbors) | `40` | `20`-`50` | Number of PCs for neighbor graph; check elbow plot |
| `n_neighbors` | `15` | `5`-`50` | k for k-NN graph; lower emphasizes local structure |
| `resolution` (leiden) | `0.5` | `0.1`-`2.0` | Clustering granularity; higher → more clusters |
| `method` (rank_genes) | `"wilcoxon"` | `"wilcoxon"`, `"t-test"`, `"logreg"` | DE test; Wilcoxon recommended for publication |
| `target_sum` (normalize) | `1e4` | `1e4`-`1e5` | Target library size per cell |

## Common Recipes

### Recipe: Batch Correction with ComBat

When to use: multiple samples/batches with visible batch effects on the UMAP.

```python
# Requires 'batch' column in adata.obs
sc.pp.combat(adata, key="batch")
# Re-run PCA, neighbors, UMAP, clustering after correction
sc.tl.pca(adata, svd_solver="arpack")
sc.pp.neighbors(adata, n_pcs=40)
sc.tl.umap(adata)
sc.pl.umap(adata, color=["batch", "leiden"])
```

### Recipe: Trajectory Inference with PAGA + Diffusion Pseudotime

When to use: cells follow a developmental continuum rather than discrete clusters.

```python
# PAGA graph abstraction
sc.tl.paga(adata, groups="leiden")
sc.pl.paga(adata, color="leiden", threshold=0.03)

# Reinitialize UMAP with PAGA layout
sc.tl.umap(adata, init_pos="paga")

# Diffusion pseudotime — set root cell
adata.uns["iroot"] = np.flatnonzero(adata.obs["leiden"] == "0")[0]
sc.tl.diffmap(adata)
sc.tl.dpt(adata)
sc.pl.umap(adata, color=["dpt_pseudotime", "leiden"])
```

### Recipe: Publication-Quality Figures

When to use: generating figures for manuscripts or presentations.

```python
sc.settings.set_figure_params(dpi=300, frameon=False, figsize=(5, 5))

# UMAP with custom palette
sc.pl.umap(
    adata, color="cell_type",
    palette="Set2",
    legend_loc="on data",
    legend_fontsize=10,
    legend_fontoutline=2,
    title="",
    save="_celltype_publication.pdf",
)

# Stacked violin plot of top markers
flat_markers = [g for genes in marker_genes.values() for g in genes[:2]]
sc.pl.stacked_violin(
    adata, var_names=flat_markers, groupby="cell_type",
    use_raw=True, swap_axes=True,
    save="_markers_violin.pdf",
)
```

### Recipe: Differential Expression Between Conditions

When to use: comparing treated vs control within a specific cell type.

```python
# Subset to cell type of interest
adata_t = adata[adata.obs["cell_type"] == "CD4 T cells"].copy()

# DE between conditions
sc.tl.rank_genes_groups(adata_t, groupby="condition", groups=["treated"], reference="control", method="wilcoxon", use_raw=True)
sc.pl.rank_genes_groups_volcano(adata_t, groups=["treated"])

de_results = sc.get.rank_genes_groups_df(adata_t, group="treated")
sig_genes = de_results[de_results["pvals_adj"] < 0.05]
print(f"Significant DE genes: {len(sig_genes)}")
```

## Expected Outputs

- `results/annotated_data.h5ad` — Full AnnData with embeddings (PCA, UMAP), cluster labels, cell type annotations, and raw counts layer
- `results/cell_metadata.csv` — Per-cell table: barcode, cluster, cell type, QC metrics (n_genes, total_counts, pct_mt)
- `results/marker_genes.csv` — DE genes per cluster: gene name, log fold change, adjusted p-value
- QC figures: violin plots (n_genes, total_counts, pct_mt), scatter plots
- Embedding figures: UMAP colored by cluster, cell type, QC metrics, pseudotime
- Marker figures: dot plot, heatmap, stacked violin of canonical markers

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: leidenalg` | Leiden package not installed | `pip install leidenalg igraph` |
| `MemoryError` during PCA | Dense matrix exceeds RAM | Use `sc.pp.pca(adata, chunked=True, chunk_size=20000)` |
| UMAP shows single blob | Over-filtering or too few HVGs | Relax QC thresholds; increase `n_top_genes` to 3000-5000 |
| Too many/few clusters | Resolution mismatch | Sweep `resolution` from 0.1 to 2.0 and compare UMAPs |
| `KeyError: 'MT-'` not found | Wrong species prefix | Use `mt-` (lowercase) for mouse, `MT-` for human |
| Batch effects dominate UMAP | Uncorrected technical variation | Apply ComBat recipe or use Harmony/scVI for integration |
| `adata.raw is None` error | Forgot to save raw before subsetting | Set `adata.raw = adata` after normalization, before HVG subset |
| Marker genes non-specific | Resolution too low merging cell types | Increase resolution or use `logistic_regression` method |
| Slow `regress_out` | Large cell count | Skip regress_out; use `sc.pp.scale()` alone (often sufficient) |
| `ValueError` in `rank_genes_groups` | Cluster with too few cells | Remove clusters with <10 cells before DE: `adata = adata[adata.obs.groupby('leiden').filter(lambda x: len(x)>=10).index]` |

## Bundled Resources

This skill includes reference files for deeper lookup. Read these on demand when the main SKILL.md needs more detail.

### references/api_reference.md
Quick-lookup table of all scanpy functions organized by module (sc.pp.*, sc.tl.*, sc.pl.*), with full signatures, common parameters, and AnnData structure reference. **Use when**: you need the exact function name or parameter for a specific operation.

### references/plotting_guide.md
Comprehensive visualization guide: QC plots, UMAP styling, marker gene plots (dot plot, heatmap, stacked violin), trajectory plots, multi-panel figures, publication customization, and color palette recommendations. **Use when**: creating figures for publications or presentations.

### references/standard_workflow.md
Detailed step-by-step reference for each pipeline stage with decision points, parameter rationale, and alternative approaches (MAD-based filtering, scran normalization, automated annotation). **Use when**: performing a full analysis from scratch and needing deeper guidance than the Workflow section above.

## References

- [Scanpy documentation](https://scanpy.readthedocs.io/) — Official API reference and tutorials (BSD-3)
- [Scanpy PBMC3k tutorial](https://scanpy-tutorials.readthedocs.io/en/latest/pbmc3k.html) — Canonical walkthrough (BSD-3)
- [Galaxy Training: Clustering 3K PBMCs with Scanpy](https://training.galaxyproject.org/training-material/topics/single-cell/) — Step-by-step tutorial (CC-BY)
- [Luecken & Theis (2019)](https://doi.org/10.15252/msb.20188746) — "Current best practices in single-cell RNA-seq analysis: a tutorial", *Mol Syst Biol*
- [Heumos et al. (2023)](https://doi.org/10.1038/s41576-023-00586-w) — "Best practices for single-cell analysis across modalities", *Nat Rev Genet*
- [scverse ecosystem](https://scverse.org/) — Related tools: anndata, scvi-tools, squidpy, cellrank
