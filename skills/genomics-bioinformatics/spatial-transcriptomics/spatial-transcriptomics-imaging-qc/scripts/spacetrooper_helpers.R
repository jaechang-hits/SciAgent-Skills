# SpaceTrooper shared helpers for spatial-transcriptomics-imaging-qc.
# Usage: source(".../scripts/spacetrooper_helpers.R") after verifying the
# SpaceTrooper namespace and before choosing the basic or D1-approved polygon
# branch. Bioconductor accessors are namespace-qualified below.

record_engine_status <- function(engine, fun, input_status, execution_status,
                                 reason="", parameters="") {
  clean <- function(x) gsub("[\t\r\n]+", " ", as.character(x))
  row <- data.frame(engine=engine, function_name=fun,
    package_version=if (requireNamespace(engine, quietly=TRUE))
      as.character(packageVersion(engine)) else "",
    input_status=input_status, execution_status=execution_status,
    parameters=clean(parameters), reason=clean(reason))
  path <- "qc_execution_log.tsv"
  write.table(row, path, sep="\t", quote=FALSE, row.names=FALSE,
    col.names=!file.exists(path), append=file.exists(path))
}

set_metadata_value <- function(x, name, value) {
  current <- S4Vectors::metadata(x)
  current[[name]] <- value
  setter <- getExportedValue("S4Vectors", "metadata<-")
  setter(x, value=current)
}

space_trooper_preflight <- function(x) {
  issues <- character()
  if (!inherits(x, "SpatialExperiment"))
    return(list(ok=FALSE, issues="not a SpatialExperiment"))
  if (!"counts" %in% SummarizedExperiment::assayNames(x))
    issues <- c(issues, "counts assay missing")
  xy <- SpatialExperiment::spatialCoords(x)
  if (nrow(xy) != ncol(x) || ncol(xy) < 2L || any(!is.finite(xy[, 1:2])))
    issues <- c(issues, "finite aligned x/y coordinates missing")
  tech <- S4Vectors::metadata(x)$technology
  supported <- c("10X_Xenium", "Nanostring_CosMx",
                 "Nanostring_CosMx_Protein", "Vizgen_MERFISH")
  if (length(tech) != 1L || !tech %in% supported)
    issues <- c(issues, "unsupported or missing technology metadata")

  cd <- as.data.frame(SummarizedExperiment::colData(x))
  positive <- function(name) {
    if (!name %in% colnames(cd)) return(FALSE)
    value <- suppressWarnings(as.numeric(cd[[name]]))
    any(is.finite(value) & value > 0, na.rm=TRUE)
  }
  has_size <- FALSE
  if (length(tech) == 1L) has_size <- switch(tech,
    "10X_Xenium"=positive("Area_um") || positive("cell_area"),
    "Nanostring_CosMx"=positive("Area"),
    "Nanostring_CosMx_Protein"=positive("Area.um2") || positive("Area_um"),
    "Vizgen_MERFISH"=positive("Area_um") || positive("volume"),
    FALSE)
  if (!has_size) issues <- c(issues, "positive platform size field missing")
  list(ok=length(issues) == 0L, issues=issues)
}

