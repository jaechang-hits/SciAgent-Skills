---
name: "trajectory-inference"
description: "Trajectory inference and cell fate mapping for single-cell and spatial transcriptomics: PAGA graph + diffusion pseudotime (no velocity needed), scVelo RNA velocity (stochastic / dynamical, from spliced/unspliced counts), CellRank 2 terminal states, fate probabilities and lineage drivers, then pseudotime and fates mapped on tissue with a spatial autocorrelation check. Outputs pseudotime, velocity streams, fate probability tables. Imaging panels (Xenium, MERFISH) have no unspliced counts: use PAGA/DPT or the CellRank pseudotime kernel. For a basic PAGA recipe inside a standard scRNA-seq workflow see scanpy-scrna-seq."
license: "CC-BY-4.0"
---

# Trajectory Inference

## Overview

Order cells along differentiation or activation paths and estimate where each
cell is heading. Output: pseudotime, velocity streams, terminal states and
fate probabilities, and on spatial data their maps on the tissue with a check
of whether the ordering follows space. Three layers, each optional on top of
the previous one:

| Method | Needs | Gives |
|---|---|---|
| PAGA + DPT | Clusters, neighbour graph, a chosen root cluster | Cluster connectivity graph, pseudotime |
| scVelo | `layers["spliced"]` and `layers["unspliced"]` | Direction of change per cell (velocity) |
| CellRank 2 | A transition kernel (velocity or pseudotime) | Terminal states, fate probabilities, driver genes |

Spliced/unspliced counts come from velocyto, STARsolo (`--soloFeatures Gene
Velocyto`) or kallisto|bustools run on the reads; for Visium and Slide-seq
run them on the Space Ranger / pipeline BAM. Imaging platforms (Xenium,
MERFISH, CosMx) count probes, not introns, so velocity is not available there.

## When to Use

- Ordering cells along a differentiation or activation path from a chosen start
- Estimating where cells are heading from spliced/unspliced counts (RNA velocity)
- Finding terminal states, fate probabilities and the genes driving each fate
- Checking whether a developmental or activation ordering is laid out in tissue space
- Finding genes that change along the inferred path
- Use `scanpy-scrna-seq` instead when you only need a quick PAGA graph inside a standard scRNA-seq workflow
- For tissue regions rather than cell-state paths, use `spatial-domain-detection`

## Prerequisites

- **Input**: raw counts plus a cluster or cell type column; for velocity, the two layers above
- **Spatial data**: coordinates in `obsm["spatial"]` for Step 6
- **Python packages**: `scvelo`, `cellrank` (CellRank 2.x needs Python >= 3.12; CPU is fine)

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi scvelo cellrank scanpy
```

## Workflow

1. Load data and check layers
2. Preprocess and build the neighbour graph
3. PAGA and diffusion pseudotime
4. RNA velocity (scVelo)
5. Terminal states and fate probabilities (CellRank)
6. Map pseudotime and fates on the tissue

### Step 1: Load Data

```python
import numpy as np
import pandas as pd
import scanpy as sc

adata = sc.read_h5ad("path/to/data.h5ad")        # your data
# Demo with spliced/unspliced layers (mouse pancreas endocrinogenesis, downloaded to ./data on first use):
# import scvelo as scv; adata = scv.datasets.pancreas()
CLUSTER_KEY = "clusters"                          # cell type / cluster column

has_velocity_layers = {"spliced", "unspliced"} <= set(adata.layers)
print(adata)
print(f"velocity layers: {has_velocity_layers}; spatial: {'spatial' in adata.obsm}")
print(adata.obs[CLUSTER_KEY].value_counts())
```

### Step 2: Preprocess and Neighbour Graph

Uses the scVelo order (filter on spliced+unspliced, normalise all layers, then
log `X`). Without velocity layers, the scanpy lines alone apply.

```python
import scvelo as scv

if has_velocity_layers:
    scv.pp.filter_genes(adata, min_shared_counts=20)
    scv.pp.normalize_per_cell(adata)              # normalises X, spliced, unspliced
else:
    adata.layers["counts"] = adata.X.copy()
    sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=2000)     # imaging panels: skip, use all genes
