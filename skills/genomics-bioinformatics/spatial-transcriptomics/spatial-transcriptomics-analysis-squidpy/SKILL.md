---
name: "spatial-transcriptomics-analysis-squidpy"
description: "Squidpy spatial statistics on annotated spatial transcriptomics: build the spatial graph (Visium grid, kNN, radius, Delaunay), neighbourhood enrichment z-scores, distance-resolved co-occurrence, interaction matrix and centrality scores, Ripley's L/F/G point patterns, spatially variable genes by Moran's I / Geary's C, and permutation ligand-receptor tests (ligrec, OmniPath). Works on Visium spots and single-cell-resolution data (Xenium, MERFISH, CosMx, Slide-seq). Needs cluster or cell type labels for all but the spatially variable gene step. For an end-to-end ligand-receptor workflow use spatial-transcriptomics-cell-cell-communication."
license: "CC-BY-4.0"
---

# Squidpy Spatial Analysis

## Overview

Graph and point-pattern statistics that describe how cell types (or spot
clusters) are arranged in tissue and which genes follow a spatial pattern.
Each Core API module answers one question and exports a CSV:

| Question | Module |
|---|---|
| Which cell types sit next to each other more than chance? | 2 Neighbourhood enrichment |
| At what distance do two types co-occur? | 3 Co-occurrence |
| How many contacts between types; which types are central? | 4 Interaction matrix + centrality |
| Is a type clustered, random or dispersed? | 5 Ripley's statistics |
| Which genes are spatially patterned? | 6 Spatial autocorrelation |
| Which LR pairs are specific to a cluster pair? | 7 Ligand-receptor test |

## When to Use

- Testing which cell types are neighbours more or less often than chance
- Measuring the distance range over which two cell types stay together
- Deciding whether a cell type is clustered, random or evenly dispersed in tissue
- Finding spatially variable genes by Moran's I or Geary's C
- Running a quick permutation ligand-receptor test between labels
- Use `spatial-transcriptomics-cell-cell-communication` instead for a multi-method LIANA ligand-receptor ranking with a spatial adjacency filter
- For tissue regions without labels, use `spatial-domain-detection` first; for cell labels use `spatial-transcriptomics-cell-type-annotation`

## Prerequisites

- **Input**: AnnData with `obsm["spatial"]` and log-normalised `X`
- **Labels**: a categorical column in `obs` (cell types for single-cell data; spot
  clusters or domains for Visium - spots are mixtures, so read results as
  region-level)
- **Network**: Module 7 downloads OmniPath interactions
- **Versions**: squidpy >= 1.6. `sq.gr.spatial_neighbors` is deprecated from 1.7 in favour
  of `spatial_neighbors_knn/_radius/_delaunay/_grid`; it still works through 1.8

```bash
# Install only what `import` reports missing. `--pypi` keeps the env's scanpy/numba
# stack; a conda add can swap it and bare pip can shadow it.
pixi add --pypi squidpy omnipath scanpy
pixi add --pypi liana        # only for the local-LR-list recipe
```

## Quick Start

```python
import scanpy as sc
import squidpy as sq

adata = sc.read_h5ad("celltype_annotated.h5ad")
adata.obs["cell_type"] = adata.obs["cell_type"].astype("category")
sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=10)     # Visium: coord_type="grid", n_rings=1
sq.gr.nhood_enrichment(adata, cluster_key="cell_type", n_perms=1000, seed=0)
sq.pl.nhood_enrichment(adata, cluster_key="cell_type", save="nhood_quick.png")
```

## Core API

### Module 1: Build the Spatial Graph

All graph-based modules (2, 4, 6) read `obsp["spatial_connectivities"]`.

