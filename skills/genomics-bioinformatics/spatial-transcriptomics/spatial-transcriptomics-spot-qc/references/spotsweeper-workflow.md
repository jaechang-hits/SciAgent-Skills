# SpotSweeper Official API Used by This Skill

Source inspected: SpotSweeper 1.9.3, commit
`7e6ebf68c205cf0c102d8ed6b363752d5288d179`.

## `localOutliers()`

Defaults: `metric="detected"`, `direction="lower"`, `n_neighbors=36`,
`samples="sample_id"`, `log=TRUE`, `cutoff=3`, `workers=1`.

For every sample separately, `BiocNeighbors::findKNN()` finds `k` neighbors and
excludes the focal spot. With transformed or raw metric `x`, the score is:

```text
qnorm(0.75) * (x_i - median(x_neighbors)) /
               median(abs(x_neighbors - median(x_neighbors)))
```

Zero/non-finite neighborhood MAD yields score 0. Outputs are `<metric>_z`,
`<metric>_outliers`, and `<metric>_log` when `log=TRUE`. A sample must contain
more spots than `n_neighbors`; metric and coordinates must be finite.

## `localVariance()` and `findArtifacts()`

`localVariance()` uses k nearest neighbors plus the focal spot, calculates
sample variance and mean, replaces non-finite statistics with 0, fits
`MASS::rlm(log2(var) ~ mean)`, and stores residuals.

`findArtifacts()` requires one `SpatialExperiment` sample and numeric nonzero
mitochondrial percentage/sum. For orders `i=1..n_order`, neighborhood sizes are
`3*i*(i+1)` for hexagonal and `4*i*(i+1)` for square arrays. It concatenates
local-variance residuals, mitochondrial percentage, and mitochondrial sum;
runs scaled PCA; clusters two groups with `kmeans(..., centers=2, nstart=25)`;
and labels as artifact the cluster with the smaller mean second-order residual
(`k18` hexagonal or `k24` square). The current source always writes `artifact`
and retains `k*` columns; its `name`/`var_output` arguments do not alter that
implementation. Record the package version because this may change.

## `flagVisiumOutliers()`

This is a package-maintained boolean flag for six **standard 10x Visium** array
row/column positions: `(38,88)`, `(28,32)`, `(49,103)`, `(57,99)`, `(47,77)`, and
`(53,117)`. It is not a learned score or numeric metric cutoff. It requires
`array_row`/`array_col` metadata or compatible Seurat image coordinates.
The official documentation calls these systematic positions observed across
Visium datasets; it does not define them for Visium HD, Slide-seq, or arbitrary
arrays that reuse the same metadata column names.

## Plotting and object support

`localOutliers()` and `flagVisiumOutliers()` support `SpatialExperiment` and
Seurat adapters. `findArtifacts()`/`localVariance()` require
`SpatialExperiment`. `plotQCmetrics()` maps a metric with an outlier overlay for
one sample; `plotQCpdf()` repeats this by sample. Plotting does not choose a
filtering rule.

## Metrics and integrated score

The package describes standard QC metrics as library size, unique/detected
genes, and mitochondrial percentage. It calculates local z-scores, local
variance residuals, and boolean flags. The inspected source provides **no
QScore-like integrated quality score**. This Skill must not create one.

## Capability and failure policy

Run count metrics when valid counts/IDs exist. Run local outliers only for
present finite numeric metrics with coordinates, sample IDs, and more than `k`
observations per sample. Run systematic flags only for a confirmed standard
10x Visium platform with array row/column; otherwise skip that function.
Mitochondrial functions require measured mitochondrial annotations; absence is
not a zero measurement. Regional artifacts additionally require positive
mitochondrial signal, one sample per call, verified shape, and enough spots for
the largest neighborhood. Record unmet inputs as `skipped` and unexpected
optional-call errors as `failed`, preserving all completed results. Corrupt
counts, count/metadata shape mismatch, and invalid observation IDs are fatal.

## Python fallback mapping

`scripts/spotsweeper_fallback.py` preserves sample-specific processing and the
equations above while replacing all-pairs distances with batched `cKDTree`
queries. It emits explicitly suffixed fallback columns. Local z-score flags are
usable with engine disclosure; local-variance and artifact outputs remain
provisional diagnostics and must not be the sole final filtering condition.
Routine user QC does not perform qualification comparisons. Read
`fallback-validation.md` for current use limits and dependency requirements.
