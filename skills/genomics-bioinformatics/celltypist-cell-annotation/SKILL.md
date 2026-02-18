---
name: "celltypist-cell-annotation"
description: "Automated cell type annotation for scRNA-seq data using pre-trained logistic regression models. CellTypist ships 45+ models covering immune cells, gut, lung, brain, fetal tissues, and cancer microenvironments. Inputs a normalized AnnData; outputs per-cell predicted labels, majority-vote cluster labels, and confidence scores. Use when you want fast, reproducible, reference-model-backed annotation without manual marker inspection."
license: "MIT"
---

# CellTypist Cell Type Annotation

## Overview

CellTypist is an automated cell type classifier for single-cell RNA-seq data built on logistic regression models trained on curated reference atlases. Given a normalized AnnData object, it predicts cell type labels at the single-cell level and optionally applies majority voting within user-defined clusters to produce consensus, biologically coherent annotations. The tool ships with 45+ ready-to-use models spanning pan-immune, organ-specific, and developmental contexts, and supports training custom models from labeled data.

## When to Use

- Annotating PBMC, whole-blood, lymph node, or other immune cell datasets using a single standardized reference model
- Generating a first-pass cell type annotation before manual curation with canonical marker genes
- Annotating cluster-level cell types in published or in-house datasets using majority voting to smooth noisy per-cell predictions
- Comparing annotation results across multiple tissue-specific models to determine the most biologically relevant reference
- Training a custom CellTypist model from a labeled reference dataset for a tissue or species not covered by pre-built models
- Quantifying annotation confidence to flag low-certainty cells (confidence score < 0.5) for manual review or exclusion
- Use **scVI/scANVI** (scvi-tools-single-cell) instead when you need probabilistic label transfer with batch correction and uncertainty quantification via a variational autoencoder
- Use **popV** (popv-cell-annotation) instead when you want ensemble consensus from 10+ methods including deep learning and KNN-based approaches

## Prerequisites

- **Python packages**: `celltypist>=1.6`, `scanpy>=1.9`, `anndata`
- **Data requirements**: AnnData with normalized, log1p-transformed counts in `adata.X` (10,000 UMIs per cell target sum). Raw counts must be normalized before calling CellTypist
- **Environment**: Python 3.8+; 8 GB RAM sufficient for most datasets; internet access required for model downloads (first run only)

```bash
pip install celltypist "scanpy[leiden]" anndata
```

## Quick Start

Minimal pipeline — annotate a preprocessed AnnData with the pan-immune model:

```python
import celltypist
import scanpy as sc

# Load a preprocessed AnnData (normalized + log1p, Leiden clusters already in adata.obs)
adata = sc.read_h5ad("preprocessed_pbmc.h5ad")

# Run annotation with majority voting across Leiden clusters
predictions = celltypist.annotate(
    adata,
    model="Immune_All_Low.pkl",
    majority_voting=True,
)
adata = predictions.to_adata()

print(adata.obs[["predicted_labels", "majority_voting", "conf_score"]].head(10))
# predicted_labels  majority_voting  conf_score
# CD4+ T cells      CD4+ T cells     0.92
# ...
```

## Workflow

### Step 1: Installation and Model Setup

Install CellTypist and download pre-trained models. Models are cached locally after the first download.

```bash
pip install celltypist "scanpy[leiden]" anndata
```

```python
import celltypist
from celltypist import models

# Download all available models (only needed once; ~2 GB total)
models.download_models(force_update=False)

# List available models with metadata
models_df = models.models_description()
print(models_df[["model", "description", "n_celltypes", "n_cells"]].to_string())
# Output (excerpt):
#   model                          description                                 n_celltypes  n_cells
#   Immune_All_Low.pkl             Pan-immune low-hierarchy (98 cell types)   98           324,320
#   Immune_All_High.pkl            Pan-immune high-hierarchy (30 cell types)  30           324,320
#   Human_Lung_Atlas.pkl           Lung cell types from Human Lung Atlas       61           584,944
```

### Step 2: Data Preparation

CellTypist requires normalized, log1p-transformed counts in `adata.X`. Run normalization before annotation. Raw counts must be stored separately.

