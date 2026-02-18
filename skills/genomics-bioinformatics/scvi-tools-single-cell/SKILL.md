---
name: "scvi-tools-single-cell"
description: "Deep generative models for single-cell omics. Probabilistic batch correction (scVI), semi-supervised annotation (scANVI), CITE-seq RNA+protein modeling (totalVI), transfer learning to new datasets (scARCHES), and differential expression with uncertainty quantification. Unified setup→train→extract API on AnnData. Use harmony-batch-correction for fast linear batch correction without deep learning; use muon for multi-modal MuData workflows; use scVI for probabilistic, deep learning-based integration with uncertainty quantification."
license: "BSD-3-Clause"
---

# scvi-tools — Single-Cell Deep Generative Models

## Overview

scvi-tools is a probabilistic modeling framework for single-cell genomics built on PyTorch. It implements variational autoencoders (VAEs) that learn low-dimensional latent representations of cells while explicitly modeling batch effects, count noise distributions, and multi-modal data. All models share a unified API: `setup_anndata()` to register data, instantiate the model, `train()`, then extract latent representations, normalized expression, or differential expression results. Models operate on raw count data in AnnData format and return statistically grounded outputs with uncertainty estimates.

## When to Use

- Integrating multiple scRNA-seq batches or studies with probabilistic batch correction that preserves biological variation
- Performing differential expression with uncertainty quantification and composite hypotheses (not just fold-change thresholding)
- Annotating cell types via semi-supervised transfer learning from a partially-labeled reference (scANVI)
- Jointly modeling CITE-seq protein and RNA data to obtain denoised protein estimates and joint embeddings (totalVI)
- Adapting a pretrained model to a new query dataset without full retraining (scARCHES transfer learning)
- Deconvolving spatial transcriptomics spots into cell type proportions using a matched scRNA-seq reference (DestVI)
- Detecting doublets in scRNA-seq data as a QC preprocessing step (Solo)
- Use **harmony-batch-correction** instead when you need fast linear batch correction (seconds vs minutes) without deep learning overhead
- For **multi-modal MuData workflows** (joint RNA+ATAC Multiome, combined modality objects), use **muon** instead
- For **standard clustering and visualization** without batch effects or probabilistic DE, use **scanpy-scrna-seq**

## Prerequisites

- **Python packages**: `scvi-tools>=1.1`, `scanpy`, `anndata`
- **Data requirements**: AnnData (`.h5ad`) with **raw counts** — not log-normalized. Store counts in `adata.layers["counts"]` if `adata.X` has been normalized.
- **Hardware**: CPU works for <50k cells; GPU (8GB+ VRAM) recommended for larger datasets. Training time: 5–30 minutes on GPU for 100k cells.

```bash
pip install scvi-tools scanpy
# GPU acceleration (recommended for >50k cells)
pip install "scvi-tools[cuda12]"   # or scvi-tools[cuda11]
```

## Quick Start

Minimal scVI batch integration on a built-in example dataset:

```python
import scvi
import scanpy as sc

# Load example data with batch labels
adata = scvi.data.heart_cell_atlas_subsampled()

# Preprocessing: filter genes, select HVGs (subset to save training time)
sc.pp.filter_genes(adata, min_counts=3)
adata.layers["counts"] = adata.X.copy()  # preserve raw counts
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=2000, batch_key="cell_source", subset=True)

# Register data, train, extract
scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="cell_source")
model = scvi.model.SCVI(adata, n_latent=30)
model.train(max_epochs=200, early_stopping=True)

adata.obsm["X_scVI"] = model.get_latent_representation()
sc.pp.neighbors(adata, use_rep="X_scVI")
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.5)
sc.pl.umap(adata, color=["cell_source", "leiden"])
print(f"Latent shape: {adata.obsm['X_scVI'].shape}")
# Latent shape: (14000, 30)
```

## Core API

