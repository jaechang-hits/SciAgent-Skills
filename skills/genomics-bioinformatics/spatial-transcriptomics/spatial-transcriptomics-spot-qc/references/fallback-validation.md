# SpotSweeper Python Fallback: Runtime Status and Limits

## Provenance and runtime policy

- SpotSweeper 1.9.3, commit
  `7e6ebf68c205cf0c102d8ed6b363752d5288d179`
- Inspected functions: `localOutliers`, `.local_modified_z`, `localVariance`,
  `findArtifacts`, and `flagVisiumOutliers`
- Runtime fallback: `scripts/spotsweeper_fallback.py`
- Upstream license notice: `UPSTREAM_LICENSE.md`

The Python script is standalone and never reads a development reference clone
or validation fixture at runtime. Use the official package first and run the
fallback only after official installation or required execution fails. Every
fallback column carries `_fallback_python` and must not be presented as an
official SpotSweeper column.

## Supported runtime calculations

- Sparse count-derived `sum`, `detected`, and explicitly validated
  mitochondrial sum/percentage metrics when they are absent from metadata
- Sample-stratified K-nearest neighbors with the focal observation excluded
- Local modified-z values and directional outlier flags
- Local-variance mean/residual calculations
- Conditional artifact calculations for verified array geometry
- Six package-maintained systematic positions only for explicitly confirmed
  standard 10x Visium data with valid `array_row` and `array_col`

The status JSON records each function as `completed`, `skipped`, or `failed`.
An optional local, systematic, or artifact failure does not discard successful
count metrics. Corrupt counts, duplicate IDs, and ID/shape mismatches remain
fatal.

## Validation and cutoff-use status

| Output | Current status | Runtime use |
|---|---|---|
| Sparse count and mitochondrial metrics | Regression fixtures passed | May be visualized and used for individual-metric cutoff recommendations |
| Local modified-z and directional flags | Equation-level source comparison and regression fixtures passed | May support recommendations with fallback-engine and tie-handling disclosure |
| Standard-Visium systematic positions | Maintained position set and gating tests passed | Use only when platform is confirmed standard 10x Visium and array indices are valid |
| Local-variance residuals | Source-derived comparison passed, but installed-package end-to-end validation is incomplete | Compute and visualize as provisional diagnostics; do not use as the sole final filtering condition |
| Artifact flags | Synthetic/source-derived fixtures passed, but installed-package end-to-end validation is incomplete | Compute only when geometry and mitochondrial inputs are valid; treat as provisional and not as the sole final filtering condition |

Routine user QC must not run official-versus-fallback comparison metrics. When
a provisional feature is unavailable or fails, record the reason and continue
with validated raw metrics, local modified-z outputs, and any other completed
features. Do not invent an integrated score.

## Large-data design

`scipy.spatial.cKDTree` performs sample-specific batched queries, so the fallback
does not form an N-by-N distance matrix. Memory is O(Nk). Artifact detection
queries the maximum required neighborhood once and reuses prefixes for smaller
orders. Optional sparse NPZ count processing is chunked, and Parquet may be used
to avoid large TSV input/output.

## Implementation differences and omission conditions

| Function | Python difference | Required runtime response |
|---|---|---|
| KNN | `cKDTree` replaces `BiocNeighbors` | Disclose that tied/equidistant neighbors can produce different local results |
| Local variance | Python Huber IRLS approximates default `MASS::rlm` | Treat residuals as provisional; surface zero-variance regression failures without adding an epsilon |
| Artifact PCA | NumPy SVD replaces `stats::prcomp` | Assess spatial flags rather than raw PC sign |
| Artifact k-means | Lloyd k-means and NumPy RNG replace R Hartigan-Wong/RNG | Treat boundary-dependent artifact flags as provisional |
| Max-k reuse | Smaller neighborhoods are prefixes of one maximum-k query | Disclose possible tie differences on regular grids |
| Systematic positions | Restricted to the maintained standard-Visium position set | Skip unless standard 10x Visium and valid array row/column structure are both confirmed |

Skip artifact calculations when mitochondrial inputs, array shape, or a valid
single-sample geometry are unavailable. Skip a local metric when a sample has
too few observations for its requested neighbor count. Preserve all unrelated
completed outputs and their denominator.

## Dependencies

Required: Python 3, NumPy, pandas, and SciPy. No scikit-learn, statsmodels, or R
package is required. A pandas Parquet backend is optional; use metadata CSV/TSV
when it is unavailable.

Never call the fallback package-equivalent. Future development validation may
update the pinned version and approved use scope, but routine Agent execution
uses only the status stated in this document.