```python
import scanpy as sc

# Load raw count matrix
adata = sc.read_h5ad("raw_counts.h5ad")
# Alternatively from 10X:
# adata = sc.read_10x_mtx("filtered_feature_bc_matrix/")
# adata.var_names_make_unique()

# Store raw counts before normalization
adata.layers["counts"] = adata.X.copy()

# Normalize to 10,000 UMIs per cell and log1p-transform
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

print(f"Prepared: {adata.n_obs} cells x {adata.n_vars} genes")
print(f"adata.X mean: {adata.X.mean():.3f}  (expected ~0.5–2.0 after log1p normalization)")
```

### Step 3: Model Selection

Choose the model that best matches your tissue type and desired annotation resolution.

```python
from celltypist import models

# Show full model table with filtering
models_df = models.models_description()

# Filter to human immune models
immune_models = models_df[models_df["description"].str.contains("immune|Immune", case=False)]
print(immune_models[["model", "description", "n_celltypes"]].to_string())

# Load a specific model to inspect its cell type labels
model = models.Model.load("Immune_All_Low.pkl")
print(f"Model cell types ({len(model.cell_types)}):")
print(model.cell_types[:20])  # first 20 labels
```

**Available models (key selection guide):**

| Model | Cell Types | Best For |
|-------|-----------|---------|
| `Immune_All_Low.pkl` | 98 | Pan-immune with fine subtypes (e.g., MAIT, Tfh, cDC1) |
| `Immune_All_High.pkl` | 30 | Pan-immune major lineages (T, B, NK, monocyte, DC) |
| `Human_Lung_Atlas.pkl` | 61 | Lung: alveolar, stromal, immune, endothelial |
| `Pan_Fetal_Human.pkl` | 139 | Fetal human multi-organ development |
| `Developing_Human_Brain.pkl` | 51 | Brain development: progenitors, neurons, glia |
| `Human_Colorectal_Cancer.pkl` | 62 | Colorectal cancer cells + tumor microenvironment |

### Step 4: Automated Annotation

Run `celltypist.annotate()` with `majority_voting=True` for cluster-level consensus labels alongside per-cell predictions.

```python
import celltypist
import scanpy as sc

# Ensure Leiden clusters exist for majority voting
# If not already computed:
sc.pp.highly_variable_genes(adata, n_top_genes=2000)
sc.pp.pca(adata)
sc.pp.neighbors(adata, n_pcs=30)
sc.tl.leiden(adata, resolution=0.5, key_added="leiden")

# Run CellTypist annotation
predictions = celltypist.annotate(
    adata,
    model="Immune_All_Low.pkl",
    majority_voting=True,          # cluster-level consensus
    over_clustering="leiden",      # clustering key for majority voting
    p_thres=0.5,                   # cells below threshold → "Unassigned"
    mode="best match",             # assign the single highest-probability label
)

# Inspect prediction object
print(type(predictions))  # celltypist.classifier.AnnotationResult
print(predictions.predicted_labels.head())
print(predictions.probability_matrix.shape)  # (n_cells, n_cell_types)
```

### Step 5: Results Integration

Transfer predictions back to the AnnData object and review confidence scores.

```python
# Merge predictions into adata.obs
adata = predictions.to_adata()

# Key result columns:
# adata.obs["predicted_labels"]  — per-cell best-match label
# adata.obs["majority_voting"]   — cluster-level consensus label
# adata.obs["conf_score"]        — probability of the predicted label (0–1)

print(adata.obs[["predicted_labels", "majority_voting", "conf_score"]].head(10))
print(f"\nCell type distribution (majority voting):")
print(adata.obs["majority_voting"].value_counts().head(15))

# Flag low-confidence cells
low_conf = adata.obs["conf_score"] < 0.5
print(f"\nLow-confidence cells (conf_score < 0.5): {low_conf.sum()} ({low_conf.mean():.1%})")
adata.obs["high_conf"] = ~low_conf
```

### Step 6: Visualization and Validation

Plot predictions on UMAP, validate with canonical marker genes, and confirm annotation quality.

