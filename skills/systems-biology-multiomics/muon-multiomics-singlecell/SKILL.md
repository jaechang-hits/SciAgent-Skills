---
name: "muon-multiomics-singlecell"
description: "Multi-modal single-cell analysis with muon/MuData. Joint RNA+ATAC (10x Multiome), CITE-seq (RNA+protein), other multi-omics. MuData holds per-modality AnnData with shared obs. WNN joint embedding, per-modality preprocessing, MOFA factor analysis. Use scanpy-scrna-seq for single-modality RNA; use muon when combining 2+ omics from the same cells."
license: "BSD-3-Clause"
---

# muon — Multi-Modal Single-Cell Analysis

## Overview

muon is a Python framework for multi-modal single-cell data analysis that extends the AnnData ecosystem. Its core data structure, `MuData`, holds multiple `AnnData` objects (one per modality: RNA, ATAC, protein, etc.) with shared observation and variable axes, enabling coordinated operations across all modalities. muon provides modality-specific preprocessing routines (TF-IDF and LSI for ATAC, CLR normalization for surface proteins), Weighted Nearest Neighbor (WNN) graph construction for joint dimensionality reduction, and cross-modal analysis tools. It integrates directly with scanpy, scvi-tools, and MOFA+ for a complete multi-omics single-cell workflow.

## When to Use

- Analyzing 10x Genomics Multiome data (simultaneous RNA + ATAC from the same nuclei)
- Processing CITE-seq experiments (RNA + surface protein from the same cells)
- Building joint UMAP embeddings that integrate signals from two or more modalities via WNN
- Preprocessing ATAC-seq modalities (TF-IDF normalization, LSI dimensionality reduction)
- Normalizing surface protein data with centered log-ratio (CLR) normalization
- Performing cross-modal feature linkage (associating ATAC peaks with nearby gene expression)
- Applying MOFA+ factor analysis across multiple omics layers within a unified container
- Use **scanpy-scrna-seq** instead when analyzing a single RNA-seq modality without any co-measured omics
- Use **scvi-tools (MultiVI / totalVI)** when you need probabilistic deep generative batch correction across modalities

## Prerequisites

- **Python packages**: `muon>=0.1.6`, `scanpy>=1.10`, `anndata>=0.10`, `numpy`, `scipy`, `pandas`, `matplotlib`, `leidenalg`
- **Data requirements**: 10x Multiome h5 or h5mu files, or per-modality AnnData objects (cells x features) sharing the same `obs_names`
- **Environment**: Python 3.9+; 16 GB+ RAM for datasets >50k cells; optional `mofapy2` for MOFA factor analysis

```bash
pip install "muon[all]" "scanpy[leiden]" anndata
# Optional: for MOFA+ integration
pip install mofapy2
```

## Quick Start

```python
import muon as mu
import scanpy as sc
import numpy as np
import anndata as ad
import pandas as pd

# Simulate a small RNA + ATAC MuData object (200 cells)
np.random.seed(42)
n_cells = 200
rna  = ad.AnnData(np.abs(np.random.negative_binomial(5, 0.3, (n_cells, 2000))).astype(float),
                  obs=pd.DataFrame(index=[f"cell_{i}" for i in range(n_cells)]),
                  var=pd.DataFrame(index=[f"gene_{j}" for j in range(2000)]))
atac = ad.AnnData(np.abs(np.random.negative_binomial(2, 0.5, (n_cells, 5000))).astype(float),
                  obs=rna.obs.copy(),
                  var=pd.DataFrame(index=[f"peak_{j}" for j in range(5000)]))

mdata = mu.MuData({"rna": rna, "atac": atac})
print(mdata)
# MuData object with n_obs × n_vars = 200 × 7000
#   2 modalities
#     rna: 200 × 2000
#     atac: 200 × 5000

# Minimal preprocessing
sc.pp.normalize_total(mdata["rna"], target_sum=1e4)
sc.pp.log1p(mdata["rna"])
sc.pp.highly_variable_genes(mdata["rna"], n_top_genes=500)
sc.pp.pca(mdata["rna"])

mu.atac.pp.tfidf(mdata["atac"])
mu.atac.tl.lsi(mdata["atac"])

# WNN joint embedding
mu.pp.neighbors(mdata, key_added="wnn",
                use_rep={"rna": "X_pca", "atac": "X_lsi"})
sc.tl.umap(mdata, neighbors_key="wnn")
sc.tl.leiden(mdata, neighbors_key="wnn", key_added="leiden_wnn")
print(f"Clusters: {mdata.obs['leiden_wnn'].nunique()}")
```

