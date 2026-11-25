#!/usr/bin/env python3
"""Scalable Python fallback for the SpotSweeper functions used by this skill.

Derived from SpotSweeper 1.9.3, commit
7e6ebf68c205cf0c102d8ed6b363752d5288d179: localOutliers(),
localVariance(), findArtifacts(), and flagVisiumOutliers(). Copyright (c) 2024
SpotSweeper authors, MIT License.

This adaptation uses scipy.spatial.cKDTree and never forms an N x N distance
matrix. Outputs are explicitly labelled as fallback results.

Usage: python spotsweeper_fallback.py --metadata spot_metrics.tsv --output
qc.tsv --id-column observation_id --x x --y y --sample sample_id
--metrics sum,detected
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

try:
    from scipy.spatial import cKDTree
    from scipy import sparse
except ImportError as exc:  # pragma: no cover
    raise SystemExit("spotsweeper_fallback.py requires scipy") from exc


QNORM_75 = 0.6744897501960817
ENGINE = "SpotSweeper-fallback-python"
SYSTEMATIC_POSITIONS = {(38, 88), (28, 32), (49, 103), (57, 99), (47, 77), (53, 117)}
STANDARD_VISIUM_PLATFORMS = {
    "visium", "10xvisium", "10xgenomicsvisium", "standardvisium",
}


def _normalize_id_column(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in frame:
        raise ValueError(f"metadata requires unique observation ID column {column!r}")
    if frame[column].isna().any():
        raise ValueError("observation IDs must not contain missing values")
    identifiers = frame[column].astype(str)
    if identifiers.eq("").any():
        raise ValueError("observation IDs must not contain empty values")
    if identifiers.duplicated().any():
        raise ValueError("observation IDs must be unique")
    out = frame.copy()
    out[column] = identifiers
    return out


def _row_summaries(matrix, feature_mask: np.ndarray | None = None,
                   chunk_size: int = 100_000) -> tuple[np.ndarray, np.ndarray]:
    n = int(matrix.shape[0])
    sums = np.empty(n, dtype=float)
    detected = np.empty(n, dtype=np.int64)
    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        block = matrix[start:stop]
        if feature_mask is not None:
            block = block[:, feature_mask]
        if sparse.issparse(block):
            # Stored zeros and duplicate entries are not detected features.
            # Work on one sparse chunk, canonicalize, and never densify.
            block = block.tocsr(copy=True)
            block.sum_duplicates()
            sums[start:stop] = np.asarray(block.sum(axis=1)).ravel()
            block.eliminate_zeros()
            detected[start:stop] = np.diff(block.indptr)
        else:
            block = np.asarray(block)
            sums[start:stop] = block.sum(axis=1)
            detected[start:stop] = np.count_nonzero(block, axis=1)
    return sums, detected


def add_count_metrics(counts, metadata: pd.DataFrame, feature_names: Sequence[str],
                      mito_features: set[str] | None = None,
                      mito_sum_name: str = "subsets_Mito_sum",
                      mito_percent_name: str = "subsets_Mito_percent",
                      chunk_size: int = 100_000) -> pd.DataFrame:
    """Sparse scuttle-style sum/detected and explicit mitochondrial subset."""
    if counts.shape != (len(metadata), len(feature_names)):
        raise ValueError("counts must be observations x features and align with metadata")
    if sparse.issparse(counts):
        if not np.all(np.isfinite(counts.data)) or np.any(counts.data < 0):
            raise ValueError("count matrix contains non-finite or negative values")
    elif isinstance(counts, np.ndarray):
        if not np.all(np.isfinite(counts)) or np.any(counts < 0):
            raise ValueError("count matrix contains non-finite or negative values")
    out = metadata.copy()
    out["sum"], out["detected"] = _row_summaries(counts, chunk_size=chunk_size)
    if mito_features is not None:
        mask = np.isin(np.asarray(feature_names, dtype=str), list(mito_features))
        if not np.any(mask):
            raise ValueError("none of the supplied mitochondrial features matched")
        mito_sum, _ = _row_summaries(counts, mask, chunk_size)
        out[mito_sum_name] = mito_sum
        with np.errstate(divide="ignore", invalid="ignore"):
            percent = 100 * mito_sum / out["sum"].to_numpy(dtype=float)
        # A zero-count spot has no calculable percentage; do not turn it into
        # a measured mitochondrial percentage of zero.
        percent[~np.isfinite(percent)] = np.nan
        out[mito_percent_name] = percent
    return out


def local_modified_z(focal: float, neighbors: np.ndarray) -> float:
    """Exact equation in SpotSweeper::.local_modified_z."""
    center = float(np.median(neighbors))
    mad_unscaled = float(np.median(np.abs(neighbors - center)))
    if not np.isfinite(mad_unscaled) or mad_unscaled == 0:
        return 0.0
    return QNORM_75 * (focal - center) / mad_unscaled


def _query_neighbors(coords: np.ndarray, k: int, workers: int = 1,
                     batch_size: int = 100_000):
    """Yield (start, stop, k-neighbor indices), excluding the focal row."""
    coords = np.asarray(coords, dtype=float)
    if coords.ndim != 2 or coords.shape[1] < 1 or not np.all(np.isfinite(coords)):
        raise ValueError("coordinates must be a finite 2-D numeric array")
    if len(coords) <= k:
        raise ValueError("each sample must contain more spots than n_neighbors")
    tree = cKDTree(coords)
    for start in range(0, len(coords), batch_size):
        stop = min(start + batch_size, len(coords))
        _, indices = tree.query(coords[start:stop], k=k + 1, workers=workers)
        indices = np.atleast_2d(indices)
        rows = np.arange(start, stop)[:, None]
        # The focal point can be anywhere among tied zero-distance entries.
        keep = indices != rows
        cleaned = np.empty((stop - start, k), dtype=np.int64)
        for i in range(stop - start):
            candidate = indices[i, keep[i]]
            if len(candidate) < k:
                raise RuntimeError("could not remove focal observation from KNN result")
            cleaned[i] = candidate[:k]
        yield start, stop, cleaned


def knn_indices(coords: np.ndarray, k: int, workers: int = 1,
                batch_size: int = 100_000) -> np.ndarray:
    result = np.empty((len(coords), k), dtype=np.int64)
    for start, stop, indices in _query_neighbors(coords, k, workers, batch_size):
        result[start:stop] = indices
    return result


def _sample_groups(metadata: pd.DataFrame, sample_column: str):
    if sample_column not in metadata or metadata[sample_column].isna().any():
        raise ValueError("sample column is missing or contains NA")
    for sample in pd.unique(metadata[sample_column]):
        yield sample, np.flatnonzero(metadata[sample_column].to_numpy() == sample)


def local_outliers(metadata: pd.DataFrame, coords: np.ndarray,
                   metric: str = "detected", direction: str = "lower",
                   n_neighbors: int = 36, samples: str = "sample_id",
                   log: bool = True, cutoff: float = 3.0, workers: int = 1,
                   batch_size: int = 100_000) -> pd.DataFrame:
    if metric not in metadata or not pd.api.types.is_numeric_dtype(metadata[metric]):
        raise ValueError("metric must identify a numeric metadata column")
    if direction not in {"lower", "higher", "both"}:
        raise ValueError("direction must be lower, higher, or both")
    if int(n_neighbors) != n_neighbors or n_neighbors < 1:
        raise ValueError("n_neighbors must be a positive integer")
    if not np.isfinite(cutoff) or cutoff < 0:
        raise ValueError("cutoff must be non-negative")
    if len(metadata) != len(coords):
        raise ValueError("metadata and coordinates must have the same rows")
    out = metadata.copy()
    values = out[metric].to_numpy(dtype=float)
    metric_to_use = metric
    if log:
        values = np.log1p(values)
        metric_to_use = f"{metric}_log"
        out[metric_to_use] = values
    if not np.all(np.isfinite(values)):
        raise ValueError("metric contains non-finite values after transformation")

    z = np.empty(len(out), dtype=float)
    for _, selected in _sample_groups(out, samples):
        sample_coords = np.asarray(coords)[selected]
        sample_values = values[selected]
        for start, stop, neighbors in _query_neighbors(sample_coords, n_neighbors, workers, batch_size):
            neighbor_values = sample_values[neighbors]
            centers = np.median(neighbor_values, axis=1)
            mad = np.median(np.abs(neighbor_values - centers[:, None]), axis=1)
            score = np.zeros(stop - start, dtype=float)
            valid = np.isfinite(mad) & (mad != 0)
            score[valid] = QNORM_75 * (sample_values[start:stop][valid] - centers[valid]) / mad[valid]
            z[selected[start:stop]] = score
    out[f"{metric}_z_fallback_python"] = z
    if direction == "lower":
        flag = z < -cutoff
    elif direction == "higher":
        flag = z > cutoff
    else:
        flag = np.abs(z) > cutoff
    out[f"{metric}_outliers_fallback_python"] = flag
    return out


def _huber_rlm(x: np.ndarray, y: np.ndarray, maxiter: int = 20,
               tolerance: float = 1e-4, k: float = 1.345) -> tuple[np.ndarray, np.ndarray]:
    """MASS::rlm(method='M', psi=psi.huber) compatible IRLS approximation."""
    design = np.column_stack([np.ones(len(x)), x])
    if not np.all(np.isfinite(design)) or not np.all(np.isfinite(y)):
        raise ValueError("non-finite values passed to robust regression")
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    for _ in range(maxiter):
        residual = y - design @ beta
        center = np.median(residual)
        scale = np.median(np.abs(residual - center)) / QNORM_75
        if not np.isfinite(scale) or scale == 0:
            break
        u = residual / scale
        weights = np.ones(len(u))
        large = np.abs(u) > k
        weights[large] = k / np.abs(u[large])
        root = np.sqrt(weights)
        updated, *_ = np.linalg.lstsq(design * root[:, None], y * root, rcond=None)
        if np.sqrt(np.mean((updated - beta) ** 2)) <= tolerance:
            beta = updated
            break
        beta = updated
    return beta, y - design @ beta


def _variance_residual(values: np.ndarray, neighbors: np.ndarray) -> np.ndarray:
    neighborhoods = np.concatenate([np.arange(len(values))[:, None], neighbors], axis=1)
    selected = values[neighborhoods]
    means = np.nanmean(selected, axis=1)
    variances = np.nanvar(selected, axis=1, ddof=1)
    means[~np.isfinite(means)] = 0
    variances[~np.isfinite(variances)] = 0
    with np.errstate(divide="ignore", invalid="ignore"):
        response = np.log2(variances)
    # SpotSweeper passes log2(0) to MASS::rlm; surface the same invalid-input
    # condition rather than silently adding an epsilon.
    _, residual = _huber_rlm(means, response)
    return residual


def local_variance(metadata: pd.DataFrame, coords: np.ndarray, metric: str,
                   n_neighbors: int = 36, samples: str = "sample_id",
                   log: bool = False, name: str | None = None,
                   workers: int = 1, batch_size: int = 100_000,
                   precomputed: Mapping[int, np.ndarray] | None = None) -> pd.DataFrame:
    if metric not in metadata or not pd.api.types.is_numeric_dtype(metadata[metric]):
        raise ValueError("metric must identify a numeric metadata column")
    out = metadata.copy()
    values = out[metric].to_numpy(dtype=float)
    if log:
        values = np.log1p(values)
        out[f"{metric}_log"] = values
    result = np.empty(len(out), dtype=float)
    for _, selected in _sample_groups(out, samples):
        if precomputed is not None and len(selected) in precomputed:
            neighbors = precomputed[len(selected)][:, :n_neighbors]
        else:
            neighbors = knn_indices(np.asarray(coords)[selected], n_neighbors, workers, batch_size)
        result[selected] = _variance_residual(values[selected], neighbors)
    out[name or f"{metric}_var_fallback_python"] = result
    return out


def _pca_scores(matrix: np.ndarray) -> np.ndarray:
    center = matrix.mean(axis=0)
    scale = matrix.std(axis=0, ddof=1)
    if np.any(~np.isfinite(scale)) or np.any(scale == 0):
        raise ValueError("artifact PCA contains a constant/non-finite feature")
    standardized = (matrix - center) / scale
    u, s, _ = np.linalg.svd(standardized, full_matrices=False)
    return u * s


def _kmeans_two(matrix: np.ndarray, seed: int, nstart: int = 25,
                maxiter: int = 100) -> np.ndarray:
    rng = np.random.default_rng(seed)
    best_labels = None
    best_inertia = np.inf
    if len(matrix) < 2:
        raise ValueError("artifact k-means requires at least two spots")
    for _ in range(nstart):
        centers = matrix[rng.choice(len(matrix), 2, replace=False)].copy()
        for _ in range(maxiter):
            distance = np.sum((matrix[:, None, :] - centers[None, :, :]) ** 2, axis=2)
            labels = np.argmin(distance, axis=1)
            if len(np.unique(labels)) < 2:
                break
            updated = np.vstack([matrix[labels == group].mean(axis=0) for group in (0, 1)])
            if np.allclose(updated, centers, rtol=0, atol=1e-8):
                centers = updated
                break
            centers = updated
        if len(np.unique(labels)) < 2:
            continue
        inertia = float(np.sum((matrix - centers[labels]) ** 2))
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()
    if best_labels is None:
        raise RuntimeError("artifact k-means could not form two non-empty clusters")
    return best_labels


def find_artifacts(metadata: pd.DataFrame, coords: np.ndarray,
                   mito_percent: str = "expr_chrM_ratio",
                   mito_sum: str = "expr_chrM", samples: str = "sample_id",
                   n_order: int = 5, shape: str = "hexagonal", log: bool = True,
                   seed: int = 123, workers: int = 1,
                   batch_size: int = 100_000) -> tuple[pd.DataFrame, np.ndarray]:
    if samples not in metadata or metadata[samples].nunique(dropna=False) != 1:
        raise ValueError("findArtifacts requires exactly one sample")
    if mito_percent not in metadata or mito_sum not in metadata:
        raise ValueError("mitochondrial metrics are missing")
    percent = metadata[mito_percent].to_numpy(dtype=float)
    summed = metadata[mito_sum].to_numpy(dtype=float)
    if np.all(~np.isfinite(summed) | (summed == 0)):
        raise ValueError("no mitochondrial signal was detected")
    if shape not in {"hexagonal", "square"}:
        raise ValueError("shape must be hexagonal or square")
    if int(n_order) != n_order or n_order < 2:
        raise ValueError("n_order must be at least 2 because annotation uses second-order variance")
    orders = [((3 if shape == "hexagonal" else 4) * i * (i + 1)) for i in range(1, n_order + 1)]
    maximum = max(orders)
    neighbors = knn_indices(coords, maximum, workers, batch_size)
    values = np.log1p(percent) if log else percent
    residuals = []
    out = metadata.copy()
    if log:
        out[f"{mito_percent}_log"] = values
    for k in orders:
        residual = _variance_residual(values, neighbors[:, :k])
        out[f"k{k}_fallback_python"] = residual
        residuals.append(residual)
    matrix = np.column_stack([*residuals, percent, summed])
    scores = _pca_scores(matrix)
    labels = _kmeans_two(scores, seed, nstart=25)
    second_order = residuals[1]
    cluster_means = np.array([second_order[labels == group].mean() for group in (0, 1)])
    artifact_cluster = int(np.argmin(cluster_means))
    out["artifact_fallback_python"] = labels == artifact_cluster
    return out, scores


def flag_visium_outliers(metadata: pd.DataFrame, row: str = "array_row",
                         col: str = "array_col") -> pd.DataFrame:
    if row not in metadata or col not in metadata:
        raise ValueError("array_row and array_col are required")
    out = metadata.copy()
    out["systematic_outliers_fallback_python"] = [
        (int(r), int(c)) in SYSTEMATIC_POSITIONS for r, c in zip(out[row], out[col])
    ]
    return out


def is_standard_visium_platform(value: str | None) -> bool:
    """True only for standard 10x Visium arrays supported by the package list."""
    if value is None:
        return False
    normalized = "".join(character for character in str(value).lower()
                         if character.isalnum())
    return normalized in STANDARD_VISIUM_PLATFORMS


def detected_platform(metadata: pd.DataFrame, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for column in ("platform", "technology"):
        if column not in metadata:
            continue
        values = metadata[column].dropna().astype(str).str.strip()
        unique = values[values.ne("")].unique()
        if len(unique) == 1:
            return str(unique[0])
    return None


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
        raise ValueError("feature files must contain exactly one non-empty name per row")
    return table[0].tolist()


def _write_table(frame: pd.DataFrame, path: str) -> None:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        frame.to_parquet(p, index=False)
    else:
        frame.to_csv(p, sep="\t" if p.suffix.lower() in {".tsv", ".txt"} else ",", index=False)


def _parse_csv(value: str) -> list[str]:
    return [item for item in value.split(",") if item]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--id-column", default="observation_id")
    parser.add_argument("--counts-npz", help="Optional observations-by-features sparse matrix")
    parser.add_argument("--features", help="One feature name per line/CSV row")
    parser.add_argument("--mito-feature-file", help="Explicit mitochondrial feature names")
    parser.add_argument("--x", default="x")
    parser.add_argument("--y", default="y")
    parser.add_argument("--sample", default="sample_id")
    parser.add_argument("--platform",
                        help="Confirmed platform; standard Visium is required for systematic positions")
    parser.add_argument("--metrics", help="Optional override; otherwise use all calculable supported metrics")
    parser.add_argument("--directions", help="Optional comma-separated directions matching --metrics")
    parser.add_argument("--neighbors", type=int, default=36)
    parser.add_argument("--cutoff", type=float, default=3)
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=100_000)
    parser.add_argument("--systematic", action="store_true")
    parser.add_argument("--artifacts", action="store_true")
    parser.add_argument("--mito-percent", default="expr_chrM_ratio")
    parser.add_argument("--mito-sum", default="expr_chrM")
    parser.add_argument("--n-order", type=int, default=5)
    parser.add_argument("--shape", choices=["hexagonal", "square"], default="hexagonal")
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args(argv)

    status = {"engine": ENGINE, "functions": [], "feature_status": [], "differences": []}
    feature_status = status["feature_status"]
    metadata = _normalize_id_column(
        _read_table(args.metadata, (args.id_column,)), args.id_column
    )
    if args.counts_npz:
        if not args.features:
            raise ValueError("--features is required with --counts-npz")
        counts = sparse.load_npz(args.counts_npz)
        features = _read_feature_names(args.features)
        mito_features = None
        if args.mito_feature_file:
            requested = set(_read_feature_names(args.mito_feature_file))
            matched = requested.intersection(features)
            if matched:
                mito_features = matched
            else:
                feature_status.append({
                    "feature": "mitochondrial_metrics", "status": "skipped",
                    "reason": "no supplied mitochondrial feature was measured",
                })
        metadata = add_count_metrics(
            counts, metadata, features, mito_features,
            mito_sum_name=args.mito_sum, mito_percent_name=args.mito_percent,
            chunk_size=args.batch_size,
        )
        status["functions"].append("addPerCellQCMetrics:sparse-python")
        feature_status.append({"feature": "basic_count_metrics", "status": "completed"})
        if mito_features is not None:
            feature_status.append({
                "feature": "mitochondrial_metrics", "status": "completed",
                "measured_all_zero": bool((metadata[args.mito_sum] == 0).all()),
            })
        elif not args.mito_feature_file:
            feature_status.append({
                "feature": "mitochondrial_metrics", "status": "skipped",
                "reason": "mitochondrial feature annotations were not supplied",
            })
    elif args.mito_percent in metadata and args.mito_sum in metadata:
        feature_status.append({"feature": "mitochondrial_metrics", "status": "completed",
                               "source": "metadata"})
    else:
        feature_status.append({"feature": "basic_count_metrics", "status": "skipped",
                               "reason": "no count matrix was supplied"})
        feature_status.append({"feature": "mitochondrial_metrics", "status": "skipped",
                               "reason": "mitochondrial columns and count annotations are unavailable"})

    coords = None
    if args.x in metadata and args.y in metadata:
        try:
            coords = metadata[[args.x, args.y]].to_numpy(dtype=float)
            if not np.all(np.isfinite(coords)):
                raise ValueError("coordinates contain non-finite values")
        except Exception as exc:
            feature_status.append({"feature": "spatial_coordinates", "status": "failed",
                                   "reason": str(exc)})
    else:
        feature_status.append({"feature": "spatial_coordinates", "status": "skipped",
                               "reason": "coordinate columns are unavailable"})

    if args.metrics:
        metrics = _parse_csv(args.metrics)
        directions = (_parse_csv(args.directions) if args.directions
                      else ["lower"] * len(metrics))
        log_metrics = [not args.no_log] * len(metrics)
    else:
        metrics = [name for name in ("sum", "detected", args.mito_percent)
                   if name in metadata]
        directions = ["higher" if name == args.mito_percent else "lower"
                      for name in metrics]
        # SpotSweeper's vignette uses log1p for count metrics and raw scale for
        # mitochondrial percentage.
        log_metrics = [False if name == args.mito_percent else not args.no_log
                       for name in metrics]
    if len(metrics) != len(directions):
        raise ValueError("directions must have one entry per metric")
    for metric, direction, use_log in zip(metrics, directions, log_metrics):
        if coords is None or metric not in metadata:
            feature_status.append({"feature": f"local_outlier:{metric}", "status": "skipped",
                                   "reason": "required coordinates or metric are unavailable"})
            continue
        values = pd.to_numeric(metadata[metric], errors="coerce")
        sample_ok = (args.sample in metadata and not metadata[args.sample].isna().any()
                     and int(metadata.groupby(args.sample, dropna=False).size().min()) > args.neighbors)
        values_ok = values.notna().all() and (not use_log or (values >= -1).all())
        if not sample_ok or not values_ok:
            feature_status.append({
                "feature": f"local_outlier:{metric}", "status": "skipped",
                "reason": "metric/sample inputs are non-finite or a sample has too few neighbors",
            })
            continue
        try:
            metadata = local_outliers(metadata, coords, metric, direction,
                                      args.neighbors, args.sample, use_log,
                                      args.cutoff, args.workers, args.batch_size)
            status["functions"].append(f"localOutliers:{metric}")
            feature_status.append({"feature": f"local_outlier:{metric}", "status": "completed"})
        except Exception as exc:
            feature_status.append({"feature": f"local_outlier:{metric}", "status": "failed",
                                   "reason": str(exc)})
    platform = detected_platform(metadata, args.platform)
    has_array_positions = {"array_row", "array_col"}.issubset(metadata.columns)
    if is_standard_visium_platform(platform) and has_array_positions:
        try:
            metadata = flag_visium_outliers(metadata)
            status["functions"].append("flagVisiumOutliers")
            feature_status.append({"feature": "systematic_outliers", "status": "completed"})
        except Exception as exc:
            feature_status.append({"feature": "systematic_outliers", "status": "failed",
                                   "reason": str(exc)})
    else:
        reason = (
            "array_row/array_col are unavailable"
            if is_standard_visium_platform(platform)
            else "platform is not confirmed as a standard 10x Visium array"
        )
        feature_status.append({"feature": "systematic_outliers", "status": "skipped",
                               "reason": reason, "platform": platform})
    if args.artifacts:
        missing = [name for name in (args.mito_percent, args.mito_sum) if name not in metadata]
        if coords is None or missing:
            feature_status.append({"feature": "regional_artifacts", "status": "skipped",
                                   "reason": "required coordinates or mitochondrial metrics are unavailable"})
        elif not np.any(pd.to_numeric(metadata[args.mito_sum], errors="coerce").fillna(0) > 0):
            feature_status.append({"feature": "regional_artifacts", "status": "skipped",
                                   "reason": "mitochondrial features were measured but contain no positive signal"})
        elif args.sample not in metadata or metadata[args.sample].nunique(dropna=False) != 1:
            feature_status.append({"feature": "regional_artifacts", "status": "skipped",
                                   "reason": "artifact detection requires exactly one sample per call"})
        elif len(metadata) <= ((3 if args.shape == "hexagonal" else 4)
                              * args.n_order * (args.n_order + 1)):
            feature_status.append({"feature": "regional_artifacts", "status": "skipped",
                                   "reason": "too few spots for the largest artifact neighborhood"})
        else:
            try:
                metadata, scores = find_artifacts(metadata, coords, args.mito_percent,
                                                  args.mito_sum, args.sample, args.n_order,
                                                  args.shape, not args.no_log, args.seed,
                                                  args.workers, args.batch_size)
                np.save(args.output + ".PCA_artifacts_fallback_python.npy", scores)
                status["functions"].append("findArtifacts")
                feature_status.append({"feature": "regional_artifacts", "status": "completed"})
                status["differences"].append("Python Huber IRLS, SVD PCA, k-means and RNG differ from MASS/stats R implementations")
            except Exception as exc:
                feature_status.append({"feature": "regional_artifacts", "status": "failed",
                                       "reason": str(exc)})
    else:
        feature_status.append({"feature": "regional_artifacts", "status": "skipped",
                               "reason": "artifact geometry was not requested/verified"})
    _write_table(metadata, args.output)
    Path(args.output + ".status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
