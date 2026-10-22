---
name: "spatial-transcriptomics-deconvolution-cell2location"
description: "Visium and other spot-based spatial transcriptomics (Slide-seq, ST) cell type deconvolution with cell2location: load Space Ranger output, get a tissue-matched scRNA-seq reference from CELLxGENE, learn cell type signatures, estimate cell type abundance per spot with posterior uncertainty, and check the maps against marker genes. Default route for 'annotate cell types' on Visium when a GPU is available. Limits: needs a tissue- and state-matched reference; the default 30000 epochs take hours on CPU, so without a GPU it runs only with fewer epochs (exploratory maps) and can exceed one execution call's time limit. For fast per-spot proportions on CPU use spatial-mapping-tangram (clusters mode); for single-cell-resolution data (Xenium, MERFISH, CosMx) use spatial-transcriptomics-cell-type-annotation."
license: "CC-BY-4.0"
---

# Spot Deconvolution with cell2location

## Overview

Each Visium spot (55 um) holds several cells, so cell types are reported as an
abundance per spot, not one label per spot. cell2location learns a signature
per cell type from a scRNA-seq reference, then explains every spot's counts as
a mixture of those signatures. Output: estimated cell counts and proportions
per spot and type, maps on the tissue, and a marker check of each map.

## When to Use

- Asked to "annotate cell types" or "find where cell types are" on Visium, Slide-seq or ST data
- Mapping a published scRNA-seq atlas onto a spot-based section
- Comparing cell type composition between tissue regions or sections
- Producing per-spot compositions for downstream niche or communication analysis
- Getting abundance estimates with posterior uncertainty (5% quantile)
- Use `spatial-transcriptomics-cell-type-annotation` instead when each observation is one cell (Xenium, MERFISH, CosMx)
- Use `spatial-mapping-tangram` (constrained deconvolution route) instead when you need single cells placed on segmented nuclei of the histology image

## Prerequisites

- **Input**: Space Ranger output (`filtered_feature_bc_matrix.h5` and the `spatial/` folder) with raw counts
- **Reference**: scRNA-seq with raw counts and `obs["cell_type"]` (Step 2 fetches one)
- **Compute**: GPU strongly preferred. On CPU the spatial model (Step 4) needs fewer epochs than the
  default, chosen by the timing probe there; the reference model (Step 3) takes minutes
- **Python packages**: `cell2location` (pulls torch, scvi-tools, pyro; large), `scanpy`

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi scanpy cell2location
```

## Pre-flight Interview

```yaml
decisions:
  - id: D1
    param: STATE
    kind: required
    source: user
    ask: "Which tissue is this, and in what state (healthy, or which tumour or disease)?"
    default: null

  - id: D2
    param: referenceSource
    kind: required
    source: user
    ask: "Do you have a scRNA/snRNA-seq reference from the same tissue and state (h5ad with raw counts and a cell type column), or should I search public data (CELLxGENE)?"
    default: null

  - id: D3
    param: CELL_TYPE_KEY
    kind: required
    source: data
    depends_on: [D2]
    ask: "Which reference column holds the cell types, and at what level: major lineages or fine subtypes?"
    default: null

  - id: D4
    param: COMPUTE_ROUTE
    kind: required
    source: user
    ask: "Without a GPU, cell2location runs only with fewer training epochs (exploratory maps, still long). Run it that way, or get per-spot proportions quickly with Tangram (clusters mode)?"
    default: "cell2location with MAX_EPOCHS from the Step 4 timing probe, reported as exploratory"

  - id: D5
    param: N_CELLS_PER_SPOT
    kind: required
    source: user
    depends_on: [D1]
    ask: "About how many nuclei does one spot hold in this tissue? I can use the tutorial value of 30 if you do not know."
    default: "30"

  - id: D6
    param: SAMPLE_KEY
    kind: required
    source: data
    skip_if: "a single section"
    ask: "There are several sections: fit them in one model (shared cell type signatures, per-section sensitivity) or each on its own?"
    default: "one model with batch_key = section"

  - id: D7
    param: DETECTION_ALPHA
    kind: optional
    source: user
    ask: "Does RNA detection vary strongly across the slide (uneven tissue quality)?"
    default: "20 (uneven detection); 200 when detection is even"

  - id: D8
    param: REF_BATCH_KEY
    kind: optional_conditional
    source: data
    depends_on: [D2]
    ask: "The reference pools several donors or studies: correct the signatures for that column?"
    default: "batch_key = donor_id when the reference has more than one donor"