## Core API

### Module 1: MuData Creation and I/O

`MuData` is the central container: a dictionary of `AnnData` modalities plus shared `obs` and `var` slots. The `mdata.obs` DataFrame merges per-modality observation metadata with a modality prefix for ambiguous columns.

```python
import muon as mu
import anndata as ad
import numpy as np
import pandas as pd

# --- Build from per-modality AnnData objects ---
n_cells = 300
rna  = ad.AnnData(np.abs(np.random.negative_binomial(5, 0.3, (n_cells, 3000))).astype(float),
                  obs=pd.DataFrame(index=[f"cell_{i}" for i in range(n_cells)]),
                  var=pd.DataFrame(index=[f"gene_{j}" for j in range(3000)]))
prot = ad.AnnData(np.abs(np.random.randn(n_cells, 30)) + 3,
                  obs=rna.obs.copy(),
                  var=pd.DataFrame(index=[f"protein_{j}" for j in range(30)]))

mdata = mu.MuData({"rna": rna, "protein": prot})
print(mdata)
# Access individual modalities
print(mdata.mod["rna"])        # AnnData: 300 × 3000
print(mdata["rna"])            # same shorthand
print(mdata.obs.head())        # shared observation metadata
print(mdata.obs_names[:5])     # cell barcodes

# Save and load
mdata.write("multiome_data.h5mu")
mdata2 = mu.read("multiome_data.h5mu")
print(f"Loaded: {mdata2.n_obs} cells, {mdata2.n_mod} modalities")
```

```python
# --- Load from 10x Multiome h5 file ---
# mdata = mu.read_10x_h5("filtered_feature_bc_matrix.h5")
# Produces MuData with mdata["rna"] and mdata["atac"] modalities

# --- Subsetting by cells or features ---
# Select high-quality cells (e.g., after QC)
mask = np.ones(mdata.n_obs, dtype=bool)  # replace with actual QC mask
mdata_filtered = mdata[mask].copy()
print(f"After filtering: {mdata_filtered.n_obs} cells")

# Propagate obs mask to each modality
mu.pp.intersect_obs(mdata)   # ensures obs consistency across modalities
```

### Module 2: RNA Modality Preprocessing

Standard scRNA-seq preprocessing applied to `mdata["rna"]` using scanpy functions. The RNA modality is preprocessed identically to a standalone scanpy workflow but operates on the slice of the MuData container.

```python
import scanpy as sc
import numpy as np

# Assume mdata["rna"] has raw integer counts
rna = mdata["rna"]

# QC metrics
sc.pp.calculate_qc_metrics(rna, percent_top=None, log1p=False, inplace=True)
rna.obs["pct_counts_mt"] = rna[:, rna.var_names.str.startswith("MT-")].X.sum(axis=1).A1 / rna.obs["total_counts"] * 100

# Filter cells and genes
min_genes, max_genes, max_mt = 200, 5000, 20
sc.pp.filter_cells(rna, min_genes=min_genes)
sc.pp.filter_genes(rna, min_cells=5)
rna = rna[(rna.obs["n_genes_by_counts"] < max_genes) &
          (rna.obs["pct_counts_mt"] < max_mt)].copy()
print(f"RNA after QC: {rna.n_obs} cells × {rna.n_vars} genes")

# Normalize and log-transform
sc.pp.normalize_total(rna, target_sum=1e4)
sc.pp.log1p(rna)

# Highly variable genes
sc.pp.highly_variable_genes(rna, n_top_genes=3000, flavor="seurat_v3",
                             batch_key=None)
print(f"HVGs: {rna.var['highly_variable'].sum()}")

# PCA on HVGs
sc.pp.pca(rna, n_comps=50, use_highly_variable=True)
print(f"PCA embedding shape: {rna.obsm['X_pca'].shape}")
# Update slice in MuData
mdata.mod["rna"] = rna
```

### Module 3: ATAC Modality Preprocessing

ATAC-seq modalities require a different normalization strategy. TF-IDF (term frequency–inverse document frequency) normalizes peak accessibility across cells and peaks; LSI (latent semantic indexing, equivalent to truncated SVD after TF-IDF) produces a low-dimensional embedding. The first LSI component typically captures sequencing depth rather than biology and is excluded.

