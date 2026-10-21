---
name: "cellphonedb-cell-cell-interaction"
description: "CellPhoneDB v5 ligand-receptor interaction inference between annotated cell types: download the curated database, write meta/counts inputs, run the simple (means), statistical (permutation p-values) or DEG-based method, restrict to spatial microenvironments, filter by cell type pair or gene, and export count heatmaps and dotplots. Works on scRNA-seq and annotated single-cell-resolution spatial data (Xenium, MERFISH, CosMx); human gene symbols required (mouse via ortholog mapping). For multi-method consensus ranking or spatial local scores use liana-spatial-cell-cell-communication; for the end-to-end spatial workflow use spatial-transcriptomics-cell-cell-communication."
license: "CC-BY-4.0"
---

# CellPhoneDB Cell-Cell Interaction Analysis

## Overview

CellPhoneDB scores each curated ligand-receptor (LR) pair, including
multi-subunit complexes, for every ordered pair of cell types. Its statistical
method tests whether the pair's mean expression is specific to that cell type
pair by shuffling cell labels. Output: means, permutation p-values and
specificity scores per interaction and cell type pair, a filtered long table,
and heatmap / dotplot figures.

| Method | Call | Use when |
|---|---|---|
| 1. Simple | `cpdb_analysis_method` | Quick look, no statistics |
| 2. Statistical | `cpdb_statistical_analysis_method` | Discovery; permutation p-values |
| 3. DEG-based | `cpdb_degs_analysis_method` | Interactions driven by genes up in a given cell type (e.g. disease-specific) |

## When to Use

- Testing which ligand-receptor pairs are specific to a sender-receiver cell type pair, with p-values
- Including multi-subunit receptor complexes in the interaction search
- Restricting tests to cell types that share a spatial region (microenvironments)
- Focusing on interactions driven by genes up-regulated in one cell type or condition (DEG method)
- Comparing interactions between conditions such as normal vs tumour
- Use `spatial-transcriptomics-cell-cell-communication` instead for a multi-method LIANA ranking with a spatial adjacency filter
- For multi-sample tensor decomposition or MISTy, use `liana-spatial-cell-cell-communication`

## Prerequisites

- **Input**: AnnData (`.h5ad`) with a cell type column in `obs`
- **Expression**: normalised (`normalize_total` + `log1p` is fine), not z-scored
- **Genes**: human HGNC symbols in `var_names`; mouse data needs Step 2
- **Database**: downloaded from the `ventolab/cellphonedb-data` GitHub releases
  on first use (Step 1)
- **Python packages**: `cellphonedb` (v5), `scanpy`, `seaborn`; `liana` for mouse ortholog mapping

```bash
pip install cellphonedb scanpy seaborn liana
```

## Workflow

1. Download the database
2. Prepare inputs (labels, normalisation, gene symbols)
3. (Optional) Spatial microenvironments
4. Run the analysis (method 1, 2 or 3)
5. Filter results by cell types or genes
6. Plot

### Step 1: Download the Database

```python
import os
from cellphonedb.utils import db_utils

CPDB_VERSION = "v5.0.0"                                   # releases: github.com/ventolab/cellphonedb-data/releases
CPDB_DIR = os.path.abspath(f"ref_cache/cellphonedb/{CPDB_VERSION}")
CPDB_ZIP = os.path.join(CPDB_DIR, "cellphonedb.zip")
if not os.path.exists(CPDB_ZIP):
    os.makedirs(CPDB_DIR, exist_ok=True)
    db_utils.download_database(CPDB_DIR, CPDB_VERSION)
print(CPDB_ZIP, os.path.exists(CPDB_ZIP))
```

### Step 2: Prepare Inputs

