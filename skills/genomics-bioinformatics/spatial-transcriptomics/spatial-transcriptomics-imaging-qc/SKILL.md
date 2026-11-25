---
name: "spatial-transcriptomics-imaging-qc"
description: "SpaceTrooper imaging-cell QC for Xenium, CosMx and MERFISH. Automatically compute input-supported per-cell metrics and QScore when possible, inspect overall/sample distributions, recommend data-dependent QScore and individual-metric cutoffs, and map expected removals. Require D1 before polygon QC; require D2 only when the user later requests a filtered copy. Use the sparse Python fallback only after official installation or execution fails."
license: "CC-BY-4.0"
---

# Imaging-Cell Spatial Transcriptomics QC

## Overview

Use SpaceTrooper as the primary calculation engine. The agent inspects computed
distributions and recommends filtering cutoffs; it does not invent a new QC
score or perform mandatory biological evidence adjudication. QScore is the
preferred final numeric criterion when valid. Individual metric cutoffs are
also reported. Keep package outlier labels separate from the selected
filtering mask.

Before execution, read:

- `references/spacetrooper-workflow.md` for official APIs and conditions;
- `references/fallback-validation.md` before using the fallback;
- `../spatial-transcriptomics-qc/references/cutoff-and-filtering.md` for D2,
  exact-rule accounting, and reporting;
- `scripts/spacetrooper_helpers.R` for official-package bridging;
- `scripts/spacetrooper_fallback.py` only after an official failure.

## When to Use

- QC Xenium segmented cells before downstream analysis
- QC CosMx RNA or protein cells with size, FOV, and control information
- QC MERFISH/MERSCOPE cells with area or volume metadata
- Calculate SpaceTrooper signal-density, control, geometry, and QScore outputs
- Recommend a QScore cutoff from observed whole-dataset/sample distributions
- Recommend individual SpaceTrooper metric cutoffs when QScore is not desired
- Add polygon-derived checks only after explicit D1 approval
- Use `spatial-transcriptomics-spot-qc` for spot/bin assays instead

## Prerequisites

Require unique aligned cell IDs, a valid nonnegative raw count matrix, and
technology metadata. Coordinates, sample/FOV, controls, area/volume, polygons,
and platform-specific fields are independent capabilities: absence skips only
the functions that require them. Never replace an unmeasured capability with a
zero-valued metric.

Check before installing and record the successful version and signatures:

```bash
command -v Rscript
Rscript -e 'cat(requireNamespace("SpaceTrooper", quietly=TRUE), "\n")'
```

If missing, attempt a compatible official Bioconductor installation. Do not
force a development release incompatible with the installed R version:

```r
if (!requireNamespace("BiocManager", quietly=TRUE))
  install.packages("BiocManager", repos="https://cloud.r-project.org")
if (!requireNamespace("SpaceTrooper", quietly=TRUE))
  BiocManager::install("SpaceTrooper", ask=FALSE, update=FALSE)
stopifnot(requireNamespace("SpaceTrooper", quietly=TRUE))
packageVersion("SpaceTrooper")
```

Preserve installation and execution errors. Use the bundled fallback only
after an actual official attempt fails; never rewrite fallback code ad hoc.

## Pre-flight Interview

Inspect polygon availability read-only, then ask D1 before any QC calculation
when usable polygon information exists. Do not ask which metrics to calculate.
D2 is not part of a QC-only request and is asked only after a later filtering
request and exact impact preview.

```yaml
decisions:
  - id: D1
    param: polygon_qc
    kind: required
    source: data
    ask: "Usable cell polygons are present. Should I run Polygon QC in addition to Basic QC?"
    default: null
    skip_if: "no parseable polygon source with cell-ID overlap"

  - id: D2
    param: filtering_rule
    kind: optional_conditional
    source: user
    ask: "Which displayed rule should I apply to a separately named filtered copy: the final recommendation, one metric at its recommended cutoff, your own rule, or no filtering?"
    default: null
    skip_if: "the user has not requested filtering"
```

D1 applies identically to official and fallback execution. Approval adds
Polygon QC to Basic QC; declining it runs Basic QC only. D1 never authorizes
filtering. Record both decisions and their exact scope.

## Workflow

### Step 1: Confirm Imaging Route and Preserve the Baseline

Verify the router selected `imaging`, align counts/metadata/coordinates by cell
ID, and keep an immutable baseline. Record loader/join losses separately.

```python
import json
from pathlib import Path

route = json.loads(Path("qc_input_classification.json").read_text())
if route["route"] != "imaging":
    raise ValueError("segmented-cell imaging evidence is required")
print(route["platform_candidates"], route["confidence"])
```

### Step 2: Resolve Official vs Fallback Execution

Probe namespace, exports, formals, and a minimal input-compatible call. The
official path wins only when both loading and required execution succeed.

```r
required <- c("spatialPerCellQC", "computeSpatialOutlier",
              "computeOutliersQScore", "computeQScore")
official_ready <- requireNamespace("SpaceTrooper", quietly=TRUE) &&
  all(required %in% getNamespaceExports("SpaceTrooper"))
print(official_ready)
```

