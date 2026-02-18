---
name: scvi-tools-single-cell
description: "Deep generative models for single-cell omics. Probabilistic batch correction (scVI), semi-supervised annotation (scANVI), multi-modal integration (totalVI, MultiVI), differential expression with uncertainty. Unified setup→train→extract API on AnnData. For standard scanpy pipelines use scanpy-scrna-seq; for classical ML use scikit-learn."
license: BSD-3-Clause
---

# scvi-tools — Single-Cell Deep Generative Models

## Overview

scvi-tools is a probabilistic modeling framework for single-cell genomics built on PyTorch. It provides deep generative models (VAEs) with a unified API: register data → create model → train → extract results. Models handle batch correction, uncertainty quantification, and multi-modal integration automatically. All models operate on raw count data in AnnData format.

## When to Use

- Integrating multiple scRNA-seq batches/studies with probabilistic batch correction
- Performing differential expression with uncertainty quantification (not just fold-change)
- Annotating cell types via transfer learning from labeled references (scANVI)
- Jointly analyzing CITE-seq protein + RNA data (totalVI)
- Integrating paired and unpaired multi-omic data (MultiVI: RNA + ATAC)
- Deconvolving spatial transcriptomics spots into cell types (DestVI)
- Detecting doublets in scRNA-seq data (Solo)
- For **standard clustering/visualization** without deep learning, use scanpy instead
- For **Bayesian statistical models** (not single-cell specific), use pymc instead

## Prerequisites

```bash
pip install scvi-tools scanpy
# GPU acceleration (recommended for >50k cells)
pip install scvi-tools[cuda12]  # or scvi-tools[cuda11]
```

**Hardware**: CPU works for <50k cells. GPU recommended for larger datasets (8GB+ VRAM for typical analyses). Training time: ~5-30 min on GPU for 100k cells.

**Data format**: AnnData (`.h5ad`). All models require **raw counts** — not log-normalized data. Store raw counts in `adata.layers["counts"]` if `adata.X` has been normalized.

## Quick Start

```python
import scvi
import scanpy as sc

adata = scvi.data.heart_cell_atlas_subsampled()
sc.pp.filter_genes(adata, min_counts=3)
sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)

scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="cell_source")
model = scvi.model.SCVI(adata)
model.train(max_epochs=100)

adata.obsm["X_scVI"] = model.get_latent_representation()
sc.pp.neighbors(adata, use_rep="X_scVI")
sc.tl.umap(adata)
sc.tl.leiden(adata)
```

## Core API

### 1. Data Registration (setup_anndata)

All models share the same data registration pattern. This tells the model where to find counts, batches, and covariates.

```python
import scvi

# Basic: counts + batch
scvi.model.SCVI.setup_anndata(
    adata,
    layer="counts",           # Layer with raw counts (None = adata.X)
    batch_key="batch",        # Technical batch column in adata.obs
)

# Full: counts + batch + covariates
scvi.model.SCVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    categorical_covariate_keys=["donor", "condition"],   # Discrete covariates
    continuous_covariate_keys=["percent_mito", "n_counts"],  # Continuous covariates
)

# Check registration summary
print(adata.uns["_scvi"]["summary_stats"])
# {'n_vars': 2000, 'n_cells': 14000, 'n_batch': 4, ...}
```

### 2. scVI — Batch Correction and Integration

Core model for unsupervised dimensionality reduction and batch correction.

```python
import scvi

# Create and train
model = scvi.model.SCVI(
    adata,
    n_latent=30,          # Latent space dimensions (10-50)
    n_layers=2,           # Hidden layers (1-3)
    n_hidden=128,         # Nodes per layer (64-256)
    gene_likelihood="zinb",  # "zinb", "nb", or "poisson"
)
model.train(max_epochs=200, early_stopping=True)

# Extract results
latent = model.get_latent_representation()         # (n_cells, n_latent)
normalized = model.get_normalized_expression(library_size=1e4)  # Denoised expression
print(f"Latent shape: {latent.shape}")

# Store in AnnData
adata.obsm["X_scVI"] = latent
adata.layers["scvi_normalized"] = normalized
```

### 3. scANVI — Semi-Supervised Cell Annotation

Transfer cell type labels from annotated reference to unannotated query data.

```python
import scvi

# Register with labels (unknown cells marked as "Unknown")
scvi.model.SCANVI.setup_anndata(
    adata, layer="counts", batch_key="batch",
    labels_key="cell_type", unlabeled_category="Unknown",
)

# Train from pre-trained scVI (recommended)
scvi_model = scvi.model.SCVI(adata)
scvi_model.train(max_epochs=100)
model = scvi.model.SCANVI.from_scvi_model(scvi_model, unlabeled_category="Unknown")
model.train(max_epochs=20)

# Predict cell types
predictions = model.predict()            # Predicted labels
probs = model.predict(soft=True)          # Probability per cell type
print(f"Predictions: {predictions[:5]}")
print(f"Max confidence: {probs.max(axis=1).mean():.3f}")

adata.obs["scANVI_prediction"] = predictions
```