run_supported_qscore <- function(x, seed=1713L) {
  exports <- getNamespaceExports("SpaceTrooper")
  has_q <- "computeQScore" %in% exports
  has_qc <- "computeQCScore" %in% exports
  q_has_spe <- has_q && "spe" %in%
    names(formals(getExportedValue("SpaceTrooper", "computeQScore")))
  qc_has_spe <- has_qc && "spe" %in%
    names(formals(getExportedValue("SpaceTrooper", "computeQCScore")))
  q_fun <- if (q_has_spe) "computeQScore" else
    if (qc_has_spe) "computeQCScore" else NA_character_
  if (is.na(q_fun)) {
    record_engine_status("SpaceTrooper", "QScore", "api_incompatible",
      "not_run", "no supported QScore function exposes spe")
    return(list(spe=x, usable=FALSE, score_col=NA_character_))
  }

  cd <- as.data.frame(SummarizedExperiment::colData(x))
  signal_ok <- "log2SignalDensity" %in% colnames(cd) &&
    any(is.finite(suppressWarnings(as.numeric(cd$log2SignalDensity))))
  total_ok <- "total" %in% colnames(cd)
  if (!signal_ok || !total_ok) {
    reason <- paste(c(if (!signal_ok) "finite log2SignalDensity missing",
      if (!total_ok) "total missing"), collapse="; ")
    record_engine_status("SpaceTrooper", q_fun, "input_incompatible",
      "not_run", reason)
    return(list(spe=x, usable=FALSE, score_col=NA_character_))
  }

  keep <- is.finite(suppressWarnings(as.numeric(x$total))) & x$total > 0
  if (!any(keep)) {
    record_engine_status("SpaceTrooper", q_fun, "input_incompatible",
      "not_run", "no positive-count cells for QScore training")
    return(list(spe=x, usable=FALSE, score_col=NA_character_))
  }
  q_input <- x[, keep]
  if ("cell_id" %in% colnames(SummarizedExperiment::colData(q_input)))
    q_input$cell_id <- as.character(q_input$cell_id)

  q_impl <- getExportedValue("SpaceTrooper", q_fun)
  q_formals <- names(formals(q_impl))
  q_args <- list(spe=q_input)
  if ("verbose" %in% q_formals) q_args$verbose <- TRUE
  if ("modelFormula" %in% q_formals) q_args$modelFormula <- NULL
  set.seed(seed)
  result <- tryCatch(list(value=do.call(q_impl, q_args), error=NULL),
    error=function(e) list(value=NULL, error=conditionMessage(e)))
  if (!is.null(result$error)) {
    record_engine_status("SpaceTrooper", q_fun, "compatible",
      "execution_failed", result$error, paste0("seed=", seed))
    return(list(spe=x, usable=FALSE, score_col=NA_character_))
  }

  score_col <- intersect(c("QScore", "QC_score"),
    colnames(SummarizedExperiment::colData(result$value)))[1]
  if (is.na(score_col)) {
    record_engine_status("SpaceTrooper", q_fun, "compatible",
      "execution_failed", "no supported score column returned")
    return(list(spe=x, usable=FALSE, score_col=NA_character_))
  }
  stopifnot(all(colnames(result$value) %in% colnames(x)))
  x[[score_col]] <- NA_real_
  x[[score_col]][match(colnames(result$value), colnames(x))] <-
    suppressWarnings(as.numeric(result$value[[score_col]]))

  model_name <- intersect(c("QScore_model", "QCScore_model"),
    names(S4Vectors::metadata(result$value)))[1]
  model_info <- if (!is.na(model_name))
    S4Vectors::metadata(result$value)[[model_name]] else list()
  model_formula <- if (!is.null(model_info$model_formula))
    paste(model_info$model_formula, collapse=" ") else "package default; not exposed"
  model_metrics <- if (!is.null(model_info$formula_variables))
    paste(as.character(model_info$formula_variables), collapse=",") else "not exposed"
  best_lambda <- if (!is.null(model_info$bestLambda))
    paste(model_info$bestLambda, collapse=",") else "not exposed"
  if (!is.na(model_name)) x <- set_metadata_value(x, model_name, model_info)
  usable <- any(is.finite(suppressWarnings(as.numeric(x[[score_col]]))))
  qscore_execution <- list(function_name=q_fun,
    package_version=as.character(packageVersion("SpaceTrooper")),
    score_column=score_col, seed=seed, model_formula=model_formula,
    model_metrics=model_metrics, best_lambda=best_lambda,
    polygon_required=FALSE)
  x <- set_metadata_value(x, "qscore_execution", qscore_execution)
  record_engine_status("SpaceTrooper", q_fun, "compatible", "executed",
    reason=if (usable) "" else "no finite score returned",
    parameters=paste0("seed=", seed, "; score_column=", score_col,
      "; model_formula=", model_formula, "; model_metrics=", model_metrics,
      "; bestLambda=", best_lambda))
  list(spe=x, usable=usable, score_col=score_col)
}

export_spatial_qc <- function(x, baseline_ids=NULL,
                              path="qc_metrics_from_r.tsv") {
  matched <- as.data.frame(SummarizedExperiment::colData(x))
  atomic_columns <- vapply(matched, function(value)
    is.atomic(value) && is.null(dim(value)), logical(1))
  matched <- matched[, atomic_columns, drop=FALSE]
  matched$observation_id <- as.character(colnames(x))
  matched <- matched[, c("observation_id",
    setdiff(colnames(matched), "observation_id")), drop=FALSE]
  stopifnot(!anyDuplicated(matched$observation_id))

  if (is.null(baseline_ids)) {
    out <- matched
  } else {
    baseline_ids <- as.character(baseline_ids)
    stopifnot(!anyDuplicated(baseline_ids),
              all(matched$observation_id %in% baseline_ids))
    index <- match(baseline_ids, matched$observation_id)
    out <- matched[index, , drop=FALSE]
    out$observation_id <- baseline_ids
    out$polygon_matched <- !is.na(index)
    out$polygon_unmatched <- is.na(index)
  }
  stopifnot(!anyDuplicated(out$observation_id),
            identical(out$observation_id,
              if (is.null(baseline_ids)) as.character(colnames(x)) else baseline_ids))
  write.table(out, path, sep="\t", quote=FALSE, row.names=FALSE, na="")
  invisible(out)
}
