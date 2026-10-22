---
name: "spatial-domain-detection"
description: "Spatial domain detection (tissue regions / niches) for spatial transcriptomics: SpaGCN (expression + spatial graph + H&E histology, Visium/ST), GraphST (self-supervised graph contrastive embedding, spots or cells) and UTAG (spatial message passing for Xenium/MERFISH/CosMx/IMC cells). Outputs a domain label per spot or cell, boundary refinement, cross-method agreement (ARI) and domain marker genes. For niches defined by the cell type composition of annotated cells use Step 7 of spatial-transcriptomics-cell-type-annotation; for neighbourhood enrichment and spatial statistics use spatial-transcriptomics-analysis-squidpy."
license: "CC-BY-4.0"
---

# Spatial Domain Detection

## Overview

Split a tissue section into spatially coherent regions (cortical layers, tumour
core vs stroma, germinal centres) from expression plus location. Each method
returns one domain label per spot or cell. Output: domain labels from one or
more methods, their agreement, domain marker genes and domain maps.

| Method | Data | Uses | Compute |
|---|---|---|---|
| SpaGCN | Visium / ST spots, optionally with the H&E image | Expression + spatial graph + histology colour | CPU, minutes |
| GraphST | Spots or cells up to ~30k observations | Contrastive graph embedding | GPU preferred (torch) |
| UTAG | Single-cell resolution (Xenium, MERFISH, CosMx, IMC) | Expression averaged over a radius | CPU, scales to 10^5-10^6 cells |
| Composition niches | Annotated single cells | Cell type mix of the neighbourhood | CPU; Step 7 of `spatial-transcriptomics-cell-type-annotation` |

Domains are clusters, not ground truth: run two methods and report where they
agree.

## When to Use

- Dividing a Visium or ST section into tissue regions such as layers, tumour core and stroma
- Using the H&E image together with expression to draw region boundaries (SpaGCN)
- Finding cellular niches in Xenium, MERFISH, CosMx or IMC data without labels (UTAG)
- Getting region labels to summarise deconvolved compositions or cell types by
- Checking whether two independent methods agree on the main boundaries
- Use Step 7 of `spatial-transcriptomics-cell-type-annotation` instead when cells are already annotated and niches should be defined by cell type mix
- For neighbourhood enrichment or spatially variable genes, use `spatial-transcriptomics-analysis-squidpy`

## Prerequisites

- **Input**: raw counts in `X` (or `layers["counts"]`) and coordinates in `obsm["spatial"]`
- **SpaGCN**: pulls torch. Its Louvain init needs `louvain`, which has no Python 3.13
  conda build or wheel and cannot be compiled here; without it use the k-means init (Step 3)
- **GraphST**: pulls torch; a CUDA GPU makes training ~10x faster; the dense
  spot-by-spot graph limits it to ~30k observations
- **UTAG**: not on PyPI; install from GitHub

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi scanpy SpaGCN GraphST
pixi add --pypi "utag @ git+https://github.com/ElementoLab/utag.git@main"
```

## Workflow

1. Load Visium data (or your own)
2. Preprocess
3. SpaGCN domains (spots, with histology)
4. GraphST domains (spots or cells)
5. UTAG domains (single-cell resolution)
6. Compare methods and characterise domains

### Step 1: Load Visium Data

For your own Space Ranger output set `OUTS` to the `outs/` folder and skip the
download. The demo is the 10x mouse brain (sagittal anterior) section.

```python
import json
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc

CACHE = Path("data_cache/V1_Mouse_Brain_Sagittal_Anterior")
BASE = ("https://cf.10xgenomics.com/samples/spatial-exp/1.1.0/V1_Mouse_Brain_Sagittal_Anterior/"
        "V1_Mouse_Brain_Sagittal_Anterior_")
CACHE.mkdir(parents=True, exist_ok=True)
for name in ["filtered_feature_bc_matrix.h5", "spatial.tar.gz"]:
    if not (CACHE / name).exists():
        urllib.request.urlretrieve(BASE + name, CACHE / name)          # ~20 MB + ~9 MB
if not (CACHE / "spatial").exists():
    with tarfile.open(CACHE / "spatial.tar.gz") as tar:
        tar.extractall(CACHE, filter="data")
