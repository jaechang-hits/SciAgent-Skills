---
name: "scrna-spatial-gene-imputation"
description: "Spatial gene expression imputation from scRNA-seq: project unmeasured or dropout-affected genes onto spots/cells through a Tangram mapping (tg.project_genes), flag which projected genes to trust from held-out gene scores, plot measured vs predicted maps, and impute with gimVI (scvi-tools) as a count-based alternative for targeted panels (osmFISH, MERFISH, Xenium). Gene projection skill of the Tangram set: the mapping itself -> spatial-mapping-tangram; mapping quality checks -> spatial-mapping-validation; constrained mode with histology segmentation -> spatial-transcriptomics-deconvolution-tangram."
license: "CC-BY-4.0"
---

# Spatial Gene Imputation (Tangram, gimVI)

## Overview

Projects reference expression into space to show genes the spatial panel did
not measure, or measured with heavy dropout. A projected gene is a weighted
mix of reference profiles at each location: it reflects where the mapped
cells sit, not new spatial measurement. Within-cell-type spatial variation
that the mapping did not capture cannot appear. Output: predicted expression
for every reference gene at every spot or cell, a trust table per target
gene, and measured-vs-predicted maps.

## When to Use

- Showing the spatial pattern of a gene that a targeted panel (Xenium, MERFISH, osmFISH) did not include
- Recovering genes with heavy dropout in Visium or Slide-seq
- Scoring gene signatures that need more genes than the panel measured
- Deciding which imputed genes are credible enough to report
- Imputing with a count-based model (gimVI) as a second opinion to Tangram
- Use `spatial-mapping-tangram` instead when the Tangram mapping has not been built yet
- For panels you are still designing, use `spatial-panel-design` instead so key genes are measured, not imputed

## Prerequisites

- **Tangram route**: outputs of `spatial-mapping-tangram` (`tangram_mapping.h5ad`,
  `tangram_sc_prep.h5ad`, `tangram_spatial.h5ad`), mapped with a marker subset
  so that held-out genes exist
- **gimVI route**: raw counts for both datasets; spatial genes must be a subset of
  the reference genes
- **Compute**: both pull PyTorch; CPU works, slower
- **Python packages**: `tangram-sc` and/or `scvi-tools`. gimVI warns that it
  moves to `scviva-tools` and is planned for removal from scvi-tools v1.6; pin
  `scvi-tools<1.6` if the import fails.

```bash
pip install tangram-sc "scvi-tools<1.6" squidpy
```

## Workflow

1. Choose target genes
2. Project genes through the Tangram mapping
3. Decide which projected genes to trust
4. Plot measured vs projected
5. (Alternative) gimVI imputation
6. Save

### Step 1: Choose Target Genes

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import tangram as tg

ad_map = sc.read_h5ad("tangram_mapping.h5ad")
adata_sc = sc.read_h5ad("tangram_sc_prep.h5ad")
adata_sp = sc.read_h5ad("tangram_spatial.h5ad")
CLUSTER_LABEL = None        # the cell type column if the map was made with mode="clusters"

TARGETS = ["foxp3", "cd8a", "gfap", "mbp"]   # lowercase: pp_adatas lowercased var_names
in_sc = [g for g in TARGETS if g in adata_sc.var_names]
print("not in reference (cannot impute):", sorted(set(TARGETS) - set(in_sc)))
print("not in spatial panel (pure imputation):", [g for g in in_sc if g not in adata_sp.var_names])

def zero_frac(ad, g):
    x = ad[:, g].X
    x = x.toarray() if hasattr(x, "toarray") else np.asarray(x)
    return float((x == 0).mean())

for g in in_sc:
    if g in adata_sp.var_names:
        print(f"{g}: zero in {zero_frac(adata_sp, g):.0%} of spots, {zero_frac(adata_sc, g):.0%} of cells")
```

Genes dense in the reference but sparse in space (dropout) gain the most.
Genes absent or near-zero in the reference cannot be imputed.

### Step 2: Project Genes

```python
ad_ge = tg.project_genes(ad_map, adata_sc, cluster_label=CLUSTER_LABEL)
ad_ge.obsm["spatial"] = adata_sp[ad_ge.obs_names].obsm["spatial"]
print(ad_ge)          # spots x all reference genes; var["is_training"] marks training genes
```

`project_genes` needs the same `cluster_label` as the mapping; a clusters-mode
map projects cell type averages.

### Step 3: Which Projected Genes to Trust

There is no ground truth for unmeasured genes. Use the held-out overlap genes
as a proxy: if they are reproduced poorly, imputed genes are not credible
either. Full diagnostics: `spatial-mapping-validation`.

```python
df_all = tg.compare_spatial_geneexp(ad_ge, adata_sp, adata_sc)
test = df_all[~df_all["is_training"]]
print(f"held-out genes: {len(test)}, median score {test['score'].median():.3f}")

