---
name: scarf-single-cell
description: Analyze single-cell data with core Scarf, the out-of-core Zarr DataStore library with immutable artifacts and pipeline runs. Covers opening, converting and mounting stores (including Cytebase datasets), QC with removal audits, HVG/PCA/neighbour graphs, Leiden/Paris clustering, UMAP, markers and cautious annotation, batch correction and donor-level comparisons, headless plotting, provenance and export. Use when a task involves a Scarf .zarr store, a Cytebase dataset, scarf.DataStore, ds.pipeline, or converting H5AD/10x/MTX/Seurat data for Scarf. Does not cover scarf.agent (the automated agent package).
license: BSD-3-Clause
compatibility: Requires Python 3.12+ and scarf 1.0.0rc17 or newer (pip install "scarf[extra]>=1.0.0rc17"; add the cytebase extra and network access for Cytebase datasets).
metadata:
  version: "0.4"
---

# Scarf Single-Cell Analysis

## Overview

Scarf streams Zarr-backed count matrices in bounded blocks and records every computation as an
immutable, content-addressed artifact. This skill encodes how to drive core Scarf for single-cell
RNA analysis: which calls to make, in what order, what evidence to check, and what not to do. It
does not use or describe `scarf.agent`. Read **Key Concepts** (mental model and golden rules)
before running anything, then open only the `references/` modules you need. Paths are relative to
this skill's directory. The maintained copy lives in the Scarf repository at
<https://github.com/NygenAnalytics/scarf/tree/master/skills/scarf-single-cell>. Every recipe in the
modules was run against a real store; numbers quoted there come from the 10x 5K PBMC documentation
dataset and are illustrations, not thresholds.

## When to Use

- Analysing a Scarf `.zarr` store, or a count matrix too large to hold in memory, with QC,
  HVGs, PCA, a neighbour graph, Leiden/Paris clustering, UMAP and markers
- Converting 10x (HDF5 or directory), Matrix Market, H5AD or Seurat RDS input into a Zarr store
- Finding, exploring or mounting a Cytebase dataset (counts stay remote, results are written locally)
- Auditing which cells a QC filter removes, per sample and per marker-defined population
- Comparing conditions at the donor level (composition, pseudobulk) with the design checked first
- Keeping a provenance trail: durable pipeline runs, artifact lineage and a handoff record
- Use **scanpy-scrna-seq** instead for an in-memory AnnData workflow in the scverse toolchain;
  `ds.to_anndata(run=run)` hands a Scarf run over to it
- Use **scvi-tools-single-cell** or **harmony-batch-correction** for model-based or standalone
  integration outside Scarf; **celltypist-cell-annotation** or **popv-cell-annotation** for
  reference-based labels on an exported AnnData

## Prerequisites

- **Python packages**: `scarf[extra]>=1.0.0rc17` (Python 3.12+); `scarf[cytebase]` for Cytebase
- **Data requirements**: a Scarf `.zarr` store, or 10x / Matrix Market / H5AD / Seurat RDS input to
  convert. Raw UMI counts for QC bounds and count models
- **Environment**: set resources per process before importing Scarf; the defaults claim all
  detected RAM and every CPU. Memory specs need a unit (a bare `8` is rejected)
- **Headless**: `MPLBACKEND=Agg`, call plots with `show=False`, then `result.save(path)` and
  `result.close()`. Quiet logs for scripts: `scarf.configure_output(level="WARNING", progress=False)`
- **Long steps** (a pipeline run on tens of thousands of cells over remote counts can take many
  minutes): write the step as a script that logs to a file and ends with a `DONE` or `FAILED` line,
  run it in the background, and wait with a bounded loop that also stops on a `Traceback` or a dead
  process. Behind a wrapper such as `uv run`, put `timeout` inside it
  (`uv run timeout N python step.py`; the reverse can leave stale `running` records) and track the
  process by `$!`, not `pgrep -f`. Never poll without a time limit
  (`references/performance-and-export.md`)

Check first and skip the install when the printed version is 1.0.0rc17 or newer (inside a pixi
project, prefix commands with `pixi run`). The explicit pre-release floor matters: a bare
`scarf[extra]` resolves to the old 0.32 series, whose API this skill does not describe.

```bash
python -c "import importlib.metadata as m; print(m.version('scarf'))"
pip install "scarf[extra]>=1.0.0rc17"          # add scarf[cytebase] for Cytebase datasets
export SCARF_MEM_BUDGET=8G SCARF_WORKERS=8 MPLBACKEND=Agg
```

## Pre-flight Interview

Settle these with the user before writing any analysis code.