```python
# Assume mdata["atac"] contains raw binary or integer peak accessibility counts
atac = mdata["atac"]

# Basic QC: filter low-coverage cells and low-frequency peaks
sc.pp.calculate_qc_metrics(atac, percent_top=None, log1p=False, inplace=True)
sc.pp.filter_cells(atac, min_genes=200)     # min peaks detected
sc.pp.filter_genes(atac, min_cells=10)      # min cells a peak appears in
print(f"ATAC after QC: {atac.n_obs} cells × {atac.n_vars} peaks")

# TF-IDF normalization (log(TF) * log(IDF) scaling)
mu.atac.pp.tfidf(atac, scale_factor=1e4)
print("TF-IDF normalization complete")
print(f"ATAC data range: [{atac.X.min():.2f}, {atac.X.max():.2f}]")

# LSI dimensionality reduction (truncated SVD on TF-IDF matrix)
mu.atac.tl.lsi(atac, n_comps=50, use_highly_variable=False)
# LSI component 1 correlates with sequencing depth — exclude it
# mu.atac.tl.lsi sets X_lsi starting from component 2 by default
print(f"LSI embedding shape: {atac.obsm['X_lsi'].shape}")

# Update modality in MuData
mdata.mod["atac"] = atac
```

### Module 4: WNN Graph and Joint Embedding

Weighted Nearest Neighbor (WNN) integrates multiple modality embeddings by learning per-cell, per-modality weights. Cells with high-quality RNA signal receive higher RNA weight; cells with cleaner ATAC signal receive higher ATAC weight. The resulting WNN graph is used for UMAP layout and Leiden clustering.

```python
# Compute per-modality neighbor graphs first (optional but enables modality-specific UMAPs)
mu.pp.neighbors(mdata["rna"],  use_rep="X_pca",  n_neighbors=30, key_added="neighbors")
mu.pp.neighbors(mdata["atac"], use_rep="X_lsi",  n_neighbors=30, key_added="neighbors")

# WNN joint neighbor graph across modalities
mu.pp.neighbors(
    mdata,
    key_added="wnn",
    use_rep={"rna": "X_pca", "atac": "X_lsi"},
    n_neighbors=30,
    random_state=42,
)
print("WNN graph built. Keys:", list(mdata.obsp.keys()))
# Expected: ['wnn_connectivities', 'wnn_distances']

# UMAP from WNN graph
sc.tl.umap(mdata, neighbors_key="wnn", random_state=42)
print(f"UMAP embedding shape: {mdata.obsm['X_umap'].shape}")

# Leiden clustering from WNN graph
sc.tl.leiden(mdata, neighbors_key="wnn", resolution=0.5, key_added="leiden_wnn")
n_clusters = mdata.obs["leiden_wnn"].nunique()
print(f"Leiden WNN clustering: {n_clusters} clusters at resolution 0.5")
```

### Module 5: Visualization

muon extends scanpy's plotting interface with modality-aware functions. `mu.pl.embedding()` colors joint UMAP embeddings by features from any modality; `sc.pl.umap()` with `color` pointing to modality-prefixed feature names (e.g., `"rna:CD3E"`) is also supported.

```python
import matplotlib.pyplot as plt

# Joint UMAP colored by cluster assignment
sc.pl.umap(mdata, color="leiden_wnn", title="WNN Leiden clusters",
           legend_loc="on data", show=False)
plt.savefig("wnn_umap_clusters.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved wnn_umap_clusters.png")

# Color by RNA gene expression on joint UMAP
sc.pl.umap(mdata, color=["rna:CD3E", "rna:CD19", "rna:CD14"],
           use_raw=False, vmax="p99", show=False, ncols=3)
plt.savefig("wnn_umap_markers.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved wnn_umap_markers.png")
```

```python
# Per-modality scatter / embedding plots
mu.pl.embedding(mdata, basis="X_umap", color="leiden_wnn",
                show=False)
plt.savefig("embedding_clusters.png", dpi=150, bbox_inches="tight")
plt.close()

# Violin plot: RNA QC metrics per cluster
sc.pl.violin(mdata["rna"], keys=["n_genes_by_counts", "total_counts"],
             groupby=mdata.obs.loc[mdata["rna"].obs_names, "leiden_wnn"],
             rotation=90, show=False)
plt.savefig("rna_qc_by_cluster.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved rna_qc_by_cluster.png")
```

### Module 6: Cross-Modal Analysis

Cross-modal analysis links features across modalities — for example, associating ATAC peak accessibility near a gene's promoter with its RNA expression, or applying MOFA+ to find shared latent factors.

