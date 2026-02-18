# Scanpy API Quick Reference

Quick lookup for commonly used scanpy functions, organized by module.

## Import

```python
import scanpy as sc
```

## Reading and Writing Data

```python
# Reading
sc.read_10x_mtx(path, var_names="gene_symbols", cache=True)  # 10X Cell Ranger directory
sc.read_10x_h5(filename)                     # 10X HDF5 file
sc.read_h5ad(filename)                       # AnnData h5ad file
sc.read_csv(filename)                        # CSV file
sc.read_loom(filename)                       # Loom file
sc.read_visium(path)                         # Visium spatial data

# Writing
adata.write("output.h5ad", compression="gzip")  # h5ad with compression
adata.write_csvs(dirname)                        # CSV directory
adata.write_loom(filename)                       # Loom format
```

## AnnData Structure

```python
adata.X                    # Expression matrix (cells x genes), sparse or dense
adata.obs                  # Cell metadata (pd.DataFrame, rows = cells)
adata.var                  # Gene metadata (pd.DataFrame, rows = genes)
adata.uns                  # Unstructured annotations (dict)
adata.obsm                 # Multi-dim cell annotations (PCA, UMAP coordinates)
adata.varm                 # Multi-dim gene annotations (PCA loadings)
adata.layers               # Named expression layers (e.g., "counts", "scaled")
adata.raw                  # Raw data backup (frozen AnnData)
adata.obs_names            # Cell barcodes (pd.Index)
adata.var_names            # Gene names (pd.Index)
adata.n_obs                # Number of cells
adata.n_vars               # Number of genes

# Slicing
adata[cell_mask, gene_mask]               # Boolean or index-based
adata[:, adata.var_names.isin(gene_list)] # Subset genes
adata[adata.obs["leiden"] == "0", :]      # Subset cells by metadata
```

## Preprocessing (sc.pp.*)

### Quality Control

```python
sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)
sc.pp.filter_cells(adata, min_genes=200)    # also: max_genes, min_counts, max_counts
sc.pp.filter_genes(adata, min_cells=3)      # also: max_cells, min_counts, max_counts
```

### Normalization

```python
sc.pp.normalize_total(adata, target_sum=1e4)          # Library-size normalization
sc.pp.log1p(adata)                                     # Log(x+1) transform
sc.pp.highly_variable_genes(adata,                     # HVG detection
    n_top_genes=2000,                                  # Number of HVGs
    flavor="seurat_v3",                                # "seurat", "seurat_v3", "cell_ranger"
    layer="counts",                                    # Which layer to use (seurat_v3)
    min_mean=0.0125, max_mean=3, min_disp=0.5,       # seurat flavor thresholds
)
```

### Scaling and Regression

```python
sc.pp.regress_out(adata, ["total_counts", "pct_counts_mt"])  # Remove confounders
sc.pp.scale(adata, max_value=10)                              # Unit variance, clip outliers
```

### Dimensionality Reduction and Neighbors

```python
sc.pp.pca(adata, n_comps=50, svd_solver="arpack", chunked=False)
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=40, method="umap")
```

### Batch Correction

```python
sc.pp.combat(adata, key="batch")  # ComBat correction
```

## Tools (sc.tl.*)

### Embeddings

```python
sc.tl.pca(adata, svd_solver="arpack", n_comps=50)
sc.tl.umap(adata, init_pos="spectral")       # also: init_pos="paga"
sc.tl.tsne(adata, perplexity=30)
sc.tl.diffmap(adata, n_comps=15)
sc.tl.draw_graph(adata, layout="fa")
```

### Clustering

```python
sc.tl.leiden(adata, resolution=0.5, flavor="igraph", n_iterations=2)
sc.tl.louvain(adata, resolution=0.5)
```

### Differential Expression

```python
sc.tl.rank_genes_groups(adata,
    groupby="leiden",
    method="wilcoxon",           # "wilcoxon", "t-test", "t-test_overestim_var", "logreg"
    use_raw=True,
    groups=["0"],                # Specific groups (optional)
    reference="rest",            # "rest" or specific group name
    mask_var="highly_variable",  # Only test HVGs (optional)
)

# Extract results
sc.get.rank_genes_groups_df(adata, group="0")          # Single group
sc.get.rank_genes_groups_df(adata, group=None)          # All groups
```

