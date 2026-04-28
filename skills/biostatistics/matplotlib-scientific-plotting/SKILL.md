---
name: "matplotlib-scientific-plotting"
description: "Low-level Python plotting for scientific figures: publication-quality line, scatter, bar, heatmap, contour, 3D; multi-panel layouts; fine control of every element. PNG/PDF/SVG export. Use seaborn for quick stats, plotly for interactive."
license: "PSF-based"
---

# matplotlib

## Overview

Matplotlib is Python's foundational visualization library for creating static, animated, and interactive plots. It provides both a MATLAB-style pyplot interface and an object-oriented API for full control over figures, axes, and artists. Essential for generating publication-quality scientific figures.

## When to Use

- Creating publication-quality plots with precise control over every element (fonts, ticks, colors, spacing)
- Building multi-panel figures with complex subplot layouts for papers
- Generating standard scientific plot types: line, scatter, bar, histogram, heatmap, box, violin, contour
- Exporting figures to vector formats (PDF, SVG) for journal submission
- Creating 3D surface, scatter, or wireframe plots
- Customizing colormaps and color schemes for accessibility (colorblind-friendly)
- Integrating plots with NumPy arrays and pandas DataFrames
- For quick statistical visualizations (distributions, regressions), use `seaborn` instead
- For interactive/web-based plots with hover and zoom, use `plotly` instead

## Prerequisites

- **Python packages**: `matplotlib`, `numpy`
- **Optional**: `pandas` (for DataFrame plotting), `seaborn` (for style presets)
- **Environment**: Works in scripts, Jupyter notebooks (`%matplotlib inline`), and GUI apps

```bash
pip install matplotlib numpy
```

## Quick Start

```python
import matplotlib.pyplot as plt
import numpy as np

# Publication-ready figure template: set size, plot, label, save as PDF
fig, ax = plt.subplots(figsize=(6, 4))  # single-column journal width ≈ 6 cm → set here in inches

x = np.linspace(0, 2 * np.pi, 200)
ax.plot(x, np.sin(x), color="steelblue", lw=1.5, label="sin(x)")
ax.plot(x, np.cos(x), color="coral",    lw=1.5, label="cos(x)", linestyle="--")

ax.set_xlabel("x (radians)")
ax.set_ylabel("Amplitude")
ax.set_title("Sine and Cosine Waves")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)  # clean axis style

plt.tight_layout()
plt.savefig("quickstart.pdf", bbox_inches="tight", dpi=300)
print("Saved quickstart.pdf")
```

## Core API

### Module 1: Figure and Axes Creation

The fundamental objects: Figure (canvas) and Axes (plotting area).

```python
import matplotlib.pyplot as plt
import numpy as np

# Single plot (recommended: OO interface)
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 2 * np.pi, 100)
ax.plot(x, np.sin(x), label="sin(x)")
ax.plot(x, np.cos(x), label="cos(x)")
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.set_title("Trigonometric Functions")
ax.legend(); ax.grid(True, alpha=0.3)
plt.savefig("basic_plot.png", dpi=300, bbox_inches="tight")
print("Saved basic_plot.png")
```

```python
# Multi-panel subplots
fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
axes[0, 0].plot(x, np.sin(x)); axes[0, 0].set_title("sin(x)")
axes[0, 1].scatter(x[::5], np.cos(x[::5])); axes[0, 1].set_title("cos(x)")
axes[1, 0].bar(["A", "B", "C"], [3, 7, 5]); axes[1, 0].set_title("Bar")
axes[1, 1].hist(np.random.randn(500), bins=30); axes[1, 1].set_title("Histogram")
plt.savefig("subplots.png", dpi=300, bbox_inches="tight")
print("Saved subplots.png with 4 panels")
```

### Module 2: Plot Types

Standard scientific chart types.

