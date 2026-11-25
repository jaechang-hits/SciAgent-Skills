#!/usr/bin/env python3
"""Sparse Python fallback for the SpaceTrooper QC functions used by this skill.

Derived from SpaceTrooper 1.3.3, commit
95265069ca8de5eeb03526f29f8debae9dde4d13. The inspected functions are
spatialPerCellQC(), computeSpatialOutlier(), computeOutliersQScore(),
checkOutliers(), computeTrainDF(), getModelFormula(), and computeQScore().
Copyright (c) 2025 SpaceTrooper authors, MIT License.

This is an independent Python adaptation, not SpaceTrooper. It never reads the
development reference repository at runtime. Its score is named
QScore_fallback_python and is never promoted to official QScore. It is not
eligible for cutoff recommendation or filtering. Development qualification and
an explicit runtime-policy update are required before that status may change;
routine user QC must not perform the qualification comparison.

Usage: python spacetrooper_fallback.py --counts-npz counts.npz --metadata
cells.tsv --features features.csv --technology 10X_Xenium --output qc.tsv
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

try:
    from scipy import sparse
    from scipy.optimize import minimize
except ImportError as exc:  # pragma: no cover - reported by CLI in minimal envs
    raise SystemExit("spacetrooper_fallback.py requires scipy") from exc


CONTROL_PREFIXES = (
    "NegPrb", "Negative", "SystemControl", "Ms IgG1", "Rb IgG", "BLANK_",
    "NegControlProbe", "NegControlCodeword", "UnassignedCodeword", "Blank",
)
SUPPORTED_QSCORE_METRICS = (
    "log2SignalDensity", "Area_um", "log2AspectRatio", "log2Ctrl_total_ratio",
)
COSMX = {"Nanostring_CosMx", "Nanostring_CosMx_Protein"}
ENGINE = "SpaceTrooper-fallback-python"


def _finite_float(values: pd.Series | np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)


def _normalize_id_column(frame: pd.DataFrame, column: str = "cell_id",
                         context: str = "metadata", unique: bool = True) -> pd.DataFrame:
    """Normalize identifiers without silently accepting missing/colliding IDs."""
    if column not in frame:
        raise ValueError(f"{context} requires {column}")
    if frame[column].isna().any():
        raise ValueError(f"{context} {column} must not contain missing values")
    identifiers = frame[column].astype(str)
    if identifiers.eq("").any():
        raise ValueError(f"{context} {column} must not contain empty values")
    if unique and identifiers.duplicated().any():
        raise ValueError(f"{context} {column} must be unique")
    out = frame.copy()
    out[column] = identifiers
    return out


def _row_summaries(matrix, feature_mask: np.ndarray | None = None,
                   chunk_size: int = 100_000) -> tuple[np.ndarray, np.ndarray]:
    """Return row sums/detected without densifying a full backed matrix."""
    n = int(matrix.shape[0])
    sums = np.empty(n, dtype=float)
    detected = np.empty(n, dtype=np.int64)
    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        block = matrix[start:stop]
        if feature_mask is not None:
            block = block[:, feature_mask]
        if sparse.issparse(block):
            # getnnz counts explicitly stored zeros. Canonicalize a chunk and
            # remove those entries without ever materializing a dense matrix.
            block = block.tocsr(copy=True)
            block.sum_duplicates()
            sums[start:stop] = np.asarray(block.sum(axis=1)).ravel()
            block.eliminate_zeros()
            detected[start:stop] = np.diff(block.indptr)
        else:
            block = np.asarray(block)
            sums[start:stop] = np.sum(block, axis=1)
            detected[start:stop] = np.count_nonzero(block, axis=1)
    return sums, detected


def compute_basic_metrics(counts, metadata: pd.DataFrame,
                          feature_names: Sequence[str], technology: str,
                          micron_conv_fact: float = 0.12,
                          chunk_size: int = 100_000,
                          feature_status: list[dict] | None = None) -> pd.DataFrame:
    """Reproduce spatialPerCellQC metrics for cells x features input."""
    if counts.shape != (len(metadata), len(feature_names)):
        raise ValueError("counts must be cells x features and align with metadata")
    if sparse.issparse(counts):
        if not np.all(np.isfinite(counts.data)) or np.any(counts.data < 0):
            raise ValueError("count matrix contains non-finite or negative values")
    elif isinstance(counts, np.ndarray):
        if not np.all(np.isfinite(counts)) or np.any(counts < 0):
            raise ValueError("count matrix contains non-finite or negative values")
    out = metadata.copy()
    if "cell_id" not in out:
        out["cell_id"] = out.index.astype(str)
    out = _normalize_id_column(out)

    features = np.asarray(feature_names, dtype=str)
    control_mask = np.zeros(len(features), dtype=bool)
    # SpaceTrooper creates one subset per prefix; overlapping prefixes are
    # intentionally accumulated more than once. Preserve that behavior.
    total_sum, total_detected = _row_summaries(counts, chunk_size=chunk_size)
    control_sum = np.zeros(len(out), dtype=float)
    control_detected = np.zeros(len(out), dtype=np.int64)
    for prefix in CONTROL_PREFIXES:
        mask = np.char.startswith(features, prefix)
        if np.any(mask):
            s, d = _row_summaries(counts, mask, chunk_size)
            control_sum += s
            control_detected += d
            control_mask |= mask

    out["sum"] = total_sum
    out["detected"] = total_detected
    if "total" not in out:
        out["total"] = total_sum
    if feature_status is not None:
        feature_status.append({"feature": "basic_count_metrics", "status": "completed"})
    if np.any(control_mask):
        out["control_sum"] = control_sum
        out["control_detected"] = control_detected
        out["target_sum"] = out["sum"].to_numpy() - control_sum
        out["target_detected"] = out["detected"].to_numpy() - control_detected
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = control_sum / _finite_float(out["total"])
        # A measured zero stays zero. A zero total is not calculable and stays NA.
        ratio[~np.isfinite(ratio)] = np.nan
        out["ctrl_total_ratio"] = ratio
        out["log2Ctrl_total_ratio"] = np.log2(ratio + 0.0001)
        if feature_status is not None:
            feature_status.append({"feature": "negative_control_metrics", "status": "completed"})
    elif feature_status is not None:
        feature_status.append({
            "feature": "negative_control_metrics", "status": "skipped",
            "reason": "no recognized negative-control features were measured",
        })

    if technology == "Nanostring_CosMx_Protein" and "Area.um2" in out:
        out = out.rename(columns={"Area.um2": "Area_um"})
    if technology in COSMX and "Area_um" not in out:
        if "Area" in out:
            out["Area_um"] = _finite_float(out["Area"]) * micron_conv_fact ** 2
    if technology == "10X_Xenium" and "Area_um" not in out:
        if "cell_area" in out:
            out["Area_um"] = _finite_float(out["cell_area"])
    if technology == "Vizgen_MERFISH" and "Area_um" not in out:
        if "volume" in out:
            out["Area_um"] = _finite_float(out["volume"])
    if "AspectRatio" in out:
        with np.errstate(divide="ignore", invalid="ignore"):
            out["log2AspectRatio"] = np.log2(_finite_float(out["AspectRatio"]))
    if "Area_um" in out or technology == "Nanostring_CosMx_Protein":
        with np.errstate(divide="ignore", invalid="ignore"):
            density = (_finite_float(out["total"])
                       if technology == "Nanostring_CosMx_Protein"
                       else _finite_float(out["sum"]) / _finite_float(out["Area_um"]))
            out["SignalDensity"] = density
            out["log2SignalDensity"] = np.log2(density)
        if feature_status is not None:
            feature_status.append({"feature": "signal_density", "status": "completed"})
    elif feature_status is not None:
        feature_status.append({
            "feature": "signal_density", "status": "skipped",
            "reason": "cell area/volume required by the platform is unavailable",
        })
    return out


def polygon_metrics(vertices: pd.DataFrame) -> pd.DataFrame:
    """Planar shoelace area and bounding-box aspect ratio after D1 approval."""
    required = {"cell_id", "x", "y"}
    if not required.issubset(vertices):
        raise ValueError("polygon vertices require cell_id, x, and y")
    work = _normalize_id_column(vertices, context="polygon vertices", unique=False)
    if "component_id" not in work:
        work["component_id"] = "1"
    elif work["component_id"].isna().any():
        raise ValueError("polygon component_id must not contain missing values")
    else:
        work["component_id"] = work["component_id"].astype(str)
    pieces = []
    for (cell_id, component), frame in work.groupby(["cell_id", "component_id"], sort=False):
        x = _finite_float(frame["x"])
        y = _finite_float(frame["y"])
        if len(x) < 3 or not np.all(np.isfinite(np.r_[x, y])):
            pieces.append((cell_id, component, np.nan, np.nan, np.nan, np.nan, np.nan))
            continue
        area = abs(np.sum(x * np.roll(y, -1) - y * np.roll(x, -1))) / 2
        pieces.append((cell_id, component, area, x.min(), x.max(), y.min(), y.max()))
    table = pd.DataFrame(pieces, columns=["cell_id", "component_id", "area", "xmin", "xmax", "ymin", "ymax"])
    rows = []
    for cell_id, frame in table.groupby("cell_id", sort=False):
        multi = len(frame) > 1
        width = frame["xmax"].max() - frame["xmin"].min()
        height = frame["ymax"].max() - frame["ymin"].min()
        aspect = np.nan if multi or not np.isfinite(height) or height == 0 else width / height
        rows.append((cell_id, frame["area"].sum(min_count=1), multi, len(frame), aspect))
    return pd.DataFrame(rows, columns=["cell_id", "polygon_area", "polygon_is_multi", "polygon_multi_n", "AspectRatio"])


def skewness_type3(values: Iterable[float]) -> float:
    """e1071::skewness(..., type=3), its default."""
    x = np.asarray(list(values), dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return np.nan
    centered = x - x.mean()
    m2 = np.mean(centered ** 2)
    if m2 == 0:
        return np.nan
    g1 = np.mean(centered ** 3) / m2 ** 1.5
    return g1 * ((n - 1) / n) ** 1.5


def mad_outliers(values: np.ndarray, direction: str = "both") -> dict:
    """Unbatched scuttle default: median +/- 3 scaled MAD."""
    x = np.asarray(values, dtype=float)
    finite = x[np.isfinite(x)]
    center = np.median(finite)
    spread = 1.4826 * np.median(np.abs(finite - center))
    thresholds = np.array([center - 3 * spread, center + 3 * spread])
    labels = np.full(len(x), "NO", dtype=object)
    if direction in {"both", "lower"}:
        labels[np.isfinite(x) & (x < thresholds[0])] = "LOW"
    if direction in {"both", "higher"}:
        labels[np.isfinite(x) & (x > thresholds[1])] = "HIGH"
    return {"labels": labels, "thresholds": thresholds, "method": "sc"}


def medcouple_python(values: np.ndarray, max_points: int = 2000) -> tuple[float, bool]:
    """Medcouple kernel median with deterministic quantile subsampling.

    The full kernel is exact for at most max_points finite values. Larger data
    use evenly spaced order statistics to bound memory; this is the principal
    adjusted-boxplot difference from robustbase::mc.
    """
    x = np.sort(np.asarray(values, dtype=float))
    x = x[np.isfinite(x)]
    approximate = len(x) > max_points
    if approximate:
        x = x[np.linspace(0, len(x) - 1, max_points).round().astype(int)]
    median = float(np.median(x))
    lower = median - x[x <= median]
    upper = x[x >= median] - median
    # h = (upper distance - lower distance) / their sum. Store only the
    # bounded/subsampled kernel; no object grows with the original cell count.
    numerator = upper[:, None] - lower[None, :]
    denominator = upper[:, None] + lower[None, :]
    kernel = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator != 0)
    return float(np.median(kernel)), approximate


def adjusted_boxplot_outliers(values: np.ndarray) -> dict:
    """robustbase adjusted-boxplot fence equations with Python medcouple."""
    x = np.asarray(values, dtype=float)
    finite = x[np.isfinite(x)]
    mc, approximate = medcouple_python(finite)
    if mc <= -0.6 or mc >= 0.6:
        raise RuntimeError(f"medcouple {mc:.6g} outside SpaceTrooper interval (-0.6, 0.6)")
    q1, q3 = np.quantile(finite, [0.25, 0.75])
    iqr = q3 - q1
    if mc >= 0:
        fences = np.array([q1 - 1.5 * math.exp(-4 * mc) * iqr,
                           q3 + 1.5 * math.exp(3 * mc) * iqr])
    else:
        fences = np.array([q1 - 1.5 * math.exp(-3 * mc) * iqr,
                           q3 + 1.5 * math.exp(4 * mc) * iqr])
    labels = np.full(len(x), "NO", dtype=object)
    labels[np.isfinite(x) & (x < fences[0])] = "LOW"
    labels[np.isfinite(x) & (x > fences[1])] = "HIGH"
    return {"labels": labels, "thresholds": fences, "method": "mc",
            "medcouple": mc, "medcouple_approximate": approximate}


def outlier_labels(values: np.ndarray) -> dict:
    skew = skewness_type3(values)
    if np.isfinite(skew) and -1 < skew < 1:
        return mad_outliers(values)
    return adjusted_boxplot_outliers(values)


def add_individual_outliers(metadata: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    out = metadata.copy()
    details: list[dict] = []
    for metric in (m for m in SUPPORTED_QSCORE_METRICS if m in out):
        finite = np.isfinite(_finite_float(out[metric]))
        if finite.sum() < 3:
            details.append({"metric": metric, "status": "skipped", "reason": "fewer than three finite values"})
            continue
        try:
            result = outlier_labels(_finite_float(out.loc[finite, metric]))
        except Exception as exc:
            details.append({"metric": metric, "status": "failed", "reason": str(exc)})
            continue
        column = f"{metric}_outlier_{result['method']}"
        labels = np.full(len(out), None, dtype=object)
        labels[np.flatnonzero(finite)] = result["labels"]
        out[column] = labels
        details.append({"metric": metric, "status": "completed", "method": result["method"],
                        "lower": float(result["thresholds"][0]), "higher": float(result["thresholds"][1]), "reason": ""})
    return out, details


def _prepare_qscore_outliers(metadata: pd.DataFrame, technology: str) -> tuple[pd.DataFrame, dict[str, str], dict]:
    out = metadata.copy()
    mapping: dict[str, str] = {}
    details = {}
    for metric in (m for m in SUPPORTED_QSCORE_METRICS if m in out):
        values = _finite_float(out[metric])
        eligible = np.isfinite(values)
        zero = np.zeros(len(out), dtype=bool)
        if metric == "log2SignalDensity":
            eligible &= _finite_float(out["total"]) > 0
            zero = _finite_float(out["total"]) == 0
        elif metric == "log2Ctrl_total_ratio":
            eligible &= _finite_float(out["ctrl_total_ratio"]) != 0
            zero = _finite_float(out["ctrl_total_ratio"]) == 0
        if eligible.sum() < 3:
            continue
        result = outlier_labels(values[eligible])
        lower, higher = map(float, result["thresholds"])
        if metric == "log2SignalDensity" and lower < np.nanmin(values[eligible]):
            lower = float(np.nanquantile(values, 0.01))
        labels = np.full(len(out), "NO", dtype=object)
        labels[(~zero) & np.isfinite(values) & (values < lower)] = "LOW"
        labels[(~zero) & np.isfinite(values) & (values > higher)] = "HIGH"
        suffix = "train" if metric in {"log2SignalDensity", "log2Ctrl_total_ratio"} else result["method"]
        column = f"{metric}_outlier_{suffix}"
        out[column] = labels
        mapping[metric] = column
        details[metric] = {"method": result["method"], "lower": lower, "higher": higher}

    if "log2SignalDensity" not in mapping:
        raise RuntimeError("log2SignalDensity outliers could not be calculated")
    minimum = len(out) * 0.001
    if np.sum(out[mapping["log2SignalDensity"]] == "LOW") < minimum:
        raise RuntimeError("not enough low log2SignalDensity outliers")
    if "Area_um" in mapping and np.sum(out[mapping["Area_um"]] == "HIGH") < minimum:
        mapping.pop("Area_um")
    if "log2Ctrl_total_ratio" in mapping and np.sum(out[mapping["log2Ctrl_total_ratio"]] == "HIGH") < minimum:
        mapping.pop("log2Ctrl_total_ratio")
    if "log2AspectRatio" in mapping:
        labels = out[mapping["log2AspectRatio"]]
        low = np.sum(labels == "LOW")
        high = np.sum(labels == "HIGH")
        if technology not in COSMX or (low < minimum and high < minimum):
            mapping.pop("log2AspectRatio")
    return out, mapping, details


def _training_frame(metadata: pd.DataFrame, mapping: Mapping[str, str], technology: str,
                    seed: int) -> pd.DataFrame:
    bad = np.zeros(len(metadata), dtype=bool)
    good = np.zeros(len(metadata), dtype=bool)
    config = {
        "log2SignalDensity": ("LOW", (0.90, 0.99)),
        "Area_um": ("HIGH", (0.25, 0.75)),
        "log2Ctrl_total_ratio": ("HIGH", None),
    }
    for metric in config.keys() & mapping.keys():
        bad_label, band = config[metric]
        bad |= metadata[mapping[metric]].to_numpy() == bad_label
        if band is not None:
            lo, hi = np.nanquantile(_finite_float(metadata[metric]), band)
            values = _finite_float(metadata[metric])
            good |= (values > lo) & (values < hi)
    if technology in COSMX and "log2AspectRatio" in mapping:
        if "dist_border" not in metadata:
            raise RuntimeError("dist_border is required for CosMx QScore")
        labels = metadata[mapping["log2AspectRatio"]].to_numpy()
        border = _finite_float(metadata["dist_border"])
        bad |= np.isin(labels, ["LOW", "HIGH"]) & (border < 50)
        lo, hi = np.nanquantile(_finite_float(metadata["log2AspectRatio"]), [0.25, 0.75])
        aspect = _finite_float(metadata["log2AspectRatio"])
        good |= (aspect > lo) & (aspect < hi) & (border > 50)
    good &= ~bad
    bad_idx = np.flatnonzero(bad)
    good_idx = np.flatnonzero(good)
    if len(bad_idx) == 0 or len(good_idx) <= len(bad_idx):
        raise RuntimeError("insufficient good/bad examples for balanced QScore training")
    rng = np.random.default_rng(seed)
    selected_good = rng.choice(good_idx, size=len(bad_idx), replace=False)
    train = metadata.iloc[np.r_[bad_idx, selected_good]].copy()
    train["QScore_train"] = np.r_[np.zeros(len(bad_idx)), np.ones(len(bad_idx))]
    return train


def _design_matrix(frame: pd.DataFrame, metrics: Sequence[str], technology: str) -> tuple[np.ndarray, list[str]]:
    base = []
    names = []
    for metric in metrics:
        if metric == "log2AspectRatio":
            values = np.abs(_finite_float(frame[metric])) * (_finite_float(frame["dist_border"]) < 50)
            names.append("I(abs(log2AspectRatio)*as.numeric(dist_border<50))")
        else:
            values = _finite_float(frame[metric])
            names.append(metric)
        base.append(values)
    columns = list(base)
    column_names = list(names)
    for i in range(len(base)):
        for j in range(i + 1, len(base)):
            columns.append(base[i] * base[j])
            column_names.append(f"{names[i]}:{names[j]}")
    return np.column_stack(columns), column_names


def _fit_ridge(x: np.ndarray, y: np.ndarray, penalty: float, start=None):
    n, p = x.shape
    if start is None:
        start = np.zeros(p + 1)
        prevalence = np.clip(y.mean(), 1e-6, 1 - 1e-6)
        start[0] = math.log(prevalence / (1 - prevalence))

    def objective(theta):
        eta = theta[0] + x @ theta[1:]
        loss = np.mean(np.logaddexp(0, eta) - y * eta)
        value = loss + 0.5 * penalty * np.dot(theta[1:], theta[1:])
        prob = 1 / (1 + np.exp(-np.clip(eta, -40, 40)))
        error = prob - y
        grad = np.r_[error.mean(), x.T @ error / n + penalty * theta[1:]]
        return value, grad

    result = minimize(objective, start, method="L-BFGS-B", jac=True,
                      options={"maxiter": 1000, "ftol": 1e-10})
    if not result.success:
        raise RuntimeError(f"ridge fit failed: {result.message}")
    return result.x


def _stratified_folds(y: np.ndarray, folds: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    assigned = np.empty(len(y), dtype=int)
    for label in (0, 1):
        idx = np.flatnonzero(y == label)
        rng.shuffle(idx)
        assigned[idx] = np.arange(len(idx)) % folds
    return assigned


def _ridge_cv(x: np.ndarray, y: np.ndarray, seed: int,
              penalties: np.ndarray | None = None) -> tuple[np.ndarray, float, dict]:
    """Ridge-binomial CV analogue; glmnet's optimiser/lambda path differs."""
    class_count = int(min(np.sum(y == 0), np.sum(y == 1)))
    folds = min(10, class_count)
    if folds < 3:
        raise RuntimeError("at least three examples per class are required for CV")
    if penalties is None:
        penalties = np.logspace(3, -6, 60)
    fold_id = _stratified_folds(y, folds, seed)
    losses = np.zeros(len(penalties))
    for fold in range(folds):
        train = fold_id != fold
        test = ~train
        mean = x[train].mean(axis=0)
        scale_values = x[train].std(axis=0, ddof=0)
        scale_values[scale_values == 0] = 1
        xt = (x[train] - mean) / scale_values
        xv = (x[test] - mean) / scale_values
        warm = None
        for index, penalty in enumerate(penalties):
            warm = _fit_ridge(xt, y[train], float(penalty), warm)
            eta = warm[0] + xv @ warm[1:]
            losses[index] += np.mean(np.logaddexp(0, eta) - y[test] * eta) / folds
    best_index = int(np.argmin(losses))
    best = float(penalties[best_index])
    mean = x.mean(axis=0)
    scale_values = x.std(axis=0, ddof=0)
    scale_values[scale_values == 0] = 1
    theta = _fit_ridge((x - mean) / scale_values, y, best)
    model = {"intercept": float(theta[0]), "coef_standardized": theta[1:].tolist(),
             "mean": mean.tolist(), "scale": scale_values.tolist()}
    return theta, best, {"cv_loss": losses.tolist(), "penalties": penalties.tolist(), "model": model}


