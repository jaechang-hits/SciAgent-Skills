---
name: "spatial-mapping-tangram"
description: "Tangram (tangram-sc) mapping of scRNA-seq onto spatial transcriptomics (Visium, Slide-seq, MERFISH, Xenium), one skill for every Tangram task: marker training genes, cells/clusters/constrained mode, per-spot cell type proportions, held-out gene validation (training scores, compare_spatial_geneexp, AUC, k-fold CV), imputation of unmeasured or dropout genes (project_genes; gimVI alternative), and Visium deconvolution into segmented nuclei with the tissue image (squidpy watershed, target_count, deconvolve_cell_annotations). Task-specific routes follow the main workflow. For probabilistic spot abundances with uncertainty use spatial-transcriptomics-deconvolution-cell2location."
license: "CC-BY-4.0"
---

# Spatial Mapping with Tangram

## Overview

Tangram fits a cell-by-spot probability matrix so that the expression of the
mapped single cells reproduces the spatial expression of shared training
genes. Every Tangram task starts from that matrix: per-spot cell type
proportions, predicted expression of genes the panel did not measure, and,
with a histology image, a cell type for every segmented nucleus. The mapping
always converges to something, so this skill validates it on genes held out
of training before any result is reported. The reference must come from the
same tissue and state as the section and share informative genes with it.

| Task | Route |
|---|---|
| Cell type proportions per spot / labels on single-cell-resolution data | Workflow Steps 1-7 |
| Predict unmeasured or dropout-affected genes | Steps 1-6, then Route: Gene Imputation |
| One cell type per segmented nucleus (Visium + full-resolution image) | Route: Nuclei Deconvolution (replaces Step 1, then Steps 2-3, Nucleus 2-4, Step 6) |
| Deeper quality checks (k-fold CV, cells vs clusters, seed stability) | After Step 6, Route: Advanced Validation |

All routes are in `## Task Routes` below the Workflow.

## When to Use

- Placing scRNA-seq cell types onto a Visium, Slide-seq, MERFISH or Xenium section
- Getting per-spot cell type proportions without a histology image
- Showing the spatial pattern of genes a targeted panel did not measure, or that Visium lost to dropout
- Labelling every segmented nucleus in a Visium spot when the full-resolution image is available
- Deciding whether a Tangram mapping is good enough to report, from held-out genes
- Mapping one reference onto several sections for a consistent comparison
- Use `spatial-transcriptomics-deconvolution-cell2location` instead when you need posterior uncertainty for spot abundances
- For label transfer on Xenium/MERFISH as the primary annotation, use `spatial-transcriptomics-cell-type-annotation` (Tangram labels are a second opinion)

## Prerequisites

- **Spatial data**: AnnData with `obsm["spatial"]` (Visium: Step 1 of
  `spatial-transcriptomics-deconvolution-cell2location`; Xenium: Step 1 of
  `spatial-transcriptomics-cell-type-annotation`)
- **Reference**: scRNA-seq with a cell type column, tissue- and state-matched
  (search/download: Steps 3-4 of `spatial-transcriptomics-cell-type-annotation`,
  with `GENES = None` and `MAX_PER_TYPE = 300` - markers are ranked over every gene)
- **Python packages**: `tangram-sc`, `squidpy`, `scanpy`. They are not
  pre-installed; `tangram-sc` pulls PyTorch, whose Linux wheel brings CUDA
  libraries (several GB). The first install takes minutes; say so to the user
  before starting.
