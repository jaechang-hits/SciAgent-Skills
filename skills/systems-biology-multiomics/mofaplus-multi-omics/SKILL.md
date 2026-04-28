---
name: "mofaplus-multi-omics"
description: "Multi-Omics Factor Analysis v2 (MOFA+) with mofapy2. Jointly decompose omics layers (scRNA, ATAC, proteomics, methylation) into latent factors capturing major variation. Multi-group designs. AnnData views → MOFA object → train → variance explained → correlate factors with metadata → visualize/cluster → enrich top loadings."
license: "LGPL-3.0"
---

# MOFA+ Multi-Omics Factor Analysis

## Overview

MOFA+ (Multi-Omics Factor Analysis v2) is an unsupervised statistical framework that jointly decomposes multiple omics datasets into a small set of latent factors. Each factor captures an independent source of variation (e.g., cell cycle, a disease phenotype, a technical batch) and is associated with feature weights (loadings) that reveal which genes, peaks, or proteins drive it. The Python package `mofapy2` produces an HDF5 model file compatible with downstream analysis in both Python and R. MOFA+ extends the original MOFA to support multi-group settings where samples belong to distinct cohorts or conditions.

## When to Use

- Integrating two or more omics layers from the same set of cells or samples (e.g., scRNA-seq + scATAC-seq, RNA + proteomics, methylation + RNA)
- Identifying shared and view-specific sources of variation across omics modalities without supervised labels
- Comparing how latent factors differ between patient groups, treatment conditions, or time points in a multi-group analysis
- Reducing multi-omics dimensionality before clustering, trajectory inference, or survival modeling
- Discovering which genomic features (genes, peaks, proteins) drive each factor via sparse loadings
- Annotating latent factors by correlating factor scores with sample metadata (age, stage, treatment response)
- Use **scVI / MultiVI** (scverse) instead when you need deep generative batch correction across modalities with explicit latent space inference and VAE architecture
- Use **LIGER** instead when your primary goal is integrating datasets across technologies (e.g., snRNA-seq + snATAC-seq) with shared and dataset-specific factors via iNMF

## Prerequisites

- **Python packages**: `mofapy2>=0.7`, `anndata>=0.10`, `numpy>=1.24`, `pandas>=2.0`, `scipy>=1.11`, `matplotlib>=3.7`, `seaborn>=0.13`, `muon` (optional, for MuData integration)
- **Data requirements**: One AnnData object per omics view (cells/samples x features). All views must share the same obs (cell/sample) index. Missing samples per group are supported.
- **Environment**: Python 3.9+; trained model is saved as HDF5 and can be analyzed in R via the `MOFA2` Bioconductor package

```bash
pip install mofapy2 anndata muon matplotlib seaborn
```

## Quick Start

```python
import numpy as np
import pandas as pd
import anndata as ad
from mofapy2.run.entry_point import entry_point

# Simulate two omics views, 200 cells, 500 RNA genes, 300 ATAC peaks
np.random.seed(42)
n_cells, n_rna, n_atac = 200, 500, 300

adata_rna  = ad.AnnData(np.abs(np.random.randn(n_cells, n_rna)),
                         obs=pd.DataFrame(index=[f"cell_{i}" for i in range(n_cells)]))
adata_atac = ad.AnnData(np.abs(np.random.randn(n_cells, n_atac)),
                         obs=adata_rna.obs.copy())

ent = entry_point()
ent.set_data_options(scale_groups=False, scale_views=True)
ent.set_data_matrix([[adata_rna.X, adata_atac.X]],
                    likelihoods=["gaussian", "gaussian"],
                    views_names=["RNA", "ATAC"],
                    groups_names=["all_cells"],
                    samples_names=[list(adata_rna.obs_names)])
ent.set_model_options(factors=10)
ent.set_train_options(iter=500, convergence_mode="fast", seed=42)
ent.build()
ent.run()
ent.save("mofa_model.hdf5")
print("Model saved to mofa_model.hdf5")
```

## Workflow

### Step 1: Load and Prepare Multi-Omics Data

Each omics layer is represented as an AnnData object. Align cell indices across modalities, log-normalize RNA counts, and binarize or normalize ATAC/methylation data as appropriate.