sc.pp.pca(adata, n_comps=30)
sc.pp.neighbors(adata, n_pcs=30, n_neighbors=30, random_state=0)
if "X_umap" not in adata.obsm:
    sc.tl.umap(adata)
adata.obs[CLUSTER_KEY] = adata.obs[CLUSTER_KEY].astype("category")
```

### Step 3: PAGA and Diffusion Pseudotime

The root cluster is a biological choice (progenitor, naive state); ask the user
when it is not obvious from markers.

```python
ROOT_GROUP = "Ngn3 low EP"                        # root cluster name

sc.tl.paga(adata, groups=CLUSTER_KEY)
sc.pl.paga(adata, threshold=0.05, show=False, save="_graph.png")
groups = adata.obs[CLUSTER_KEY].cat.categories
paga_adj = pd.DataFrame(adata.uns["paga"]["connectivities"].toarray(), index=groups, columns=groups)
paga_adj.to_csv("paga_adjacency.csv")

# Root = the root-cluster cell at the extreme of diffusion component 1
# (the first cell of the cluster is arbitrary and shifts the whole pseudotime)
sc.tl.diffmap(adata)
dc1 = adata.obsm["X_diffmap"][:, 1]
in_root = (adata.obs[CLUSTER_KEY] == ROOT_GROUP).to_numpy()
assert in_root.any(), f"{ROOT_GROUP} not in {list(groups)}"
side = np.sign(dc1[in_root].mean() - dc1.mean()) or 1.0
adata.uns["iroot"] = int(np.flatnonzero(in_root)[np.argmax(side * dc1[in_root])])
sc.tl.dpt(adata)
print(adata.obs.groupby(CLUSTER_KEY, observed=True)["dpt_pseudotime"].median().sort_values())
sc.pl.umap(adata, color=[CLUSTER_KEY, "dpt_pseudotime"], show=False, save="_pseudotime.png")
```

If the median pseudotime per cluster does not follow the expected order, the
root or the clustering is wrong; DPT is not a test of the order.

### Step 4: RNA Velocity (scVelo)

```python
MODE = "stochastic"                               # "dynamical" is slower but gives latent time

scv.pp.moments(adata, n_pcs=None, n_neighbors=None)      # reuses the Step 2 graph
if MODE == "dynamical":
    scv.tl.recover_dynamics(adata, n_jobs=8)
scv.tl.velocity(adata, mode=MODE)
scv.tl.velocity_graph(adata, n_jobs=8)
scv.tl.velocity_confidence(adata)
if MODE == "dynamical":
    scv.tl.latent_time(adata)

print(f"velocity genes: {int(adata.var['velocity_genes'].sum())}")
print(adata.obs.groupby(CLUSTER_KEY, observed=True)["velocity_confidence"].median().round(2))
scv.pl.velocity_embedding_stream(adata, basis="umap", color=CLUSTER_KEY, show=False,
                                 save="velocity_stream_umap.png")
```

Low `velocity_confidence` (< ~0.5) in a cluster means its arrows are noise;
say so rather than interpreting them. Fewer than ~100 velocity genes usually
means too few unspliced reads.

### Step 5: Terminal States and Fate Probabilities (CellRank 2)

```python
import cellrank as cr

N_STATES = 8                                      # macrostates; try a few values
if has_velocity_layers:
    vk = cr.kernels.VelocityKernel(adata).compute_transition_matrix()
    ck = cr.kernels.ConnectivityKernel(adata).compute_transition_matrix()
    kernel = 0.8 * vk + 0.2 * ck                  # connectivity term damps velocity noise
else:
    kernel = cr.kernels.PseudotimeKernel(adata, time_key="dpt_pseudotime").compute_transition_matrix()

g = cr.estimators.GPCCA(kernel)
g.compute_schur(n_components=20)
g.compute_macrostates(n_states=N_STATES, cluster_key=CLUSTER_KEY)
g.predict_terminal_states()                       # or g.set_terminal_states(states=["Alpha", "Beta"])
print("terminal states:", list(g.terminal_states.cat.categories))

g.compute_fate_probabilities()
fp = g.fate_probabilities                         # also in adata.obsm["lineages_fwd"]
fate = pd.DataFrame(np.asarray(fp), index=adata.obs_names, columns=fp.names)
fate.to_csv("fate_probabilities.csv")
print(fate.groupby(adata.obs[CLUSTER_KEY], observed=True).mean().round(2))