- **Compute**: CPU works. `mode="cells"` holds a reference-cells x spots
  matrix plus optimiser state (roughly 16 bytes per entry): ~2 GB for 30k cells
  x 5k spots, but tens of GB for single-cell-resolution sections with 100k+
  cells. Use `mode="clusters"` or subsample there (Step 4 prints the estimate).

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi squidpy scanpy tangram-sc
```

## Pre-flight Interview

```yaml
decisions:
  - id: D1
    param: TASK
    kind: required
    source: user
    ask: "What should the mapping give you: cell type proportions per spot (or labels per cell), predicted expression of genes the panel did not measure, or a cell type for every nucleus seen in the tissue image?"
    default: "cell type proportions"

  - id: D2
    param: referenceSource
    kind: required
    source: user
    ask: "Do you have a scRNA/snRNA-seq reference from the same tissue and state (h5ad with a cell type column), or should I search public data (CELLxGENE)?"
    default: null

  - id: D3
    param: CELL_TYPE_KEY
    kind: required
    source: data
    depends_on: [D2]
    ask: "Which column of the reference holds the cell types to map?"
    default: null

  - id: D4
    param: MODE
    kind: required
    source: user
    depends_on: [D1]
    ask: "Do the reference and the spatial section come from the same specimen (or a biological replicate), or from different samples/studies?"
    default: "clusters when from different samples or when the Step 4 memory estimate exceeds the sandbox; cells otherwise; constrained for the nucleus task"

  - id: D5
    param: density_prior
    kind: required
    source: data
    depends_on: [D1]
    ask: "This section looks like <spot data / single-cell-resolution data>: weight each location by its RNA count, or treat every location as one cell?"
    default: "per-spot total counts on spot data; uniform on single-cell-resolution data; nucleus counts for the nucleus task"

  - id: D6
    param: TARGETS
    kind: required
    source: user
    depends_on: [D1]
    skip_if: "TASK is not gene imputation"
    ask: "Which genes or gene signatures do you want predicted on the tissue?"
    default: null

  - id: D7
    param: STAIN
    kind: required
    source: data
    depends_on: [D1]
    skip_if: "TASK is not the nucleus task"
    ask: "Is the full-resolution image H&E (dark nuclei) or fluorescent DAPI (bright nuclei)?"
    default: null

  - id: D8
    param: N_MARKERS
    kind: optional
    source: user
    ask: "How many top marker genes per cell type should drive the mapping?"
    default: "100 per type"

  - id: D9
    param: num_epochs
    kind: optional
    source: user
    ask: "How many training epochs?"
    default: "500 (1000 in constrained mode)"

  - id: D10
    param: DEVICE
    kind: never_ask
    source: data
    reason: "Picks CUDA when present, otherwise CPU; changes runtime only"
```

Ask D1, D2 and D4 together. D3 and D5 follow from inspecting the files: offer
the reference's `obs` columns that look like cell type labels, and state the
platform the coordinates suggest. If no column groups the reference cells,
stop and ask; never map on clusters you computed yourself without saying so.

## Workflow

1. Load spatial data and reference
2. Normalise and keep the raw-count density prior
3. Select training genes and run `tg.pp_adatas`
4. Map cells to space
5. Project cell type annotations
6. Validate on training and held-out genes
7. Plot and save

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
    CELL_TYPE_KEY = "cell_type"                  # D3

print(adata_sp)
print(adata_sc.obs[CELL_TYPE_KEY].value_counts())
shared = adata_sc.var_names.str.lower().intersection(adata_sp.var_names.str.lower())
print(f"shared genes: {len(shared)}")
```

For the nucleus task use Nucleus 1 (Task Routes) instead of this step.

### Step 2: Normalise, Keep the Density Prior

Use the same normalisation on both sides. `tg.pp_adatas` computes its
`rna_count_based` prior from `adata_sp.X`, which `normalize_total` flattens, so
take the per-spot total from raw counts first.

```python
def is_raw_counts(ad):
    x = ad.X[: min(500, ad.n_obs)]
    x = x.toarray() if hasattr(x, "toarray") else np.asarray(x)
    return np.allclose(x, np.round(x)) and x.max() > 20

SINGLE_CELL_RESOLUTION = False                   # D5: True for Xenium/MERFISH/CosMx
if SINGLE_CELL_RESOLUTION:
    density_prior = np.full(adata_sp.n_obs, 1 / adata_sp.n_obs)
else:
    if "total_counts" in adata_sp.obs:
        totals = adata_sp.obs["total_counts"].to_numpy(dtype=float)
    else:
        totals = np.asarray(adata_sp.X.sum(1)).ravel().astype(float)   # raw if X is raw
    density_prior = totals / totals.sum()
adata_sp.obs["density_prior"] = density_prior      # reused by validation / re-mapping

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

Top markers per cell type, stratified across types (the Tangram authors
suggest ~1k unique markers). Genes not used for training stay available as
held-out genes for Step 6; with `genes=None` every shared gene trains and
nothing is left to validate on.

```python
N_MARKERS = 100                                   # D8
sc.tl.rank_genes_groups(adata_sc, groupby=CELL_TYPE_KEY, use_raw=False, method="wilcoxon")
markers_df = pd.DataFrame(adata_sc.uns["rank_genes_groups"]["names"]).iloc[:N_MARKERS, :]
markers = list(np.unique(markers_df.melt().value.values))