```python
import numpy as np
import pandas as pd
import scanpy as sc

adata = sc.read_h5ad("celltype_annotated.h5ad")
CELL_TYPE_KEY = "cell_type"
OUT = "cellphonedb"
os.makedirs(OUT, exist_ok=True)

labels = adata.obs[CELL_TYPE_KEY].astype(str)
assert not labels.str.contains(r"\|").any(), "'|' is the result separator; rename those cell types"
print(labels.value_counts())

# Normalised, not z-scored. Raw integer counts -> normalise + log1p here.
sample = adata.X[:500]
sample = sample.toarray() if hasattr(sample, "toarray") else np.asarray(sample)
if np.allclose(sample, np.round(sample)) and sample.max() > 20:
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

counts = sc.AnnData(X=adata.X, obs=pd.DataFrame(index=adata.obs_names), var=pd.DataFrame(index=adata.var_names))
counts.write_h5ad(f"{OUT}/counts.h5ad")
pd.DataFrame({"barcode_sample": adata.obs_names, "cell_type": labels.values}).to_csv(
    f"{OUT}/meta.tsv", sep="\t", index=False)
print(counts)
```

**Mouse data.** The database is human-only. Map mouse symbols to human with
the HGNC HCOP ortholog table (via liana, `pip install liana` if missing), keep
one-to-one matches, and rename before writing `counts.h5ad`:

```python
import liana as li

hcop = li.rs.get_hcop_orthologs(target_organism="mouse", columns=["human_symbol", "mouse_symbol"],
                                min_evidence=3)
one2one = hcop.drop_duplicates("mouse_symbol", keep=False).drop_duplicates("human_symbol", keep=False)
m2h = dict(zip(one2one["mouse_symbol"], one2one["human_symbol"]))
keep = [g for g in adata.var_names if g in m2h]
adata = adata[:, keep].copy()
adata.var_names = [m2h[g] for g in keep]
print(f"{len(keep)} mouse genes mapped 1:1 to human")
```

### Step 3 (Optional): Spatial Microenvironments

A microenvironment file lists which **cell types** share a region; CellPhoneDB
then only tests pairs of types found together in at least one region. Build it
from a region/niche column (from `spatial-domain-detection` or the niche step
of `spatial-transcriptomics-cell-type-annotation`):

```python
REGION_KEY = "niche"
MIN_FRAC = 0.02          # a type counts as present in a region above 2% of its cells

comp = pd.crosstab(adata.obs[REGION_KEY].astype(str), labels, normalize="index")
comp_long = comp.stack().reset_index()
comp_long.columns = ["microenvironment", "cell_type", "frac"]
microenvs = comp_long[comp_long["frac"] >= MIN_FRAC][["cell_type", "microenvironment"]]
microenvs.to_csv(f"{OUT}/microenvs.tsv", sep="\t", index=False)
print(microenvs.groupby("microenvironment")["cell_type"].apply(list))
```

### Step 4: Run the Analysis

Method 2 (statistical). For method 1 import `cpdb_analysis_method` and drop
`iterations`, `debug_seed`, `pvalue` and the `subsampling*` arguments.

```python
from cellphonedb.src.core.methods import cpdb_statistical_analysis_method

USE_MICROENVS = os.path.exists(f"{OUT}/microenvs.tsv")
res = cpdb_statistical_analysis_method.call(
    cpdb_file_path=CPDB_ZIP,
    meta_file_path=f"{OUT}/meta.tsv",
    counts_file_path=f"{OUT}/counts.h5ad",
    counts_data="hgnc_symbol",
    microenvs_file_path=f"{OUT}/microenvs.tsv" if USE_MICROENVS else None,
    score_interactions=True,       # 0-100 specificity score
    iterations=1000,
    threshold=0.1,                 # min fraction of a cell type expressing each gene
    threads=4,
    debug_seed=42,
    pvalue=0.05,
    subsampling=False,             # >~100k cells: True, subsampling_num_cells=..., subsampling_log=False for log data
    output_path=OUT,
    output_suffix="stat",
)
print(list(res.keys()))
sig = res["significant_means"]
pair_cols = [c for c in sig.columns if c.count("|") == 1 and set(c.split("|")) <= set(labels.unique())]
print(f"{len(sig)} interactions tested, "
      f"{int(sig[pair_cols].notna().any(axis=1).sum())} significant in >= 1 cell type pair")
```