def compute_qscore_fallback(metadata: pd.DataFrame, technology: str,
                            seed: int = 1713) -> tuple[pd.DataFrame, dict]:
    """Compute a distinct, validation-gated Python QScore analogue."""
    out = metadata.copy()
    score_column = "QScore_fallback_python"
    out[score_column] = np.nan
    status = {"engine": ENGINE, "score_name": score_column, "qscore_usable": False,
              "validation_state": "unvalidated", "seed": seed}
    try:
        positive = np.isfinite(_finite_float(out["total"])) & (_finite_float(out["total"]) > 0)
        work = out.loc[positive].copy()
        work, mapping, outlier_details = _prepare_qscore_outliers(work, technology)
        train = _training_frame(work, mapping, technology, seed)
        metrics = list(mapping)
        train_x, term_names = _design_matrix(train, metrics, technology)
        train_y = _finite_float(train["QScore_train"])
        complete_train = np.all(np.isfinite(train_x), axis=1) & np.isfinite(train_y)
        if len(np.unique(train_y[complete_train])) != 2:
            raise RuntimeError("complete training cases do not contain both classes")
        theta, best_penalty, fit = _ridge_cv(train_x[complete_train], train_y[complete_train], seed)
        full_x, _ = _design_matrix(work, metrics, technology)
        complete = np.all(np.isfinite(full_x), axis=1)
        model = fit["model"]
        standardized = (full_x[complete] - np.asarray(model["mean"])) / np.asarray(model["scale"])
        eta = theta[0] + standardized @ theta[1:]
        score = 1 / (1 + np.exp(-np.clip(eta, -40, 40)))
        out.loc[work.index[complete], score_column] = score
        status.update({"candidate_computed": True, "reason": "development qualification required",
                       "model_metrics": metrics, "model_terms": term_names,
                       "best_penalty_python": best_penalty,
                       "training_cells": int(complete_train.sum()),
                       "outlier_details": outlier_details,
                       "implementation_difference": "scipy ridge optimiser/CV path and NumPy RNG differ from glmnet/R"})
    except Exception as exc:
        status.update({"candidate_computed": False, "validation_state": "unavailable", "reason": str(exc)})
    return out, status


