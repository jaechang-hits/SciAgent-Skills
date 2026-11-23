# SpaceTrooper and Polygon Execution Details

Read this reference before writing imaging QC code. Read
`/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-imaging-qc/scripts/spacetrooper_helpers.R`,
copy it unchanged into the analysis workspace, and source it before choosing
the basic or D1-approved branch. The helpers are deliberately defined outside
either branch so Polygon QC cannot skip their definitions.

## Capability inventory

Record each capability as `usable`, `present_unverified`, `absent`, or
`invalid`, with evidence and failure reason:

- raw counts and unique cell IDs;
- finite coordinates aligned to cells;
- platform technology and FOV/sample grouping;
- control-probe annotations;
- positive cell area/volume fields;
- image availability;
- polygon source and ID overlap;
- SpaceTrooper namespace, exports and installed signatures.

Counts plus coordinates support common QC. They do not prove polygon, control,
geometry, image, or QScore capability.

## Loader API compatibility

Inspect installed exports and formals in the step that calls the loader. Try
only documented argument variants and retain the exact successful call. Do not
mark a package available merely because its namespace loaded.

```r
call_first_supported <- function(fun, candidates) {
  formal_names <- names(formals(fun))
  accepts_dots <- "..." %in% formal_names
  errors <- character()
  for (args in candidates) {
    if (!accepts_dots && !all(names(args) %in% formal_names)) next
    result <- tryCatch(list(value=do.call(fun, args), error=NULL),
      error=function(e) list(value=NULL, error=conditionMessage(e)))
    if (is.null(result$error))
      return(list(value=result$value, args=args))
    errors <- c(errors, result$error)
  }
  stop(paste(unique(errors), collapse=" | "))
}

loader <- getExportedValue("SpaceTrooper", "readXeniumSPE")
loaded <- call_first_supported(loader, list(
  list(dataDir=INPUT_DIR, keepPolygons=FALSE,
       polygonsFPattern=POLYGON_PATTERN, addFOVs=FALSE),
  list(dataDir=INPUT_DIR, polygonsFPattern=POLYGON_PATTERN,
       keepPolygons=FALSE),
  list(dataDir=INPUT_DIR, boundariesType=POLYGON_TYPE,
       polygonsFPattern=POLYGON_PATTERN, keepPolygons=FALSE)))
spe <- loaded$value
```

Use the corresponding installed CosMx or MERFISH loader and its observed
documented formals. The initial loader call must keep polygons disabled; the
D1-approved branch attaches the already-probed geometry later.

## Pre-D1 polygon probe

Before D1, use the official reader only to test schema, parseability, non-empty
geometry, unique IDs and overlap. Do not attach polygons, compute boundary
metrics, plot polygons, or flag cells.

| Platform | Reader | Required normalized columns |
|---|---|---|
| Xenium | `readPolygonsXenium()` | `cell_id`, `is_multi`, `multi_n`, geometry |
| CosMx | `readPolygonsCosmx()` | `cell_id`, `is_multi`, `multi_n`, geometry |
| MERFISH | `readPolygonsMerfish()` | `cell_id`, `is_multi`, `multi_n`, geometry |

```r
polygon_probe <- switch(S4Vectors::metadata(spe)$technology,
  "10X_Xenium"=SpaceTrooper::readPolygonsXenium(POLYGON_SOURCE,
    type=POLYGON_TYPE, keepMultiPol=TRUE, verbose=TRUE),
  "Nanostring_CosMx"=SpaceTrooper::readPolygonsCosmx(POLYGON_SOURCE,
    type=POLYGON_TYPE, keepMultiPol=TRUE, verbose=TRUE),
  "Nanostring_CosMx_Protein"=SpaceTrooper::readPolygonsCosmx(POLYGON_SOURCE,
    type=POLYGON_TYPE, keepMultiPol=TRUE, verbose=TRUE),
  "Vizgen_MERFISH"=SpaceTrooper::readPolygonsMerfish(POLYGON_SOURCE,
    type=POLYGON_TYPE, keepMultiPol=TRUE, verbose=TRUE))
polygon_ids <- as.character(polygon_probe$cell_id)
stopifnot(inherits(polygon_probe, "sf"), !anyDuplicated(polygon_ids))
geometry_ok <- any(!sf::st_is_empty(sf::st_geometry(polygon_probe)))
matched_ids <- intersect(colnames(spe), polygon_ids)
polygon_usable <- geometry_ok && length(matched_ids) > 0L
rm(polygon_probe)
```

Ask D1 only when `polygon_usable` is true and report matched count/fraction and
known loss risk. QScore remains independently eligible from existing
SpaceTrooper metrics.

## Basic branch

Run when D1 is declined or not applicable. Preserve `spe`; execute on
`spe_qc <- spe`. Use `rmZeros=FALSE` and record count equality.

```r
st_check <- space_trooper_preflight(spe_qc)
if (!st_check$ok) stop(paste(st_check$issues, collapse="; "))
n_before <- ncol(spe_qc)
spe_qc <- SpaceTrooper::spatialPerCellQC(spe_qc, rmZeros=FALSE)
stopifnot(ncol(spe_qc) == n_before)
spe_qc <- set_metadata_value(spe_qc, "space_trooper_executed", TRUE)
record_engine_status("SpaceTrooper", "spatialPerCellQC", "compatible",
  "executed", parameters="rmZeros=FALSE; basic branch")
```