```python
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)

# Line plot — trends over time
x = np.linspace(0, 10, 50)
axes[0, 0].plot(x, np.exp(-x/3) * np.sin(x), "b-", linewidth=2)
axes[0, 0].set_title("Line Plot")

# Scatter plot — correlations
np.random.seed(42)
axes[0, 1].scatter(np.random.randn(100), np.random.randn(100), alpha=0.6, c=np.random.rand(100), cmap="viridis")
axes[0, 1].set_title("Scatter Plot")

# Bar chart — categorical comparisons
categories = ["Gene A", "Gene B", "Gene C", "Gene D"]
axes[0, 2].bar(categories, [4.2, 7.1, 3.5, 6.8], color="steelblue", edgecolor="black")
axes[0, 2].set_title("Bar Chart")

# Histogram — distributions
axes[1, 0].hist(np.random.randn(1000), bins=40, edgecolor="black", alpha=0.7)
axes[1, 0].set_title("Histogram")

# Box plot — statistical distributions
data = [np.random.randn(50) + i for i in range(4)]
axes[1, 1].boxplot(data, labels=["Ctrl", "Drug A", "Drug B", "Drug C"])
axes[1, 1].set_title("Box Plot")

# Heatmap — matrix data
matrix = np.random.rand(8, 8)
im = axes[1, 2].imshow(matrix, cmap="coolwarm", aspect="auto")
plt.colorbar(im, ax=axes[1, 2])
axes[1, 2].set_title("Heatmap")

plt.savefig("plot_types.png", dpi=300, bbox_inches="tight")
print("Saved 6 plot types to plot_types.png")
```

### Module 3: Styling and Customization

Colors, fonts, styles, annotations.

```python
import matplotlib.pyplot as plt
import numpy as np

# Use style sheets
plt.style.use("seaborn-v0_8-whitegrid")

# Custom rcParams for publication
plt.rcParams.update({
    "font.size": 12, "axes.labelsize": 14,
    "axes.titlesize": 16, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "legend.fontsize": 11,
})

fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 5, 100)
ax.plot(x, np.exp(-x), "r--", linewidth=2, label="Exponential decay")
ax.fill_between(x, np.exp(-x) - 0.1, np.exp(-x) + 0.1, alpha=0.2, color="red")

# Annotations
ax.annotate("Half-life", xy=(0.693, 0.5), xytext=(2, 0.7),
            arrowprops=dict(arrowstyle="->", color="black"),
            fontsize=12, fontweight="bold")
ax.set_xlabel("Time (s)"); ax.set_ylabel("Signal")
ax.legend()
plt.savefig("styled_plot.png", dpi=300, bbox_inches="tight")
print("Saved styled_plot.png")
```

### Module 4: Advanced Layouts

Mosaic layouts, GridSpec, insets.

```python
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

# Mosaic layout — named axes
fig, axes = plt.subplot_mosaic(
    [["main", "right"], ["main", "bottom_right"]],
    figsize=(10, 7), constrained_layout=True,
    gridspec_kw={"width_ratios": [2, 1]}
)
x = np.linspace(0, 10, 200)
axes["main"].plot(x, np.sin(x) * np.exp(-x/5), "b-", linewidth=2)
axes["main"].set_title("Main Panel")
axes["right"].hist(np.random.randn(300), bins=20, orientation="horizontal")
axes["right"].set_title("Distribution")
axes["bottom_right"].bar(["A", "B"], [3, 5])
axes["bottom_right"].set_title("Summary")
plt.savefig("mosaic_layout.png", dpi=300, bbox_inches="tight")
print("Saved mosaic_layout.png")
```

### Module 5: 3D Visualization

Surface, scatter, and wireframe plots.

```python
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

# Surface plot
u = np.linspace(0, 2 * np.pi, 50)
v = np.linspace(0, np.pi, 50)
X = np.outer(np.cos(u), np.sin(v))
Y = np.outer(np.sin(u), np.sin(v))
Z = np.outer(np.ones_like(u), np.cos(v))

ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)
ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
ax.set_title("3D Surface Plot")
plt.savefig("surface_3d.png", dpi=300, bbox_inches="tight")
print("Saved surface_3d.png")
```

### Module 6: Export and Saving

Output to various formats with publication settings.

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot([1, 2, 3], [1, 4, 9], "ko-")
ax.set_title("Export Example")

# High-res PNG for presentations
fig.savefig("figure.png", dpi=300, bbox_inches="tight", facecolor="white")

# Vector PDF for journal submission
fig.savefig("figure.pdf", bbox_inches="tight")

# SVG for web
fig.savefig("figure.svg", bbox_inches="tight")

# Transparent background
fig.savefig("figure_transparent.png", dpi=300, bbox_inches="tight", transparent=True)