Log `official`, `fallback_python`, or `not_run`, plus the failure reason. A
failure in official calculation may trigger the bundled Python fallback from
the preserved baseline. Python fallback requirements are `numpy`, `pandas`,
and `scipy`; `anndata` is optional and used only for direct H5AD input.

### Step 3: Perform the D1 Polygon Gate

Before QC, inspect only polygon presence, parseability, non-empty geometry, and
cell-ID overlap. If usable, ask D1. Do not calculate polygon area/aspect ratio,
attach geometry, or map polygons until approved.

```python
polygon_usable = polygon_file_exists and polygon_ids_overlap_cells
print({"polygon_usable": polygon_usable, "matched_cells": matched_count})
# Ask D1 here when polygon_usable is true; otherwise continue Basic QC.
```

### Step 4: Detect Capabilities, Then Run Supported Official Functions

Before each call, inspect feature annotations and metadata. Always calculate
valid count totals/detected features. Calculate control metrics only when
recognized controls are actually measured; area/signal density only when the
platform area/volume input exists; aspect/border metrics only when their source
fields exist; and QScore only when its eligible predictors and training set are
available. A measured control value of zero is different from no control
features. Record every function as `completed`, `skipped`, or `failed`, with a
reason. Unexpected failure of an optional function preserves earlier outputs;
invalid counts, duplicate/misaligned IDs, or corrupt core input remain fatal.

Use the documented platform loader with polygon attachment matching D1. Run
`spatialPerCellQC(..., rmZeros=FALSE)` to preserve the denominator. Basic
outputs include `sum`, `detected`, control/target metrics, control ratio,
`Area_um`, and signal density; aspect ratio and CosMx border distance are
conditional.

```r
spe_qc <- SpaceTrooper::spatialPerCellQC(spe_baseline, rmZeros=FALSE)
stopifnot(ncol(spe_qc) == ncol(spe_baseline))
```

Calculate package outlier labels for supported QScore metrics, then calculate
dataset-specific QScore with a recorded seed. Do not transfer an unrelated
model.

```r
set.seed(1713)
spe_qc <- SpaceTrooper::computeOutliersQScore(spe_qc)
spe_qc <- SpaceTrooper::checkOutliers(spe_qc, verbose=TRUE)
spe_qc <- SpaceTrooper::computeQScore(spe_qc, verbose=TRUE)
stopifnot("QScore" %in% colnames(SummarizedExperiment::colData(spe_qc)))
```

For other displayed metrics, calculate official fences as references, not
final cutoffs.

```r
spe_qc <- SpaceTrooper::computeSpatialOutlier(
  spe_qc, computeBy="log2SignalDensity", method="both", scuttleType="both")
print(attr(spe_qc$log2SignalDensity_outlier_sc, "thresholds"))
```

### Step 5: Run the Sparse Python Fallback Only After Failure

Copy the bundled script unchanged to the workspace. Keep counts sparse: use a
SciPy sparse NPZ plus a feature list and metadata, or H5AD when `anndata` is
available. Do not export the count matrix to TSV. Pass polygon vertices only
after D1 approval.

```bash
python spacetrooper_fallback.py \
  --counts-npz cells_by_features.npz \
  --metadata cell_metadata.tsv \
  --features feature_names.csv \
  --technology 10X_Xenium \
  --output qc_metrics.parquet \
  --seed 1713
```

The fallback detects the same capabilities, preserves completed metrics when
polygon/outlier/QScore work is skipped or fails, and emits `*.status.json` with
per-feature `completed`/`skipped`/`failed` states. It names its candidate
`QScore_fallback_python`, never `QScore`. It preserves the official training-
label rules, balanced sampling, pairwise interactions, ridge-binomial model,
and cross-validation, but SciPy optimization/lambda paths and Python sampling
differ from `glmnet`/R. The candidate is currently unvalidated and its status
remains `qscore_usable=false` with `validation_state=unvalidated`. Never use
`QScore_fallback_python` for cutoff recommendation, expected-removal preview,
or filtering. Record QScore as unavailable and continue with individual
metrics. Official-versus-fallback qualification is a development activity and
must not be repeated on routine user datasets.

### Step 6: Review QScore Distributions and Recommend Its Cutoff

Plot QScore overall and by sample/FOV, inspect tails and sample shifts, then
choose a candidate cutoff. Show sensitivity around nearby values. Do not accept
the package flag default `0.5` without this review.

```python
q = metrics["QScore"].dropna()
print(q.describe(percentiles=[.01, .05, .1, .25, .5, .75, .9, .95, .99]))
for cutoff in candidate_cutoffs:
    print(cutoff, int((metrics["QScore"] < cutoff).sum()))
```

Record the recommended cutoff with `operator=lt`, explanation, exact expected
impact, and spatial map. This QScore workflow applies to official SpaceTrooper
`QScore`; do not substitute `QScore_fallback_python`. If the official score is
missing, incomplete, or has no defensible cutoff, explain why and use individual
metrics.