```python
import numpy as np
import pandas as pd
import anndata as ad
import scipy.sparse as sp

# --- RNA-seq: 200 cells x 2000 highly variable genes ---
np.random.seed(42)
n_cells = 200
cell_ids = [f"cell_{i:03d}" for i in range(n_cells)]

# Simulate log-normalized counts (in practice: load from h5ad after Scanpy preprocessing)
rna_counts = np.abs(np.random.randn(n_cells, 2000) * 2)
adata_rna = ad.AnnData(
    X=rna_counts,
    obs=pd.DataFrame(
        {"condition": ["A"] * 100 + ["B"] * 100,
         "patient": [f"P{i % 10}" for i in range(n_cells)]},
        index=cell_ids
    ),
    var=pd.DataFrame(index=[f"Gene_{i}" for i in range(2000)])
)

# --- ATAC-seq: same cells x 1000 peaks ---
atac_matrix = (np.random.rand(n_cells, 1000) > 0.8).astype(float)
adata_atac = ad.AnnData(
    X=atac_matrix,
    obs=adata_rna.obs.copy(),
    var=pd.DataFrame(index=[f"Peak_{i}" for i in range(1000)])
)

# Confirm alignment
assert list(adata_rna.obs_names) == list(adata_atac.obs_names), "Cell indices must match"
print(f"RNA: {adata_rna.shape}, ATAC: {adata_atac.shape}")
print(f"Conditions: {adata_rna.obs['condition'].value_counts().to_dict()}")
```

### Step 2: Create the MOFA+ Model Object

Instantiate the `entry_point` and register all data views. Views are provided as a list-of-lists: `data[groups][views]`. Assign meaningful view and group names for interpretability.

```python
from mofapy2.run.entry_point import entry_point

ent = entry_point()

# Configure data options before setting data
ent.set_data_options(
    scale_groups=False,   # Do not rescale variance between groups
    scale_views=True,     # Rescale each view to unit variance (recommended when views differ in scale)
)

# Provide data as list-of-lists: [groups][views]
# Single group → wrap each view in a list
ent.set_data_matrix(
    data=[[adata_rna.X, adata_atac.X]],       # outer list = groups, inner = views
    likelihoods=["gaussian", "bernoulli"],      # gaussian for continuous, bernoulli for binary ATAC
    views_names=["RNA", "ATAC"],
    groups_names=["all_cells"],
    samples_names=[list(adata_rna.obs_names)]  # one list per group
)

print("Data registered. Views: RNA, ATAC | Groups: all_cells")
```

### Step 3: Set Model and Training Options

Configure the number of factors and training hyperparameters. More factors capture finer variation but increase computation and risk overfitting; `convergence_mode="medium"` balances speed and accuracy.

```python
# Model options
ent.set_model_options(
    factors=15,          # Number of latent factors (start with 15; prune inactive ones automatically)
    spikeslab_weights=True,  # Sparse weight prior (ARD+spike-slab); recommended for feature selection
    ard_factors=True,    # Automatic relevance determination per factor per view
    ard_weights=True,    # ARD per feature weight; enables pruning of irrelevant features
)

# Training options
ent.set_train_options(
    iter=1000,                     # Maximum EM iterations
    convergence_mode="medium",     # "fast" (<1000 iter), "medium" (default), "slow" (>5000 iter)
    startELBO=1,                   # Start computing ELBO from iteration 1
    freqELBO=5,                    # Compute ELBO every 5 iterations
    dropR2=0.01,                   # Drop factors explaining < 1% variance (set to None to disable)
    seed=42,
    verbose=False
)

print("Model and training options set")
```

### Step 4: Build and Train the Model

Build the internal data structures, then run variational inference. Training produces a fitted model where each factor's weights and scores are optimized to maximize the evidence lower bound (ELBO).

```python
# Build internal model structure
ent.build()

# Run training (EM algorithm with variational Bayes updates)
ent.run()

# Save trained model to HDF5 — required for downstream analysis
output_path = "mofa_model.hdf5"
ent.save(output_path, overwrite=True)
print(f"Model trained and saved to {output_path}")
```

### Step 5: Load Trained Model and Inspect Variance Explained

Load the HDF5 model and inspect how much variance each factor explains per view. Factors explaining less than ~1-2% total variance are typically noise.