```python
# --- Peak-to-gene distance annotation ---
# Annotate ATAC peaks with nearest gene (requires genomic coordinates in var)
# mdata["atac"].var should contain columns: chrom, chromStart, chromEnd
# mu.atac.tl.rank_peaks_groups(mdata, groupby="leiden_wnn")  # differential peaks

# --- Differentially accessible peaks per cluster ---
atac = mdata["atac"]
# Transfer cluster labels from MuData obs to ATAC obs
atac.obs["cluster"] = mdata.obs.loc[atac.obs_names, "leiden_wnn"].values
sc.tl.rank_genes_groups(atac, groupby="cluster", method="wilcoxon",
                        use_raw=False)
top_peaks = sc.get.rank_genes_groups_df(atac, group="0").head(5)
print("Top differential peaks in cluster 0:")
print(top_peaks[["names", "logfoldchanges", "pvals_adj"]])
```

```python
# --- MOFA+ factor analysis on MuData ---
# Requires: pip install mofapy2
try:
    mu.tl.mofa(mdata, n_factors=10, seed=42,
               use_obs="all", outfile="mofa_model.hdf5")
    # Factor scores stored in mdata.obsm["X_mofa"]
    print(f"MOFA factors: {mdata.obsm['X_mofa'].shape}")
    # Variance explained per factor per modality
    # Inspect with mdata.uns["mofa"]
except ImportError:
    print("Install mofapy2 to enable MOFA factor analysis")
```

## Common Workflows

### Workflow 1: Full 10x Multiome (RNA + ATAC) Joint WNN Clustering

**Goal**: Process paired RNA and ATAC data from 10x Genomics Multiome, build a WNN joint embedding, cluster cells, and identify RNA marker genes per cluster.

```python
import muon as mu
import scanpy as sc
import numpy as np
import anndata as ad
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Simulate 10x Multiome-like data (replace with mu.read_10x_h5()) ---
np.random.seed(0)
n_cells = 400
cell_ids = [f"AAACGAATC{i:05d}-1" for i in range(n_cells)]
# Simulate two cell types with distinct expression/accessibility
labels = np.array(["typeA"] * 200 + ["typeB"] * 200)

rna_counts = np.abs(np.random.negative_binomial(6, 0.35, (n_cells, 2000))).astype(float)
rna_counts[:200, :100] += 10   # typeA marker genes
rna_counts[200:, 100:200] += 10  # typeB marker genes

atac_counts = np.abs(np.random.binomial(1, 0.05, (n_cells, 50000))).astype(float)
atac_counts[:200, :5000] += 1   # typeA accessible peaks
atac_counts[200:, 5000:10000] += 1  # typeB accessible peaks

rna  = ad.AnnData(rna_counts,
                  obs=pd.DataFrame({"cell_type": labels}, index=cell_ids),
                  var=pd.DataFrame(index=[f"gene_{j}" for j in range(2000)]))
atac = ad.AnnData(atac_counts,
                  obs=pd.DataFrame({"cell_type": labels}, index=cell_ids),
                  var=pd.DataFrame(index=[f"peak_{j}" for j in range(50000)]))

mdata = mu.MuData({"rna": rna, "atac": atac})
print(f"Loaded: {mdata}")

# --- 2. RNA preprocessing ---
sc.pp.filter_cells(mdata["rna"], min_genes=50)
sc.pp.filter_genes(mdata["rna"], min_cells=5)
sc.pp.normalize_total(mdata["rna"], target_sum=1e4)
sc.pp.log1p(mdata["rna"])
sc.pp.highly_variable_genes(mdata["rna"], n_top_genes=500)
sc.pp.pca(mdata["rna"], n_comps=30, use_highly_variable=True)
print(f"RNA PCA: {mdata['rna'].obsm['X_pca'].shape}")

# --- 3. ATAC preprocessing: TF-IDF + LSI ---
sc.pp.filter_cells(mdata["atac"], min_genes=100)
sc.pp.filter_genes(mdata["atac"], min_cells=5)
mu.atac.pp.tfidf(mdata["atac"])
mu.atac.tl.lsi(mdata["atac"], n_comps=30)
print(f"ATAC LSI: {mdata['atac'].obsm['X_lsi'].shape}")

# --- 4. Per-modality neighbors (optional for modality-specific plots) ---
mu.pp.neighbors(mdata["rna"],  use_rep="X_pca", n_neighbors=15, key_added="neighbors")
mu.pp.neighbors(mdata["atac"], use_rep="X_lsi",  n_neighbors=15, key_added="neighbors")

# --- 5. WNN joint neighbor graph ---
mu.pp.intersect_obs(mdata)   # align obs after per-modality filtering
mu.pp.neighbors(mdata, key_added="wnn",
                use_rep={"rna": "X_pca", "atac": "X_lsi"},
                n_neighbors=15, random_state=42)

# --- 6. UMAP + Leiden clustering ---
sc.tl.umap(mdata, neighbors_key="wnn", random_state=42)
sc.tl.leiden(mdata, neighbors_key="wnn", resolution=0.5, key_added="leiden_wnn")
print(f"Clusters: {mdata.obs['leiden_wnn'].value_counts().to_dict()}")

# --- 7. Marker genes per cluster ---
sc.tl.rank_genes_groups(mdata["rna"],
                        groupby=mdata.obs.loc[mdata["rna"].obs_names, "leiden_wnn"],
                        method="wilcoxon", use_raw=False)
top_markers = sc.get.rank_genes_groups_df(mdata["rna"], group="0").head(5)
print("Top RNA markers for cluster 0:")
print(top_markers[["names", "logfoldchanges", "pvals_adj"]])

# --- 8. Visualization ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sc.pl.umap(mdata, color="leiden_wnn", ax=axes[0], show=False, title="WNN clusters")
sc.pl.umap(mdata, color="rna:gene_0",  ax=axes[1], show=False, title="gene_0 expression",
           use_raw=False, vmax="p99")
plt.tight_layout()
plt.savefig("multiome_wnn_pipeline.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved multiome_wnn_pipeline.png")
```