tg.pp_adatas(adata_sc, adata_sp, genes=markers)   # lowercases var_names in both objects
print(f"training genes: {len(adata_sc.uns['training_genes'])}; "
      f"overlap genes: {len(adata_sc.uns['overlap_genes'])}")
```

Fewer than ~100 training genes makes the mapping unstable; raise `N_MARKERS` or
check gene symbol formats (Ensembl IDs vs symbols, human vs mouse case). From
here on, gene names are lowercase. For the nucleus task, continue with
Nucleus 2-4 (Task Routes), then return to Step 6.

### Step 4: Map Cells to Space

`mode="cells"` maps every cell (needed for per-cell placement and the
constrained mode); `mode="clusters"` maps cell type averages, is far cheaper,
and is the safer choice when the reference comes from a different sample.

```python
import torch

MODE = "cells"                                    # D4: or "clusters"
CLUSTER_LABEL = CELL_TYPE_KEY if MODE == "clusters" else None
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"

n_rows = adata_sc.obs[CELL_TYPE_KEY].nunique() if MODE == "clusters" else adata_sc.n_obs
print(f"rough memory for the map + optimiser: {n_rows * adata_sp.n_obs * 16 / 1e9:.1f} GB")

kwargs = dict(mode=MODE, density_prior=density_prior, num_epochs=500,   # D9
              device=DEVICE, random_state=0)
if CLUSTER_LABEL:
    kwargs["cluster_label"] = CLUSTER_LABEL

ad_map = tg.map_cells_to_space(adata_sc, adata_sp, **kwargs)
train_df = ad_map.uns["train_genes_df"]
print(ad_map)                                     # cells (or clusters) x spots
print(f"mean training score: {train_df['train_score'].mean():.3f}")
```

If the estimate exceeds ~12 GB on the 16 GB sandbox, switch to `clusters`
or subsample the reference per cell type before mapping.

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

### Step 6: Validate on Training and Held-out Genes

Training scores show the fit; only held-out genes show whether the mapping
generalises. Low scores on genes sparse in space (high `sparsity_sp`) are
dropout; low scores on well-detected genes point to a reference mismatch.

```python
import matplotlib.pyplot as plt

tg.plot_training_scores(ad_map, bins=20, alpha=0.5)   # score; vs sc / sp sparsity; vs difference
plt.savefig("tangram_training_scores.png", dpi=150, bbox_inches="tight")

ad_ge = tg.project_genes(ad_map, adata_sc, cluster_label=CLUSTER_LABEL)   # spots x all reference genes
df_all = tg.compare_spatial_geneexp(ad_ge, adata_sp, adata_sc)
df_all.to_csv("tangram_gene_scores.csv")
train = df_all[df_all["is_training"]]
test = df_all[~df_all["is_training"]]
print(f"training genes: {len(train)}, mean score {train['score'].mean():.3f}")
print(f"held-out genes: {len(test)}, mean score {test['score'].mean():.3f}")
```

`tg.eval_metric` fits held-out score against spatial sparsity; its AUC is the
main quality number. Plot from its coordinates (`tg.plot_auc` calls seaborn
with positional arguments, which recent seaborn rejects):

```python
metrics, ((pol_xs, pol_ys), (xs, ys)) = tg.eval_metric(df_all)
print({k: round(float(v), 3) for k, v in metrics.items()})
fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(xs, ys, s=8, alpha=0.5); ax.plot(pol_xs, pol_ys, c="r")
ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="score (held-out genes)", ylabel="spatial sparsity",
       title=f"AUC = {metrics['auc_score']:.3f}")