### 4. totalVI — CITE-seq (RNA + Protein)

Joint modeling of RNA and surface protein data from CITE-seq experiments.

```python
import scvi

# Register RNA + protein data
scvi.model.TOTALVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    protein_expression_obsm_key="protein_expression",  # Protein counts in obsm
)

model = scvi.model.TOTALVI(adata)
model.train(max_epochs=200)

# Extract joint latent space
latent = model.get_latent_representation()
# Denoised RNA and protein separately
rna_norm, protein_norm = model.get_normalized_expression(
    n_samples=25, return_mean=True
)
print(f"RNA normalized shape: {rna_norm.shape}")
print(f"Protein normalized shape: {protein_norm.shape}")
```

### 5. Differential Expression

Probabilistic DE with uncertainty — uses the generative model, not just raw counts.

```python
# Differential expression between cell types
de = model.differential_expression(
    groupby="cell_type",
    group1="CD4 T",
    group2="CD8 T",
    mode="change",      # "vanilla" or "change" (composite hypothesis)
    delta=0.25,         # Minimum log-fold-change threshold
)

# Filter significant genes
sig = de[(de["is_de_fdr_0.05"]) & (de["lfc_mean"].abs() > 0.5)]
print(f"Significant DE genes: {len(sig)}")
print(sig.sort_values("lfc_mean", ascending=False).head())
```

### 6. Model Persistence

Save and load trained models to avoid retraining.

```python
# Save
model.save("./scvi_model/", overwrite=True)

# Load (requires matching AnnData)
loaded_model = scvi.model.SCVI.load("./scvi_model/", adata=adata)

# Query-to-reference mapping (scANVI)
# Train on reference, then map query
ref_model = scvi.model.SCANVI.load("./scanvi_ref/", adata=ref_adata)
query_model = scvi.model.SCANVI.load_query_data(query_adata, ref_model)
query_model.train(max_epochs=100, plan_kwargs={"weight_decay": 0.0})
```

## Key Concepts

### Model Selection Guide

| Data Type | Model | Key Feature | Use When |
|-----------|-------|-------------|----------|
| scRNA-seq | **scVI** | Batch correction, denoising | Default starting point for any scRNA-seq |
| scRNA-seq (labeled) | **scANVI** | Cell type transfer learning | Have partial labels, want to annotate rest |
| CITE-seq | **totalVI** | Joint RNA+protein | CITE-seq or REAP-seq data |
| RNA + ATAC | **MultiVI** | Multi-omic integration | Multiome, paired or unpaired |
| Spatial | **DestVI** | Deconvolution | 10x Visium, Slide-seq |
| scRNA-seq | **Solo** | Doublet detection | QC preprocessing step |
| scRNA-seq | **CellAssign** | Marker-based annotation | Have known marker gene lists |

### Unified API Pattern

All scvi-tools models follow the same 4-step workflow:

```
1. setup_anndata(adata, ...)  →  Register data layers and covariates
2. Model(adata, ...)          →  Create model with architecture hyperparameters
3. model.train(...)           →  Fit model (GPU auto-detected)
4. model.get_*()              →  Extract latent representations, normalized values, DE results
```

### Raw Counts Requirement

scvi-tools models learn the data distribution from raw counts. Providing log-normalized data will produce incorrect results. Always:

```python
# Store raw counts before normalization
adata.layers["counts"] = adata.X.copy()
# Then normalize for scanpy
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
# Use layer="counts" in setup_anndata
```

## Common Workflows

### Workflow: Multi-Batch Integration

```python
import scvi
import scanpy as sc

# Load and concatenate multiple datasets
adata1 = sc.read_h5ad("batch1.h5ad")
adata2 = sc.read_h5ad("batch2.h5ad")
adata = sc.concat([adata1, adata2], label="batch", keys=["batch1", "batch2"])

# Preprocessing
adata.layers["counts"] = adata.X.copy()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=4000, batch_key="batch")
adata = adata[:, adata.var["highly_variable"]]

# scVI integration
scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = scvi.model.SCVI(adata, n_latent=30)
model.train(max_epochs=200, early_stopping=True)

# Batch-corrected downstream analysis
adata.obsm["X_scVI"] = model.get_latent_representation()
sc.pp.neighbors(adata, use_rep="X_scVI")
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.5)
sc.pl.umap(adata, color=["batch", "leiden"])
```

### Workflow: Reference-Based Cell Annotation (scANVI)

1. Train scVI on reference dataset with cell type labels
2. Initialize scANVI from scVI with `SCANVI.from_scvi_model()`
3. Train scANVI (short: 20 epochs)
4. Load query data with `SCANVI.load_query_data()`
5. Fine-tune on query (100 epochs, weight_decay=0)
6. `predict()` for labels, `predict(soft=True)` for probabilities
7. Filter low-confidence predictions (max probability < 0.7)

## Key Parameters