### Workflow 2: CITE-seq (RNA + Surface Protein) Analysis

**Goal**: Process CITE-seq data with paired RNA and antibody-derived tag (ADT/protein) counts. Normalize proteins with CLR, annotate cell types from protein markers, and build a joint UMAP.

```python
import muon as mu
import scanpy as sc
import numpy as np
import anndata as ad
import pandas as pd
import matplotlib.pyplot as plt
from scipy.sparse import csr_matrix

np.random.seed(1)
n_cells = 350
cell_ids = [f"CITESEQ_{i:04d}" for i in range(n_cells)]

# Simulate RNA + protein modalities
# Three cell types: T-cells (CD3+CD4+), B-cells (CD19+CD20+), Monocytes (CD14+CD16+)
n_t, n_b, n_mono = 120, 130, 100
labels = ["Tcell"] * n_t + ["Bcell"] * n_b + ["Monocyte"] * n_mono

rna_mat = np.abs(np.random.negative_binomial(4, 0.4, (n_cells, 1500))).astype(float)
rna_mat[:n_t, :50] += 15       # T-cell RNA markers
rna_mat[n_t:n_t+n_b, 50:100] += 15   # B-cell RNA markers
rna_mat[n_t+n_b:, 100:150] += 15     # Monocyte RNA markers

# 20 surface proteins: first 5 T-cell, next 5 B-cell, next 5 Monocyte, rest baseline
prot_mat = np.abs(np.random.normal(2, 0.5, (n_cells, 20)))
prot_mat[:n_t, :5] += 8          # CD3, CD4, CD5, CD7, CD8 for T-cells
prot_mat[n_t:n_t+n_b, 5:10] += 8  # CD19, CD20, CD22, CD24, CD79 for B-cells
prot_mat[n_t+n_b:, 10:15] += 8    # CD14, CD16, CD64, CD11b, HLA-DR for Monocytes

protein_names = ["CD3", "CD4", "CD5", "CD7", "CD8",
                 "CD19", "CD20", "CD22", "CD24", "CD79a",
                 "CD14", "CD16", "CD64", "CD11b", "HLA-DR",
                 "CD25", "CD56", "CD45RA", "CD45RO", "IgG-ctrl"]

rna = ad.AnnData(csr_matrix(rna_mat),
                 obs=pd.DataFrame({"cell_type": labels}, index=cell_ids),
                 var=pd.DataFrame(index=[f"gene_{j}" for j in range(1500)]))
prot = ad.AnnData(prot_mat,
                  obs=pd.DataFrame({"cell_type": labels}, index=cell_ids),
                  var=pd.DataFrame(index=protein_names))

mdata = mu.MuData({"rna": rna, "protein": prot})
print(mdata)

# --- RNA preprocessing ---
sc.pp.normalize_total(mdata["rna"], target_sum=1e4)
sc.pp.log1p(mdata["rna"])
sc.pp.highly_variable_genes(mdata["rna"], n_top_genes=500)
sc.pp.pca(mdata["rna"], n_comps=30, use_highly_variable=True)

# --- Protein CLR normalization (Centered Log-Ratio) ---
# CLR normalizes each protein across cells: log(x / geometric_mean(x))
mu.prot.pp.clr(mdata["protein"])
print("Protein CLR normalization applied")
print(f"Protein data range: [{mdata['protein'].X.min():.2f}, {mdata['protein'].X.max():.2f}]")

# PCA on protein modality
sc.pp.pca(mdata["protein"], n_comps=min(15, prot.n_vars - 1))

# --- WNN joint embedding ---
mu.pp.neighbors(mdata, key_added="wnn",
                use_rep={"rna": "X_pca", "protein": "X_pca"},
                n_neighbors=20, random_state=0)
sc.tl.umap(mdata, neighbors_key="wnn", random_state=0)
sc.tl.leiden(mdata, neighbors_key="wnn", resolution=0.4, key_added="leiden_wnn")

# --- Protein-based cell type annotation ---
# Compute mean CLR protein per cluster
prot_df = pd.DataFrame(
    mdata["protein"].X,
    index=mdata["protein"].obs_names,
    columns=protein_names
)
prot_df["cluster"] = mdata.obs.loc[mdata["protein"].obs_names, "leiden_wnn"].values
cluster_means = prot_df.groupby("cluster").mean()
print("\nMean CLR protein per cluster:")
print(cluster_means[["CD3", "CD4", "CD19", "CD14"]].round(2))

# --- Visualization ---
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
sc.pl.umap(mdata, color="leiden_wnn",   ax=axes[0], show=False, title="WNN Leiden")
sc.pl.umap(mdata, color="protein:CD3",  ax=axes[1], show=False, title="CD3 (CLR)",
           use_raw=False, vmax="p99")
sc.pl.umap(mdata, color="protein:CD19", ax=axes[2], show=False, title="CD19 (CLR)",
           use_raw=False, vmax="p99")
plt.tight_layout()
plt.savefig("citeseq_joint_umap.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved citeseq_joint_umap.png")

# --- Dot plot: protein markers per cluster ---
sc.pl.dotplot(mdata["protein"],
              var_names=["CD3", "CD4", "CD19", "CD20", "CD14", "CD16"],
              groupby=mdata.obs.loc[mdata["protein"].obs_names, "leiden_wnn"],
              show=False)
plt.savefig("citeseq_protein_dotplot.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved citeseq_protein_dotplot.png")
```

