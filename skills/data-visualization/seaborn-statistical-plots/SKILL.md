---
name: "seaborn-statistical-plots"
description: "Statistical visualization library built on matplotlib with native pandas DataFrame support. Automatic aggregation, confidence intervals, and grouping for distribution plots (histplot, kdeplot), categorical comparisons (boxplot, violinplot, stripplot), relational plots (scatterplot, lineplot), regression plots (regplot, lmplot), matrix plots (heatmap, clustermap), and multi-variable grids (pairplot, jointplot, FacetGrid). Use seaborn for statistical summaries with minimal code; use matplotlib for fine-grained figure control; use plotly for interactive HTML output."
license: BSD-3-Clause
---

# Seaborn — Statistical Plots

## Overview

Seaborn is a Python library for statistical data visualization built on top of matplotlib. It works directly with pandas DataFrames, automatically handles grouping by categorical variables, computes confidence intervals and kernel density estimates, and produces attractive publication-ready figures with minimal configuration. Seaborn separates axes-level functions (embeddable in custom layouts) from figure-level functions (with built-in faceting), enabling both quick exploratory analysis and structured multi-panel figures.

## When to Use

- Comparing gene expression, protein abundance, or measurement distributions across experimental conditions (treatment vs. control, cell lines, time points)
- Generating grouped box plots, violin plots, or strip plots to show both summary statistics and individual data points simultaneously
- Visualizing pairwise correlations in multi-gene or multi-feature datasets as annotated heatmaps
- Plotting regression fits with confidence bands between continuous variables (e.g., cell viability vs. drug concentration)
- Faceting a single plot type across multiple sample subsets, tissue types, or experimental batches in one call
- Rapid exploratory analysis of a new dataset using `pairplot` to survey all pairwise relationships at once
- Use `matplotlib` directly when you need pixel-level control over figure elements, complex mixed-type layouts, or non-statistical custom plots
- Use `plotly` when the output must be interactive (hover tooltips, zoom, pan) or embedded in a web application

## Prerequisites

- **Python packages**: `seaborn>=0.13`, `matplotlib`, `pandas`, `numpy`
- **Data requirements**: Pandas DataFrame in long-form (tidy) format; each observation is a row, each variable is a column
- **Environment**: Standard Python environment; no GPU or special hardware required

```bash
pip install "seaborn>=0.13" matplotlib pandas numpy scipy
```

## Quick Start

```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Simulate gene expression across conditions
rng = np.random.default_rng(42)
df = pd.DataFrame({
    "gene":      ["BRCA1"] * 60 + ["TP53"] * 60,
    "condition": ["control", "treated"] * 60,
    "log2_expr": np.concatenate([
        rng.normal(5.2, 0.8, 60),
        rng.normal(6.1, 0.9, 60),
    ])
})

sns.set_theme(style="ticks", context="notebook")
sns.boxplot(data=df, x="gene", y="log2_expr", hue="condition", palette="Set2")
plt.ylabel("log2 Expression")
plt.title("Gene Expression by Condition")
plt.tight_layout()
plt.savefig("quickstart_boxplot.png", dpi=150)
print("Saved quickstart_boxplot.png")
```

## Core API

### 1. Distribution Plots

Visualize univariate distributions and compare them across groups. `histplot` bins data; `kdeplot` fits a smooth density estimate; `displot` is the figure-level wrapper that adds faceting.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(0)
n = 200
df = pd.DataFrame({
    "log2_tpm":  np.concatenate([rng.normal(4.5, 1.1, n), rng.normal(6.0, 1.3, n)]),
    "sample":    ["tumor"] * n + ["normal"] * n,
})

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Histogram with density normalization and stacked hue groups
sns.histplot(data=df, x="log2_tpm", hue="sample", stat="density",
             multiple="stack", bins=30, ax=axes[0])
axes[0].set_title("Histogram (stacked)")

# KDE with fill — bandwidth controlled by bw_adjust
sns.kdeplot(data=df, x="log2_tpm", hue="sample", fill=True,
            bw_adjust=0.8, alpha=0.4, ax=axes[1])
axes[1].set_title("KDE (filled)")

# ECDF — useful for comparing cumulative distributions
sns.ecdfplot(data=df, x="log2_tpm", hue="sample", ax=axes[2])
axes[2].set_title("ECDF")

plt.tight_layout()
plt.savefig("distributions.png", dpi=150)
print("Saved distributions.png")
```

```python
# Bivariate KDE: joint distribution of two continuous variables
rng = np.random.default_rng(1)
df2 = pd.DataFrame({
    "log2_rna": rng.normal(5.5, 1.2, 300),
    "log2_prot": rng.normal(4.8, 1.0, 300) + 0.6 * rng.normal(5.5, 1.2, 300),
})
sns.kdeplot(data=df2, x="log2_rna", y="log2_prot",
            fill=True, levels=8, thresh=0.05, cmap="Blues")
