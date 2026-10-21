---
name: "spatial-mapping-validation"
description: "Tangram mapping quality control for scRNA-seq-to-spatial mappings: training-gene cosine scores vs sparsity, held-out (test) gene scores with tg.compare_spatial_geneexp, AUC of score vs spatial sparsity (tg.eval_metric), k-fold gene cross-validation, cells vs clusters mode comparison, and a marker-based biological check of projected cell types. Validation skill of the Tangram set: the mapping itself -> spatial-mapping-tangram; projecting/imputing genes -> scrna-spatial-gene-imputation; constrained mode with histology segmentation -> spatial-transcriptomics-deconvolution-tangram."
license: "CC-BY-4.0"
---

# Tangram Mapping Validation

## Overview

A Tangram mapping always converges to something. Training-gene scores show
how well it fits; only genes held out of training show whether it
generalises. Run these checks before reporting cell type maps or projected
genes. Output: per-gene training and held-out scores, an AUC that accounts
for spatial dropout, optional cross-validation and mode comparison, and a
marker check of each projected cell type.

## When to Use

- Deciding whether a Tangram mapping is good enough to report
- Explaining low scores: spatial dropout vs a mismatched reference
- Choosing between `cells` and `clusters` mode on held-out genes
- Checking that projected cell type maps follow markers the mapping did not train on
- Reporting mapping quality numbers alongside cell type maps or imputed genes
- Use `spatial-mapping-tangram` instead when the mapping itself has not been run yet
- For cell2location results, use its own marker check in `spatial-transcriptomics-deconvolution-cell2location` instead

## Prerequisites

- **Inputs**: outputs of `spatial-mapping-tangram`: `tangram_mapping.h5ad`,
  `tangram_sc_prep.h5ad`, `tangram_spatial.h5ad` (same objects that went
  through `tg.pp_adatas`)
- **Held-out genes**: `pp_adatas` must have been run with a marker subset
  (`genes=markers`). With `genes=None` every shared gene is a training gene
  and Steps 2-3 have nothing to test.
- **Python packages**: `tangram-sc` (pulls PyTorch; CPU works), `scanpy`

```bash
pip install tangram-sc scanpy
```

## Workflow

1. Training-gene scores and sparsity diagnostics
2. Held-out gene scores
3. AUC of score vs spatial sparsity
4. (Optional) k-fold gene cross-validation
5. (Optional) cells vs clusters mode comparison
6. Biological check of projected cell types

### Step 1: Training-Gene Scores

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import tangram as tg
import torch

ad_map = sc.read_h5ad("tangram_mapping.h5ad")
adata_sc = sc.read_h5ad("tangram_sc_prep.h5ad")
adata_sp = sc.read_h5ad("tangram_spatial.h5ad")
CELL_TYPE_KEY = "cell_subclass"        # same column used for mapping
MODE_CLUSTER_LABEL = None              # set to CELL_TYPE_KEY if mapped with mode="clusters"
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
PRIOR = adata_sp.obs["density_prior"].to_numpy()   # raw-count prior saved by spatial-mapping-tangram

train_df = ad_map.uns["train_genes_df"]          # sorted by train_score
print(train_df["train_score"].describe())
print("lowest-scoring training genes:\n", train_df.tail(10))

tg.plot_training_scores(ad_map, bins=20, alpha=0.5)   # 4 panels: score, vs sc/sp sparsity, vs difference
plt.savefig("tangram_training_scores.png", dpi=150, bbox_inches="tight")
```

Reading the panels: low scores concentrated on genes that are sparse in the
spatial data (high `sparsity_sp`, large `sparsity_diff`) are dropout, not a
bad mapping. Low scores on well-detected genes point to a reference mismatch.
As a rough guide, mean training score > 0.7 is good, 0.5-0.7 usable with
care, < 0.5 poor.

### Step 2: Held-out Gene Scores

`tg.project_genes` predicts every reference gene in each spot;
`tg.compare_spatial_geneexp` scores the overlap genes (cosine similarity
across spots) and flags which were used for training.

```python
ad_ge = tg.project_genes(ad_map, adata_sc, cluster_label=MODE_CLUSTER_LABEL)
df_all = tg.compare_spatial_geneexp(ad_ge, adata_sp, adata_sc)
df_all.to_csv("tangram_gene_scores.csv")