### 1. Data Registration (setup_anndata)

All models share the same registration pattern. Call `setup_anndata()` on the model class before instantiation to tell scvi-tools where to find counts, batch labels, and covariates.

```python
import scvi

# Minimal: counts in a layer, batch column in obs
scvi.model.SCVI.setup_anndata(
    adata,
    layer="counts",        # Key in adata.layers with raw counts; None = adata.X
    batch_key="batch",     # Column in adata.obs for technical batch
)

# Extended: additional categorical and continuous covariates
scvi.model.SCVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    categorical_covariate_keys=["donor", "protocol"],   # Discrete biological/technical vars
    continuous_covariate_keys=["percent_mito", "log_n_counts"],  # Continuous covariates
)

# Inspect registered summary
print(adata.uns["_scvi"]["summary_stats"])
# {'n_vars': 2000, 'n_cells': 45000, 'n_batch': 6, 'n_extra_categorical_covs': 2, ...}
```

### 2. scVI — Batch Correction and Integration

The core unsupervised model. Learns a batch-corrected latent space and a denoised expression layer. Starting point for any multi-batch scRNA-seq analysis.

```python
import scvi

model = scvi.model.SCVI(
    adata,
    n_latent=30,              # Latent space dimensions; 10–50 typical
    n_layers=2,               # Hidden layers in encoder/decoder; 1–3
    n_hidden=128,             # Neurons per hidden layer; 64–256
    gene_likelihood="zinb",   # "zinb" (zero-inflated NB), "nb", or "poisson"
    dispersion="gene",        # "gene" or "gene-batch" for batch-specific dispersion
)
model.train(max_epochs=200, early_stopping=True)

# Extract results
latent = model.get_latent_representation()        # ndarray (n_cells, n_latent)
normalized = model.get_normalized_expression(
    library_size=1e4, n_samples=25, return_mean=True
)
print(f"Latent: {latent.shape}")
print(f"Denoised expression: {normalized.shape}")
# Latent: (45000, 30)
# Denoised expression: (45000, 2000)

adata.obsm["X_scVI"] = latent
adata.layers["scvi_normalized"] = normalized
```

### 3. scANVI — Semi-Supervised Cell Annotation

Extends scVI with label supervision for cell type transfer learning. Accepts partially labeled data (unannotated cells labeled `"Unknown"`) and predicts cell types for unlabeled cells.

```python
import scvi

# Register with cell type labels; mark unannotated cells as "Unknown"
scvi.model.SCANVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    labels_key="cell_type",           # Column in adata.obs with known labels
    unlabeled_category="Unknown",     # Sentinel value for unannotated cells
)

# Recommended: initialize from a pretrained scVI model
scvi_model = scvi.model.SCVI(adata, n_latent=30)
scvi_model.train(max_epochs=200, early_stopping=True)

model = scvi.model.SCANVI.from_scvi_model(scvi_model, unlabeled_category="Unknown")
model.train(max_epochs=20)  # Short fine-tuning on top of scVI

# Predict cell types
labels_pred = model.predict()              # Hard labels (str per cell)
probs = model.predict(soft=True)           # DataFrame: probability per cell type
confidence = probs.max(axis=1)

adata.obs["scANVI_pred"] = labels_pred
adata.obs["scANVI_confidence"] = confidence
print(f"Median confidence: {confidence.median():.3f}")
print(f"High-confidence cells (>0.7): {(confidence > 0.7).sum()}")
```

### 4. totalVI — CITE-seq RNA + Protein

Joint probabilistic model for CITE-seq data. Denoises both RNA and protein counts and estimates protein foreground probability (signal vs background).

