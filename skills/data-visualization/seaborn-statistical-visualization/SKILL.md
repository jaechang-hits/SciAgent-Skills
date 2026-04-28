---
name: seaborn-statistical-visualization
description: "Statistical visualization on matplotlib + pandas. Distributions (histplot, kdeplot, violin, box), relational (scatter, line), categorical, regression, correlation heatmaps. Auto aggregation/CIs. Use plotly for interactive; matplotlib for low-level."
license: BSD-3-Clause
---

# Seaborn — Statistical Visualization

## Overview

Seaborn is a Python visualization library for creating publication-quality statistical graphics with minimal code. It works directly with pandas DataFrames, provides automatic statistical estimation (means, CIs, KDE), and offers attractive default themes. Built on matplotlib for full customization access.

## When to Use

- Creating distribution plots (histograms, KDE, violin plots, box plots) for data exploration
- Visualizing relationships between variables with automatic trend fitting and confidence intervals
- Comparing distributions across categorical groups (treatment vs control, tissue types)
- Generating correlation heatmaps and clustered heatmaps
- Quick exploratory data analysis with `pairplot` for all pairwise relationships
- Multi-panel figures with automatic faceting by categorical variables
- For **interactive plots** with hover/zoom, use plotly instead
- For **low-level figure control** or custom layouts, use matplotlib directly

## Prerequisites

```bash
pip install seaborn matplotlib pandas
```

## Quick Start

```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

df = sns.load_dataset("tips")
sns.scatterplot(data=df, x="total_bill", y="tip", hue="day", style="time")
plt.title("Tips by Day and Time")
plt.tight_layout()
plt.savefig("scatter.png", dpi=150)
print("Saved scatter.png")
```

## Core API

### 1. Distribution Plots

Visualize univariate and bivariate distributions.

```python
import seaborn as sns
import matplotlib.pyplot as plt

df = sns.load_dataset("tips")

# Histogram with density normalization
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

sns.histplot(data=df, x="total_bill", hue="time", stat="density",
             multiple="stack", ax=axes[0])
axes[0].set_title("Histogram")

# KDE (smooth density estimate)
sns.kdeplot(data=df, x="total_bill", hue="time", fill=True,
            bw_adjust=0.8, ax=axes[1])
axes[1].set_title("KDE")

# ECDF (empirical cumulative distribution)
sns.ecdfplot(data=df, x="total_bill", hue="time", ax=axes[2])
axes[2].set_title("ECDF")

plt.tight_layout()
plt.savefig("distributions.png", dpi=150)
print("Saved distributions.png")
```

```python
# Bivariate KDE with contours
sns.kdeplot(data=df, x="total_bill", y="tip", fill=True,
            levels=5, thresh=0.1, cmap="mako")
plt.title("Bivariate KDE")
plt.savefig("bivariate_kde.png", dpi=150)
```

### 2. Categorical Plots

Compare distributions or estimates across discrete categories.

```python
import seaborn as sns
import matplotlib.pyplot as plt

df = sns.load_dataset("tips")
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Box plot — quartiles and outliers
sns.boxplot(data=df, x="day", y="total_bill", hue="sex",
            dodge=True, ax=axes[0])
axes[0].set_title("Box Plot")

# Violin plot — KDE + quartiles
sns.violinplot(data=df, x="day", y="total_bill", hue="sex",
               split=True, inner="quart", ax=axes[1])
axes[1].set_title("Violin Plot")

# Bar plot — mean with CI
sns.barplot(data=df, x="day", y="total_bill", hue="sex",
            estimator="mean", errorbar="ci", ax=axes[2])
axes[2].set_title("Bar Plot (mean ± 95% CI)")

plt.tight_layout()
plt.savefig("categorical.png", dpi=150)
print("Saved categorical.png")
```

```python
# Swarm plot — all individual observations, non-overlapping
sns.swarmplot(data=df, x="day", y="total_bill", hue="sex", dodge=True)
plt.title("Swarm Plot")
plt.savefig("swarm.png", dpi=150)
```

### 3. Relational Plots

Explore relationships between continuous variables.

```python
import seaborn as sns
import matplotlib.pyplot as plt

df = sns.load_dataset("tips")

# Scatter with multiple semantic mappings
sns.scatterplot(data=df, x="total_bill", y="tip",
                hue="day", size="size", style="time")
plt.title("Scatter with Multi-Encoding")
plt.savefig("relational.png", dpi=150)
```