drivers = g.compute_lineage_drivers(cluster_key=CLUSTER_KEY)
drivers.to_csv("lineage_drivers.csv")
g.plot_fate_probabilities(same_plot=False)
adata.write_h5ad("trajectory_result.h5ad", compression="gzip")
```

Terminal states (`adata.obs["term_states_fwd"]`) should be clusters the user
recognises as end points. If `predict_terminal_states` misses a known end
state, change `N_STATES` or set the states by name from `g.macrostates`.

### Step 6: Map Pseudotime and Fates on the Tissue

On spatial data, check whether the inferred ordering is spatially organised
(e.g. crypt-to-villus, cortical depth). Moran's I near 0 means the ordering is
not reflected in space.

```python
import matplotlib.pyplot as plt
from sklearn.neighbors import kneighbors_graph

W = kneighbors_graph(adata.obsm["spatial"], n_neighbors=6, include_self=False)

def morans_i(v):
    z = np.asarray(v, float) - np.mean(v)
    return len(z) / W.sum() * (z @ (W @ z)) / (z @ z)

tracks = {"dpt_pseudotime": adata.obs["dpt_pseudotime"].to_numpy()}
if "fate" in globals():
    tracks.update({f"fate_{c}": fate[c].to_numpy() for c in fate.columns})
for name, v in tracks.items():
    adata.obs[name] = v
    ok = np.isfinite(v)
    print(f"{name}: Moran's I = {morans_i(np.where(ok, v, np.nanmean(v[ok]))):.2f}")

axes = sc.pl.embedding(adata, basis="spatial", color=list(tracks), cmap="viridis", size=1.5, show=False)
for ax in np.atleast_1d(axes):
    ax.invert_yaxis()                             # pixel y grows downwards; drop for micron coordinates
plt.savefig("trajectory_spatial.png", dpi=150, bbox_inches="tight")

if "velocity" in adata.layers:                    # velocity arrows projected onto tissue coordinates
    adata.obsm["X_spatial"] = adata.obsm["spatial"]
    scv.pl.velocity_embedding_stream(adata, basis="spatial", color=CLUSTER_KEY, show=False,
                                     save="velocity_stream_spatial.png")
```

A velocity stream on tissue coordinates shows transcriptional direction drawn
in space; it is not physical cell migration.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `ROOT_GROUP` | from the user | Start of pseudotime; flips the whole ordering if wrong |
| `n_neighbors` (Step 2) | 30 | Graph used by PAGA, DPT, moments and CellRank |
| `min_shared_counts` | 20 | Gene filter on spliced + unspliced counts |
| `MODE` | `"stochastic"` | `"dynamical"` fits per-gene kinetics, adds latent time, ~10x slower |
| Kernel weights | 0.8 velocity / 0.2 connectivity | More connectivity = smoother, less directional |
| `N_STATES` | 8 | Macrostates searched for terminal states |
| PAGA `threshold` | 0.05 | Edges below this connectivity are hidden in the plot |

## Common Recipes

### Recipe: Genes Changing Along Pseudotime

Rank genes by Spearman correlation with pseudotime and plot the top ones in
pseudotime order:

```python
from scipy.stats import spearmanr

pt = adata.obs["dpt_pseudotime"].to_numpy()
ok = np.isfinite(pt)
genes = adata.var_names[adata.var["highly_variable"]] if "highly_variable" in adata.var else adata.var_names
X = adata[ok, genes].X
X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
rho = pd.Series(spearmanr(pt[ok], X, axis=0)[0][0, 1:], index=genes).dropna()
trend = pd.concat([rho.nlargest(15), rho.nsmallest(15)])
trend.to_csv("pseudotime_genes.csv")
print(trend.round(2))

order = np.argsort(pt[ok])
sc.pl.heatmap(adata[ok][order], var_names=list(trend.index), groupby=CLUSTER_KEY,
              standard_scale="var", show=False, save="_pseudotime_genes.png")
