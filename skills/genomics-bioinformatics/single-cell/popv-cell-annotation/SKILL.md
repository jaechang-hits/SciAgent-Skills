---
name: "popv-cell-annotation"
description: "Consensus cell type annotation: runs 10+ algorithms (KNN-Harmony/BBKNN/Scanorama/scVI, CellTypist, ONCLASS, Random Forest, SCANVI, SVM, XGBoost) on a labeled reference and transfers labels via majority voting. Outputs per-method labels, consensus, agreement score. Use when single-method annotation is insufficient or you need ensemble uncertainty for novel states."
license: "BSD-3-Clause"
---

# popV Multi-Method Cell Type Transfer

## Overview

popV (Population Voting for single-cell annotation) annotates a query scRNA-seq dataset by running 10+ independent classification algorithms against a labeled reference atlas and aggregating results via majority voting. Each method produces its own label; the final `popv_prediction` is the consensus across all methods, and the `popv_agreement` score quantifies how many methods agree. This ensemble strategy is robust to individual method failures on unusual datasets and provides a principled uncertainty estimate: low agreement highlights novel cell states or annotation gaps.

## When to Use

- Annotating a query dataset by transferring labels from a well-curated reference atlas when you want a consensus rather than a single model's judgment
- Identifying novel or ambiguous cell states as cells where methods disagree (low `popv_agreement` score)
- Benchmarking annotation reliability by comparing per-method labels to detect systematic disagreements
- Annotating large atlas datasets (>100k cells) where batch effects between reference and query are substantial
- Producing annotation for downstream analyses that require high-confidence labels (clinical data, regulatory submissions)
- Use **CellTypist** (celltypist-cell-annotation) instead when speed matters and a pre-trained model matches your tissue; popV is slower because it trains multiple models on your reference
- Use **scANVI** (scvi-tools-single-cell) instead when you need a single probabilistic deep generative model with formal uncertainty quantification and do not require the ensemble

## Prerequisites

- **Python packages**: `popv>=0.6`, `scanpy>=1.9`, `anndata`, `scvi-tools>=1.0`, `harmonypy`, `bbknn`, `celltypist`
- **Data requirements**: Two AnnData objects — a labeled reference (`adata_ref`) with cell type labels in `obs`, and an unlabeled query (`adata_query`). Both must be from the same species and have overlapping gene sets. Raw counts in `adata.X` (popV applies its own normalization internally)
- **Environment**: Python 3.9+; GPU recommended for scVI/SCANVI methods (falls back to CPU); 32 GB RAM recommended for >200k reference cells

```bash
pip install popv scvi-tools harmonypy bbknn celltypist
```

## Quick Start

Minimal pipeline from labeled reference and unlabeled query to annotated result:

```python
import popv
import scanpy as sc

# Load reference (labeled) and query (unlabeled) AnnData objects
adata_ref = sc.read_h5ad("reference_atlas.h5ad")  # adata_ref.obs["cell_type"] exists
adata_query = sc.read_h5ad("query_dataset.h5ad")

# Prepare combined object with popV preprocessing
adata = popv.preprocessing.Process_Query(
    adata_ref,
    adata_query,
    ref_labels_key="cell_type",
    ref_batch_key="batch",
    query_batch_key="batch",
    unknown_celltype_label="unknown",
    save_path_trained_models="./popv_models/",
    n_epochs_unsupervised=50,
)

# Run all annotation methods
popv.annotation.annotate_data(adata)

# Inspect consensus results for query cells
query_mask = adata.obs["_dataset"] == "query"
print(adata[query_mask].obs[["popv_prediction", "popv_agreement"]].head(10))
```

## Core API

### Module 1: Reference and Query Data Setup

Both AnnData objects must share a gene space and have required metadata columns. popV will subset to the intersection of genes automatically.

