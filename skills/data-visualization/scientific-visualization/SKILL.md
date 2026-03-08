---
name: "scientific-visualization"
description: "Guide for choosing and creating scientific visualizations for publications and presentations. Covers selecting chart types for different data structures, color theory for accessibility and print, figure composition, journal-specific formatting requirements (Nature, Cell, ACS), and common pitfalls that undermine scientific credibility. Consult this guide when deciding how to visualize your data or preparing figures for submission."
license: "CC-BY-4.0"
---

# scientific-visualization

## Overview

Effective scientific visualization communicates data clearly, honestly, and accessibly. Poor chart choices, misleading axes, or inaccessible color palettes can obscure findings or introduce bias. This guide covers the full workflow of scientific figure preparation: from selecting the right chart type for your data structure through color theory, accessibility, and journal submission formatting requirements.

## Key Concepts

### Chart Type and Data Type Alignment

Every chart type is optimized for a specific data structure. Mismatches (e.g., pie charts for continuous distributions, bar charts for time series) hide structure and distort perception.

| Data Type | Recommended Chart | Avoid |
|-----------|------------------|-------|
| Continuous distribution (1 group) | Histogram, violin plot, ridge plot | Bar chart with mean only |
| Continuous distribution (2–5 groups) | Violin + boxplot overlay, beeswarm | Grouped bar chart |
| Two continuous variables, correlation | Scatter plot, hexbin (large N) | Line chart without temporal order |
| Categorical counts / proportions | Bar chart (horizontal for long labels) | Pie chart (>4 categories) |
| Change over time (continuous) | Line chart | Bar chart |
| Change over time (sparse events) | Step chart, event raster | Connected scatter |
| Part-to-whole (≤5 parts) | Stacked bar, waffle chart | 3D pie chart |
| High-dimensional (>5 variables) | Heatmap (clustered), parallel coordinates | 3D scatter |
| Spatial data | Map, spatial heatmap | Bubble chart |
| Survival / time-to-event | Kaplan-Meier curve | Bar chart of median survival |

### Color Theory for Science

Color encodes information. Misused color introduces artifacts and fails readers with color vision deficiency (CVD; ~8% of males).

**Sequential palettes** encode ordered numeric data from low to high (e.g., expression level, concentration). Use perceptually uniform palettes: `viridis`, `magma`, `cividis`. These also print in grayscale.

**Diverging palettes** encode data with a meaningful midpoint (e.g., fold-change centered at 0, correlation from -1 to +1). Use `RdBu`, `coolwarm`, or `vlag`. Always ensure the midpoint maps to white/neutral.

**Qualitative palettes** encode unordered categories. Use Okabe-Ito (CVD-safe), `tab10` (matplotlib default), or ColorBrewer qualitative palettes. Limit to ≤8 distinguishable colors; use shape or pattern as redundant encoding beyond that.

**Color don'ts**:
- Rainbow/jet colormap: not perceptually uniform; creates false contours
- Red vs. green encoding: fails deuteranopia (~6% males)
- Saturated color for background or large areas

### Figure Composition and Layout

Scientific figures are typically multi-panel. Panel layout and labeling affect how readers parse information.

- **Panel labels**: Bold uppercase letters (A, B, C) in the top-left corner; use 8–12 pt in the figure, larger in the caption reference.
- **Alignment**: Align panel edges on a grid. Unaligned panels signal lack of attention to detail.
- **White space**: Leave adequate margins; crowded panels reduce readability.
- **Figure size**: Design for the target column width — single column (~85 mm / 3.35 in), 1.5 column (~114 mm / 4.5 in), or double column (~170 mm / 6.7 in) for Nature-family journals.
- **Font**: Sans-serif (Arial, Helvetica) at 6–8 pt minimum in the final figure at publication resolution.

### Journal Formatting Requirements

Major journals specify exact figure requirements for submission. Violating these causes desk-rejection delays.

| Journal/Style | Max Width | Resolution | Color Mode | Font | File Format |
|---------------|-----------|------------|------------|------|-------------|
| Nature family | 89 mm (1-col), 183 mm (2-col) | 300 dpi (photos), 600 dpi (line art) | RGB or CMYK | Arial 5–7 pt | PDF, TIFF, EPS |
| Cell/iScience | 85 mm (1-col), 170 mm (2-col) | 300 dpi raster, 600 dpi halftone | RGB | Helvetica 6–8 pt | PDF, EPS, TIFF |
| ACS journals | 3.25 in (1-col), 7 in (2-col) | 600 dpi (color), 1200 dpi (b&w line art) | RGB (screen), CMYK (print) | Arial/Helvetica 4.5–7 pt | TIFF, EPS, PDF |
| PLOS ONE | No strict width | 300 dpi (raster), 600–1200 dpi (line art) | RGB | Any | TIFF, EPS, PDF |