```python
import numpy as np
import pandas as pd
import scanpy as sc
import squidpy as sq
import matplotlib.pyplot as plt

adata = sc.read_h5ad("celltype_annotated.h5ad")
CLUSTER_KEY = "cell_type"
adata.obs[CLUSTER_KEY] = adata.obs[CLUSTER_KEY].astype("category")
cats = adata.obs[CLUSTER_KEY].cat.categories

PLATFORM = "single_cell"      # "visium" for Visium spots
if PLATFORM == "visium":
    sq.gr.spatial_neighbors(adata, coord_type="grid", n_neighs=6, n_rings=1)   # hexagonal ring
else:
    sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=10)
    # alternatives: delaunay=True (natural neighbours) or radius=30 (same units as coordinates)

deg = np.asarray(adata.obsp["spatial_connectivities"].sum(1)).ravel()
print(f"{adata.n_obs} nodes, median degree {np.median(deg):.0f}, isolated {(deg == 0).sum()}")
```

### Module 2: Neighbourhood Enrichment

Permutation test of how often two labels are neighbours versus shuffled labels:

```python
sq.gr.nhood_enrichment(adata, cluster_key=CLUSTER_KEY, n_perms=1000, seed=0)
z = pd.DataFrame(adata.uns[f"{CLUSTER_KEY}_nhood_enrichment"]["zscore"], index=cats, columns=cats)
z.to_csv("nhood_enrichment_z.csv")
sq.pl.nhood_enrichment(adata, cluster_key=CLUSTER_KEY, method="average", figsize=(8, 8),
                       save="nhood_enrichment.png")

pairs = z.where(np.triu(np.ones(z.shape, bool), k=1)).stack().sort_values()
print("most co-located:\n", pairs.tail(8).round(1))
print("most avoiding:\n", pairs.head(8).round(1))
```

z > 2: neighbours more often than chance; z < -2: avoid each other. The
diagonal measures self-clustering.

### Module 3: Co-occurrence Across Distances

Ratio of P(type B | within distance d of type A) to P(type B). Memory grows
with cell count squared, so subsample large data:

```python
MAX_CELLS = 20000
sub = adata if adata.n_obs <= MAX_CELLS else sc.pp.subsample(adata, n_obs=MAX_CELLS, random_state=0, copy=True)
occ, interval = sq.gr.co_occurrence(sub, cluster_key=CLUSTER_KEY, interval=50, copy=True)
# occ: n_clusters x n_clusters x n_distances; distance bins = interval[1:]
dist = interval[1:] if len(interval) == occ.shape[2] + 1 else interval
sub_cats = sub.obs[CLUSTER_KEY].cat.categories
rows = [(a, b, d, occ[i, j, k]) for i, a in enumerate(sub_cats) for j, b in enumerate(sub_cats)
        for k, d in enumerate(dist)]
co = pd.DataFrame(rows, columns=["anchor", "other", "distance", "ratio"])
co.to_csv("co_occurrence.csv", index=False)

ANCHOR = sub_cats[0]           # set to the cell type of interest
sq.pl.co_occurrence(sub, cluster_key=CLUSTER_KEY, clusters=[ANCHOR], figsize=(8, 4),
                    save="co_occurrence.png")
```

Ratio > 1 at short distance = attraction; the distance where it returns to 1
is the spatial range of the association. Older squidpy versions also take
`n_splits` to reduce memory.

### Module 4: Interaction Matrix and Centrality

```python
im = sq.gr.interaction_matrix(adata, cluster_key=CLUSTER_KEY, normalized=True, copy=True)
im = pd.DataFrame(im, index=cats, columns=cats)          # row-normalised share of each type's edges
im.to_csv("interaction_matrix.csv")
sq.pl.interaction_matrix(adata, cluster_key=CLUSTER_KEY, save="interaction_matrix.png")  # recomputes uns if needed

cent = sq.gr.centrality_scores(adata, cluster_key=CLUSTER_KEY, copy=True)
cent.to_csv("centrality_scores.csv")
print(cent.sort_values("closeness_centrality", ascending=False).round(3))
```

