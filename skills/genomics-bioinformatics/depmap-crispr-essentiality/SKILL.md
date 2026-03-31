---
name: depmap-crispr-essentiality
description: "Guide to DepMap CRISPR gene effect (Chronos) data analysis. Covers the critical sign convention for essentiality interpretation, per-gene NaN-safe Spearman correlation computation, and data loading/alignment patterns. For general NaN-safe correlation techniques see nan-safe-correlation. For upstream data quality filtering see degenerate-input-filtering."
license: CC-BY-4.0
---

# DepMap CRISPR Gene Effect Analysis Guide

## Overview

This guide covers the correct interpretation and analysis of DepMap CRISPR gene effect (Chronos) data. The most critical and common error in DepMap analyses is failing to negate the CRISPR scores when computing correlations with "essentiality." A secondary but equally damaging mistake is using bulk correlation shortcuts that mishandle per-gene NaN patterns. This guide provides the mandatory sign convention, the correct per-gene NaN-safe Spearman correlation implementation, and data loading/alignment procedures.

## Key Concepts

### DepMap CRISPR Score Convention

The CRISPR gene effect score (produced by the Chronos algorithm) quantifies how gene knockout affects cell viability:

- **Negative score**: gene knockout reduces cell viability -- the gene is **essential** for that cell line
- **Zero score**: no measurable effect on viability
- **Positive score**: gene knockout increases viability (rare, may indicate tumor-suppressive behavior)

The DepMap portal distributes these scores in the file `CRISPRGeneEffect.csv`. Each row is a cell line (DepMap ID, e.g., `ACH-000001`) and each column is a gene in the format `GENE_NAME (ENTREZ_ID)`, e.g., `A1BG (1)`.

### Essentiality Sign Interpretation

Because negative raw scores indicate essentiality, any analysis that asks about "essentiality" or "dependency" requires negating the raw CRISPR scores:

- "Correlation with essentiality" = correlation with `-CRISPRGeneEffect` (negated)
- "Higher essentiality" = more negative raw score = more positive negated score
- "Most essential gene" = gene with the most negative raw score

If you correlate expression with **raw** CRISPR scores and find 3 genes with correlation <= -0.6 and 0 genes with correlation >= 0.6, then the correct answer for "genes with strong positive correlation with essentiality" is **3**, not 0. The negative correlations with raw scores ARE the positive correlations with essentiality.

### Data Structure: CRISPRGeneEffect Format

The standard DepMap data files use a consistent structure:

- **Index**: DepMap cell line identifiers (`ACH-XXXXXX`)
- **Columns**: Gene identifiers in `GENE_NAME (ENTREZ_ID)` format
- **Values**: Floating-point scores (may contain NaN for genes not screened in a given cell line)
- **Companion files**: Expression data (`OmicsExpressionProteinCodingGenesTPMLogp1BatchCorrected.csv`) uses the same index/column format, enabling direct alignment

Different genes have different patterns of missing data across cell lines. This is because not all genes are screened in all cell lines, and quality control may remove specific gene-cell line combinations.

## Decision Framework

