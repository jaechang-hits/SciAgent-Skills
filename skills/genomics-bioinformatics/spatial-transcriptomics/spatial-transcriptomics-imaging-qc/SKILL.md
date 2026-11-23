---
name: "spatial-transcriptomics-imaging-qc"
description: "Imaging-cell spatial transcriptomics QC for Xenium, CosMx and MERFISH segmented cells. Validate counts, cell IDs, centroids, controls, size and FOV fields; run SpaceTrooper spatialPerCellQC, robust computeSpatialOutlier and version-compatible QScore; optionally add D1-approved polygon geometry without gating QScore; restore matched R results to the full Python baseline, integrate evidence, visualize cutoffs, validate impact, and require D2 before filtering."
license: "CC-BY-4.0"
---

# Imaging-Cell Spatial Transcriptomics QC

## Overview

Assess segmented-cell imaging assays with SpaceTrooper while preserving the
complete cell denominator. Basic table/centroid QC and QScore eligibility are
independent of polygon approval. Polygon parsing, attachment, geometry metrics
and polygon maps require D1. No metric, package flag, 3-MAD fence or low QScore
alone is a final filtering decision.

Before planning, read all required resources:

- `/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-imaging-qc/references/spacetrooper-workflow.md`
- `/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-qc/references/integrated-assessment.md`
- `/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-imaging-qc/scripts/spacetrooper_helpers.R`

The Supervisor must pass this Skill and required reference content to
WorkflowPlanner. The Planner does not read Skills itself.

## When to Use

- QC Xenium segmented cells before annotation or downstream spatial analysis
- QC CosMx RNA or protein cell tables with global coordinates and FOV metadata
- QC MERFISH/MERSCOPE cells with counts, centroids and area/volume metadata
- Evaluate signal density, controls, cell size, aspect ratio or FOV-border effects
- Compute a dataset-specific QScore when installed APIs and metrics support it
- Add polygon validity and geometry QC after explicit D1 approval
- Use `spatial-transcriptomics-spot-qc` instead for Visium or Visium HD spots/bins
- Use `spatial-transcriptomics-qc` first when observation type is uncertain

## Prerequisites

SpaceTrooper is the required imaging engine, not an optional enhancement.
Install it before writing any QC code, just as a Python skill installs its
required package before importing it. This runtime uses R 4.5/Bioconductor
3.22; do not switch to a development Bioconductor release.

Run this bootstrap first. It installs only when the package is missing, then
loads the package and checks the functions required by this workflow:

```python
import subprocess

r_code = r'''
if (!requireNamespace("BiocManager", quietly=TRUE))
  install.packages("BiocManager", repos="https://cloud.r-project.org")
if (!requireNamespace("SpaceTrooper", quietly=TRUE))
  BiocManager::install("SpaceTrooper", version="3.22", ask=FALSE, update=FALSE)
suppressPackageStartupMessages({
  library(SpaceTrooper)
  library(SpatialExperiment)
  library(SummarizedExperiment)
  library(S4Vectors)
})
required <- c("readXeniumSPE", "readCosmxSPE", "readMerfishSPE",
              "spatialPerCellQC", "computeSpatialOutlier")
stopifnot(all(required %in% getNamespaceExports("SpaceTrooper")))
cat("SpaceTrooper", as.character(packageVersion("SpaceTrooper")), "import OK\n")
'''

result = subprocess.run(
    ["Rscript", "-e", r_code],
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.returncode != 0:
    raise RuntimeError(f"SpaceTrooper bootstrap failed:\n{result.stderr}")
```

Obtain the runtime's required slow-install approval before running the bootstrap
when installation is needed. If installation or import fails, preserve the
exact error. Only then may the workflow record `engine_unavailable` and offer
labeled common QC; never describe common QC as SpaceTrooper-equivalent.

Required core data:

- raw counts with unique cell IDs;
- finite cell centroids aligned one-to-one to cells;
- supported technology metadata and sample/FOV grouping;
- positive platform size field required by `spatialPerCellQC()`.

Controls, polygons and images are conditional capabilities, not prerequisites
for all basic QC.

## Pre-flight Interview

Inspect first and ask only applicable decisions.

```yaml
decisions:
  - id: D1
    param: polygonGeometryQC
    kind: optional_conditional
    source: data
    ask: "I found parseable non-empty cell polygons with overlapping IDs. Should I include polygon validity, matching loss, multipolygon, area/aspect-ratio and polygon-map checks?"
    default: "basic table/centroid QC only"
    skip_if: "no usable polygon/segmentation geometry capability"

  - id: D2
    param: applyFiltering
    kind: required
    source: user
    ask: "I have shown the final integrated rule, cutoff/flag plots, expected impact and biological-loss risk. Should I create a separately named filtered copy using this exact rule set?"
    default: null
    skip_if: "assessment/recommendation only, or no Exclude candidate observations"
```

D1 controls only polygon-derived work. It never authorizes filtering and never
blocks polygon-free SpaceTrooper metrics, robust outliers or an otherwise
executable QScore. D2 occurs only after impact validation. Persist both in
`qc_approval_state.tsv` with decision, exact scope, status, reason and timestamp;
reuse a decision only while that scope is unchanged.