```python
import scvi

# Protein counts must be in adata.obsm (not adata.X or layers)
# adata.obsm["protein_expression"] shape: (n_cells, n_proteins)
scvi.model.TOTALVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    protein_expression_obsm_key="protein_expression",
)

model = scvi.model.TOTALVI(adata, latent_distribution="normal")
model.train(max_epochs=200, early_stopping=True)

# Extract joint latent space (RNA + protein)
latent = model.get_latent_representation()

# Denoised RNA and protein separately
rna_norm, protein_norm = model.get_normalized_expression(
    n_samples=25, return_mean=True
)

# Protein foreground probability (probability that signal > background)
foreground_prob = model.get_protein_foreground_probability(n_samples=25, return_mean=True)
print(f"RNA normalized: {rna_norm.shape}")
print(f"Protein normalized: {protein_norm.shape}")
print(f"Foreground prob: {foreground_prob.shape}")  # (n_cells, n_proteins)

adata.obsm["X_totalVI"] = latent
```

### 5. Differential Expression

Probabilistic DE using the generative model rather than raw counts. Supports composite hypotheses testing whether effect size exceeds a biologically meaningful threshold (`delta`).

```python
# DE between two cell type groups
de_df = model.differential_expression(
    groupby="cell_type",
    group1="CD4 T",         # Numerator group
    group2="CD8 T",         # Denominator group; None = rest of cells
    mode="change",          # "change": composite |LFC| > delta; "vanilla": any LFC
    delta=0.25,             # Minimum |LFC| to be considered DE
    fdr_target=0.05,        # FDR level for calling significance
    all_stats=True,         # Include mean expression per group
)

# Filter significant DE genes
sig = de_df[de_df["is_de_fdr_0.05"] & (de_df["lfc_mean"].abs() > 0.5)]
sig_sorted = sig.sort_values("lfc_mean", ascending=False)
print(f"Total DE genes (FDR<5%, |LFC|>0.5): {len(sig)}")
print(sig_sorted[["lfc_mean", "bayes_factor", "proba_de"]].head(10))
```

```python
# One-vs-rest DE across all clusters (generates a dict of DataFrames)
de_all = {}
for ct in adata.obs["cell_type"].unique():
    de_all[ct] = model.differential_expression(
        idx1=[adata.obs["cell_type"] == ct],   # Boolean index
        mode="change",
        delta=0.25,
    )
    sig_n = de_all[ct]["is_de_fdr_0.05"].sum()
    print(f"  {ct}: {sig_n} DE genes vs rest")
```

### 6. scARCHES — Query-to-Reference Transfer Learning

Adapts a pretrained reference model to a new query dataset without re-training from scratch. Preserves the reference embedding structure and maps query cells into the same latent space.

```python
import scvi

# --- Reference training (done once, save the model) ---
scvi.model.SCVI.setup_anndata(ref_adata, layer="counts", batch_key="batch")
ref_model = scvi.model.SCVI(ref_adata, n_latent=30)
ref_model.train(max_epochs=200, early_stopping=True)
ref_model.save("./reference_model/", overwrite=True)

# Reference annotation (use scANVI for label transfer)
scvi.model.SCANVI.setup_anndata(
    ref_adata, layer="counts", batch_key="batch",
    labels_key="cell_type", unlabeled_category="Unknown",
)
ref_scanvi = scvi.model.SCANVI.from_scvi_model(ref_model, unlabeled_category="Unknown")
ref_scanvi.train(max_epochs=20)
ref_scanvi.save("./reference_scanvi/", overwrite=True)

# --- Query mapping (new dataset, minimal training) ---
ref_scanvi = scvi.model.SCANVI.load("./reference_scanvi/", adata=ref_adata)

# Prepare query: must share gene set with reference
query_adata.obs["cell_type"] = "Unknown"   # All query cells are unlabeled
query_model = scvi.model.SCANVI.load_query_data(query_adata, ref_scanvi)
query_model.train(
    max_epochs=100,
    plan_kwargs={"weight_decay": 0.0},  # Critical: prevents catastrophic forgetting
)

# Map query into reference latent space
query_latent = query_model.get_latent_representation(query_adata)
query_labels = query_model.predict(query_adata)
print(f"Query latent: {query_latent.shape}")
print(f"Query label predictions: {query_labels[:5]}")
```

