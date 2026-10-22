---
name: "spatial-transcriptomics-cell-type-annotation"
description: "Spatial transcriptomics cell type annotation for single-cell-resolution platforms (Xenium, MERFISH, CosMx, SeqFISH): CELLxGENE reference download, Harmony label transfer, per-cluster marker evidence naming lineages then subtypes, spatial niches. Visium/Slide-seq spots: GPU -> spatial-transcriptomics-deconvolution-cell2location; CPU -> spatial-mapping-tangram (cell types: per-spot proportions); no reference -> spatial-domain-detection (regions: domains from markers). Beyond labels (microenvironment, arrangement, spatial patterns): read spatial-transcriptomics-analysis-squidpy before asking the user."
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
# Install only what `import` reports missing. 
pixi add --pypi harmonypy cellxgene-census   # scanpy, scikit-learn are usually present
pixi add --pypi squidpy                      # Step 7 (niches) only
```

## Pre-flight Interview

```yaml
decisions:
  - id: D1
    param: STATE
    kind: required
    source: user
    ask: "Which tissue, and in what state (healthy, or which tumour or disease)?"
    default: null

  - id: D2
    param: referenceSource
    kind: required
    source: user
    ask: "Do you have a matched scRNA/snRNA-seq reference (h5ad with raw counts and a cell type column), or should I search public data (CELLxGENE) for one?"
    default: null

  - id: D3
    param: annotationRoute
    kind: required
    source: user
    ask: "Transfer labels from a reference (recommended, slow; CellTypist only if installing the transfer tools fails), run CellTypist (fast, not recommended: less accurate on this panel), or name clusters from markers only?"
    default: null

  - id: D4
    param: MIN_COUNTS
    kind: optional
    source: user
    ask: "Keep cells with at least how many transcripts?"
    default: "10"
```

Ask D1-D3 together, and give each D3 option its cost:

- **Reference transfer (recommended, slow)**: Harmony + classifier (Step 5),
  Tangram or scANVI, installed at run time. Fetching a public reference is not
  guaranteed: install, query and download take minutes or longer, and the
  dataset can be missing from Census or exhaust memory (Step 4). Transfer is
  also long: on ~154k cells, UMAP took ~45 s and Leiden ~2 min before Harmony
  and training even start. Install the transfer tools first, even though
  CellTypist is pre-installed. Only if that install or import fails, stop,
  tell the user the error, then fall back to CellTypist with the caveat below
  and say so in the result.
- **CellTypist (fast, not recommended)**: pre-installed, but its models are
  trained on whole-transcriptome scRNA-seq, so on a targeted panel only the
  overlapping genes are used and labels are less accurate. State this
  whenever its labels are reported, and check them with markers (Step 6).
- **Markers only**: no reference; see the Marker-Only recipe.

When the user asks whether anything else must be uploaded, answer from D2:
the Xenium output is enough to start, and a matched reference of their own is
the fastest and most reliable route. Never describe the reference fetch or the
transfer as immediate or guaranteed.

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

### Step 2: QC, Preprocess and Cluster

A targeted panel gives few transcripts per cell, so QC is per cell and
lenient: high cutoffs or gene filtering remove small and rare cells. Look at
the distributions first:

```python
import numpy as np

obs = adata.obs
obs["n_counts"] = np.asarray(adata.X.sum(axis=1)).ravel()
obs["n_genes"] = np.asarray((adata.X > 0).sum(axis=1)).ravel()
neg_cols = [c for c in ("control_probe_counts", "control_codeword_counts", "unassigned_codeword_counts") if c in obs]
if neg_cols:  # Xenium cells.csv; absent for MERFISH/CosMx loaded via squidpy
    neg = obs[neg_cols].sum(axis=1)
    obs["neg_frac"] = neg / (obs["n_counts"] + neg).clip(lower=1)
if {"cell_area", "nucleus_area"} <= set(obs):
    obs["nucleus_ratio"] = obs["nucleus_area"] / obs["cell_area"]