### Step 7: Recommend Individual Metric Cutoffs

Review overall/sample distributions for all available major metrics. Prioritize
`log2SignalDensity` (bad-low), `Area_um` (data-dependent; SpaceTrooper uses
bad-high for QScore training), `log2Ctrl_total_ratio` (bad-high), and CosMx
`log2AspectRatio`/border context (two-sided when appropriate). Also report
`sum`, `detected`, control, and target metrics when informative.

```python
for metric in available_metrics:
    print(metric, metrics.groupby("sample_id")[metric].describe())
```

For each metric, record a cutoff and direction or `no_cutoff` with a reason.
Report metric-level package outliers separately.

### Step 8: Recommend the Final Rule and Complete the QC Report

Prefer a valid QScore cutoff; otherwise use the smallest defensible individual-
metric rule. Use explicit AND/OR for multiple conditions. Run the shared
calculator and map `selected_filter_match`.

```bash
python qc_apply_rules.py --metrics qc_metrics.tsv \
  --rules qc_filter_rules.tsv --rule-set-id agent-final-001 --logic OR \
  --mode preview \
  --id-column observation_id --group-column sample_id \
  --output-prefix qc_recommendation
```

Show exact overall/sample removal counts and spatial distribution in the QC
report. If filtering was not requested, record D2=`not_applicable` and finish.
If the user later requests the recommendation, one metric, a changed cutoff,
or an AND/OR combination, preview that exact `rule_set_id`, show revised impact,
then obtain D2. Apply mode requires the matching rule-set digest; any change
invalidates the prior approval. Only then create a separately named copy.

## Key Parameters

| Parameter | Official default | Use in this workflow |
|---|---:|---|
| `spatialPerCellQC(rmZeros)` | `TRUE` | set `FALSE`; preserve source denominator |
| `micronConvFact` | `0.12` | use only for CosMx pixels and record provenance |
| `computeSpatialOutlier(method)` | `mc/scuttle/both` | package reference flags selected from actual skew |
| `scuttleType` | `both` | choose direction per displayed metric |
| `computeQScore(bestLambda)` | internal CV | leave `NULL`, record seed and returned lambda |
| `computeQScoreFlags(qsThreshold)` | `0.5` | call only with reviewed explicit cutoff |
| QScore minimum outliers | `0.1%` | package eligibility rule, not filtering cutoff |

## Common Recipes

### Apply the Reviewed QScore Cutoff

```r
reviewed_cutoff <- rules$threshold[rules$metric == "QScore"]
spe_qc <- SpaceTrooper::computeQScoreFlags(
  spe_qc, qsThreshold=reviewed_cutoff, useQSQuantiles=FALSE)
```

### Preserve Original and Create the D2-Approved Copy

```python
approved = pd.read_csv("qc_recommendation_matches.tsv", sep="\t")
mask = approved.set_index("observation_id").loc[adata.obs_names,
                                                   "selected_filter_match"]
adata_filtered = adata[(~mask).to_numpy()].copy()
adata_filtered.write_h5ad("spatial_imaging_qc_filtered_copy.h5ad")
```

## Expected Outputs

- engine/version/function log and fallback reason
- complete per-cell metric/QScore table and package outlier columns
- D1 polygon results only when approved
- overall/sample distributions and maps for QScore and major metrics
- exact rules and per-rule/final impact tables
- QC report containing D1/D2 and actual filtering result
- optional separately named filtered object; unchanged source object

## Troubleshooting

| Problem | Cause | Resolution |
|---|---|---|
| Official package cannot install | R/Bioconductor or system dependency mismatch | preserve error, run bundled fallback, disclose mode |
| Counts disappear | package default `rmZeros=TRUE` | restart from baseline with `rmZeros=FALSE` |
| QScore fails | required metric/outliers/training set/dependencies absent | report reason; recommend individual metrics |
| Fallback QScore status is false | official parity is unverified or dependencies failed | ignore the quarantined candidate; use individual metrics |
| Polygon fields exist but D1 unanswered | mandatory conditional approval unresolved | pause before QC and ask D1 |
| Samples have different distributions | slide shift | show per-sample panels; avoid blind global cutoff |
| Count differs from plot | thresholds duplicated in code | use only the rule table and rerun calculator |

## Bundled Resources

- `references/spacetrooper-workflow.md` — official functions, formulas, inputs, and errors.
- `references/fallback-validation.md` — runtime validation status, use limits, and dependencies.
- `scripts/spacetrooper_helpers.R` — official package bridge.
- `scripts/spacetrooper_fallback.py` — sparse runtime fallback used only after official failure.
- `../spatial-transcriptomics-qc/references/cutoff-and-filtering.md` — shared cutoff/D2/report contract.
- `../spatial-transcriptomics-qc/scripts/qc_apply_rules.py` — deterministic rule/impact calculator.

## References

- SpaceTrooper source: https://github.com/drighelli/SpaceTrooper
- SpaceTrooper Bioconductor package: https://bioconductor.org/packages/SpaceTrooper
- SpatialExperiment: https://bioconductor.org/packages/SpatialExperiment
