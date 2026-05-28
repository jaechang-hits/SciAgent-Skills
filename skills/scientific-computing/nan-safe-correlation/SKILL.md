---
name: nan-safe-correlation
description: "Per-feature NaN-safe Spearman/Pearson correlation across many features (genes, proteins, variants) with missing values. Covers why bulk matrix shortcuts fail, correct pairwise deletion, degenerate input filtering, and large-dataset performance. Use statistical-analysis for test choice; shap-model-explainability for interpretability."
license: CC-BY-4.0
---

# NaN-Safe Correlation Computation

## Overview

Computing correlations across many features (genes, proteins, variants) when missing values are present is error-prone. The most common mistake is using bulk matrix shortcuts that silently mishandle NaN, producing incorrect correlation values. This guide covers correct per-feature pairwise computation, degenerate input filtering, and performance optimization.

## Key Concepts

### Pairwise vs Listwise Deletion

- **Pairwise deletion**: For each feature pair, remove only samples where either value is NaN. Each feature uses the maximum available data.
- **Listwise deletion**: Remove any sample with NaN in any feature. Wastes valid data and biases results if missingness is not completely random.
- **Rule**: Always use pairwise deletion for per-feature correlations.

### Why Bulk Matrix Shortcuts Fail

Different features have different missing value patterns across samples. Bulk methods handle this inconsistently:

| Method | Problem |
|--------|---------|
| `DataFrame.rank()` then `corrwith()` | `rank()` assigns NaN ranks; `corrwith()` may drop globally or per-column inconsistently |
| `DataFrame.corrwith(method='spearman')` | Implementation varies by pandas version; may use listwise deletion |
| `np.corrcoef` on ranked data | Propagates NaN to entire result if any value is missing |

### Impact of Incorrect Computation

- Correlations can shift by 0.01-0.05 or more
- Features near a threshold (e.g., 0.6) can be misclassified
- Valid sample count per feature is unknown (may silently use fewer samples than expected)

### Degenerate Inputs

Features that produce undefined or unstable correlations:

| Type | Description | Effect |
|------|-------------|--------|
| Constant features | All values identical (variance = 0) | Correlation undefined (division by zero) |
| Near-constant features | Very low variance | Correlation numerically unstable |
| Too few valid values | After NaN removal, fewer than min_valid pairs | Statistically unreliable |
| Single-value after filtering | Only one unique value remains post-NaN removal | Correlation undefined |

## Decision Framework

