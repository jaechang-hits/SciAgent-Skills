---
name: "spatial-transcriptomics-cell-type-annotation"
description: "Spatial transcriptomics cell type annotation for single-cell-resolution platforms (Xenium, MERFISH, CosMx, SeqFISH): load Xenium outs, find and download a tissue- and disease-matched scRNA-seq reference from CELLxGENE, transfer labels with Harmony, build a per-cluster evidence table (markers + transferred labels) to name lineages then subtypes, and call spatial niches. Not for spot-based data (Visium, Slide-seq): use spatial-transcriptomics-deconvolution-cell2location."
license: "CC-BY-4.0"
---

# Spatial Cell Type Annotation (single-cell resolution)

## Overview

Annotates cells and tissue niches in imaging-based spatial data, where each
observation is one segmented cell. A tissue- and state-matched scRNA-seq
reference is pulled from CELLxGENE, its labels are transferred with Harmony,
and each cluster is then named from a table that puts its markers next to the
transferred labels. Output: an AnnData with per-cell labels, confidence and
niches, plus the evidence table behind every name.

Check the platform before anything else:

| Signal | Single-cell resolution -> this skill | Spot-based -> `spatial-transcriptomics-deconvolution-cell2location` |
|---|---|---|
| Genes | ~100-5,000 targeted panel | ~18,000-33,000 (whole transcriptome) |
| Files | `cell_feature_matrix.h5`, `cells.csv(.gz)`, `experiment.xenium` | `filtered_feature_bc_matrix.h5`, `spatial/tissue_positions*.csv` |
| Platforms | Xenium, MERFISH, CosMx, SeqFISH | Visium, Visium HD bins, Slide-seq, ST |

A spot mixes several cells; naming each spot with one label is wrong, so a
Visium request to "annotate cell types" goes to deconvolution.

## When to Use

- Naming the cell types in a Xenium, MERFISH, CosMx or SeqFISH section
- Transferring labels from a published scRNA-seq atlas onto a targeted gene panel
- Checking whether transferred labels are supported by the panel's own markers
- Finding tissue niches (tumour core, immune-rich stroma) from neighbourhood composition
- Preparing labels for spatial cell-cell communication (`spatial-transcriptomics-cell-cell-communication`)
- Use `spatial-transcriptomics-deconvolution-cell2location` instead when the data is Visium or another spot-based platform
- For dissociated scRNA-seq without coordinates, use `cell-type-annotation` instead

## Prerequisites

- **Input**: Xenium output folder (`cell_feature_matrix.h5`, `cells.csv.gz`) or an `.h5ad` with raw counts and `obsm["spatial"]`
- **Network**: CELLxGENE Discover API and Census (public, no key)
- **Python packages**: `scanpy`, `cellxgene-census`, `harmonypy`, `scikit-learn`, `squidpy` (niches only)

```bash
pip install scanpy cellxgene-census harmonypy scikit-learn squidpy
```

## Workflow

### Step 1: Load Xenium Output

```python
import pandas as pd
import scanpy as sc

XENIUM_DIR = "path/to/xenium_outs"  # folder with cell_feature_matrix.h5 + cells.csv.gz

adata = sc.read_10x_h5(f"{XENIUM_DIR}/cell_feature_matrix.h5", gex_only=False)
# Control probes/codewords are not genes; keep Gene Expression only.
adata = adata[:, adata.var["feature_types"] == "Gene Expression"].copy()
cells = pd.read_csv(f"{XENIUM_DIR}/cells.csv.gz", index_col="cell_id")
adata.obs = adata.obs.join(cells, how="left")
adata.obsm["spatial"] = adata.obs[["x_centroid", "y_centroid"]].to_numpy()  # microns

print(adata)
print(f"panel: {adata.n_vars} genes; median transcripts/cell: {adata.obs['total_counts'].median():.0f}")
```

For an `.h5ad`, `sc.read_h5ad(path)` and confirm `adata.obsm["spatial"]` and
that `X` holds raw counts (integers). Other platforms: Common Recipes.

### Step 2: Preprocess and Cluster

```python
adata.layers["counts"] = adata.X.copy()
sc.pp.filter_cells(adata, min_counts=10)
sc.pp.filter_genes(adata, min_cells=5)
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
sc.pp.pca(adata, n_comps=30)          # targeted panel: no HVG selection
sc.pp.neighbors(adata, n_neighbors=15)
sc.tl.umap(adata)
sc.tl.leiden(adata, resolution=0.5, key_added="leiden", flavor="igraph", n_iterations=2)
print(f"{adata.n_obs} cells, {adata.obs['leiden'].nunique()} clusters")
```

