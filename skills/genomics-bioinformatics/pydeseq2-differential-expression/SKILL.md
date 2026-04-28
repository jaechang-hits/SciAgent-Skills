---
name: "pydeseq2-differential-expression"
description: "Bulk RNA-seq DE with PyDESeq2: load counts, normalize, fit negative binomial models, Wald test (BH-FDR), LFC shrinkage, volcano/MA plots. Use for two-group comparisons, multi-factor designs with batch correction, multiple contrasts."
license: "CC-BY-4.0"
---

# PyDESeq2 Differential Expression Analysis

## Overview

PyDESeq2 is a Python reimplementation of the R DESeq2 package for differential gene expression analysis from bulk RNA-seq count data. It fits negative binomial generalized linear models per gene, estimates dispersion with empirical Bayes shrinkage, and performs Wald tests with Benjamini-Hochberg FDR correction. This skill covers the full pipeline from raw counts to publication-ready result tables and visualizations.

## When to Use

- Identifying differentially expressed genes between two or more experimental conditions from bulk RNA-seq
- Performing two-group comparisons (e.g., treated vs control) with proper statistical testing
- Running multi-factor designs that account for batch effects or covariates (e.g., `~batch + condition`)
- Applying log2 fold change shrinkage (apeGLM) for ranking and visualization
- Generating volcano plots, MA plots, and heatmaps from differential expression results
- Converting R-based DESeq2 workflows to a pure Python environment
- Integrating DE analysis into larger Python bioinformatics pipelines (e.g., with scanpy, pandas)
- Use **DESeq2** (R/Bioconductor) or **edgeR** instead for the reference R implementations with the broadest method support and community validation

## Prerequisites

- **Python packages**: `pydeseq2>=0.4`, `pandas>=1.4`, `numpy>=1.23`, `scipy>=1.11`, `scikit-learn>=1.1`, `anndata>=0.8`
- **Data requirements**: Raw (unnormalized) integer count matrix (samples x genes) + sample metadata DataFrame
- **Environment**: Python 3.10+; optional `matplotlib`, `seaborn` for visualization

```bash
pip install pydeseq2 matplotlib seaborn
```

## Workflow

### Step 1: Data Loading and Validation

Load the count matrix and metadata. PyDESeq2 expects counts as a samples x genes DataFrame with non-negative integers, and metadata as a samples x variables DataFrame with matching indices.

```python
import pandas as pd

# Load data — typical CSV has genes as rows, samples as columns
counts_raw = pd.read_csv("counts.csv", index_col=0)
metadata = pd.read_csv("metadata.csv", index_col=0)

# Transpose if needed: PyDESeq2 requires samples x genes
if counts_raw.shape[0] > counts_raw.shape[1]:
    counts_df = counts_raw.T  # genes x samples → samples x genes
else:
    counts_df = counts_raw

# Validate alignment
common_samples = counts_df.index.intersection(metadata.index)
counts_df = counts_df.loc[common_samples]
metadata = metadata.loc[common_samples]

print(f"Samples: {counts_df.shape[0]}, Genes: {counts_df.shape[1]}")
print(f"Metadata columns: {list(metadata.columns)}")
print(f"Condition counts:\n{metadata['condition'].value_counts()}")
```

### Step 2: Gene Filtering

Remove lowly expressed genes to improve statistical power and reduce multiple testing burden.

```python
# Filter genes with total counts below threshold
min_total_counts = 10
gene_counts = counts_df.sum(axis=0)
genes_to_keep = gene_counts[gene_counts >= min_total_counts].index
counts_df = counts_df[genes_to_keep]

# Optional: require minimum counts in a minimum number of samples
min_count_per_sample = 5
min_samples = 3
genes_expressed = (counts_df >= min_count_per_sample).sum(axis=0) >= min_samples
counts_df = counts_df.loc[:, genes_expressed]

print(f"Genes after filtering: {counts_df.shape[1]}")
```

### Step 3: DeseqDataSet Initialization and Fitting

Create the DESeq dataset object, specify the design formula, and run the full pipeline (size factor estimation, dispersion estimation, model fitting).

```python
from pydeseq2.dds import DeseqDataSet

dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata,
    design="~condition",   # Wilkinson-style formula
    refit_cooks=True,      # Refit after Cook's outlier removal
    n_cpus=4               # Parallel threads
)

# Run: size factors → dispersions → trend → MAP shrinkage → LFC fitting
dds.deseq2()

# Inspect normalization
print(f"Size factors (first 5): {dds.obsm['size_factors'][:5]}")
print(f"Size factor range: {dds.obsm['size_factors'].min():.2f} - {dds.obsm['size_factors'].max():.2f}")
```

### Step 4: Statistical Testing (Wald Test)

Perform Wald tests to identify differentially expressed genes. Specify the contrast as `[variable, test_level, reference_level]`.

