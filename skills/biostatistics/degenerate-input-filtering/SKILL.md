---
name: degenerate-input-filtering
description: "Mandatory filtering of degenerate and uninformative data points before statistical tests. Covers single-sequence alignments, empty files, constant-value features, zero-variance inputs, and all-NaN columns. For NaN-aware correlation computation, see the nan-safe-correlation skill. For broader statistical testing guidance, see the statistical-analysis skill."
license: CC-BY-4.0
---

# Degenerate Input Filtering Guide

## Overview

Degenerate inputs are data points that carry no statistical information: constant-value features, all-NaN columns, single-sequence alignments, empty files, and similar edge cases. When these reach a statistical test or model, the result is meaningless -- a correlation of NaN, a p-value of 1.0, a score of 0.0, or an outright crash. This guide establishes the mandatory practice of detecting and removing such inputs before any analysis, and of reporting every removal so that downstream consumers know the effective sample size.

## Key Concepts

### What Counts as Degenerate

A data point is degenerate when it cannot contribute to the statistic being computed. The root cause is always the same: the input lacks the variation or completeness that the method requires.

| Type | Example | Why It Fails |
|---|---|---|
| Constant-value feature | Gene with identical expression across all samples | Variance = 0; correlation, t-test, fold-change are all undefined |
| All-NaN feature | Column with no valid observations | Every aggregation returns NaN |
| Single-sequence alignment | BLAST result with one sequence | Score = 0.0; no pairwise comparison is possible |
| Empty file | 0-byte FASTA or CSV | Parser crashes or returns an empty frame |
| Single value after grouping | One sample in a treatment group | Within-group variance is undefined; group comparison is meaningless |
| Zero-length sequence | Empty FASTA entry | Alignment and k-mer tools fail or produce nonsense |
| Near-constant feature | Gene with one outlier and N-1 identical values | Technically non-zero variance but correlation is dominated by a single point |

### Why Silent Failures Are Dangerous

Many numerical libraries do not raise errors on degenerate input. Instead they return sentinel values:

- `numpy.corrcoef` returns `nan` for constant columns without warning.
- `scipy.stats.spearmanr` returns `(nan, nan)` when one array is constant.
- `scipy.stats.ttest_ind` returns `(nan, nan)` for zero-variance groups.

These NaN values propagate silently through pipelines, contaminating aggregated statistics, heatmaps, volcano plots, and ranked gene lists. By the time a researcher notices the problem, it may be unclear which upstream step introduced the NaN.

### The Reporting Obligation

Filtering without reporting is nearly as harmful as not filtering. When items are silently dropped, the effective sample or feature count differs from what the user expects, leading to incorrect power calculations and misleading summary statistics. Every filtering step must print:

1. The count of items removed.
2. The reason for removal.
3. The count of items remaining.

## Decision Framework

Use this tree to determine which filtering checks apply to your data before running a statistical analysis:

```
Is the input tabular (DataFrame)?
├── Yes
│   ├── Are there columns with zero unique values (all NaN)? → Remove, report count
│   ├── Are there columns with exactly one unique value (constant)? → Remove, report count
│   ├── Are there columns with fewer than N valid observations? → Remove, report count
│   └── Are there near-constant columns (1 outlier, rest identical)? → Flag or remove
└── No (file list, sequence set, etc.)
    ├── Are there empty files (0 bytes)? → Skip, report count
    ├── Are there single-entry collections (e.g., 1-sequence alignment)? → Skip, report count
    └── Are there zero-length entries within a file? → Filter entries, report count
```

| Scenario | Recommended Check | Threshold |
|---|---|---|
| Gene expression matrix before DE analysis | Remove zero-variance genes, remove genes detected in fewer than N samples | N = max(3, 10% of samples) |
| Correlation analysis between two feature sets | Remove features constant in either set; require >= 10 shared non-NaN pairs | nunique >= 2 in both vectors; shared observations >= 10 |
| Multiple sequence alignment scoring | Skip alignments with < 2 sequences | Sequence count >= 2 |
| Survival analysis with grouped covariates | Remove groups with < 2 events | Events per group >= 2 |
| PCA or clustering on a feature matrix | Remove zero-variance and all-NaN features | Variance > 0 and at least 1 non-NaN value |
| Batch correction (e.g., ComBat) | Remove features absent in any batch | Feature detected in all batches |

## Best Practices

1. **Filter before any statistical computation, not after.** Degenerate inputs can cause division-by-zero, NaN propagation, and inflated multiple-testing corrections. Filtering after the test means the damage is already done.

