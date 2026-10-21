---
name: "liana-spatial-cell-cell-communication"
description: "LIANA (liana-py) cell-cell communication beyond a single-sample ranking: consensus ligand-receptor ranks with dotplots and sender-receiver count maps, multi-sample comparison with Tensor-cell2cell factors (context, LR, sender, receiver loadings), spatial bivariate local LR scores with bandwidth selection, p-value and category layers, and MISTy multi-view models of what predicts cell type composition from intra, juxta and para views. Works on scRNA-seq, Visium (with cell2location compositions) and single-cell-resolution spatial data. For the standard spatial workflow (LIANA ranking + squidpy adjacency + local scores) use spatial-transcriptomics-cell-cell-communication; for CellPhoneDB statistics use cellphonedb-cell-cell-interaction."
license: "CC-BY-4.0"
---

# LIANA Cell-Cell Communication: Multi-sample, Spatial and MISTy

## Overview

LIANA aggregates several LR methods into consensus ranks and adds
multi-sample and spatial extensions. The base single-sample spatial run
(rank -> keep adjacent pairs -> local scores) is in
`spatial-transcriptomics-cell-cell-communication`; this skill covers the parts
it does not. Output: ranked LR tables and plots, Tensor-cell2cell
communication patterns across samples, local LR maps with p-values and
categories, and MISTy models of what shapes cell type composition.

| Question | Module |
|---|---|
| Which LR pairs between my cell types, plotted | Modules 1-2 |
| How does communication differ across samples / conditions | Module 3 (Tensor-cell2cell) |
| Where on the tissue is an LR pair co-expressed, and how sure | Module 4 (bivariate) |
| Which neighbourhood features explain cell type composition | Module 5 (MISTy) |
| Permutation p-values per pair from one method | `cellphonedb-cell-cell-interaction` |

## When to Use

- Comparing communication programs across many samples or conditions (Tensor-cell2cell)
- Mapping where on the tissue a ligand and receptor are co-expressed, with per-location p-values
- Choosing a spatial kernel bandwidth from the coordinate scale
- Explaining cell type composition from neighbouring compositions or LR activity (MISTy)
- Plotting LIANA consensus results as dotplots and sender-receiver count maps
- Use `spatial-transcriptomics-cell-cell-communication` instead for a single-sample ranking filtered by spatial adjacency
- For CellPhoneDB's own permutation statistics and microenvironments, use `cellphonedb-cell-cell-interaction`

## Prerequisites

- **Input**: log-normalised expression in `X`; cell type labels in `obs` for Modules 1-3;
  `obsm["spatial"]` for Modules 4-5
- **Versions**: functions follow the current `li.pp` / `li.ms` namespaces; older
  releases exposed them as `li.ut` / `li.multi`
- **Python packages**: `liana`; `cell2cell` for Module 3; `squidpy` for the MISTy juxta view

```bash
pip install liana cell2cell squidpy seaborn
```

## Quick Start

```python
import liana as li
import scanpy as sc

adata = sc.read_h5ad("celltype_annotated.h5ad")
li.mt.rank_aggregate(adata, groupby="cell_type", resource_name="consensus", expr_prop=0.1, use_raw=False)
print(adata.uns["liana_res"].sort_values("magnitude_rank").head(10))
```

## Core API

### Module 1: Load Data and Choose the Resource

```python
import liana as li
import numpy as np
import pandas as pd
import scanpy as sc

adata = sc.read_h5ad("celltype_annotated.h5ad")
CELL_TYPE_KEY = "cell_type"
adata.obs[CELL_TYPE_KEY] = adata.obs[CELL_TYPE_KEY].astype("category")

# Mouse symbols look like "Actb", human like "ACTB".
head = adata.var_names[:200]
n_mouse = sum(len(g) > 1 and g[0].isupper() and g[1:].islower() for g in head)
RESOURCE = "mouseconsensus" if n_mouse > len(head) / 2 else "consensus"
print(f"resource: {RESOURCE}; max X = {adata.X.max():.1f} (expect < ~15 for log data)")
```

### Module 2: Consensus Ranking and Plots

```python
SAMPLE_KEY = None          # e.g. "sample" to run per sample (needed for Module 3)
if SAMPLE_KEY:
    li.mt.rank_aggregate.by_sample(adata, groupby=CELL_TYPE_KEY, sample_key=SAMPLE_KEY,
                                   resource_name=RESOURCE, expr_prop=0.1, use_raw=False,
                                   n_perms=None, return_all_lrs=True, verbose=True)
else:
    li.mt.rank_aggregate(adata, groupby=CELL_TYPE_KEY, resource_name=RESOURCE,
                         expr_prop=0.1, use_raw=False, verbose=True)
res = adata.uns["liana_res"]
res.to_csv("liana_results.csv", index=False)

p = li.pl.dotplot(adata=adata, colour="magnitude_rank", size="specificity_rank",
                  inverse_colour=True, inverse_size=True, top_n=20,
                  orderby="magnitude_rank", orderby_ascending=True, figure_size=(10, 8),
                  return_fig=True)          # restrict with source_labels=[...], target_labels=[...]
p.save("liana_dotplot.png", dpi=150)
```