plt.savefig("tangram_auc.png", dpi=150, bbox_inches="tight")
```

Each projected cell type should also follow a held-out marker the training
could not have forced:

```python
checks = {"Oligo": "mobp", "Astro": "aqp4"}       # cell type -> lowercase marker; fill for the tissue
training = set(adata_sp.uns["training_genes"])
for t, g in checks.items():
    if t in prop and g in adata_sp.var_names:
        x = adata_sp[:, g].X
        x = np.asarray(x.todense()).ravel() if hasattr(x, "todense") else np.asarray(x).ravel()
        tag = "training" if g in training else "held-out"
        print(f"{t} vs {g} ({tag}): r = {np.corrcoef(prop[t], x)[0, 1]:.2f}")
```

| Number | Good | Usable with care | Poor - do not report as a finding |
|---|---|---|---|
| Mean training score | > 0.7 | 0.5-0.7 | < 0.5 |
| Held-out AUC | > 0.6 | 0.4-0.6 | < 0.4 |
| Held-out marker r | clearly positive | weak | ~0 or negative |

A large train-test gap means the mapping memorised the markers: broaden the
marker set, use `mode="clusters"`, or set `lambda_r` > 0. Report these numbers
next to every map or imputed gene.

### Step 7: Plot and Save

```python
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
neurons in the upper cortical layers, L6 types deep). The three h5ad files let
the reference routes resume without re-mapping.

## Task Routes

Each route continues the Workflow session (same variable names). Only the calls
that differ from the Workflow, or that fail silently when written another way,
are shown; plotting and saving follow Step 7.

### Route: Gene Imputation (Tangram, gimVI)

Predicts genes the panel did not measure, or measured with heavy dropout, by
projecting reference expression through the mapping. A projected gene reflects
where the mapped cells sit, not a new measurement: report every imputed map as
a prediction, next to the held-out score from Step 6. Start after Step 6
(`ad_ge`, `df_all`), mapped with a marker subset so held-out genes exist.

1. **Targets (D6)**: lowercase names (after `pp_adatas`); a gene absent or
   near-zero in the reference cannot be imputed. Genes dense in the reference
   but sparse in space (dropout) gain the most.
2. **Trust table**: there is no ground truth for unmeasured genes; the held-out
   score is the proxy, and a gene expressed in < ~5% of reference cells gives a
   noisy map.
3. **Plot measured vs projected**: `tg.plot_genes_sc(genes, adata_measured=adata_sp,
   adata_predicted=ad_ge, perc=0.02)` needs `uns["spatial"]`; otherwise scatter on
   `obsm["spatial"]` copied below.
4. **Store** predictions in `obsm`, never in `X`, so later steps cannot mistake
   them for counts.

```python
TARGETS = ["foxp3", "cd8a", "gfap", "mbp"]                      # D6
in_sc = [g for g in TARGETS if g in adata_sc.var_names]
ad_ge.obsm["spatial"] = adata_sp[ad_ge.obs_names].obsm["spatial"]

detect_sc = pd.Series(np.asarray((adata_sc.X > 0).mean(0)).ravel(), index=adata_sc.var_names)
trust = pd.DataFrame({
    "measured_in_spatial": [g in adata_sp.var_names for g in in_sc],
    "heldout_score": [df_all["score"].get(g, np.nan) for g in in_sc],
    "frac_cells_expressing_sc": [detect_sc[g] for g in in_sc],
}, index=in_sc)
trust.to_csv("imputation_trust.csv")
print(f"held-out median score: {df_all.loc[~df_all['is_training'], 'score'].median():.3f}")

keep = [g for g in in_sc if g not in adata_sp.var_names]       # imputed-only genes
x = ad_ge[:, keep].X
adata_sp.obsm["imputed_tangram"] = pd.DataFrame(x.toarray() if hasattr(x, "toarray") else x,
                                                index=ad_ge.obs_names, columns=keep)
ad_ge.write_h5ad("tangram_projected_genes.h5ad", compression="gzip")
```

- **Signature score**: `sc.tl.score_genes(ad_ge, genes, score_name="signature_score")`
  on the projected genes; it marks where cells expressing the signature in the
  reference were placed.
- **Spatially structured imputed genes**: `sq.gr.spatial_neighbors(ad_ge, coord_type="generic")`
  then `sq.gr.spatial_autocorr(ad_ge, mode="moran", genes=unmeasured)`. High
  Moran's I often mirrors the layout of the expressing cell type; check that
  before calling it a finding.