plt.xlabel("log2 RNA (TPM)")
plt.ylabel("log2 Protein (iBAQ)")
plt.title("RNA–Protein Correlation Density")
plt.tight_layout()
plt.savefig("bivariate_kde.png", dpi=150)
print("Saved bivariate_kde.png")
```

### 2. Categorical Plots

Compare distributions or aggregated statistics across categorical groups. Axes-level functions (`boxplot`, `violinplot`, `stripplot`, `swarmplot`, `barplot`) accept an `ax=` parameter for embedding in custom layouts.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(2)
conditions = ["DMSO", "Drug A 1uM", "Drug A 10uM", "Drug B 1uM", "Drug B 10uM"]
df = pd.DataFrame({
    "condition": np.repeat(conditions, 30),
    "viability": np.concatenate([
        rng.normal(100, 5, 30),
        rng.normal(92, 7, 30),
        rng.normal(65, 10, 30),
        rng.normal(88, 8, 30),
        rng.normal(45, 12, 30),
    ])
})

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Box plot — shows quartiles and outliers
sns.boxplot(data=df, x="condition", y="viability",
            palette="husl", width=0.5, ax=axes[0])
axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=30, ha="right")
axes[0].set_title("Box Plot")

# Violin — KDE shape + inner quartile lines
sns.violinplot(data=df, x="condition", y="viability",
               inner="quart", palette="muted", ax=axes[1])
axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=30, ha="right")
axes[1].set_title("Violin Plot")

# Strip plot overlaid on box — shows all individual points
sns.boxplot(data=df, x="condition", y="viability",
            palette="pastel", width=0.5, ax=axes[2])
sns.stripplot(data=df, x="condition", y="viability",
              color="black", alpha=0.4, size=3, jitter=True, ax=axes[2])
axes[2].set_xticklabels(axes[2].get_xticklabels(), rotation=30, ha="right")
axes[2].set_title("Box + Strip")

plt.tight_layout()
plt.savefig("categorical.png", dpi=150)
print("Saved categorical.png")
```

```python
# Bar plot with mean ± 95% CI and individual points (swarm)
fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=df, x="condition", y="viability",
            estimator="mean", errorbar="ci", palette="Set3", ax=ax)
sns.swarmplot(data=df, x="condition", y="viability",
              color="black", size=3, alpha=0.5, ax=ax)
ax.set_ylabel("Cell Viability (%)")
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
plt.tight_layout()
plt.savefig("barswarm.png", dpi=150)
print("Saved barswarm.png")
```

### 3. Relational Plots

Visualize relationships between continuous variables. `scatterplot` and `lineplot` are axes-level; `relplot` is the figure-level wrapper that supports `col` and `row` faceting.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(3)
n = 150
df = pd.DataFrame({
    "molecular_weight": rng.uniform(200, 800, n),
    "logP":             rng.uniform(-2, 6, n),
    "pIC50":            rng.normal(6.5, 1.2, n),
    "target_class":     rng.choice(["kinase", "GPCR", "protease"], n),
    "pass_lipinski":    rng.choice(["yes", "no"], n, p=[0.7, 0.3]),
})

# Scatter with hue (categorical color) + size (continuous) + style (marker)
sns.scatterplot(data=df, x="molecular_weight", y="pIC50",
                hue="target_class", size="logP", style="pass_lipinski",
                sizes=(30, 120), alpha=0.7)
plt.xlabel("Molecular Weight (Da)")
plt.ylabel("pIC50")
plt.title("Compound Bioactivity by Target Class")
plt.tight_layout()
plt.savefig("relational_scatter.png", dpi=150)
print("Saved relational_scatter.png")
```

```python
# Line plot with automatic mean aggregation and SD error band across replicates
timepoints = [0, 1, 2, 4, 8, 24]
groups = ["untreated", "low_dose", "high_dose"]
rows = []
for grp, base in zip(groups, [100.0, 95.0, 80.0]):
    for tp in timepoints:
        for _ in range(5):  # 5 replicates
            rows.append({"timepoint_h": tp, "group": grp,
                         "confluency": base * np.exp(-0.02 * tp * (1 + rng.normal(0, 0.1)))})
time_df = pd.DataFrame(rows)

sns.lineplot(data=time_df, x="timepoint_h", y="confluency",
             hue="group", style="group", errorbar="sd", markers=True, dashes=False)
