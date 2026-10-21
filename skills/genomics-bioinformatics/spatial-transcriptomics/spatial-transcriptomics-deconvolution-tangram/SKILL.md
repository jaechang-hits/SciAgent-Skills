---
name: "spatial-transcriptomics-deconvolution-tangram"
description: "Visium spot deconvolution into single segmented cells with Tangram constrained mode and the tissue image: squidpy nucleus segmentation (watershed) and per-spot cell counts, constrained mapping with target_count and a segmentation-based density prior, per-spot cell type counts, and a cell type label for every segmented nucleus (tg.deconvolve_cell_annotations). Histology-based deconvolution skill of the Tangram set: unconstrained mapping and per-spot proportions -> spatial-mapping-tangram; mapping quality checks -> spatial-mapping-validation; projecting/imputing genes -> scrna-spatial-gene-imputation. Without an image use spatial-transcriptomics-deconvolution-cell2location."
license: "CC-BY-4.0"
---

# Visium Deconvolution with Tangram and Histology

## Overview

Counts nuclei in each Visium spot from the tissue image, then asks Tangram to
select exactly that many reference cells and place them, so every segmented
nucleus receives a cell type. Output: cell type counts per spot and a
coordinate and cell type for every segmented nucleus. Segmentation quality
bounds the result: a spot with miscounted nuclei gets the wrong number of
cells.

## When to Use

- Placing single cells, not proportions, onto a Visium section that has its full-resolution image
- Labelling every segmented nucleus in a spot with a cell type from a scRNA-seq reference
- Constraining deconvolution by the number of nuclei actually visible in each spot
- Producing a cell-level table from spot data for neighbourhood or interaction analysis
- Cross-checking per-spot compositions from another deconvolution method against histology
- Use `spatial-transcriptomics-deconvolution-cell2location` instead when no full-resolution image is available or when you need posterior uncertainty
- For unconstrained Tangram mapping and per-spot proportions, use `spatial-mapping-tangram`

## Prerequisites

- **Input**: Visium Space Ranger folder (`filtered_feature_bc_matrix.h5` + `spatial/`)
  and the **full-resolution** image given to Space Ranger (not
  `tissue_hires_image.png`, which is too small to segment nuclei)
- **Reference**: scRNA-seq with a cell type column, tissue- and state-matched
  (Steps 3-4 of `spatial-transcriptomics-cell-type-annotation`)
- **Compute**: Tangram needs PyTorch (large); constrained mode on CPU takes
  minutes for ~20k cells x ~1k spots, GPU is much faster
- **Python packages**: `tangram-sc`, `squidpy`, `scanpy`

```bash
pip install tangram-sc squidpy scanpy
```

## Workflow

1. Load Visium data and image
2. Segment nuclei
3. Count nuclei per spot
4. Prepare reference and training genes
5. Constrained mapping
6. Assign a cell type to each segmented nucleus
7. Plot and save

### Step 1: Load Data and Image

The demo is the Tangram tutorial data (mouse cortex, fluorescent Visium, DAPI
in channel 0), downloaded and cached by squidpy on first use.

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
    img = sq.datasets.visium_fluo_image_crop()
    adata_sc = sq.datasets.sc_mouse_cortex()
    CELL_TYPE_KEY, STAIN = "cell_subclass", "fluorescent"
else:
    VISIUM_DIR = "path/to/spaceranger_outs"
    adata_sp = sq.read.visium(VISIUM_DIR)                    # obsm["spatial"] in full-res pixels
    adata_sp.var_names_make_unique()
    library_id = list(adata_sp.uns["spatial"])[0]
    img = sq.im.ImageContainer("path/to/fullres_image.tif", layer="image", library_id=library_id)
    adata_sc = sc.read_h5ad("reference.h5ad")
    CELL_TYPE_KEY, STAIN = "cell_type", "he"                 # "he" for H&E, "fluorescent" for DAPI