```python
# Line plot with automatic aggregation and CI
fmri = sns.load_dataset("fmri")
sns.lineplot(data=fmri, x="timepoint", y="signal",
             hue="region", style="event", errorbar="sd")
plt.title("Line Plot (mean ± SD)")
plt.savefig("lineplot.png", dpi=150)
```

### 4. Regression Plots

Fit and visualize linear models.

```python
import seaborn as sns
import matplotlib.pyplot as plt

df = sns.load_dataset("tips")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Linear regression with CI band
sns.regplot(data=df, x="total_bill", y="tip", ci=95, ax=axes[0])
axes[0].set_title("Linear Regression")

# Residual plot (check model assumptions)
sns.residplot(data=df, x="total_bill", y="tip", ax=axes[1])
axes[1].set_title("Residuals")

plt.tight_layout()
plt.savefig("regression.png", dpi=150)
print("Saved regression.png")
```

### 5. Matrix Plots

Visualize rectangular data (correlations, heatmaps).

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Correlation heatmap
df = sns.load_dataset("tips")
corr = df.select_dtypes(include=[np.number]).corr()

sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
            center=0, square=True, linewidths=0.5)
plt.title("Correlation Heatmap")
plt.tight_layout()
plt.savefig("heatmap.png", dpi=150)
print("Saved heatmap.png")
```

```python
# Clustered heatmap with hierarchical clustering
flights = sns.load_dataset("flights").pivot(index="month", columns="year", values="passengers")
sns.clustermap(flights, cmap="viridis", standard_scale=1,
               figsize=(10, 8), linewidths=0.5)
plt.savefig("clustermap.png", dpi=150)
```

### 6. Figure-Level Functions and Faceting

Create multi-panel figures with automatic faceting.

```python
import seaborn as sns

df = sns.load_dataset("tips")

# relplot — faceted scatter/line plots
g = sns.relplot(data=df, x="total_bill", y="tip",
                col="time", row="sex", hue="smoker",
                kind="scatter", height=3, aspect=1.2)
g.set_axis_labels("Total Bill ($)", "Tip ($)")
g.savefig("faceted_scatter.png", dpi=150)
print("Saved faceted_scatter.png")
```

```python
# catplot — faceted categorical plots
g = sns.catplot(data=df, x="day", y="total_bill",
                col="time", kind="box", height=4, aspect=1)
g.set_titles("{col_name}")
g.savefig("faceted_boxplot.png", dpi=150)
```

### 7. Exploratory Grids (pairplot, jointplot)

Quickly explore all pairwise relationships.

```python
import seaborn as sns

iris = sns.load_dataset("iris")

# Pairplot — matrix of pairwise relationships
g = sns.pairplot(iris, hue="species", corner=True,
                 diag_kind="kde", plot_kws={"alpha": 0.6})
g.savefig("pairplot.png", dpi=150)
print("Saved pairplot.png")
```

```python
# Joint plot — bivariate + marginal distributions
g = sns.jointplot(data=iris, x="sepal_length", y="petal_length",
                  hue="species", kind="scatter")
g.savefig("jointplot.png", dpi=150)
```

## Key Concepts

### Figure-Level vs Axes-Level Functions

Understanding this distinction is critical for composing seaborn with matplotlib:

| Feature | Axes-Level | Figure-Level |
|---------|-----------|--------------|
| **Examples** | `scatterplot`, `histplot`, `boxplot`, `heatmap` | `relplot`, `displot`, `catplot`, `lmplot` |
| **Returns** | `matplotlib.axes.Axes` | `FacetGrid` / `JointGrid` / `PairGrid` |
| **Faceting** | Manual (create subplots yourself) | Built-in (`col`, `row` params) |
| **Sizing** | `figsize` on parent figure | `height` + `aspect` per subplot |
| **Placement** | `ax=` parameter | Cannot be placed in existing figure |
| **Use when** | Combining with other plot types, custom layouts | Quick faceted views, exploratory analysis |

```python
# Axes-level: embed in custom layout
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sns.boxplot(data=df, x="day", y="tip", ax=axes[0])
sns.scatterplot(data=df, x="total_bill", y="tip", ax=axes[1])
```

### Data Format: Long vs Wide

Seaborn strongly prefers **long-form** (tidy) data where each variable is a column:

```python
# Long-form (preferred) — works with all functions
#    subject  condition  value
# 0        1    control   10.5
# 1        1  treatment   12.3