OUTS = CACHE                                    # your data: Path("path/to/outs")

SPATIAL_DIR = OUTS / "spatial"
adata = sc.read_10x_h5(OUTS / "filtered_feature_bc_matrix.h5")
adata.var_names_make_unique()
cols = ["in_tissue", "array_row", "array_col", "pxl_row", "pxl_col"]
if (SPATIAL_DIR / "tissue_positions.csv").exists():                    # Space Ranger >= 2.0
    pos = pd.read_csv(SPATIAL_DIR / "tissue_positions.csv", index_col=0)
    pos.columns = cols
else:                                                                   # older, no header
    pos = pd.read_csv(SPATIAL_DIR / "tissue_positions_list.csv", header=None, index_col=0, names=cols)
adata.obs = adata.obs.join(pos, how="left")
adata.obsm["spatial"] = adata.obs[["pxl_col", "pxl_row"]].to_numpy(float)   # x, y in full-res pixels
scale = json.loads((SPATIAL_DIR / "scalefactors_json.json").read_text())
print(adata)
```

### Step 2: Preprocess

```python
adata.var["mt"] = adata.var_names.str.upper().str.startswith("MT-")
sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True)
sc.pp.filter_cells(adata, min_counts=500)       # Visium; use ~10 for imaging panels
sc.pp.filter_genes(adata, min_cells=10)
adata.layers["counts"] = adata.X.copy()         # SpaGCN and GraphST start from counts
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
print(f"{adata.n_obs} spots, {adata.n_vars} genes, median mt% {adata.obs['pct_counts_mt'].median():.1f}")
```

### Step 3: SpaGCN (Visium with H&E)

SpaGCN smooths expression over a graph whose edges combine spot distance and
histology colour, then clusters with a graph convolutional network. Coordinates
passed with the image must be **(image row, image column)** at the image's
scale.

```python
import random

import SpaGCN as spg
import torch
from PIL import Image

N_DOMAINS = 7
USE_HISTOLOGY = True

sp = adata.copy()
sp.X = sp.layers["counts"].toarray()            # dense: SpaGCN calls .A on sparse, removed in scipy>=1.14
hires = scale["tissue_hires_scalef"]
x_pix = (sp.obs["pxl_row"] * hires).round().astype(int).to_numpy()   # image row
y_pix = (sp.obs["pxl_col"] * hires).round().astype(int).to_numpy()   # image column
if USE_HISTOLOGY:
    img = np.array(Image.open(SPATIAL_DIR / "tissue_hires_image.png").convert("RGB"))
    beta = max(3, int(scale["spot_diameter_fullres"] * hires))       # spot size in hires pixels
    adj = spg.calculate_adj_matrix(x=x_pix, y=y_pix, x_pixel=x_pix, y_pixel=y_pix,
                                   image=img, beta=beta, alpha=1, histology=True)
else:
    adj = spg.calculate_adj_matrix(x=x_pix, y=y_pix, histology=False)

spg.prefilter_genes(sp, min_cells=3)
spg.prefilter_specialgenes(sp)                  # drops ERCC / MT- genes
sc.pp.normalize_total(sp)
sc.pp.log1p(sp)

l = spg.search_l(0.5, adj, start=0.01, end=1000, tol=0.01, max_run=100)   # p=0.5
r_seed = t_seed = n_seed = 100
res = spg.search_res(sp, adj, l, N_DOMAINS, start=0.7, step=0.1, tol=5e-3, lr=0.05,
                     max_epochs=20, r_seed=r_seed, t_seed=t_seed, n_seed=n_seed)
random.seed(r_seed); torch.manual_seed(t_seed); np.random.seed(n_seed)
clf = spg.SpaGCN()
clf.set_l(l)
clf.train(sp, adj, init_spa=True, init="louvain", res=res, tol=5e-3, lr=0.05, max_epochs=200)
y_pred, prob = clf.predict()
adata.obs["spagcn"] = pd.Categorical(y_pred.astype(str))

# Refinement: relabel a spot when most of its ring disagrees (spot grids only)
adj_2d = spg.calculate_adj_matrix(x=sp.obs["array_row"].to_numpy(), y=sp.obs["array_col"].to_numpy(),
                                  histology=False)