**gimVI (count-based second opinion, targeted panels)**: install
`pixi add --pypi "scvi-tools<1.6"` (gimVI leaves scvi-tools in v1.6). Both
objects need raw counts, and the spatial genes must be a subset of the reference
genes. Hold out ~1/5 of the panel genes, train on the rest, and report the
held-out Spearman correlation before trusting the imputed genes.

```python
from scvi.external import GIMVI

GIMVI.setup_anndata(seq)                       # reference counts, all genes
GIMVI.setup_anndata(st_train)                  # spatial counts without the held-out genes
model = GIMVI(seq, st_train)
model.train(max_epochs=200)
_, imputed = model.get_imputed_values(normalized=True)   # spatial cells x reference genes
```

### Route: Nuclei Deconvolution with Histology (constrained mode)

Counts nuclei per Visium spot from the image, then asks Tangram
(`mode="constrained"`) to select exactly that many reference cells, so every
segmented nucleus gets a cell type. Segmentation quality bounds the result.
Needs the Space Ranger folder and the **full-resolution** image given to Space
Ranger (`tissue_hires_image.png` is too small to segment). Without it use
`spatial-transcriptomics-deconvolution-cell2location`.

Order: Nucleus 1 replaces Step 1, then Steps 2-3, Nucleus 2-4, and Step 6 on
the constrained map (`CLUSTER_LABEL = None`).

#### Nucleus 1: Load Data and Image

```python
VISIUM_DIR = "path/to/spaceranger_outs"
adata_sp = sq.read.visium(VISIUM_DIR)                     # obsm["spatial"] in full-res pixels
adata_sp.var_names_make_unique()
library_id = list(adata_sp.uns["spatial"])[0]
img = sq.im.ImageContainer("path/to/fullres_image.tif", layer="image", library_id=library_id)
adata_sc = sc.read_h5ad("reference.h5ad")
CELL_TYPE_KEY, STAIN = "cell_type", "he"                  # D7: "he" or "fluorescent"
# count_cell_annotations indexes obs[annotation][k] positionally; newer pandas rejects integer keys
adata_sc.obs_names = [str(i) for i in range(adata_sc.n_obs)]
```

Demo: `sq.datasets.visium_fluo_adata_crop()`, `sq.datasets.visium_fluo_image_crop()`
(DAPI in channel 0, `STAIN = "fluorescent"`) and `sq.datasets.sc_mouse_cortex()`.

#### Nucleus 2: Segment and Count Nuclei

Fluorescent nuclei are bright; H&E nuclei are dark (`geq=False`). Tangram reads
`obsm["image_features"]`, not squidpy's default `img_features`.

```python
if STAIN == "fluorescent":
    sq.im.process(img, layer="image", method="smooth")
    sq.im.segment(img, layer="image_smooth", method="watershed", channel=0)
else:
    sq.im.process(img, layer="image", method="gray")
    sq.im.process(img, layer="image_gray", method="smooth")
    sq.im.segment(img, layer="image_gray_smooth", method="watershed", channel=0, geq=False)

sq.im.calculate_image_features(
    adata_sp, img, layer="image", features="segmentation", key_added="image_features",
    features_kwargs={"segmentation": {"label_layer": "segmented_watershed", "props": ["label", "centroid"]}},
    mask_circle=True)
adata_sp.obs["cell_count"] = adata_sp.obsm["image_features"]["segmentation_label"]
print(adata_sp.obs["cell_count"].describe(), (adata_sp.obs["cell_count"] == 0).sum())
```

Inspect a crop of `img["image"]` next to `img["segmented_watershed"]` before
going on. Merged clumps or fragments: pass `thresh=` to `sq.im.segment` or
change `sigma=` in `sq.im.process`. Visium spots usually hold ~1-10 nuclei in
brain, more in dense tissue; many zero-count spots inside tissue mean failed
segmentation.

#### Nucleus 3: Constrained Mapping

The nucleus counts replace the Step 2 density prior; `target_count` is the total
number of nuclei, and `obs["F_out"]` is each reference cell's selection
probability. The reference needs more cells than `target_count`.

