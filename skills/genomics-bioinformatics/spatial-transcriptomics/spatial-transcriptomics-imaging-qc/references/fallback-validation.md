# SpaceTrooper Python Fallback: Runtime Status and Limits

## Provenance and runtime policy

- SpaceTrooper 1.3.3, commit
  `95265069ca8de5eeb03526f29f8debae9dde4d13`
- Inspected functions: `spatialPerCellQC`, `computeSpatialOutlier`,
  `computeOutliersQScore`, `checkOutliers`, `computeTrainDF`,
  `getModelFormula`, `computeQScore`, `computeQScoreFlags`, and polygon helpers
- Runtime fallback: `scripts/spacetrooper_fallback.py`
- Upstream license notice: `UPSTREAM_LICENSE.md`

The Python script is standalone and never reads a development reference clone
or validation fixture at runtime. Use the official R package first. Run the
Python fallback only after official installation or required execution fails,
and always disclose `engine=fallback_python`.

## Supported runtime calculations

- Sparse/chunked cell totals and detected-feature counts without converting the
  whole matrix to dense form or TSV
- Text-preserving cell identifiers, with missing-ID, duplicate-ID, and
  normalization-collision rejection
- Supported control/target totals and detections, stabilized control ratio,
  platform area conventions, and signal density
- Individual median/MAD and adjusted-boxplot outlier labels
- Planar polygon area and bounding-box aspect ratio only after D1 approval and
  only for validated planar coordinates
- A separately named experimental `QScore_fallback_python` candidate

Failures in polygon, individual-outlier, or candidate-QScore work do not erase
earlier valid basic metrics. Corrupt counts and ID/shape mismatches remain fatal.
The `*.status.json` output records each optional feature as `completed`,
`skipped`, or `failed` with its reason.

## Validation and cutoff-use status

| Output | Current status | Runtime use |
|---|---|---|
| Sparse count, control/target, area, and signal-density metrics | Formula and regression fixtures passed | May be visualized and used for individual-metric cutoff recommendations with fallback disclosure |
| Individual outlier labels | Regression tests cover supported equations and edge handling | May be shown as package-derived reference labels; keep them separate from the selected filtering mask |
| Polygon area/aspect ratio | Planar synthetic fixtures passed | Use only after D1 and only when coordinate units and planar geometry are valid |
| `QScore_fallback_python` | Direct official SpaceTrooper QScore agreement is unverified | Do not use for cutoff recommendation, removal preview, or filtering |

The fallback candidate is always named `QScore_fallback_python`; it is never
written as `QScore`. Its status remains `qscore_usable=false` and
`validation_state=unvalidated`, even when a candidate column was computed.
Treat QScore as unavailable and recommend cutoffs from supported individual
metrics. Do not compare official and fallback scores during routine user QC.

Official SpaceTrooper `QScore` remains usable when the official package
successfully computes it and the observed distribution supports a defensible
cutoff. Never substitute the fallback candidate for that official column.

## Implementation differences and omission conditions

| Function | Python difference | Required runtime response |
|---|---|---|
| Medcouple | Exact kernel median up to 2,000 finite values; deterministic order-statistic subsample above that | Disclose that adjusted fences can differ on very large or skewed distributions |
| MAD outliers | Simple unbatched median plus/minus three scaled MADs, without every `scuttle::isOutlier` batch/edge option | Skip or report a failure when the supported unbatched assumptions do not hold |
| QScore sampling | NumPy RNG differs from R `sample()` | Keep the candidate quarantined regardless of successful computation |
| Ridge/CV | SciPy L-BFGS ridge-binomial fits and a fixed penalty grid replace `glmnet` | Keep `qscore_usable=false`; do not infer calibration or cutoff parity |
| Polygon area | Planar shoelace lacks `sf::st_area` CRS and validity semantics | Skip polygon metrics unless D1 is approved and planar coordinates are validated |
| Loader total | `total=sum` only when a loader-provided total is absent | Record the loader path and disclose possible platform-loader differences |

If signal-density prerequisites are absent, skip the QScore candidate and
recommend from the remaining valid individual metrics. If an optional adapter
or output format is unavailable, change the adapter or format rather than
failing unrelated calculations.

## Dependencies

Required: Python 3, NumPy, pandas, and SciPy. `anndata` is optional for direct
H5AD input; NPZ plus metadata/feature files does not require it. Parquet output
requires a pandas Parquet backend. Use CSV/TSV or sparse NPZ inputs when the
optional adapters are unavailable.

Never describe the fallback as package-equivalent. A future development
validation may update the pinned version and the explicitly approved use scope;
until the runtime documents and status behavior are deliberately updated,
`QScore_fallback_python` remains unavailable for cutoff or filtering.