## Key Parameters

| Parameter | Module / Function | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `n_neighbors` | `mu.pp.neighbors()` | `30` | `10`–`100` | Neighborhood size for graph; lower = finer local structure |
| `use_rep` | `mu.pp.neighbors()` | `None` (auto) | dict of `{modality: embedding_key}` | Which embedding per modality to use for WNN |
| `key_added` | `mu.pp.neighbors()` | `"neighbors"` | any string | Key under which graph is stored; use `"wnn"` for joint graphs |
| `n_comps` | `sc.pp.pca()`, `mu.atac.tl.lsi()` | `50` | `10`–`100` | Number of reduced dimensions; 30–50 typical |
| `resolution` | `sc.tl.leiden()` | `1.0` | `0.1`–`2.0` | Clustering granularity; lower = fewer, larger clusters |
| `scale_factor` | `mu.atac.pp.tfidf()` | `1e4` | `1e3`–`1e5` | TF scaling constant before log transform |
| `n_factors` | `mu.tl.mofa()` | `10` | `5`–`50` | Number of MOFA latent factors; use elbow on variance explained |
| `target_sum` | `sc.pp.normalize_total()` | `1e4` | `1e3`–`1e6` | Library size normalization target per cell (RNA) |
| `n_top_genes` | `sc.pp.highly_variable_genes()` | varies | `1000`–`5000` | Number of highly variable genes to retain for PCA |

## Best Practices

1. **Align obs before WNN**: After per-modality QC filtering, cell counts across modalities may differ. Always call `mu.pp.intersect_obs(mdata)` before WNN to ensure every modality has the same cell set.
   ```python
   mu.pp.intersect_obs(mdata)
   print(f"Shared cells after intersect: {mdata.n_obs}")
   ```