```yaml
decisions:
  - id: D1
    param: count_matrix_check
    kind: required
    source: data
    ask: "Do the counts look like raw UMIs, or were they corrected (for example SCTransform) or already filtered before import?"
    default: "propose from scripts/inspect_store.py; treat as raw UMIs only when no hint fires"

  - id: D2
    param: snapshot_columns
    kind: required
    source: data
    ask: "Which columns identify the donor, the sample or capture, the batch and the condition, so the unit of inference and any confounding are explicit?"
    default: null

  - id: D3
    param: held_out_columns
    kind: required
    source: data
    ask: "Which author annotation columns should stay hidden until a final, separate comparison?"
    default: "every annotation-like column flagged by scripts/inspect_store.py"

  - id: D4
    param: filtering
    kind: required
    source: data
    depends_on: [D1]
    ask: "Which QC policy removes debris without removing real low-complexity (platelets, erythrocytes, neutrophils) or high-RNA (plasma, cycling) populations?"
    default: "pooled 3-MAD (pipeline default) as one candidate; choose after the removal audit; gentle or flag-only on corrected or pre-filtered counts"

  - id: D5
    param: params.hvg.blacklist
    kind: required
    source: data
    ask: "Which species are the genes from, and should Ig V/J (clonotype) or haemoglobin genes be kept out of the variable genes?"
    default: "human or mouse string from references/gene-blacklists.md, no add-ons"

  - id: D6
    param: hvg_count, pca_dims, neighbors_k
    kind: optional
    source: user
    ask: "Should the cell graph use the standard representation, or is a broader or finer one under test?"
    default: "1000, 21, 11"

  - id: D7
    param: leiden
    kind: optional
    source: user
    ask: "How finely should cells be split: broad lineages, or states within them?"
    default: "partitions 0.5, 0.75, 1.0, 1.25; the silhouette pick is a baseline, the final choice rests on seed stability, nesting and markers"

  - id: D8
    param: harmony_batch_columns
    kind: optional_conditional
    source: data
    depends_on: [D2]
    ask: "Is there a technical batch to correct, and is it free of confounding with the condition being compared?"
    default: null
    skip_if: "all cells come from one batch"

  - id: D9
    param: markerPanel
    kind: required
    source: literature
    ask: "Which canonical markers, positive and negative, define the populations expected in this tissue and species?"
    default: null

  - id: D10
    param: sample_by
    kind: required
    source: user
    depends_on: [D2]
    ask: "For condition claims, what is the independent replicate (usually the donor), and how are donors sampled in two arms handled?"
    default: "donor_id; donors in two arms leave the between-group test"
    skip_if: "no condition comparison is requested"

  - id: D11
    param: SCARF_MEM_BUDGET, SCARF_WORKERS
    kind: never_ask
    source: user
    reason: "Bounds memory and CPU use only; results do not change"
    default: "set per process from the host, for example 8G and 8"

  - id: D12
    param: random_seed
    kind: never_ask
    source: data
    reason: "Leiden is seeded (4444) for reproducibility; stability is checked across seeds in Step 5"
    default: 4444
```

D4 hangs on D1 because QC bounds assume raw UMIs from unfiltered cell calls; on corrected or
pre-filtered counts the candidate policies change. D8 and D10 hang on D2: the batch and replicate
options are the design columns found there. Naming a batch adds Harmony to the run only when the
donors x batch x condition audit (Step 2) shows no confounding.

## Quick Start

A complete first pass on an RNA store. Every step after the run reuses the run's artifacts.

```python
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless; select the backend before importing scarf
import numpy as np
import pandas as pd
import scarf

scarf.configure_output(level="WARNING", progress=False)
store = "analysis.zarr"
out = Path("analysis_out")
(out / "figures").mkdir(parents=True, exist_ok=True)

ds = scarf.DataStore(store, min_features_per_cell=-1)

# QC: compare candidate filters and audit them before choosing (quality-control.md).
cells = ds.snapshot_cell_selection("I")
mad5 = ds.auto_filter_cells(cell_selection=cells, n_mads=5)
kept = np.asarray(ds.load_artifact(mad5)["values"][:], dtype=bool)
print(f"MAD 5 keeps {kept.sum()} of {ds.cells.N} cells")

# Baseline run with the chosen policy; freeze design columns you will need later.
run = ds.pipeline.run(
    label="baseline_mad5",
    filtering={"method": "mad", "n_mads": 5},
    snapshot_columns=[c for c in ("donor_id", "sample_id") if c in ds.cells.columns],
)
print(run.status, list(run.keys()))
(out / "run_report.md").write_text(run.report(format="markdown"))

# Figures and tables.
umap = ds.plots.embedding(run=run, color_by="clusters", show=False)
umap.save(out / "figures" / "umap_clusters.png", dpi=150)
umap.close()
markers = ds.get_markers(marker=run["markers"])
markers.to_csv(out / "markers_top.csv", index=False)
print(markers.groupby("group_id", sort=False).head(5)
      .groupby("group_id", sort=False)["feature_name"].agg(", ".join))
sizes = pd.Series(run.cells.fetch("clusters")).value_counts().sort_index()
print(sizes.to_dict())
```

## Workflow

Work in this order. After each step, write the decision and its evidence to an analysis log
(see Expected Outputs).