## Decision Framework

Use this tree to select the right visualization for your analysis goal:

```
What is the primary message of this figure?
|
+-- Show a distribution or spread of values
|   +-- One group         --> Histogram or violin plot
|   +-- 2-5 groups        --> Violin + jitter (show all points if N < 100)
|   +-- Many groups       --> Ridge plot (joy plot)
|
+-- Compare quantities between categories
|   +-- Few categories (2-5)    --> Bar chart with error bars + individual points
|   +-- Many categories (>8)    --> Lollipop chart or dot plot (horizontal)
|   +-- Paired measurements     --> Slopegraph or paired dot plot
|
+-- Show a relationship between two continuous variables
|   +-- N < 1000                --> Scatter plot
|   +-- N > 1000                --> Hexbin or 2D density plot
|   +-- Time ordered            --> Line chart
|
+-- Show composition or part-to-whole
|   +-- 2-4 parts               --> Stacked bar or waffle chart
|   +-- Over time               --> Stacked area chart
|   +-- Avoid pie chart unless <= 3 parts and proportions are obvious
|
+-- Show high-dimensional data
|   +-- Genes x samples         --> Clustered heatmap (seaborn.clustermap)
|   +-- Embeddings (UMAP, PCA)  --> Scatter colored by metadata
|   +-- Feature importance      --> Horizontal bar chart (sorted)
|
+-- Show spatial or geographic data
|   +-- Microscopy              --> Image overlay with colorbar
|   +-- Geographic              --> Choropleth map
```

| Analysis Goal | Chart Type | Library | Key Consideration |
|---------------|-----------|---------|-------------------|
| Gene expression across groups | Violin + jitter | `seaborn`, `plotnine` | Show all points if N < 50; never bar+SEM only |
| Differential expression | Volcano plot | `matplotlib` | Log2FC on x-axis, -log10(p) on y-axis |
| Clustering results | UMAP scatter | `scanpy`, `matplotlib` | One plot per annotation variable |
| Correlation matrix | Clustered heatmap | `seaborn.clustermap` | Use diverging palette centered at 0 |
| Protein structure | Ribbon diagram | PyMOL, ChimeraX | Not covered here — use dedicated molecular graphics tools |
| Survival analysis | Kaplan-Meier | `lifelines` | Include confidence bands and at-risk table |
| Time course | Line chart with CI | `matplotlib` | Show uncertainty; connect group means, not individual points |

## Best Practices

1. **Show the data, not just summaries**: For N < 100, overlay individual data points on violin or box plots using jitter or beeswarm. Bar charts with only mean ± SEM conceal distribution shape, outliers, and bimodality.

2. **Choose CVD-safe color palettes by default**: Use Okabe-Ito or `viridis`/`cividis` for sequential data. Test your figure with a CVD simulator (e.g., [Coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/)) before submission.

3. **Design at final publication size from the start**: Set your figure canvas to the exact column width of the target journal (e.g., 89 mm for Nature single-column). Rescaling after the fact makes fonts too small or too large, and changes aspect ratios.

4. **Label axes with units and use descriptive titles**: Every axis must have a label with units in parentheses (e.g., "Expression level (log2 CPM)"). Avoid cryptic abbreviations without legend entries.

5. **Use vector formats for line art and text**: Save figures as PDF or SVG when they contain text and lines. Rasterize only when submitting to a journal that requires TIFF. Vector figures scale without pixelation and remain editable.

6. **Match statistical annotations to the test performed**: If you annotate significance stars (*), state in the caption which test was used, the exact p-value, and the sample size. "n.s." should still report the p-value.

7. **Avoid dual y-axes**: Two different y-axes on one plot are almost always misleading — the apparent relationship depends on scale choices. Use two separate panels instead.

## Common Pitfalls

1. **Bar chart for continuous distributions (dynamite plot)**
   - *What goes wrong*: Mean ± SEM bars hide whether data is normally distributed, multimodal, or has outliers. Two datasets with identical bars can have completely different distributions.
   - *How to avoid*: Use violin plots, box-and-whisker with jitter, or beeswarm plots. Show all data points when N < 50.

2. **Truncated or broken y-axis that exaggerates differences**
   - *What goes wrong*: Starting the y-axis at a non-zero value makes small differences appear large and misleads readers about effect size.
   - *How to avoid*: Start y-axis at zero for ratio/count data. If zooming in is genuinely needed, use an inset or a separate panel with a clear label indicating the truncation.

3. **Using rainbow/jet colormap for heatmaps**
   - *What goes wrong*: Jet is not perceptually uniform — it creates false contour lines and fails under CVD and grayscale printing.
   - *How to avoid*: Use `viridis`, `magma`, or `inferno` for sequential; `RdBu` or `coolwarm` for diverging data. These are the defaults in seaborn >= 0.12.

