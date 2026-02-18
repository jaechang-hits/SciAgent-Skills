# Scanpy Plotting Guide

Comprehensive guide for creating publication-quality single-cell visualizations.

## Setup for Publication Figures

```python
import scanpy as sc
import matplotlib.pyplot as plt

# High-quality defaults
sc.settings.set_figure_params(dpi=300, frameon=False, figsize=(5, 5), facecolor="white")
sc.settings.figdir = "./figures/"
sc.settings.file_format_figs = "pdf"  # Vector format for publications
```

## Quality Control Plots

```python
# Violin plots — before filtering, inspect distributions
sc.pl.violin(
    adata,
    ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
    jitter=0.4,
    multi_panel=True,
    save="_qc_violin.pdf",
)

# Scatter plots — identify outlier populations
sc.pl.scatter(adata, x="total_counts", y="pct_counts_mt", save="_qc_mt.pdf")
sc.pl.scatter(adata, x="total_counts", y="n_genes_by_counts", save="_qc_genes.pdf")

# Top expressed genes — check for contamination
sc.pl.highest_expr_genes(adata, n_top=20, save="_highest_expr.pdf")
```

## UMAP Visualizations

### Basic UMAP

```python
# Clusters with on-data labels
sc.pl.umap(adata, color="leiden", legend_loc="on data",
           legend_fontsize=10, legend_fontoutline=2,
           frameon=False, save="_clusters.pdf")

# Multiple variables side-by-side
sc.pl.umap(adata, color=["leiden", "cell_type", "batch"], ncols=3, save="_overview.pdf")

# Gene expression overlay
sc.pl.umap(adata, color=["CD3D", "CD14", "MS4A1", "NKG7"],
           use_raw=True, ncols=2, cmap="viridis", save="_markers.pdf")
```

### Publication Styling

```python
# Clean, minimal style
sc.pl.umap(
    adata, color="cell_type",
    palette="Set2",
    legend_loc="on data",
    legend_fontsize=10,
    legend_fontoutline=2,
    title="",
    frameon=False,
    save="_publication.pdf",
)

# Custom color palette
custom_colors = ["#E64B35", "#4DBBD5", "#00A087", "#3C5488",
                 "#F39B7F", "#8491B4", "#91D1C2", "#DC0000"]
sc.pl.umap(adata, color="cell_type", palette=custom_colors, save="_custom.pdf")
```

## Marker Gene Plots

### Dot Plot (most informative for cell type markers)

```python
# Grouped markers by cell type
marker_genes = {
    "T cells":    ["CD3D", "CD3E"],
    "B cells":    ["MS4A1", "CD79A"],
    "Monocytes":  ["CD14", "LYZ"],
    "NK cells":   ["NKG7", "GNLY"],
}
sc.pl.dotplot(adata, var_names=marker_genes, groupby="leiden",
              use_raw=True, save="_markers_dotplot.pdf")
```

### Heatmap

```python
sc.pl.heatmap(adata, var_names=marker_genes, groupby="cell_type",
              swap_axes=True, use_raw=True, show_gene_labels=True,
              save="_markers_heatmap.pdf")
```

### Stacked Violin

```python
flat_markers = [g for genes in marker_genes.values() for g in genes]
sc.pl.stacked_violin(adata, var_names=flat_markers, groupby="cell_type",
                     use_raw=True, swap_axes=True, save="_stacked_violin.pdf")
```

### DE Results Visualization

```python
# Top markers per cluster
sc.pl.rank_genes_groups(adata, n_genes=20, sharey=False, save="_de_overview.pdf")
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5, save="_de_dotplot.pdf")
sc.pl.rank_genes_groups_heatmap(adata, n_genes=10, use_raw=True,
                                 show_gene_labels=True, save="_de_heatmap.pdf")

# Violin for specific cluster's markers
sc.pl.rank_genes_groups_violin(adata, groups=["0"], n_genes=8, save="_de_violin.pdf")
```

## Trajectory and Pseudotime

```python
# PAGA graph
sc.pl.paga(adata, color="leiden", threshold=0.03, save="_paga.pdf")

# Pseudotime on UMAP
sc.pl.umap(adata, color="dpt_pseudotime", cmap="viridis", save="_pseudotime.pdf")

# Gene expression along pseudotime
sc.pl.umap(adata, color=["dpt_pseudotime", "leiden"], ncols=2, save="_trajectory.pdf")
```

## Multi-Panel Figures with Matplotlib

```python
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

sc.pl.umap(adata, color="leiden", ax=axes[0, 0], show=False, title="Clusters")
sc.pl.umap(adata, color="cell_type", ax=axes[0, 1], show=False, title="Cell Types")
sc.pl.umap(adata, color="n_genes_by_counts", ax=axes[0, 2], show=False, title="nGenes")
sc.pl.umap(adata, color="CD3D", ax=axes[1, 0], show=False, use_raw=True, title="CD3D")
sc.pl.umap(adata, color="CD14", ax=axes[1, 1], show=False, use_raw=True, title="CD14")
sc.pl.umap(adata, color="MS4A1", ax=axes[1, 2], show=False, use_raw=True, title="MS4A1")

plt.tight_layout()
plt.savefig("figures/multi_panel.pdf", dpi=300, bbox_inches="tight")
plt.close()
```

## Color Palette Recommendations

| Use Case | Palette | Notes |
|----------|---------|-------|
| Categorical (≤10 groups) | `"Set2"`, `"tab10"` | Colorblind-friendly |
| Categorical (>10 groups) | `"tab20"` | More colors |
| Sequential (gene expression) | `"viridis"`, `"magma"` | Perceptually uniform |
| Diverging (fold change) | `"RdBu_r"`, `"coolwarm"` | Centered at zero |
| Nature-style | `["#E64B35", "#4DBBD5", "#00A087", "#3C5488"]` | npg palette |

## Tips

1. **Always use `use_raw=True`** for gene expression plots (shows normalized, not scaled values)
2. **Use vector formats** (PDF/SVG) for publications — set `sc.settings.file_format_figs = "pdf"`
3. **`frameon=False`** removes axis box for cleaner look
4. **`legend_fontoutline=2`** adds white outline to on-data labels for readability
5. **Save then show**: use `save=` parameter, or `show=False` + `plt.savefig()` for custom layouts
6. **Consistent palettes**: use the same `palette` across all figures in a paper