print(adata_sp, img, sep="\n")
```

### Step 2: Segment Nuclei

Watershed with an Otsu threshold. Fluorescent nuclei are bright; H&E nuclei
are dark, so convert to grayscale and segment below the threshold.

```python
if STAIN == "fluorescent":
    sq.im.process(img, layer="image", method="smooth")             # -> "image_smooth"
    sq.im.segment(img, layer="image_smooth", method="watershed", channel=0)
else:
    sq.im.process(img, layer="image", method="gray")               # -> "image_gray"
    sq.im.process(img, layer="image_gray", method="smooth")        # -> "image_gray_smooth"
    sq.im.segment(img, layer="image_gray_smooth", method="watershed", channel=0, geq=False)
print(img)                                                         # adds "segmented_watershed"
```

Inspect a crop before going on:

```python
import matplotlib.pyplot as plt

y0, x0, h, w = 1500, 1700, 400, 500                                # any tissue region
raw = img["image"][y0:y0 + h, x0:x0 + w, 0, 0].values
seg = img["segmented_watershed"][y0:y0 + h, x0:x0 + w, 0, 0].values
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].imshow(raw, cmap="gray"); axes[0].set_title("image")
axes[1].imshow(np.ma.masked_equal(seg, 0) % 20, cmap="tab20"); axes[1].set_title("nuclei")
for ax in axes: ax.axis("off")
plt.savefig("segmentation_crop.png", dpi=150)
```

Merged clumps or fragmented nuclei mean a bad threshold: pass
`thresh=<value>` to `sq.im.segment`, or adjust the smoothing (`sigma=` in
`sq.im.process`).

### Step 3: Count Nuclei per Spot

Tangram reads `obsm["image_features"]`; squidpy's default key is
`img_features`, so set `key_added`.

```python
sq.im.calculate_image_features(
    adata_sp, img, layer="image", features="segmentation", key_added="image_features",
    features_kwargs={"segmentation": {"label_layer": "segmented_watershed",
                                      "props": ["label", "centroid"]}},
    mask_circle=True,
)
adata_sp.obs["cell_count"] = adata_sp.obsm["image_features"]["segmentation_label"]
print(adata_sp.obs["cell_count"].describe())
print(f"total nuclei: {adata_sp.obs['cell_count'].sum()}; spots with 0: {(adata_sp.obs['cell_count'] == 0).sum()}")
sc.pl.spatial(adata_sp, color="cell_count", save="_cell_count.png")
```

Visium spots usually hold ~1-10 nuclei in brain, more in dense tissue. Many
zero-count spots inside tissue indicate failed segmentation.

### Step 4: Reference and Training Genes

Same preparation as Steps 2-3 of `spatial-mapping-tangram`, condensed:

```python
for ad in (adata_sc, adata_sp):
    x = ad.X[:500]
    x = x.toarray() if hasattr(x, "toarray") else np.asarray(x)
    if np.allclose(x, np.round(x)) and x.max() > 20:               # raw counts -> normalise
        sc.pp.normalize_total(ad); sc.pp.log1p(ad)

vc = adata_sc.obs[CELL_TYPE_KEY].value_counts()
adata_sc = adata_sc[adata_sc.obs[CELL_TYPE_KEY].isin(vc[vc >= 10].index)].copy()
adata_sc.obs[CELL_TYPE_KEY] = adata_sc.obs[CELL_TYPE_KEY].astype("category").cat.remove_unused_categories()
sc.tl.rank_genes_groups(adata_sc, groupby=CELL_TYPE_KEY, use_raw=False, method="wilcoxon")
markers = list(np.unique(pd.DataFrame(adata_sc.uns["rank_genes_groups"]["names"]).iloc[:100].melt().value))
tg.pp_adatas(adata_sc, adata_sp, genes=markers)
print(f"training genes: {len(adata_sc.uns['training_genes'])}")
```

### Step 5: Constrained Mapping

The density prior is the nucleus count per spot, and `target_count` is the
total number of nuclei, so Tangram selects that many cells from the reference
(`obs["F_out"]` = selection probability per cell).

```python
import torch