```python
from pydeseq2.ds import DeseqStats

ds = DeseqStats(
    dds,
    contrast=["condition", "treated", "control"],
    alpha=0.05,              # FDR threshold
    cooks_filter=True,       # Filter Cook's outliers
    independent_filter=True  # Independent filtering for power
)

ds.summary()

# Access full results
results = ds.results_df
print(f"Total genes tested: {len(results)}")
print(f"Significant (padj < 0.05): {(results.padj < 0.05).sum()}")
```

### Step 5: LFC Shrinkage (Optional)

Apply apeGLM shrinkage to reduce noise in log2 fold change estimates. Use shrunk values for visualization and ranking, not for significance calls.

```python
# Apply shrinkage — modifies results_df.log2FoldChange in place
ds.lfc_shrink()

# Compare pre/post shrinkage effect
print(f"Max |LFC| after shrinkage: {results.log2FoldChange.abs().max():.2f}")
print(f"Genes with |LFC| > 2: {(results.log2FoldChange.abs() > 2).sum()}")
```

### Step 6: Result Filtering and Export

Filter significant genes and export results for downstream analysis.

```python
import numpy as np

# Significance + effect size filter
significant = results[
    (results.padj < 0.05) &
    (results.log2FoldChange.abs() > 1.0)
].copy()

# Separate up/down-regulated
up = significant[significant.log2FoldChange > 0].sort_values("padj")
down = significant[significant.log2FoldChange < 0].sort_values("padj")

print(f"Upregulated: {len(up)}, Downregulated: {len(down)}")

# Export
results.to_csv("deseq2_all_results.csv")
significant.to_csv("deseq2_significant.csv")
up.to_csv("deseq2_upregulated.csv")
down.to_csv("deseq2_downregulated.csv")
print("Results exported to CSV files")
```

### Step 7: Visualization — Volcano Plot

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 7))
res = results.dropna(subset=["padj"]).copy()
res["-log10_padj"] = -np.log10(res.padj)

# Color categories
is_sig = (res.padj < 0.05) & (res.log2FoldChange.abs() > 1.0)
is_up = is_sig & (res.log2FoldChange > 0)
is_down = is_sig & (res.log2FoldChange < 0)

ax.scatter(res.loc[~is_sig, "log2FoldChange"], res.loc[~is_sig, "-log10_padj"],
           c="grey", alpha=0.3, s=8, label="Not significant")
ax.scatter(res.loc[is_up, "log2FoldChange"], res.loc[is_up, "-log10_padj"],
           c="firebrick", alpha=0.6, s=12, label=f"Up ({is_up.sum()})")
ax.scatter(res.loc[is_down, "log2FoldChange"], res.loc[is_down, "-log10_padj"],
           c="steelblue", alpha=0.6, s=12, label=f"Down ({is_down.sum()})")

ax.axhline(-np.log10(0.05), ls="--", c="black", alpha=0.4)
ax.axvline(-1, ls="--", c="black", alpha=0.4)
ax.axvline(1, ls="--", c="black", alpha=0.4)
ax.set_xlabel("Log2 Fold Change")
ax.set_ylabel("-Log10(Adjusted P-value)")
ax.set_title("Volcano Plot — Treated vs Control")
ax.legend()
plt.tight_layout()
plt.savefig("volcano_plot.png", dpi=300)
print("Saved volcano_plot.png")
```

### Step 8: Visualization — MA Plot

```python
fig, ax = plt.subplots(figsize=(10, 7))

ax.scatter(np.log10(res.loc[~is_sig, "baseMean"] + 1),
           res.loc[~is_sig, "log2FoldChange"],
           c="grey", alpha=0.3, s=8)
ax.scatter(np.log10(res.loc[is_sig, "baseMean"] + 1),
           res.loc[is_sig, "log2FoldChange"],
           c="firebrick", alpha=0.6, s=12)

ax.axhline(0, ls="--", c="black", alpha=0.5)
ax.set_xlabel("Log10(Mean Normalized Count + 1)")
ax.set_ylabel("Log2 Fold Change")
ax.set_title("MA Plot")
plt.tight_layout()
plt.savefig("ma_plot.png", dpi=300)
print("Saved ma_plot.png")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `design` | (required) | Wilkinson formula | Model formula; put covariates before variable of interest |
| `contrast` | `None` | `[var, test, ref]` | Which comparison to test; `None` uses last coefficient |
| `alpha` | `0.05` | `0.01`–`0.10` | FDR threshold for significance calling |
| `refit_cooks` | `True` | `True`/`False` | Refit model after removing Cook's distance outliers |
| `cooks_filter` | `True` | `True`/`False` | Apply Cook's distance filtering during testing |
| `independent_filter` | `True` | `True`/`False` | Independent filtering to optimize detection power |
| `n_cpus` | `1` | `1`–`N` | Number of parallel threads for dispersion fitting |
| `min_total_counts` (user) | `10` | `5`–`50` | Gene filtering: minimum total reads across all samples |
| `lfc_shrink()` | off | call after `summary()` | apeGLM shrinkage; reduces noisy LFC estimates |