2. **Drop LSI component 1 from ATAC**: The first LSI component captures sequencing depth (total counts per cell) rather than biological signal. `mu.atac.tl.lsi()` stores all components in `X_lsi`, so verify that component 1 correlates with `log_total_counts` before using `X_lsi` in WNN; if so, restrict to `X_lsi[:, 1:]`.
   ```python
   import numpy as np, pandas as pd
   atac = mdata["atac"]
   corr = np.corrcoef(atac.obsm["X_lsi"][:, 0],
                      np.log1p(atac.obs["total_counts"]))[0, 1]
   print(f"LSI1 vs log_counts correlation: {corr:.3f}")
   # If |corr| > 0.9, exclude component 1:
   # atac.obsm["X_lsi"] = atac.obsm["X_lsi"][:, 1:]
   ```

3. **Use `key_added="wnn"` consistently**: Always name the joint graph `"wnn"` and pass `neighbors_key="wnn"` to all downstream `sc.tl.umap()`, `sc.tl.leiden()`, and `sc.tl.paga()` calls. Mixing `neighbors_key` values silently uses the wrong graph.

4. **CLR normalization for proteins, not log-normalization**: Antibody-derived tag (ADT) counts from CITE-seq have a different noise model than RNA. Use `mu.prot.pp.clr()` for per-protein CLR normalization. Do NOT apply `sc.pp.normalize_total()` + `sc.pp.log1p()` to the protein modality.

5. **Store raw RNA counts before normalization**: Before any normalization, store the raw RNA counts in `mdata["rna"].layers["counts"]` and set `mdata["rna"].raw = mdata["rna"]`. This is required for downstream differential expression tests and scvi-tools integration.
   ```python
   import scipy.sparse as sp
   mdata["rna"].layers["counts"] = mdata["rna"].X.copy()
   # Store pre-normalization snapshot
   mdata["rna"].raw = mdata["rna"]
   ```

6. **Match WNN embedding dimensions**: The RNA PCA and ATAC LSI embeddings passed to WNN should have comparable dimensionality (e.g., both 30 or 50 components). Mismatched dimensions do not cause errors but can down-weight the smaller modality.

## Common Recipes

### Recipe: Compute Per-Cluster Modality Weights from WNN

When to use: Inspect which cells rely more on RNA vs ATAC signal in the WNN graph. High RNA weight in a cluster suggests cleaner RNA data; high ATAC weight suggests stronger chromatin accessibility signal.

```python
# WNN stores per-cell modality weights in mdata.obsm after mu.pp.neighbors()
# Key name: "{key_added}_weights" — check available keys
print([k for k in mdata.obsm.keys() if "wnn" in k.lower()])

# If weights are stored (depends on muon version):
if "wnn_weights" in mdata.obsm:
    weights_df = pd.DataFrame(
        mdata.obsm["wnn_weights"],
        index=mdata.obs_names,
        columns=["rna_weight", "atac_weight"]
    )
    weights_df["cluster"] = mdata.obs["leiden_wnn"].values
    print(weights_df.groupby("cluster").mean().round(3))
else:
    # Proxy: compare RNA vs ATAC PCA explained variance per cell
    rna_var  = np.var(mdata["rna"].obsm["X_pca"],  axis=1)
    atac_var = np.var(mdata["atac"].obsm["X_lsi"], axis=1)
    mdata.obs["rna_signal_proxy"]  = rna_var / (rna_var + atac_var)
    mdata.obs["atac_signal_proxy"] = atac_var / (rna_var + atac_var)
    print(mdata.obs[["rna_signal_proxy", "atac_signal_proxy", "leiden_wnn"]].groupby("leiden_wnn").mean().round(3))
```

### Recipe: Export Cluster Labels Back to Per-Modality AnnData

When to use: After joint WNN clustering, copy shared cluster labels back into each modality's `.obs` for modality-specific downstream analyses (e.g., differential peaks within clusters).

```python
# Copy joint cluster labels into each modality's obs
for mod_name in mdata.mod:
    mod_adata = mdata[mod_name]
    shared_cells = mod_adata.obs_names
    mod_adata.obs["leiden_wnn"] = mdata.obs.loc[shared_cells, "leiden_wnn"].values
    print(f"{mod_name}: added leiden_wnn, {mod_adata.obs['leiden_wnn'].nunique()} clusters")

# Now run modality-specific differential analysis per cluster
sc.tl.rank_genes_groups(mdata["rna"],  groupby="leiden_wnn",
                        method="wilcoxon", use_raw=False)
sc.tl.rank_genes_groups(mdata["atac"], groupby="leiden_wnn",
                        method="wilcoxon", use_raw=False)
print("Differential features computed for both modalities")
```