### Step 3: Find a Matched Reference

The reference must match tissue **and** state (healthy vs tumour vs other
disease); a mismatched reference still labels every cell confidently. Search
the public CELLxGENE metadata (~10 MB, ~15 s):

```python
import requests

datasets = requests.get("https://api.cellxgene.cziscience.com/curation/v1/datasets", timeout=120).json()

def labels(field):
    return "; ".join(x["label"] for x in field or [])

meta = pd.DataFrame([{
    "dataset_id": d["dataset_id"], "title": d.get("title"),
    "organism": labels(d.get("organism")), "tissue": labels(d.get("tissue")),
    "disease": labels(d.get("disease")), "assay": labels(d.get("assay")),
    "n_cells": d.get("cell_count"), "n_cell_types": len(d.get("cell_type") or []),
    "spatial": bool(d.get("spatial")),
} for d in datasets])

ORGANISM, TISSUE = "Homo sapiens", "lung"
STATE = "lung adenocarcinoma|non-small cell lung carcinoma"   # use "normal" for healthy tissue
hits = meta[(meta["organism"] == ORGANISM)
            & meta["tissue"].str.contains(TISSUE, case=False)
            & meta["disease"].str.contains(STATE, case=False)
            & ~meta["spatial"]
            & meta["assay"].str.contains("10x", case=False)].sort_values("n_cells", ascending=False)
print(hits[["dataset_id", "title", "disease", "n_cells", "n_cell_types"]].head(8).to_string(max_colwidth=60))
```

If nothing matches, relax `STATE` before `TISSUE`; never relax `ORGANISM`.
Show the candidates to the user rather than picking silently.

### Step 4: Download a Subsampled Reference

Full datasets can be several GB. Cap cells per type through CELLxGENE Census:

```python
import cellxgene_census
import numpy as np

DATASET_ID = "<dataset_id from Step 3>"
MAX_PER_TYPE = 300  # rare types keep all their cells

with cellxgene_census.open_soma(census_version="stable") as census:
    found = census["census_info"]["datasets"].read(
        value_filter=f"dataset_id == '{DATASET_ID}'").concat().to_pandas()
    assert len(found), "dataset is not in this Census release - pick another candidate"
    obs = census["census_data"][ORGANISM.lower().replace(" ", "_")].obs.read(
        value_filter=f"dataset_id == '{DATASET_ID}'",
        column_names=["soma_joinid", "cell_type"]).concat().to_pandas()
    rng = np.random.default_rng(0)
    keep = np.sort(obs.groupby("cell_type", observed=True)["soma_joinid"]
                      .apply(lambda s: rng.choice(s.to_numpy(), min(len(s), MAX_PER_TYPE), replace=False))
                      .explode().astype(int).to_numpy())
    ref = cellxgene_census.get_anndata(census, organism=ORGANISM, obs_coords=keep,
                                       obs_column_names=["cell_type", "disease", "donor_id"])

ref.var_names = ref.var["feature_name"].astype(str)
ref.var.index.name = None            # same name as a column blocks h5ad writing
ref.var_names_make_unique()
ref = ref[ref.obs["cell_type"] != "unknown"].copy()
ref.write_h5ad("reference.h5ad", compression="gzip")   # X holds raw counts
print(f"reference: {ref.n_obs} cells, {ref.obs['cell_type'].nunique()} types")
```

### Step 5: Transfer Labels with Harmony

Joint PCA on shared genes, Harmony to remove the platform effect, then a
classifier trained on reference cells:

```python
import harmonypy
from sklearn.neural_network import MLPClassifier

common = adata.var_names.intersection(ref.var_names)
print(f"shared genes: {len(common)}")          # < ~100 makes transfer unreliable

def prep(a, name):
    b = sc.AnnData(a[:, common].layers["counts"] if "counts" in a.layers else a[:, common].X,
                   obs=pd.DataFrame(index=a.obs_names))
    sc.pp.normalize_total(b)
    sc.pp.log1p(b)
    b.obs["dataset"] = name
    return b

combined = sc.concat([prep(adata, "spatial"), prep(ref, "reference")], index_unique="-")
sc.pp.scale(combined, max_value=10)
sc.pp.pca(combined, n_comps=30)
ho = harmonypy.run_harmony(combined.obsm["X_pca"], combined.obs, "dataset", random_state=0)
Z = np.asarray(ho.Z_corr)
combined.obsm["X_harmony"] = Z.T if Z.shape[0] != combined.n_obs else Z

is_ref = (combined.obs["dataset"] == "reference").to_numpy()
clf = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=0)
clf.fit(combined.obsm["X_harmony"][is_ref], ref.obs["cell_type"].astype(str).to_numpy())
proba = clf.predict_proba(combined.obsm["X_harmony"][~is_ref])
adata.obs["transfer_label"] = clf.classes_[proba.argmax(1)]
adata.obs["transfer_conf"] = proba.max(1)
print(adata.obs["transfer_label"].value_counts().head(15))
print(f"cells with confidence < 0.5: {(adata.obs['transfer_conf'] < 0.5).mean():.0%}")
```

### Step 6: Cluster Evidence Table, then Name Clusters

The transferred label is evidence, not the answer. Put markers and transfer
composition side by side per cluster:

```python
sc.tl.rank_genes_groups(adata, "leiden", method="wilcoxon")
markers = sc.get.rank_genes_groups_df(adata, group=None)
top_markers = (markers[markers["logfoldchanges"] > 0].groupby("group").head(8)
               .groupby("group")["names"].apply(", ".join))
comp = pd.crosstab(adata.obs["leiden"], adata.obs["transfer_label"], normalize="index")
top_transfer = comp.apply(lambda r: ", ".join(f"{k} {v:.0%}" for k, v in r.nlargest(3).items() if v >= 0.05), axis=1)

evidence = pd.DataFrame({
    "n_cells": adata.obs["leiden"].value_counts(),
    "top_markers": top_markers,
    "transferred": top_transfer,
    "median_conf": adata.obs.groupby("leiden", observed=True)["transfer_conf"].median().round(2),
}).sort_index(key=lambda i: i.astype(int))
evidence.to_csv("cluster_evidence.csv")
print(evidence.to_string())
```

Read the table and name each cluster in two passes: lineage first (epithelial,
immune, stromal, endothelial, ...), then a subtype within it. Use the subtype
only where markers support it. When markers and transfer disagree, trust the
markers and say so; with no clear signal, label `Unresolved` rather than
forcing a type.

```python
lineage = {"0": "Epithelial", "1": "Immune"}            # fill one entry per cluster
cell_type = {"0": "Alveolar type 2", "1": "Macrophage"}
adata.obs["cell_type_broad"] = adata.obs["leiden"].map(lineage).fillna("Unresolved")
adata.obs["cell_type"] = adata.obs["leiden"].map(cell_type).fillna("Unresolved")
sc.pl.embedding(adata, basis="spatial", color="cell_type", size=1, save="_celltype.png")
adata.write_h5ad("celltype_annotated.h5ad", compression="gzip")
```

### Step 7 (Optional): Spatial Niches

Group cells by the cell type composition of their neighbourhood:

```python
import squidpy as sq
from sklearn.cluster import KMeans

N_NICHES = 6
sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=15)
onehot = pd.get_dummies(adata.obs["cell_type"]).to_numpy(dtype=float)
neigh = adata.obsp["spatial_connectivities"] @ onehot
neigh = neigh / np.maximum(neigh.sum(1, keepdims=True), 1)
adata.obs["niche"] = KMeans(N_NICHES, n_init=10, random_state=0).fit_predict(neigh).astype(str)
print(pd.crosstab(adata.obs["niche"], adata.obs["cell_type"], normalize="index").round(2))
```