cols = [c for c in ("n_counts", "n_genes", "cell_area", "nucleus_ratio", "neg_frac") if c in obs]
print(obs[cols].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99]).round(3))
```

Check segmentation before reading clusters. Transcripts leaking between
neighbouring cells show up as cells positive for two exclusive lineages:

```python
pairs = [("EPCAM", "PTPRC"), ("PECAM1", "PTPRC"), ("COL1A1", "PTPRC"), ("EPCAM", "PECAM1")]
for a, b in pairs:  # mutually exclusive lineage markers; swap in ones on the panel
    if a in adata.var_names and b in adata.var_names:
        pos = (adata[:, [a, b]].X > 0).toarray()
        pa, pb = pos.mean(axis=0)
        print(f"{a}+{b}+: {(pos[:, 0] & pos[:, 1]).mean():.1%} of cells (by chance: {pa * pb:.1%})")
```

Double positives well above the chance rate mean leakage. Mixed clusters and
mixed transferred labels (Step 6) then reflect segmentation, not biology: report
it as such, and consider nucleus-only counts or re-segmentation (e.g. Baysor,
ProSeg) before naming subtypes.

```python
MIN_COUNTS = 10       # 10-20; higher drops small and rare cells on a small panel
MAX_NEG_FRAC = 0.05   # cells dominated by control probes / unassigned codewords
keep = obs["n_counts"] >= MIN_COUNTS
if "neg_frac" in obs:
    keep &= obs["neg_frac"] <= MAX_NEG_FRAC
if "cell_area" in obs:
    keep &= obs["cell_area"] <= obs["cell_area"].quantile(0.995)  # merged-cell outliers
print(f"keep {keep.sum()} / {adata.n_obs} cells")
adata = adata[keep.to_numpy()].copy()

adata.layers["counts"] = adata.X.copy()
sc.pp.filter_genes(adata, min_cells=5)
sc.pp.normalize_total(adata)          # SCTransform (Seurat, R) is the alternative
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
Show the candidates to the user rather than picking silently. Prefer
whole-tissue datasets with many cell types: a one-compartment subset
("Myeloid cells", "T cells") cannot label the other lineages. Do not pick a
smaller dataset to save memory - Step 4 fetches only panel genes and a capped
number of cells. Each catalog entry's `assets` holds the h5ad download URL.

### Step 4: Download a Subsampled Reference

Full datasets are several GB; label transfer needs neither all ~60k genes nor
all cells. Query CELLxGENE Census for the panel genes only (`var_value_filter`)
and a capped number of cells per type, reading `obs` first to sample.

Run the query in a separate Python process. After clustering, the notebook
kernel is often near its memory limit, and TileDB-SOMA's read buffers then fail
with `std::bad_alloc` even on a small dataset. A child process gets its own
limit and frees everything on exit; the kernel only reads `reference.h5ad`.
It still shares the machine's RAM, so `del` large objects you no longer need
first. Run the child with the interpreter that has `cellxgene_census`, not a
bare `python`:

```python
import gc
import json
import pathlib
import subprocess

import cellxgene_census

DATASET_ID = "<dataset_id from Step 3>"  # or None to pool every matching dataset
DISEASES = ["normal"]                    # pooled mode only: exact disease labels from Step 3's metadata
MAX_PER_TYPE = 2000                      # a few thousand per type is enough; rare types keep all
CENSUS_VERSION = "2025-11-08"            # pin a release; "stable" moves between runs
# Panel genes only: ~100x less data. Use None (and MAX_PER_TYPE ~300) when the reference
# needs every gene (spatial-panel-design, cell2location, Tangram).
GENES = list(adata.var_names)

FETCH_SCRIPT = r'''
import json, sys
import numpy as np
import cellxgene_census

p = json.load(open(sys.argv[1]))
if p["dataset_id"]:
    # Not is_primary_data: integrated atlases (LuCA, HLCA) mark their cells False.
    obs_filter = f"dataset_id == '{p['dataset_id']}'"
else:
    # Pooled: is_primary_data drops cells re-deposited in several datasets.
    obs_filter = (f"tissue_general == '{p['tissue']}' and disease in {p['diseases']} "
                  "and is_primary_data == True")
# Read buffers default to 1 GiB per column; 128 MiB fits under a per-process memory cap.
buffers = {"soma.init_buffer_bytes": 128 * 1024**2, "py.init_buffer_bytes": 128 * 1024**2}
with cellxgene_census.open_soma(census_version=p["census_version"], tiledb_config=buffers) as census:
    obs = census["census_data"][p["organism"].lower().replace(" ", "_")].obs.read(
        value_filter=obs_filter, column_names=["soma_joinid", "cell_type"]).concat().to_pandas()
    if obs.empty:
        sys.exit("no cells match - dataset not in this Census release (download its h5ad below)")
    rng = np.random.default_rng(0)
    keep = np.sort(obs.groupby("cell_type", observed=True)["soma_joinid"]
                      .apply(lambda s: rng.choice(s.to_numpy(), min(len(s), p["max_per_type"]), replace=False))
                      .explode().astype(int).to_numpy())
    genes = p["genes"]
    ref = cellxgene_census.get_anndata(census, organism=p["organism"], obs_coords=keep,
                                       var_value_filter=None if genes is None else f"feature_name in {genes}",
                                       obs_column_names=["cell_type", "disease", "donor_id"])
ref.var_names = ref.var["feature_name"].astype(str)
ref.var.index.name = None            # same name as a column blocks h5ad writing
ref.var_names_make_unique()
ref = ref[ref.obs["cell_type"] != "unknown"].copy()
ref.write_h5ad(p["out"], compression="gzip")   # X holds raw counts
print(f"reference: {ref.n_obs} cells, {ref.n_vars} genes, {ref.obs['cell_type'].nunique()} types")
'''

params = {"dataset_id": DATASET_ID, "diseases": DISEASES, "tissue": TISSUE, "organism": ORGANISM,
          "max_per_type": MAX_PER_TYPE, "census_version": CENSUS_VERSION, "genes": GENES,
          "out": "reference.h5ad"}
pathlib.Path("/tmp/census_params.json").write_text(json.dumps(params))
pathlib.Path("/tmp/fetch_reference.py").write_text(FETCH_SCRIPT)

# <env>/lib/pythonX.Y/site-packages/cellxgene_census/__init__.py -> <env>/bin/python
py = pathlib.Path(cellxgene_census.__file__).parents[4] / "bin" / "python"
gc.collect()
res = subprocess.run([str(py), "/tmp/fetch_reference.py", "/tmp/census_params.json"],
                     capture_output=True, text=True, timeout=1800)
print(res.stdout[-2000:], res.stderr[-2000:])
res.check_returncode()
ref = sc.read_h5ad("reference.h5ad")
```

**One dataset's h5ad instead** (not in Census, or Census still fails): this is
the next step, before any CellTypist fallback. Download the file from the
`assets` URL in Step 3's catalog entry, open it without loading `X`, and keep
only sampled cells and panel genes. Read rows in chunks - a row slice loads
every gene. If the kernel is short on memory, run this the same way, as a
script with `py`:

```python
import anndata as ad
import scipy.sparse as sp

full = ad.read_h5ad("dataset.h5ad", backed="r")
rng = np.random.default_rng(0)
ct = full.obs["cell_type"].to_numpy()
rows = np.sort(np.concatenate([rng.choice(np.flatnonzero(ct == t), min((ct == t).sum(), MAX_PER_TYPE), replace=False)
                               for t in np.unique(ct)]))
src = full.raw if full.raw is not None else full     # raw.X holds counts when X is normalized
symbols = src.var["feature_name"].astype(str).to_numpy()   # var index is Ensembl IDs
cols = np.flatnonzero(np.isin(symbols, GENES))
counts = sp.vstack([sp.csr_matrix(src.X[rows[i:i + 5000]])[:, cols] for i in range(0, len(rows), 5000)])
ref = ad.AnnData(counts.tocsr(), obs=full.obs.iloc[rows][["cell_type", "disease", "donor_id"]].copy(),
                 var=pd.DataFrame(index=symbols[cols]))
ref.var_names_make_unique()
ref = ref[ref.obs["cell_type"] != "unknown"].copy()
ref.write_h5ad("reference.h5ad", compression="gzip")
print(f"reference: {ref.n_obs} cells x {ref.n_vars} panel genes")
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
| `MIN_COUNTS` (Step 2) | 10 | Keep 10-20; higher drops small and rare cells |
| `MAX_NEG_FRAC` (Step 2) | 0.05 | Max share of control probe / unassigned codeword counts per cell |
| `STATE` (Step 3) | from the user | Healthy vs disease reference; the most consequential choice |
| `MAX_PER_TYPE` (Step 4) | 2000 | Reference cells per type; 2,000-5,000 is enough, rare types keep all |
| `GENES` (Step 4) | panel genes | Genes fetched from the reference; `None` only when every gene is needed |
| Leiden `resolution` | 0.5 | Cluster granularity that names are assigned to |
| `transfer_conf` cutoff | 0.5 | Below it, rely on markers |
| `N_NICHES` | 6 | Number of neighbourhood types |

## Key Concepts

### Annotation Routes

| Route | Use when | Tools |
|---|---|---|
| (a) Reference label transfer - the most common | A tissue- and state-matched scRNA/snRNA-seq reference exists; transfer on the shared panel genes | Seurat `FindTransferAnchors` / `TransferData` (R), scANVI / scArches (scvi-tools), Tangram; this skill uses Harmony + a classifier (Step 5) |
| (b) Marker-based manual | No matching reference, or to check (a) | Step 6 evidence table; Marker-Only recipe |
| (c) Deconvolution, as a supplement | Regions where segmentation is unreliable (dense tissue, merged cells) | RCTD (spacexr), cell2location |
| (d) Pre-trained classifier - not reference transfer | Fast first look, or fallback when (a) cannot be installed | CellTypist |

Transfer only sees genes that are both on the panel and in the reference.
CellTypist is not route (a): it applies a fixed model trained on
whole-transcriptome scRNA-seq, not the user's chosen reference, so on a panel
only the overlapping genes are used and labels are less accurate. Never use it
in place of an approved (a); confirm its labels with markers (Step 6).

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
| Many cells removed at QC | Cutoffs too strict for a targeted panel | Lower `MIN_COUNTS` toward 10; check the `neg_frac` distribution |
| Clusters or transferred labels mix two lineages | Transcripts leaking between neighbouring cells | Step 2 double-positive check; report as segmentation, consider nucleus-only counts or re-segmentation |
| Few shared genes | Gene symbols differ (Ensembl IDs, case) | Map to symbols; `var["feature_name"]` holds symbols in Census data |
| Most cells < 0.5 confidence | Reference lacks the tissue's states | Pick a disease-matched reference; fall back to markers |
| `no cells match` in Step 4 | Dataset newer than Census | Download its h5ad (Step 4 alternative) or pick the next candidate |
| Almost no cells from an atlas `DATASET_ID` | `is_primary_data == True` added; atlases mark their cells False | Drop that filter for a single dataset |
| `SOMAError: std::bad_alloc` / `MemoryError` fetching the reference | Kernel near its memory limit with 1 GiB read buffers, all genes fetched, or a whole h5ad loaded | Run Step 4 as written (child process, 128 MiB buffers, panel genes); open h5ad files with `backed="r"`. Do not switch to a smaller dataset |
| `Unable to allocate ... MiB` in the notebook | Kernel memory filled by earlier steps | `del` objects no longer needed and `gc.collect()`; run memory-heavy steps as a script in a child process |
| CellTypist downloads all 61 models | `Model.load` with no local models | `celltypist.models.download_models(model=["Human_Lung_Atlas.pkl"])` first |
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