### 7. Downstream Analysis on Latent Space

After extracting the latent representation, use scanpy for UMAP, clustering, and marker genes — with the batch-corrected embedding as input.

```python
import scanpy as sc

# UMAP and clustering on scVI latent representation
adata.obsm["X_scVI"] = model.get_latent_representation()

sc.pp.neighbors(
    adata,
    use_rep="X_scVI",   # Use scVI latent (not PCA)
    n_neighbors=30,
    n_pcs=None,         # n_pcs ignored when use_rep is set
)
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.5)

# Marker genes using raw counts or normalized expression
# Option A: scanpy Wilcoxon on log-normalized expression
sc.tl.rank_genes_groups(adata, groupby="leiden", method="wilcoxon", n_genes=25)

# Option B: scVI probabilistic DE per cluster (more accurate)
markers = {}
for cluster in adata.obs["leiden"].unique():
    de = model.differential_expression(
        idx1=[adata.obs["leiden"] == cluster],
        mode="change", delta=0.25,
    )
    markers[cluster] = de[de["is_de_fdr_0.05"]].sort_values("lfc_mean", ascending=False)

# Visualization
sc.pl.umap(adata, color=["leiden", "batch", "cell_type"], ncols=3)
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5, groupby="leiden")
```

## Key Concepts

### Unified API Pattern

All scvi-tools models follow the same 4-step workflow:

```
1. ModelClass.setup_anndata(adata, ...)   →  Register layers, batch keys, covariates
2. model = ModelClass(adata, ...)         →  Set architecture hyperparameters
3. model.train(max_epochs=..., ...)       →  Fit model (GPU auto-detected)
4. model.get_*()                          →  Extract results: latent, normalized, DE
```

### Model Selection Guide

| Data | Model | Core Feature | When to Use |
|------|-------|--------------|-------------|
| scRNA-seq | **scVI** | Batch correction, denoising | Default for any multi-batch scRNA-seq |
| scRNA-seq (partial labels) | **scANVI** | Cell type transfer | Have reference labels; want to annotate query |
| CITE-seq (RNA+protein) | **totalVI** | Joint RNA+protein | 10x CITE-seq, REAP-seq |
| Reference → query | **scARCHES** | Transfer learning | Map new data to existing atlas |
| Spatial | **DestVI** | Spot deconvolution | 10x Visium, Slide-seq |
| scRNA-seq QC | **Solo** | Doublet detection | Pre-analysis QC step |

### Raw Counts Requirement

scvi-tools models learn count distributions directly from raw data. Log-normalized input produces incorrect results. Always preserve raw counts before normalization:

```python
# Correct workflow: save counts, then normalize for scanpy steps
adata.layers["counts"] = adata.X.copy()   # Save raw before any transformation
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
# Then: scvi.model.SCVI.setup_anndata(adata, layer="counts", ...)
```

## Common Workflows

### Workflow 1: Multi-Batch scRNA-seq Integration

**Goal**: Integrate multiple scRNA-seq datasets, remove batch effects, identify cell clusters, and find marker genes.