```python
import scanpy as sc
import matplotlib.pyplot as plt

# Compute UMAP if not already done
if "X_umap" not in adata.obsm:
    sc.tl.umap(adata)

# UMAP colored by annotation results
fig, axes = plt.subplots(1, 3, figsize=(21, 6))
sc.pl.umap(adata, color="majority_voting", legend_loc="on data",
           legend_fontsize=7, title="Majority Voting", ax=axes[0], show=False)
sc.pl.umap(adata, color="predicted_labels", legend_loc="right margin",
           legend_fontsize=7, title="Per-Cell Prediction", ax=axes[1], show=False)
sc.pl.umap(adata, color="conf_score", cmap="RdYlGn",
           title="Confidence Score", ax=axes[2], show=False)
plt.tight_layout()
plt.savefig("celltypist_annotation.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved celltypist_annotation.png")

# Validate with canonical immune markers
marker_genes = {
    "CD4+ T": ["CD3D", "CD4", "IL7R"],
    "CD8+ T": ["CD3D", "CD8A", "GZMK"],
    "B cells": ["MS4A1", "CD79A"],
    "NK cells": ["GNLY", "NKG7"],
    "CD14 Mono": ["CD14", "LYZ"],
}
sc.pl.dotplot(adata, var_names=marker_genes, groupby="majority_voting",
              use_raw=False, standard_scale="var",
              save="_celltypist_markers.png")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `model` | — | Any `.pkl` filename or path | Selects the reference atlas for annotation; must match tissue/species |
| `majority_voting` | `False` | `True`, `False` | When `True`, smooths per-cell labels to cluster consensus; requires a clustering key in `over_clustering` |
| `over_clustering` | `None` | Any `adata.obs` key, `"leiden"`, `"louvain"` | Clustering column used for majority voting; auto-detected if common keys present |
| `p_thres` | `0.5` | `0.0`–`1.0` | Minimum probability to assign a label; cells below threshold are labeled `"Unassigned"` |
| `mode` | `"best match"` | `"best match"`, `"prob match"` | `"best match"`: top label regardless of threshold; `"prob match"`: applies `p_thres` |
| `min_prop` | `0.0` | `0.0`–`1.0` | For majority voting: minimum fraction of cluster cells with the consensus label; rare labels may be suppressed |

## Key Concepts

### Pre-Trained Model Architecture

Each CellTypist model is a one-vs-rest logistic regression classifier trained on a curated cell atlas. Key properties:

- **Input**: 33,694 genes (or fewer if the dataset has a smaller gene space — unshared genes are zero-filled)
- **Output**: per-cell probability vector over all cell type classes; highest probability is the predicted label
- **Confidence score**: the probability assigned to the winning class (0–1); high values (>0.7) indicate reliable predictions
- **Species/version specificity**: models are trained on specific atlases; using a human model on mouse data will produce spurious results

### Majority Voting

Majority voting applies a two-stage correction after per-cell prediction:

1. Each cell receives a per-cell label from the logistic regression output
2. Within each cluster (e.g., Leiden cluster), the most frequent per-cell label becomes the cluster's consensus `majority_voting` label
3. Cells whose per-cell label disagrees with the cluster majority are re-labeled to the cluster consensus unless `min_prop` is set

Majority voting is recommended when individual cells have noisy expression but the cluster is biologically coherent. Disable it when cells within a cluster are biologically heterogeneous (e.g., transitional states).

### Gene Space Alignment

CellTypist automatically intersects the model's training genes with the input AnnData's gene names. Genes present in the model but absent from the query are zero-filled. Annotations degrade if fewer than ~60% of model genes are present — check with `model.cell_types` and `adata.var_names`.

## Common Recipes

### Recipe: Train a Custom Model

When to use: your tissue or species is not covered by an existing model, and you have a labeled reference dataset.

```python
import celltypist
import scanpy as sc

# Load labeled reference AnnData (must be normalized + log1p)
ref = sc.read_h5ad("labeled_reference.h5ad")
# ref.obs["cell_type"] must contain string cell type labels

# Train custom model
new_model = celltypist.train(
    ref,
    labels="cell_type",       # obs column with training labels
    n_jobs=4,                  # parallel workers
    max_iter=200,              # logistic regression iterations
    use_SGD=False,             # use full L-BFGS-B solver (recommended for <100k cells)
    top_genes=500,             # number of most informative genes per class
)

# Save for reuse
new_model.write("custom_tissue_model.pkl")
print(f"Trained model: {len(new_model.cell_types)} cell types")

# Apply to query
predictions = celltypist.annotate(query_adata, model="custom_tissue_model.pkl",
                                  majority_voting=True)
```

### Recipe: Multi-Model Comparison

When to use: uncertain which model best matches your dataset; run multiple models and compare agreement.

```python
import celltypist
import pandas as pd

model_names = ["Immune_All_High.pkl", "Immune_All_Low.pkl", "Human_Lung_Atlas.pkl"]
results = {}

for model_name in model_names:
    preds = celltypist.annotate(adata, model=model_name, majority_voting=True)
    adata_tmp = preds.to_adata()
    key = model_name.replace(".pkl", "")
    results[key] = adata_tmp.obs["majority_voting"].values