detect_sc = pd.Series(np.asarray((adata_sc.X > 0).mean(0)).ravel(), index=adata_sc.var_names)
trust = pd.DataFrame({
    "measured_in_spatial": [g in adata_sp.var_names for g in in_sc],
    "heldout_score": [df_all["score"].get(g, np.nan) for g in in_sc],
    "frac_cells_expressing_sc": [detect_sc[g] for g in in_sc],
}, index=in_sc)
trust.to_csv("imputation_trust.csv")
print(trust)
```

Report imputed maps as predictions, with the held-out median score next to
them. A gene expressed in < ~5% of reference cells gives a noisy map.

### Step 4: Plot Measured vs Projected

```python
def gene_vec(ad, g):
    x = ad[:, g].X
    return x.toarray().ravel() if hasattr(x, "toarray") else np.asarray(x).ravel()

fig, axes = plt.subplots(len(in_sc), 2, figsize=(9, 4 * len(in_sc)), squeeze=False)
xy = ad_ge.obsm["spatial"]
for row, g in zip(axes, in_sc):
    for ax, (ad, label) in zip(row, [(adata_sp, "measured"), (ad_ge, "projected")]):
        ax.set_title(f"{g} ({label})"); ax.axis("off")
        if g not in ad.var_names:
            ax.text(0.5, 0.5, "not in panel", ha="center", transform=ax.transAxes)
            continue
        v = gene_vec(ad, g)
        ax.scatter(xy[:, 0], xy[:, 1], c=v, s=10, cmap="inferno", vmax=np.quantile(v, 0.98))
        ax.invert_yaxis(); ax.set_aspect("equal")
plt.tight_layout(); plt.savefig("imputed_genes.png", dpi=150)
```

### Step 5 (Alternative): gimVI

gimVI learns a joint latent space of reference and spatial counts. Demo data:
osmFISH mouse cortex (33 genes) and the Zeisel cortex scRNA-seq, downloaded by
scvi-tools on first use into `data/`. A fifth of the panel is held out to
score imputation before imputing the rest of the reference.

```python
from scipy.stats import spearmanr
from scvi.data import cortex, smfish
from scvi.external import GIMVI

st = smfish(save_path="data/")                # replace with your spatial counts AnnData
seq = cortex(save_path="data/")               # replace with your reference counts AnnData
assert set(st.var_names) <= set(seq.var_names), "spatial genes must be a subset of reference genes"