plt.xlabel("Time (h)")
plt.ylabel("Confluency (%)")
plt.title("Cell Growth Inhibition (mean ± SD, n=5)")
plt.tight_layout()
plt.savefig("lineplot.png", dpi=150)
print("Saved lineplot.png")
```

### 4. Regression Plots

Fit linear (or polynomial/lowess) models and visualize them with confidence bands. `regplot` is axes-level; `lmplot` is figure-level with faceting support.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(4)
n = 120
tumor_size = rng.uniform(0.5, 6.0, n)
survival_months = 40 - 5 * tumor_size + rng.normal(0, 4, n)
grade = rng.choice(["low", "high"], n, p=[0.5, 0.5])
df = pd.DataFrame({"tumor_size_cm": tumor_size,
                   "survival_months": survival_months,
                   "grade": grade})

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Linear regression with 95% CI band
sns.regplot(data=df, x="tumor_size_cm", y="survival_months",
            ci=95, scatter_kws={"alpha": 0.4, "s": 25}, ax=axes[0])
axes[0].set_title("Linear Regression (95% CI)")

# Residuals plot — check for homoscedasticity
sns.residplot(data=df, x="tumor_size_cm", y="survival_months",
              scatter_kws={"alpha": 0.4, "s": 25}, ax=axes[1])
axes[1].axhline(0, color="red", linestyle="--", linewidth=1)
axes[1].set_title("Residuals vs Fitted")

plt.tight_layout()
plt.savefig("regression.png", dpi=150)
print("Saved regression.png")
```

```python
# lmplot — figure-level: separate regression lines per grade (hue) + facets
g = sns.lmplot(data=df, x="tumor_size_cm", y="survival_months",
               hue="grade", col="grade", ci=95,
               scatter_kws={"alpha": 0.4}, height=4, aspect=1.1)
g.set_axis_labels("Tumor Size (cm)", "Survival (months)")
g.set_titles("{col_name} grade")
g.savefig("lmplot_faceted.png", dpi=150)
print("Saved lmplot_faceted.png")
```

### 5. Matrix Plots

Visualize rectangular data as color-encoded matrices. `heatmap` is axes-level; `clustermap` is figure-level and applies hierarchical clustering to rows and columns.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(5)
genes = [f"GENE{i}" for i in range(1, 9)]
samples = [f"S{i}" for i in range(1, 7)]

# Simulate log2 fold-change matrix (rows=genes, cols=samples)
lfc = pd.DataFrame(
    rng.normal(0, 1.5, size=(8, 6)),
    index=genes, columns=samples
)
# Inject a pattern: first 3 genes up in samples 1-3, down in 4-6
lfc.iloc[:3, :3] += 2.5
lfc.iloc[:3, 3:] -= 2.5

# Correlation heatmap of numeric features
df_num = pd.DataFrame(
    rng.standard_normal((80, 5)),
    columns=["GeneA", "GeneB", "GeneC", "GeneD", "GeneE"]
)
df_num["GeneB"] = df_num["GeneA"] * 0.85 + rng.normal(0, 0.3, 80)
corr = df_num.corr()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
            center=0, square=True, linewidths=0.5, ax=axes[0])
axes[0].set_title("Pearson Correlation Heatmap")

sns.heatmap(lfc, cmap="RdBu_r", center=0, annot=True, fmt=".1f",
            linewidths=0.3, cbar_kws={"label": "log2FC"}, ax=axes[1])
axes[1].set_title("log2 Fold Change Matrix")

plt.tight_layout()
plt.savefig("heatmaps.png", dpi=150)
print("Saved heatmaps.png")
```

```python
# Clustermap with hierarchical clustering and row/column color annotations
rng = np.random.default_rng(6)
n_genes, n_samples = 30, 16
expr = pd.DataFrame(
    rng.lognormal(mean=2.0, sigma=1.2, size=(n_genes, n_samples)),
    index=[f"GENE{i:03d}" for i in range(n_genes)],
    columns=[f"{'T' if i < 8 else 'N'}{i:02d}" for i in range(n_samples)]
)

# Column annotation colors (tumor vs normal)
col_colors = ["#D32F2F" if c.startswith("T") else "#1976D2" for c in expr.columns]

