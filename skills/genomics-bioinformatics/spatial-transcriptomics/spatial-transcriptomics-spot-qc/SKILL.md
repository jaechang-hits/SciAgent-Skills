---
name: "spatial-transcriptomics-spot-qc"
description: "SpotSweeper spot/bin QC for Visium, Visium HD, Slide-seq and related assays. Automatically compute input-supported metrics, local robust-z outliers and conditional spatial flags, inspect overall/sample distributions, and recommend data-dependent cutoffs and a final explicit rule. D2 is required only when the user requests a filtered copy. Uses the scalable Python fallback only after official execution fails; no invented integrated score."
license: "CC-BY-4.0"
---

# Spot/Bin Spatial Transcriptomics QC

## Overview

Use SpotSweeper as the primary spatial QC engine. It has no SpaceTrooper-like
integrated QScore, so do not invent one. Review raw metric distributions and
SpotSweeper spatial flags, recommend numeric cutoffs and a final explicit
filtering rule, and keep package flags distinct from raw-metric cutoffs.

Before execution, read:

- `references/spotsweeper-workflow.md` for official calculations/conditions;
- `references/fallback-validation.md` before fallback execution;
- `../spatial-transcriptomics-qc/references/cutoff-and-filtering.md` for cutoff,
  D2, and report consistency;
- `scripts/spotsweeper_fallback.py` only after an official failure.

## When to Use

- QC Visium or Visium HD spots/bins before downstream analysis
- Detect locally low library size or detected-feature spots
- Inspect local mitochondrial outliers when mitochondrial targets are measured
- Detect regional mitochondrial artifacts on a valid array geometry
- Report known systematic Visium array positions separately
- Compare metric distributions and expected filtering impact across sections
- Use `spatial-transcriptomics-imaging-qc` instead for Xenium/CosMx/MERFISH cells

## Prerequisites

Require valid nonnegative raw counts and unique aligned spot/bin IDs for count
QC. Coordinates, sample/slide fields, array positions, mitochondrial features,
and verified array geometry are separate capabilities. Missing optional inputs
skip only their dependent functions; do not fill unmeasured metrics with zero.

Check before installing:

```bash
command -v Rscript
Rscript -e 'cat(requireNamespace("SpotSweeper", quietly=TRUE), "\n")'
```

Attempt the compatible official Bioconductor package when missing:

```r
if (!requireNamespace("BiocManager", quietly=TRUE))
  install.packages("BiocManager", repos="https://cloud.r-project.org")
if (!requireNamespace("SpotSweeper", quietly=TRUE))
  BiocManager::install("SpotSweeper", ask=FALSE, update=FALSE)
stopifnot(requireNamespace("SpotSweeper", quietly=TRUE))
packageVersion("SpotSweeper")
```

Record the actual error if install/load/function execution fails. Only then
execute the bundled fallback; do not write a new approximation during analysis.

## Pre-flight Interview

There is no D1 polygon decision for spot/bin QC and no pre-QC metric-selection
question. Automatically run every supported function whose inputs are usable.
Ask D2 only if the user requests filtering after seeing the report and impact.

```yaml
decisions:
  - id: D2
    param: filtering_rule
    kind: optional_conditional
    source: user
    ask: "Which displayed rule should I apply to a separately named filtered copy: the final recommendation, one metric at its recommended cutoff, your own rule, or no filtering?"
    default: null
    skip_if: "the user has not requested filtering"
```

## Workflow

### Step 1: Confirm Spot/Bin Routing and Preserve the Source

Require compound spot/bin evidence, verify the selected HD resolution, align
IDs and coordinates, and preserve the complete source. A tissue-only analysis
view is not filtering and must be recorded separately.

```python
import json
from pathlib import Path

route = json.loads(Path("qc_input_classification.json").read_text())
if route["route"] != "spot":
    raise ValueError("spot/bin evidence is required")
print(route["platform_candidates"], route["observation_unit"])
```

### Step 2: Detect Capabilities and Compute Supported Numeric Metrics

Calculate `sum`/total counts and `detected` genes from raw counts. Add
mitochondrial sum/percentage only after identifying actual mitochondrial
features. If no mitochondrial features are measured, omit those columns and
record `skipped`; if measured counts are all zero, retain true zeros but skip
functions requiring positive signal. Retain raw and transformed columns used
by SpotSweeper. Record each function as `completed`, `skipped`, or `failed`.

```r
spe <- scuttle::addPerCellQCMetrics(
  spe, subsets=list(Mito=is_mitochondrial_feature))
stopifnot(all(c("sum", "detected") %in% colnames(colData(spe))))
```

### Step 3: Resolve Official vs Fallback Mode

Verify exports and actual execution compatibility. Official use requires the
function call to succeed, not just namespace load.

```r
required <- c("localOutliers", "localVariance", "findArtifacts",
              "flagVisiumOutliers", "plotQCmetrics")
official_ready <- requireNamespace("SpotSweeper", quietly=TRUE) &&
  all(required %in% getNamespaceExports("SpotSweeper"))
print(official_ready)
```