```python
import anndata as ad
import scanpy as sc
import numpy as np

# Reference: must have cell type labels and (optionally) batch metadata
adata_ref = sc.read_h5ad("reference_atlas.h5ad")
print(f"Reference: {adata_ref.n_obs} cells x {adata_ref.n_vars} genes")
print(f"Cell types: {adata_ref.obs['cell_type'].nunique()} unique labels")
print(f"Reference cell type counts:\n{adata_ref.obs['cell_type'].value_counts().head(10)}")

# Query: no labels required; batch metadata optional
adata_query = sc.read_h5ad("query_dataset.h5ad")
print(f"\nQuery: {adata_query.n_obs} cells x {adata_query.n_vars} genes")

# Check gene overlap (popV will handle subsetting but >70% overlap is recommended)
shared_genes = adata_ref.var_names.intersection(adata_query.var_names)
pct_shared = len(shared_genes) / adata_ref.n_vars
print(f"\nShared genes: {len(shared_genes)} ({pct_shared:.1%} of reference genes)")
if pct_shared < 0.5:
    print("WARNING: <50% gene overlap — annotation quality may be reduced")
```

```python
# Verify required fields before popV setup
assert "cell_type" in adata_ref.obs.columns, "Reference needs cell type labels"

# Add batch column if absent (popV requires it even for single-batch data)
if "batch" not in adata_ref.obs.columns:
    adata_ref.obs["batch"] = "ref_batch"
if "batch" not in adata_query.obs.columns:
    adata_query.obs["batch"] = "query_batch"

print("Reference obs columns:", adata_ref.obs.columns.tolist())
print("Query obs columns:    ", adata_query.obs.columns.tolist())
```

### Module 2: POPV Object Creation (Process_Query)

`Process_Query` combines reference and query, normalizes counts, selects HVGs, and prepares the joint embedding needed by all annotation methods.

```python
import popv

# Create processed combined AnnData
adata = popv.preprocessing.Process_Query(
    adata_ref,
    adata_query,
    ref_labels_key="cell_type",      # obs column with reference labels
    ref_batch_key="batch",           # obs column with reference batch info
    query_batch_key="batch",         # obs column with query batch info
    unknown_celltype_label="unknown",# label to use for query cells before annotation
    save_path_trained_models="./popv_models/",  # directory for scVI/SCANVI model checkpoints
    n_epochs_unsupervised=50,        # scVI training epochs (increase to 100–200 for large datasets)
    n_epochs_semisupervised=20,      # scANVI fine-tuning epochs
    use_gpu=True,                    # GPU for scVI/SCANVI (falls back to CPU if unavailable)
    hvg=4000,                        # number of highly variable genes to use
)

print(f"Combined object: {adata.n_obs} cells x {adata.n_vars} genes")
print(f"Dataset labels: {adata.obs['_dataset'].value_counts().to_dict()}")
# Expected: {'ref': N_ref, 'query': N_query}
```

### Module 3: Running the Method Ensemble

`annotate_data` runs all selected methods sequentially and adds per-method label columns plus the consensus to `adata.obs`.

```python
import popv

# Run annotation with default set of methods
popv.annotation.annotate_data(
    adata,
    methods=[
        "knn_harmony",    # KNN on Harmony-corrected embedding
        "knn_bbknn",      # KNN on BBKNN cross-batch graph
        "knn_scvi",       # KNN on scVI latent space
        "scanvi_popv",    # Semi-supervised scANVI label transfer
        "celltypist_popv",# CellTypist logistic regression
        "rf",             # Random Forest on HVG expression
        "xgboost",        # XGBoost classifier
        "svm",            # Support Vector Machine
        "onclass",        # ONCLASS (ontology-guided)
    ],
)

# Inspect per-method result columns (all end in "_popv")
query_mask = adata.obs["_dataset"] == "query"
popv_cols = adata.obs.filter(like="_popv").columns.tolist()
print(f"Per-method columns: {popv_cols}")
print(adata[query_mask].obs[popv_cols + ["popv_prediction", "popv_agreement"]].head(10))
```

### Module 4: Consensus Results and Agreement Scoring

`popv_prediction` is the majority-vote consensus; `popv_agreement` is the fraction of methods that agreed on the winning label.

