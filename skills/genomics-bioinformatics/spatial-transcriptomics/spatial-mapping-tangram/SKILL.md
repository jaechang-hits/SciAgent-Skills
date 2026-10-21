---
name: "spatial-mapping-tangram"
description: "Tangram mapping of scRNA-seq cells onto spatial transcriptomics (Visium, Slide-seq, MERFISH, Xenium): marker-based training genes, cell-to-spot probability matrix in cells or clusters mode, per-spot cell type proportions via tg.project_cell_annotations, and spatial maps of the projected types. Core mapping skill of the Tangram set: mapping quality checks -> spatial-mapping-validation; projecting/imputing genes -> scrna-spatial-gene-imputation; constrained mode with histology segmentation on Visium -> spatial-transcriptomics-deconvolution-tangram."
license: "CC-BY-4.0"
---

# Spatial Mapping with Tangram

## Overview

Tangram fits a cell-by-spot probability matrix so that the expression of the
mapped single cells reproduces the spatial expression of shared genes. From
that matrix this skill derives cell type proportions per spot. The reference
must come from the same tissue (ideally a biological replicate) and must share
a set of informative genes with the spatial panel. Output: the mapping matrix,
per-spot cell type proportions and maps, and preprocessed objects that the
validation and gene projection skills reuse.

## When to Use

- Placing scRNA-seq cell types onto a Visium, Slide-seq, MERFISH or Xenium section
- Getting per-spot cell type proportions without a histology image
- Building the cell-to-spot mapping that gene imputation and validation start from
- Mapping one reference onto several sections for a consistent comparison
- Labelling single-cell-resolution spatial cells from a reference as a second opinion
- Use `spatial-transcriptomics-deconvolution-cell2location` instead when you need posterior uncertainty for spot abundances
- For constrained mapping with nuclei segmented from the H&E image, use `spatial-transcriptomics-deconvolution-tangram`

## Prerequisites

- **Spatial data**: AnnData with `obsm["spatial"]` (Visium: Step 1 of
  `spatial-transcriptomics-deconvolution-cell2location`; Xenium: Step 1 of
  `spatial-transcriptomics-cell-type-annotation`)
- **Reference**: scRNA-seq with a cell type column, tissue- and state-matched
  (search/download: Steps 3-4 of `spatial-transcriptomics-cell-type-annotation`)
- **Compute**: Tangram needs PyTorch (large download); CPU works,
  `mode="cells"` is much faster on a GPU
- **Python packages**: `tangram-sc`, `squidpy`, `scanpy`

```bash
pip install tangram-sc squidpy scanpy
```

## Workflow

1. Load spatial data and reference
2. Normalise and keep the raw-count density prior
3. Select training genes and run `tg.pp_adatas`
4. Map cells to space
5. Project cell type annotations
6. Plot and save

### Step 1: Load Data

The demo uses the Tangram tutorial data (mouse cortex Visium + scRNA-seq);
squidpy downloads it on first use and caches it.

```python
import numpy as np
import pandas as pd
import scanpy as sc
import squidpy as sq
import tangram as tg

USE_DEMO = True
if USE_DEMO:
    adata_sp = sq.datasets.visium_fluo_adata_crop()
    adata_sp = adata_sp[adata_sp.obs["cluster"].isin([f"Cortex_{i}" for i in range(1, 5)])].copy()
    adata_sc = sq.datasets.sc_mouse_cortex()
    CELL_TYPE_KEY = "cell_subclass"
else:
    adata_sp = sc.read_h5ad("spatial.h5ad")      # obsm["spatial"] required
    adata_sc = sc.read_h5ad("reference.h5ad")
    CELL_TYPE_KEY = "cell_type"

print(adata_sp)
print(adata_sc.obs[CELL_TYPE_KEY].value_counts())
shared = adata_sc.var_names.str.lower().intersection(adata_sp.var_names.str.lower())
print(f"shared genes: {len(shared)}")
```

### Step 2: Normalise, Keep the Density Prior

Use the same normalisation on both sides. `tg.pp_adatas` computes its
`rna_count_based` prior from `adata_sp.X`, which `normalize_total` flattens, so
take the per-spot total from raw counts first.

```python
def is_raw_counts(ad):
    x = ad.X[: min(500, ad.n_obs)]
    x = x.toarray() if hasattr(x, "toarray") else np.asarray(x)
    return np.allclose(x, np.round(x)) and x.max() > 20

if "total_counts" in adata_sp.obs:
    totals = adata_sp.obs["total_counts"].to_numpy(dtype=float)
else:
    totals = np.asarray(adata_sp.X.sum(1)).ravel().astype(float)   # raw if X is raw
density_prior = totals / totals.sum()
adata_sp.obs["density_prior"] = density_prior      # saved for validation / re-mapping

for ad in (adata_sc, adata_sp):
    if is_raw_counts(ad):
        ad.layers["counts"] = ad.X.copy()
        sc.pp.normalize_total(ad)
        sc.pp.log1p(ad)

# rank_genes_groups needs >= 2 cells per group; tiny types cannot be placed reliably anyway
keep = adata_sc.obs[CELL_TYPE_KEY].map(adata_sc.obs[CELL_TYPE_KEY].value_counts()) >= 10
adata_sc = adata_sc[keep].copy()
adata_sc.obs[CELL_TYPE_KEY] = adata_sc.obs[CELL_TYPE_KEY].astype("category").cat.remove_unused_categories()
```