```python
import scvi
import scanpy as sc

# Load and concatenate datasets
adata1 = sc.read_h5ad("dataset1.h5ad")
adata2 = sc.read_h5ad("dataset2.h5ad")
adata3 = sc.read_h5ad("dataset3.h5ad")
adata = sc.concat(
    [adata1, adata2, adata3],
    label="batch",
    keys=["dataset1", "dataset2", "dataset3"],
)

# Preprocessing: preserve raw counts, select HVGs per batch
adata.layers["counts"] = adata.X.copy()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(
    adata,
    n_top_genes=4000,
    batch_key="batch",       # Select HVGs consistently across batches
    subset=True,
)
print(f"HVGs selected: {adata.n_vars}")

# scVI integration
scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = scvi.model.SCVI(adata, n_latent=30, n_layers=2)
model.train(max_epochs=300, early_stopping=True, early_stopping_patience=15)
print(f"Training history: {model.history['elbo_train'].tail()}")

# Batch-corrected analysis
adata.obsm["X_scVI"] = model.get_latent_representation()
adata.layers["scvi_norm"] = model.get_normalized_expression(n_samples=25, return_mean=True)

sc.pp.neighbors(adata, use_rep="X_scVI", n_neighbors=30)
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.5)

# Verify batch mixing (batches should overlap on UMAP)
sc.pl.umap(adata, color=["batch", "leiden"], save="_batch_integration.png")
model.save("./scvi_model/", overwrite=True)
print(f"Clusters: {adata.obs['leiden'].nunique()}")
```

### Workflow 2: CITE-seq totalVI Pipeline

**Goal**: Model CITE-seq RNA + protein data jointly, obtain denoised protein estimates, and generate a joint embedding for annotation.

```python
import scvi
import scanpy as sc
import pandas as pd

# Load CITE-seq AnnData (RNA in X, protein counts in obsm)
adata = sc.read_h5ad("citeseq_data.h5ad")
# Expected structure:
#   adata.X or adata.layers["counts"] : RNA raw counts (n_cells, n_genes)
#   adata.obsm["protein_expression"]   : Protein raw counts (n_cells, n_proteins)

# Preprocessing
adata.layers["counts"] = adata.X.copy()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=4000, batch_key="batch", subset=True)

# totalVI setup and training
scvi.model.TOTALVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    protein_expression_obsm_key="protein_expression",
)

model = scvi.model.TOTALVI(adata, latent_distribution="normal")
model.train(max_epochs=200, early_stopping=True)

# Extract joint embedding and denoised values
adata.obsm["X_totalVI"] = model.get_latent_representation()
rna_norm, protein_norm = model.get_normalized_expression(n_samples=25, return_mean=True)
foreground = model.get_protein_foreground_probability(n_samples=25, return_mean=True)

adata.layers["rna_denoised"] = rna_norm
protein_df = pd.DataFrame(
    protein_norm,
    index=adata.obs_names,
    columns=adata.uns["protein_names"],
)
protein_df.to_csv("denoised_protein_expression.csv")
print(f"Protein foreground: min={foreground.min():.3f}, max={foreground.max():.3f}")

# Joint clustering on RNA + protein latent
sc.pp.neighbors(adata, use_rep="X_totalVI", n_neighbors=30)
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.8)

# Protein-guided annotation (use denoised protein for clean signal)
protein_markers = {"B cell": "CD19", "T cell": "CD3E", "Monocyte": "CD14"}
for cell_type, marker in protein_markers.items():
    if marker in protein_df.columns:
        adata.obs[f"denoised_{marker}"] = protein_df[marker].values
sc.pl.umap(adata, color=["leiden"] + [f"denoised_{m}" for m in protein_markers.values()])
```

## Key Parameters

| Parameter | Model / Function | Default | Range / Options | Effect |
|-----------|-----------------|---------|-----------------|--------|
| `n_latent` | All models | `10` | `10`–`50` | Latent space dimensionality; 20–30 typical for most datasets |
| `n_layers` | All models | `1` | `1`–`3` | Depth of encoder/decoder networks |
| `n_hidden` | All models | `128` | `64`–`256` | Width of each hidden layer |
| `gene_likelihood` | scVI, scANVI | `"zinb"` | `"zinb"`, `"nb"`, `"poisson"` | Count noise distribution; "nb" faster if sparsity is low |
| `max_epochs` | `train()` | `400` | `50`–`1000` | Training iterations (ELBO steps) |
| `early_stopping` | `train()` | `False` | `True`/`False` | Halt when validation ELBO plateaus |
| `early_stopping_patience` | `train()` | `45` | `5`–`100` | Epochs to wait before stopping |
| `batch_size` | `train()` | `128` | `64`–`512` | Mini-batch size; reduce if OOM |
| `lr` | `train()` | `1e-3` | `1e-4`–`1e-2` | Initial learning rate |
| `delta` | `differential_expression()` | `0.25` | `0.1`–`1.0` | Min |LFC| threshold for composite DE |
| `n_samples` | `get_normalized_expression()` | `1` | `1`–`100` | Posterior samples; ≥25 for stable estimates |

