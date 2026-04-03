---
name: "statistical-significance-annotation"
description: "Guide for annotating statistical significance (p-value asterisk notation) on comparison plots. Covers standard notation conventions (ns, *, **, ***, ****), when to annotate, matplotlib bracket+asterisk implementation, and integration with seaborn box/violin/bar plots. Use when generating publication-ready comparison figures that need significance markers to support statistical claims made in the analysis."
license: "CC-BY-4.0"
---

# Statistical Significance Annotation on Plots

## Overview

Statistical significance annotations (asterisk notation) are visual markers placed on comparison plots to indicate the results of hypothesis tests between groups. They consist of brackets connecting two groups and asterisk symbols denoting the p-value range. Proper annotation ensures that the visual claims in a figure match the quantitative evidence, making plots publication-ready and scientifically rigorous. This guide covers the standard conventions, when and how to annotate, and a reusable matplotlib implementation.

## Key Concepts

### Standard Asterisk Notation

The widely adopted convention maps p-value ranges to asterisk symbols:

| Symbol | P-value Range | Meaning |
|--------|--------------|---------|
| ns | p > 0.05 | Not significant |
| \* | p <= 0.05 | Significant |
| \*\* | p <= 0.01 | Highly significant |
| \*\*\* | p <= 0.001 | Very highly significant |
| \*\*\*\* | p <= 0.0001 | Extremely significant |

The conversion function:

```python
def pvalue_to_asterisk(p: float) -> str:
    """Convert a p-value to standard asterisk notation."""
    if p <= 0.0001:
        return "****"
    elif p <= 0.001:
        return "***"
    elif p <= 0.01:
        return "**"
    elif p <= 0.05:
        return "*"
    else:
        return "ns"
```

### Adjusted vs Raw P-values

- **Single comparison** (one t-test): Use raw p-value.
- **Multiple comparisons** (pairwise tests across 3+ groups, multiple genes): Use adjusted p-values (FDR/Benjamini-Hochberg or Bonferroni). Annotating with raw p-values inflates significance.
- **Pre-computed results** (DESeq2 `padj`, ANOVA post-hoc): Use the adjusted values already provided.

### Comparison Selection

Not every pair of groups needs annotation. Select comparisons that:

- Directly support the claim made in the analysis text
- Are biologically meaningful (e.g., treatment vs control, not control-A vs control-B)
- Are limited in number to keep the figure readable (typically 1-5 per panel)

## Decision Framework

```
Does the plot compare groups?
├── No (scatter, heatmap, PCA, line trend) → Do NOT annotate
└── Yes (box, violin, bar, strip)
    ├── Does the analysis claim significance? → Annotate the claimed comparisons
    ├── Exploratory (no specific claim) → Annotate vs control only, or skip
    └── Too many groups (>6 pairwise) → Annotate key comparisons only
```

| Scenario | Annotate? | Which pairs |
|----------|-----------|-------------|
| DEG box plot: treatment vs control | Yes | Treatment vs Control |
| Multi-group ANOVA with post-hoc | Yes | Significant post-hoc pairs only |
| Gene expression across 10 cell types | Selectively | vs reference cell type only |
| PCA or UMAP | No | N/A |
| Heatmap or volcano plot | No | N/A |
| Correlation scatter | No | Report r and p in text/legend |
| Exploratory bar plot, no hypothesis | Optional | vs control if applicable |

## Best Practices

1. **Match annotations to text claims**: Every asterisk on the plot must correspond to a statistical test described in the analysis. Never annotate without having computed the test.
2. **Use adjusted p-values for multiple comparisons**: When testing more than one pair, always use FDR-corrected or Bonferroni-corrected p-values. State the correction method in the figure legend.
3. **Limit annotated pairs**: Annotate only comparisons relevant to the analysis conclusion. Over-annotating clutters the figure and dilutes focus.
4. **Position brackets clearly**: Place brackets above the data range with enough vertical offset to avoid overlapping with data points, error bars, or other brackets. Stack multiple brackets with consistent spacing.
5. **State the statistical test**: Always note the test used (t-test, Mann-Whitney U, Wilcoxon, ANOVA + Tukey HSD, etc.) in the figure title, caption, or legend.
6. **Include sample sizes**: Show n per group in the axis labels (e.g., "Control (n=30)") or figure legend.
7. **Use bold titles**: Set `fontweight='bold'` on figure titles for publication readiness.