Sender-receiver count map of top interactions:

```python
import matplotlib.pyplot as plt
import seaborn as sns

top = res[(res["magnitude_rank"] <= 0.05) & (res["specificity_rank"] <= 0.05)]
counts = top.groupby(["source", "target"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(9, 8))
sns.heatmap(counts, cmap="YlOrRd", annot=True, fmt="d", ax=ax)
ax.set_xlabel("receiver"); ax.set_ylabel("sender")
plt.tight_layout(); plt.savefig("liana_sender_receiver_counts.png", dpi=150); plt.close()
print(top.sort_values("magnitude_rank").head(15)[
    ["source", "target", "ligand_complex", "receptor_complex", "lr_means", "magnitude_rank", "specificity_rank"]])
```

| Column | Meaning |
|---|---|
| `source` / `target` | Sender (ligand) / receiver (receptor) cell type |
| `ligand_complex` / `receptor_complex` | Genes; complexes joined by `_` |
| `lr_means` | Mean of ligand and receptor expression |
| `magnitude_rank` | Consensus rank of expression strength (lower = stronger) |
| `specificity_rank` | Consensus rank of cell type specificity (lower = more specific) |

### Module 3: Multi-sample - Tensor-cell2cell

Needs Module 2 run with `SAMPLE_KEY` set and several samples per condition.
Factorises a samples x LR x sender x receiver tensor into patterns:

```python
import cell2cell as c2c
from collections import defaultdict

CONDITION_KEY = "condition"
tensor = li.ms.to_tensor_c2c(adata, sample_key=SAMPLE_KEY, score_key="magnitude_rank",
                             how="outer_cells")
ctx = adata.obs[[SAMPLE_KEY, CONDITION_KEY]].drop_duplicates()
context_dict = defaultdict(lambda: "Unknown", zip(ctx[SAMPLE_KEY], ctx[CONDITION_KEY]))
meta = c2c.tensor.generate_tensor_metadata(interaction_tensor=tensor,
                                           metadata_dicts=[context_dict, None, None, None],
                                           fill_with_order_elements=True)
RANK = None   # None = elbow search up to upper_rank (slow); or fix e.g. 6
tensor = c2c.analysis.run_tensor_cell2cell_pipeline(
    tensor, meta, copy_tensor=True, rank=RANK, tf_optimization="regular", random_state=0,
    device="cpu", elbow_metric="error", upper_rank=15, tf_init="random",
    sample_col="Element", group_col="Category", output_fig=False)

for name, df in tensor.factors.items():   # Contexts, Ligand-Receptor Pairs, Sender Cells, Receiver Cells
    df.to_csv(f"tensor_factors_{name.replace(' ', '_').replace('-', '_')}.csv")
contexts = tensor.factors["Contexts"]
print(contexts.groupby(contexts.index.map(context_dict)).mean().round(3))
```

Read a factor as one pattern: its context loadings show which samples (and
conditions) use it, the LR loadings which pairs, and sender/receiver loadings
which cell types. A factor whose context loading differs between conditions is
a condition-specific communication program; test that difference across
samples (e.g. Mann-Whitney on the per-sample loadings) before claiming it.

### Module 4: Spatial Bivariate Scores

Pick the kernel bandwidth from the coordinate scale, then score every LR pair
at every location (no labels needed, so it works on Visium spots):

```python
plot, bw_table = li.pp.query_bandwidth(coordinates=adata.obsm["spatial"], start=0, end=500, interval_n=20)
plot.save("liana_bandwidth.png", dpi=150)
print(bw_table.head(10))      # average neighbours per bandwidth: aim for a few-to-tens of neighbours

BANDWIDTH = 200               # coordinate units (Visium full-res pixels, Xenium microns)
li.pp.spatial_neighbors(adata, bandwidth=BANDWIDTH, cutoff=0.1, kernel="gaussian", set_diag=True)
lrdata = li.mt.bivariate(adata, resource_name=RESOURCE, local_name="cosine", global_name="morans",
                         n_perms=100, mask_negatives=False, add_categories=True, nz_prop=0.2,
                         use_raw=False, verbose=True)
summary = lrdata.var.sort_values("morans", ascending=False)
summary.to_csv("liana_bivariate_summary.csv")
lrdata.write_h5ad("liana_bivariate.h5ad")
print(summary.head(10)[["ligand", "receptor", "morans", "morans_pvals", "mean"]])

top4 = summary.index[:4].tolist()
sc.pl.embedding(lrdata, basis="spatial", color=top4, cmap="magma", save="_lr_local.png")
sc.pl.embedding(lrdata, basis="spatial", color=top4, layer="cats", cmap="coolwarm", save="_lr_cats.png")
```