| Step | Do | Evidence to record | Module |
|---|---|---|---|
| 1. Inspect | `scripts/inspect_store.py`, `ds.summary()`, existing runs; check raw versus corrected counts | cells, assays, mounted or local, count type, metadata roles | `data-access.md`, `quality-control.md` |
| 2. Design | identify donor, sample, capture, batch and condition columns; derive missing units | unit of inference, confounding, held-out columns | `integration-and-comparisons.md` |
| 3. QC | inspect distributions; compare policies; audit removals | chosen policy, cells kept per group, what was removed | `quality-control.md` |
| 4. Baseline | `ds.pipeline.run(label=..., filtering=<chosen>, snapshot_columns=<design>)` | run id, report, kept cells | `pipeline-runs-and-artifacts.md` |
| 5. Structure | resolutions, seed stability, nesting, marker support, QC and doublets per cluster; branch if needed (HVG count and blacklist, PCs, `k`, subclustering, Harmony only if the design allows) | chosen partition and why; which alternative changed what | `clustering-and-embedding.md`, `features-and-graphs.md`, `gene-blacklists.md` |
| 6. Annotate | marker tables, canonical panels, gene-set scores | label, markers, negatives, unresolved clusters | `markers-and-annotation.md` |
| 7. Compare | composition per donor, pseudobulk; only with replicates | what can and cannot be claimed | `integration-and-comparisons.md`, `performance-and-export.md` |
| 8. Report | figures, tables, handoff JSON, lineage, export | files written, open questions | `plotting.md`, `performance-and-export.md` |

### Step 1: Inspect read-only

`zarr_mode="r"` writes nothing. The script prints cell and feature counts, runs, artifact kinds,
whether counts look raw, and a profile of every metadata column with design-like, annotation-like
and author-derived columns flagged. Annotation values stay hidden unless you pass
`--show-annotation-values`.

```bash
python scripts/inspect_store.py analysis.zarr
```

```python
import scarf

scarf.configure_output(level="WARNING", progress=False)
ds = scarf.DataStore("analysis.zarr", zarr_mode="r")   # read-only: writes nothing
print(ds)                                              # active (total) cells, assays, columns
snap = ds.summary().to_dict()                          # metadata only, JSON-safe
print(snap["default_assay"], snap["total_cells"], snap["active_cells"])
print(snap["pipeline_run_counts"], snap["labeled_pipeline_runs"])
print(ds.pipeline.list_runs())                         # existing work to reuse, newest first
```

### Step 2: Identify the design and held-out columns

Find the unit of inference before any filter. A donor in two arms, or a batch whose donors sit in
one condition only, changes what can be claimed later. Column names below are placeholders.

```python
import re

import pandas as pd

design_like = re.compile(r"donor|individual|patient|subject|sample|library|batch|"
                         r"condition|disease|treatment|time|day|sex", re.I)
design_cols = [c for c in ds.cells.columns if design_like.search(c)]
held_out = [c for c in ds.cells.columns
            if re.search(r"cell_?type|cell\.type|annotation|singler|predicted", c, re.I)]
print("design-like:", design_cols, "| hold out until the end:", held_out)
meta = ds.cells.to_pandas_dataframe(design_cols, key="I") if design_cols else pd.DataFrame()
print(meta.isna().sum())                        # resolve missing labels before any insert
if {"donor_id", "condition"} <= set(meta.columns):
    arms = meta.groupby("donor_id")["condition"].nunique()
    print("donors in two arms:", arms.index[arms > 1].tolist())
    print(meta.drop_duplicates(["donor_id", "condition"])["condition"].value_counts())
if {"donor_id", "batch", "condition"} <= set(meta.columns):
    units = meta.drop_duplicates(["donor_id", "batch", "condition"])
    print(pd.crosstab(units["batch"], units["condition"]))   # donors per batch x condition
```

### Step 3: Compare QC policies and audit removals

Filters never edit `I`; each returns a frozen `cell_selection` ref. Build several candidates, then
check what each removes on an unfiltered scaffold clustering, without author labels. A scaffold
cluster losing more than about a third of its cells is biology being removed.

```python
import numpy as np

ds = scarf.DataStore("analysis.zarr", min_features_per_cell=-1)   # writable; I left as is
cells = ds.snapshot_cell_selection("I")


def mask(ref):
    return np.asarray(ds.load_artifact(ref)["values"][:], dtype=bool)


candidates = {
    "mad3": ds.auto_filter_cells(cell_selection=cells),           # pipeline default
    "mad5": ds.auto_filter_cells(cell_selection=cells, n_mads=5),
    "manual": ds.filter_cells(["RNA_nFeatures", "RNA_percentMito"], lows=[200, None],
                              highs=[None, 20], cell_selection=cells),
}
bounds = ds.inspect_artifact(candidates["mad3"]).parameters["resolved_bounds"]["all"]
print(pd.DataFrame(bounds).T[["low", "high", "skip_reason"]])     # raw scale; never expm1
print({name: int(mask(ref).sum()) for name, ref in candidates.items()}, "of", ds.cells.N)

scaffold = ds.pipeline.run(label="qc_scaffold", filtering=False, cell_cycle=False, paris=False)
in_scaffold = mask(scaffold["analysis_cell_selection"])
scaffold_clusters = np.asarray(scaffold.cells.fetch("clusters"))
kept = pd.DataFrame({name: mask(ref)[in_scaffold] for name, ref in candidates.items()})
print(kept.groupby(scaffold_clusters).mean().round(2)
      .assign(n=kept.groupby(scaffold_clusters).size()))           # retention per cluster
```

### Step 4: Run the baseline pipeline

One `ds.pipeline.run` covers filtering, cell cycle, HVGs, normalization, PCA, graph, UMAP, Leiden
at 0.5/0.75/1.0/1.25 with a silhouette pick, Paris, doublet scores and markers. Pass an explicit
HVG blacklist (golden rule 15; strings from `references/gene-blacklists.md`) and choose
`snapshot_columns` now, because changing them later recomputes everything downstream.