Then run global robust outliers on available supported metrics:

```r
metrics <- intersect(c("log2SignalDensity", "Area_um", "log2AspectRatio",
  "log2Ctrl_total_ratio"),
  colnames(SummarizedExperiment::colData(spe_qc)))
for (metric in metrics)
  spe_qc <- SpaceTrooper::computeSpatialOutlier(
    spe_qc, computeBy=metric, method="both", scuttleType="both")
```

`computeSpatialOutlier()` is distribution-based, not a local-neighbour test.
`plotCentroids()` maps a result but does not make it local.

## D1-approved integrated polygon branch

This branch replaces the basic imaging branch; do not run both. Preserve the
pre-polygon baseline and attach the already validated `sf` object.

```r
spe_pre_polygon <- spe
ids_before <- as.character(colnames(spe_pre_polygon))
spe_polygon <- addPolygonsToSPE(spe_pre_polygon, polygon_sf,
                                polygonsCol="polygons")
ids_after <- as.character(colnames(spe_polygon))
lost_ids <- setdiff(ids_before, ids_after)
stopifnot(all(ids_after %in% ids_before))
```

Write `qc_polygon_matching_status.csv` with every baseline cell. This is
integration loss, not filtering and not an outlier result.

```r
polygon_status <- data.frame(
  cell_id=ids_before,
  polygon_matched=ids_before %in% ids_after,
  polygon_unmatched=ids_before %in% lost_ids)
write.csv(polygon_status, "qc_polygon_matching_status.csv", row.names=FALSE)
```

Join geometry metrics by `cell_id`, never row position:

```r
polygon_ids <- as.character(polygon_sf$cell_id)
index <- match(ids_after, polygon_ids)
stopifnot(!anyNA(index))
spe_polygon$polygon_valid_after_reader <- sf::st_is_valid(polygon_sf)[index]
spe_polygon$polygon_empty <- sf::st_is_empty(polygon_sf)[index]
spe_polygon$polygon_area <- computeAreaFromPolygons(polygon_sf)[index]
spe_polygon$AspectRatio <- computeAspectRatioFromPolygons(polygon_sf)[index]
spe_polygon$polygon_is_multi <- polygon_sf$is_multi[index]
spe_polygon$polygon_multi_n <- polygon_sf$multi_n[index]
```

Run `spatialPerCellQC(..., rmZeros=FALSE)` once on the matched polygon object,
then robust outliers over supported common and polygon metrics. Save polygon
validity, empty geometry, multipolygon state, area/aspect ratio, matching loss,
package fences and plots. Reader-repaired validity does not prove the original
source geometry was valid.

## QScore after either branch

Call `run_supported_qscore()` after successful SpaceTrooper per-cell metrics.
The helper selects `computeQScore()` or historical `computeQCScore()` by actual
exports and signatures. It requires finite `log2SignalDensity`, `total`, and
positive-count training cells; optional predictors are left to the installed
package model. It keeps zero-count cells with missing scores.

```r
qscore_run <- run_supported_qscore(spe_qc)
spe_qc <- qscore_run$spe
qscore_usable <- qscore_run$usable
qscore_col <- qscore_run$score_col
```

Plot the actual returned score column with `plotMetricHist()` and
`plotCentroids()`. Polygon display is an additional view only if D1-approved
polygons are already attached.

Do not create a low-score flag unless the integrated review recommends and
records an explicit QScore cutoff. Pass that exact cutoff to the installed
compatible flag function with quantile mode disabled when supported. Never
silently use a package default such as `0.5`.

## Full-baseline R/Python bridge

Polygon metrics exist only for matched cells, but the exported table must cover
the complete pre-polygon baseline. Use the helper:

```r
export_spatial_qc(spe_qc,
  baseline_ids=if (exists("ids_before")) ids_before else NULL)
```

In Python, enforce exact ID-set equality, reorder, update existing R-derived
columns with non-missing values, and join only new columns. This supports the
second export after an optional QScore flag without duplicate suffix columns.

```python
qc = pd.read_csv("qc_metrics_from_r.tsv", sep="\t",
                 dtype={"observation_id": str}).set_index("observation_id")
python_ids = pd.Index(adata.obs_names.astype(str), name="observation_id")
missing, extra = python_ids.difference(qc.index), qc.index.difference(python_ids)
if len(missing) or len(extra):
    raise ValueError(f"Python/R observation mismatch: missing={len(missing)}, extra={len(extra)}")
qc = qc.reindex(python_ids)
overlap = adata.obs.columns.intersection(qc.columns)
for column in overlap:
    adata.obs[column] = qc[column].combine_first(adata.obs[column])
new_columns = qc.columns.difference(adata.obs.columns, sort=False)
adata.obs = adata.obs.join(qc[new_columns], how="left", validate="one_to_one")
```

Unmatched cells retain missing polygon/SpaceTrooper-derived fields plus explicit
`polygon_unmatched=True`. Never convert those missing metrics to flags.