g = sns.clustermap(
    np.log2(expr + 1),
    cmap="viridis",
    standard_scale=0,          # z-score across rows (genes)
    method="ward",
    metric="euclidean",
    col_colors=col_colors,
    figsize=(12, 10),
    linewidths=0,
    cbar_pos=(0.02, 0.8, 0.03, 0.15),
    cbar_kws={"label": "Row z-score"},
)
g.ax_heatmap.set_xlabel("Sample")
g.ax_heatmap.set_ylabel("Gene")
plt.savefig("clustermap.png", dpi=150, bbox_inches="tight")
print("Saved clustermap.png")
```

### 6. Multi-Variable Grids

Survey all pairwise relationships with `pairplot` or display a bivariate distribution with marginals using `jointplot`. For fully custom grid layouts, use `FacetGrid` directly.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
n = 60
df = pd.DataFrame({
    "cell_area":      rng.normal(350, 60, n * 3),
    "nucleus_area":   rng.normal(90, 15, n * 3),
    "mean_intensity": rng.exponential(500, n * 3),
    "aspect_ratio":   np.abs(rng.normal(1.3, 0.3, n * 3)),
    "cell_type":      (["HeLa"] * n + ["MCF7"] * n + ["A549"] * n),
})

# Pairplot — matrix of pairwise scatter + KDE on diagonal
g = sns.pairplot(df, hue="cell_type", corner=True,
                 diag_kind="kde", plot_kws={"alpha": 0.5, "s": 20})
g.savefig("pairplot.png", dpi=150)
print("Saved pairplot.png")
```

```python
# Jointplot — bivariate KDE with marginal histograms
g = sns.jointplot(data=df, x="cell_area", y="nucleus_area",
                  hue="cell_type", kind="scatter",
                  marginal_kws={"fill": True, "alpha": 0.3})
g.set_axis_labels("Cell Area (µm²)", "Nucleus Area (µm²)")
g.savefig("jointplot.png", dpi=150)
print("Saved jointplot.png")
```

```python
# FacetGrid — custom layout: KDE of mean_intensity per cell type
g = sns.FacetGrid(df, col="cell_type", height=3.5, aspect=1.1,
                  sharey=False)
g.map(sns.histplot, "mean_intensity", bins=20, kde=True, color="steelblue")
g.set_axis_labels("Mean Intensity (AU)", "Count")
g.set_titles("{col_name}")
g.tight_layout()
g.savefig("facetgrid_intensity.png", dpi=150)
print("Saved facetgrid_intensity.png")
```

## Key Concepts

### Figure-Level vs Axes-Level Functions

Seaborn has two tiers of functions with different return types and composability:

| Feature | Axes-Level | Figure-Level |
|---------|-----------|--------------|
| **Examples** | `scatterplot`, `histplot`, `boxplot`, `heatmap`, `regplot` | `relplot`, `displot`, `catplot`, `lmplot` |
| **Returns** | `matplotlib.axes.Axes` | `FacetGrid` / `JointGrid` / `PairGrid` |
| **Faceting** | Manual (create subplots yourself) | Built-in (`col=`, `row=` params) |
| **Sizing** | `figsize=` on parent figure | `height=` + `aspect=` per facet panel |
| **Placement** | `ax=` parameter | Cannot be placed in an existing axes |
| **Saving** | `plt.savefig(...)` | `g.savefig(...)` |
| **Use when** | Combining different plot types in one figure | Quick multi-panel exploratory views |

```python
# Axes-level: place in a pre-allocated subplot grid
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sns.violinplot(data=df, x="cell_type", y="cell_area", ax=axes[0])
sns.scatterplot(data=df, x="cell_area", y="nucleus_area", hue="cell_type", ax=axes[1])
```

### Long-Form vs Wide-Form Data

Seaborn semantic mappings (`hue`, `size`, `style`) require **long-form (tidy) data** where each variable is a column and each observation is a row. Some functions (`heatmap`, `clustermap`, `lineplot`) also accept wide-form.

```python
# Wide-form: unsuitable for hue/style mappings
#   sample_A  sample_B  sample_C
# 0      5.1       6.2       4.8

# Long-form (preferred): melt wide → long
wide = pd.DataFrame({"sampleA": [5.1, 4.3], "sampleB": [6.2, 5.9]})
long = wide.melt(var_name="sample", value_name="log2_expr")
# → columns: sample, log2_expr
```

## Common Workflows

### Workflow 1: Differential Expression Scatter with Significance Thresholds

**Goal**: Visualize log2 fold-change vs -log10 p-value (volcano-style) with significance annotations, colored by regulation status, and labeled top hits.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 500
lfc   = rng.normal(0, 1.5, n)
pvals = 10 ** (-rng.exponential(1.5, n))        # skewed toward low significance
pvals = np.clip(pvals, 1e-20, 1.0)
genes = [f"GENE{i:04d}" for i in range(n)]

df_de = pd.DataFrame({"gene": genes, "log2fc": lfc, "pvalue": pvals})
df_de["neg_log10_p"] = -np.log10(df_de["pvalue"])