```python
from pathlib import Path

MITO = r"^MT-"
RIBO = r"^RP[SL]\d+[AXY]?\d*$|^RPLP[0-2]$|^RPSA$|^MRP[SL]\d+[A-C]?$"
HISTONE = (r"^HIST[1-4]H|^H1-[1-6]$|^H1F[1-6]$|^H2AC\d+$|^H2BC\d+$|^H3C\d+$|^H4C\d+$"
           r"|^H2AW$|^H3-4$|^H4-16$")
HUMAN_BLACKLIST = "|".join([MITO, RIBO, r"^HLA-", HISTONE,
    r"^XIST$|^DDX3Y$|^USP9Y$|^EIF1AY$|^KDM5D$|^SRY$|^ZFY$|^UTY$|^TMSB4Y$|^NLGN4Y$"])

run = ds.pipeline.run(
    label="baseline",                                   # labels are immutable: new one per variant
    filtering={"method": "mad", "n_mads": 5},           # the policy chosen in Step 3
    params={"hvg": {"blacklist": HUMAN_BLACKLIST}},
    snapshot_columns=[c for c in ("donor_id", "sample_id", "condition") if c in ds.cells.columns],
)
print(run.status, run.run_id, run.label)
print(list(run.keys()))
print("analysed", int(run.cells.fetch_all("I").sum()), "of", ds.cells.N, "cells")
out = Path("analysis_out")
(out / "figures").mkdir(parents=True, exist_ok=True)
(out / "run_report.md").write_text(run.report(format="markdown"))
```

### Step 5: Choose a partition with evidence

`run["clusters"]` is the silhouette pick, a reproducible baseline only. Check seed stability and
marker support per resolution, and QC and doublet covariates per cluster. Cluster payloads follow
the run's cell selection, not `ds.cells.N`.

```python
from itertools import combinations

from sklearn.metrics import adjusted_rand_score

graph = run["connectivity_map"]


def labels_of(ref):
    key = "labels" if ref.kind == "cluster_cut" else "values"   # Paris stores labels
    return np.asarray(ds.load_artifact(ref)[key][:])


rows = []
for resolution in (0.5, 1.0, 1.5):
    refs = [ds.run_leiden_clustering(graph, resolution=resolution, random_seed=seed)
            for seed in (4444, 1, 2)]
    seeds = [labels_of(ref) for ref in refs]
    found = ds.get_markers(marker=ds.run_marker_search(refs[0], features=run["feature_universe"]))
    n_markers = found["group_id"].value_counts().reindex(
        [str(g) for g in np.unique(seeds[0])], fill_value=0)
    rows.append({"resolution": resolution, "n_clusters": len(np.unique(seeds[0])),
                 "min_seed_ari": min(adjusted_rand_score(a, b) for a, b in combinations(seeds, 2)),
                 "clusters_lt3_markers": int((n_markers < 3).sum())})
print(pd.DataFrame(rows).round(3))
print("pipeline pick:", ds.load_artifact(run["cluster_selection"]).attrs["selectedKey"])

in_run = run.cells.fetch_all("I").astype(bool)
per_cell = pd.DataFrame({c: ds.cells.fetch_all(c)[in_run]
                         for c in ("RNA_nCounts", "RNA_nFeatures", "RNA_percentMito")})
per_cell["doublet_score"] = run.cells.fetch("doublet_score")
print(per_cell.groupby(run.cells.fetch("clusters")).median().round(2))  # QC-only clusters are technical
```

### Step 6: Read markers and assign labels

`get_markers` defaults (`min_score=0.25, min_frac_exp=0.2`) hide genes; pass `-1` for both to see
full panels. Name a cluster only with two or more specific positive markers plus low
lineage-negative markers; keep `unresolved` otherwise. The panel and label map are templates.

```python
markers = ds.get_markers(marker=run["markers"])
print(markers.groupby("group_id", sort=False).head(5)
      .groupby("group_id", sort=False)["feature_name"].agg(", ".join))
everything = ds.get_markers(marker=run["markers"], min_score=-1, min_frac_exp=-1)

genes = set(ds.RNA.feats.fetch_all("names"))
panel = {"T": ["CD3D", "CD3E", "IL7R"], "B": ["MS4A1", "CD79A"], "NK": ["NKG7", "GNLY"],
         "myeloid": ["CD14", "LYZ", "FCGR3A"], "platelet": ["PPBP", "PF4"]}  # human blood; adapt
panel = {k: [g for g in v if g in genes] for k, v in panel.items()}
panel = {k: v for k, v in panel.items() if v}
if panel:
    dot = ds.plots.dotplot(features=panel, groups=run["clusters"], standardize="feature", show=False)
    dot.save(out / "figures" / "dotplot_panel.png", dpi=150)
    dot.close()

labels = {  # TEMPLATE: fill from this dataset's markers; never copy a map from another dataset
    # "<id>": "CD14 monocyte",  # + CD14, LYZ, FCN1 | - CD3E, MS4A1 | confidence high
}
per_cluster = pd.Series(run.cells.fetch("clusters").astype(str))
annotation = np.full(ds.cells.N, "not analyzed", dtype=object)
annotation[in_run] = per_cluster.map(labels).fillna("unresolved").to_numpy()
ds.cells.insert("annotation_v1", annotation, overwrite=True)   # live column, full cell axis
print(pd.Series(annotation[in_run]).value_counts())
```