```python
import pandas as pd

query_mask = adata.obs["_dataset"] == "query"
query_obs = adata[query_mask].obs.copy()

# Consensus label distribution
print("Consensus cell type distribution:")
print(query_obs["popv_prediction"].value_counts().head(15))

# Agreement score statistics
print(f"\npopv_agreement statistics:")
print(query_obs["popv_agreement"].describe())
# agreement = 1.0 → all methods agree; agreement = 0.2 → only 2/10 methods agree

# Cells with high confidence (>80% method agreement)
high_conf = query_obs["popv_agreement"] >= 0.8
print(f"\nHigh-confidence cells (agreement >= 0.8): {high_conf.sum()} ({high_conf.mean():.1%})")

# Cells with low confidence — candidate novel states or annotation gaps
low_conf = query_obs["popv_agreement"] < 0.5
print(f"Low-confidence cells  (agreement <  0.5): {low_conf.sum()} ({low_conf.mean():.1%})")
```

### Module 5: Visualization

popV provides built-in UMAP and heatmap visualization of per-method agreement and consensus labels.

```python
import popv
import scanpy as sc
import matplotlib.pyplot as plt

# Compute UMAP on the joint reference+query embedding (if not already present)
if "X_umap" not in adata.obsm:
    sc.tl.umap(adata)

# popV built-in visualization: UMAP panel showing consensus + agreement
popv.visualization.predict_celltypes_umap(
    adata,
    save="popv_annotation_umap.png",
)
print("Saved popv_annotation_umap.png")

# Custom UMAP panels
fig, axes = plt.subplots(1, 3, figsize=(21, 6))
sc.pl.umap(adata, color="popv_prediction", ax=axes[0],
           title="popV Consensus", legend_loc="on data",
           legend_fontsize=6, show=False)
sc.pl.umap(adata, color="popv_agreement", ax=axes[1],
           cmap="RdYlGn", vmin=0, vmax=1,
           title="Method Agreement Score", show=False)
sc.pl.umap(adata, color="_dataset", ax=axes[2],
           title="Reference vs Query", show=False)
plt.tight_layout()
plt.savefig("popv_custom_umap.png", dpi=150, bbox_inches="tight")
print("Saved popv_custom_umap.png")
```

## Key Concepts

### Method Ensemble and Majority Voting

popV runs each method independently; the final prediction is determined by plurality vote across all methods. The `popv_agreement` score equals the fraction of methods that voted for the winning label (e.g., 0.7 = 7/10 methods agreed). This design has several properties:

- **Robustness**: if one method fails or produces outlier labels, the consensus is unaffected if the remaining methods agree
- **Uncertainty signal**: low agreement does not mean the annotation is wrong — it often flags biologically interesting cells (transitional states, rare populations) that differ from all reference cell types
- **Method independence**: KNN-based methods depend on the embedding quality; tree-based methods (RF, XGBoost) work directly on expression; SVM works in feature space; CellTypist uses a separate logistic regression. Together they span multiple algorithmic families

### Method Comparison

| Method | Batch Correction | Speed | Best For |
|--------|-----------------|-------|---------|
| `knn_harmony` | Harmony | Fast | Moderate batch effects, large datasets |
| `knn_bbknn` | BBKNN | Fast | Diverse multi-tissue references |
| `knn_scanorama` | Scanorama | Fast | Multiple heterogeneous batches |
| `knn_scvi` | scVI VAE | Medium | Complex batch effects, probabilistic embedding |
| `scanvi_popv` | scVI+labels | Slow | Semi-supervised; most accurate when reference is clean |
| `celltypist_popv` | None (logistic) | Fast | Immune cells; works well without batch correction |
| `rf` | None | Medium | Balanced class distributions; interpretable feature importance |
| `xgboost` | None | Medium | High-confidence predictions on well-separated cell types |
| `svm` | None | Medium | High-dimensional gene expression; linear boundaries |
| `onclass` | None | Medium | Ontology-aware; handles unseen cell types via CL ontology |

### ONCLASS and Ontology-Aware Annotation

ONCLASS uses the Cell Ontology (CL) to represent cell types as nodes in a knowledge graph and predict unseen cell types by propagating similarity through the ontology. Unlike other methods, ONCLASS can predict a cell type that was not present in the training reference if it is ontologically adjacent to known types. Enable it by including `"onclass"` in the methods list.

### Reference Quality Requirements

popV annotation quality scales directly with reference quality:

- **Minimum cell count per type**: 50–100 cells per label; rare types with <20 cells may be missed by KNN methods
- **Balanced representation**: highly imbalanced references (one type is 80% of cells) cause tree methods to be biased toward the majority class
- **Label granularity**: coarse labels (10 types) annotate reliably; fine-grained labels (100+ types) require a larger, matched reference