# Wide-form — works with some functions (heatmap, lineplot)
#    control  treatment
# 0     10.5       12.3

# Convert wide → long
df_long = df.melt(var_name="condition", value_name="value")
```

## Common Workflows

### Workflow 1: Exploratory Data Analysis

**Goal**: Quickly survey a new dataset's distributions and relationships.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

df = sns.load_dataset("penguins").dropna()

# 1. Pairwise relationships
g = sns.pairplot(df, hue="species", corner=True)
g.savefig("eda_pairplot.png", dpi=150)

# 2. Correlation heatmap
fig, ax = plt.subplots(figsize=(8, 6))
corr = df.select_dtypes(include=[np.number]).corr()
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
ax.set_title("Feature Correlations")
plt.tight_layout()
plt.savefig("eda_corr.png", dpi=150)

# 3. Distribution by group
g = sns.displot(df, x="flipper_length_mm", hue="species",
                kind="kde", fill=True, col="sex", height=4)
g.savefig("eda_dist.png", dpi=150)
print("EDA figures saved")
```

### Workflow 2: Publication-Quality Figure

**Goal**: Create a polished multi-panel figure for a paper.

```python
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style="ticks", context="paper", font_scale=1.1)
df = sns.load_dataset("penguins").dropna()

fig, axes = plt.subplots(1, 3, figsize=(12, 4))

# Panel A: Box plot
sns.boxplot(data=df, x="species", y="body_mass_g", hue="sex",
            palette="Set2", ax=axes[0])
axes[0].set_ylabel("Body Mass (g)")
axes[0].set_title("A", loc="left", fontweight="bold")

# Panel B: Scatter with regression
sns.regplot(data=df, x="flipper_length_mm", y="body_mass_g",
            scatter_kws={"alpha": 0.5, "s": 20}, ax=axes[1])
axes[1].set_xlabel("Flipper Length (mm)")
axes[1].set_ylabel("Body Mass (g)")
axes[1].set_title("B", loc="left", fontweight="bold")

# Panel C: Violin plot
sns.violinplot(data=df, x="species", y="bill_length_mm",
               inner="quart", palette="muted", ax=axes[2])
axes[2].set_ylabel("Bill Length (mm)")
axes[2].set_title("C", loc="left", fontweight="bold")

sns.despine(trim=True)
plt.tight_layout()
plt.savefig("figure_pub.pdf", dpi=300, bbox_inches="tight")
plt.savefig("figure_pub.png", dpi=300, bbox_inches="tight")
print("Publication figure saved as PDF and PNG")
```

## Key Parameters

| Parameter | Function | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `hue` | All plot functions | None | Column name | Color-encode a categorical/continuous variable |
| `style` | `scatterplot`, `lineplot` | None | Column name | Marker/line style encoding |
| `size` | `scatterplot`, `lineplot` | None | Column name | Point/line size encoding |
| `col` / `row` | Figure-level only | None | Column name | Create faceted subplots |
| `col_wrap` | Figure-level only | None | int | Max columns before wrapping |
| `estimator` | `barplot`, `pointplot` | `"mean"` | `"mean"`, `"median"`, callable | Aggregation function |
| `errorbar` | `barplot`, `lineplot` | `("ci", 95)` | `"ci"`, `"sd"`, `"se"`, `"pi"` | Error bar type |
| `stat` | `histplot` | `"count"` | `"count"`, `"frequency"`, `"density"`, `"probability"` | Histogram normalization |
| `bw_adjust` | `kdeplot`, `violinplot` | `1.0` | `0.1`–`3.0` | KDE bandwidth multiplier (higher=smoother) |
| `multiple` | `histplot`, `kdeplot` | `"layer"` | `"layer"`, `"stack"`, `"dodge"`, `"fill"` | How to handle overlapping hue groups |
| `kind` | `relplot`, `catplot`, `displot` | varies | Plot type string | Select specific plot type for figure-level functions |

## Best Practices

