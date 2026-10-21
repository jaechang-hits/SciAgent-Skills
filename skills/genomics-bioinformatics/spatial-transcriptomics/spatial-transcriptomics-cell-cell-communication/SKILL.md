---
name: "spatial-transcriptomics-cell-cell-communication"
description: "Spatial cell-cell communication / interaction analysis: LIANA consensus ligand-receptor ranking between annotated cell types, squidpy neighborhood enrichment to keep only spatially adjacent sender-receiver pairs, and LIANA bivariate local ligand-receptor scores on the tissue. Works on annotated Xenium/MERFISH/CosMx cells and on Visium spots. Needs cell type labels first (spatial-transcriptomics-cell-type-annotation or deconvolution)."
license: "CC-BY-4.0"
---

# Spatial Cell-Cell Communication

## Overview

Expression-based ligand-receptor (LR) inference ranks pairs that *could*
signal; spatial data adds whether sender and receiver actually sit next to
each other. This skill ranks LR pairs between cell types with LIANA's
multi-method consensus, keeps the pairs whose cell types are spatial
neighbours (squidpy), and scores LR co-expression at each location. Output:
ranked and spatially filtered interaction tables, co-location z-scores, and
local LR maps.

## When to Use

- Finding which annotated cell types may signal to each other in a spatial section
- Separating interactions between neighbouring cell types from those between distant ones
- Mapping where on the tissue a ligand and its receptor are co-expressed
- Checking how much of the LR resource a targeted panel measures before interpreting results
- Following cell type annotation or deconvolution with an interaction summary
- Use `cellphonedb-cell-cell-interaction` instead when you need CellPhoneDB's permutation p-values per pair or microenvironment-restricted testing
- For multi-sample tensor decomposition or MISTy models, use `liana-spatial-cell-cell-communication`

## Prerequisites

- **Input**: log-normalised expression in `X` and `obsm["spatial"]`
- **Labels**: single-cell-resolution data needs a cell type column in `obs` (`spatial-transcriptomics-cell-type-annotation`)
- **Visium**: no per-spot labels - Step 4 works without them; Steps 2-3 need deconvolution first (`spatial-transcriptomics-deconvolution-cell2location`)
- **Python packages**: `liana`, `squidpy`, `scanpy`

```bash
pip install liana squidpy scanpy
```

## Workflow

### Step 1: Inputs and Panel Coverage

```python
import liana as li
import numpy as np
import pandas as pd
import scanpy as sc

adata = sc.read_h5ad("celltype_annotated.h5ad")
CELL_TYPE_KEY = "cell_type"
RESOURCE = "consensus"                              # "mouseconsensus" for mouse
adata.obs[CELL_TYPE_KEY] = adata.obs[CELL_TYPE_KEY].astype("category")
print(adata.obs[CELL_TYPE_KEY].value_counts())

resource = li.rs.select_resource(RESOURCE)
genes = set(adata.var_names)
def present(complex_):
    return all(g in genes for g in complex_.split("_"))
covered = resource[resource["ligand"].map(present) & resource["receptor"].map(present)]
print(f"LR pairs measurable: {len(covered)} of {len(resource)}")
```

A targeted panel (Xenium ~400 genes) measures only a small share of the
resource. Report that coverage with the results: absent pairs were not
measured, not ruled out.

### Step 2: Rank LR Pairs Between Cell Types

```python
li.mt.rank_aggregate(adata, groupby=CELL_TYPE_KEY, resource_name=RESOURCE,
                     expr_prop=0.1, use_raw=False, key_added="liana_res", verbose=True)
res = adata.uns["liana_res"]
res.to_csv("liana_results.csv", index=False)
print(res.sort_values("magnitude_rank").head(15)[
    ["source", "target", "ligand_complex", "receptor_complex", "magnitude_rank", "specificity_rank"]])
```

`magnitude_rank` (lower = stronger) and `specificity_rank` aggregate several
methods (CellPhoneDB, CellChat, NATMI, Connectome, ...). Plot the top pairs:

```python
p = li.pl.dotplot(adata=adata, colour="magnitude_rank", size="specificity_rank",
                  inverse_colour=True, inverse_size=True, top_n=20,
                  orderby="magnitude_rank", orderby_ascending=True, figure_size=(10, 8),
                  return_fig=True)          # restrict with source_labels=[...], target_labels=[...]
p.save("liana_dotplot.png", dpi=150)
```

### Step 3: Keep Spatially Adjacent Pairs

```python
import squidpy as sq

sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=15)   # Visium: coord_type="grid", n_rings=1
sq.gr.nhood_enrichment(adata, cluster_key=CELL_TYPE_KEY, n_perms=1000, seed=0)
cats = adata.obs[CELL_TYPE_KEY].cat.categories
z = pd.DataFrame(adata.uns[f"{CELL_TYPE_KEY}_nhood_enrichment"]["zscore"], index=cats, columns=cats)
z.to_csv("nhood_enrichment_z.csv")

top = res[res["magnitude_rank"] < 0.05].copy()
top["neighbour_z"] = [z.loc[s, t] for s, t in zip(top["source"], top["target"])]
adjacent = top[top["neighbour_z"] > 2].sort_values("magnitude_rank")
adjacent.to_csv("liana_adjacent_pairs.csv", index=False)
print(f"{len(adjacent)} of {len(top)} top interactions are between neighbouring cell types")
print(adjacent.head(15)[["source", "target", "ligand_complex", "receptor_complex", "neighbour_z"]])
```

Autocrine pairs (`source == target`) are always adjacent; read them
separately. Show the co-location matrix the filter is based on:

```python
sq.pl.nhood_enrichment(adata, cluster_key=CELL_TYPE_KEY, cmap="coolwarm", vmin=-10, vmax=10,
                       figsize=(7, 6), save="nhood_enrichment.png")
```

### Step 4: Local LR Co-expression on the Tissue

Scores each LR pair at every location, so it also works on Visium spots
without labels:

```python
BANDWIDTH = 100     # coordinate units: ~50-100 um for Xenium; for Visium full-res pixels, ~2-3 spot spacings
spatial_neighbors = li.pp.spatial_neighbors if hasattr(li, "pp") else li.ut.spatial_neighbors  # li.ut in older liana
spatial_neighbors(adata, bandwidth=BANDWIDTH, cutoff=0.1, kernel="gaussian", set_diag=True)
lrdata = li.mt.bivariate(adata, resource_name=RESOURCE, local_name="cosine", global_name="morans",
                         n_perms=100, mask_negatives=False, add_categories=True, nz_prop=0.1,
                         use_raw=False, verbose=True)
summary = lrdata.var.sort_values("morans", ascending=False)
summary.to_csv("liana_bivariate_summary.csv")
print(summary.head(10))
sc.pl.embedding(lrdata, basis="spatial", color=summary.index[:4].tolist(), cmap="coolwarm", save="_lr_local.png")
```

`li.pp.query_bandwidth` helps pick the bandwidth from the coordinate scale
(see `liana-spatial-cell-cell-communication`).

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `expr_prop` | 0.1 | Min fraction of a cell type expressing each gene |
| `magnitude_rank` cutoff | 0.05 | How many pairs count as top interactions |
| neighbour z cutoff | 2 | How strongly two types must co-locate |
| `n_neighs` | 15 | Size of the spatial neighbourhood (cells) |
| `BANDWIDTH` | 100 | Spatial kernel for local scores, in coordinate units |

## Common Recipes

### Recipe: Compare Conditions Across Samples

Rank per sample, then compare the same LR pair between conditions:

```python
SAMPLE_KEY, CONDITION_KEY = "sample", "condition"
li.mt.rank_aggregate.by_sample(adata, groupby=CELL_TYPE_KEY, sample_key=SAMPLE_KEY,
                               resource_name=RESOURCE, expr_prop=0.1, use_raw=False, verbose=True)
res_s = adata.uns["liana_res"]
cond = adata.obs.groupby(SAMPLE_KEY, observed=True)[CONDITION_KEY].first()
res_s[CONDITION_KEY] = res_s[SAMPLE_KEY].map(cond)
res_s["pair"] = (res_s["source"].astype(str) + "->" + res_s["target"].astype(str) + ": "
                 + res_s["ligand_complex"] + "-" + res_s["receptor_complex"])
by_cond = res_s.pivot_table(index="pair", columns=CONDITION_KEY, values="magnitude_rank", aggfunc="median")
by_cond.to_csv("liana_by_condition.csv")
print(by_cond.dropna().assign(diff=lambda d: d.iloc[:, 0] - d.iloc[:, 1]).sort_values("diff").head(15))
```