# Classify regulation status
lfc_thresh = 1.0
padj_thresh = 0.05
df_de["sig"] = "NS"
df_de.loc[(df_de["log2fc"] >  lfc_thresh) & (df_de["pvalue"] < padj_thresh), "sig"] = "Up"
df_de.loc[(df_de["log2fc"] < -lfc_thresh) & (df_de["pvalue"] < padj_thresh), "sig"] = "Down"

palette = {"NS": "#AAAAAA", "Up": "#D32F2F", "Down": "#1976D2"}

sns.set_theme(style="ticks", context="paper", font_scale=1.1)
fig, ax = plt.subplots(figsize=(8, 6))

sns.scatterplot(data=df_de, x="log2fc", y="neg_log10_p",
                hue="sig", palette=palette,
                alpha=0.6, s=18, linewidth=0, ax=ax)

# Threshold lines
ax.axhline(-np.log10(padj_thresh), color="black", linestyle="--", linewidth=0.8)
ax.axvline( lfc_thresh,            color="black", linestyle="--", linewidth=0.8)
ax.axvline(-lfc_thresh,            color="black", linestyle="--", linewidth=0.8)

# Label top 5 most significant genes per direction
for direction in ["Up", "Down"]:
    top = df_de[df_de["sig"] == direction].nlargest(5, "neg_log10_p")
    for _, row in top.iterrows():
        ax.text(row["log2fc"], row["neg_log10_p"] + 0.3, row["gene"],
                fontsize=6, ha="center", va="bottom",
                color=palette[direction])

# Annotation counts
n_up   = (df_de["sig"] == "Up").sum()
n_down = (df_de["sig"] == "Down").sum()
ax.set_title(f"Volcano Plot  |  Up: {n_up}  Down: {n_down}")
ax.set_xlabel("log2 Fold Change")
ax.set_ylabel("-log10 p-value")
sns.despine(trim=True)
plt.tight_layout()
plt.savefig("volcano_plot.png", dpi=300, bbox_inches="tight")
print(f"Volcano: {n_up} up, {n_down} down — saved volcano_plot.png")
```

### Workflow 2: Multi-Condition Comparison with Grouped Violin + Strip Plots

**Goal**: Compare gene expression (or any continuous measurement) across multiple treatments and time points, showing full distributions plus individual replicates.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(99)
genes    = ["BRCA1", "TP53", "EGFR"]
treats   = ["DMSO", "Drug A", "Drug B"]
timepoints = ["6h", "24h", "48h"]
rows = []
for gene in genes:
    base_expr = {"BRCA1": 7.5, "TP53": 6.2, "EGFR": 8.1}[gene]
    for treat in treats:
        treat_shift = {"DMSO": 0.0, "Drug A": -0.8, "Drug B": 0.6}[treat]
        for tp in timepoints:
            tp_shift = {"6h": 0.0, "24h": 0.3, "48h": 0.6}[tp]
            for _ in range(12):
                rows.append({
                    "gene":      gene,
                    "treatment": treat,
                    "timepoint": tp,
                    "log2_expr": base_expr + treat_shift + tp_shift + rng.normal(0, 0.5),
                })
df_mc = pd.DataFrame(rows)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
g = sns.catplot(
    data=df_mc,
    x="timepoint", y="log2_expr",
    hue="treatment",
    col="gene",
    kind="violin",
    inner="quart",
    dodge=True,
    palette="Set2",
    height=4, aspect=0.9,
    col_order=genes,
    order=timepoints,
)

# Overlay individual points
for ax in g.axes.flat:
    gene_label = ax.get_title()
    gene_name  = gene_label.split(" = ")[-1] if " = " in gene_label else gene_label
    subset = df_mc[df_mc["gene"] == gene_name]
    sns.stripplot(
        data=subset,
        x="timepoint", y="log2_expr",
        hue="treatment",
        dodge=True,
        jitter=True,
        size=2.5,
        alpha=0.4,
        palette="dark:black",
        order=timepoints,
        legend=False,
        ax=ax,
    )

g.set_axis_labels("Timepoint", "log2 Expression")
g.set_titles("{col_name}")
g.add_legend(title="Treatment")
sns.despine(trim=True)
g.tight_layout()
g.savefig("multigroup_violin.png", dpi=300, bbox_inches="tight")
print("Saved multigroup_violin.png")
```

### Workflow 3: Pairwise Feature Exploration for Cell Morphology