## Common Pitfalls

1. **Annotating all pairwise comparisons in a multi-group plot**
   - *How to avoid*: Select only hypothesis-driven pairs. For k groups, k*(k-1)/2 pairs quickly becomes unreadable. Show vs control or specific contrasts only.

2. **Using raw p-values when multiple comparisons were performed**
   - *How to avoid*: Apply `statsmodels.stats.multitest.multipletests(pvals, method='fdr_bh')` or use adjusted p-values from upstream tools (DESeq2 `padj`).

3. **Bracket overlap with data or other brackets**
   - *How to avoid*: Use incremental vertical offset for stacked brackets. Start the first bracket above the maximum data value + error bar, then add a fixed offset for each additional bracket.

4. **Asterisks without stating which test was used**
   - *How to avoid*: Always include the test name in the plot title or annotation (e.g., "Mann-Whitney U test" or "Tukey HSD post-hoc").

5. **Inconsistent notation across figures**
   - *How to avoid*: Use the same `pvalue_to_asterisk()` function throughout the analysis. Define it once and reuse.

6. **Annotating "ns" on every non-significant pair**
   - *How to avoid*: Only show "ns" when the non-significance itself is a notable finding (e.g., showing no difference between two treatments). Omit ns annotations for pairs not being compared.

7. **Placing annotations below the data**
   - *How to avoid*: Always place brackets and asterisks above the compared groups, never below.

## Workflow

### Step 1: Compute Statistical Tests

Run the appropriate test and collect p-values before plotting:

```python
from scipy import stats

# Two-group comparison
stat, pval = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
# or for normal data:
stat, pval = stats.ttest_ind(group_a, group_b)

# Multi-group: ANOVA + post-hoc
from scipy.stats import f_oneway
stat, pval_anova = f_oneway(group_a, group_b, group_c)

# Post-hoc pairwise (if ANOVA significant)
from itertools import combinations
from statsmodels.stats.multitest import multipletests

pairs = list(combinations(["A", "B", "C"], 2))
groups = {"A": group_a, "B": group_b, "C": group_c}
raw_pvals = []
for g1, g2 in pairs:
    _, p = stats.mannwhitneyu(groups[g1], groups[g2], alternative='two-sided')
    raw_pvals.append(p)

# Adjust for multiple comparisons
rejected, adj_pvals, _, _ = multipletests(raw_pvals, method='fdr_bh')
```

### Step 2: Add Bracket Annotations to the Plot

Use this helper function to draw brackets with asterisks on any matplotlib axes:

```python
def add_significance_bracket(ax, x1, x2, y, p_value, dh=0.02, barh=0.015, fontsize=11):
    """Draw a significance bracket with asterisk notation between two x positions.

    Args:
        ax: matplotlib Axes object.
        x1, x2: x-axis positions of the two groups (0-indexed).
        y: y-coordinate for the bracket (top of bracket line).
        p_value: p-value for the comparison.
        dh: vertical offset above bracket for the text (in axes fraction).
        barh: height of the bracket tips (in axes fraction).
        fontsize: font size for the asterisk text.
    """
    asterisk = pvalue_to_asterisk(p_value)

    # Draw bracket: two tips and a connecting line
    ax.plot([x1, x1, x2, x2], [y - barh, y, y, y - barh],
            lw=1.2, color='black')
    # Place asterisk text centered above the bracket
    ax.text((x1 + x2) / 2, y + dh, asterisk,
            ha='center', va='bottom', fontsize=fontsize, fontweight='bold')
```

### Step 3: Integrate with Seaborn Plots

