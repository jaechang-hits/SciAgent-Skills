---
name: nan-safe-correlation
description: "Mandatory per-feature NaN-safe Spearman correlation computation. Covers why bulk matrix shortcuts fail with missing data, correct pairwise deletion, and degenerate input filtering."
license: CC-BY-4.0
compatibility: Python 3.10+
metadata:
  authors: HITS
  version: "1.0"
---

# NaN-Safe Correlation Computation Guide

## Overview

This guide covers the correct computation of Spearman (and Pearson) correlations across many features (genes, proteins, variants) when missing values are present. The most common error is using bulk matrix shortcuts that silently mishandle NaN, producing incorrect correlation values.

---

## Rule 1 (MANDATORY): Per-Feature Correlation with Pairwise NaN Removal

**CRITICAL: When computing correlations across many features, use `scipy.stats.spearmanr` (or `pearsonr`) per feature in a loop with pairwise NaN removal. Do NOT use bulk matrix shortcuts.**

### Why Bulk Shortcuts Fail

Different features have different missing value patterns across samples. Bulk methods handle this inconsistently:

| Method | Problem |
|---|---|
| `DataFrame.rank()` then `corrwith()` | `rank()` assigns NaN ranks, `corrwith()` may drop globally or per-column inconsistently |
| `DataFrame.corrwith(method='spearman')` | Implementation varies by pandas version; may use listwise deletion (drops all rows with any NaN) |
| `np.corrcoef` on ranked data | Propagates NaN to entire result if any value is missing |

### Impact

- Correlations can shift by 0.01-0.05 or more
- Genes near a threshold (e.g., 0.6) can be misclassified
- Total valid sample count per gene is unknown (may silently use fewer samples than expected)

### Correct Implementation

```python
from scipy.stats import spearmanr, pearsonr
import numpy as np
import pandas as pd

def pairwise_spearman(df_x, df_y, min_valid=10):
    """Compute per-feature Spearman correlation with pairwise NaN removal.

    Args:
        df_x: DataFrame (samples x features), aligned with df_y
        df_y: DataFrame (samples x features), same shape as df_x
        min_valid: Minimum number of valid (non-NaN) pairs required

    Returns:
        DataFrame with columns: rho, pvalue, n_valid
    """
    # Print NaN summary
    total_nan_x = df_x.isna().sum().sum()
    total_nan_y = df_y.isna().sum().sum()
    print(f"Total NaN in X: {total_nan_x} / {df_x.size}")
    print(f"Total NaN in Y: {total_nan_y} / {df_y.size}")

    results = []
    for feature in df_x.columns:
        x = df_x[feature].values
        y = df_y[feature].values

        # Pairwise deletion: remove pairs where either is NaN
        mask = ~(np.isnan(x) | np.isnan(y))
        n_valid = mask.sum()

        if n_valid < min_valid:
            results.append({'feature': feature, 'rho': np.nan,
                          'pvalue': np.nan, 'n_valid': n_valid})
            continue

        rho, pval = spearmanr(x[mask], y[mask])
        results.append({'feature': feature, 'rho': rho,
                       'pvalue': pval, 'n_valid': n_valid})

    result_df = pd.DataFrame(results).set_index('feature')

    # Report how many features were skipped
    skipped = result_df['rho'].isna().sum()
    if skipped > 0:
        print(f"Skipped {skipped} features with < {min_valid} valid pairs")

    return result_df
```

### Anti-Patterns (DO NOT DO THIS)

```python
# WRONG: Bulk rank-then-correlate
ranked_x = df_x.rank()
ranked_y = df_y.rank()
corrs = ranked_x.corrwith(ranked_y)

# WRONG: Bulk corrwith with method parameter
corrs = df_x.corrwith(df_y, method='spearman')

# WRONG: numpy corrcoef on ranked arrays (propagates NaN)
corrs = np.corrcoef(df_x.rank().values.T, df_y.rank().values.T)
```

---

## Rule 2: Filter Degenerate Inputs Before Correlation

**CRITICAL: Before computing correlations, filter out degenerate/uninformative data points.**

### What Are Degenerate Inputs?

- **Constant features**: All values identical (variance = 0) -- correlation is undefined
- **Near-constant features**: Very low variance -- correlation is unstable
- **Too few valid values**: After NaN removal, fewer than min_valid pairs remain
- **Single-value after filtering**: Only one unique value remains after removing NaN

### Implementation

```python
def filter_degenerate(df, min_unique=3, min_nonnan_frac=0.5):
    """Remove degenerate features before correlation analysis.

    Args:
        df: DataFrame (samples x features)
        min_unique: Minimum number of unique non-NaN values required
        min_nonnan_frac: Minimum fraction of non-NaN values required

    Returns:
        Filtered DataFrame, count of removed features
    """
    n_samples = len(df)
    keep = []

    for col in df.columns:
        values = df[col].dropna()
        if len(values) < n_samples * min_nonnan_frac:
            continue
        if values.nunique() < min_unique:
            continue
        keep.append(col)

    removed = len(df.columns) - len(keep)
    print(f"Filtered {removed} degenerate features out of {len(df.columns)}")

    return df[keep], removed
```

---

## Rule 3: Always Print NaN Summary Before Analysis

**MANDATORY: Print the total NaN count and per-feature NaN distribution before computing correlations.**

```python
# Before any correlation computation
print(f"Dataset shape: {df.shape}")
print(f"Total NaN: {df.isna().sum().sum()}")
print(f"Features with any NaN: {(df.isna().any()).sum()}")
print(f"NaN per feature (mean): {df.isna().sum().mean():.1f}")
print(f"NaN per feature (max): {df.isna().sum().max()}")
```

This serves two purposes:
1. Documents the data quality in the output
2. Alerts you if the NaN pattern is severe enough to affect results

---

## Performance Optimization

For large datasets (>10,000 features), the per-feature loop can be slow. Optimize with:

```python
from joblib import Parallel, delayed

def parallel_spearman(df_x, df_y, min_valid=10, n_jobs=4):
    """Parallelized per-feature Spearman correlation."""

    def compute_one(feature):
        x = df_x[feature].values
        y = df_y[feature].values
        mask = ~(np.isnan(x) | np.isnan(y))
        n = mask.sum()
        if n < min_valid:
            return feature, np.nan, np.nan, n
        rho, pval = spearmanr(x[mask], y[mask])
        return feature, rho, pval, n

    results = Parallel(n_jobs=n_jobs)(
        delayed(compute_one)(f) for f in df_x.columns
    )

    return pd.DataFrame(results, columns=['feature', 'rho', 'pvalue', 'n_valid']).set_index('feature')
```

---

## Checklist

Before reporting correlation results across many features, verify:

- [ ] Total NaN count was printed before analysis
- [ ] Per-feature Spearman was computed using `scipy.stats.spearmanr` in a loop
- [ ] Pairwise NaN removal was used (not listwise/global deletion)
- [ ] Degenerate features (constant values, too few valid pairs) were filtered
- [ ] Count of filtered/skipped features was reported
- [ ] Number of valid pairs per feature is tracked (not assumed uniform)