**Goal**: Quickly survey pairwise relationships in a multi-feature cell morphology dataset using `pairplot`, then examine one key pair with a `jointplot`.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(12)
n_per_type = 80
df_morph = pd.DataFrame({
    "cell_area_um2":    np.concatenate([rng.normal(320, 50, n_per_type),
                                        rng.normal(420, 70, n_per_type),
                                        rng.normal(280, 40, n_per_type)]),
    "nucleus_area_um2": np.concatenate([rng.normal(85, 12, n_per_type),
                                        rng.normal(110, 18, n_per_type),
                                        rng.normal(75, 10, n_per_type)]),
    "eccentricity":     np.abs(np.concatenate([rng.normal(0.6, 0.12, n_per_type),
                                               rng.normal(0.8, 0.10, n_per_type),
                                               rng.normal(0.5, 0.09, n_per_type)])),
    "mean_dapi":        np.concatenate([rng.exponential(400, n_per_type),
                                        rng.exponential(600, n_per_type),
                                        rng.exponential(350, n_per_type)]),
    "cell_line":        ["HeLa"] * n_per_type + ["MCF7"] * n_per_type + ["U2OS"] * n_per_type,
})

# 1. Pairplot survey
g = sns.pairplot(df_morph, hue="cell_line", corner=True,
                 diag_kind="kde", plot_kws={"alpha": 0.5, "s": 15},
                 palette="Dark2")
g.savefig("morphology_pairplot.png", dpi=150)
print("Saved morphology_pairplot.png")

# 2. Focused jointplot for the most informative pair
g2 = sns.jointplot(data=df_morph, x="cell_area_um2", y="nucleus_area_um2",
                   hue="cell_line", kind="scatter",
                   marginal_kws={"fill": True, "alpha": 0.25},
                   palette="Dark2", alpha=0.6)