Log mode, version, function, parameters, and failure reason.

### Step 4: Run Official Local Outliers by Sample

For each sample, choose `n_neighbors` smaller than its spot count. Run
`localOutliers()` on `sum` and `detected` (usually lower direction, `log=TRUE`)
and on mitochondrial percentage only when measured. The official modified z is
the focal value versus neighbor median/unscaled MAD; the focal spot is excluded.

```r
k <- min(36L, min(table(spe$sample_id)) - 1L)
stopifnot(k >= 1L)
spe <- SpotSweeper::localOutliers(
  spe, metric="sum", direction="lower", n_neighbors=k,
  samples="sample_id", log=TRUE, cutoff=3, workers=1)
spe <- SpotSweeper::localOutliers(
  spe, metric="detected", direction="lower", n_neighbors=k,
  samples="sample_id", log=TRUE, cutoff=3, workers=1)
```

`cutoff=3` applies to the local robust z-score and creates a package flag. It
is not a raw-count cutoff and is not automatically the final filtering rule.
Run this automatically for every calculable supported metric. Missing metrics,
coordinates, or sufficient per-sample neighbors skip only that calculation.

### Step 5: Run Conditional Spatial Artifact Functions

Only for confirmed standard 10x Visium arrays with array row/column metadata,
report the six package-maintained `systematic_outliers` positions separately.
Do not apply this fixed list to Visium HD, Slide-seq, or another spot platform
merely because it has columns named `array_row` and `array_col`.

```r
if (identical(confirmed_platform, "10x Visium") &&
    all(c("array_row", "array_col") %in% colnames(colData(spe))))
  spe <- SpotSweeper::flagVisiumOutliers(spe)
```

Run `findArtifacts()` only for one sample at a time, with measured finite
nonzero mitochondrial sum/percentage and verified hexagonal/square geometry.

```r
if (mitochondrial_signal_available) {
  sample_spe <- spe[, spe$sample_id == selected_sample]
  sample_spe <- SpotSweeper::findArtifacts(
    sample_spe, mito_percent="subsets_Mito_percent",
    mito_sum="subsets_Mito_sum", samples="sample_id",
    n_order=5, shape="hexagonal", log=TRUE,
    name="artifact", var_output=TRUE)
}
```

Treat `artifact`, `systematic_outliers`, and `*_outliers` as package flag
results, not numeric cutoff recommendations.

### Step 6: Use the Scalable Python Fallback Only After Official Failure

Standardize metadata with IDs, sample, coordinates, and numeric metrics, copy
the script unchanged, and execute it. Parquet is preferred for large inputs;
TSV/CSV remains supported for metadata only. The script requires `numpy`,
`pandas`, and `scipy`.

```bash
python spotsweeper_fallback.py \
  --metadata spot_metrics.parquet \
  --output qc_metrics.parquet \
  --id-column observation_id \
  --x x --y y --sample sample_id \
  --neighbors 36 --cutoff 3 --workers 1
```

Confirmed standard Visium plus valid `array_row`/`array_col` columns trigger
systematic-position checks; pass `--platform "10x Visium"` when the metadata
does not already contain an unambiguous platform/technology field. The legacy
`--systematic` flag does not bypass platform validation. Pass
`--artifacts --mito-percent ... --mito-sum ... --shape ...` only after array
geometry is verified; the script then checks remaining input conditions.
Disclose fallback scalability and tie limitations from the validation
reference. Outputs use
`*_z_fallback_python`, `*_outliers_fallback_python`, and
`artifact_fallback_python` names so they cannot be mistaken for official
package output.

When `--metrics` is omitted, the script automatically uses the supported
numeric metrics actually present: lower/logged for `sum` and `detected`, and
higher/raw for measured mitochondrial percentage, matching the official
vignette. Its status JSON records each function as
`completed`, `skipped`, or `failed`. An optional local/artifact failure does not
discard count metrics or other successful outputs; corrupt counts and ID/shape
mismatches remain fatal.

The fallback uses `cKDTree` per sample, processes queries in batches, and never
forms an N-by-N distance matrix. Its local modified-z equation is the official
equation. Local variance uses a Python Huber-IRLS approximation to `MASS::rlm`;
artifact PCA/k-means and random initialization differ from R. Present these as
fallback flags. Local modified-z results may support cutoff recommendations
with fallback-engine disclosure. Treat local-variance residuals and artifact
flags as provisional diagnostics, not as the sole basis for a final filtering
rule. Routine user QC must not run official-versus-fallback qualification.

When `sum`/`detected` are not already available, pass an observations-by-
features sparse NPZ and feature list with `--counts-npz` and `--features`.
Optionally pass `--mito-feature-file` containing explicitly validated
mitochondrial features; the script then computes the requested mitochondrial
sum/percent columns without densifying counts. Do not infer mitochondrial
features from an unverified naming prefix.

### Step 7: Plot and Review Actual Distributions and Flags

Plot every major numeric metric overall and by sample: total counts, detected
genes, mitochondrial sum/percentage when valid, and any requested metric.
Also map raw metric values, local z-scores, package flags, and artifact regions.