plt.close(fig)  # Free memory
print("Exported to PNG, PDF, SVG, and transparent PNG")
```

## Common Workflows

### Workflow 1: Multi-Panel Figure for Publication

**Goal**: Create a 4-panel figure combining different plot types for a paper.

```python
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)

# Panel A: Time series
t = np.linspace(0, 24, 100)
axes[0, 0].plot(t, 50 + 10 * np.sin(t * np.pi / 12), "b-", linewidth=2)
axes[0, 0].set_xlabel("Time (h)"); axes[0, 0].set_ylabel("Expression")
axes[0, 0].set_title("A", loc="left", fontweight="bold")

# Panel B: Volcano plot
fc = np.random.randn(500)
pval = -np.log10(np.random.uniform(0.0001, 1, 500))
colors = ["red" if abs(f) > 1 and p > 2 else "grey" for f, p in zip(fc, pval)]
axes[0, 1].scatter(fc, pval, c=colors, s=10, alpha=0.7)
axes[0, 1].axhline(2, ls="--", color="black", alpha=0.5)
axes[0, 1].set_xlabel("log₂ FC"); axes[0, 1].set_ylabel("-log₁₀ p-value")
axes[0, 1].set_title("B", loc="left", fontweight="bold")

# Panel C: Bar chart with error bars
means = [3.2, 5.1, 4.7, 6.3]
sems = [0.4, 0.6, 0.3, 0.5]
axes[1, 0].bar(["Ctrl", "Drug A", "Drug B", "Combo"], means, yerr=sems,
               capsize=5, color="steelblue", edgecolor="black")
axes[1, 0].set_ylabel("Response"); axes[1, 0].set_title("C", loc="left", fontweight="bold")

# Panel D: Heatmap
data = np.random.randn(6, 4)
im = axes[1, 1].imshow(data, cmap="RdBu_r", aspect="auto")
plt.colorbar(im, ax=axes[1, 1])
axes[1, 1].set_title("D", loc="left", fontweight="bold")

fig.savefig("publication_figure.pdf", bbox_inches="tight")
print("Saved publication_figure.pdf (4 panels)")
```

### Workflow 2: Statistical Comparison Plot

**Goal**: Bar chart with individual data points and significance annotations.

```python
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
groups = {"Control": np.random.normal(5, 1.2, 20),
          "Treatment A": np.random.normal(7, 1.5, 20),
          "Treatment B": np.random.normal(6, 1.0, 20)}

fig, ax = plt.subplots(figsize=(6, 5))
positions = range(len(groups))
for i, (name, data) in enumerate(groups.items()):
    ax.bar(i, np.mean(data), yerr=np.std(data)/np.sqrt(len(data)),
           capsize=5, color=["#4C72B0", "#DD8452", "#55A868"][i],
           edgecolor="black", alpha=0.8, width=0.6)
    # Overlay individual data points
    ax.scatter(np.full_like(data, i) + np.random.uniform(-0.15, 0.15, len(data)),
               data, color="black", s=15, alpha=0.5, zorder=5)

ax.set_xticks(positions); ax.set_xticklabels(groups.keys())
ax.set_ylabel("Measurement")

# Add significance bracket
y_max = max(max(d) for d in groups.values()) + 1
ax.plot([0, 0, 1, 1], [y_max, y_max + 0.2, y_max + 0.2, y_max], "k-", linewidth=1)
ax.text(0.5, y_max + 0.3, "**", ha="center", fontsize=14)

fig.savefig("comparison_plot.png", dpi=300, bbox_inches="tight")
print("Saved comparison_plot.png")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `figsize` | Figure creation | `(6.4, 4.8)` | `(w, h)` in inches | Figure dimensions |
| `dpi` | `savefig` | `100` | `72`-`600` | Resolution: 300 for print, 150 for web |
| `bbox_inches` | `savefig` | `None` | `"tight"`, `None` | Crop whitespace around figure |
| `constrained_layout` | `subplots` | `False` | `True`/`False` | Auto-adjust spacing to prevent overlap |
| `cmap` | Heatmap/scatter | `"viridis"` | `"viridis"`, `"coolwarm"`, `"RdBu_r"`, etc. | Colormap for data mapping |
| `alpha` | All plot types | `1.0` | `0.0`-`1.0` | Transparency (0=invisible, 1=opaque) |
| `linewidth` | Line plots | `1.5` | `0.5`-`5.0` | Line thickness in points |
| `s` | Scatter | `20` | `1`-`500` | Marker size in points² |
| `bins` | Histogram | `10` | `5`-`100` or array | Number of histogram bins |
| `projection` | `add_subplot` | `None` | `"3d"`, `"polar"` | Axes projection type |