```python
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_mofa_r2(model_path):
    """Extract variance explained (R2) per factor per view from MOFA+ HDF5."""
    with h5py.File(model_path, "r") as f:
        r2 = f["variance_explained"]["r2_per_factor"]
        views = [v.decode() for v in f["views"]["views"][:]]
        groups = [g.decode() for g in f["groups"]["groups"][:]]

        # r2_per_factor: shape (n_groups, n_views, n_factors)
        r2_array = np.stack([r2[g][:] for g in groups], axis=0)  # (groups, views, factors)

    # Average across groups; shape → (n_views, n_factors)
    r2_mean = r2_array.mean(axis=0)
    n_factors = r2_mean.shape[1]
    df = pd.DataFrame(r2_mean * 100,
                      index=views,
                      columns=[f"Factor{i+1}" for i in range(n_factors)])
    return df

r2_df = load_mofa_r2("mofa_model.hdf5")
print("Variance explained (%) per factor per view:")
print(r2_df.round(2))

# Heatmap of variance explained
fig, ax = plt.subplots(figsize=(max(8, r2_df.shape[1] * 0.6), 3))
sns.heatmap(r2_df, annot=True, fmt=".1f", cmap="YlOrRd",
            linewidths=0.5, ax=ax, vmin=0)
ax.set_title("MOFA+ Variance Explained (%) per Factor per View")
ax.set_xlabel("Factor")
ax.set_ylabel("Omics View")
plt.tight_layout()
plt.savefig("mofa_variance_explained.png", dpi=200)
print("Saved mofa_variance_explained.png")
```

### Step 6: Extract Factor Scores and Correlate with Metadata

Factor scores (Z matrix) are the per-sample coordinates in factor space. Correlate scores with continuous or categorical metadata to biologically annotate each factor.

```python
import scipy.stats as stats

def load_mofa_factors(model_path):
    """Load factor scores (Z) from MOFA+ HDF5. Returns DataFrame (samples x factors)."""
    with h5py.File(model_path, "r") as f:
        groups = [g.decode() for g in f["groups"]["groups"][:]]
        factors_list = []
        for g in groups:
            z = f["expectations"]["Z"][g][:]   # shape: (n_factors, n_samples)
            samples = [s.decode() for s in f["samples"][g][:]]
            n_factors = z.shape[0]
            df = pd.DataFrame(z.T, index=samples,
                              columns=[f"Factor{i+1}" for i in range(n_factors)])
            factors_list.append(df)
    return pd.concat(factors_list, axis=0)

factors_df = load_mofa_factors("mofa_model.hdf5")
print(f"Factor scores: {factors_df.shape} (cells x factors)")

# Merge with metadata
meta = adata_rna.obs[["condition", "patient"]].copy()
factors_meta = factors_df.join(meta)

# Point-biserial correlation: factor score vs binary metadata
factor_cols = [c for c in factors_meta.columns if c.startswith("Factor")]
print("\nFactor–Condition correlation (eta-squared approximation):")
for fc in factor_cols[:5]:
    groups_vals = [factors_meta.loc[factors_meta["condition"] == g, fc].values
                   for g in factors_meta["condition"].unique()]
    stat, pval = stats.f_oneway(*groups_vals)
    print(f"  {fc}: F={stat:.2f}, p={pval:.3f}")
```

### Step 7: Visualize Factors — Scatter Plots and Feature Heatmaps

Plot factor score scatter plots colored by metadata, and heatmaps of the top-weighted features (loadings) per factor to understand what each factor captures.