```
Question: How should I compute correlations with DepMap CRISPR data?
├── Does the question mention "essentiality" or "dependency"?
│   ├── Yes → Negate CRISPR scores before correlating (see Best Practices #1)
│   └── No (raw gene effect) → Use raw scores directly
├── How should I compute correlations?
│   ├── Per-gene correlation → scipy.stats.spearmanr in a loop (see Best Practices #2)
│   └── Matrix-wide correlation → AVOID; use per-gene loop instead
└── How should I handle missing data?
    ├── Pairwise NaN removal → CORRECT (see Best Practices #3)
    └── Global row/column dropping → INCORRECT; loses too much data
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Correlating expression with "essentiality" | Negate CRISPR scores, then per-gene Spearman | Sign convention requires negation; per-gene handles NaN correctly |
| Correlating expression with raw gene effect | Per-gene Spearman on raw scores | No negation needed, but NaN-safe per-gene loop still required |
| Ranking genes by essentiality across cell lines | Rank by most negative mean raw score | More negative = more essential across the panel |
| Identifying selectively essential genes | Compare score distributions across subgroups | Use per-subgroup mean/median of raw scores, then compare |
| Filtering genes before correlation | Require minimum 10 valid cell line pairs | Genes with too few observations yield unreliable correlations |

## Best Practices

1. **Always negate CRISPR scores when the analysis asks about "essentiality"**: The raw DepMap convention is that negative = essential. When a question or hypothesis refers to "essentiality," "dependency," or "gene importance," negate the scores so that higher values mean more essential. Explicitly state the sign convention in your results.

2. **Use scipy.stats.spearmanr per gene in a loop**: Bulk matrix shortcuts (`DataFrame.corrwith`, `DataFrame.rank().corrwith()`) handle NaN inconsistently across columns. The only reliable method is to compute Spearman correlation gene by gene using `scipy.stats.spearmanr` with pairwise-complete observations.

3. **Apply pairwise NaN removal, not global dropping**: Different genes have different missing-data patterns. Dropping rows globally (any NaN in any column) discards far too much data. Instead, for each gene, mask out only the cell lines where either the expression or CRISPR value is NaN.

4. **Set a minimum valid-pair threshold**: Genes with very few non-NaN cell line pairs produce unreliable correlation estimates. Require at least 10 (preferably 20+) valid pairs before computing a correlation. Skip genes below this threshold.

5. **Report NaN summary before analysis**: Before computing correlations, print the total NaN count per dataset, the number of common cell lines, and the number of common genes. This provides an audit trail and helps catch data loading errors early.

6. **Verify dataset alignment before computation**: Always intersect cell line IDs and gene columns between datasets before analysis. Misaligned indices produce silent errors -- correlations computed on mismatched rows are meaningless.

7. **State the sign convention explicitly in results**: When reporting correlation results, always include a statement like "CRISPR scores were negated so that positive values represent higher essentiality." This prevents downstream misinterpretation.

## Common Pitfalls

1. **Forgetting to negate CRISPR scores for essentiality analysis**: The raw DepMap score convention (negative = essential) is counterintuitive. Omitting the negation reverses every correlation sign, leading to completely inverted conclusions.
   - *How to avoid*: Always check whether the analysis question uses the word "essentiality" or "dependency." If so, negate the CRISPR scores. Add a comment in the code: `# Negate: in DepMap, negative = essential`.

2. **Using bulk DataFrame correlation methods**: Methods like `DataFrame.corrwith(method='spearman')` or `DataFrame.rank().corrwith()` silently mishandle NaN values, potentially shifting correlations enough to push genes above or below significance thresholds.
   - *How to avoid*: Always use a per-gene loop with `scipy.stats.spearmanr`. See the reference implementation in the Workflow section below.

3. **Dropping rows globally instead of pairwise**: Calling `dropna()` on the entire DataFrame before correlation removes all cell lines that have any NaN in any gene, drastically reducing sample size.
   - *How to avoid*: Apply NaN masking inside the per-gene loop: `mask = ~(np.isnan(x) | np.isnan(y))`. This preserves the maximum number of observations per gene.

4. **Not checking for sufficient valid pairs**: Computing Spearman correlation on fewer than 10 observations produces unstable, unreliable estimates that may appear significant by chance.
   - *How to avoid*: Add a guard clause: `if mask.sum() < 10: continue`. Adjust the threshold upward (e.g., 20) for more conservative analysis.

5. **Misinterpreting correlation signs without stated convention**: Reporting "positive correlation" without stating whether CRISPR scores were negated leaves results ambiguous. Reviewers cannot tell if "positive" means "higher expression associates with more essential" or "less essential."
   - *How to avoid*: Always include a sentence in the results section stating the sign convention used. For example: "CRISPR scores were negated so that positive correlation indicates higher expression is associated with greater essentiality."

6. **Failing to align datasets before computation**: Expression and CRISPR datasets may have different cell lines or different gene sets. Computing correlations without explicit alignment can silently match wrong rows or produce index errors.
   - *How to avoid*: Always compute `common_lines = expr.index.intersection(crispr.index)` and `common_genes = expr.columns.intersection(crispr.columns)`, then subset both DataFrames before any computation.