### Step 7: Compare conditions at the donor level

Cells are not replicates. Condition claims need at least two independent donors per group;
`sample_by="donor_id"` refuses a donor in two arms, while `sample_by="sample_id"` silently counts
it in both. Clusters stand in for your own labels here.

```python
from scarf.plotting import CellField

if {"donor_id", "condition"} <= set(run.cells.columns):
    frame = run.cells.to_pandas_dataframe(["donor_id", "condition", "clusters"])
    print(pd.crosstab(frame["donor_id"], frame["clusters"], normalize="index").round(3))
    donors_per_arm = frame.drop_duplicates(["donor_id", "condition"])["condition"].value_counts()
    print(donors_per_arm)
    if len(donors_per_arm) == 2 and (donors_per_arm >= 2).all():
        clusters_all = run.cells.fetch_all("clusters")          # -1 outside the run
        keys = []
        for c in np.unique(clusters_all[in_run]):
            keys.append(f"is_cluster_{c}")
            ds.cells.insert(keys[-1], (clusters_all == c).astype(np.float64), overwrite=True)
        ds.cells.insert("in_composition", in_run, overwrite=True)
        result = ds.run_statistical_testing(
            keys, CellField("condition"), cell_selection=ds.snapshot_cell_selection("in_composition"),
            groups=sorted(donors_per_arm.index), test="mann_whitney", sample_by="donor_id",
        )
        print(result.p_value_method)
        print(pd.concat([result.tables[k].assign(key=k) for k in keys]))
```

### Step 8: Report, record and export

Save figures and tables, the run report, lineage and a handoff record with the refs you relied
on, then export the run for downstream tools. Refs round-trip with `ref.to_dict()` and
`scarf.ArtifactRef.from_dict`.