counts = adata_sp.obs["cell_count"].to_numpy(dtype=float)
ad_map = tg.map_cells_to_space(
    adata_sc, adata_sp, mode="constrained",
    target_count=int(counts.sum()), density_prior=counts / counts.sum(),
    num_epochs=1000, device="cuda:0" if torch.cuda.is_available() else "cpu", random_state=0,
)
print(f"mean training score: {ad_map.uns['train_genes_df']['train_score'].mean():.3f}")
print(f"cells selected (F_out > 0.5): {(ad_map.obs['F_out'] > 0.5).sum()} of target {int(counts.sum())}")
```

The reference needs more cells than `target_count`; subsample the spatial
area or use a larger reference otherwise.

### Step 6: One Cell Type per Nucleus

`tg.project_cell_annotations` in tangram-sc 1.0.4 ignores `F_out` (the
filtered map is overwritten), so compute the per-spot prediction from
selected cells only. `count_cell_annotations` already applies the filter.

```python
sel = (ad_map.obs["F_out"] > 0.5).to_numpy()
onehot = pd.get_dummies(ad_map.obs.loc[sel, CELL_TYPE_KEY]).astype(float)
ct = pd.DataFrame(ad_map.X[sel].T @ onehot.to_numpy(), index=ad_map.var_names, columns=onehot.columns)
adata_sp.obsm["tangram_ct_pred"] = ct                              # used by deconvolve below

tg.create_segment_cell_df(adata_sp)                                # nucleus table with spot ids
tg.count_cell_annotations(ad_map, adata_sc, adata_sp, annotation=CELL_TYPE_KEY)
adata_segment = tg.deconvolve_cell_annotations(adata_sp)           # one row per nucleus, obs["cluster"]
adata_segment.obsm["spatial"] = adata_segment.obs[["x", "y"]].to_numpy(float)

print(adata_sp.obsm["tangram_ct_count"].iloc[:5])
print(adata_segment.obs["cluster"].value_counts())
print("nuclei x/y range:", adata_segment.obsm["spatial"].min(0), adata_segment.obsm["spatial"].max(0))
print("spots  x/y range:", adata_sp.obsm["spatial"].min(0), adata_sp.obsm["spatial"].max(0))
```

The two coordinate ranges should overlap; if they look swapped, swap the
columns of `adata_segment.obsm["spatial"]`.

### Step 7: Plot and Save

```python
fig, ax = plt.subplots(figsize=(10, 10))
sc.pl.spatial(adata_segment, color="cluster", size=0.4, alpha_img=0.3, frameon=False, show=False, ax=ax)
plt.savefig("tangram_deconvolved_cells.png", dpi=200, bbox_inches="tight")

adata_sp.obsm["tangram_ct_count"].drop(columns=["centroids"]).to_csv("tangram_ct_count_per_spot.csv")
adata_segment.obs[["x", "y", "cluster"]].to_csv("tangram_segment_celltypes.csv")
ad_map.write_h5ad("tangram_constrained_mapping.h5ad", compression="gzip")
```

Compare per-spot type counts with an unconstrained run
(`spatial-mapping-tangram`) or cell2location; large disagreements usually
trace back to segmentation.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| Reference choice | from the user | Same tissue and state; most consequential choice |
| `STAIN` / `geq` | from the image | Bright (fluorescent) vs dark (H&E) nuclei |
| `thresh` (`sq.im.segment`) | Otsu | Nucleus threshold; drives every count |
| `mask_circle` | True | Count only nuclei inside the round spot |
| `num_epochs` | 1000 | Constrained mode needs more epochs than cells mode |
| `F_out` threshold | 0.5 | Probability for a reference cell to count as selected |

## Common Recipes

### Recipe: Compare with cell2location per Spot

Two methods agreeing on a type's spot pattern is stronger evidence than
either alone; disagreement usually traces back to segmentation:

```python
tg_count = adata_sp.obsm["tangram_ct_count"].drop(columns=["centroids", "cell_n"], errors="ignore")
tg_prop = tg_count.div(tg_count.sum(1).replace(0, np.nan), axis=0)
c2l_prop = pd.read_csv("cell2location_proportions.csv", index_col=0)