## Common Workflows

### Workflow 1: Standard Reference-Query Annotation

**Goal**: Annotate an unlabeled query dataset using a curated reference atlas end-to-end.

```python
import popv
import scanpy as sc
import pandas as pd

# 1. Load data
adata_ref = sc.read_h5ad("reference_atlas.h5ad")   # has obs["cell_type"] and obs["batch"]
adata_query = sc.read_h5ad("query_dataset.h5ad")   # no cell type labels
if "batch" not in adata_query.obs.columns:
    adata_query.obs["batch"] = "query"

# 2. Preprocess: build joint normalized object
adata = popv.preprocessing.Process_Query(
    adata_ref,
    adata_query,
    ref_labels_key="cell_type",
    ref_batch_key="batch",
    query_batch_key="batch",
    unknown_celltype_label="unknown",
    save_path_trained_models="./popv_models/",
    n_epochs_unsupervised=100,
    n_epochs_semisupervised=30,
    use_gpu=True,
    hvg=4000,
)
print(f"Prepared: {adata.n_obs} total cells")

# 3. Run ensemble annotation
popv.annotation.annotate_data(adata)

# 4. Extract query results
query_mask = adata.obs["_dataset"] == "query"
query_annotations = adata[query_mask].obs[[
    "popv_prediction", "popv_agreement",
    "knn_harmony_popv", "scanvi_popv", "rf_popv", "xgboost_popv"
]].copy()

# 5. Transfer back to original query object
adata_query.obs = adata_query.obs.join(
    query_annotations, how="left"
)
print(f"Annotated {query_mask.sum()} query cells")
print(query_annotations["popv_prediction"].value_counts().head(10))

# 6. Save annotated query
adata_query.write_h5ad("annotated_query.h5ad", compression="gzip")
query_annotations.to_csv("popv_annotations.csv")
print("Saved annotated_query.h5ad and popv_annotations.csv")
```

### Workflow 2: Confidence Filtering and Novel Cell State Detection

**Goal**: Separate high-confidence annotations from ambiguous cells; flag candidate novel or transitional states for manual review.