train = df_all[df_all["is_training"]]
test = df_all[~df_all["is_training"]]
print(f"training genes: {len(train)}, mean score {train['score'].mean():.3f}")
print(f"held-out genes: {len(test)}, mean score {test['score'].mean():.3f}")
print("best held-out genes:\n", test.head(10)[["score", "sparsity_sp", "sparsity_sc"]])
```

A large train-test gap means the mapping memorised the training genes; use a
broader marker set, `mode="clusters"`, or more `lambda_r` regularisation.

### Step 3: AUC of Score vs Spatial Sparsity

`tg.eval_metric` fits score against spatial sparsity for held-out genes; the
area under that curve summarises prediction quality while accounting for
dropout. Plot from its coordinates (`tg.plot_auc` calls seaborn with
positional arguments, which recent seaborn rejects).

```python
metrics, ((pol_xs, pol_ys), (xs, ys)) = tg.eval_metric(df_all)
print({k: round(float(v), 3) for k, v in metrics.items()})

fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(xs, ys, s=8, alpha=0.5)
ax.plot(pol_xs, pol_ys, c="r")
ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="score (held-out genes)", ylabel="spatial sparsity",
       title=f"AUC = {metrics['auc_score']:.3f}")
plt.savefig("tangram_auc.png", dpi=150, bbox_inches="tight")
```

AUC > 0.6 is good, 0.4-0.6 moderate, < 0.4 the mapping does not generalise.

### Step 4 (Optional): k-fold Gene Cross-Validation

Re-map with each fold of training genes withheld via `cv_train_genes` and
score the withheld fold. Clusters mode keeps it affordable on CPU.

```python
K, EPOCHS = 5, 300
genes = np.array(adata_sc.uns["training_genes"])
rng = np.random.default_rng(0)
folds = np.array_split(rng.permutation(genes), K)

rows = []
for i, held in enumerate(folds):
    train_genes = [g for g in genes if g not in set(held)]
    m = tg.map_cells_to_space(adata_sc, adata_sp, cv_train_genes=train_genes, mode="clusters",
                              cluster_label=CELL_TYPE_KEY, density_prior=PRIOR,
                              num_epochs=EPOCHS, device=DEVICE, random_state=0, verbose=False)
    ge = tg.project_genes(m, adata_sc, cluster_label=CELL_TYPE_KEY)
    s = tg.compare_spatial_geneexp(ge, adata_sp, genes=list(held))["score"]
    rows.append({"fold": i, "train_score": m.uns["train_genes_df"]["train_score"].mean(),
                 "test_score": s.mean()})
cv = pd.DataFrame(rows)
cv.to_csv("tangram_cv.csv", index=False)
print(cv, f"\nmean test score: {cv['test_score'].mean():.3f}")
```

`tg.cross_val` does the same but calls `np.float`, removed in NumPy >= 1.24;
it also defaults to `device="cuda:0"`.

### Step 5 (Optional): Cells vs Clusters Mode

Compare on held-out genes, not training scores (cells mode always fits the
training genes more tightly).

```python
for mode in ("cells", "clusters"):
    kw = {"cluster_label": CELL_TYPE_KEY} if mode == "clusters" else {}
    m = tg.map_cells_to_space(adata_sc, adata_sp, mode=mode, density_prior=PRIOR, num_epochs=500,
                              device=DEVICE, random_state=0, verbose=False, **kw)
    ge = tg.project_genes(m, adata_sc, cluster_label=kw.get("cluster_label"))
    d = tg.compare_spatial_geneexp(ge, adata_sp)
    print(f"{mode}: train {d[d.is_training]['score'].mean():.3f}, "
          f"held-out {d[~d.is_training]['score'].mean():.3f}, AUC {tg.eval_metric(d)[0]['auc_score']:.3f}")
```

### Step 6: Biological Check

Each projected cell type should co-vary with a marker the reference cannot
have forced: preferably a held-out gene (not in `training_genes`).

```python
ct = adata_sp.obsm["tangram_ct_pred"]
prop = ct.div(ct.sum(axis=1), axis=0)
checks = {"Oligo": "mobp", "Astro": "aqp4"}      # cell type -> lowercase marker; fill for the tissue
training = set(adata_sp.uns["training_genes"])
for t, g in checks.items():
    if t in prop and g in adata_sp.var_names:
        x = adata_sp[:, g].X
        x = np.asarray(x.todense()).ravel() if hasattr(x, "todense") else np.asarray(x).ravel()
        tag = "training" if g in training else "held-out"
        print(f"{t} vs {g} ({tag}): r = {np.corrcoef(prop[t], x)[0, 1]:.2f}")