comparison = pd.DataFrame(results, index=adata.obs_names)
print("Agreement between Immune_All_High and Immune_All_Low:")
agreement = (comparison["Immune_All_High"] == comparison["Immune_All_Low"]).mean()
print(f"  {agreement:.1%} of cells agree")
print(comparison.head(10))
```

### Recipe: Export Annotations for Downstream Analysis

When to use: saving annotated data with all prediction metadata for downstream differential expression or trajectory analysis.

```python
import scanpy as sc
import pandas as pd

# Save full annotated AnnData
adata.write_h5ad("annotated_celltypist.h5ad", compression="gzip")
print(f"Saved annotated_celltypist.h5ad  ({adata.n_obs} cells)")

# Export cell type table
cell_table = adata.obs[[
    "predicted_labels", "majority_voting", "conf_score", "leiden"
]].copy()
cell_table.to_csv("celltypist_annotations.csv")

# Cell type proportions per sample
if "sample" in adata.obs.columns:
    props = (adata.obs.groupby(["sample", "majority_voting"])
             .size().unstack(fill_value=0))
    props_norm = props.div(props.sum(axis=1), axis=0)
    props_norm.to_csv("celltypist_proportions.csv")
    print(f"Cell type proportions saved (shape: {props_norm.shape})")
```

## Expected Outputs

| Output | Description |
|--------|-------------|
| `adata.obs["predicted_labels"]` | Per-cell best-match label from logistic regression |
| `adata.obs["majority_voting"]` | Cluster-consensus label (when `majority_voting=True`) |
| `adata.obs["conf_score"]` | Probability of the predicted label (0–1); `>0.5` = confident |
| `adata.obsm["X_umap"]` | UMAP embedding (if computed in preprocessing step) |
| `celltypist_annotation.png` | UMAP panels: majority voting label, per-cell label, confidence scores |
| `celltypist_annotations.csv` | Per-cell annotation table with predicted labels and confidence |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: adata.X does not appear to be log1p normalized` | Raw counts passed directly | Run `sc.pp.normalize_total(adata, target_sum=1e4)` then `sc.pp.log1p(adata)` before calling `celltypist.annotate()` |
| Many cells labeled `"Unassigned"` | `p_thres` too high or model species mismatch | Lower `p_thres` to `0.3`; verify model matches species and tissue; check `conf_score` distribution |
| `KeyError` for `over_clustering` key | Clustering column name not found in `adata.obs` | Run `sc.tl.leiden(adata, key_added="leiden")` first, or set `over_clustering="leiden"` explicitly |
| Implausible labels (e.g., immune labels on neurons) | Wrong model selected for tissue | Choose a tissue-specific model (e.g., `Developing_Human_Brain.pkl` for brain data); list options with `models.models_description()` |
| `MemoryError` on large datasets (>500k cells) | Full probability matrix held in RAM | Subsample to 200k cells for annotation, then transfer labels via KNN; or use `mode="best match"` to skip storing full probability matrix |
| Low overall `conf_score` (<0.4 median) | Dataset is poorly represented by the reference model | Train a custom model from a matched reference or use `popv-cell-annotation` for ensemble voting |
| `Model not found` error on download | Network issue or wrong model name | Run `models.download_models(force_update=True)`; verify name with `models.models_description()["model"].tolist()` |

## Related Skills

- **scanpy-scrna-seq** — preprocessing pipeline (QC, normalization, clustering) that produces the AnnData input for CellTypist
- **popv-cell-annotation** — ensemble annotation using 10+ methods; use when you want consensus across methods rather than a single model
- **scvi-tools-single-cell** — scANVI for semi-supervised label transfer with deep generative models and probabilistic uncertainty
- **harmony-batch-correction** — batch correction to apply before annotation when integrating multiple samples

## References

- [CellTypist documentation](https://celltypist.readthedocs.io/) — official API reference, model descriptions, and tutorials
- [GitHub: Teichlab/celltypist](https://github.com/Teichlab/celltypist) — source code and issue tracker
- [Dominguez Conde et al., Science 2022](https://doi.org/10.1126/science.abl5197) — "Cross-tissue immune cell analysis reveals tissue-specific features in humans", original CellTypist paper
- [CellTypist model portal](https://www.celltypist.org/models) — interactive model browser with cell type hierarchies and training dataset details