The interaction matrix counts raw contacts (dominated by abundant types);
use Module 2 for enrichment over chance. Centrality: `degree_centrality` = share
of graph connections, `closeness_centrality` = how central a type is in the
tissue graph, `average_clustering` = how tightly its cells group.

### Module 5: Ripley's Statistics

```python
MODE = "L"                     # "L" clustering scale, "G" nearest-neighbour, "F" empty space
rip = sq.gr.ripley(adata, cluster_key=CLUSTER_KEY, mode=MODE, n_simulations=100, seed=0, copy=True)
stat = rip[f"{MODE}_stat"]     # columns: bins, <cluster_key>, stats
stat.to_csv(f"ripley_{MODE}.csv", index=False)
fig, ax = plt.subplots(figsize=(8, 5))
for ct, d in stat.groupby(CLUSTER_KEY, observed=True):
    ax.plot(d["bins"], d["stats"], label=ct)
band = rip["sims_stat"].groupby("bins")["stats"]      # columns: bins, simulations, stats
lo, hi = band.min(), band.max()
ax.fill_between(lo.index, lo, hi, color="grey", alpha=0.3, label="random (simulated)")
ax.set_xlabel("distance"); ax.set_ylabel(f"Ripley's {MODE}"); ax.legend(fontsize=7)
plt.tight_layout(); plt.savefig(f"ripley_{MODE}.png", dpi=150); plt.close()
```

For L, a curve above the simulated band = clustered at that distance, below =
dispersed (regular). `rip["pvalues"]` (cluster x bin) tests each curve
against the simulations.

### Module 6: Spatially Variable Genes

```python
GENES = None                   # None -> highly variable genes; or a list of genes
if GENES is None:
    if "highly_variable" not in adata.var:
        sc.pp.highly_variable_genes(adata, n_top_genes=min(2000, adata.n_vars))
    GENES = adata.var_names[adata.var["highly_variable"]].tolist()

sq.gr.spatial_autocorr(adata, mode="moran", genes=GENES, n_perms=100, n_jobs=4, seed=0)
moran = adata.uns["moranI"].sort_values("I", ascending=False)
moran.to_csv("moran_i.csv")
sig = moran[moran["pval_norm_fdr_bh"] < 0.05]
print(f"{len(sig)} of {len(moran)} genes spatially autocorrelated (FDR < 0.05)")
print(sig.head(15)[["I", "pval_norm_fdr_bh"]])
sq.pl.spatial_scatter(adata, color=sig.index[:4].tolist(), shape=None, size=2, save="top_svg.png")
```

Moran's I near 1 = smooth spatial pattern, near 0 = random. For a targeted
panel (< ~1,000 genes) test all genes with `GENES = adata.var_names.tolist()`.
`mode="geary"` writes `uns["gearyC"]` (C near 0 = clustered, 1 = random).
On Visium use `sq.pl.spatial_scatter` with the default `shape` to draw spots
over the image.

### Module 7: Ligand-Receptor Permutation Test

CellPhoneDB-style test with OmniPath LR pairs, between labels:

```python
res = sq.gr.ligrec(adata, cluster_key=CLUSTER_KEY, n_perms=1000, threshold=0.1, use_raw=False,
                   corr_method="fdr_bh", seed=0, copy=True,
                   transmitter_params={"categories": "ligand"}, receiver_params={"categories": "receptor"})

def to_long(df, name):
    d = df.copy()
    d.columns = [f"{a}|{b}" for a, b in d.columns]
    d.index = [f"{a}|{b}" for a, b in d.index]
    return d.stack().rename(name).rename_axis(["lr", "pair"]).reset_index()

lr = to_long(res["means"], "mean").merge(to_long(res["pvalues"], "pval"), on=["lr", "pair"])
lr[["ligand", "receptor"]] = lr["lr"].str.split("|", n=1, expand=True)
lr[["sender", "receiver"]] = lr["pair"].str.split("|", n=1, expand=True)
hits = lr[(lr["pval"] < 0.05) & (lr["mean"] > 0)].sort_values("mean", ascending=False)
hits.to_csv("ligrec_significant.csv", index=False)
print(f"{len(hits)} significant LR x cluster pair combinations")
print(hits.head(15)[["sender", "receiver", "ligand", "receptor", "mean", "pval"]])
```