```python
import json

umap = ds.plots.embedding(run=run, color_by="clusters", show=False)
umap.save(out / "figures" / "umap_clusters.png", dpi=150)
umap.close()
markers.to_csv(out / "markers_top.csv", index=False)
pd.Series(run.cells.fetch("clusters")).value_counts().sort_index().to_csv(out / "cluster_sizes.csv")
lineage = ds.lineage({"clusters": run["clusters"], "markers": run["markers"]})
(out / "lineage.md").write_text(lineage.to_markdown())
keys = ("analysis_cell_selection", "highly_variable_features", "connectivity_map", "clusters")
handoff = {"pipelineRun": {"runId": run.run_id, "label": run.label, "status": run.status},
           "refs": {k: run[k].to_dict() for k in keys},
           "unsupportedClaims": [], "openQuestions": []}
(out / "handoff.json").write_text(json.dumps(handoff, indent=2))
assert scarf.ArtifactRef.from_dict(handoff["refs"]["clusters"]) == run["clusters"]
adata = ds.to_anndata(run=run)        # obs: frozen fields; obsm: X_umap; X: raw counts in memory
adata.write_h5ad(out / "baseline_run.h5ad")
print(adata)
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `zarr_mode` (`DataStore`) | `"r+"` | `"r"`, `"r+"` | `"r"` writes nothing; producers then return existing artifacts or raise `PermissionError` |
| `min_features_per_cell` (`DataStore`) | `10` | `-1` or a feature count | A writable open drops cells at or below it from `I` permanently; `-1` leaves `I` untouched |
| `filtering` (`pipeline.run`) | `True` (pooled 3-MAD on the four `RNA_*` QC columns) | `False`; `{"method": "mad", "n_mads": 5, "sample_column": ...}`; `{"method": "manual", ...}` | Defines `analysis_cell_selection`; audit before accepting |
| `params["hvg"]["blacklist"]` | built-in regex | species string from `gene-blacklists.md` (+ add-ons) | Replaces the default entirely; new HVG, PCA and graph artifacts |
| `hvg_count` / `pca_dims` / `neighbors_k` | `1000` / `21` / `11` | e.g. `2000` / `30` / `21` for a branch; `pca_dims=0` skips PCA | Representation behind the graph and every partition |
| `leiden` | `[0.5, 0.75, 1.0, 1.25]`, silhouette pick | `{"partitions": [...]}`; `params["leiden"]["selected"]` pins one | Cluster granularity; the pick is a baseline only |
| `snapshot_columns` | `()` | design columns, your own label columns | Frozen into `run.cells` and exports; changing them recomputes downstream |
| `harmony_batch_columns` | `None` | real batch columns | Adds Harmony after PCA; runs silently even when confounded |
| `get_markers(min_score, min_frac_exp)` | `0.25`, `0.2` | `-1`, `-1` for every gene and group | Hides negatives and weak markers by default |
| `run_statistical_testing(sample_by=)` | none | `"donor_id"` | Unit of replication for condition tests |
| `SCARF_MEM_BUDGET` / `SCARF_WORKERS` | all detected RAM / every CPU | e.g. `8G` / `8` | Per-process memory and CPU bound; set before import |

## Key Concepts

### Mental model

- A **DataStore** is one Zarr directory: a shared cell table `ds.cells`, one group per assay
  (`ds.RNA`, feature table `ds.RNA.feats`, counts as cell-major `counts` plus gene-major `countsT`),
  artifacts, and `pipeline/runs`. QC columns are assay-prefixed: `RNA_nCounts`, `RNA_nFeatures`,
  `RNA_percentMito`, `RNA_percentRibo`.
- **`I`** is the live boolean cell key. Analytical filters never edit it; they return a frozen
  **cell selection** artifact.
- Every result is an **`ArtifactRef`** (`scope`, `kind`, `artifact_id`, `assay`). Producers take refs
  and return refs: `select_hvgs -> run_normalization -> run_pca -> build_ann_index ->
  query_neighbors -> build_connectivity_map -> run_leiden_clustering / run_umap ->
  run_marker_search`. An identical call returns the existing artifact without recomputing.
- **`ds.pipeline.run(label=...)`** runs that whole RNA recipe (filtering, cell cycle, HVG,
  normalization, PCA, graph, UMAP, Leiden at 0.5/0.75/1.0/1.25 with a silhouette pick, Paris,
  doublet scores, markers) and returns a durable **`PipelineRun`**: a mapping of output names to
  refs plus frozen `run.cells` / `run.features` views and `run.report()`.
- Artifact payload rows follow the artifact's **cell selection**, not `ds.cells.N`.
- A **mount** is a local writable store whose counts stay in a remote source (`matrixSource`).
  Every pass over counts is a network read; artifacts are written locally.

### Golden rules

1. **Inspect read-only first.** `scarf.DataStore(path, zarr_mode="r")` writes nothing. A writable
   open (the default) prepares new stores and applies `min_features_per_cell` (default 10) to `I`
   permanently. Reopen existing stores and mounts with
   `scarf.DataStore(path, min_features_per_cell=-1)`.
2. **Never filter by editing `I`.** Keep the `cell_selection` ref a filter returns and pass it on, or
   insert a boolean column and use `cell_key=`. `ds.cells.reset_key("I")` undoes an accidental
   open-time filter.
3. **Keep every ref you will reuse in a dict** and record them. Never guess artifact IDs or read
   private Zarr paths. Use `ds.inspect_artifact(ref)`, `ds.load_artifact(ref)` and
   `ds.list_artifacts(...)`. Cell selections need `scope="datastore"` when listing.
4. **Check the matrix, then audit QC removals before accepting a filter.** Published matrices can
   be corrected (for example SCTransform) or already filtered, which makes QC bounds meaningless;
   `scripts/inspect_store.py` reports this. Pooled MAD filters routinely remove low-complexity
   populations (platelets, erythrocytes, neutrophils) and high-RNA ones (plasma, cycling cells).
   Audit retention per sample and per marker-defined group without author labels, and look at the
   markers of removed cells (`references/quality-control.md`).
5. **Labels are immutable and runs cannot be resumed.** Use a new `label` for every variant. A rerun
   reuses every complete artifact, so it is cheap. Choose `snapshot_columns` (design columns you
   want inside `run.cells` and exports) on the first run, because changing them recomputes
   everything downstream.
6. **Read pipeline outputs instead of recomputing them.** `run["markers"]`, `run["cell_cycle"]` and
   `run["doublets"]` already exist. A direct `run_marker_search(run["clusters"], ...)` creates a new
   artifact and rereads all counts.
7. **Align arrays through the cell selection.** Use `run.cells.fetch(...)` (run cells only) or
   `fetch_all(...)` (full length, with -1, NaN or "" outside the run). For explicit artifacts use
   `ds.inspect_artifact(ref).input_ref("cell_selection")`. Join tables on cell `ids`, never on row
   order.
8. **Budget count passes on mounts.** QC metrics, the HVG summary, normalization per selection,
   markers, gene plots and AUCell each read counts. For many passes, make a local copy once:
   `python -m scarf.tools.repack_zarr MOUNT.zarr LOCAL.zarr --mem-budget 4G`.
9. **One DataStore per process; it is not thread-safe.** Run parallel analyses in separate
   processes on separate stores, each with its own `SCARF_MEM_BUDGET`/`SCARF_WORKERS`.
10. **Payload names differ by kind.** Leiden labels, embeddings, doublet and strength scores live
    under `values`; Paris (`cluster_cut`) under `labels`; PCA under `data`. `get_markers` returns
    string `group_id` while Leiden labels are integers.
11. **`get_markers` defaults hide genes.** `min_score=0.25, min_frac_exp=0.2`; pass `-1` for both
    to see negatives and full panels.
12. **Labels are hypotheses.** Name a cluster only with two or more specific positive markers plus
    low lineage-negative markers and a plausible QC and doublet profile. Keep `unresolved` for
    mixed, doublet-like or marker-poor clusters.
13. **Cells are not replicates, and Scarf does not check your design.** Condition claims need
    donor-level aggregation and at least two independent donors per group. A donor sampled twice is
    repeated measures. A donor with samples in two arms must not count in both:
    `run_statistical_testing(sample_by="sample_id")` silently does that, while `sample_by="donor_id"`
    refuses such a design. `run_harmony` runs silently on a column confounded with the biology you
    want to compare, so audit donors x batch x condition first. When inserting design columns, replace
    missing values explicitly: `ds.cells.insert` stores `None` as `""` and `pd.NA` as `"<NA>"`.
14. **Hold out annotation columns when they will judge the result.** Do not use author labels
    (`cell_type`, `author_cell_type`, `cell.type.*`, `singler`, `predicted.*`, ...) to choose QC,
    parameters or labels. Use them only in a final, clearly separated comparison.
15. **Pass an explicit HVG blacklist.** On stores with current gene symbols the default blacklist
    misses replication-dependent histones (`^HIST` matches only pre-2020 names), and its `^CCN`
    family removes the CCN1-6 matricellular genes and non-cell-cycle cyclins. It also leaves Ig V/J
    genes in, which can split plasma cells by light chain instead of biology. Use the species string
    from `references/gene-blacklists.md` (`params={"hvg": {"blacklist": ...}}` in the pipeline). Add
    the clonotype add-on only on marker evidence. A `blacklist=` string replaces the default
    entirely, and changing it creates new HVG, PCA and graph artifacts.

## Common Recipes

### Recipe: Convert H5AD or 10x input into a store

When to use: the data arrive as a file, not a Scarf store. Every writer follows reader, then
`*ToZarr(...).dump()`; open each new store writable once. Seurat RDS, Matrix Market and Cytebase
are in `references/data-access.md`.

```python
insp = scarf.inspect_h5ad("data.h5ad")
print(insp.matrixKey, insp.integerLike, insp.layers, insp.suggestedAssays)
reader = scarf.H5adReader.from_inspect(insp)  # embedding_roles={"X_umap": "umap"} imports obsm
scarf.H5adToZarr(reader, zarr_loc="h5ad.zarr").dump()
new = scarf.DataStore("h5ad.zarr", min_features_per_cell=-1)   # first writable open prepares it
print(new)
# 10x HDF5 (assays inferred from feature types):
# scarf.CrToZarr(scarf.CrH5Reader("filtered_feature_bc_matrix.h5"), zarr_loc="pbmc.zarr",
#                mem_budget="4G").dump()
```

### Recipe: Branch from a completed run

When to use: a finer partition or another representation is under test. Passing the run's exact
refs reuses its artifacts; new parameters create a branch. Explicit HVG, PCA and graph chains are
in `references/features-and-graphs.md`.

```python
assert ds.run_leiden_clustering(graph, resolution=0.5) == run["leiden_0.5"]   # reused
fine = ds.run_leiden_clustering(graph, resolution=2.0)                          # new artifact
fine_markers = ds.run_marker_search(fine, features=run["feature_universe"])
print(len(np.unique(labels_of(fine))), "clusters at resolution 2.0")
plot = ds.plots.embedding(layout=run["umap"], color_by=fine, show=False)
plot.save(out / "figures" / "umap_leiden_2.0.png", dpi=150)
plot.close()
print(ds.lineage({"selected": run["clusters"], "fine": fine}).to_markdown()[:400])
```

### Recipe: Evaluate against held-out labels

When to use: the dataset ships author annotations. Run the whole loop without them, freeze your
labels, then compare once in a clearly separated final section. Write the vocabulary map before
any crosstab; never tune parameters or labels on the result, and record any later change as such.

```python
from sklearn.metrics import adjusted_rand_score