```python
def load_mofa_weights(model_path, view_name):
    """Load feature weights (W) for a specific view. Returns DataFrame (features x factors)."""
    with h5py.File(model_path, "r") as f:
        views = [v.decode() for v in f["views"]["views"][:]]
        view_idx = views.index(view_name)
        # Weights stored per view as (n_factors, n_features)
        w = f["expectations"]["W"][view_name][:]
        features = [ft.decode() for ft in f["features"][view_name][:]]
        n_factors = w.shape[0]
        df = pd.DataFrame(w.T, index=features,
                          columns=[f"Factor{i+1}" for i in range(n_factors)])
    return df

# --- Factor scatter plot ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax, (fx, fy) in zip(axes, [("Factor1", "Factor2"), ("Factor1", "Factor3")]):
    for cond, grp in factors_meta.groupby("condition"):
        ax.scatter(grp[fx], grp[fy], label=cond, alpha=0.6, s=20)
    ax.set_xlabel(fx)
    ax.set_ylabel(fy)
    ax.legend(title="Condition")
    ax.set_title(f"{fx} vs {fy}")

plt.tight_layout()
plt.savefig("mofa_factor_scatter.png", dpi=200)
print("Saved mofa_factor_scatter.png")

# --- Top-loading heatmap for RNA view ---
weights_rna = load_mofa_weights("mofa_model.hdf5", "RNA")
top_n = 20
top_features = []
for fc in [f"Factor{i+1}" for i in range(min(5, weights_rna.shape[1]))]:
    top_pos = weights_rna[fc].nlargest(top_n // 2).index.tolist()
    top_neg = weights_rna[fc].nsmallest(top_n // 2).index.tolist()
    top_features.extend(top_pos + top_neg)
top_features = list(dict.fromkeys(top_features))  # unique, preserve order

fig, ax = plt.subplots(figsize=(8, max(6, len(top_features) * 0.3)))
sns.heatmap(weights_rna.loc[top_features, [f"Factor{i+1}" for i in range(min(5, weights_rna.shape[1]))]],
            cmap="RdBu_r", center=0, ax=ax, yticklabels=True)
ax.set_title("Top RNA Feature Weights per Factor")
plt.tight_layout()
plt.savefig("mofa_rna_weights_heatmap.png", dpi=200)
print("Saved mofa_rna_weights_heatmap.png")
```

### Step 8: Downstream — Cluster Cells by Factor Scores and Enrichment

Use factor scores as a low-dimensional embedding for clustering, and extract top-weighted genes per factor for pathway enrichment.

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

# --- Cluster cells using factor scores ---
factor_cols = [c for c in factors_df.columns if c.startswith("Factor")]
X_factors = StandardScaler().fit_transform(factors_df[factor_cols].values)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    cluster_labels = kmeans.fit_predict(X_factors)

factors_df["mofa_cluster"] = cluster_labels.astype(str)
print(f"K-means clusters (k=4):\n{pd.Series(cluster_labels).value_counts().sort_index()}")

# --- Extract top-weighted genes per factor for enrichment input ---
weights_rna = load_mofa_weights("mofa_model.hdf5", "RNA")

enrichment_inputs = {}
for fc in [f"Factor{i+1}" for i in range(min(5, weights_rna.shape[1]))]:
    # Positive weights: top activating genes; negative: top repressing genes
    top_pos = weights_rna[fc].nlargest(100).index.tolist()
    top_neg = weights_rna[fc].nsmallest(100).index.tolist()
    enrichment_inputs[f"{fc}_positive"] = top_pos
    enrichment_inputs[f"{fc}_negative"] = top_neg

# Save gene lists for external enrichment (e.g., gseapy Enrichr)
for name, genes in list(enrichment_inputs.items())[:2]:
    print(f"\n{name} — top 10: {genes[:10]}")

# Example: run ORA with gseapy (install separately)
# import gseapy
# enr = gseapy.enrichr(gene_list=enrichment_inputs["Factor1_positive"],
#                       gene_sets="GO_Biological_Process_2023",
#                       organism="human", outdir=None)
# print(enr.results.head(5)[["Term", "Adjusted P-value", "Genes"]])

factors_df.to_csv("mofa_factor_scores.csv")
print("\nFactor scores with cluster labels saved to mofa_factor_scores.csv")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `factors` | `15` | `5`–`50` | Number of latent factors to infer; inactive ones pruned by ARD |
| `likelihoods` | (required) | `"gaussian"`, `"bernoulli"`, `"poisson"` | Per-view likelihood; gaussian for normalized continuous, bernoulli for binary ATAC, poisson for raw counts |
| `scale_views` | `True` | `True`/`False` | Rescale each view to unit variance; recommended when views differ in scale or unit |
| `scale_groups` | `False` | `True`/`False` | Rescale variance across groups; set `True` if groups have very different total variances |
| `spikeslab_weights` | `True` | `True`/`False` | Spike-and-slab sparsity prior on weights; enables feature selection via near-zero weights |
| `ard_factors` | `True` | `True`/`False` | Automatic relevance determination per factor per view; prunes factors not used in a view |
| `iter` | `1000` | `200`–`5000` | Maximum EM iterations; convergence usually reached in 200–800 |
| `convergence_mode` | `"medium"` | `"fast"`, `"medium"`, `"slow"` | ELBO convergence tolerance: fast = 1e-4, medium = 1e-6, slow = 1e-8 |
| `dropR2` | `0.01` | `None`, `0.001`–`0.05` | Drop factors explaining less than this fraction of variance; `None` keeps all |
| `startELBO` | `1` | `1`–`100` | Iteration to start ELBO monitoring; set higher to skip initial instability |