## Common Recipes

### Recipe: Multiple Contrasts from One Model

When comparing multiple treatment groups against a shared control.

```python
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design="~condition")
dds.deseq2()

contrasts = {
    "A_vs_ctrl": ["condition", "treatment_A", "control"],
    "B_vs_ctrl": ["condition", "treatment_B", "control"],
    "C_vs_ctrl": ["condition", "treatment_C", "control"],
}

for name, contrast in contrasts.items():
    ds = DeseqStats(dds, contrast=contrast, alpha=0.05)
    ds.summary()
    n_sig = (ds.results_df.padj < 0.05).sum()
    ds.results_df.to_csv(f"results_{name}.csv")
    print(f"{name}: {n_sig} significant genes")
```

### Recipe: Batch-Corrected Analysis

When samples come from multiple batches or sequencing runs.

```python
# Verify batch is not confounded with condition
print(pd.crosstab(metadata["batch"], metadata["condition"]))

dds = DeseqDataSet(
    counts=counts_df, metadata=metadata,
    design="~batch + condition"  # batch first, then variable of interest
)
dds.deseq2()

ds = DeseqStats(dds, contrast=["condition", "treated", "control"])
ds.summary()
print(f"Significant genes (batch-corrected): {(ds.results_df.padj < 0.05).sum()}")
```

### Recipe: P-value Distribution QC

Diagnostic check — a healthy analysis shows a flat histogram with a spike near 0.

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# P-value histogram
axes[0].hist(ds.results_df.pvalue.dropna(), bins=50, edgecolor="black")
axes[0].set_xlabel("P-value")
axes[0].set_ylabel("Frequency")
axes[0].set_title("P-value Distribution")

# Dispersion plot
axes[1].scatter(
    np.log10(dds.varm["_normed_means"] + 1),
    np.log10(dds.varm["dispersions"]),
    alpha=0.3, s=5
)
axes[1].set_xlabel("Log10(Mean Expression + 1)")
axes[1].set_ylabel("Log10(Dispersion)")
axes[1].set_title("Dispersion vs Mean")

plt.tight_layout()
plt.savefig("qc_diagnostics.png", dpi=300)
print("Saved qc_diagnostics.png")
```

### Recipe: Save and Reload DESeq Dataset

For resuming analysis without re-running the expensive fitting step.

```python
import pickle

# Save
with open("dds_fitted.pkl", "wb") as f:
    pickle.dump(dds.to_picklable_anndata(), f)
print("Saved fitted DESeqDataSet")

# Reload
with open("dds_fitted.pkl", "rb") as f:
    adata = pickle.load(f)
# Note: reload requires re-constructing DeseqDataSet from the AnnData
```

## Expected Outputs

- `deseq2_all_results.csv` — Full results table (baseMean, log2FoldChange, lfcSE, stat, pvalue, padj) for all tested genes
- `deseq2_significant.csv` — Filtered results (padj < 0.05 and |LFC| > 1)
- `deseq2_upregulated.csv` — Significant upregulated genes sorted by padj
- `deseq2_downregulated.csv` — Significant downregulated genes sorted by padj
- `volcano_plot.png` — Volcano plot with significance and fold change thresholds
- `ma_plot.png` — MA plot showing fold change vs mean expression
- `qc_diagnostics.png` — P-value distribution and dispersion plot

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: Index mismatch` | Sample names differ between counts and metadata | Use `counts_df.index.intersection(metadata.index)` to align |
| All genes have `padj = NaN` | Genes have zero variance or all zero counts | Apply stricter gene filtering (increase `min_total_counts`) |
| `Design matrix is not full rank` | Confounded variables (e.g., all treated in one batch) | Check with `pd.crosstab()`; simplify design or remove confounded variable |
| No significant genes found | Small effect size, high variability, or low sample size | Check p-value distribution; relax alpha or |LFC| threshold; inspect QC plots |
| `MemoryError` during fitting | Too many genes or very large dataset | Pre-filter more aggressively; reduce `n_cpus`; use machine with more RAM |
| Very large size factors (>5) | Extreme library size differences | Verify raw counts are unnormalized; check for contamination or failed libraries |
| Shrinkage produces unexpected LFCs | Calling `lfc_shrink()` before `summary()` | Always call `ds.summary()` first, then `ds.lfc_shrink()` |

## References

- [PyDESeq2 Documentation](https://pydeseq2.readthedocs.io/) — Official API reference and tutorials
- [Muzellec et al. (2023)](https://doi.org/10.1093/bioinformatics/btad547) — PyDESeq2: a Python package for bulk differential expression analysis with DESeq2. Bioinformatics.
- [Love et al. (2014)](https://doi.org/10.1186/s13059-014-0550-8) — Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. Genome Biology.
- [DESeq2 Vignette (Bioconductor)](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html) — Comprehensive R DESeq2 guide with design formula examples