Method 3 (DEG-based): write up-regulated genes per cell type, then call
`cpdb_degs_analysis_method.call(..., degs_file_path=f"{OUT}/degs.tsv")` with
the same arguments minus `iterations`, `debug_seed`, `pvalue` and
`subsampling*`. Its result has `relevant_interactions` (1/0 per pair) in place
of `pvalues`.

```python
sc.tl.rank_genes_groups(adata, CELL_TYPE_KEY, method="wilcoxon")
degs = sc.get.rank_genes_groups_df(adata, group=None)
degs = degs[(degs["pvals_adj"] < 0.05) & (degs["logfoldchanges"] > 0.25)]   # up-regulated only
degs[["group", "names"]].rename(columns={"group": "cluster", "names": "gene"}).to_csv(
    f"{OUT}/degs.tsv", sep="\t", index=False)
print(degs.groupby("group").size())
```

### Step 5: Filter Results

Convert to a long table, then filter on exact cell type and gene matches:

```python
dec = res["deconvoluted"]
genes_per_int = dec.groupby("id_cp_interaction")["gene_name"].apply(lambda s: set(s.dropna()))
meta_cols = ["id_cp_interaction", "interacting_pair", "partner_a", "partner_b", "secreted",
             "receptor_a", "receptor_b"]
meta_cols = [c for c in meta_cols if c in sig.columns]
long = sig.melt(id_vars=meta_cols, value_vars=pair_cols, var_name="pair", value_name="mean").dropna(subset=["mean"])
pv = res["pvalues"].melt(id_vars=["id_cp_interaction"], value_vars=pair_cols, var_name="pair", value_name="pval")
long = long.merge(pv, on=["id_cp_interaction", "pair"], how="left")
long[["cell_a", "cell_b"]] = long["pair"].str.split("|", expand=True)
if "interaction_scores" in res and "id_cp_interaction" in res["interaction_scores"]:
    sc_long = res["interaction_scores"].melt(id_vars=["id_cp_interaction"], value_vars=pair_cols,
                                             var_name="pair", value_name="score")
    long = long.merge(sc_long, on=["id_cp_interaction", "pair"], how="left")
long["genes"] = long["id_cp_interaction"].map(genes_per_int)
long.to_csv(f"{OUT}/significant_long.csv", index=False)

CELL_TYPES = {"T cell", "Macrophage"}          # empty set = all
GENES = {"CD40", "CD40LG", "CD274", "PDCD1"}   # exact symbols; empty set = all
mask = pd.Series(True, index=long.index)
if CELL_TYPES:
    mask &= long["cell_a"].isin(CELL_TYPES) | long["cell_b"].isin(CELL_TYPES)
if GENES:
    mask &= long["genes"].map(lambda g: isinstance(g, set) and bool(g & GENES))
hit = long[mask]
hit.sort_values("mean", ascending=False).to_csv(f"{OUT}/cellphonedb_filtered.csv", index=False)
print(hit.sort_values("mean", ascending=False).head(20)[["interacting_pair", "pair", "mean", "pval"]])
```

`cell_a` expresses `partner_a` and `cell_b` expresses `partner_b`; read the
`receptor_a`/`receptor_b` flags for the signalling direction, since partner A
is not always the ligand. `cellphonedb.utils.search_utils.search_analysis_results`
is the built-in alternative for the same filtering.

### Step 6: Plot