## Key Concepts

### Latent Factors and Loadings

Each latent factor Z_k (a vector of length n_samples) represents a source of variation. The corresponding weight matrix W_k (a vector of length n_features per view) contains the loading of each feature on that factor. Factors with spike-and-slab priors produce sparse loadings: most weights are shrunk to near zero, leaving a small set of features that meaningfully drive the factor. A positive weight means higher factor score correlates with higher feature expression.

### Multi-Group vs Single-Group

A "group" in MOFA+ is a set of samples that share the same factor weight matrices W but have independent factor score distributions Z. Use multi-group analysis when:
- Samples come from distinct cohorts with batch-level differences (patients, datasets)
- You want to compare how much each factor explains within vs between groups
- You expect the same biological programs to operate differently across conditions

Single-group analysis (all samples in one group) is appropriate when samples are from a single experiment with no major batch structure.

### Variance Explained Heatmap Interpretation

The R2 heatmap (views x factors) is the primary diagnostic output. Factors should show:
- View-specific R2: a factor driving only RNA captures transcriptional programs; one driving both RNA and ATAC captures chromatin-accessibility-coupled gene expression
- Declining R2: Factor 1 explains the most variance; factors should be inspected in order
- Factors with <1% R2 in all views can generally be ignored

## Common Recipes

### Recipe: Multi-Group Analysis Across Conditions

Use when comparing two or more patient groups or experimental conditions, where you want to identify condition-specific vs shared factors.

```python
from mofapy2.run.entry_point import entry_point
import numpy as np
import pandas as pd
import anndata as ad

# Simulate two groups: condition A (100 cells) and condition B (100 cells)
np.random.seed(0)
n_per_group, n_genes, n_peaks = 100, 1000, 500
groups = {"condA": {}, "condB": {}}

for g in groups:
    groups[g]["rna"] = np.abs(np.random.randn(n_per_group, n_genes))
    groups[g]["atac"] = (np.random.rand(n_per_group, n_peaks) > 0.75).astype(float)

sample_ids_A = [f"A_cell_{i}" for i in range(n_per_group)]
sample_ids_B = [f"B_cell_{i}" for i in range(n_per_group)]

ent = entry_point()
ent.set_data_options(scale_groups=False, scale_views=True)

# Multi-group: data[groups][views] — two groups, each with RNA and ATAC
ent.set_data_matrix(
    data=[[groups["condA"]["rna"], groups["condA"]["atac"]],
          [groups["condB"]["rna"], groups["condB"]["atac"]]],
    likelihoods=["gaussian", "bernoulli"],
    views_names=["RNA", "ATAC"],
    groups_names=["condA", "condB"],
    samples_names=[sample_ids_A, sample_ids_B]
)

ent.set_model_options(factors=10, spikeslab_weights=True, ard_factors=True)
ent.set_train_options(iter=500, convergence_mode="fast", seed=0, verbose=False)
ent.build()
ent.run()
ent.save("mofa_multigroup.hdf5", overwrite=True)

# Compare factor scores between groups
factors_all = load_mofa_factors("mofa_multigroup.hdf5")
factors_all["group"] = ["condA"] * n_per_group + ["condB"] * n_per_group
print(f"Multi-group model trained. Factor scores: {factors_all.shape}")
print(factors_all.groupby("group")[["Factor1", "Factor2"]].mean().round(3))
```

### Recipe: Identify and Annotate Factors by Top-Weighted Genes

Retrieve the top positive and negative loading genes per factor and print a summary table for biological annotation.