Means index = (ligand, receptor), columns = (sender, receiver). For a
consensus across several LR methods and spatial filtering use
`spatial-transcriptomics-cell-cell-communication`.

## Common Workflows

### Workflow: Cell Type Arrangement Report

Graph, enrichment, contact counts and the distance range of the strongest
pair, in one pass:

```python
sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=10)
sq.gr.nhood_enrichment(adata, cluster_key=CLUSTER_KEY, n_perms=1000, seed=0)
z = pd.DataFrame(adata.uns[f"{CLUSTER_KEY}_nhood_enrichment"]["zscore"], index=cats, columns=cats)
im = pd.DataFrame(sq.gr.interaction_matrix(adata, cluster_key=CLUSTER_KEY, normalized=True, copy=True),
                  index=cats, columns=cats)
pairs = z.where(np.triu(np.ones(z.shape, bool), k=1)).stack()
a, b = pairs.idxmax()
report = pd.DataFrame({"z": pairs, "contact_share": [im.loc[x, y] for x, y in pairs.index]})
report.sort_values("z", ascending=False).to_csv("arrangement_report.csv")

sub = adata if adata.n_obs <= 20000 else sc.pp.subsample(adata, n_obs=20000, random_state=0, copy=True)
occ, interval = sq.gr.co_occurrence(sub, cluster_key=CLUSTER_KEY, interval=50, copy=True)
sc_ = list(sub.obs[CLUSTER_KEY].cat.categories)
dist = interval[1:] if len(interval) == occ.shape[2] + 1 else interval
print(f"strongest pair: {a} - {b} (z = {pairs.max():.1f})")
print(pd.Series(occ[sc_.index(a), sc_.index(b)], index=np.round(dist, 1)).head(10).round(2))
```

### Workflow: Compare Arrangement Between Samples

Neighbourhood z-scores are computed per sample (graphs must not connect
cells across sections), then compared:

```python
SAMPLE_KEY = "sample"
zs = {}
for s in adata.obs[SAMPLE_KEY].unique():
    a_s = adata[adata.obs[SAMPLE_KEY] == s].copy()
    a_s.obs[CLUSTER_KEY] = a_s.obs[CLUSTER_KEY].cat.remove_unused_categories()
    sq.gr.spatial_neighbors(a_s, coord_type="generic", n_neighs=10)
    sq.gr.nhood_enrichment(a_s, cluster_key=CLUSTER_KEY, n_perms=1000, seed=0)
    c = a_s.obs[CLUSTER_KEY].cat.categories
    zs[s] = pd.DataFrame(a_s.uns[f"{CLUSTER_KEY}_nhood_enrichment"]["zscore"], index=c, columns=c).stack()
zdf = pd.DataFrame(zs)
zdf.to_csv("nhood_z_by_sample.csv")
print(zdf.assign(spread=zdf.max(axis=1) - zdf.min(axis=1)).sort_values("spread", ascending=False).head(15).round(1))
```

With one section per condition the difference is descriptive; replicate
sections are needed to call a change.

## Key Parameters

| Parameter | Module | Default | Effect |
|---|---|---|---|
| `n_neighs` / `radius` / `delaunay` | 1 | 10 / - / False | Defines "neighbour"; drives Steps 2, 4, 6 |
| `n_rings` | 1 | 1 | Visium hex rings (1 = 6 neighbours) |
| `n_perms` | 2, 6, 7 | 1000 / 100 / 1000 | Permutation precision |
| `interval` | 3 | 50 | Number of distance bins |
| `MODE` | 5 | "L" | Ripley's function |
| `threshold` | 7 | 0.1 | Min fraction of a cluster expressing each gene |