```python
counts = adata_sp.obs["cell_count"].to_numpy(dtype=float)
ad_map = tg.map_cells_to_space(adata_sc, adata_sp, mode="constrained",
                               target_count=int(counts.sum()), density_prior=counts / counts.sum(),
                               num_epochs=1000, device=DEVICE, random_state=0)
print(f"selected (F_out > 0.5): {(ad_map.obs['F_out'] > 0.5).sum()} of {int(counts.sum())}")
```

#### Nucleus 4: One Cell Type per Nucleus

`tg.project_cell_annotations` in tangram-sc 1.0.4 ignores `F_out`, so build the
per-spot prediction from selected cells only; `count_cell_annotations` already
applies the filter.

```python
sel = (ad_map.obs["F_out"] > 0.5).to_numpy()
onehot = pd.get_dummies(ad_map.obs.loc[sel, CELL_TYPE_KEY]).astype(float)
adata_sp.obsm["tangram_ct_pred"] = pd.DataFrame(ad_map.X[sel].T @ onehot.to_numpy(),
                                                index=ad_map.var_names, columns=onehot.columns)
tg.create_segment_cell_df(adata_sp)
tg.count_cell_annotations(ad_map, adata_sc, adata_sp, annotation=CELL_TYPE_KEY)
adata_segment = tg.deconvolve_cell_annotations(adata_sp)        # one row per nucleus, obs["cluster"]
adata_segment.obsm["spatial"] = adata_segment.obs[["x", "y"]].to_numpy(float)
adata_sp.obsm["tangram_ct_count"].drop(columns=["centroids"]).to_csv("tangram_ct_count_per_spot.csv")
adata_segment.obs[["x", "y", "cluster"]].to_csv("tangram_segment_celltypes.csv")
```

Nucleus and spot coordinate ranges must overlap; if they look swapped, swap the
columns of `adata_segment.obsm["spatial"]`. Per-spot counts can be compared with
cell2location by correlating proportions per type over shared spots; large
disagreements usually trace back to segmentation. The per-nucleus table works
like single-cell-resolution data for `sq.gr.nhood_enrichment(adata_segment,
cluster_key="cluster")`, but carries labels, not its own expression.

### Route: Advanced Validation (k-fold CV, mode, seeds)

Run after Step 6 when its numbers are borderline, when choosing a mode, or
before a result goes into a report. Each check re-maps; on CPU use `clusters`
mode and fewer epochs, and report the settings. `PRIOR =
adata_sp.obs["density_prior"].to_numpy()` (saved in Step 2).

- **k-fold gene CV**: withhold each fold of training genes through
  `cv_train_genes` and score the withheld fold. `tg.cross_val` calls `np.float`
  (removed in NumPy >= 1.24) and defaults to `device="cuda:0"`; use the loop.
- **Cells vs clusters**: compare held-out score and AUC (`tg.eval_metric(d)[0]["auc_score"]`),
  never training scores, which always favour `cells`.
- **Seed stability**: re-map with seeds 0-2, project annotations, correlate each
  type's proportions between runs; r < ~0.8 means that type's map is not stable.
- **Genes the reference explains badly**: held-out genes with `sparsity_sp < 0.5`
  and `score < 0.3` are not dropout; tumour, stress or tissue-specific genes among
  them point to a reference from the wrong state or tissue.