spots = tg_prop.index.intersection(c2l_prop.index)
shared_types = tg_prop.columns.intersection(c2l_prop.columns)   # align names first if they differ
agreement = pd.Series({ct: tg_prop.loc[spots, ct].corr(c2l_prop.loc[spots, ct]) for ct in shared_types})
print(agreement.sort_values().round(2))
agreement.to_csv("tangram_vs_cell2location.csv")
```

### Recipe: Use the Segmented Cells Downstream

The per-nucleus table behaves like single-cell-resolution data, so
neighbourhood statistics and interaction analyses can run on it:

```python
adata_segment.obs["cluster"] = adata_segment.obs["cluster"].astype("category")
sq.gr.spatial_neighbors(adata_segment, coord_type="generic", n_neighs=10)
sq.gr.nhood_enrichment(adata_segment, cluster_key="cluster", n_perms=1000, seed=0)
sq.pl.nhood_enrichment(adata_segment, cluster_key="cluster", cmap="coolwarm", save="segment_nhood.png")
adata_segment.write_h5ad("tangram_segment_cells.h5ad", compression="gzip")
```

The cells carry labels but no own expression; for expression-based
interaction scoring see `spatial-transcriptomics-cell-cell-communication`
on the spot data.

## Expected Outputs

- `segmentation_crop.png` - segmentation check
- `figures/spatial_cell_count.png` - nuclei per spot
- `tangram_constrained_mapping.h5ad` - constrained map with `obs["F_out"]`
- `tangram_ct_count_per_spot.csv` - cell type counts per spot
- `tangram_segment_celltypes.csv` - coordinates and cell type of every nucleus
- `tangram_deconvolved_cells.png` - single-cell map over the tissue

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Missing parameter ... Run sqidpy.im.calculate_image_features` | Features stored under `img_features` | Pass `key_added="image_features"` (Step 3) |
| `KeyError: 'tangram_ct_pred'` in `deconvolve_cell_annotations` | Annotation not projected | Run the `tangram_ct_pred` block of Step 6 first |
| Almost all spots have 0 nuclei | Low-res image, or wrong polarity | Use the full-res image; switch `geq` / stain branch |
| Counts far too high | Over-segmentation of texture | Raise `thresh` or smoothing `sigma` |
| `ValueError` about `target_count` | Missing or zero count | Check `cell_count` sum > 0 |
| Out of memory | Large reference x many spots | Subsample the reference per type; process tissue tiles separately |
| `KeyError` / `FutureWarning` on integer key in `count_cell_annotations` | tangram indexes `obs[annotation][k]` positionally; newer pandas rejects it | `adata_sc.obs_names = [str(i) for i in range(adata_sc.n_obs)]` before Step 4 |
| Image and spots misaligned | Image is not the one Space Ranger used, or wrong scale | Use the Space Ranger input image at full resolution |

## Related Skills

- `spatial-mapping-tangram` - unconstrained mapping and per-spot proportions
- `spatial-mapping-validation` - training/held-out scores apply to this map too
- `scrna-spatial-gene-imputation` - project genes through the mapping
- `spatial-transcriptomics-deconvolution-cell2location` - deconvolution without an image
- `spatial-transcriptomics-analysis-squidpy` - squidpy image and neighbourhood analysis
- `spatial-transcriptomics-cell-cell-communication` - interactions between the assigned cells

## References

- Biancalani et al. (2021) Tangram, Nature Methods: https://doi.org/10.1038/s41592-021-01264-7
- Tangram source: https://github.com/broadinstitute/Tangram
- Tangram documentation: https://tangram-sc.readthedocs.io/
- squidpy + Tangram tutorial (constrained mode with segmentation): https://squidpy.readthedocs.io/en/stable/notebooks/tutorials/tutorial_tangram.html
- squidpy nucleus segmentation: https://squidpy.readthedocs.io/en/stable/api/squidpy.im.segment.html
