---
name: degenerate-input-filtering
description: "Mandatory filtering of degenerate and uninformative data points before statistical tests. Covers single-sequence alignments, empty files, constant-value features, and zero-variance inputs."
license: CC-BY-4.0
compatibility: Python 3.10+, R 4.0+
metadata:
  authors: HITS
  version: "1.0"
---

# Degenerate Input Filtering Guide

## Overview

This guide covers the mandatory filtering of degenerate and uninformative data points before performing statistical tests or analyses. Degenerate inputs produce meaningless results (e.g., score=0.0, correlation=NaN, p-value=1.0) that contaminate downstream analyses.

---

## Rule 1 (MANDATORY): Filter Degenerate Inputs Before Statistical Tests

**CRITICAL: Before performing any statistical test, filter out degenerate/uninformative data points. Always print the count of filtered items.**

### What Are Degenerate Inputs?

| Type | Example | Why It Fails |
|---|---|---|
| Single-sequence alignment | BLAST/alignment with only 1 sequence | Score = 0.0, no meaningful comparison |
| Empty files | 0-byte input files | Analysis crashes or returns NaN |
| Constant-value features | Gene with same expression in all samples | Variance = 0, correlation undefined |
| All-NaN features | Feature with no valid observations | Any statistic is NaN |
| Single-value after grouping | One sample per group | No variance, test is meaningless |
| Zero-length sequences | Empty FASTA entries | Alignment/analysis fails |

### General Pattern

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

---

## Rule 2: Domain-Specific Degenerate Inputs

### Sequence Alignments

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

### Gene Expression Analysis

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

### Correlation Analysis

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

---

## Rule 3: Always Report Filtering in Output

**MANDATORY: Every time you filter degenerate inputs, print:**
1. The count of items filtered
2. The reason for filtering
3. The count of remaining items

This ensures:
- The filtering is documented and auditable
- Unexpected data quality issues are surfaced
- The user knows the effective sample/feature size

### Example Output Format

```
Input: 18500 genes
Filtered: 230 genes with zero variance
Filtered: 45 genes with < 3 valid samples
Remaining: 18225 genes for analysis
```

---

## Checklist

Before performing statistical analysis, verify:

- [ ] Checked for constant-value features (zero variance) and removed them
- [ ] Checked for all-NaN features and removed them
- [ ] Checked for features with too few valid observations
- [ ] Checked for domain-specific degenerate inputs (single-sequence alignments, empty files, etc.)
- [ ] Printed the count of filtered items with reason
- [ ] Printed the count of remaining items
- [ ] Did NOT silently drop data without reporting