### Step 3: Training Genes

Top markers per cell type, stratified across types, are a good start (the
Tangram authors suggest ~1k unique markers). Genes not used for training stay
available as held-out genes for `spatial-mapping-validation`.

```python
N_MARKERS = 100
sc.tl.rank_genes_groups(adata_sc, groupby=CELL_TYPE_KEY, use_raw=False, method="wilcoxon")
markers_df = pd.DataFrame(adata_sc.uns["rank_genes_groups"]["names"]).iloc[:N_MARKERS, :]
markers = list(np.unique(markers_df.melt().value.values))

tg.pp_adatas(adata_sc, adata_sp, genes=markers)   # lowercases var_names in both objects
print(f"training genes: {len(adata_sc.uns['training_genes'])}; "
      f"overlap genes: {len(adata_sc.uns['overlap_genes'])}")
```

Fewer than ~100 training genes makes the mapping unstable; raise `N_MARKERS` or
check gene symbol formats (Ensembl IDs vs symbols, human vs mouse case).

### Step 4: Map Cells to Space

`mode="cells"` maps every cell (needed for gene projection and the constrained
mode); `mode="clusters"` maps cell type averages, is far cheaper, and is the
safer choice when the reference comes from a different sample.

```python
import torch

MODE = "cells"                      # or "clusters"
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
kwargs = dict(mode=MODE, density_prior=density_prior, num_epochs=500,
              device=DEVICE, random_state=0)
if MODE == "clusters":
    kwargs["cluster_label"] = CELL_TYPE_KEY

ad_map = tg.map_cells_to_space(adata_sc, adata_sp, **kwargs)
train_df = ad_map.uns["train_genes_df"]
print(ad_map)                       # cells (or clusters) x spots
print(f"mean training score: {train_df['train_score'].mean():.3f}")
```

A mean training score well below ~0.6 means the shared genes do not agree;
inspect it with `spatial-mapping-validation` before using the results.

### Step 5: Project Cell Type Annotations

`tangram_ct_pred` holds the mapped probability mass per type and spot; divide
by the row sum for proportions.

```python
tg.project_cell_annotations(ad_map, adata_sp, annotation=CELL_TYPE_KEY)
ct = adata_sp.obsm["tangram_ct_pred"]
prop = ct.div(ct.sum(axis=1), axis=0)
adata_sp.obs["tangram_top_type"] = prop.idxmax(axis=1).astype("category")
adata_sp.obs["tangram_top_frac"] = prop.max(axis=1)

print(prop.mean().sort_values(ascending=False).head(10))
print(f"spots where the top type is < 50%: {(adata_sp.obs['tangram_top_frac'] < 0.5).mean():.0%}")
```

On spot data (Visium) report proportions; `tangram_top_type` is a summary, not
the identity of the spot.

### Step 6: Plot and Save

```python
import matplotlib.pyplot as plt

xy = adata_sp.obsm["spatial"]
top = prop.mean().nlargest(6).index
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
for ax, t in zip(axes.flat, top):
    s = ax.scatter(xy[:, 0], xy[:, 1], c=prop[t], s=12, cmap="viridis", vmin=0)
    ax.set_title(t); ax.invert_yaxis(); ax.set_aspect("equal"); ax.axis("off")
    fig.colorbar(s, ax=ax, shrink=0.6)
plt.tight_layout(); plt.savefig("tangram_celltype_maps.png", dpi=150)

prop.to_csv("tangram_celltype_proportions.csv")
ad_map.write_h5ad("tangram_mapping.h5ad", compression="gzip")
adata_sc.write_h5ad("tangram_sc_prep.h5ad", compression="gzip")
adata_sp.write_h5ad("tangram_spatial.h5ad", compression="gzip")
```

Check each map against biology the user expects (for the demo: L2/3 IT
neurons in the upper cortical layers, L6 types deep). Keep the three h5ad
files; validation and gene projection reuse them.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| Reference choice | from the user | Same tissue and state; the most consequential choice |
| `N_MARKERS` | 100 per type | Training gene count; more genes = more constraint, but noisy genes hurt |
| `mode` | `"cells"` | `"clusters"` is faster and smoother, cannot give per-cell placement |
| `num_epochs` | 500 | 500-1000; check the score has plateaued in `training_history` |
| `density_prior` | raw-count based | `"uniform"` when spot density is truly even; array must sum to 1 |
| `lambda_r` | 0 | Entropy regulariser; > 0 makes each cell's placement more peaked |

## Common Recipes

### Recipe: One Reference, Several Sections

Map each section separately with the same training genes, then compare mean
compositions. `clusters` mode keeps it fast:

```python
sections = {"S1": "s1.h5ad", "S2": "s2.h5ad"}
props = {}
for name, path in sections.items():
    sp = sc.read_h5ad(path)
    totals = np.asarray(sp.X.sum(1)).ravel().astype(float)       # raw counts before normalising
    if is_raw_counts(sp):
        sc.pp.normalize_total(sp); sc.pp.log1p(sp)
    ref = adata_sc.copy()
    tg.pp_adatas(ref, sp, genes=list(adata_sc.uns["training_genes"]))
    m = tg.map_cells_to_space(ref, sp, mode="clusters", cluster_label=CELL_TYPE_KEY,
                              density_prior=totals / totals.sum(), num_epochs=500, device=DEVICE, random_state=0)
    tg.project_cell_annotations(m, sp, annotation=CELL_TYPE_KEY)
    ct_s = sp.obsm["tangram_ct_pred"]
    props[name] = ct_s.div(ct_s.sum(axis=1), axis=0)
summary = pd.DataFrame({k: v.mean() for k, v in props.items()}).round(3)
summary.to_csv("tangram_composition_by_section.csv")
print(summary)
```

### Recipe: Label Cells on Single-Cell-Resolution Data

On Xenium or MERFISH each spatial observation is one cell, so the top
projected type is a per-cell label. Compare it with an existing annotation
rather than replacing it:

```python
adata_sp.obs["tangram_label"] = prop.idxmax(axis=1).astype("category")
adata_sp.obs["tangram_conf"] = prop.max(axis=1)
print(adata_sp.obs["tangram_label"].value_counts().head(15))
if "cell_type" in adata_sp.obs:
    agree = pd.crosstab(adata_sp.obs["cell_type"], adata_sp.obs["tangram_label"], normalize="index")
    agree.round(2).to_csv("tangram_vs_annotation.csv")
    print(agree.max(axis=1).round(2).sort_values())      # low values = the two methods disagree
```

### Recipe: Where Each Reference Cell Lands

In `cells` mode, each reference cell's expected position and how sharply it
is placed (low entropy = one clear location):

```python
P = np.asarray(ad_map.X, dtype=float)
P = P / P.sum(axis=1, keepdims=True)                      # cells x spots, rows sum to 1
adata_sc.obsm["tangram_xy"] = P @ adata_sp.obsm["spatial"]
adata_sc.obs["placement_entropy"] = -(P * np.log(P + 1e-12)).sum(axis=1)
print(adata_sc.obs.groupby(CELL_TYPE_KEY, observed=True)["placement_entropy"].median()
      .sort_values().round(2))
```

Types with high entropy are spread evenly and their spatial pattern carries
little information.

## Expected Outputs

- `tangram_mapping.h5ad` - cell (or cluster) x spot probability matrix; `uns["train_genes_df"]`
- `tangram_sc_prep.h5ad`, `tangram_spatial.h5ad` - preprocessed inputs; spatial has `obs["density_prior"]`, `obsm["tangram_ct_pred"]`, `obs["tangram_top_type"]`
- `tangram_celltype_proportions.csv` - per-spot cell type proportions
- `tangram_celltype_maps.png` - maps of the most abundant types

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `AssertionError` on `training_genes` | `pp_adatas` not run on these exact objects | Re-run Step 3 right before mapping |
| Very few training genes | Symbol mismatch (Ensembl IDs, species) | Map IDs to symbols; `pp_adatas` already lowercases |
| CUDA out of memory / very slow on CPU | Too many cells in `mode="cells"` | Subsample the reference per type, or use `mode="clusters"` |
| One type dominates every spot | Reference lacks the tissue's major types or wrong state | Choose a better-matched reference |
| `ValueError: A cluster_label must be specified` | `mode="clusters"` without label | Pass `cluster_label=CELL_TYPE_KEY` |
| `Invalid input for density_prior` | List instead of array, or does not sum to 1 | Pass a numpy array normalised to sum 1 |
| Gene names lowercase afterwards | `pp_adatas` default `gene_to_lowercase=True` | Expected; use lowercase names downstream |

## Related Skills

- `spatial-mapping-validation` - training/held-out gene scores, AUC, cross-validation of this mapping
- `scrna-spatial-gene-imputation` - project unmeasured genes through the mapping
- `spatial-transcriptomics-deconvolution-tangram` - constrained mode with histology segmentation (Visium + image)
- `spatial-transcriptomics-deconvolution-cell2location` - probabilistic spot deconvolution alternative
- `spatial-transcriptomics-cell-type-annotation` - reference search/download; labels for single-cell-resolution data
- `spatial-transcriptomics-cell-cell-communication` - interactions between the mapped types

## References

- Biancalani et al. (2021) Tangram, Nature Methods: https://doi.org/10.1038/s41592-021-01264-7
- Tangram source and tutorials: https://github.com/broadinstitute/Tangram
- Tangram documentation: https://tangram-sc.readthedocs.io/
- squidpy + Tangram tutorial (demo data used here): https://squidpy.readthedocs.io/en/stable/notebooks/tutorials/tutorial_tangram.html