Name niches from that composition table (e.g. "tumour core", "immune-rich
stroma"). For graph-based domain methods see `spatial-domain-detection`.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `STATE` (Step 3) | from the user | Healthy vs disease reference; the most consequential choice |
| `MAX_PER_TYPE` | 300 | Reference size; raise for rare types, lower for speed |
| Leiden `resolution` | 0.5 | Cluster granularity that names are assigned to |
| `transfer_conf` cutoff | 0.5 | Below it, rely on markers |
| `N_NICHES` | 6 | Number of neighbourhood types |

## Common Recipes

### Recipe: Load MERFISH (Vizgen) or CosMx (NanoString) Output

```python
import squidpy as sq

# Vizgen MERSCOPE: obsm["spatial"] in microns; blank probes go to obsm["blank_genes"]
adata = sq.read.vizgen("path/to/merscope", counts_file="cell_by_gene.csv", meta_file="cell_metadata.csv")

# NanoString CosMx: obsm["spatial"] is local to each FOV; use the global one for whole-slide analysis
adata = sq.read.nanostring("path/to/cosmx", counts_file="exprMat_file.csv", meta_file="metadata_file.csv")
adata.obsm["spatial"] = adata.obsm["spatial_fov"]
adata = adata[:, ~adata.var_names.str.startswith("NegPrb")].copy()   # negative probes are not genes
print(adata)
```

Then continue from Step 2.

### Recipe: Several Sections or Samples

Correct the sample effect before clustering so clusters reflect cell types,
not slides:

```python
import harmonypy

sections = {"S1": "path/to/s1.h5ad", "S2": "path/to/s2.h5ad"}
adata = sc.concat({k: sc.read_h5ad(v) for k, v in sections.items()}, label="sample", index_unique="-")
adata.layers["counts"] = adata.X.copy()
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
sc.pp.pca(adata, n_comps=30)
ho = harmonypy.run_harmony(adata.obsm["X_pca"], adata.obs, "sample", random_state=0)
Z = np.asarray(ho.Z_corr)
adata.obsm["X_pca_harmony"] = Z.T if Z.shape[0] != adata.n_obs else Z
sc.pp.neighbors(adata, use_rep="X_pca_harmony")
sc.tl.leiden(adata, resolution=0.5, flavor="igraph", n_iterations=2)
print(pd.crosstab(adata.obs["leiden"], adata.obs["sample"]))
```

### Recipe: Marker-Only Annotation (no suitable reference)

When no reference matches the tissue and state, score a canonical marker
panel per cluster and name clusters from that table instead of Step 5:

```python
panel = {                       # canonical markers for the user's tissue; keep genes on the panel
    "Epithelial": ["EPCAM", "KRT8", "KRT18"],
    "T cell": ["CD3E", "CD3D", "TRAC"],
    "Macrophage": ["CD68", "CD163", "C1QA"],
    "Fibroblast": ["COL1A1", "DCN", "LUM"],
    "Endothelial": ["PECAM1", "VWF", "CDH5"],
}
panel = {ct: [g for g in genes if g in adata.var_names] for ct, genes in panel.items()}
for ct, genes in panel.items():
    if len(genes) >= 2:
        sc.tl.score_genes(adata, genes, score_name=f"score_{ct}")
scores = adata.obs.filter(like="score_").groupby(adata.obs["leiden"], observed=True).mean()
print(scores.round(2).assign(best=scores.idxmax(axis=1).str.removeprefix("score_")))
```

## Expected Outputs

- `reference.h5ad` - subsampled reference (raw counts)
- `cluster_evidence.csv` - markers + transferred labels per cluster
- `celltype_annotated.h5ad` - `transfer_label`, `transfer_conf`, `cell_type_broad`, `cell_type`, `niche`
- `figures/` - spatial cell type map

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Few shared genes | Gene symbols differ (Ensembl IDs, case) | Map to symbols; `var["feature_name"]` holds symbols in Census data |
| Most cells < 0.5 confidence | Reference lacks the tissue's states | Pick a disease-matched reference; fall back to markers |
| `dataset is not in this Census release` | Dataset newer than Census | Pick the next candidate |
| Clusters split by sample | Batch effect | See the "Several Sections or Samples" recipe |
| Leiden very slow | >200k cells | Cluster a subsample, then `sc.tl.ingest` the rest |
| CosMx cells overlap on one spot | Local FOV coordinates used | Set `obsm["spatial"] = obsm["spatial_fov"]` |

## Related Skills

- `spatial-transcriptomics-deconvolution-cell2location` - spot-based platforms
- `spatial-transcriptomics-cell-cell-communication` - interactions between the annotated types
- `spatial-domain-detection` - graph-based tissue domains
- `cell-type-annotation` - dissociated scRNA-seq annotation strategy

## References

- CZ CELLxGENE Census documentation: https://chanzuckerberg.github.io/cellxgene-census/
- CELLxGENE Discover Curation API: https://api.cellxgene.cziscience.com/curation/ui/
- Korsunsky et al. (2019) Harmony, Nature Methods: https://doi.org/10.1038/s41592-019-0619-0
- harmonypy: https://github.com/slowkow/harmonypy
- squidpy readers for Vizgen and NanoString: https://squidpy.readthedocs.io/en/stable/api/squidpy.read.vizgen.html