rng = np.random.default_rng(0)
held = rng.choice(st.var_names, max(1, st.n_vars // 5), replace=False)
st_train = st[:, ~st.var_names.isin(held)].copy()
sc.pp.filter_cells(st_train, min_counts=1)
sc.pp.filter_cells(seq, min_counts=1)
st = st[st_train.obs_names].copy()

GIMVI.setup_anndata(seq)
GIMVI.setup_anndata(st_train)
model = GIMVI(seq, st_train)
model.train(max_epochs=200)
_, imputed = model.get_imputed_values(normalized=True)   # spatial cells x all reference genes
imp = pd.DataFrame(imputed, index=st_train.obs_names, columns=seq.var_names)

X = st.X.toarray() if hasattr(st.X, "toarray") else np.asarray(st.X)
obs = pd.DataFrame(X / X.sum(1, keepdims=True).clip(1), index=st.obs_names, columns=st.var_names)
rho = {g: spearmanr(obs[g], imp[g])[0] for g in held}
print(f"held-out genes median Spearman: {np.nanmedian(list(rho.values())):.2f}")
imp.to_csv("gimvi_imputed.csv")
```

To impute genes the panel never measured, keep all reference genes in `seq`
(as above); the held-out check tells how far to trust them.

### Step 6: Save

```python
ad_ge.write_h5ad("tangram_projected_genes.h5ad", compression="gzip")
df_all.to_csv("tangram_gene_scores.csv")
```

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `TARGETS` | from the user | Genes to impute; must be expressed in the reference |
| `cluster_label` (`project_genes`) | same as mapping | Mismatch raises an obs-index error |
| Held-out fraction (gimVI) | 1/5 of panel | Genes withheld to score imputation |
| `max_epochs` (gimVI) | 200 | Training length; lower for a quick CPU run, report it |
| `normalized` (gimVI) | True | Returns normalised expression; compare against library-size-normalised counts |

## Common Recipes

### Recipe: Signature Score from Imputed Genes

A pathway or state signature usually needs more genes than a targeted panel
holds; score it on the projected expression:

```python
SIGNATURE = ["ifng", "gzmb", "prf1", "nkg7", "cxcl9", "cxcl10"]   # lowercase after pp_adatas
genes = [g for g in SIGNATURE if g in ad_ge.var_names]
print(f"{len(genes)} of {len(SIGNATURE)} signature genes available")
sc.tl.score_genes(ad_ge, genes, score_name="signature_score")
xy = ad_ge.obsm["spatial"]
plt.figure(figsize=(6, 6))
plt.scatter(xy[:, 0], xy[:, 1], c=ad_ge.obs["signature_score"], s=10, cmap="viridis")
plt.gca().invert_yaxis(); plt.axis("off"); plt.colorbar(shrink=0.6)
plt.savefig("signature_score_imputed.png", dpi=150)
```

The score inherits the mapping's limits: it marks where cells that express the
signature in the reference were placed.

### Recipe: Which Imputed Genes Have Spatial Structure

Rank projected genes by Moran's I to find those with a spatial pattern
(`pip install squidpy`):

```python
import squidpy as sq

sq.gr.spatial_neighbors(ad_ge, coord_type="generic", n_neighs=6)
cand = [g for g in ad_ge.var_names if g not in adata_sp.var_names][:2000]    # unmeasured genes only
sq.gr.spatial_autocorr(ad_ge, mode="moran", genes=cand, n_perms=100, n_jobs=4)
moran = ad_ge.uns["moranI"].sort_values("I", ascending=False)
moran.to_csv("imputed_genes_moran.csv")
print(moran.head(20)[["I", "pval_norm_fdr_bh"]])
```

High Moran's I on an imputed gene often mirrors the layout of the cell type
that expresses it; check that before calling it a new spatial finding.

### Recipe: Keep Imputed Values Apart from Measurements

Store predictions next to the measured data, never inside `X`, so later
analyses cannot mistake them for counts:

```python
keep = [g for g in in_sc if g not in adata_sp.var_names]          # imputed-only target genes
imputed = pd.DataFrame({g: gene_vec(ad_ge, g) for g in keep}, index=ad_ge.obs_names)
adata_out = adata_sp.copy()
adata_out.obsm["imputed_tangram"] = imputed.loc[adata_out.obs_names]
adata_out.uns["imputation"] = {"method": "tangram", "heldout_median_score": float(test["score"].median())}
adata_out.write_h5ad("spatial_with_imputed.h5ad", compression="gzip")
print(adata_out.obsm["imputed_tangram"].shape)
```

## Expected Outputs

- `tangram_projected_genes.h5ad` - spots x reference genes predicted by Tangram
- `tangram_gene_scores.csv` - per-gene score with `is_training` and sparsity
- `imputation_trust.csv` - target genes with held-out score and reference detection
- `imputed_genes.png` - measured vs projected maps
- `gimvi_imputed.csv` - gimVI imputed expression (optional route)
- `spatial_with_imputed.h5ad` - measured data with imputed genes in `obsm` (recipe)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Target gene missing | Not in reference, or uppercase name | Lowercase names after `pp_adatas`; pick a reference that measures it |
| `The two AnnDatas need to have same obs index` | Clusters-mode map without `cluster_label` | Pass the mapping's `cluster_label` |
| `sc.pl.spatial` fails on projected data | Projected AnnData lacks `uns["spatial"]` | Use the scatter in Step 4 (coords copied in Step 2) |
| Projected map mirrors one cell type's layout | Gene restricted to that type in the reference | Expected; state it, it is not independent evidence |
| `spatial genes needs to be subset of seq genes` | Panel genes absent from the reference, or case differs | Harmonise symbols; drop panel genes the reference lacks |
| gimVI `ImportError`/`AttributeError` | gimVI moved out of scvi-tools | `pip install "scvi-tools<1.6"` |
| gimVI expects counts | Normalised `X` passed | Use raw counts (`setup_anndata(..., layer="counts")`) |

## Related Skills

- `spatial-mapping-tangram` - builds the mapping used here
- `spatial-mapping-validation` - held-out gene scores, AUC, cross-validation
- `spatial-transcriptomics-deconvolution-tangram` - constrained mapping on segmented Visium
- `spatial-panel-design` - choose panel genes so imputation is less needed

## References

- Biancalani et al. (2021) Tangram, Nature Methods: https://doi.org/10.1038/s41592-021-01264-7
- Tangram documentation: https://tangram-sc.readthedocs.io/
- Lopez et al. (2019) gimVI: https://arxiv.org/abs/1905.02269
- scvi-tools GIMVI API: https://docs.scvi-tools.org/en/stable/api/reference/scvi.external.GIMVI.html
- squidpy spatial autocorrelation: https://squidpy.readthedocs.io/en/stable/api/squidpy.gr.spatial_autocorr.html