reference = pd.Series(ds.cells.fetch_all("author_cell_type")[in_run]).astype(str)  # held out
print(sorted(reference.unique()))           # vocabulary only; now write the map below
to_reference = {  # TEMPLATE: our label -> reference label, fixed before seeing any agreement
    # "CD4 T": "<reference label>",
}
ours = pd.Series(ds.cells.fetch_all("annotation_v1")[in_run]).astype(str)
pred = ours.map(to_reference).fillna("unmatched")
print(pd.crosstab(pred, reference))
print("ARI vs clusters", round(adjusted_rand_score(reference, run.cells.fetch("clusters")), 3))
print("ARI vs labels", round(adjusted_rand_score(reference, pred), 3))
```

Report per-type precision and recall, QC retention per author type (an audit of the filter), and
explain disagreements with marker evidence (`references/markers-and-annotation.md`).

## Expected Outputs

Keep these in the output directory so another agent or a person can audit and continue:

- `analysis_log.md` — the question, the units, and one entry per step (decision, alternatives
  considered, evidence with numbers, figure paths)
- `handoff.json` — run label and ID, and the refs you relied on (`ref.to_dict()`; restore with
  `scarf.ArtifactRef.from_dict`), plus unsupported claims and open questions
  (`references/pipeline-runs-and-artifacts.md`)
- `run_report.md` (`run.report(format="markdown")`) and `lineage.md`
  (`ds.lineage({...}).to_markdown()`)
- Figures as PNG (`figures/umap_clusters.png`, `figures/dotplot_panel.png`) and tables as CSV
  (markers, cluster sizes, composition, label map)
- `baseline_run.h5ad` — the run's analysed cells with raw counts, frozen fields and `X_umap`
- Inside the store: immutable artifacts and the `PipelineRun` record, reopened with
  `ds.pipeline.open(label="baseline")`

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Assay 'RNA' is not prepared` on a read-only open | store just written by a converter or `SubsetZarr` | open once writable, then read-only |
| Fewer active cells than expected after opening | writable open applied `min_features_per_cell` | `ds.cells.reset_key("I")`; reopen with `-1` |
| `ValueError` on `ds.pipeline.run(label=...)` | label already completed | new label; reuse makes it cheap |
| `PermissionError` from a producer | store opened with `zarr_mode="r"` and no matching artifact | reopen writable |
| `KeyError: 'values'` on a Paris ref | Paris stores `labels` | `ds.load_artifact(ref)["labels"]` |
| Array length differs from `ds.cells.N` | payload follows the cell selection | align with `run.cells.fetch_all` or the selection mask |
| Plot raises with `run=` and a gene or live column | run mode accepts one frozen field only | `layout=run["umap"], color_by=[...]` |
| `TypeError` from `distribution(grouping="col")` | grouping needs a ref or `CellField` | `grouping=scarf.plotting.CellField("col")` |
| Very slow steps on a mount | each count pass is a network read | fewer passes; repack locally (golden rule 8) |
| `MemoryError` (`CountLayoutMemoryError` after 1.0.0rc19) from a converter | default count layout does not fit `mem_budget` | larger `mem_budget`; else the `policy=` the message names (`references/data-access.md`) |
| `ValueError` plotting after reopening the store | a `PipelineRun` is bound to the store object that opened it | reopen the run from the new `ds` |
| `list_artifacts(kind="cell_selection")` is empty | cell selections are datastore-scoped | add `scope="datastore"` |
| `KeyError: 'groups'` in a dot plot table | with `group_by=` the column is named after the grouping column | read `res.tables["aggregate"].columns` first |
| A wait for a long step never ends | unbounded polling, or the process died | bounded wait that checks the process and the log tail (Prerequisites) |
| QC bounds look odd or nothing is filtered | counts are corrected or already filtered | check the matrix first; prefer flag-only or gentle filters |
| `ValueError: None of the s_genes match the assay feature names` from `ds.pipeline.run` | feature names are not gene symbols (Ensembl IDs, synthetic names); matching ignores case, so mouse symbols work | `cell_cycle=False`, or pass lists in the store's naming via `params={"cell_cycle": {"s_genes": [...], "g2m_genes": [...]}}` |