## Workflow

### Step 1: Confirm Imaging Routing and Inventory Capabilities

Require compound segmented-cell evidence. Record matrix, cell IDs, centroids,
technology, sample/FOV, controls, size fields, images and polygon sources with
evidence and uncertainty.

```python
from pathlib import Path
import json

classification = json.loads(Path("qc_input_classification.json").read_text())
if classification["route"] != "imaging":
    raise ValueError("imaging QC requires confirmed segmented-cell routing")
print(classification["confidence"], classification["imaging_evidence"])
```

Initialize `qc_observation_accounting.tsv`; distinguish loader/join/polygon
losses from any later D2-approved filtering.

### Step 2: Build One Baseline Object and Probe Polygons Read-Only

Use the platform loader with polygon attachment disabled. Preserve raw counts,
cell IDs, centroids, controls and size fields. Keep one immutable baseline.

```r
suppressPackageStartupMessages({
  library(SpaceTrooper)
  library(SpatialExperiment)
  library(SummarizedExperiment)
  library(S4Vectors)
})
spe <- SpaceTrooper::readXeniumSPE(
  XENIUM_DIR, keepPolygons=FALSE, addFOVs=FALSE)
stopifnot("counts" %in% SummarizedExperiment::assayNames(spe),
          !anyDuplicated(colnames(spe)))
xy <- SpatialExperiment::spatialCoords(spe)
stopifnot(nrow(xy) == ncol(spe), all(is.finite(xy[, 1:2])))
spe_baseline <- spe
```

Adapt the official loader to CosMx or MERFISH as observed. Before D1, use the
official polygon reader only to verify parseability, required normalized
columns, non-empty geometry, unique polygon IDs and overlap. Do not attach,
derive geometry metrics, plot, or flag.

### Step 3: Define Shared Helpers Before Branching

Read the bundled helper, copy it unchanged into the analysis workspace, and
source that workspace copy after constructing `spe` and before choosing basic
or polygon branches. This placement prevents Polygon QC from skipping required
definitions.

```r
source("spacetrooper_helpers.R")
stopifnot(exists("record_engine_status"),
          exists("set_metadata_value"),
          exists("space_trooper_preflight"),
          exists("run_supported_qscore"),
          exists("export_spatial_qc"))
```

The helpers log engine status, validate the object contract, adapt to installed
QScore APIs and restore matched results to the complete baseline.

### Step 4: Execute Exactly One SpaceTrooper Metric Branch

If D1 is declined/not applicable, run basic `spatialPerCellQC()` on a copy with
`rmZeros=FALSE`. If D1 is approved, the integrated polygon branch replaces the
basic branch: attach polygons, account for matching loss, join geometry by ID,
then run `spatialPerCellQC(..., rmZeros=FALSE)` once.

```r
spe_qc <- spe_baseline
check <- space_trooper_preflight(spe_qc)
if (!check$ok) stop(paste(check$issues, collapse="; "))
n_before <- ncol(spe_qc)
spe_qc <- SpaceTrooper::spatialPerCellQC(spe_qc, rmZeros=FALSE)
stopifnot(ncol(spe_qc) == n_before)
spe_qc <- set_metadata_value(spe_qc, "space_trooper_executed", TRUE)
```

In the D1 branch, preserve `ids_before`, write matching status for every cell,
and never count unmatched cells as metric outliers. Read the execution reference
for the complete branch contract.

### Step 5: Compute Robust Outliers and QScore Independently of D1

Run `computeSpatialOutlier()` on supported observed metrics. Use medcouple for
skewed distributions and scuttle MAD for symmetric ones after inspecting the
distribution; package fences remain metric evidence.

```r
metrics <- intersect(c("log2SignalDensity", "Area_um", "log2AspectRatio",
  "log2Ctrl_total_ratio", "polygon_area"),
  colnames(SummarizedExperiment::colData(spe_qc)))
for (metric in metrics)
  spe_qc <- SpaceTrooper::computeSpatialOutlier(
    spe_qc, computeBy=metric, method="both", scuttleType="both")
```

Then call the same version-adaptive QScore helper after either branch. Its
eligibility depends on actual metrics and installed API, not D1.

```r
qscore_run <- run_supported_qscore(spe_qc, seed=1713L)
spe_qc <- qscore_run$spe
qscore_usable <- qscore_run$usable
qscore_col <- qscore_run$score_col
```

Record actual function, version, output column, seed, model formula, included
metrics and lambda when exposed. Do not invent missing predictors or transfer a
model between datasets.

### Step 6: Plot, Restore Full IDs and Integrate Evidence

Save SpaceTrooper histograms and centroid maps for major metrics and QScore.
Save polygon maps only in the D1-approved branch. A centroid/polygon map is
descriptive, not a local-neighbour test.