```python
import matplotlib.pyplot as plt
import seaborn as sns

n_sig = long.groupby(["cell_a", "cell_b"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(9, 8))
sns.heatmap(n_sig, cmap="YlOrRd", annot=True, fmt="d", ax=ax)
ax.set_title("Significant interactions (row: partner A cell, col: partner B cell)")
plt.tight_layout(); plt.savefig(f"{OUT}/cellphonedb_heatmap.png", dpi=150); plt.close()

TOP_N = 30
sub = hit if len(hit) else long
top = sub.groupby("interacting_pair")["mean"].max().nlargest(TOP_N).index
d = sub[sub["interacting_pair"].isin(top)].copy()
d["-log10p"] = -np.log10(d["pval"].clip(lower=1e-3))
fig, ax = plt.subplots(figsize=(max(8, 0.35 * d["pair"].nunique()), max(6, 0.3 * TOP_N)))
s = ax.scatter(d["pair"], d["interacting_pair"], c=d["mean"], s=20 + 40 * d["-log10p"], cmap="Reds")
plt.colorbar(s, label="mean expression"); plt.xticks(rotation=90)
plt.tight_layout(); plt.savefig(f"{OUT}/cellphonedb_dotplot.png", dpi=150); plt.close()
```

`ktplotspy` (`pip install ktplotspy`) offers publication-style
`plot_cpdb_heatmap` / `plot_cpdb` from the same `res` tables.

## Interpreting Results

| Signal | Meaning |
|---|---|
| Low p-value, high mean | Expressed and specific to this cell type pair - strongest candidates |
| High mean, p >= 0.05 | Broadly expressed; not specific to this pair |
| High `interaction_scores` (0-100) | Partners specific to these two types relative to all types |
| `secreted == True` | Ligand can act at a distance; membrane-bound pairs need contact |
| Microenvironment restriction | Pairs of types never co-located are not tested |

Expression of both partners does not prove signalling; report results as
candidates and check spatial adjacency (`spatial-transcriptomics-cell-cell-communication`, Step 3).

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `threshold` | 0.1 | Min fraction of a cell type expressing each partner gene |
| `iterations` | 1000 | Label permutations; fewer = coarser p-values |
| `pvalue` | 0.05 | Significance cutoff for `significant_means` |
| `MIN_FRAC` (microenvs) | 0.02 | Presence cutoff for a type in a region |
| DEG cutoffs (method 3) | adj p < 0.05, logFC > 0.25 | Which genes count as up-regulated |
| `subsampling_num_cells` | 1/3 of cells | Geometric sketching size for large datasets |

## Common Recipes

### Recipe: Compare Two Conditions

Run the statistical method separately per condition with the same database and
parameters, then compare which interactions are significant where:

```python
CONDITION_KEY = "condition"
sig_by_cond = {}
for cond in adata.obs[CONDITION_KEY].unique():
    d = f"{OUT}/{cond}"; os.makedirs(d, exist_ok=True)
    a = adata[adata.obs[CONDITION_KEY] == cond]
    sc.AnnData(X=a.X, obs=pd.DataFrame(index=a.obs_names), var=pd.DataFrame(index=a.var_names)).write_h5ad(f"{d}/counts.h5ad")
    pd.DataFrame({"barcode_sample": a.obs_names, "cell_type": a.obs[CELL_TYPE_KEY].astype(str).values}).to_csv(
        f"{d}/meta.tsv", sep="\t", index=False)
    r = cpdb_statistical_analysis_method.call(
        cpdb_file_path=CPDB_ZIP, meta_file_path=f"{d}/meta.tsv", counts_file_path=f"{d}/counts.h5ad",
        counts_data="hgnc_symbol", iterations=1000, threshold=0.1, threads=4, debug_seed=42,
        pvalue=0.05, output_path=d, output_suffix=str(cond))
    s = r["significant_means"]
    cols = [c for c in s.columns if c.count("|") == 1]
    sig_by_cond[cond] = set(s.melt(id_vars=["interacting_pair"], value_vars=cols).dropna(subset=["value"])
                            .apply(lambda x: f"{x['variable']}: {x['interacting_pair']}", axis=1))
c1, c2 = list(sig_by_cond)[:2]
print(f"only in {c1}: {len(sig_by_cond[c1] - sig_by_cond[c2])}; only in {c2}: {len(sig_by_cond[c2] - sig_by_cond[c1])}")
pd.Series(sorted(sig_by_cond[c2] - sig_by_cond[c1])).to_csv(f"{OUT}/only_in_{c2}.csv", index=False)
```

