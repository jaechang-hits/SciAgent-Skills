---
name: depmap-crispr-essentiality
description: "Mandatory sign convention for DepMap CRISPR gene effect data. Covers essentiality interpretation, correlation direction, and per-gene NaN-safe Spearman correlation computation."
license: CC-BY-4.0
compatibility: Python 3.10+
metadata:
  authors: HITS
  version: "1.0"
---

# DepMap CRISPR Gene Effect Analysis Guide

## Overview

This guide covers the correct interpretation and analysis of DepMap CRISPR gene effect (Chronos) data. The most critical and common error is failing to negate the CRISPR scores when computing correlations with "essentiality." This guide also addresses NaN-safe per-gene correlation computation.

---

## Rule 1 (MANDATORY): Negate CRISPR Scores for Essentiality

**CRITICAL: In DepMap CRISPRGeneEffect data, negative values mean the gene is essential (knockout kills the cell). When a question refers to "essentiality", you MUST negate the CRISPR scores.**

### Why This Matters

The CRISPR gene effect score convention is:
- **Negative score** = gene knockout reduces cell viability = gene is **essential**
- **Zero score** = no effect on viability
- **Positive score** = gene knockout increases viability (rare)

Therefore:
- "Correlation with essentiality" = correlation with `-CRISPRGeneEffect` (negated)
- "Higher essentiality" = more negative raw score = more positive negated score

### Common Mistake

```python
# WRONG: Correlating expression with raw CRISPR scores
# This gives the OPPOSITE sign -- positive correlation here means
# "higher expression correlates with LESS essential"
corr = spearmanr(expression, crispr_raw)

# CORRECT: Negate CRISPR scores to represent essentiality
essentiality = -crispr_raw
corr = spearmanr(expression, essentiality)
```

### Practical Impact

If you correlate expression with raw CRISPR scores and find:
- 0 genes with correlation >= 0.6
- 3 genes with correlation <= -0.6

Then the correct answer for "genes with strong positive correlation with essentiality" is **3**, not 0. The negative correlations with raw scores ARE the positive correlations with essentiality.

---

## Rule 2 (MANDATORY): Per-Gene NaN-Safe Spearman Correlation

**CRITICAL: Use `scipy.stats.spearmanr` per gene in a loop. Do NOT use bulk matrix shortcuts.**

### Why This Matters

Different genes have different patterns of missing data across cell lines. Bulk correlation methods handle NaN inconsistently:

- `DataFrame.rank()` then `corrwith()` -- silently mishandles NaN, may drop rows globally
- `DataFrame.corrwith(method='spearman')` -- inconsistent NaN handling per column
- These shortcuts can shift correlations enough to push genes above or below thresholds

### Correct Implementation

```python
from scipy.stats import spearmanr
import numpy as np
import pandas as pd

def compute_per_gene_spearman(expression_df, crispr_df, negate_crispr=True):
    """Compute Spearman correlation per gene with proper NaN handling.

    Args:
        expression_df: DataFrame (cell_lines x genes)
        crispr_df: DataFrame (cell_lines x genes)
        negate_crispr: If True, negate CRISPR scores to represent essentiality

    Returns:
        Series of Spearman correlations indexed by gene name
    """
    # Align cell lines and genes
    common_lines = expression_df.index.intersection(crispr_df.index)
    common_genes = expression_df.columns.intersection(crispr_df.columns)

    expr = expression_df.loc[common_lines, common_genes]
    crispr = crispr_df.loc[common_lines, common_genes]

    if negate_crispr:
        crispr = -crispr

    # Print NaN summary BEFORE analysis
    expr_nan = expr.isna().sum().sum()
    crispr_nan = crispr.isna().sum().sum()
    print(f"Expression NaN count: {expr_nan}")
    print(f"CRISPR NaN count: {crispr_nan}")
    print(f"Common cell lines: {len(common_lines)}")
    print(f"Common genes: {len(common_genes)}")

    # Per-gene Spearman correlation with pairwise NaN removal
    correlations = {}
    for gene in common_genes:
        x = expr[gene].values
        y = crispr[gene].values

        # Remove pairs where either value is NaN
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 10:  # Skip genes with too few valid pairs
            continue

        rho, pval = spearmanr(x[mask], y[mask])
        correlations[gene] = rho

    return pd.Series(correlations).sort_values(ascending=False)
```

### Anti-Pattern (DO NOT DO THIS)

```python
# WRONG: Bulk rank-then-correlate shortcut
ranked_expr = expression_df.rank()
ranked_crispr = crispr_df.rank()
correlations = ranked_expr.corrwith(ranked_crispr)  # NaN handling is unreliable

# WRONG: Bulk corrwith with method='spearman'
correlations = expression_df.corrwith(crispr_df, method='spearman')  # Same issue
```

---

## Rule 3: Data Loading and Alignment

### Loading DepMap Data

```python
import pandas as pd

# Load CRISPR gene effect data
crispr = pd.read_csv('CRISPRGeneEffect.csv', index_col=0)

# Load expression data
expr = pd.read_csv('OmicsExpressionProteinCodingGenesTPMLogp1BatchCorrected.csv', index_col=0)

# Column format: "GENE_NAME (ENTREZ_ID)" e.g., "A1BG (1)"
# Index: DepMap cell line IDs e.g., "ACH-000001"
```

### Aligning Datasets

```python
# Find common cell lines and genes
common_lines = crispr.index.intersection(expr.index)
common_genes = crispr.columns.intersection(expr.columns)

print(f"Common cell lines: {len(common_lines)}")
print(f"Common genes: {len(common_genes)}")

# Subset to common
crispr_aligned = crispr.loc[common_lines, common_genes]
expr_aligned = expr.loc[common_lines, common_genes]
```

---

## Checklist

Before reporting DepMap CRISPR correlation results, verify:

- [ ] CRISPR scores were negated when the question asks about "essentiality"
- [ ] Spearman correlation was computed per gene using `scipy.stats.spearmanr`
- [ ] NaN values were reported before analysis (total count per dataset)
- [ ] Pairwise NaN removal was used (not global row/column dropping)
- [ ] Genes with too few valid data points were excluded
- [ ] The sign convention is explicitly stated in the answer