| Output | Meaning |
|---|---|
| `X` | Local score per location and LR pair (`ligand^receptor`) |
| `layers["pvals"]` | Per-location permutation p-value |
| `layers["cats"]` | 1 = both high, -1 = one high one low, 0 = both low |
| `var["morans"]` | Global spatial co-pattern of ligand and receptor |

Use the `cats` map to separate true co-localisation (1) from regions where
only one partner is present (-1).

### Module 5: MISTy Spatial Relationships

MISTy fits, for each target feature, how well it is predicted by the same
location (intra), direct neighbours (juxta) and the wider area (para). Here the
targets are cell type proportions, e.g. cell2location output on Visium:

```python
from liana.method import genericMistyData
from liana.method.sp import LinearModel, RandomForestModel

prop = pd.read_csv("cell2location_proportions.csv", index_col=0)   # spots x cell types
adata.obsm["compositions"] = prop.loc[adata.obs_names]
comps = li.pp.obsm_to_adata(adata, "compositions")

misty = genericMistyData(intra=comps, cutoff=0.05, bandwidth=BANDWIDTH, n_neighs=6)
# add extra=<AnnData of pathway/TF scores> to predict compositions from other features
misty(model=LinearModel, k_cv=10, seed=1337, bypass_intra=False, verbose=True)   # or RandomForestModel

metrics = misty.uns["target_metrics"]       # target, intra_R2, multi_R2, gain_R2, intra, juxta, para
inter = misty.uns["interactions"]           # target, predictor, view, importances
metrics.to_csv("misty_target_metrics.csv", index=False)
inter.to_csv("misty_interactions.csv", index=False)
print(metrics.sort_values("gain_R2", ascending=False).head(10))
li.pl.misty_target_metrics(misty, stat="gain_R2", return_fig=True).save("misty_gain_r2.png", dpi=150)
li.pl.misty_interactions(misty, view="juxta", return_fig=True).save("misty_juxta.png", dpi=150)
```

`gain_R2` is how much the spatial views add over intra alone; a cell type with
high gain depends on its surroundings. `interactions` with `view == "juxta"`
or `"para"` name which neighbouring types predict it.

## Common Workflows

### Workflow: Visium - Local LR Activity as a MISTy Predictor

Combine Modules 4 and 5: score LR pairs on the spots, then ask whether local
LR activity predicts cell2location compositions beyond the compositions
themselves:

```python
li.pp.spatial_neighbors(adata, bandwidth=BANDWIDTH, cutoff=0.1, kernel="gaussian", set_diag=True)
lrdata = li.mt.bivariate(adata, resource_name=RESOURCE, local_name="cosine", global_name="morans",
                         n_perms=100, mask_negatives=False, add_categories=True, nz_prop=0.2, use_raw=False)
top_lr = lrdata.var.sort_values("morans", ascending=False).index[:30]
extra = lrdata[:, top_lr].copy()

prop = pd.read_csv("cell2location_proportions.csv", index_col=0)
adata.obsm["compositions"] = prop.loc[adata.obs_names]
comps = li.pp.obsm_to_adata(adata, "compositions")
misty = genericMistyData(intra=comps, extra=extra, cutoff=0.05, bandwidth=BANDWIDTH, n_neighs=6)
misty(model=LinearModel, k_cv=10, seed=1337, verbose=True)
inter = misty.uns["interactions"]
print(inter[inter["view"] == "extra"].sort_values("importances", ascending=False).head(15))
```

### Workflow: Condition-Specific Communication Patterns

Modules 2 and 3 end to end, then a per-factor test of context loadings
between two conditions:

```python
from scipy.stats import mannwhitneyu

li.mt.rank_aggregate.by_sample(adata, groupby=CELL_TYPE_KEY, sample_key=SAMPLE_KEY, resource_name=RESOURCE,
                               expr_prop=0.1, use_raw=False, n_perms=None, return_all_lrs=True)
tensor = li.ms.to_tensor_c2c(adata, sample_key=SAMPLE_KEY, score_key="magnitude_rank", how="outer_cells")
meta = c2c.tensor.generate_tensor_metadata(interaction_tensor=tensor, metadata_dicts=[context_dict, None, None, None],
                                           fill_with_order_elements=True)
tensor = c2c.analysis.run_tensor_cell2cell_pipeline(tensor, meta, copy_tensor=True, rank=6, tf_optimization="regular",
                                                    random_state=0, device="cpu", tf_init="random",
                                                    sample_col="Element", group_col="Category", output_fig=False)
ctx = tensor.factors["Contexts"]
cond = ctx.index.map(context_dict)
c1, c2 = sorted(set(cond))[:2]
tests = {f: mannwhitneyu(ctx.loc[cond == c1, f], ctx.loc[cond == c2, f]).pvalue for f in ctx.columns}
print(pd.Series(tests).sort_values().round(4))      # few samples: treat as exploratory
```