g2.set_axis_labels("Cell Area (µm²)", "Nucleus Area (µm²)")
g2.savefig("morphology_jointplot.png", dpi=150)
print("Saved morphology_jointplot.png")
```

## Key Parameters

| Parameter | Function(s) | Default | Range / Options | Effect |
|-----------|-------------|---------|-----------------|--------|
| `hue` | All plot functions | `None` | Column name (categorical or continuous) | Color-encodes a variable; triggers automatic legend |
| `style` | `scatterplot`, `lineplot` | `None` | Categorical column name | Encodes variable with marker shape or line dash pattern |
| `size` | `scatterplot`, `lineplot` | `None` | Categorical or continuous column | Encodes variable via point or line size |
| `col` / `row` | Figure-level only (`relplot`, `displot`, `catplot`, `lmplot`) | `None` | Categorical column name | Creates one subplot panel per unique value |
| `col_wrap` | Figure-level only | `None` | int | Wraps columns onto a new row after N panels |
| `estimator` | `barplot`, `pointplot` | `"mean"` | `"mean"`, `"median"`, any callable | Aggregation function applied within each category |
| `errorbar` | `barplot`, `lineplot`, `pointplot` | `("ci", 95)` | `"ci"`, `"sd"`, `"se"`, `"pi"`, `None` | Error bar type displayed around the estimate |
| `stat` | `histplot` | `"count"` | `"count"`, `"frequency"`, `"density"`, `"probability"` | Normalization applied to histogram bar heights |
| `bw_adjust` | `kdeplot`, `violinplot` | `1.0` | `0.1`–`3.0` | KDE bandwidth multiplier; lower=spikier, higher=smoother |
| `multiple` | `histplot`, `kdeplot` | `"layer"` | `"layer"`, `"stack"`, `"dodge"`, `"fill"` | How overlapping hue groups are drawn |
| `inner` | `violinplot` | `"box"` | `"box"`, `"quart"`, `"point"`, `"stick"`, `None` | Interior annotation inside the violin body |
| `standard_scale` | `clustermap` | `None` | `0` (rows), `1` (columns) | Z-score normalization axis before clustering |
| `dodge` | `boxplot`, `violinplot`, `stripplot` | Varies | `True`, `False` | Separate hue-grouped elements along the axis |
| `context` | `set_theme()` | `"notebook"` | `"paper"`, `"notebook"`, `"talk"`, `"poster"` | Scales font and line widths for output medium |

## Best Practices

1. **Prefer long-form DataFrames with named columns**: Seaborn's semantic mapping (`hue`, `style`, `size`) reads variable names directly from column names. Passing raw arrays loses axis labels and legends. Use `pd.melt()` to convert wide-form data.

2. **Call `set_theme()` once at the top of a script**: This sets the global style, context, and palette for all subsequent plots, ensuring consistency. Reset to defaults with `sns.set_theme()`.
   ```python
   sns.set_theme(style="ticks", context="paper", font_scale=1.1,
                 rc={"axes.spines.right": False, "axes.spines.top": False})
   ```

3. **Use axes-level functions for mixed-type custom layouts**: Figure-level functions (`relplot`, `catplot`) create their own figure and cannot be placed in an existing `Axes`. When combining different plot types (e.g., scatter + violin + heatmap), allocate a `plt.subplots()` grid and use axes-level functions with `ax=`.

4. **Use colorblind-safe palettes**: `sns.set_palette("colorblind")` or `palette="colorblind"` produces a palette distinguishable by readers with common color vision deficiencies. For diverging data, use `"RdBu_r"` or `"coolwarm"` with `center=0`.

5. **Overlay individual data points on summary plots**: Violin and bar plots hide distribution shape and sample size. Overlaying a `stripplot` or `swarmplot` with `alpha=0.4` and small `size` conveys data density without obscuring the summary statistic.

6. **Size figure-level plots with `height` and `aspect`, not `figsize`**: Figure-level functions ignore `figsize`. Use `height=` (inches per panel) and `aspect=` (width-to-height ratio per panel). For axes-level, set `figsize` on the `plt.subplots()` call.

7. **Anti-pattern — calling `plt.savefig()` on a figure-level grid**: Figure-level functions return a `FacetGrid`/`JointGrid` object. Save it with `g.savefig("out.png", dpi=300, bbox_inches="tight")`, not `plt.savefig()`, which may capture a blank figure.

## Common Recipes

### Recipe: Publication-Ready Figure with Custom Palette and 300 DPI Export

When to use: Preparing a multi-panel figure for journal submission or a slide deck.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sns.set_theme(style="ticks", context="paper", font_scale=1.2,
              rc={"pdf.fonttype": 42, "ps.fonttype": 42})

rng = np.random.default_rng(7)
df = pd.DataFrame({
    "condition": np.repeat(["Control", "Treated"], 40),
    "ki67_pct":  np.concatenate([rng.normal(18, 4, 40), rng.normal(32, 6, 40)]),
    "apoptosis": np.concatenate([rng.normal(5, 1.5, 40), rng.normal(12, 2.5, 40)]),
})

custom_palette = {"Control": "#4575B4", "Treated": "#D73027"}

fig, axes = plt.subplots(1, 2, figsize=(8, 4))

# Panel A
sns.boxplot(data=df, x="condition", y="ki67_pct",
            palette=custom_palette, width=0.45, linewidth=1.2, ax=axes[0])
sns.stripplot(data=df, x="condition", y="ki67_pct",
              color="black", alpha=0.35, size=3, jitter=True, ax=axes[0])
axes[0].set_ylabel("Ki67 Positive Cells (%)")
axes[0].set_xlabel("")
axes[0].set_title("A", loc="left", fontweight="bold")

# Panel B
sns.boxplot(data=df, x="condition", y="apoptosis",
            palette=custom_palette, width=0.45, linewidth=1.2, ax=axes[1])
sns.stripplot(data=df, x="condition", y="apoptosis",
              color="black", alpha=0.35, size=3, jitter=True, ax=axes[1])
axes[1].set_ylabel("Apoptotic Cells (%)")
axes[1].set_xlabel("")
axes[1].set_title("B", loc="left", fontweight="bold")

sns.despine(trim=True)
plt.tight_layout()
plt.savefig("figure1.pdf", dpi=300, bbox_inches="tight")
plt.savefig("figure1.png", dpi=300, bbox_inches="tight")
print("Saved figure1.pdf and figure1.png at 300 DPI")
```

### Recipe: Clustered Heatmap with Row and Column Color Annotations

When to use: Displaying a gene expression matrix with sample group annotations and hierarchical clustering to reveal co-expression modules.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

rng = np.random.default_rng(21)
n_genes, n_samples = 40, 20
conditions = ["tumor"] * 10 + ["normal"] * 10

# Simulate expression: 3 co-expression modules
expr = pd.DataFrame(
    rng.lognormal(2.5, 0.8, (n_genes, n_samples)),
    index=[f"GENE{i:03d}" for i in range(n_genes)],
    columns=[f"{c[0].upper()}{i:02d}" for i, c in enumerate(conditions)],
)
# Module 1: genes 0-13 up in tumor
expr.iloc[:14, :10]  *= 3.0
# Module 2: genes 14-27 down in tumor
expr.iloc[14:28, :10] *= 0.3
# Module 3: genes 28-39 unchanged

log_expr = np.log2(expr + 1)

# Column colors: tumor=red, normal=blue
cond_pal = {"tumor": "#C62828", "normal": "#1565C0"}
col_colors = [cond_pal[c] for c in conditions]