refined = spg.refine(sample_id=sp.obs_names.tolist(), pred=y_pred.tolist(), dis=adj_2d, shape="hexagon")
adata.obs["spagcn_refined"] = pd.Categorical(np.asarray(refined).astype(str))
print(adata.obs["spagcn_refined"].value_counts())
```

Without `louvain`, skip `search_res` and initialise with k-means:
`clf.train(sp, adj, init_spa=True, init="kmeans", n_clusters=N_DOMAINS, tol=5e-3, lr=0.05, max_epochs=200)`.

`shape="hexagon"` for Visium, `"square"` for legacy ST. Raise `alpha` to give
histology more weight; set `USE_HISTOLOGY = False` when the image is missing or
poorly registered.

### Step 4: GraphST

GraphST learns a spatially smoothed embedding by contrasting the real graph
with a corrupted one, then clusters it. Give it raw counts: it selects 3,000
HVGs (seurat_v3), normalises, log-transforms and scales internally.

```python
import torch
from GraphST import GraphST
from GraphST.utils import clustering

gst = sc.AnnData(adata.layers["counts"].copy(), obs=adata.obs[[]].copy(), var=adata.var[[]].copy())
gst.obsm["spatial"] = adata.obsm["spatial"].copy()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# datatype: "10X" (spot grids, imaging cells); "Slide" or "Stereo" for Slide-seq / Stereo-seq (KNN graph)
model = GraphST.GraphST(gst, device=device, random_seed=42, datatype="10X")
gst = model.train()                             # 600 epochs; embedding in obsm["emb"]

# Scans Leiden resolution from `end` down to `start` until exactly N_DOMAINS clusters appear
clustering(gst, n_clusters=N_DOMAINS, radius=50, method="leiden",
           start=0.1, end=2.0, increment=0.01, refinement=False)
adata.obs["graphst"] = pd.Categorical(gst.obs["domain"].astype(str).to_numpy())
adata.obsm["graphst_emb"] = gst.obsm["emb"]
print(adata.obs["graphst"].value_counts())
```

The GraphST authors recommend `method="mclust"` (needs R with the `mclust`
package and `rpy2`); `refinement=True` relabels each observation by its
`radius` nearest neighbours.

### Step 5: UTAG (Single-Cell Resolution)

UTAG averages each cell's expression over neighbours within `max_dist`, then
clusters. Input: one `.h5ad` of cells with log-normalised `X` and
`obsm["spatial"]` in microns (e.g. the output of
`spatial-transcriptomics-cell-type-annotation`).

```python
from scipy.spatial import cKDTree
from sklearn.neighbors import NearestNeighbors
from utag import utag

cells = sc.read_h5ad("celltype_annotated.h5ad")
SLIDE_KEY = None                     # obs column with sample/section IDs, if several
MIN_NICHES, MIN_CLUSTER_SIZE = 5, 100

# max_dist: radius where a typical cell has ~3 neighbours (estimated per slide)
slides = cells.obs[SLIDE_KEY].unique() if SLIDE_KEY else [None]
d3 = []
for s in slides:
    xy = cells.obsm["spatial"] if s is None else cells[cells.obs[SLIDE_KEY] == s].obsm["spatial"]
    d3.append(cKDTree(xy).query(xy[:20000], k=4)[0][:, 3])
MAX_DIST = float(np.ceil(np.median(np.concatenate(d3))))
print(f"max_dist = {MAX_DIST}")

for resolution in [0.05, 0.1, 0.3, 0.5]:          # coarsest resolution giving enough niches
    out = utag(cells, slide_key=SLIDE_KEY, max_dist=MAX_DIST, normalization_mode="l1_norm",
               apply_umap=False, apply_clustering=True, clustering_method=["leiden"],
               resolutions=[resolution])
    key = f"UTAG Label_leiden_{resolution}"
    print(resolution, out.obs[key].nunique())
    if out.obs[key].nunique() >= MIN_NICHES:
        break