```

### Recipe: Trajectory Within One Spatial Domain

A global graph can connect cells from unrelated regions. Restrict to one
domain (from `spatial-domain-detection`) and recompute:

```python
DOMAIN_KEY, DOMAIN = "spagcn_refined", "3"
sub = adata[adata.obs[DOMAIN_KEY].astype(str) == DOMAIN].copy()
sc.pp.neighbors(sub, n_pcs=30, n_neighbors=15, random_state=0)
sc.tl.diffmap(sub)
in_root = (sub.obs[CLUSTER_KEY] == ROOT_GROUP).to_numpy()
assert in_root.any(), "root cluster absent from this domain"
sub.uns["iroot"] = int(np.flatnonzero(in_root)[np.argmax(sub.obsm["X_diffmap"][in_root, 1])])
sc.tl.dpt(sub)
print(sub.obs.groupby(CLUSTER_KEY, observed=True)["dpt_pseudotime"].median().sort_values())
```

Check the sign of diffusion component 1 as in Step 3 if the order looks
reversed.

### Recipe: Does Pseudotime Follow Distance from a Landmark?

For tissues with a spatial axis (crypt base, vessel, tumour edge), correlate
pseudotime with each cell's distance to the nearest landmark cell:

```python
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

LANDMARK = adata.obs[CLUSTER_KEY] == ROOT_GROUP          # or a domain / cell type marking the landmark
dist = cKDTree(adata.obsm["spatial"][LANDMARK.to_numpy()]).query(adata.obsm["spatial"])[0]
adata.obs["dist_to_landmark"] = dist
ok = np.isfinite(adata.obs["dpt_pseudotime"])
r, p = spearmanr(dist[ok], adata.obs.loc[ok, "dpt_pseudotime"])
print(f"pseudotime vs distance to landmark: Spearman r = {r:.2f} (p = {p:.1e})")
```

With thousands of cells p is always tiny; judge by r and by the map.

## Expected Outputs

- `paga_adjacency.csv` - cluster-to-cluster PAGA connectivity
- `fate_probabilities.csv` - per-cell probability of reaching each terminal state
- `lineage_drivers.csv` - genes correlated with each fate
- `trajectory_result.h5ad` - pseudotime, velocity layers, `term_states_fwd`, `lineages_fwd`
- `figures/` - PAGA graph, pseudotime UMAP, velocity streams
- `trajectory_spatial.png` - pseudotime and fate maps on the tissue
- `pseudotime_genes.csv` - genes most correlated with pseudotime (recipe)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `KeyError: 'spliced'` | No velocity layers | Run velocyto / STARsolo Velocyto on the BAM, or use Steps 3 and 5 with the pseudotime kernel |
| Arrows point from mature to progenitor cells | Steady-state violated, few unspliced reads, or batch effect | Try `MODE="dynamical"`, check `velocity_confidence`, analyse batches separately |
| `dpt_pseudotime` is `inf` for some cells | Disconnected graph components | Subset to the connected lineage or raise `n_neighbors` |
| `predict_terminal_states` returns none or too many | Stability threshold vs `N_STATES` | Change `N_STATES` or call `g.set_terminal_states(states=[...])` |
| Velocity on Xenium / MERFISH data | Probes do not separate spliced and unspliced RNA | Not possible; use PAGA/DPT |
| Stream plot on `spatial` fails | scVelo looks up `obsm["X_spatial"]` | Copy `obsm["spatial"]` to `obsm["X_spatial"]` (Step 6 does) |

## Related Skills

- `scanpy-scrna-seq` - preprocessing and a short PAGA recipe for dissociated scRNA-seq
- `spatial-domain-detection` - restrict trajectories to one tissue domain
- `spatial-transcriptomics-cell-type-annotation` - cluster labels used as `CLUSTER_KEY`
- `scvi-tools-single-cell` - batch-corrected latent space to build the neighbour graph on

## References

- Wolf et al. (2019) PAGA, Genome Biology: https://doi.org/10.1186/s13059-019-1663-x
- Haghverdi et al. (2016) Diffusion pseudotime, Nature Methods: https://doi.org/10.1038/nmeth.3971
- Bergen et al. (2020) scVelo, Nature Biotechnology: https://doi.org/10.1038/s41587-020-0591-3
- Weiler et al. (2024) CellRank 2, Nature Methods: https://doi.org/10.1038/s41592-024-02303-9
- scVelo documentation: https://scvelo.readthedocs.io/en/stable/
- CellRank documentation: https://cellrank.readthedocs.io/en/latest/