Presence in one condition and absence in the other is descriptive; cell
numbers per type differ between conditions and change the power of each test.

### Recipe: Keep Spatially Adjacent Cell Type Pairs

On spatial data, keep significant interactions whose two cell types are
neighbours more often than chance (`pip install squidpy`):

```python
import squidpy as sq

adata.obs[CELL_TYPE_KEY] = adata.obs[CELL_TYPE_KEY].astype("category")
sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=15)
sq.gr.nhood_enrichment(adata, cluster_key=CELL_TYPE_KEY, n_perms=1000, seed=0)
cats = adata.obs[CELL_TYPE_KEY].cat.categories
z = pd.DataFrame(adata.uns[f"{CELL_TYPE_KEY}_nhood_enrichment"]["zscore"], index=cats, columns=cats)
sig_long = long[long["pval"] < 0.05].copy()
sig_long["neighbour_z"] = [z.loc[a, b] for a, b in zip(sig_long["cell_a"], sig_long["cell_b"])]
adjacent = sig_long[(sig_long["neighbour_z"] > 2) | (sig_long["cell_a"] == sig_long["cell_b"])]
adjacent.to_csv(f"{OUT}/cellphonedb_adjacent.csv", index=False)
print(f"{len(adjacent)} of {len(sig_long)} significant interactions are between co-located types")
```

## Expected Outputs

- `ref_cache/cellphonedb/v5.0.0/cellphonedb.zip` - database (cached)
- `cellphonedb/meta.tsv`, `counts.h5ad`, `microenvs.tsv`, `degs.tsv` - inputs
- `cellphonedb/statistical_analysis_*_stat.txt` - CellPhoneDB tables (means, pvalues, significant_means, deconvoluted, interaction_scores)
- `cellphonedb/significant_long.csv` - long-format significant interactions
- `cellphonedb/cellphonedb_filtered.csv` - filtered subset
- `cellphonedb/cellphonedb_heatmap.png`, `cellphonedb_dotplot.png`
- `cellphonedb/cellphonedb_adjacent.csv` - significant interactions between co-located types (recipe)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Almost no interactions | Mouse or Ensembl IDs in `var_names` | Map to human HGNC symbols (Step 2) |
| `Some clusters/cell_types in microenvironments file are not present in metadata` | Label mismatch between files | Build both files from the same `labels` series |
| Very slow / out of memory | Many cells | `subsampling=True` with `subsampling_num_cells`; raise `threads` |
| Results dominated by housekeeping-like pairs | Data was z-scored or not normalised | Use normalised (log) expression, not scaled data |
| `download_database` fails | No network access to GitHub | Download `cellphonedb.zip` from the release page manually into `CPDB_DIR` |
| Pair columns missing a cell type | Type below `threshold` for all genes or absent from microenvs | Check `value_counts`; lower `MIN_FRAC` |

## Related Skills

- `spatial-transcriptomics-cell-cell-communication` - LIANA ranking + spatial adjacency on the tissue
- `liana-spatial-cell-cell-communication` - consensus ranking, multi-sample and spatial LIANA methods
- `spatial-single-cell-ligand-receptor-discovery` - pathway-focused queries and evidence for candidate pairs
- `spatial-transcriptomics-cell-type-annotation` - cell type labels and niches used here
- `spatial-transcriptomics-analysis-squidpy` - neighbourhood enrichment to check co-location

## References

- Troule et al. (2025) CellPhoneDB v5, Nature Protocols: https://doi.org/10.1038/s41596-024-01137-1
- Efremova et al. (2020) CellPhoneDB, Nature Protocols: https://doi.org/10.1038/s41596-020-0292-x
- CellPhoneDB documentation: https://cellphonedb.readthedocs.io/en/latest/
- CellPhoneDB source and tutorials: https://github.com/ventolab/CellphoneDB
- CellPhoneDB database releases: https://github.com/ventolab/cellphonedb-data