4. **Overlapping data points without jitter or transparency**
   - *What goes wrong*: Points stack on top of each other (overplotting), making dense regions appear sparse and hiding the true data density.
   - *How to avoid*: Add jitter (`seaborn.stripplot(jitter=True)`), use transparency (`alpha=0.3`), or switch to a hexbin / 2D density plot for large N.

5. **P-value annotations without effect size or sample size**
   - *What goes wrong*: A statistically significant result (p < 0.05) with N = 10,000 may be scientifically trivial. Stars alone are uninformative.
   - *How to avoid*: Report exact p-values, effect sizes (Cohen's d, odds ratio), and sample sizes in the figure caption or directly on the plot.

6. **Figure text too small at publication size**
   - *What goes wrong*: Designing at screen size and then shrinking to journal column width results in 3–4 pt text that fails minimum readability standards.
   - *How to avoid*: Design at final print size from the start. Check that axis labels are ≥ 6 pt at the final dimensions.

7. **Inconsistent style across panels in a multi-panel figure**
   - *What goes wrong*: Different fonts, line widths, or color schemes across panels make the figure look unprofessional and harder to compare.
   - *How to avoid*: Define a shared `matplotlib.rcParams` style dictionary at the top of your figure script and apply it to all panels.

## Workflow

1. **Define the message first**
   - Write one sentence describing what you want the reader to take away from this figure.
   - Choose the chart type that most directly communicates that message using the Decision Framework above.

2. **Prepare the data**
   - Aggregate, tidy, and validate your data before plotting.
   - Check for outliers that should be investigated, not silently dropped.

3. **Prototype at screen resolution**
   - Build a draft figure in your preferred library (matplotlib, seaborn, ggplot2, plotnine).
   - Focus on getting data and chart type right; ignore styling at this stage.

4. **Apply journal-specific styling**
   - Set canvas size to target journal column width.
   - Set font family and minimum size.
   - Choose CVD-safe palette.
   - Standardize line widths (0.5–1.0 pt for axes and ticks, 1.0–2.0 pt for data lines).

5. **Add annotations and labels**
   - Panel labels (A, B, C) in bold.
   - Axis labels with units.
   - Statistical annotations with test name and exact p-value.
   - Legend with descriptive entries.

6. **Export at correct resolution**
   - Vector: PDF or SVG for line art and text.
   - Raster: TIFF at 300 dpi (halftone/photos) or 600 dpi (line art).
   - Use `plt.savefig("fig1.pdf", bbox_inches="tight")` in matplotlib.

7. **Accessibility check**
   - Simulate CVD using an online tool or GIMP color blindness filter.
   - Print in grayscale and verify panels remain distinguishable.

## Protocol Guidelines

1. **For matplotlib/seaborn**: Set `rcParams` at the top of every figure script; use `fig.set_size_inches()` to enforce journal dimensions; export with `dpi=300` minimum.
2. **For R/ggplot2**: Use `theme_classic()` or a custom theme; set `ggsave(width=..., units="mm", dpi=300)`.
3. **For multi-panel assembly**: Use `matplotlib.gridspec`, `patchworklib` (Python), or `cowplot`/`patchwork` (R) for aligned panel grids.
4. **For interactive figures**: Plotly or Bokeh for HTML outputs; Vega-Lite for web embedding. Always provide a static fallback for publication.
5. **For poster presentations**: Scale all fonts up by 1.5–2×; use larger markers (pt size 8–12) and thicker lines (2–3 pt); prefer high-contrast, dark background palettes.

## Further Reading

- [Fundamentals of Data Visualization — Claus O. Wilke (open access)](https://clauswilke.com/dataviz/) — comprehensive guide covering chart selection, color, and figure design
- [Ten Simple Rules for Better Figures (Rougier et al., 2014, PLOS Computational Biology)](https://doi.org/10.1371/journal.pcbi.1003833) — practical peer-reviewed guidelines
- [ColorBrewer 2.0](https://colorbrewer2.org/) — browser tool for selecting print-safe, CVD-safe color palettes
- [Coblis CVD Simulator](https://www.color-blindness.com/coblis-color-blindness-simulator/) — test figure accessibility under 8 types of color vision deficiency
- [Nature Methods — Points of View column](https://www.nature.com/collections/cajwddbnjb) — monthly visualization advice from Bang Wong and colleagues
- [ACS Publications Figure Preparation Guide](https://publish.acs.org/publish/author_guidelines) — journal-specific technical requirements

## Related Skills

- `matplotlib-figures` — Python implementation of publication-quality figures with matplotlib and seaborn
- `data-visualization` — general Python plotting recipes
- `biostatistics` — statistical test selection to accompany figure annotations