1. **Use DataFrames with named columns**: Seaborn's strength is semantic mapping from column names. Avoid passing raw arrays — you lose axis labels and legend entries.

2. **Choose axes-level for custom layouts, figure-level for faceting**: If you need to combine different plot types in one figure, use axes-level functions with `ax=`. If you want automatic faceting, use figure-level functions.

3. **Use `set_theme()` once at the start**: Set style, context, and palette globally before creating plots. Reset with `sns.set_theme()`.

4. **Use `"colorblind"` palette for accessibility**: `sns.set_palette("colorblind")` ensures your plots are distinguishable for readers with color vision deficiency.

5. **Always call `plt.tight_layout()` before saving**: Prevents axis labels from being clipped. For figure-level functions, use `g.tight_layout()`.

6. **Anti-pattern — using seaborn for highly customized layouts**: If you need pixel-perfect control over every element, use matplotlib directly. Seaborn is for quick, attractive statistical plots, not for custom infographics.

7. **Anti-pattern — wide-form data with semantic mappings**: Functions like `scatterplot(hue=...)` require long-form data. Use `pd.melt()` to convert wide-form first.

## Common Recipes

### Recipe: Annotated Heatmap with Significance Stars

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Compute correlation and p-values
df = sns.load_dataset("penguins").dropna().select_dtypes(include=[np.number])
n = len(df)
corr = df.corr()
p_values = df.corr().copy()
for i in df.columns:
    for j in df.columns:
        _, p = stats.pearsonr(df[i], df[j])
        p_values.loc[i, j] = p

# Create annotation with stars
annot = corr.round(2).astype(str)
for i in range(len(corr)):
    for j in range(len(corr)):
        if i != j and p_values.iloc[i, j] < 0.001:
            annot.iloc[i, j] += "***"
        elif i != j and p_values.iloc[i, j] < 0.01:
            annot.iloc[i, j] += "**"

sns.heatmap(corr, annot=annot, fmt="", cmap="coolwarm", center=0, square=True)
plt.title("Correlation with Significance")
plt.tight_layout()
plt.savefig("heatmap_sig.png", dpi=150)
```

### Recipe: Custom PairGrid with Mixed Plot Types

```python
import seaborn as sns

df = sns.load_dataset("penguins").dropna()
g = sns.PairGrid(df, hue="species", corner=True)
g.map_upper(sns.scatterplot, alpha=0.5)
g.map_lower(sns.kdeplot, fill=True, alpha=0.3)
g.map_diag(sns.histplot, kde=True)
g.add_legend()
g.savefig("custom_pairgrid.png", dpi=150)
print("Saved custom_pairgrid.png")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Legend outside plot area (clipped) | Figure-level functions place legend outside by default | Use `g._legend.set_bbox_to_anchor((0.9, 0.5))` or `plt.tight_layout()` |
| Overlapping x-axis labels | Long category names | `plt.xticks(rotation=45, ha="right")` + `plt.tight_layout()` |
| Figure too small | Default sizing insufficient | Axes-level: `fig, ax = plt.subplots(figsize=(10, 6))`; Figure-level: `height=6, aspect=1.5` |
| Colors not distinct enough | Default palette has too-similar colors | Use `sns.set_palette("bright")` or `sns.color_palette("husl", n_colors=N)` |
| KDE too smooth or jagged | Bandwidth too wide or narrow | Adjust `bw_adjust`: lower (0.5) for detail, higher (2.0) for smoothing |
| `FacetGrid` cannot be placed in existing figure | Figure-level functions create their own figure | Use the corresponding axes-level function with `ax=` parameter |
| `ValueError` with hue on wide-form data | Semantic mappings require long-form | Convert with `df.melt(var_name=..., value_name=...)` |

## Related Skills

- **matplotlib-scientific-plotting** — low-level control, custom layouts, and publication-quality figure export
- **plotly-interactive-visualization** — interactive charts with hover, zoom, and HTML export
- **statsmodels-statistical-modeling** — statistical models whose results can be visualized with seaborn regression plots

## References

- [Seaborn documentation](https://seaborn.pydata.org/) — official API reference and tutorial
- [Seaborn gallery](https://seaborn.pydata.org/examples/index.html) — visual examples of all plot types
- Waskom (2021) "seaborn: statistical data visualization" — [JOSS](https://doi.org/10.21105/joss.03021)