# Row colors: module membership
module_pal = {"up": "#EF9A9A", "down": "#90CAF9", "stable": "#C8E6C9"}
row_modules = (["up"] * 14) + (["down"] * 14) + (["stable"] * 12)
row_colors  = [module_pal[m] for m in row_modules]

g = sns.clustermap(
    log_expr,
    cmap="RdYlBu_r",
    center=log_expr.values.mean(),
    standard_scale=0,           # z-score per gene (row)
    method="ward",
    metric="euclidean",
    col_colors=col_colors,
    row_colors=row_colors,
    figsize=(14, 12),
    linewidths=0,
    cbar_pos=(0.02, 0.85, 0.03, 0.12),
    cbar_kws={"label": "Row z-score"},
    dendrogram_ratio=(0.12, 0.08),
)
g.ax_heatmap.set_xlabel("Sample", fontsize=10)
g.ax_heatmap.set_ylabel("Gene",   fontsize=10)
g.ax_heatmap.set_title("Gene Expression Clustermap", fontsize=12, pad=80)

# Manual legend for column/row annotations
legend_handles = [
    mpatches.Patch(color="#C62828", label="Tumor"),
    mpatches.Patch(color="#1565C0", label="Normal"),
    mpatches.Patch(color="#EF9A9A", label="Up in tumor"),
    mpatches.Patch(color="#90CAF9", label="Down in tumor"),
    mpatches.Patch(color="#C8E6C9", label="Stable"),
]
g.ax_heatmap.legend(handles=legend_handles, bbox_to_anchor=(1.25, 1.05),
                    loc="upper left", frameon=False, fontsize=9)

plt.savefig("clustermap_annotated.png", dpi=300, bbox_inches="tight")
print("Saved clustermap_annotated.png")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Legend placed outside plot, clipped in saved file | Figure-level functions place the legend outside by default | Add `bbox_inches="tight"` to `savefig()`: `g.savefig("out.png", dpi=300, bbox_inches="tight")` |
| `TypeError: FacetGrid.savefig()` or blank figure saved | Called `plt.savefig()` on a figure-level grid that owns its own figure | Use `g.savefig(...)` instead of `plt.savefig(...)` |
| Overlapping x-axis category labels | Long label strings overlap at default rotation | Add `plt.xticks(rotation=45, ha="right")` and `plt.tight_layout()` after the plot call |
| `ValueError: Could not interpret value ... for parameter 'hue'` | Data is in wide-form; hue mapping requires long-form | Convert with `df.melt(id_vars=[...], var_name="sample", value_name="expr")` |
| KDE bandwidth too smooth (loses bimodality) | Default `bw_adjust=1.0` over-smooths small datasets | Lower to `bw_adjust=0.5`; confirm peaks with `histplot` |
| `clustermap` ignores `figsize` | Figure-level functions do not accept `figsize` as a kwarg in older seaborn | Pass `figsize` as a direct argument: `sns.clustermap(..., figsize=(12, 10))` |
| Violin plot is a thin line (no shape) | Too few observations for KDE estimation | Switch to `kind="box"` or `kind="strip"`; or use `cut=0` to restrict KDE to data range |
| Colors not distinguishable for many groups | Default palette repeats with >6 categories | Use `sns.color_palette("husl", n_colors=N)` or `"tab20"` for up to 20 distinct colors |
| Figure-level function ignores `ax=` parameter | Axes-level distinction: figure-level functions create their own figure | Use the corresponding axes-level function (`scatterplot`, `histplot`, etc.) with `ax=` |

## Related Skills

- **matplotlib-scientific-plotting** — low-level figure building, custom annotations, non-statistical plot types, and multi-panel layouts that mix seaborn with raw matplotlib
- **plotly-interactive-visualization** — interactive charts with hover, zoom, and HTML/Dash export
- **pydeseq2-differential-expression** — produces the log2FC and p-values that feed into volcano-style scatter plots
- **scikit-image-processing** — generates cell morphology measurements visualized with seaborn categorical/distribution plots
- **scientific-visualization** — decision guide for selecting the right chart type and color scheme before coding

## References

- [Seaborn official documentation](https://seaborn.pydata.org/) — API reference, tutorial, and gallery
- [Seaborn example gallery](https://seaborn.pydata.org/examples/index.html) — visual index of all plot types
- [Seaborn GitHub](https://github.com/mwaskom/seaborn) — source code and issue tracker
- Waskom ML (2021). "seaborn: statistical data visualization." *Journal of Open Source Software*, 6(60), 3021. [https://doi.org/10.21105/joss.03021](https://doi.org/10.21105/joss.03021)