```python
import popv
import scanpy as sc
import pandas as pd
import matplotlib.pyplot as plt

# Assume adata has been annotated (as in Workflow 1)
query_mask = adata.obs["_dataset"] == "query"
query_obs = adata[query_mask].obs.copy()

# Tier cells by agreement score
bins = [0.0, 0.5, 0.8, 1.01]
labels = ["low (<0.5)", "medium (0.5–0.8)", "high (≥0.8)"]
query_obs["confidence_tier"] = pd.cut(
    query_obs["popv_agreement"], bins=bins, labels=labels, right=False
)
print("Cells per confidence tier:")
print(query_obs["confidence_tier"].value_counts())

# High-confidence subset: use popv_prediction directly
high_conf_mask = query_obs["popv_agreement"] >= 0.8
print(f"\nHigh-confidence annotations ({high_conf_mask.mean():.1%} of query cells):")
print(query_obs[high_conf_mask]["popv_prediction"].value_counts().head(10))

# Low-confidence subset: inspect per-method disagreement
low_conf = query_obs[query_obs["popv_agreement"] < 0.5]
popv_method_cols = [c for c in query_obs.columns if c.endswith("_popv") and
                    c not in ("popv_prediction", "popv_agreement")]
print(f"\nLow-confidence cells sample (showing per-method labels):")
print(low_conf[popv_method_cols + ["popv_prediction"]].head(10).to_string())

# Visualize agreement distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
query_obs["popv_agreement"].hist(bins=20, ax=axes[0], color="steelblue", edgecolor="white")
axes[0].axvline(0.8, color="red", linestyle="--", label="High-confidence threshold")
axes[0].set_xlabel("Method Agreement Score")
axes[0].set_ylabel("Cell Count")
axes[0].set_title("popV Agreement Distribution")
axes[0].legend()

query_obs["confidence_tier"].value_counts().plot.bar(ax=axes[1], color="steelblue")
axes[1].set_title("Cells by Confidence Tier")
axes[1].set_xlabel("Confidence Tier")
axes[1].set_ylabel("Cell Count")
plt.tight_layout()
plt.savefig("popv_confidence_distribution.png", dpi=150, bbox_inches="tight")
print("Saved popv_confidence_distribution.png")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `ref_labels_key` | Process_Query | — | Any `obs` column | Column in `adata_ref.obs` containing training cell type labels |
| `n_epochs_unsupervised` | Process_Query | `50` | `20`–`500` | scVI training epochs; increase for better embedding on large/complex datasets |
| `n_epochs_semisupervised` | Process_Query | `20` | `10`–`100` | scANVI fine-tuning epochs on top of scVI |
| `hvg` | Process_Query | `4000` | `2000`–`8000` | Highly variable genes used for embedding and KNN methods |
| `use_gpu` | Process_Query | `True` | `True`, `False` | GPU acceleration for scVI/SCANVI; falls back to CPU automatically if no GPU |
| `methods` | annotate_data | all | List of method names | Subset of methods to run; excluding slow methods (scanvi, onclass) speeds up pipeline |
| `unknown_celltype_label` | Process_Query | `"unknown"` | Any string | Label assigned to query cells before annotation; used to separate reference labels from query |
| `popv_agreement` | (output) | — | `0.0`–`1.0` | Fraction of methods agreeing on consensus label; `>=0.8` recommended for high confidence |

## Best Practices

1. **Check gene overlap before running**: popV performs best with >70% gene overlap between reference and query. If overlap is <50%, annotation quality degrades significantly — consider using a different reference or imputing missing genes.
   ```python
   shared = adata_ref.var_names.intersection(adata_query.var_names)
   print(f"Gene overlap: {len(shared) / adata_ref.n_vars:.1%}")
   ```

2. **Use raw counts as input**: pass raw (un-normalized) counts in `adata.X` to `Process_Query`. popV internally applies its own normalization. Pre-normalized data can distort the scVI/SCANVI latent space.

3. **Match reference granularity to query biology**: if your query contains subtypes not in the reference, no method will correctly assign them — they will appear as low-agreement cells. Either add them to the reference or accept that the consensus will assign the nearest parent type.

4. **Exclude slow methods when speed matters**: `scanvi_popv` and `onclass` are the slowest. For a quick first-pass, run only `knn_harmony`, `knn_bbknn`, `rf`, `xgboost`, and `celltypist_popv`.
   ```python
   popv.annotation.annotate_data(adata, methods=["knn_harmony", "knn_bbknn", "rf", "xgboost", "celltypist_popv"])
   ```

5. **Save trained models for repeated queries**: `Process_Query` stores scVI/SCANVI models in `save_path_trained_models`. Reuse these when annotating additional query batches against the same reference to avoid retraining.

## Common Recipes

### Recipe: Subset to High-Confidence Annotations Only

When to use: downstream analyses (DE, trajectory) require clean labels; exclude ambiguous cells.

```python
import scanpy as sc

# Annotate as in Workflow 1 first
query_mask = adata.obs["_dataset"] == "query"
adata_query_annotated = adata[query_mask].copy()

# Keep only high-confidence cells
high_conf = adata_query_annotated[adata_query_annotated.obs["popv_agreement"] >= 0.8].copy()
print(f"High-confidence cells: {high_conf.n_obs} / {adata_query_annotated.n_obs} "
      f"({high_conf.n_obs/adata_query_annotated.n_obs:.1%})")
print(high_conf.obs["popv_prediction"].value_counts())

# Recompute UMAP on high-confidence subset for visualization
sc.pp.neighbors(high_conf, use_rep="X_scVI")  # use scVI embedding stored by popV
sc.tl.umap(high_conf)
sc.pl.umap(high_conf, color="popv_prediction", save="_high_conf_celltypes.png")
```

### Recipe: Per-Method Label Comparison Heatmap

When to use: understanding where methods disagree to identify systematic biases or novel populations.

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

query_mask = adata.obs["_dataset"] == "query"
query_obs = adata[query_mask].obs.copy()

# Collect per-method columns
method_cols = [c for c in query_obs.columns
               if c.endswith("_popv") and c not in ("popv_prediction", "popv_agreement")]

# Cross-tabulate two key methods
ct = pd.crosstab(
    query_obs["knn_harmony_popv"],
    query_obs["scanvi_popv"],
    margins=False,
)
# Normalize rows
ct_norm = ct.div(ct.sum(axis=1), axis=0)

plt.figure(figsize=(12, 10))
sns.heatmap(ct_norm, cmap="Blues", vmin=0, vmax=1,
            xticklabels=True, yticklabels=True,
            cbar_kws={"label": "Fraction of cells"})
plt.title("knn_harmony vs scanvi label agreement")
plt.xlabel("SCANVI label")
plt.ylabel("KNN-Harmony label")
plt.tight_layout()
plt.savefig("popv_method_agreement_heatmap.png", dpi=150)
print("Saved popv_method_agreement_heatmap.png")
```