```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Example: box plot with significance annotation
fig, ax = plt.subplots(figsize=(6, 5))
sns.boxplot(data=df, x="group", y="value", ax=ax, palette="Set2")
sns.stripplot(data=df, x="group", y="value", ax=ax,
              color="black", alpha=0.4, size=3, jitter=True)

# Determine bracket y-position from data
y_max = df["value"].max()
y_range = df["value"].max() - df["value"].min()
offset = y_range * 0.08  # spacing between brackets

# Add brackets for each significant comparison
# pairs_with_pvals: list of (group1_idx, group2_idx, p_value)
pairs_with_pvals = [(0, 1, 0.003), (0, 2, 0.042)]

for i, (x1, x2, pval) in enumerate(pairs_with_pvals):
    bracket_y = y_max + offset * (i + 1)
    add_significance_bracket(ax, x1, x2, bracket_y, pval)

ax.set_title("Gene Expression by Treatment", fontweight='bold', fontsize=14)
ax.set_ylabel("Expression (log2 CPM)")
# Extend y-axis to fit brackets
ax.set_ylim(top=y_max + offset * (len(pairs_with_pvals) + 1.5))

plt.tight_layout()
plt.savefig("expression_comparison.png", dpi=150, bbox_inches='tight')
```

### Step 4: Annotating Grouped Bar Plots

For bar plots with error bars, position brackets above the error bars:

```python
fig, ax = plt.subplots(figsize=(7, 5))
bar_plot = sns.barplot(data=df, x="gene", y="fold_change", hue="condition",
                       ax=ax, palette="Set2", ci="sd", capsize=0.05)

# For grouped bars, calculate x positions manually
# Each gene has multiple bars offset by group
n_groups = df["condition"].nunique()
n_genes = df["gene"].nunique()
bar_width = 0.8 / n_groups

for gene_idx in range(n_genes):
    # x positions of the two bars within this gene group
    x1 = gene_idx - bar_width / 2
    x2 = gene_idx + bar_width / 2
    # Get the max value + error for this gene
    gene_data = df[df["gene"] == df["gene"].unique()[gene_idx]]
    y_top = gene_data["fold_change"].mean() + gene_data["fold_change"].std()
    p_val = pvals_per_gene[gene_idx]  # pre-computed

    if p_val <= 0.05:  # only annotate significant results
        add_significance_bracket(ax, x1, x2, y_top + 0.1, p_val)

ax.set_title("Fold Change by Condition", fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig("fold_change_comparison.png", dpi=150, bbox_inches='tight')
```

## Protocol Guidelines

1. **Always compute tests before plotting**: The statistical test should be run and results stored before any plotting code. Do not compute p-values inside the plotting block.
2. **Use consistent style**: Use the same `add_significance_bracket` function and `pvalue_to_asterisk` conversion across all figures in an analysis.
3. **Report test details in solution text**: When presenting the figure, state: the test used, number of samples per group, and whether p-values are adjusted.
4. **Adjust y-axis limits**: After adding brackets, extend the y-axis upper limit to prevent clipping. Use `ax.set_ylim(top=...)` or `ax.margins(y=0.15)`.
5. **For DESeq2/edgeR results**: Use `padj` (adjusted p-value) directly. Do not re-test the raw counts.

## Further Reading

- [Graphpad: How to report statistical significance](https://www.graphpad.com/support/faq/what-is-the-meaning-of--or--or--in-reports-of-statistical-significance-from-prism-or-instat/) — Asterisk notation conventions
- [Nature Methods: Points of Significance](https://www.nature.com/collections/qghhqm/pointsofsignificance) — Statistical best practices for figures
- [Weissgerber et al. (2015) Beyond Bar and Line Graphs](https://doi.org/10.1371/journal.pbio.1002128) — Why to show individual data points alongside statistical annotations

## Related Skills

- `seaborn-statistical-plots` — Seaborn plotting fundamentals; use this guide's annotation workflow on top of seaborn figures
- `scientific-visualization` — General scientific figure design principles