```

Ask D1, D2 and D4 together, with D6 when there is more than one section. The
tissue and state come from the user: a sample name will not be found in public
databases, so do not search the web for it. Spot data cannot tell a tumour from
healthy tissue reliably; if the user does not know, propose a tissue from the
top marker genes and ask them to confirm. If D4 picks Tangram, use
`spatial-mapping-tangram` with `MODE = "clusters"` and the same reference.

## Workflow

### Step 1: Load Visium Output

```python
import os
import numpy as np
import pandas as pd
import scanpy as sc

H5 = "path/to/filtered_feature_bc_matrix.h5"
SPATIAL_DIR = "path/to/spatial"

st = sc.read_10x_h5(H5)
st.var_names_make_unique()
if os.path.exists(f"{SPATIAL_DIR}/tissue_positions.csv"):           # Space Ranger >= 2.0
    pos = pd.read_csv(f"{SPATIAL_DIR}/tissue_positions.csv", index_col=0)
else:                                                                  # older, no header
    pos = pd.read_csv(f"{SPATIAL_DIR}/tissue_positions_list.csv", header=None, index_col=0,
                      names=["barcode", "in_tissue", "array_row", "array_col",
                             "pxl_row_in_fullres", "pxl_col_in_fullres"])
st.obsm["spatial"] = pos.loc[st.obs_names, ["pxl_col_in_fullres", "pxl_row_in_fullres"]].to_numpy()
st = st[:, ~st.var_names.str.startswith("MT-")].copy()   # mito reads are not cell type signal
print(st)
print(f"median UMIs/spot: {np.median(np.asarray(st.X.sum(1)).ravel()):.0f}")
```

### Step 2: Get a Reference

Use the tissue and state from D1. Without the user's own reference (D2),
search and download a subsampled CELLxGENE reference with Steps 3-4 of
`spatial-transcriptomics-cell-type-annotation` (same code, with `GENES = None` and
`MAX_PER_TYPE = 300` - signatures need every gene), and load it:

```python
ref = sc.read_h5ad("reference.h5ad")      # X = raw counts, obs["cell_type"]
print(ref.obs["cell_type"].value_counts())
```

Types with fewer than ~20 cells cannot yield a stable signature; Step 3 drops them.

### Step 3: Fit Reference Signatures

```python
from cell2location.models import RegressionModel
from cell2location.utils.filtering import filter_genes

ref = ref[ref.obs["cell_type"].map(ref.obs["cell_type"].value_counts()) >= 20].copy()
selected = filter_genes(ref, cell_count_cutoff=5, cell_percentage_cutoff2=0.03, nonz_mean_cutoff=1.12)
ref = ref[:, selected].copy()

RegressionModel.setup_anndata(ref, labels_key="cell_type")   # add batch_key="donor_id" for multi-donor references
ref_model = RegressionModel(ref)
ref_model.train(max_epochs=250)
ref = ref_model.export_posterior(ref, sample_kwargs={"num_samples": 1000, "batch_size": 2500})

factors = ref.uns["mod"]["factor_names"]
inf_aver = ref.varm["means_per_cluster_mu_fg"][[f"means_per_cluster_mu_fg_{f}" for f in factors]].copy()
inf_aver.columns = factors                     # genes x cell types
print(inf_aver.shape)
```

### Step 4: Fit the Spatial Model

```python
from cell2location.models import Cell2location

shared = np.intersect1d(st.var_names, inf_aver.index)
print(f"shared genes: {len(shared)}")
st = st[:, shared].copy()
inf_aver = inf_aver.loc[shared]