## Common Recipes

### Recipe: Visium - Use Expression Clusters as Labels

Spots have no cell type; cluster them on expression (or use domains from
`spatial-domain-detection`) and run the modules on those labels:

```python
sc.pp.pca(adata, n_comps=30)
sc.pp.neighbors(adata)
sc.tl.leiden(adata, resolution=0.5, key_added="spot_cluster", flavor="igraph", n_iterations=2)
sq.gr.spatial_neighbors(adata, coord_type="grid", n_rings=1)
sq.gr.nhood_enrichment(adata, cluster_key="spot_cluster", n_perms=1000, seed=0)
sq.pl.spatial_scatter(adata, color="spot_cluster", save="spot_clusters.png")   # spots over the H&E image
```

### Recipe: Ligrec with a Local LR List (no OmniPath download)

Pass interactions as a DataFrame with `source` (ligand) and `target`
(receptor) columns, for example from LIANA's consensus resource:

```python
import liana as li

pairs_df = li.rs.select_resource("consensus").rename(columns={"ligand": "source", "receptor": "target"})
pairs_df = pairs_df[~pairs_df["source"].str.contains("_") & ~pairs_df["target"].str.contains("_")]   # simple genes only
res = sq.gr.ligrec(adata, cluster_key=CLUSTER_KEY, interactions=pairs_df[["source", "target"]],
                   n_perms=1000, threshold=0.1, use_raw=False, corr_method="fdr_bh", seed=0, copy=True)
print(res["pvalues"].shape)
```

Complex (multi-subunit) pairs are dropped here; Module 7 with OmniPath or the
CellPhoneDB route of `spatial-transcriptomics-cell-cell-communication` handles complexes.

## Expected Outputs

- `nhood_enrichment_z.csv`, `figures/nhood_enrichment.png`
- `co_occurrence.csv`, `figures/co_occurrence.png`
- `interaction_matrix.csv`, `centrality_scores.csv`
- `ripley_L.csv`, `ripley_L.png`
- `moran_i.csv`, `figures/top_svg.png`
- `ligrec_significant.csv`

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `KeyError: spatial_connectivities` | Module 1 not run on this object | Run `sq.gr.spatial_neighbors` first |
| `ValueError` on `coord_type="visium"` | Not a valid value | Use `coord_type="grid"` for Visium |
| Co-occurrence out of memory | Too many cells | Lower `MAX_CELLS` |
| Many isolated nodes | `radius` too small for the coordinate units | Check units (pixels vs microns); use kNN |
| Ligrec fails to download | No internet / omnipath missing | `pixi add --pypi omnipath`; or pass `interactions=` a DataFrame with `source`/`target` columns |
| Neighbourhood z-scores extreme for rare types | Few cells | Merge rare types or interpret with counts |
| Deprecation warning for `spatial_neighbors` | squidpy >= 1.7 | Switch to `sq.gr.spatial_neighbors_knn` etc. |

## Related Skills

- `spatial-transcriptomics-cell-cell-communication` - LIANA/CellPhoneDB ranking filtered by neighbourhood enrichment, local LR scores, MISTy
- `spatial-transcriptomics-cell-type-annotation` - labels and niches for single-cell data
- `spatial-domain-detection` - spatial domains to use as `CLUSTER_KEY`

## References

- Palla et al. (2022) Squidpy, Nature Methods: https://doi.org/10.1038/s41592-021-01358-2
- squidpy documentation: https://squidpy.readthedocs.io/en/stable/
- squidpy ligand-receptor test: https://squidpy.readthedocs.io/en/stable/api/squidpy.gr.ligrec.html
- squidpy Ripley's statistics: https://squidpy.readthedocs.io/en/stable/api/squidpy.gr.ripley.html
- OmniPath: https://omnipathdb.org/