## Best Practices

1. **Always store raw counts before normalization**: Run `adata.layers["counts"] = adata.X.copy()` immediately after loading data, before any `normalize_total` or `log1p` call. Passing log-normalized data silently produces incorrect latent spaces.

2. **Select highly variable genes before training**: Use `sc.pp.highly_variable_genes(n_top_genes=2000–4000, batch_key="batch")` to reduce training time and model noise. Including all genes rarely improves results and significantly slows training.

3. **Register all known batch variables**: If data has multiple technical sources (sequencing plate, donor, protocol), include them as `batch_key` or `categorical_covariate_keys`. Unregistered batch effects contaminate the latent space and downstream DE.

4. **Use the scVI → scANVI two-step pipeline**: Initializing scANVI with `from_scvi_model()` after training scVI is faster, more stable, and produces better embeddings than training scANVI from scratch. Always train scVI first when using scANVI.

5. **Save trained models immediately**: `model.save("./model_dir/")` persists the full model. Reloading with `SCVI.load()` is seconds vs. minutes of retraining. Models are typically 10–50 MB.

6. **Use `n_latent=20–30` as starting point**: Values below 10 lose resolution; above 50 tend to overfit without added biological insight. Increase to 50 only for very heterogeneous atlases (>500k cells, many cell types).

7. **Filter low-confidence scANVI predictions**: Cells where `predict(soft=True).max(axis=1) < 0.7` are ambiguous; treat them as `"Unknown"` rather than accepting the argmax label.

## Common Recipes

### Recipe: Doublet Detection with Solo

When to use: Remove doublets before integration or DE to avoid spurious clusters.

```python
import scvi

scvi.model.SCVI.setup_anndata(adata, layer="counts")
vae = scvi.model.SCVI(adata, n_latent=20)
vae.train(max_epochs=100)

solo = scvi.external.SOLO.from_scvi_model(vae)
solo.train(max_epochs=200)
doublet_preds = solo.predict()   # DataFrame: {"singlet": prob, "doublet": prob}
adata.obs["doublet_score"] = doublet_preds["doublet"].values
adata.obs["is_doublet"] = doublet_preds["prediction"].values

n_doublets = (adata.obs["is_doublet"] == "doublet").sum()
print(f"Detected {n_doublets} doublets ({n_doublets / adata.n_obs:.1%})")
adata = adata[adata.obs["is_doublet"] == "singlet"].copy()
print(f"Cells after doublet removal: {adata.n_obs}")
```

### Recipe: Spatial Deconvolution with DestVI

When to use: Estimate cell type proportions in spatial transcriptomics spots using a matched scRNA-seq reference.

```python
import scvi

# Step 1: Train CondSCVI on reference single-cell data
scvi.model.CondSCVI.setup_anndata(sc_adata, layer="counts", labels_key="cell_type")
sc_model = scvi.model.CondSCVI(sc_adata, weight_obs=False)
sc_model.train(max_epochs=200)

# Step 2: Deconvolve spatial spots
scvi.model.DestVI.setup_anndata(st_adata, layer="counts")
st_model = scvi.model.DestVI.from_rna_model(st_adata, sc_model)
st_model.train(max_epochs=2500)

proportions = st_model.get_proportions()  # DataFrame (n_spots, n_cell_types)
st_adata.obsm["cell_type_proportions"] = proportions.values
print(f"Proportions per spot: {proportions.shape}")
print(proportions.head())
```