```r
p <- SpotSweeper::plotQCmetrics(
  spe, sample_id="sample_id", sample=selected_sample,
  metric="sum", outliers="sum_outliers")
ggplot2::ggsave("spotsweeper_sum_outliers.png", p, width=6, height=6)
```

```python
for metric in numeric_metrics:
    print(metric, metrics.groupby("sample_id")[metric].describe())
for flag in package_flags:
    print(flag, metrics.groupby("sample_id")[flag].agg(["sum", "size"]))
```

### Step 8: Recommend Numeric Cutoffs and the Final Rule

Only after inspecting plots, recommend raw-metric cutoffs and directions.
Explain the observed tail/separation/sample behavior and show exact count,
percentage, and spatial map for each. A metric may be `no_cutoff` when a single
value is not defensible.

Do not translate the local z cutoff into a raw-count threshold. Present numeric
rules separately from `sum_outliers`, `detected_outliers`,
`systematic_outliers`, and `artifact`. Because SpotSweeper has no integrated
score, recommend a transparent final expression such as one numeric criterion,
one package flag, or an explicit AND/OR combination—never a new weighted score.

```text
(sum < reviewed_sum_cutoff) OR detected_outliers
```

#### Calculate Exact Impact and Complete the Report

Write the selected rows to `qc_filter_rules.tsv`, state AND/OR, run the shared
calculator, and map `selected_filter_match`.

```bash
python qc_apply_rules.py --metrics qc_metrics.tsv \
  --rules qc_filter_rules.tsv --rule-set-id agent-final-001 --logic OR \
  --mode preview \
  --id-column observation_id --group-column sample_id \
  --output-prefix qc_recommendation
```

Show overall/sample counts, percentages, and spatial distribution. With no
filtering request, record D2=`not_applicable` and finish the QC report. If the
user later selects another rule, preview that exact rule set again. D2 approval
includes its digest and becomes invalid after any rule or AND/OR change. Apply
only the approved mask to a separately named copy.

## Key Parameters

| Function/parameter | Official default | Condition |
|---|---:|---|
| `localOutliers(metric)` | `detected` | numeric metadata column |
| `direction` | `lower` | `lower`, `higher`, or `both` |
| `n_neighbors` | `36` | strictly less than every sample size |
| `log` | `TRUE` | uses `log1p(metric)` and keeps `<metric>_log` |
| local-z `cutoff` | `3` | package flag reference, not raw cutoff |
| `findArtifacts(n_order)` | `5` | one sample, sufficient spots and mito signal |
| `shape` | `hexagonal` | verify actual geometry; square is supported |
| `workers` | `1` | changes neighbor-search execution only |

## Common Recipes

### Inspect Local-Z Flags Without Filtering

```r
table(spe$sum_outliers, useNA="ifany")
summary(spe$sum_z)
```

### D2-Approved Filtered Copy

```python
matches = pd.read_csv("qc_recommendation_matches.tsv", sep="\t")
mask = matches.set_index("observation_id").loc[adata.obs_names,
                                                  "selected_filter_match"]
adata_filtered = adata[(~mask).to_numpy()].copy()
adata_filtered.write_h5ad("spatial_spot_qc_filtered_copy.h5ad")
```

## Expected Outputs

- official/fallback execution log with version, parameters, and reason
- complete numeric metrics, local z-scores, and package flag table
- overall/sample distributions and spatial maps
- numeric cutoff recommendations separate from package flags
- explicit final AND/OR rule and exact impact tables
- D2 state and optional separately named filtered copy
- unchanged source object and observation accounting

## Troubleshooting

| Problem | Cause | Resolution |
|---|---|---|
| `n_neighbors` error | sample has at most `k` spots | reduce `k` and record it |
| Non-finite after log | negative/invalid metric | correct input; do not run flag |
| Artifact call fails | no mitochondrial signal or multiple samples | skip with reason or run per sample |
| Wrong artifact neighborhood | incorrect array shape | verify hexagonal versus square |
| Fallback is slow | base-R all-pairs neighbor search | use official package for large data |
| Equidistant results differ | fallback deterministic tie break differs | disclose; compare flags spatially |
| Final rule looks like a score | independent flags were numerically combined | replace with explicit AND/OR rule |

## Bundled Resources

- `references/spotsweeper-workflow.md` — official functions and algorithms.
- `references/fallback-validation.md` — runtime validation status, use limits, and dependencies.
- `scripts/spotsweeper_fallback.py` — scalable runtime fallback used only after official failure.
- `../spatial-transcriptomics-qc/references/cutoff-and-filtering.md` — shared cutoff/D2/report contract.
- `../spatial-transcriptomics-qc/scripts/qc_apply_rules.py` — deterministic rule/impact calculator.

## References

- SpotSweeper source: https://github.com/MicTott/SpotSweeper
- SpotSweeper Bioconductor package: https://bioconductor.org/packages/SpotSweeper
- SpatialExperiment: https://bioconductor.org/packages/SpatialExperiment