# Merge clusters smaller than MIN_CLUSTER_SIZE (within each slide) into the nearest larger one
lab = out.obs[key].astype(str).copy()
for s in slides:
    m = np.ones(out.n_obs, bool) if s is None else (out.obs[SLIDE_KEY] == s).to_numpy()
    counts = lab[m].value_counts()
    small = lab[m].isin(counts[counts < MIN_CLUSTER_SIZE].index).to_numpy()
    if small.any() and (~small).any():
        xy = out.obsm["spatial"][m]
        nn = NearestNeighbors(n_neighbors=1).fit(xy[~small])
        idx = nn.kneighbors(xy[small], return_distance=False).ravel()
        lab.iloc[np.flatnonzero(m)[small]] = lab[m].to_numpy()[~small][idx]
cells.obs["utag"] = pd.Categorical(lab.reindex(cells.obs_names))   # utag may reorder cells by slide
print(cells.obs["utag"].value_counts())
```

### Step 6: Compare Methods and Characterise Domains

```python
from sklearn.metrics import adjusted_rand_score

ari = adjusted_rand_score(adata.obs["spagcn_refined"], adata.obs["graphst"])
print(f"SpaGCN vs GraphST ARI: {ari:.2f}")      # > ~0.5: the main boundaries agree
print(pd.crosstab(adata.obs["spagcn_refined"], adata.obs["graphst"]))

import matplotlib.pyplot as plt

axes = sc.pl.embedding(adata, basis="spatial", color=["spagcn_refined", "graphst"], size=1.5, show=False)
for ax in axes:
    ax.invert_yaxis()                            # pixel y grows downwards
plt.savefig("domains_spatial.png", dpi=150, bbox_inches="tight")

DOMAIN = "spagcn_refined"
sc.tl.rank_genes_groups(adata, DOMAIN, method="wilcoxon")
markers = sc.get.rank_genes_groups_df(adata, group=None)
markers.to_csv("domain_markers.csv", index=False)
top = (markers[markers["logfoldchanges"] > 0].groupby("group").head(8)
       .groupby("group")["names"].apply(", ".join))
print(top)
adata.obs[["spagcn", "spagcn_refined", "graphst"]].to_csv("spatial_domains.csv")
adata.write_h5ad("spatial_domains.h5ad", compression="gzip")
```

Name domains from their markers (e.g. `Mbp` / `Plp1` = white matter, layer
markers in cortex). If cell type labels or cell2location abundances exist,
`pd.crosstab(domain, cell_type, normalize="index")` shows what each domain is
made of. With an expert annotation, report ARI against it instead.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `N_DOMAINS` | 7 | Target number of domains (SpaGCN, GraphST); try 5-15 and compare |
| SpaGCN `p` (`search_l`) | 0.5 | Share of expression taken from neighbours; higher = smoother domains |
| SpaGCN `alpha` | 1 | Weight of histology colour in the graph |
| SpaGCN `shape` | `"hexagon"` | Neighbour ring used in refinement (`"square"` for ST) |
| GraphST `datatype` | `"10X"` | `"Slide"` / `"Stereo"` switch to a KNN graph for dense data |
| GraphST `radius` | 50 | Neighbours used when `refinement=True` |
| UTAG `max_dist` | auto (~3 neighbours) | Averaging radius in coordinate units; larger = coarser niches |
| UTAG `resolutions` | 0.05-0.5 | Leiden resolution on the averaged expression |
| `MIN_CLUSTER_SIZE` | 100 | Smaller UTAG clusters are merged into the nearest larger one |

## Common Recipes

### Recipe: Choose the Number of Domains

`N_DOMAINS` is a guess unless the anatomy fixes it. Scan k on the GraphST
embedding and look for a plateau or peak in silhouette:

```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

emb = adata.obsm["graphst_emb"]
rng = np.random.default_rng(0)
sub = rng.choice(emb.shape[0], min(emb.shape[0], 5000), replace=False)
scores = {}
for k in range(4, 16):
    labels = KMeans(k, n_init=10, random_state=0).fit_predict(emb)
    scores[k] = silhouette_score(emb[sub], labels[sub])
print(pd.Series(scores).round(3))
```

Prefer a k that matches known anatomy over the highest score; report the scan.

### Recipe: What Each Domain Is Made Of

With cell type labels (single cells) or cell2location abundances (spots):

```python
DOMAIN = "spagcn_refined"
if "cell_type" in adata.obs:
    comp = pd.crosstab(adata.obs[DOMAIN], adata.obs["cell_type"], normalize="index")