### Recipe: Convert MuData to Concatenated AnnData for scvi-tools

When to use: MultiVI and totalVI in scvi-tools require a concatenated AnnData with modality identity tracked in `var`. This recipe prepares the input for these models.

```python
# Concatenate RNA and ATAC into a single AnnData with modality column in var
rna_adata  = mdata["rna"].copy()
atac_adata = mdata["atac"].copy()

rna_adata.var["modality"]  = "Gene Expression"
atac_adata.var["modality"] = "Peaks"

# Restore raw counts for scvi-tools (requires integer counts)
# Ensure mdata["rna"].layers["counts"] and mdata["atac"].X are integer
import anndata as ad
combined = ad.concat([rna_adata, atac_adata], axis=1, merge="unique")
combined.obs = mdata.obs.loc[combined.obs_names].copy()
print(f"Combined AnnData: {combined.n_obs} cells × {combined.n_vars} features")
print(combined.var["modality"].value_counts())
# Use combined with scvi.model.MULTIVI.setup_anndata(combined, ...)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `KeyError: 'rna'` when building MuData | Modality key not set or loaded from file without expected names | Check `mdata.mod.keys()`. When loading 10x h5 files, use `mu.read_10x_h5()` which auto-names modalities `"rna"` and `"atac"` |
| `ValueError: obs_names mismatch` during WNN | Cells filtered differently per modality leaving mismatched obs | Call `mu.pp.intersect_obs(mdata)` after per-modality QC to harmonize cell sets |
| UMAP/Leiden uses wrong graph | Multiple neighbor graphs exist; function uses default key `"neighbors"` | Always pass `neighbors_key="wnn"` explicitly to `sc.tl.umap()` and `sc.tl.leiden()` |
| LSI component 1 dominates ATAC embedding | First component captures sequencing depth, not biology | Compute correlation of `X_lsi[:, 0]` with `log_total_counts`; if |r| > 0.9, use `X_lsi[:, 1:]` |
| `mu.atac.pp.tfidf` raises sparse matrix error | Input matrix is dense or wrong dtype | Convert first: `mdata["atac"].X = scipy.sparse.csr_matrix(mdata["atac"].X.astype(float))` |
| CLR normalization produces NaN for proteins | Zero counts in a cell for all proteins | Filter cells with `sc.pp.filter_cells(mdata["protein"], min_genes=1)` before CLR |
| `mu.tl.mofa()` fails with missing mofapy2 | mofapy2 not installed | `pip install mofapy2`; ensure `muon` version ≥ 0.1.5 for MOFA integration |
| Memory error for large ATAC peak matrices | ATAC matrices (50k+ peaks × 10k+ cells) exceed RAM | Use `sc.pp.highly_variable_genes()` to select top 50k peaks first, or load in chunks |

## Related Skills

- **scanpy-scrna-seq** — single-modality RNA analysis; use as the foundation for the RNA preprocessing steps within muon
- **scvi-tools-single-cell** — deep generative multi-modal integration (MultiVI for RNA+ATAC, totalVI for CITE-seq); use when probabilistic batch correction across samples is needed
- **mofaplus-multi-omics** — multi-omics factor analysis; `mu.tl.mofa()` calls mofapy2 internally and stores factors in MuData
- **anndata-data-structure** — AnnData fundamentals; each MuData modality is a standard AnnData object
- **deeptools-ngs-analysis** — upstream ATAC-seq BAM → bigWig normalization before peak calling
- **macs3-peak-calling** — produces the peak BED files used to generate the ATAC AnnData count matrix

## References

- [muon documentation](https://muon.readthedocs.io/) — official docs, tutorials, API reference
- [muon GitHub (scverse)](https://github.com/scverse/muon) — source code, issues, examples
- [Bredikhin et al. Genome Biology 2022](https://doi.org/10.1186/s13059-021-02577-8) — muon/MuData publication
- [10x Genomics Multiome analysis guide](https://muon-tutorials.readthedocs.io/en/latest/single-cell-rna-atac/pbmc10k/1-Gene-Expression-Processing.html) — step-by-step Multiome tutorial in muon
- [WNN method (Hao et al. Cell 2021)](https://doi.org/10.1016/j.cell.2021.04.048) — original Weighted Nearest Neighbor paper from Seurat v4
