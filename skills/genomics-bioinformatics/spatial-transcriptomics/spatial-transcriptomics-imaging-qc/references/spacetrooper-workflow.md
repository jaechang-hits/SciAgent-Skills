# SpaceTrooper Official API Used by This Skill

Source inspected: SpaceTrooper 1.3.3, commit
`95265069ca8de5eeb03526f29f8debae9dde4d13`.

## Per-cell metrics

`spatialPerCellQC(spe, micronConvFact=0.12, rmZeros=TRUE,
negProbList=..., use_altexps=NULL)` calls `scater::addPerCellQC()` and adds:

| Output | Official calculation / condition |
|---|---|
| `sum`, `detected`, `total` | package per-cell QC/loader fields |
| `control_sum` | row sum of all `subsets_*_sum` control columns |
| `control_detected` | corresponding `subsets_*_detected` sum |
| `target_sum`, `target_detected` | total metric minus control metric |
| `ctrl_total_ratio` | `control_sum / total`; `NA` becomes 0 |
| `log2Ctrl_total_ratio` | `log2(ctrl_total_ratio + 0.0001)` |
| `Area_um` | CosMx `Area * micronConvFact^2`; Xenium uses `cell_area` fallback; MERFISH loader supplies area/volume |
| `SignalDensity` | `sum / Area_um`; CosMx protein uses `total` |
| `log2SignalDensity` | `log2(SignalDensity)` |
| `log2AspectRatio` | `log2(AspectRatio)` when present |
| `dist_border` | CosMx minimum x/y distance to FOV borders |

Default control prefixes are `NegPrb`, `Negative`, `SystemControl`, `Ms IgG1`,
`Rb IgG`, `BLANK_`, `NegControlProbe`, `NegControlCodeword`,
`UnassignedCodeword`, and `Blank`. `rmZeros=TRUE` removes zero-sum cells; this
workflow overrides it to `FALSE`.

The package may materialize control-derived zeros when no control subset was
measured. The workflow capability check must distinguish this absence from a
measured zero: omit those metrics from recommendations/filtering and report
them as skipped. Missing area/volume prevents signal-density/QScore work but
does not prevent valid count metrics.

## Outliers

`computeSpatialOutlier()` supports `scuttle` MAD fences,
`robustbase::mc()`/`adjbox()` adjusted-boxplot fences, or both. The medcouple
must be strictly between -0.6 and 0.6. Labels are `LOW`, `HIGH`, or `NO`, with
numeric fences in the `thresholds` attribute.

`computeOutliersQScore()` selects scuttle when skewness is between -1 and 1 and
medcouple otherwise. Signal density is assessed for `total > 0`; if its lower
fence is below the observed minimum, the 1% quantile replaces it. Control ratio
is assessed where nonzero. `checkOutliers()` requires bad outliers to comprise
at least 0.1% before a metric enters the default model; low signal-density
outliers are mandatory.

## QScore

Supported predictors are `log2SignalDensity`, `Area_um`,
`log2AspectRatio`, and `log2Ctrl_total_ratio`. Signal density is mandatory;
aspect ratio/border is CosMx-only. The fullest default formula is:

```text
~(log2SignalDensity + Area_um +
  I(abs(log2AspectRatio) * as.numeric(dist_border < 50)) +
  log2Ctrl_total_ratio)^2
```

Bad training cells are low signal density, high area, high control ratio, and
for CosMx two-sided aspect-ratio outliers within 50 px of an FOV border. Good
examples use signal density between the 90th/99th percentiles, area between the
25th/75th percentiles, and for CosMx central aspect ratio beyond 50 px. Good
examples overlapping bad are removed and downsampled to match bad.

The model is ridge logistic regression (`glmnet`, `alpha=0`); `lambda.min`
comes from `cv.glmnet()` unless supplied. Probabilities are `QScore`; incomplete
predictor rows remain `NA`. Training is dataset-specific and stochastic unless
the seed is fixed. `computeQScoreFlags()` defaults to `QScore < 0.5`, but this
workflow supplies only a post-review cutoff.

## Polygon functions and D1

Official readers normalize cell IDs, multipolygon state, and `sf` geometry.
`computeAreaFromPolygons()` uses `sf::st_area()`.
`computeAspectRatioFromPolygons()` uses bounding-box width/height and returns
`NA` for multipolygons, empty geometry, or zero height. Polygon calculations
begin only after D1. Basic metrics/QScore remain independent where inputs exist.

## Input and error conditions

- Unique aligned cell IDs and `SpatialExperiment` are required officially.
- Missing area, unsupported custom predictors, technology-incompatible border
  terms, inadequate outliers/training examples, and missing variables
  invalidate QScore.
- `computeQScore()` removes zero-total cells internally; map scores back to the
  full baseline with `NA` for unscored cells.
- Namespace load alone is insufficient; record actual function execution.

## Python fallback mapping

`scripts/spacetrooper_fallback.py` accepts a cells-by-features SciPy sparse NPZ
plus metadata and feature names, or an H5AD file when `anndata` is installed.
It aggregates backed/sparse matrices in row chunks and never requires a dense
count matrix. Its QScore analogue follows the official sequence above but is
named `QScore_fallback_python` and is currently ineligible for cutoff
recommendation or filtering. Read `fallback-validation.md` for the authoritative
runtime status. An unavailable fallback score does not stop basic metrics or
individual-metric recommendations.