else:
    abund = pd.read_csv("cell2location_abundance.csv", index_col=0).reindex(adata.obs_names)
    prop = abund.div(abund.sum(axis=1), axis=0)
    comp = prop.groupby(adata.obs[DOMAIN], observed=True).mean()
comp.round(3).to_csv("domain_composition.csv")
print(comp.apply(lambda r: ", ".join(f"{k} {v:.0%}" for k, v in r.nlargest(3).items()), axis=1))
```

### Recipe: Domain Boundaries and Interfaces

Which domains touch, and which spots sit on a boundary (interfaces such as the
tumour edge are often where the biology is):

```python
import squidpy as sq

sq.gr.spatial_neighbors(adata, coord_type="grid", n_rings=1)   # imaging cells: coord_type="generic", n_neighs=10
A = adata.obsp["spatial_connectivities"].tocoo()
lab = adata.obs[DOMAIN].astype(str).to_numpy()
edges = pd.DataFrame({"a": lab[A.row], "b": lab[A.col]})
touch = pd.crosstab(edges["a"], edges["b"])
print(touch)                                       # off-diagonal counts = shared boundary length

diff = lab[A.row] != lab[A.col]
boundary = np.zeros(adata.n_obs, bool)
boundary[A.row[diff]] = True
adata.obs["domain_boundary"] = boundary
print(f"boundary spots: {boundary.mean():.0%}")
```

## Expected Outputs

- `spatial_domains.csv` - `spagcn`, `spagcn_refined`, `graphst` labels per spot
- `spatial_domains.h5ad` - data with domain labels and `obsm["graphst_emb"]`
- `domain_markers.csv` - Wilcoxon markers per domain
- `domains_spatial.png` - domain maps on tissue coordinates
- `domain_composition.csv` - cell type mix per domain (recipe)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| SpaGCN `UnboundLocalError: y_pred` | `init` other than `"louvain"` / `"kmeans"` | Use `init="louvain"` (needs `louvain`) or `init="kmeans"` with `n_clusters` |
| SpaGCN `AttributeError: ... has no attribute 'A'` | Sparse `X` with scipy >= 1.14 | Densify `X` before SpaGCN (Step 3 does) |
| SpaGCN domains ignore the tissue image | Coordinates swapped or at full-res scale on the hires image | Pass `pxl_row`/`pxl_col` scaled by `tissue_hires_scalef`, row first |
| GraphST `AssertionError` in clustering | No Leiden resolution gives exactly `n_clusters` | Widen `end` (e.g. 3.0), change `N_DOMAINS` by 1, or use `mclust` |
| GraphST out of memory | Dense n x n adjacency | Use UTAG for >30k cells, or run per region |
| GraphST fails on a targeted panel (< 3,000 genes) | Internal `n_top_genes=3000` | Set `gst.var["highly_variable"] = True`, then normalise, log1p and scale yourself before `GraphST.GraphST` |
| UTAG gives one huge niche | `max_dist` too large | Lower `max_dist` or raise resolution |
| Fragmented, salt-and-pepper domains | Too little spatial smoothing | Raise SpaGCN `p`, use refinement, or raise UTAG `max_dist` |

## Related Skills

- `spatial-transcriptomics-cell-type-annotation` - cell labels; its Step 7 builds composition niches
- `spatial-transcriptomics-deconvolution-cell2location` - cell type abundance per spot to interpret domains
- `spatial-transcriptomics-analysis-squidpy` - neighbourhood enrichment, co-occurrence, spatially variable genes
- `spatial-transcriptomics-cell-cell-communication` - signalling between cell types inside or across domains
- `trajectory-inference` - pseudotime within a domain

## References

- Hu et al. (2021) SpaGCN, Nature Methods: https://doi.org/10.1038/s41592-021-01255-8
- Long et al. (2023) GraphST, Nature Communications: https://doi.org/10.1038/s41467-023-36796-3
- Kim et al. (2022) UTAG, Nature Methods: https://doi.org/10.1038/s41592-022-01657-2
- SpaGCN source: https://github.com/jianhuupenn/SpaGCN
- GraphST source: https://github.com/JinmiaoChenLab/GraphST
- UTAG source: https://github.com/ElementoLab/utag