### Recipe: Extract Denoised Expression for Imputation

When to use: Obtain smooth, denoised expression values for visualization or downstream machine learning when raw sparse counts are too noisy.

```python
import scvi

scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = scvi.model.SCVI(adata, n_latent=30)
model.train(max_epochs=200, early_stopping=True)

# n_samples >= 25 gives stable posterior mean; increase to 100 for publication
denoised = model.get_normalized_expression(
    n_samples=50,
    library_size="latent",  # "latent" uses learned library size; int for fixed normalization
    return_mean=True,
)
adata.layers["denoised"] = denoised
print(f"Denoised layer added: {denoised.shape}")
# Use adata.layers["denoised"] for heatmaps, pseudotime, or ML features
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: adata must contain raw counts` | Log-normalized data passed instead of raw counts | Save raw before normalizing: `adata.layers["counts"] = adata.X.copy()` then `setup_anndata(layer="counts")` |
| Training loss oscillates without decreasing | Learning rate too high or very heterogeneous data | Try `lr=1e-4`; check that `adata.X` and the registered layer are not sparse with negatives |
| CUDA out of memory | Dataset too large for GPU VRAM | Reduce `batch_size=64`, `n_hidden=64`; subset to fewer HVGs; use CPU for small datasets |
| Poor batch integration (batches separate on UMAP) | Batch key not registered, or too few epochs | Verify `batch_key` column exists in `adata.obs`; increase `max_epochs`; add `early_stopping=True` |
| scANVI predicts same label for all cells | Too few labeled cells per type or learning rate issue | Need ≥50 labeled cells per type; use `from_scvi_model()` workflow; check `unlabeled_category` matches exactly |
| `load()` fails with `KeyError` or shape mismatch | AnnData `var_names` differ from training data | Ensure query `adata.var_names` exactly matches training data; do not subset genes after training |
| Slow training on CPU for large datasets | Large dataset without GPU acceleration | Install `scvi-tools[cuda12]`; pass `accelerator="gpu"` to `train()`; or subsample to 50k cells for prototyping |
| `scvi.model.SCANVI.load_query_data` shape error | Query and reference have different gene sets | Align genes: `query_adata = query_adata[:, ref_adata.var_names]` before calling `load_query_data` |

## Related Skills

- **scanpy-scrna-seq** — standard scRNA-seq QC, clustering, marker genes; use scVI latent as input to `sc.pp.neighbors(use_rep="X_scVI")`
- **anndata-data-structure** — create, subset, concatenate, and persist AnnData objects required by scvi-tools
- **harmony-batch-correction** — fast linear batch correction alternative; use when deep learning overhead is not justified
- **cellxgene-census** — download reference atlases for scANVI transfer learning and scARCHES query-to-reference mapping
- **muon-multiomics-singlecell** — multi-modal single-cell analysis with MuData; complement to totalVI for Multiome workflows

## References

- [scvi-tools documentation](https://docs.scvi-tools.org/) — official API reference, tutorials, and model guides
- [scvi-tools GitHub](https://github.com/scverse/scvi-tools) — source code, issue tracker, and changelog
- Lopez et al. (2018) "Deep generative modeling for single-cell transcriptomics" — [Nature Methods 15:1053–1058](https://doi.org/10.1038/s41592-018-0229-2) — original scVI paper
- Xu et al. (2021) "Probabilistic harmonization and annotation of single-cell transcriptomics data with deep generative models" — [Molecular Systems Biology 17:e9620](https://doi.org/10.15252/msb.20209620) — scANVI paper
- Gayoso et al. (2022) "A Python library for probabilistic analysis of single-cell omics data" — [Nature Biotechnology 40:163–166](https://doi.org/10.1038/s41587-021-01206-w) — scvi-tools library paper