```

A type whose map ignores its own held-out markers is not supported by the
data; say so rather than reporting the map.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| Training score threshold | ~0.7 good / < 0.5 poor | Fit on training genes |
| AUC threshold | > 0.6 good / < 0.4 poor | Generalisation to held-out genes |
| `K` (CV folds) | 5 | More folds = smaller held-out sets, more runs |
| `EPOCHS` (CV) | 300 | Shorter than the main run to save time; report it |
| Marker for biological check | from the user | Must be a gene not used for training |

## Common Recipes

### Recipe: One-Row Quality Summary for the Report

```python
summary = pd.DataFrame([{
    "mode": "clusters" if MODE_CLUSTER_LABEL else "cells",
    "n_training_genes": int(df_all["is_training"].sum()),
    "n_heldout_genes": int((~df_all["is_training"]).sum()),
    "mean_train_score": round(train["score"].mean(), 3),
    "mean_heldout_score": round(test["score"].mean(), 3),
    "auc_heldout": round(float(metrics["auc_score"]), 3),
    "cv_test_score": round(cv["test_score"].mean(), 3) if "cv" in globals() else None,
}])
summary["verdict"] = np.where(summary["auc_heldout"] > 0.6, "good",
                              np.where(summary["auc_heldout"] >= 0.4, "moderate", "poor"))
summary.to_csv("tangram_validation_summary.csv", index=False)
print(summary.T)
```

### Recipe: Stability Across Random Seeds

A mapping whose cell type maps change with the seed is not a finding. Re-map
with a few seeds and correlate the proportions per type:

```python
runs = {}
for seed in (0, 1, 2):
    kw = {"cluster_label": CELL_TYPE_KEY} if MODE_CLUSTER_LABEL else {}
    m = tg.map_cells_to_space(adata_sc, adata_sp, mode="clusters" if kw else "cells", density_prior=PRIOR,
                              num_epochs=500, device=DEVICE, random_state=seed, verbose=False, **kw)
    sp = adata_sp.copy()
    tg.project_cell_annotations(m, sp, annotation=CELL_TYPE_KEY)
    p = sp.obsm["tangram_ct_pred"]
    runs[seed] = p.div(p.sum(axis=1), axis=0)
stab = pd.DataFrame({t: [runs[0][t].corr(runs[s][t]) for s in (1, 2)] for t in runs[0].columns},
                    index=["seed0_vs_1", "seed0_vs_2"]).T.round(3)
print(stab.sort_values("seed0_vs_1"))      # r < ~0.8 for a type: its map is not stable
```

### Recipe: Find Genes the Reference Explains Badly

Held-out genes that are well detected in space but score low are not dropout;
they point to biology the reference lacks:

```python
bad = test[(test["sparsity_sp"] < 0.5) & (test["score"] < 0.3)].sort_values("score")
bad.to_csv("tangram_poorly_explained_genes.csv")
print(f"{len(bad)} well-detected held-out genes score < 0.3")
print(bad.head(20)[["score", "sparsity_sp", "sparsity_sc"]])
```

Look the genes up: a cluster of tumour, stress or tissue-specific genes
suggests a reference from the wrong state or tissue.

## Expected Outputs

- `tangram_training_scores.png` - 4-panel training diagnostics
- `tangram_gene_scores.csv` - per-gene score, `is_training`, sparsity
- `tangram_auc.png` - held-out score vs sparsity with AUC
- `tangram_cv.csv` - per-fold train/test scores (optional)
- `tangram_validation_summary.csv` - one-row summary with a verdict (recipe)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| No held-out genes / `eval_metric` fails | `pp_adatas(genes=None)` used all genes | Re-run mapping with a marker subset |
| `AssertionError` on `overlap_genes` | Spatial object differs from the one given to `pp_adatas` | Load the saved `tangram_spatial.h5ad`, not the raw file |
| `The two AnnDatas need to have same obs index` | Clusters-mode map projected without `cluster_label` | Set `MODE_CLUSTER_LABEL = CELL_TYPE_KEY` |
| `AttributeError: np.float` in `tg.cross_val` | NumPy >= 1.24 | Use the Step 4 loop |
| `TypeError` in `tg.plot_auc` | seaborn >= 0.12 positional args | Plot from `eval_metric` coordinates (Step 3) |
| Good training, poor held-out scores | Overfitting to markers | Broader markers, `mode="clusters"`, `lambda_r` > 0 |
| One cell type maps everywhere | Missing types in the reference | Check reference composition and state |

## Related Skills

- `spatial-mapping-tangram` - produces the mapping validated here
- `scrna-spatial-gene-imputation` - uses held-out scores to decide which projected genes to trust
- `spatial-transcriptomics-deconvolution-tangram` - constrained-mode mapping; same checks apply
- `spatial-transcriptomics-deconvolution-cell2location` - alternative deconvolution to compare against

## References

- Biancalani et al. (2021) Tangram, Nature Methods: https://doi.org/10.1038/s41592-021-01264-7
- Tangram documentation: https://tangram-sc.readthedocs.io/
- Tangram source (eval_metric, compare_spatial_geneexp): https://github.com/broadinstitute/Tangram
- squidpy + Tangram tutorial: https://squidpy.readthedocs.io/en/stable/notebooks/tutorials/tutorial_tangram.html