With few samples per condition this is descriptive; do not attach p-values to it.

### Recipe: Visium - Link Local LR Scores to Deconvolved Cell Types

On spot data, say which cell types a local LR signal sits on by correlating
local scores with cell2location abundances:

```python
abund = pd.read_csv("cell2location_abundance.csv", index_col=0).loc[lrdata.obs_names]
lr_top = summary.index[:20]
local = pd.DataFrame(np.asarray(lrdata[:, lr_top].X.todense()) if hasattr(lrdata.X, "todense")
                     else lrdata[:, lr_top].X, index=lrdata.obs_names, columns=lr_top)
corr = pd.DataFrame({ct: local.corrwith(abund[ct]) for ct in abund.columns}).round(2)
corr.to_csv("lr_local_vs_abundance.csv")
print(corr.apply(lambda r: ", ".join(f"{k} {v}" for k, v in r.nlargest(3).items()), axis=1))
```

### Recipe: Distance Range of One Cell Type Pair

Neighbourhood enrichment is a yes/no at one scale; co-occurrence shows over
which distance two types stay together:

```python
ANCHOR = "Macrophage"                                  # a category of CELL_TYPE_KEY
sub = adata[np.random.default_rng(0).choice(adata.n_obs, min(adata.n_obs, 20000), replace=False)].copy()
occ, interval = sq.gr.co_occurrence(sub, cluster_key=CELL_TYPE_KEY, interval=50, copy=True)
sub_cats = list(sub.obs[CELL_TYPE_KEY].cat.categories)
dist = interval[1:] if len(interval) == occ.shape[2] + 1 else interval
curve = pd.DataFrame(occ[sub_cats.index(ANCHOR)].T, index=np.round(dist, 1), columns=sub_cats)
print(curve.iloc[:10].round(2))          # ratio > 1 at short distance = attraction
```

## Expected Outputs

- `liana_results.csv` - LR ranking per sender-receiver pair
- `liana_dotplot.png` - top pairs
- `nhood_enrichment_z.csv`, `nhood_enrichment.png` - cell type co-location z-scores
- `liana_adjacent_pairs.csv` - top LR pairs whose cell types are neighbours
- `liana_bivariate_summary.csv` - global spatial LR scores (Moran's R)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Very few results | Targeted panel lacks LR genes | Report coverage (Step 1); do not extrapolate |
| `KeyError` on cell type | Column not categorical | `adata.obs[CELL_TYPE_KEY] = adata.obs[CELL_TYPE_KEY].astype("category")` |
| All local scores near 0 | Bandwidth smaller than spot/cell spacing | Increase `BANDWIDTH` |
| Mouse genes not matched | Human resource | `RESOURCE = "mouseconsensus"` |
| Slow permutations | Many cells | Lower `n_perms` for exploration, report it |
| `AttributeError: module 'liana' has no attribute 'pp'` | Older liana | The Step 4 fallback uses `li.ut`; or upgrade liana |

## Related Skills

- `spatial-transcriptomics-cell-type-annotation` - labels for Steps 2-3
- `spatial-transcriptomics-deconvolution-cell2location` - abundances for Visium
- `liana-spatial-cell-cell-communication` - tensor decomposition, MISTy, bandwidth selection
- `cellphonedb-cell-cell-interaction` - CellPhoneDB statistical analysis
- `spatial-transcriptomics-analysis-squidpy` - further spatial statistics

## References

- Dimitrov et al. (2024) LIANA+, Nature Cell Biology: https://doi.org/10.1038/s41556-024-01469-w
- LIANA+ documentation: https://liana.readthedocs.io/
- Palla et al. (2022) Squidpy, Nature Methods: https://doi.org/10.1038/s41592-021-01358-2
- squidpy documentation: https://squidpy.readthedocs.io/en/stable/