### Trajectory

```python
sc.tl.paga(adata, groups="leiden")
sc.tl.dpt(adata)                              # Requires adata.uns["iroot"]
sc.tl.diffmap(adata)
```

### Scoring

```python
sc.tl.score_genes(adata, gene_list, score_name="score")
sc.tl.score_genes_cell_cycle(adata, s_genes, g2m_genes)
sc.tl.dendrogram(adata, groupby="leiden")
sc.tl.embedding_density(adata, basis="umap", groupby="leiden")
```

## Plotting (sc.pl.*)

### Embeddings

```python
sc.pl.umap(adata, color="leiden", legend_loc="on data", frameon=False, save="_umap.pdf")
sc.pl.tsne(adata, color="gene_name", save="_tsne.pdf")
sc.pl.pca(adata, color="leiden", annotate_var_explained=True)
sc.pl.pca_variance_ratio(adata, log=True, n_pcs=50)
sc.pl.pca_loadings(adata, components=[1, 2])
```

### QC Plots

```python
sc.pl.violin(adata, ["n_genes_by_counts", "total_counts", "pct_counts_mt"], jitter=0.4, multi_panel=True)
sc.pl.scatter(adata, x="total_counts", y="pct_counts_mt")
sc.pl.highest_expr_genes(adata, n_top=20)
sc.pl.highly_variable_genes(adata)
```

### Marker Genes

```python
sc.pl.rank_genes_groups(adata, n_genes=25, sharey=False)
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5)
sc.pl.rank_genes_groups_heatmap(adata, n_genes=10, show_gene_labels=True)
sc.pl.rank_genes_groups_stacked_violin(adata, n_genes=5)
sc.pl.rank_genes_groups_matrixplot(adata, n_genes=5)
sc.pl.rank_genes_groups_violin(adata, groups="0", n_genes=8)
```

### Gene Expression Plots

```python
sc.pl.dotplot(adata, var_names=marker_dict, groupby="leiden", use_raw=True)
sc.pl.heatmap(adata, var_names=genes, groupby="leiden", swap_axes=True)
sc.pl.stacked_violin(adata, var_names=genes, groupby="leiden")
sc.pl.matrixplot(adata, var_names=genes, groupby="leiden")
sc.pl.tracksplot(adata, var_names=genes, groupby="leiden")
sc.pl.violin(adata, keys=["CD3D", "CD14"], groupby="leiden")
```

### Trajectory Plots

```python
sc.pl.paga(adata, color="leiden", threshold=0.03)
sc.pl.umap(adata, color="dpt_pseudotime")
sc.pl.embedding_density(adata, basis="umap", key="umap_density_leiden")
```

### Utility

```python
sc.pl.dendrogram(adata, groupby="leiden")
sc.pl.correlation_matrix(adata, groupby="leiden")
```

## Settings

```python
sc.settings.verbosity = 3                    # 0=error, 1=warning, 2=info, 3=hint
sc.settings.set_figure_params(dpi=80, facecolor="white")
sc.settings.set_figure_params(dpi=300, frameon=False)   # Publication quality
sc.settings.figdir = "./figures/"
sc.settings.file_format_figs = "pdf"         # "png", "pdf", "svg"
sc.settings.autoshow = False
sc.settings.autosave = True
sc.settings.n_jobs = 8                       # Parallel jobs
```

## Common Plotting Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `color` | gene name, obs column | What to color by |
| `use_raw` | `True`/`False` | Use `.raw` for gene expression |
| `palette` | `"Set2"`, `"tab20"`, custom list | Color palette |
| `cmap` | `"viridis"`, `"Reds"`, `"RdBu_r"` | Continuous colormap |
| `vmin`, `vmax` | float | Color scale limits |
| `legend_loc` | `"on data"`, `"right margin"`, `None` | Legend position |
| `frameon` | `True`/`False` | Show axis frame |
| `size` | int | Point size |
| `save` | `"_suffix.pdf"` | Save to figdir + plot_type + suffix |