```python
K, EPOCHS = 5, 300
genes = np.array(adata_sc.uns["training_genes"])
folds = np.array_split(np.random.default_rng(0).permutation(genes), K)
rows = []
for i, held in enumerate(folds):
    m = tg.map_cells_to_space(adata_sc, adata_sp, cv_train_genes=[g for g in genes if g not in set(held)],
                              mode="clusters", cluster_label=CELL_TYPE_KEY, density_prior=PRIOR,
                              num_epochs=EPOCHS, device=DEVICE, random_state=0, verbose=False)
    ge = tg.project_genes(m, adata_sc, cluster_label=CELL_TYPE_KEY)
    rows.append({"fold": i, "test_score": tg.compare_spatial_geneexp(ge, adata_sp, genes=list(held))["score"].mean()})
cv = pd.DataFrame(rows); cv.to_csv("tangram_cv.csv", index=False)
print(cv["test_score"].mean())
```

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| Reference choice | from the user | Same tissue and state; the most consequential choice |
| `N_MARKERS` | 100 per type | Training gene count; more genes = more constraint, but noisy genes hurt |
| `mode` | `"cells"` | `"clusters"` is faster and smoother, cannot give per-cell placement; `"constrained"` selects `target_count` cells |
| `num_epochs` | 500 | 500-1000; check the score has plateaued in `training_history` |
| `density_prior` | raw-count based | `"uniform"` on single-cell-resolution data; array must sum to 1 |
| `lambda_r` | 0 | Entropy regulariser; > 0 makes each cell's placement more peaked |
| AUC threshold | > 0.6 good / < 0.4 poor | Generalisation to held-out genes (Step 6) |
| `TARGETS` | from the user (D6) | Genes to impute; must be expressed in the reference |
| `cluster_label` (`project_genes`) | same as mapping | Mismatch raises an obs-index error |
| Held-out fraction (gimVI) | 1/5 of panel | Genes withheld to score imputation |
| `max_epochs` (gimVI) | 200 | Lower for a quick CPU run; report it |
| `normalized` (gimVI) | True | Compare against library-size-normalised counts |
| `STAIN` / `geq` | from the image (D7) | Bright (fluorescent) vs dark (H&E) nuclei |
| `thresh` (`sq.im.segment`) | Otsu | Nucleus threshold; drives every count |
| `mask_circle` | True | Count only nuclei inside the round spot |
| `F_out` threshold | 0.5 | Probability for a reference cell to count as selected |
| `K` (CV folds) | 5 | More folds = smaller held-out sets, more runs |
| `EPOCHS` (CV) | 300 | Shorter than the main run to save time; report it |
| Seeds | 0, 1, 2 | Number of re-mappings for the stability check |
| Seed stability cutoff | r ~0.8 | Below it, the type's map is not stable |
| Poorly explained gene filter | `sparsity_sp < 0.5`, score < 0.3 | Separates reference mismatch from dropout |

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

### Recipe: One-Row Quality Summary for the Report

```python
summary = pd.DataFrame([{
    "mode": MODE,
    "n_training_genes": int(df_all["is_training"].sum()),
    "n_heldout_genes": int((~df_all["is_training"]).sum()),
    "mean_train_score": round(train["score"].mean(), 3),
    "mean_heldout_score": round(test["score"].mean(), 3),
    "auc_heldout": round(float(metrics["auc_score"]), 3),
}])
summary["verdict"] = np.where(summary["auc_heldout"] > 0.6, "good",
                              np.where(summary["auc_heldout"] >= 0.4, "moderate", "poor"))
summary.to_csv("tangram_validation_summary.csv", index=False)
print(summary.T)
```

## Expected Outputs