## Bundled Resources

Read `SKILL.md` first, then open only the module the current step needs.

| File | Read when |
|---|---|
| `references/data-access.md` | opening, inspecting, converting (H5AD, 10x, MTX, Seurat), Cytebase search, open and mount |
| `references/quality-control.md` | QC metrics, MAD/manual/per-sample filters, removal audits, doublet scores |
| `references/features-and-graphs.md` | HVGs, normalization, PCA dims, ANN, neighbours, graph diagnostics, branching, subclustering |
| `references/gene-blacklists.md` | what the default HVG blacklist removes, corrected blacklists for human and mouse, Ig/TCR and haemoglobin add-ons |
| `references/clustering-and-embedding.md` | Leiden and Paris, choosing a partition, UMAP and t-SNE, labels as arrays |
| `references/markers-and-annotation.md` | marker tables, canonical marker panels, labelling, AUCell/WAGGR, cell cycle, label comparison |
| `references/pipeline-runs-and-artifacts.md` | `ds.pipeline.run` options, run reports, artifacts, lineage, failures, handoff record |
| `references/plotting.md` | headless figures, run mode versus ref mode, every `ds.plots` method |
| `references/integration-and-comparisons.md` | study design and units, donors in two arms, composition tests, Harmony and its safety, merging, mapping, condition comparisons |
| `references/performance-and-export.md` | budgets, long-running steps, streaming, mount repacking, AnnData/H5AD/MTX/CSV and pseudobulk export, subset stores |
| `scripts/inspect_store.py` | read-only first look: `python scripts/inspect_store.py STORE.zarr [--show-annotation-values]` |

## References

- [Scarf documentation](https://scarf.readthedocs.io/en/latest/) — `quickstart.html`, one tutorial
  page per step under `tutorials/` (for example `quality_control`, `graph_construction`,
  `clustering`, `annotation`, `batch_correction`, `pseudobulk_and_differential_expression`,
  `cytebase`), and exact signatures under `reference/api/<module>.html`
- [Provenance](https://scarf.readthedocs.io/en/latest/concepts/provenance.html) and
  [memory and execution](https://scarf.readthedocs.io/en/latest/concepts/memory_and_execution.html)
  — the artifact model and resource budgets
- [Benchmarks](https://scarf.readthedocs.io/en/latest/concepts/benchmarks.html) — end-to-end runs
  on S3-compatible storage at 0.1, 1 and 10 million cells, with their hardware
- [Analysis with agents](https://scarf.readthedocs.io/en/latest/analysis_with_agents.html) —
  scientific decision loop, task routing and handoff
- [NygenAnalytics/scarf on GitHub](https://github.com/NygenAnalytics/scarf) — source (BSD-3-Clause)
  and the maintained copy of this skill under `skills/scarf-single-cell`
- [scarf on PyPI](https://pypi.org/project/scarf/) — releases and extras
- [Dhapola et al. (2022)](https://doi.org/10.1038/s41467-022-32097-3) — "Scarf enables a highly
  memory-efficient analysis of large-scale single-cell genomics data", *Nat Commun* 13, 4616