### Recipe: Fast Annotation Without Deep Learning Methods

When to use: quick annotation without GPU or when scVI/SCANVI training is prohibitively slow (>500k cells).

```python
import popv

# Process without training deep generative models (scVI not needed for KNN-Harmony)
adata = popv.preprocessing.Process_Query(
    adata_ref,
    adata_query,
    ref_labels_key="cell_type",
    ref_batch_key="batch",
    query_batch_key="batch",
    unknown_celltype_label="unknown",
    save_path_trained_models="./popv_models/",
    n_epochs_unsupervised=0,   # skip scVI training
    n_epochs_semisupervised=0, # skip scANVI training
    use_gpu=False,
    hvg=3000,
)

# Run only fast non-DL methods
popv.annotation.annotate_data(
    adata,
    methods=["knn_harmony", "knn_bbknn", "knn_scanorama", "rf", "xgboost", "svm", "celltypist_popv"],
)

query_mask = adata.obs["_dataset"] == "query"
print(adata[query_mask].obs[["popv_prediction", "popv_agreement"]].describe())
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `KeyError: ref_labels_key not in adata_ref.obs` | Reference lacks a cell type column | Verify the column name: `print(adata_ref.obs.columns.tolist())`; update `ref_labels_key` accordingly |
| Gene space mismatch error | Reference and query have very few shared genes | Check `adata_ref.var_names.intersection(adata_query.var_names)`; if <50% overlap, use a different reference or match gene panels |
| CUDA out-of-memory for scVI/SCANVI | GPU VRAM insufficient for batch size | Set `use_gpu=False` or reduce `n_epochs_unsupervised`; scVI falls back to CPU automatically on most systems |
| `onclass_popv` failures on small datasets | ONCLASS requires sufficient label coverage | Remove `"onclass"` from the methods list when reference has <10 cell types or <500 cells per type |
| Very slow annotation (>2 hours) | scVI/SCANVI training on large reference | Subsample reference to 50k cells per type; exclude `"scanvi_popv"` and `"onclass"` from methods |
| All cells receive same consensus label | Reference highly imbalanced toward one type | Balance reference by subsampling the dominant type or upsampling rare types before running popV |
| `popv_agreement` is 0 for many cells | Many methods returning different labels | Inspect per-method columns; consider whether reference covers the query biology; add methods or retrain with a better reference |

## Related Skills

- **celltypist-cell-annotation** — single-model annotation with pre-trained logistic regression; faster but lacks ensemble uncertainty
- **scanpy-scrna-seq** — preprocessing pipeline (QC, normalization, clustering) that produces AnnData inputs for popV
- **scvi-tools-single-cell** — scANVI for probabilistic label transfer with a single deep generative model; use when you prefer a formal variational framework over ensemble voting
- **harmony-batch-correction** — Harmony embedding used by `knn_harmony` method internally; understand it to tune popV's KNN-based methods

## References

- [GitHub: YosefLab/popV](https://github.com/YosefLab/popV) — official source code, installation instructions, and example notebooks
- [popV documentation](https://popv.readthedocs.io/) — API reference and tutorials
- [Ergen et al., bioRxiv 2023](https://doi.org/10.1101/2023.06.15.545239) — "Population-level integration of single-cell datasets enables multi-scale analysis across samples", original popV preprint
- [ONCLASS paper — Wang et al., Nature Methods 2021](https://doi.org/10.1038/s41592-021-01080-9) — ontology-aware cell type classification underlying the ONCLASS method in popV