7. **Ignoring the gene column format**: DepMap gene columns use the format `GENE_NAME (ENTREZ_ID)`. Attempting to match against plain gene symbols (e.g., `TP53` instead of `TP53 (7157)`) will produce empty intersections.
   - *How to avoid*: Inspect column formats with `df.columns[:5]` before attempting any join or intersection. Parse gene names if needed: `df.columns.str.extract(r'^(.+?)\s*\(')[0]`.

## Workflow

1. **Step 1: Load DepMap data**

   ```python
   import pandas as pd

   # Load CRISPR gene effect data
   crispr = pd.read_csv('CRISPRGeneEffect.csv', index_col=0)

   # Load expression data
   expr = pd.read_csv(
       'OmicsExpressionProteinCodingGenesTPMLogp1BatchCorrected.csv',
       index_col=0
   )

   # Column format: "GENE_NAME (ENTREZ_ID)" e.g., "A1BG (1)"
   # Index: DepMap cell line IDs e.g., "ACH-000001"
   ```

2. **Step 2: Align datasets**

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

3. **Step 3: Report NaN summary**

   ```python
   expr_nan = expr_aligned.isna().sum().sum()
   crispr_nan = crispr_aligned.isna().sum().sum()
   print(f"Expression NaN count: {expr_nan}")
   print(f"CRISPR NaN count: {crispr_nan}")
   ```

4. **Step 4: Negate CRISPR scores if computing essentiality correlations**

   ```python
   # Negate: in DepMap, negative raw score = essential
   # After negation, positive = essential
   essentiality = -crispr_aligned
   ```

5. **Step 5: Compute per-gene NaN-safe Spearman correlation**

   ```python
   from scipy.stats import spearmanr
   import numpy as np

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

6. **Step 6: Apply threshold and report results**

   ```python
   correlations = compute_per_gene_spearman(expr_aligned, crispr_aligned,
                                            negate_crispr=True)

   threshold = 0.6
   strong_positive = correlations[correlations >= threshold]
   strong_negative = correlations[correlations <= -threshold]

   print(f"Genes with correlation >= {threshold}: {len(strong_positive)}")
   print(f"Genes with correlation <= -{threshold}: {len(strong_negative)}")
   print(f"\nNote: CRISPR scores were negated so that positive correlation")
   print(f"indicates higher expression associated with greater essentiality.")
   ```

7. **Step 7: Validate -- check for anti-patterns**

   Verify that none of these bulk shortcuts were used anywhere in the analysis:

   ```python
   # WRONG: Bulk rank-then-correlate shortcut
   ranked_expr = expression_df.rank()
   ranked_crispr = crispr_df.rank()
   correlations = ranked_expr.corrwith(ranked_crispr)  # NaN handling is unreliable

   # WRONG: Bulk corrwith with method='spearman'
   correlations = expression_df.corrwith(crispr_df, method='spearman')  # Same issue
   ```

   If any of these patterns appear in the code, replace them with the per-gene loop from Step 5.

## Further Reading

- [DepMap Portal](https://depmap.org/portal/) -- Primary data source for CRISPR gene effect scores, expression data, and other omics datasets across cancer cell lines
- [Dempster et al. (2019) -- Chronos algorithm](https://doi.org/10.1038/s41467-019-09612-6) -- Original paper describing the Chronos computational method for estimating gene effect from CRISPR screen data
- [DepMap Documentation and Data Downloads](https://depmap.org/portal/download/all/) -- Detailed file format descriptions, release notes, and download links for all DepMap datasets

## Related Skills

- `nan-safe-correlation` -- General techniques for NaN-safe correlation computation across omics datasets; this guide applies those principles specifically to DepMap CRISPR data
- `degenerate-input-filtering` -- Upstream data quality filtering to remove low-variance or degenerate features before correlation analysis; recommended as a preprocessing step before DepMap essentiality correlation