## Best Practices

1. **Always use the OO interface** (`fig, ax = plt.subplots()`) for production code. Reserve `plt.plot()` for quick interactive exploration only

2. **Use `constrained_layout=True`** to prevent overlapping labels and titles:
   ```python
   fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
   ```

3. **Choose accessible colormaps**: Use `viridis`, `cividis`, or `plasma` (perceptually uniform, colorblind-safe). Avoid `jet` and `rainbow`

4. **Close figures after saving** to prevent memory leaks in loops:
   ```python
   plt.close(fig)  # After savefig
   ```

5. **Set DPI appropriately**: 300 for print/journal, 150 for web/slides, 72 for screen-only

6. **Use `rasterized=True`** for large datasets to reduce PDF/SVG file size:
   ```python
   ax.scatter(x, y, rasterized=True)  # Vector labels + rasterized data
   ```

7. **Label panels consistently**: Use bold letters (A, B, C, D) at top-left of each subplot for multi-panel figures

## Common Recipes

### Recipe: Custom Color Palette

When to use: Consistent colors across multiple figures in a paper.

```python
import matplotlib.pyplot as plt

# Define a custom palette
palette = {"control": "#4C72B0", "treatment": "#DD8452", "combo": "#55A868"}

fig, ax = plt.subplots()
for group, color in palette.items():
    ax.bar(group, [5, 7, 6][list(palette.keys()).index(group)], color=color)
plt.savefig("custom_palette.png", dpi=300, bbox_inches="tight")
```

### Recipe: Twin Y-Axes

When to use: Plotting two variables with different scales on the same figure.

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax1 = plt.subplots(figsize=(8, 5))
x = np.arange(10)
ax1.bar(x, np.random.randint(10, 100, 10), alpha=0.7, color="steelblue", label="Count")
ax1.set_ylabel("Count", color="steelblue")

ax2 = ax1.twinx()
ax2.plot(x, np.cumsum(np.random.rand(10)), "r-o", linewidth=2, label="Cumulative")
ax2.set_ylabel("Cumulative", color="red")

fig.legend(loc="upper left", bbox_to_anchor=(0.15, 0.95))
plt.savefig("twin_axes.png", dpi=300, bbox_inches="tight")
```

### Recipe: Inset Zoom Plot

When to use: Showing a zoomed-in region of a larger plot.

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 10, 500)
y = np.sin(x) * np.exp(-x / 5)
ax.plot(x, y, "b-", linewidth=2)

# Inset
axins = ax.inset_axes([0.5, 0.5, 0.4, 0.4])
axins.plot(x, y, "b-", linewidth=2)
axins.set_xlim(1, 3); axins.set_ylim(0.2, 0.8)
ax.indicate_inset_zoom(axins, edgecolor="black")
plt.savefig("inset_zoom.png", dpi=300, bbox_inches="tight")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Overlapping labels/titles | No layout management | Add `constrained_layout=True` to `plt.subplots()` |
| `UserWarning: tight_layout` | Incompatible with constrained_layout | Use only one: `constrained_layout` OR `tight_layout()`, not both |
| Blurry figures in Jupyter | Low default DPI | Set `%config InlineBackend.figure_format = 'retina'` |
| Memory grows in loops | Figures not closed | Add `plt.close(fig)` after each `savefig()` |
| Font not found warning | Missing system font | Use `plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]` |
| Large PDF/SVG file size | Many data points in vector | Use `rasterized=True` on heavy artists |
| 3D plot rotation stuck | Interactive backend issue | Use `%matplotlib widget` in Jupyter or `plt.show()` in scripts |
| Colorbar wrong size | Default sizing doesn't match axes | Use `fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)` |

## References

- [matplotlib documentation](https://matplotlib.org/stable/) — official docs
- [matplotlib gallery](https://matplotlib.org/stable/gallery/) — examples by plot type
- [matplotlib cheatsheets](https://matplotlib.org/cheatsheets/) — quick reference (PDF)
- Hunter, J.D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering* 9(3):90-95.