## Key Parameters

| Parameter | Module | Default | Effect |
|---|---|---|---|
| `expr_prop` | 2 | 0.1 | Min fraction of a cell type expressing each gene |
| rank cutoffs | 2 | 0.05 | Which pairs count as top interactions |
| `RANK` | 3 | None (elbow) | Number of communication patterns |
| `BANDWIDTH` | 4-5 | 200 | Spatial kernel width, in coordinate units |
| `nz_prop` | 4 | 0.2 | Min fraction of locations expressing each partner |
| `n_perms` | 4 | 100 | Permutations for local p-values |
| `n_neighs` | 5 | 6 | Juxta view neighbours |

## Common Recipes

### Recipe: Focus on Chosen Senders and Receivers

```python
SENDERS, RECEIVERS = ["Macrophage"], ["T cell"]
sub = res[res["source"].isin(SENDERS) & res["target"].isin(RECEIVERS)].sort_values("magnitude_rank")
sub.to_csv("liana_focus.csv", index=False)
p = li.pl.dotplot(adata=adata, colour="magnitude_rank", size="specificity_rank", inverse_colour=True,
                  inverse_size=True, source_labels=SENDERS, target_labels=RECEIVERS, top_n=20,
                  orderby="magnitude_rank", orderby_ascending=True, figure_size=(6, 8), return_fig=True)
p.save("liana_focus_dotplot.png", dpi=150)
```

### Recipe: One Method Instead of the Consensus

Run a single method, e.g. LIANA's CellPhoneDB implementation, to get its
permutation p-values next to the consensus ranks:

```python
li.mt.cellphonedb(adata, groupby=CELL_TYPE_KEY, resource_name=RESOURCE, expr_prop=0.1,
                  use_raw=False, n_perms=1000, seed=0, key_added="cpdb_res")
cpdb = adata.uns["cpdb_res"]
sig = cpdb[cpdb["cellphone_pvals"] < 0.05].sort_values("lr_means", ascending=False)
print(f"{len(sig)} significant rows")
print(sig.head(15)[["source", "target", "ligand_complex", "receptor_complex", "lr_means", "cellphone_pvals"]])
```

## Expected Outputs

- `liana_results.csv`, `liana_dotplot.png`, `liana_sender_receiver_counts.png`
- `tensor_factors_*.csv` - context, LR, sender, receiver loadings
- `liana_bandwidth.png`, `liana_bivariate_summary.csv`, `liana_bivariate.h5ad`, `figures/*_lr_*.png`
- `misty_target_metrics.csv`, `misty_interactions.csv`, `misty_*.png`

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `AttributeError: module 'liana' has no attribute 'pp'` | Old liana | Use `li.ut.*` / `li.multi.*`, or upgrade liana |
| Few or no LR pairs | Targeted panel or wrong resource | Check organism; report panel coverage |
| Tensor factorization fails | Too few samples or cell types missing in many samples | Use `how="outer_cells"`, fix `RANK` low (3-4), add samples |
| Local scores all near 0 | Bandwidth below spot/cell spacing | Re-read `query_bandwidth` table; raise `BANDWIDTH` |
| MISTy juxta view error | squidpy missing | `pip install squidpy` |
| `KeyError` aligning compositions | Spot IDs differ between files | Align on `adata.obs_names` before `obsm` |

## Related Skills

- `spatial-transcriptomics-cell-cell-communication` - standard spatial LR workflow with adjacency filter
- `cellphonedb-cell-cell-interaction` - permutation-based CellPhoneDB analysis
- `spatial-single-cell-ligand-receptor-discovery` - pathway-focused candidate evidence
- `spatial-transcriptomics-deconvolution-cell2location` - compositions used by MISTy
- `spatial-transcriptomics-analysis-squidpy` - spatial graph statistics

## References

- Dimitrov et al. (2024) LIANA+, Nature Cell Biology: https://doi.org/10.1038/s41556-024-01469-w
- Armingol et al. (2022) Tensor-cell2cell, Nature Communications: https://doi.org/10.1038/s41467-022-31369-2
- Tanevski et al. (2022) MISTy, Genome Biology: https://doi.org/10.1186/s13059-022-02663-5
- LIANA+ documentation: https://liana.readthedocs.io/
- LIANA+ source: https://github.com/scverse/liana
- cell2cell source: https://github.com/earmingol/cell2cell
