# SpotSweeper Execution Details

Read this reference before writing the R execution step. It supplements the
entrypoint with the version-sensitive bridge, engine logging, and plotting
contract. The shared interpretation policy is at
`/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-qc/references/integrated-assessment.md`.

## Observation contract

The `SpatialExperiment` passed to SpotSweeper must have:

- raw counts in `assay(spe, "counts")`;
- unique spot/bin IDs in `colnames(spe)`;
- two finite coordinates in `spatialCoords(spe)` with matching row names;
- `sample_id` for independent slides/sections;
- platform metadata distinguishing Visium from Visium HD;
- selected HD `bin_size_um` when applicable.

Keep off-tissue observations in the preserved source object. Use an explicit
analysis view for tissue observations and record that transition as
`analysis_view`, not filtering.

## Execution status

Use these statuses consistently:

```text
runtime_unavailable, package_missing, dependency_error, api_incompatible,
input_incompatible, execution_failed, executed, not_applicable
```

Log package version, function, actual parameters, input status, execution
status, and exact error/reason to `qc_execution_log.tsv`. A Python or scuttle
fallback is never SpotSweeper execution.

```r
record_engine_status <- function(engine, fun, input_status, execution_status,
                                 reason="", parameters="") {
  clean <- function(x) gsub("[\\t\\r\\n]+", " ", as.character(x))
  row <- data.frame(engine=engine, function_name=fun,
    package_version=if (requireNamespace(engine, quietly=TRUE))
      as.character(packageVersion(engine)) else "",
    input_status=input_status, execution_status=execution_status,
    parameters=clean(parameters), reason=clean(reason))
  path <- "qc_execution_log.tsv"
  write.table(row, path, sep="\t", quote=FALSE, row.names=FALSE,
    col.names=!file.exists(path), append=file.exists(path))
}
```

## Local outliers

Run within each sample, never across unrelated slides. Choose
`n_neighbors < min(table(sample_id))`; reduce it transparently for small groups
and do not run when a group has fewer than three observations.

```r
group_sizes <- table(spe_qc$sample_id)
n_neighbors <- min(36L, as.integer(min(group_sizes)) - 1L)
stopifnot(n_neighbors >= 2L)

spe_qc <- SpotSweeper::localOutliers(
  spe_qc, metric="sum", direction="lower", n_neighbors=n_neighbors,
  samples="sample_id", log=TRUE, cutoff=3, workers=1)
spe_qc <- SpotSweeper::localOutliers(
  spe_qc, metric="detected", direction="lower", n_neighbors=n_neighbors,
  samples="sample_id", log=TRUE, cutoff=3, workers=1)
```

The robust-z cutoff identifies metric-level local outliers. It is not the final
filtering cutoff. Validate distribution, spatial position, biological region,
and agreement with other evidence before proposing an integrated rule.

Save native plots for each sample and metric:

```r
dir.create("qc_package_plots", showWarnings=FALSE)
for (sample_value in unique(as.character(spe_qc$sample_id))) {
  for (metric_name in c("sum", "detected")) {
    outlier_name <- paste0(metric_name, "_outliers")
    p <- SpotSweeper::plotQCmetrics(
      spe_qc, sample_id="sample_id", sample=sample_value,
      metric=metric_name, outliers=outlier_name)
    safe <- gsub("[^A-Za-z0-9_.-]+", "_", sample_value)
    ggplot2::ggsave(file.path("qc_package_plots", paste0(
      "spotsweeper_", safe, "_", metric_name, ".png")),
      p, width=6, height=6, dpi=200)
  }
}
```

## Mitochondrial regional artifacts

Run `findArtifacts()` only when feature annotation proves mitochondrial genes
are measured and both mitochondrial sum and percentage are finite and non-zero.
Panel or FFPE assays without mitochondrial targets make this step
`input_incompatible`, not failed.

```r
can_find_artifacts <- all(c("expr_chrM_ratio", "expr_chrM") %in%
  colnames(colData(spe_qc))) && any(spe_qc$expr_chrM > 0, na.rm=TRUE)
if (can_find_artifacts) {
  spe_qc <- SpotSweeper::findArtifacts(
    spe_qc, mito_percent="expr_chrM_ratio", mito_sum="expr_chrM",
    samples="sample_id", n_order=5, shape="hexagonal", log=TRUE,
    name="artifact", var_output=TRUE)
}
```

Use the actual array geometry. Do not assume a hexagonal grid for irregular HD
bins or another technology.

## Return bridge

Export results by observation ID after all package calls. Enforce complete ID
set equality and reorder to Python before joining.

```r
qc_from_r <- as.data.frame(colData(spe_qc))
qc_from_r$observation_id <- as.character(colnames(spe_qc))
stopifnot(!anyDuplicated(qc_from_r$observation_id))
write.table(qc_from_r, "qc_metrics_from_r.tsv", sep="\t", quote=FALSE,
            row.names=FALSE, na="")
```

```python
qc_from_r = pd.read_csv("qc_metrics_from_r.tsv", sep="\t",
                        dtype={"observation_id": str}).set_index("observation_id")
python_ids = pd.Index(adata.obs_names.astype(str), name="observation_id")
missing = python_ids.difference(qc_from_r.index)
extra = qc_from_r.index.difference(python_ids)
if len(missing) or len(extra):
    raise ValueError(f"Python/R observation mismatch: missing={len(missing)}, extra={len(extra)}")
qc_from_r = qc_from_r.reindex(python_ids)
adata.obs = adata.obs.join(qc_from_r, how="left", validate="one_to_one", rsuffix="_r")
```

## Interpretation handoff

After the return bridge, read and execute the shared integrated-assessment
reference. The SpotSweeper local-outlier columns and artifact result are metric
evidence only. Do not convert them directly to `Exclude candidate`.