```python
import pandas as pd

def annotate_factors(model_path, view_name="RNA", top_n=20, n_factors=5):
    """
    Summarize top-loading features per factor to assist biological annotation.

    Returns a DataFrame with factor names, top positive genes, top negative genes,
    and the absolute weight range (an activity proxy).
    """
    weights = load_mofa_weights(model_path, view_name)
    factor_cols = [f"Factor{i+1}" for i in range(min(n_factors, weights.shape[1]))]

    rows = []
    for fc in factor_cols:
        w = weights[fc]
        top_pos = w.nlargest(top_n).index.tolist()
        top_neg = w.nsmallest(top_n).index.tolist()
        rows.append({
            "Factor": fc,
            "Max_weight": round(w.max(), 4),
            "Min_weight": round(w.min(), 4),
            "Top_positive": ", ".join(top_pos[:5]),
            "Top_negative": ", ".join(top_neg[:5]),
        })

    summary = pd.DataFrame(rows)
    return summary

summary_df = annotate_factors("mofa_model.hdf5", view_name="RNA", top_n=20, n_factors=5)
print("\nFactor annotation summary (RNA view):")
print(summary_df.to_string(index=False))
summary_df.to_csv("mofa_factor_annotation.csv", index=False)
print("\nSaved mofa_factor_annotation.csv")
```

## Expected Outputs

| Output | Description |
|--------|-------------|
| `mofa_model.hdf5` | Trained MOFA+ model — factor scores, weights, ELBO trace, variance explained |
| `mofa_variance_explained.png` | Heatmap of R2 (%) per factor per view; primary diagnostic for factor selection |
| `mofa_factor_scatter.png` | Scatter plots of Factor1 vs Factor2/3 colored by metadata (condition, patient) |
| `mofa_rna_weights_heatmap.png` | Heatmap of top RNA feature weights across the first 5 factors |
| `mofa_factor_scores.csv` | Table of per-cell factor scores (cells x factors) with cluster labels |
| `mofa_factor_annotation.csv` | Factor annotation table: top positive/negative genes per factor |
| Per-factor gene lists | Input for gseapy Enrichr or GSEA to identify enriched pathways per factor |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `KeyError` in `set_data_matrix` | Mismatched number of groups, views, or sample list dimensions | Ensure `data`, `likelihoods`, `views_names`, `groups_names`, `samples_names` all have consistent lengths |
| All factors show near-zero variance explained | Data not preprocessed or scale mismatch across views | Normalize each view before input; set `scale_views=True`; verify non-zero variance in input matrices |
| Model trains but factor scores are NaN | Convergence failure due to extreme values or near-singular data | Check for Inf/NaN in input matrices; reduce `iter`; try `convergence_mode="fast"` first |
| Too many factors pruned (only 1-2 remain) | `dropR2` threshold too aggressive or insufficient variation in data | Set `dropR2=0.001` or `dropR2=None`; increase data diversity or reduce noise |
| `HDF5` file cannot be read | File truncated due to crash during training | Re-run training; check disk space; use `overwrite=True` in `ent.save()` |
| Factor scores identical across all samples | Single-sample group or zero-variance input view | Confirm at least 2 distinct samples per group; check input matrix is not all zeros |
| Very slow training (>1 hr) | Large feature space (>10k features per view) or many factors | Pre-filter to top HVGs (2000-5000) per view; reduce factors to 10-15; enable `verbose=False` |
| ELBO not converging (oscillates) | Learning rate instability or poorly scaled data | Increase `startELBO`; standardize each view independently; use `convergence_mode="slow"` |
| Weights all near zero for one view | Bernoulli likelihood on continuous data or vice versa | Verify `likelihoods` list matches view data types; use `"gaussian"` for normalized RNA |
| `ModuleNotFoundError: mofapy2` | Package not installed | `pip install mofapy2` |

## References

- [MOFA2 GitHub repository](https://github.com/bioFAM/MOFA2) — Source code for mofapy2 (Python) and MOFA2 R package
- [MOFA2 documentation and tutorials](https://biofam.github.io/MOFA2/) — Official documentation with vignettes for Python and R
- [Argelaguet et al. (2020)](https://doi.org/10.1186/s13059-020-02015-1) — "MOFA+: a statistical framework for comprehensive integration of multi-modal single-cell data", *Genome Biology*
- [Argelaguet et al. (2018)](https://doi.org/10.15252/msb.20178124) — Original MOFA paper, *Molecular Systems Biology*
- [mofapy2 PyPI package](https://pypi.org/project/mofapy2/) — Installation and version history