```r
dir.create("qc_package_plots", showWarnings=FALSE)
for (metric in intersect(c("sum", "detected", "log2SignalDensity", "Area_um",
    "log2AspectRatio", "log2Ctrl_total_ratio", qscore_col),
    colnames(SummarizedExperiment::colData(spe_qc)))) {
  p <- SpaceTrooper::plotMetricHist(spe_qc, metric=metric)
  ggplot2::ggsave(file.path("qc_package_plots", paste0(metric, "_distribution.png")),
                  p, width=6, height=4, dpi=200)
}
```

Export matched metrics onto the complete pre-polygon baseline and require exact
Python/R ID equality and ordering. Unmatched cells retain missing derived
metrics and explicit matching status.

Read the shared assessment reference. Treat QScore and its optional low-score
flag as one evidence domain. Call the installed QScore flag function only when
the review has recorded an explicit cutoff; never silently use `0.5`.

### Step 7: Visualize Recommendations, Validate Impact, Resolve D2 and Report

Plot all major metric distributions and spatial views. Draw a cutoff only when
the recommendation configuration contains that explicit numeric value.
Validate final impact overall and by sample/FOV on the complete baseline.

```python
import pandas as pd

class_order = ["Retain", "Review", "Exclude candidate"]
impact = adata.obs["qc_class"].value_counts().reindex(class_order, fill_value=0)
print(impact, (100 * impact / adata.n_obs).round(2))
if "polygon_unmatched" in adata.obs:
    unmatched = adata.obs["polygon_unmatched"].fillna(False).astype(bool)
    assert not adata.obs.loc[unmatched, "qc_class"].eq("Exclude candidate").any()
```

If no exclusions exist or the request is assessment-only, record D2 as
`not_applicable`. Otherwise show the exact final rule set, plots, expected
impact and biological-loss risk and ask D2 once. Preserve the original and
write only a separately named filtered copy after approval.

## Key Parameters

| Parameter | Default/reference | Decision rule |
|---|---|---|
| `rmZeros` | `FALSE` | invariant; package default may silently subset cells |
| `method` | compare `both` | choose medcouple vs MAD from observed distribution |
| `scuttleType` | `both` | metric-specific direction after inspection |
| QScore seed | `1713` | provenance/reproducibility; does not gate D1 |
| `modelFormula` | installed package default | never invent unavailable predictors |
| `keepMultiPol` | `TRUE` | preserve and flag multipolygons |
| `micronConvFact` | platform metadata | never assume when coordinates already use microns |
| D1 | conditional explicit approval | polygon-derived work only |

## Common Recipes

### Inspect Actual QScore Metadata

```r
print(S4Vectors::metadata(spe_qc)$qscore_execution)
score_column <- S4Vectors::metadata(spe_qc)$qscore_execution$score_column
print(summary(spe_qc[[score_column]]))
```

### Inspect SpaceTrooper Fences Without Filtering

```r
flag <- spe_qc$log2SignalDensity_outlier_sc
print(attr(flag, "thresholds"))
print(table(flag, useNA="ifany"))
```

## Expected Outputs

- `qc_input_classification.json`, `qc_capabilities.tsv`
- `qc_environment_status.tsv`, `qc_execution_log.tsv`
- `qc_observation_accounting.tsv`, `qc_observation_flags.tsv`
- actual `QScore`/`QC_score` values and execution metadata when supported
- `qc_polygon_matching_status.csv` only after approved polygon work
- SpaceTrooper distributions, centroid maps and conditional polygon maps
- recommendation, candidate, impact and validation tables
- `qc_filtering_recommendation.html`, `spatial_qc_report.html`
- optional filtered copy only after D2

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `Rscript` or SpaceTrooper unavailable | runtime/package/dependency missing | request the slow install when required, install and verify the approved 1.0.1 build; use labeled common QC only after an actual install/import attempt fails |
| `spatialPerCellQC()` loses cells | `rmZeros=TRUE` used | restart from baseline with `rmZeros=FALSE` |
| QScore unavailable | required metrics/API/model fit absent | log actual reason; do not tie the skip to D1 |
| Polygon object has fewer cells | unmatched/invalid polygon IDs | account before/after IDs; restore full baseline on export |
| Polygon plot cannot find geometry | flattened geometry column varies by reader | inspect actual `colData` names and class |
| R/Python join fails | subset or order mismatch | export all baseline IDs and enforce exact set/order |
| Empty candidate file fails | zero-byte TSV lacks headers | normalize to the shared declared schema |
| A single fence drives exclusion | integrated review was skipped | finish evidence integration, plots and impact validation |

## Bundled Resources

- `scripts/spacetrooper_helpers.R` — required shared definitions before branching.
- `references/spacetrooper-workflow.md` — required branch, polygon and bridge details.
- `../spatial-transcriptomics-qc/references/integrated-assessment.md` — required shared interpretation and D2 policy.

## References

- SpaceTrooper Bioconductor package: https://bioconductor.org/packages/SpaceTrooper
- SpaceTrooper source: https://github.com/drighelli/SpaceTrooper
- SpatialExperiment package: https://bioconductor.org/packages/SpatialExperiment
- zellkonverter AnnData/H5AD conversion: https://bioconductor.org/packages/zellkonverter