N_CELLS_PER_SPOT = 30       # D5; tutorial value; set from nuclei counted on the H&E for this tissue
DETECTION_ALPHA = 20        # D7; 20 when RNA detection varies across the slide; also try 200
Cell2location.setup_anndata(st)
```

On CPU, time a short run on a throwaway model before choosing `MAX_EPOCHS`.
The default 30000 epochs often takes hours there, longer than one execution
call is allowed to run in many sandboxes:

```python
import time
import torch

probe = Cell2location(st, cell_state_df=inf_aver,
                      N_cells_per_location=N_CELLS_PER_SPOT, detection_alpha=DETECTION_ALPHA)
t0 = time.time()
probe.train(max_epochs=50, batch_size=None, train_size=1)
sec_per_epoch = (time.time() - t0) / 50
del probe

BUDGET_S = 20 * 60          # leave headroom under the per-call time limit
if torch.cuda.is_available():
    MAX_EPOCHS = 30000      # tutorial default
else:
    MAX_EPOCHS = int(min(30000, BUDGET_S / sec_per_epoch) // 1000 * 1000)
print(f"{sec_per_epoch:.2f} s/epoch -> MAX_EPOCHS = {MAX_EPOCHS} (30000 needs ~{sec_per_epoch * 30000 / 3600:.1f} h)")
```

Below ~3000 epochs the maps are too rough to report; switch to the Tangram
route of D4 instead. Then fit:

```python
st_model = Cell2location(st, cell_state_df=inf_aver,
                         N_cells_per_location=N_CELLS_PER_SPOT, detection_alpha=DETECTION_ALPHA)
st_model.train(max_epochs=MAX_EPOCHS, batch_size=None, train_size=1)
```

Report `MAX_EPOCHS` with the maps; anything below 30000 is exploratory.

### Step 5: Export and Check Abundances

```python
st = st_model.export_posterior(st, sample_kwargs={"num_samples": 1000, "batch_size": st_model.adata.n_obs})
abund = pd.DataFrame(st.obsm["q05_cell_abundance_w_sf"].to_numpy(), index=st.obs_names, columns=factors)
prop = abund.div(abund.sum(1), axis=0)          # per-spot proportions
abund.to_csv("cell2location_abundance.csv")
prop.to_csv("cell2location_proportions.csv")
st.write_h5ad("cell2location_spatial.h5ad", compression="gzip")
print(prop.mean().sort_values(ascending=False).head(10))
```

Plot the most abundant types on the tissue:

```python
import matplotlib.pyplot as plt

top = prop.mean().nlargest(6).index
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
for ax, ct in zip(axes.flat, top):
    sc_ = ax.scatter(st.obsm["spatial"][:, 0], st.obsm["spatial"][:, 1], c=abund[ct], s=8, cmap="magma")
    ax.invert_yaxis(); ax.set_title(ct); ax.axis("off"); fig.colorbar(sc_, ax=ax, shrink=0.6)
plt.tight_layout(); plt.savefig("cell2location_top_types.png", dpi=150)
```

Check each map against a marker the user's biology predicts (for example
plasma cells vs `JCHAIN`): abundance and marker expression should correlate
across spots. A type whose map ignores its own markers is not supported.

```python
st_norm = st.copy(); sc.pp.normalize_total(st_norm); sc.pp.log1p(st_norm)
checks = {"Plasma cell": "JCHAIN"}             # fill with types present in `factors`
for ct, gene in checks.items():
    if ct in abund and gene in st_norm.var_names:
        expr = np.asarray(st_norm[:, gene].X.todense()).ravel()
        print(f"{ct} vs {gene}: r = {np.corrcoef(abund[ct], expr)[0, 1]:.2f}")
```

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| Reference state | from the user | Healthy vs disease signatures; the most consequential choice |
| `N_CELLS_PER_SPOT` | 30 | Prior on spot density; scales absolute abundance. Set from histology |
| `DETECTION_ALPHA` | 20 | Regularises per-spot sensitivity; 200 when detection is even |
| `MAX_EPOCHS` (spatial) | 30000 | Convergence; fewer epochs = rougher maps |
| min cells per type | 20 | Types below it are dropped from the reference |

## Common Recipes

### Recipe: Several Sections in One Model

Fit all sections together so signatures are shared while sensitivity is
estimated per section:

```python
sections = {"S1": ("s1/filtered_feature_bc_matrix.h5", "s1/spatial"),
            "S2": ("s2/filtered_feature_bc_matrix.h5", "s2/spatial")}
parts = {}
for name, (h5, sp_dir) in sections.items():
    a = sc.read_10x_h5(h5); a.var_names_make_unique()
    pos = pd.read_csv(f"{sp_dir}/tissue_positions.csv", index_col=0)
    a.obsm["spatial"] = pos.loc[a.obs_names, ["pxl_col_in_fullres", "pxl_row_in_fullres"]].to_numpy()
    parts[name] = a
st = sc.concat(parts, label="sample", index_unique="-")
st = st[:, np.intersect1d(st.var_names, inf_aver.index)].copy()
Cell2location.setup_anndata(st, batch_key="sample")
```

Then build and train the model as in Step 4.

### Recipe: Maps over the H&E Image

`squidpy` reads the Space Ranger folder with its image and draws spots on it:

```python
import squidpy as sq

st_img = sq.read.visium("path/to/spaceranger_outs")   # folder with filtered_feature_bc_matrix.h5 + spatial/
st_img.var_names_make_unique()
st_img = st_img[abund.index].copy()
st_img.obs[list(top)] = abund.loc[st_img.obs_names, top].to_numpy()
sq.pl.spatial_scatter(st_img, color=list(top), ncols=3, cmap="magma", save="cell2location_on_he.png")
```

### Recipe: Dominant Type and Composition per Region

```python
st.obs["dominant_type"] = prop.idxmax(axis=1)
st.obs["dominant_share"] = prop.max(axis=1)
print(st.obs["dominant_type"].value_counts())

REGION_KEY = "domain"     # e.g. from spatial-domain-detection or a pathologist's annotation
if REGION_KEY in st.obs:
    region_comp = prop.groupby(st.obs[REGION_KEY]).mean().round(3)
    region_comp.to_csv("composition_per_region.csv")
    print(region_comp)
```

A spot's dominant type is a summary, not a label: report its share alongside it.

## Expected Outputs

- `cell2location_abundance.csv` - estimated cells per spot and type (5% posterior quantile)
- `cell2location_proportions.csv` - per-spot proportions
- `cell2location_spatial.h5ad` - full posterior in `obsm`
- `cell2location_top_types.png` - maps of the most abundant types

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Few shared genes | Symbols vs Ensembl IDs | Use symbols on both sides (`feature_name` in Census data) |
| Training very slow | CPU, 30000 epochs | Lower `MAX_EPOCHS`, state it in the report; or run on GPU |
| One type dominates every spot | Reference missing the tissue's major types | Choose a better-matched reference |
| `KeyError: means_per_cluster_mu_fg_...` | `export_posterior` not run | Run it on the reference before Step 4 |
| Out of memory in export | Large `batch_size` | Lower `batch_size` in `sample_kwargs` |
| Total abundance does not follow nuclei density | `DETECTION_ALPHA` too strong | Compare 20 and 200; keep the one that follows histology |

## Related Skills

- `spatial-transcriptomics-cell-type-annotation` - single-cell-resolution platforms; its Steps 3-4 fetch the reference
- `spatial-mapping-tangram` - Tangram mapping, incl. per-cell mapping with histology segmentation
- `spatial-domain-detection` - tissue regions to summarise compositions by
- `spatial-transcriptomics-cell-cell-communication` - interactions on the deconvolved slide

## References

- Kleshchevnikov et al. (2022) cell2location, Nature Biotechnology: https://doi.org/10.1038/s41587-021-01139-4
- cell2location documentation: https://cell2location.readthedocs.io/en/latest/
- cell2location tutorial (hyperparameter guidance): https://cell2location.readthedocs.io/en/latest/notebooks/cell2location_tutorial.html
- cell2location source: https://github.com/BayraktarLab/cell2location
- squidpy Visium reader: https://squidpy.readthedocs.io/en/stable/api/squidpy.read.visium.html