| Parameter | Function/Model | Default | Range | Effect |
|-----------|---------------|---------|-------|--------|
| `n_latent` | All models | 10 | 10–50 | Latent space dimensionality |
| `n_layers` | All models | 1 | 1–3 | Number of hidden layers |
| `n_hidden` | All models | 128 | 64–256 | Nodes per hidden layer |
| `gene_likelihood` | scVI, scANVI | `"zinb"` | `"zinb"`, `"nb"`, `"poisson"` | Count distribution |
| `max_epochs` | `train()` | 400 | 50–1000 | Training iterations |
| `early_stopping` | `train()` | `False` | `True`/`False` | Stop when validation loss plateaus |
| `batch_size` | `train()` | 128 | 64–512 | Mini-batch size |
| `lr` | `train()` | 1e-3 | 1e-4–1e-2 | Learning rate |
| `delta` | `differential_expression()` | 0.25 | 0.1–1.0 | Minimum LFC for DE |
| `n_samples` | `get_normalized_expression()` | 1 | 1–100 | Posterior samples for denoising |

## Best Practices

1. **Always use raw counts**: Store pre-normalization counts in `adata.layers["counts"]` and specify `layer="counts"` in setup.

2. **Feature selection before training**: Use `sc.pp.highly_variable_genes(n_top_genes=2000-4000)` — reduces training time and improves model focus.

3. **Anti-pattern — training without batch_key**: If data has known batches, always register them. Unregistered batch effects contaminate the latent space.

4. **Save models after training**: `model.save()` avoids expensive retraining. Models are small (< 100 MB) compared to training cost.

5. **Use scVI → scANVI pipeline**: Train scVI first, then initialize scANVI with `from_scvi_model()` — faster and more stable than training scANVI from scratch.

6. **Anti-pattern — using too many latent dimensions**: `n_latent=10-30` is sufficient for most datasets. Higher values overfit without improving biological signal.

7. **GPU for large datasets**: For >100k cells, GPU training is 10-50x faster. Set `accelerator="gpu"` in `train()`.

## Common Recipes

### Recipe: Doublet Detection with Solo

```python
import scvi

scvi.model.SCVI.setup_anndata(adata, layer="counts")
vae = scvi.model.SCVI(adata)
vae.train()

solo = scvi.external.SOLO.from_scvi_model(vae)
solo.train()
doublet_preds = solo.predict()
adata.obs["is_doublet"] = doublet_preds["prediction"]
adata = adata[adata.obs["is_doublet"] == "singlet"]
print(f"Cells after doublet removal: {adata.n_obs}")
```

### Recipe: Spatial Deconvolution with DestVI

```python
import scvi

# Train on reference scRNA-seq
scvi.model.CondSCVI.setup_anndata(sc_adata, layer="counts", labels_key="cell_type")
sc_model = scvi.model.CondSCVI(sc_adata)
sc_model.train()

# Deconvolve spatial data
scvi.model.DestVI.setup_anndata(st_adata, layer="counts")
st_model = scvi.model.DestVI.from_rna_model(st_adata, sc_model)
st_model.train(max_epochs=2500)
proportions = st_model.get_proportions()
print(f"Cell type proportions per spot: {proportions.shape}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: adata must contain raw counts` | Log-normalized data passed | Store raw counts: `adata.layers["counts"] = adata.X.copy()` before normalizing |
| Training loss not decreasing | Learning rate too high or data issue | Reduce `lr=1e-4`; check for empty cells/genes; verify `layer=` points to counts |
| CUDA out of memory | Dataset too large for GPU VRAM | Reduce `batch_size=64`; reduce `n_hidden=64`; subset to HVGs |
| Poor batch integration | Batch key not registered | Verify `batch_key` column exists in `adata.obs`; re-run `setup_anndata` |
| scANVI predictions all same type | Too few labeled cells or too few epochs | Need >50 labeled cells per type; increase `max_epochs` for scANVI fine-tuning |
| `load()` fails with shape mismatch | AnnData genes changed since training | Ensure `adata.var_names` matches training data exactly |
| Slow training on CPU | Large dataset without GPU | Install `scvi-tools[cuda12]`; use `accelerator="gpu"` in `train()` |

## Related Skills

- **scanpy-scrna-seq** — standard scRNA-seq analysis (QC, clustering, markers); use scVI outputs as input to scanpy
- **anndata-annotated-data** — create, manipulate, and concatenate AnnData objects used by scvi-tools
- **cellxgene-census** — download reference datasets for scANVI transfer learning
- **pymc-bayesian-modeling** — general Bayesian modeling; scvi-tools is specialized for single-cell

## References

- [scvi-tools documentation](https://docs.scvi-tools.org/) — official API and tutorials
- Lopez et al. (2018) "Deep generative modeling for single-cell transcriptomics" — [Nature Methods](https://doi.org/10.1038/s41592-018-0229-2)
- Xu et al. (2021) "Probabilistic harmonization and annotation of single-cell transcriptomics data with deep generative models" — [Molecular Systems Biology](https://doi.org/10.15252/msb.20209620)
- Gayoso et al. (2022) "A Python library for probabilistic analysis of single-cell omics data" — [Nature Biotechnology](https://doi.org/10.1038/s41587-021-01206-w)