2. **Use a single reusable filtering function.** Centralizing the logic prevents inconsistencies between scripts and ensures the reporting format is uniform. See the reference implementation in the Workflow section below.

3. **Print counts at every filtering step.** Even when the count is zero, printing "0 items removed" confirms that the check ran. This makes logs self-documenting and auditable.

4. **Set domain-appropriate thresholds rather than relying on generic defaults.** A gene expression analysis might require detection in at least 10% of samples, while a proteomics dataset with more missingness might use 5%. Document the threshold and the rationale.

5. **Treat near-constant features with caution.** A feature with one non-identical value technically has non-zero variance, but its correlation with anything is driven entirely by that single point. Consider flagging these separately rather than including them blindly.

6. **Never filter silently.** Dropping data without reporting is a form of hidden data manipulation. Every removal must be logged with the reason and the count, so that the effective sample size is always transparent.

7. **Re-check after transformations.** Log-transforming expression data can introduce negative infinities from zero counts. Merging datasets can introduce new NaN columns. Run the degenerate check again after any transformation or merge step.

## Common Pitfalls

1. **Running a correlation on constant-valued columns and getting NaN without realizing it.** The NaN result silently propagates into downstream rankings, heatmaps, or enrichment inputs, producing misleading figures.
   - *How to avoid*: Always check `nunique() >= 2` for every column before computing correlations. Use the reference implementation below.

2. **Scoring single-sequence alignments and reporting a score of 0.0 as a real result.** Alignment scores require at least two sequences; a single-sequence "alignment" is not a failed alignment, it is a non-alignment.
   - *How to avoid*: Count sequences before scoring. Skip and report any alignment file with fewer than 2 sequences.

3. **Filtering data but not reporting the count, leading to confusion about effective sample size.** A volcano plot based on 15,000 genes looks very different from one based on 18,500, but without a log message, no one knows which it is.
   - *How to avoid*: Always print three things: count removed, reason, count remaining. Include this in every notebook and script.

4. **Applying a minimum-samples threshold that is too low, retaining genes detected in only 1-2 samples.** These genes produce unstable variance estimates and unreliable p-values that inflate the false discovery rate.
   - *How to avoid*: Use `max(3, int(0.1 * n_samples))` as a floor. Adjust upward for small studies where even 10% is fewer than 3.

5. **Forgetting to re-check after a merge or transformation step.** Joining two datasets can introduce all-NaN columns from non-overlapping features. Log-transforming zeros creates negative infinities. Both are degenerate.
   - *How to avoid*: Run the degenerate filter again after every merge, join, or mathematical transformation.

6. **Using `df.var() > 0` without handling NaN correctly.** If a column is all NaN, `var()` returns NaN, which is not `> 0`, so the column is dropped -- but the reason logged is "zero variance" rather than "all NaN," which is misleading.
   - *How to avoid*: Check for all-NaN columns separately before checking for zero variance. Report each category with its own label.

7. **Assuming the input is clean because it came from a curated database.** Public databases contain placeholder values, missing entries, and withdrawn records. Always validate, even when the source is trusted.
   - *How to avoid*: Treat every input as untrusted. Run the full degenerate-input check regardless of the data source.

## Workflow

The following sequential process should be applied before any statistical analysis.

1. **Step 1: Load and inspect**
   - Load the data into a DataFrame or equivalent structure.
   - Print the shape: rows, columns, and dtype summary.

2. **Step 2: Remove all-NaN features**
   - Identify columns (or rows, depending on orientation) where every value is NaN.
   - Remove them and print the count.

3. **Step 3: Remove constant-value features**
   - Identify columns with `nunique() <= 1` (after excluding NaN).
   - Remove them and print the count.

4. **Step 4: Remove features with too few valid observations**
   - Set a threshold (e.g., at least 10% of samples or at least 3).
   - Remove features below the threshold and print the count.

5. **Step 5: Apply domain-specific checks**
   - For sequence data: skip single-sequence alignments, empty files, zero-length entries.
   - For expression data: filter low-detection genes.
   - For correlation inputs: verify both vectors are non-constant and share enough observations.

6. **Step 6: Report summary**
   - Print a final summary: total input, total removed (by category), total remaining.

### Reference Implementation