def _read_table(path: str, string_columns: Sequence[str] = ()) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(p)
    dtype = {column: "string" for column in string_columns}
    return pd.read_csv(
        p,
        sep="\t" if p.suffix.lower() in {".tsv", ".txt"} else ",",
        dtype=dtype or None,
    )


def _read_feature_names(path: str) -> list[str]:
    table = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    if table.shape[1] != 1 or table[0].eq("").any():
        raise ValueError("features must contain exactly one non-empty name per row")
    return table[0].tolist()


def _write_table(frame: pd.DataFrame, path: str) -> None:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        frame.to_parquet(p, index=False)
    else:
        frame.to_csv(p, sep="\t" if p.suffix.lower() in {".tsv", ".txt"} else ",", index=False)


def load_input(args):
    if args.h5ad:
        try:
            import anndata as ad
        except ImportError as exc:
            raise RuntimeError("anndata is required only for --h5ad input") from exc
        adata = ad.read_h5ad(args.h5ad, backed="r")
        metadata = adata.obs.copy()
        if "cell_id" not in metadata:
            metadata.insert(0, "cell_id", adata.obs_names.astype(str))
        metadata = metadata.reset_index(drop=True)
        return adata.X, metadata, adata.var_names.astype(str).tolist(), adata
    if not (args.counts_npz and args.metadata and args.features):
        raise ValueError("use --h5ad or all of --counts-npz, --metadata, --features")
    counts = sparse.load_npz(args.counts_npz)
    metadata = _read_table(args.metadata, ("cell_id",))
    features = _read_feature_names(args.features)
    return counts, metadata, features, None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--h5ad")
    source.add_argument("--counts-npz")
    parser.add_argument("--metadata")
    parser.add_argument("--features")
    parser.add_argument("--technology", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--polygon-vertices", help="Pass only after D1 approval")
    parser.add_argument("--micron-conv-fact", type=float, default=0.12)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=1713)
    parser.add_argument("--skip-qscore", action="store_true")
    args = parser.parse_args(argv)

    counts, metadata, features, handle = load_input(args)
    try:
        functions = []
        feature_status: list[dict] = []
        if "cell_id" not in metadata:
            metadata["cell_id"] = metadata.index.astype(str)
        metadata = _normalize_id_column(metadata)
        if args.polygon_vertices:
            try:
                poly = polygon_metrics(_read_table(
                    args.polygon_vertices, ("cell_id", "component_id")
                ))
                metadata = metadata.merge(poly, on="cell_id", how="left", sort=False)
                functions.append("polygonMetrics:fallback_python")
                feature_status.append({"feature": "polygon_qc", "status": "completed"})
            except Exception as exc:
                feature_status.append({"feature": "polygon_qc", "status": "failed",
                                       "reason": str(exc)})
        else:
            feature_status.append({"feature": "polygon_qc", "status": "skipped",
                                   "reason": "polygon input was unavailable or D1 was not approved"})
        metrics = compute_basic_metrics(counts, metadata, features, args.technology,
                                        args.micron_conv_fact, args.chunk_size,
                                        feature_status)
        functions.append("spatialPerCellQC:fallback_python")
        metrics, outlier_status = add_individual_outliers(metrics)
        for item in outlier_status:
            feature_status.append({
                "feature": f"individual_outlier:{item['metric']}",
                "status": item["status"],
                **({"reason": item.get("reason")} if item.get("reason") else {}),
            })
        functions.append("computeSpatialOutlier:fallback_python")
        qscore_status = {"engine": ENGINE, "qscore_usable": False,
                         "validation_state": "not_requested", "reason": "--skip-qscore"}
        if not args.skip_qscore:
            if "log2SignalDensity" not in metrics:
                qscore_status = {"engine": ENGINE, "qscore_usable": False,
                                 "candidate_computed": False,
                                 "validation_state": "unavailable",
                                 "reason": "signal density prerequisites are unavailable"}
                feature_status.append({"feature": "qscore_candidate", "status": "skipped",
                                       "reason": qscore_status["reason"]})
            else:
                metrics, qscore_status = compute_qscore_fallback(metrics, args.technology, args.seed)
                functions.append("computeQScore:fallback_python_candidate")
                feature_status.append({
                    "feature": "qscore_candidate",
                    "status": "completed" if qscore_status.get("candidate_computed") else "failed",
                    "reason": qscore_status.get("reason"),
                })
        else:
            feature_status.append({"feature": "qscore_candidate", "status": "skipped",
                                   "reason": "--skip-qscore"})
        qscore_status["functions"] = functions
        qscore_status["feature_status"] = feature_status
        qscore_status["dependencies"] = {"required": ["numpy", "pandas", "scipy"],
                                           "optional_input_adapter": ["anndata"],
                                           "optional_output_adapter": ["pyarrow_or_fastparquet"]}
        _write_table(metrics, args.output)
        Path(args.output + ".status.json").write_text(json.dumps(qscore_status, indent=2), encoding="utf-8")
        pd.DataFrame(outlier_status).to_csv(args.output + ".outliers.tsv", sep="\t", index=False)
    finally:
        if handle is not None:
            handle.file.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