- `tangram_mapping.h5ad` - cell (or cluster) x spot probability matrix; `uns["train_genes_df"]`
- `tangram_sc_prep.h5ad`, `tangram_spatial.h5ad` - preprocessed inputs; spatial has `obs["density_prior"]`, `obsm["tangram_ct_pred"]`, `obs["tangram_top_type"]`
- `tangram_celltype_proportions.csv`, `tangram_celltype_maps.png` - per-spot proportions and maps
- `tangram_training_scores.png`, `tangram_gene_scores.csv`, `tangram_auc.png` - validation (Step 6)
- `tangram_validation_summary.csv` - one-row summary with a verdict (recipe)
- Gene Imputation: `tangram_projected_genes.h5ad` (spots x reference genes), `imputation_trust.csv`, imputed-only genes in `adata_sp.obsm["imputed_tangram"]`
- Nuclei Deconvolution: `tangram_ct_count_per_spot.csv` (cell type counts per spot), `tangram_segment_celltypes.csv` (every nucleus with coordinates and type)
- Advanced Validation: `tangram_cv.csv` (per-fold held-out scores)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `AssertionError` on `training_genes` / `overlap_genes` | `pp_adatas` not run on these exact objects | Re-run Step 3 right before mapping; load the saved `tangram_*.h5ad`, not the raw files |
| Very few training genes | Symbol mismatch (Ensembl IDs, species) | Map IDs to symbols; `pp_adatas` already lowercases |
| CUDA/CPU out of memory, or very slow | Too many cells in `mode="cells"` | Subsample the reference per type, or use `mode="clusters"` |
| One type dominates every spot | Reference lacks the tissue's major types or wrong state | Choose a better-matched reference |
| `ValueError: A cluster_label must be specified` | `mode="clusters"` without label | Pass `cluster_label=CELL_TYPE_KEY` |
| `The two AnnDatas need to have same obs index` | Clusters-mode map projected without `cluster_label` | Pass `cluster_label=CLUSTER_LABEL` to `project_genes` |
| `Invalid input for density_prior` | List instead of array, or does not sum to 1 | Pass a numpy array normalised to sum 1 |
| No held-out genes / `eval_metric` fails | `pp_adatas(genes=None)` used all genes | Re-run Step 3 with a marker subset |
| `TypeError` in `tg.plot_auc` | seaborn >= 0.12 positional args | Plot from `eval_metric` coordinates (Step 6) |
| Gene names lowercase afterwards | `pp_adatas` default `gene_to_lowercase=True` | Expected; use lowercase names downstream |
| Target gene missing | Not in reference, or uppercase name | Use lowercase names; pick a reference that measures it |
| `sc.pl.spatial` fails on projected data | Projected AnnData lacks `uns["spatial"]` | Scatter on `obsm["spatial"]` (Gene Imputation route) |
| Projected map mirrors one cell type's layout | Gene restricted to that type in the reference | Expected; state it, it is not independent evidence |
| `spatial genes needs to be subset of seq genes` | Panel genes absent from the reference, or case differs | Harmonise symbols; drop panel genes the reference lacks |
| gimVI `ImportError`/`AttributeError` | gimVI moved out of scvi-tools | `pixi add --pypi "scvi-tools<1.6"` |
| `Missing parameter ... Run sqidpy.im.calculate_image_features` | Features stored under `img_features` | Pass `key_added="image_features"` (Nucleus 2) |
| `KeyError: 'tangram_ct_pred'` in `deconvolve_cell_annotations` | Annotation not projected | Run the `tangram_ct_pred` block of Nucleus 4 first |
| Almost all spots have 0 nuclei | Low-res image, or wrong polarity | Use the full-res image; switch `geq` / stain branch |
| Counts far too high | Over-segmentation of texture | Raise `thresh` or smoothing `sigma` |
| `ValueError` about `target_count` | Missing or zero count | Check `cell_count` sum > 0 |
| `KeyError` / `FutureWarning` on integer key in `count_cell_annotations` | Non-string reference `obs_names` | String `obs_names` (Nucleus 1) before `pp_adatas` |
| Image and spots misaligned | Image is not the one Space Ranger used, or wrong scale | Use the Space Ranger input image at full resolution |

## Bundled Resources

Merged from four former Tangram skills: `spatial-mapping-tangram` (Steps 1-5, 7,
recipes), `spatial-mapping-validation` (Step 6, summary recipe, Route: Advanced
Validation), `scrna-spatial-gene-imputation` (Route: Gene Imputation) and
`spatial-transcriptomics-deconvolution-tangram` (Route: Nuclei Deconvolution).
Duplicated loading, normalisation and `pp_adatas` code was kept once (Steps 1-3).

## Related Skills

- `spatial-transcriptomics-deconvolution-cell2location` - probabilistic spot deconvolution alternative
- `spatial-transcriptomics-cell-type-annotation` - reference search/download; labels for single-cell-resolution data
- `spatial-panel-design` - choose panel genes so imputation is less needed
- `spatial-transcriptomics-analysis-squidpy` - squidpy image and neighbourhood analysis
- `spatial-transcriptomics-cell-cell-communication` - interactions between the mapped types

## References

- Biancalani et al. (2021) Tangram, Nature Methods: https://doi.org/10.1038/s41592-021-01264-7
- Tangram source and tutorials: https://github.com/broadinstitute/Tangram
- Tangram documentation: https://tangram-sc.readthedocs.io/
- squidpy + Tangram tutorial (demo data used here): https://squidpy.readthedocs.io/en/stable/notebooks/tutorials/tutorial_tangram.html