```python
import pandas as pd
import numpy as np

def filter_degenerate(data, context="features"):
    """Filter degenerate data points and report what was removed.

    Always call this BEFORE statistical analysis.
    """
    n_before = len(data)

    # Filter based on data type
    if isinstance(data, pd.DataFrame):
        # Remove constant columns (zero variance)
        non_constant = data.loc[:, data.nunique() > 1]
        # Remove all-NaN columns
        non_nan = non_constant.dropna(axis=1, how='all')
        filtered = non_nan
    elif isinstance(data, list):
        # Remove None, empty, and zero-length items
        filtered = [x for x in data if x is not None and len(x) > 0]
    else:
        filtered = data

    n_after = len(filtered) if not isinstance(filtered, pd.DataFrame) else filtered.shape[1]
    n_removed = n_before if not isinstance(data, pd.DataFrame) else data.shape[1]
    n_removed = n_removed - n_after

    # MANDATORY: Print the count
    print(f"Degenerate {context} filtered: {n_removed} / {n_before} removed")
    print(f"Remaining {context}: {n_after}")

    return filtered
```

### Sequence Alignment Filtering

```python
# Filter single-sequence alignments (score=0.0 is meaningless)
alignment_scores = {}
for aln_file in alignment_files:
    n_seqs = count_sequences(aln_file)
    if n_seqs < 2:
        print(f"Skipping {aln_file}: only {n_seqs} sequence(s)")
        continue
    score = compute_alignment_score(aln_file)
    alignment_scores[aln_file] = score

print(f"Filtered {len(alignment_files) - len(alignment_scores)} single-sequence alignments")
```

### Gene Expression Filtering

```python
# Filter genes with zero variance (constant expression)
gene_vars = expression_df.var(axis=1)
zero_var = (gene_vars == 0).sum()
print(f"Genes with zero variance: {zero_var}")
expression_filtered = expression_df.loc[gene_vars > 0]

# Filter genes detected in too few samples
min_samples = max(3, int(0.1 * expression_df.shape[1]))  # At least 10% of samples
detected = (expression_df > 0).sum(axis=1)
low_detection = (detected < min_samples).sum()
print(f"Genes detected in < {min_samples} samples: {low_detection}")
expression_filtered = expression_filtered.loc[detected >= min_samples]
```

### Correlation Pre-filtering

```python
from scipy.stats import spearmanr

# Filter features before computing correlations
valid_correlations = {}
skipped_constant = 0
skipped_few_values = 0

for feature in features:
    x = data_x[feature].dropna()
    y = data_y[feature].dropna()

    # Check for constant values
    if x.nunique() < 2 or y.nunique() < 2:
        skipped_constant += 1
        continue

    # Check for sufficient data points
    common = x.index.intersection(y.index)
    if len(common) < 10:
        skipped_few_values += 1
        continue

    rho, pval = spearmanr(x[common], y[common])
    valid_correlations[feature] = rho

print(f"Skipped (constant values): {skipped_constant}")
print(f"Skipped (< 10 valid pairs): {skipped_few_values}")
print(f"Valid correlations computed: {len(valid_correlations)}")
```

### Expected Output Format

A well-formatted filtering report looks like this:

```
Input: 18500 genes
Filtered: 230 genes with zero variance
Filtered: 45 genes with < 3 valid samples
Remaining: 18225 genes for analysis
```

## Further Reading

- [scipy.stats documentation](https://docs.scipy.org/doc/scipy/reference/stats.html) -- Reference for statistical functions and their behavior on edge-case inputs including constant arrays and NaN values.
- [pandas DataFrame.dropna](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.dropna.html) -- Official documentation for NaN removal with axis and threshold control.
- [numpy NaN handling](https://numpy.org/doc/stable/user/misc.html) -- NumPy documentation covering NaN propagation semantics in arithmetic and aggregation functions.
- [Lun, A. et al. (2016) "A step-by-step workflow for low-level analysis of single-cell RNA-seq data with Bioconductor"](https://doi.org/10.12688/f1000research.9501.2) -- Demonstrates gene-level quality control filtering including low-abundance and zero-variance gene removal prior to normalization and differential expression.
- [Law, C.W. et al. (2018) "RNA-seq analysis is easy as 1-2-3 with limma, Glimma and edgeR"](https://doi.org/10.12688/f1000research.9005.3) -- Covers filterByExpr-style gene filtering to remove lowly expressed and uninformative genes before differential expression analysis.

## Related Skills

- `nan-safe-correlation` -- Techniques for computing correlations in the presence of missing values; complements this guide's pre-filtering step for correlation inputs.
- `statistical-analysis` -- Broader guidance on choosing and applying statistical tests; assumes degenerate inputs have already been removed per this guide.