```
Do you have missing values (NaN) in your feature matrix?
├── No NaN at all → Bulk methods are safe (corrwith, np.corrcoef)
└── Yes, NaN present
    ├── Same NaN pattern across all features? → Listwise deletion is acceptable
    └── Different NaN patterns per feature (typical)
        ├── < 10,000 features → Per-feature loop with scipy.stats.spearmanr
        └── > 10,000 features → Parallelized per-feature loop (joblib)
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| No missing data | `DataFrame.corrwith()` | Fast, correct when no NaN |
| Sparse NaN, < 10K features | Per-feature `spearmanr` loop | Correct pairwise deletion, acceptable speed |
| Sparse NaN, > 10K features | Parallelized per-feature loop | Same correctness, scales with cores |
| Dense NaN (> 50% missing) | Per-feature loop + strict min_valid | Many features will be skipped; report skip count |
| Uniform NaN pattern | Listwise deletion + bulk method | If all features share same NaN rows, pairwise = listwise |

## Best Practices

1. **Always print NaN summary before analysis**: Report total NaN count, features with any NaN, and per-feature NaN distribution. This documents data quality and alerts you to severe missingness patterns.

2. **Use scipy.stats.spearmanr per feature in a loop**: This is the only method that guarantees correct pairwise NaN removal for each feature independently.

3. **Set a minimum valid pair threshold (min_valid)**: Default to 10. Features with fewer valid pairs after NaN removal produce unreliable correlations and should be skipped with NaN.

4. **Filter degenerate inputs before computing correlations**: Remove constant features, near-constant features, and features with excessive NaN before the correlation loop. This avoids undefined results and speeds up computation.

5. **Track n_valid per feature in the output**: The number of valid pairs varies per feature. Report it alongside rho and p-value so downstream analysis can assess reliability.

6. **Report how many features were skipped or filtered**: Silent feature loss is a common source of confusion. Always print the count of filtered degenerate features and skipped low-data features.

7. **Use parallelization for large datasets**: For > 10,000 features, use joblib to distribute the per-feature loop across cores. The per-feature computation is embarrassingly parallel.

## Common Pitfalls

1. **Using bulk rank-then-correlate with NaN present**: `df.rank()` followed by `corrwith()` silently mishandles NaN, producing incorrect correlations.
   - *How to avoid*: Always use `scipy.stats.spearmanr` per feature when NaN is present.

2. **Assuming uniform sample count across features**: Different features have different NaN patterns, so each correlation is computed on a different number of samples.
   - *How to avoid*: Track and report `n_valid` for every feature.

3. **Not filtering degenerate inputs**: Constant or near-constant features produce undefined correlations or divide-by-zero warnings that can silently corrupt results.
   - *How to avoid*: Run `filter_degenerate()` before the correlation loop.

4. **Using listwise deletion when NaN patterns differ**: Listwise deletion removes any row with NaN in any feature, potentially discarding most of your data.
   - *How to avoid*: Use pairwise deletion (per-feature NaN removal).

5. **Ignoring the NaN summary step**: Skipping the data quality report means you cannot verify whether the NaN pattern is severe enough to affect results.
   - *How to avoid*: Always print NaN summary before correlation computation.

6. **Setting min_valid too low**: With fewer than ~10 valid pairs, Spearman correlation is unreliable and p-values are meaningless.
   - *How to avoid*: Use min_valid >= 10; increase for high-dimensional studies.

## Workflow

1. **Step 1: Print NaN Summary**
   - Report dataset shape, total NaN, features with any NaN, mean/max NaN per feature
   - Decision point: If > 50% NaN overall, reconsider data quality before proceeding

2. **Step 2: Filter Degenerate Features**
   - Remove constant features (nunique < 3)
   - Remove features with excessive NaN (< 50% non-NaN)
   - Report count of removed features

3. **Step 3: Compute Per-Feature Correlations**
   - Loop over features with `scipy.stats.spearmanr`
   - Apply pairwise NaN removal per feature
   - Skip features with < min_valid valid pairs (record as NaN)

4. **Step 4: Assemble and Report Results**
   - Create DataFrame with rho, p-value, n_valid per feature
   - Report count of skipped features
   - Verify no silent data loss (input features = output features + skipped + filtered)

### Reference Implementation

```python
from scipy.stats import spearmanr
import numpy as np
import pandas as pd

def nan_summary(df):
    """Print NaN summary before correlation analysis."""
    print(f"Dataset shape: {df.shape}")
    print(f"Total NaN: {df.isna().sum().sum()}")
    print(f"Features with any NaN: {(df.isna().any()).sum()}")
    print(f"NaN per feature (mean): {df.isna().sum().mean():.1f}")
    print(f"NaN per feature (max): {df.isna().sum().max()}")

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

def pairwise_spearman(df_x, df_y, min_valid=10):
    """Compute per-feature Spearman correlation with pairwise NaN removal.

    Args:
        df_x: DataFrame (samples x features), aligned with df_y
        df_y: DataFrame (samples x features), same shape as df_x
        min_valid: Minimum number of valid (non-NaN) pairs required

    Returns:
        DataFrame with columns: rho, pvalue, n_valid
    """
    nan_summary(df_x)
    nan_summary(df_y)

    results = []
    for feature in df_x.columns:
        x = df_x[feature].values
        y = df_y[feature].values
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
    skipped = result_df['rho'].isna().sum()
    if skipped > 0:
        print(f"Skipped {skipped} features with < {min_valid} valid pairs")
    return result_df
```

### Anti-Patterns

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

### Performance Optimization (> 10,000 features)

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
    return pd.DataFrame(
        results, columns=['feature', 'rho', 'pvalue', 'n_valid']
    ).set_index('feature')
```

## Further Reading

- [scipy.stats.spearmanr documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html) -- Official API reference
- [pandas corrwith documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corrwith.html) -- Known NaN handling behavior
- [Pairwise vs Listwise Deletion](https://stefvanbuuren.name/fimd/sec-pairwise.html) -- Chapter from Flexible Imputation of Missing Data

## Related Skills

- `statistical-analysis` -- General statistical test selection and assumption checking
- `degenerate-input-filtering` -- Broader guide on filtering uninformative data before any statistical test
- `scikit-learn-machine-learning` -- Feature selection and preprocessing pipelines
