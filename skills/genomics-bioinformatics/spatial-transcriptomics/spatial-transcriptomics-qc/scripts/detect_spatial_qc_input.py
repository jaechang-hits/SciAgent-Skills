#!/usr/bin/env python3
"""Classify spatial-transcriptomics QC input as spot/bin, imaging-cell, or unknown.

Usage:
    python detect_spatial_qc_input.py /path/to/input
    python detect_spatial_qc_input.py --evidence-json evidence.json

The detector requires compound evidence. A platform-looking filename alone is
never sufficient. It prints a JSON record containing the selected route,
confidence, supporting evidence, conflicts, and remaining uncertainty.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from typing import Any


SPOT_PLATFORMS = {"visium", "visium hd", "slide-seq", "slideseq", "st"}
IMAGING_PLATFORMS = {
    "xenium", "cosmx", "nanostring cosmx", "merfish", "merscope", "seqfish"
}
SPOT_UNITS = {"spot", "bin", "bead"}
IMAGING_UNITS = {"cell", "segmented cell", "segmentation cell"}


def _normalise(values: Any) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        values = [values]
    return {str(value).strip().lower() for value in values if str(value).strip()}


def classify_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Classify already-inspected evidence without trusting one filename."""
    files = _normalise(evidence.get("files"))
    columns = _normalise(evidence.get("columns"))
    platforms = _normalise(evidence.get("platform_labels"))
    units = _normalise(evidence.get("observation_units"))
    structures = _normalise(evidence.get("structures"))
    has_coordinates = bool(evidence.get("has_spatial_coordinates"))
    has_counts = bool(evidence.get("has_count_matrix"))

    spot_reasons: list[str] = []
    imaging_reasons: list[str] = []

    spot_platforms = platforms & SPOT_PLATFORMS
    imaging_platforms = platforms & IMAGING_PLATFORMS
    spot_units = units & SPOT_UNITS
    imaging_units = units & IMAGING_UNITS
    if spot_platforms:
        spot_reasons.append(f"platform metadata: {sorted(spot_platforms)}")
    if imaging_platforms:
        imaging_reasons.append(f"platform metadata: {sorted(imaging_platforms)}")
    if spot_units:
        spot_reasons.append(f"observation unit: {sorted(spot_units)}")
    if imaging_units:
        imaging_reasons.append(f"observation unit: {sorted(imaging_units)}")

    has_tissue_positions = any("tissue_positions" in value for value in files | structures)
    has_spatial_dir = any(value == "spatial" or value.endswith("/spatial") for value in structures)
    has_binned = any("binned_outputs" in value or "square_" in value for value in files | structures)
    spot_columns = {"array_row", "array_col", "in_tissue"} & columns
    if has_counts and has_coordinates and (
        (has_tissue_positions and (has_spatial_dir or len(spot_columns) >= 2))
        or has_binned
        or (len(spot_columns) >= 2 and bool(spot_units))
    ):
        spot_reasons.append("count matrix + spatial coordinates + spot/bin structure")

    has_cells_table = any(
        value.endswith("cells.csv") or value.endswith("cells.csv.gz")
        or "cell_metadata" in value
        for value in files
    )
    has_boundaries = any("boundar" in value or "polygon" in value for value in files | structures)
    cell_id_columns = {"cell_id", "cellid", "entityid"} & columns
    centroid_columns = {"x_centroid", "y_centroid", "center_x", "center_y"} & columns
    segmentation_columns = {
        "cell_area", "nucleus_area", "fov", "volume",
        "control_probe_counts", "control_codeword_counts",
    } & columns
    if has_counts and has_coordinates and cell_id_columns and (
        has_cells_table or has_boundaries or len(segmentation_columns) >= 1
        or len(centroid_columns) >= 2
    ):
        imaging_reasons.append("count matrix + cell IDs + cell-level spatial/segmentation evidence")

    conflicts: list[str] = []
    if spot_reasons and imaging_reasons:
        conflicts.append("both spot/bin and imaging-cell evidence were found")
    if spot_platforms and imaging_units:
        conflicts.append("spot platform metadata conflicts with cell observation unit")
    if imaging_platforms and spot_units:
        conflicts.append("imaging platform metadata conflicts with spot/bin observation unit")

    core_ok = has_counts and has_coordinates
    if conflicts:
        route, confidence = "unknown", "conflicting"
    elif core_ok and spot_reasons and not imaging_reasons:
        route = "spot"
        confidence = "high" if (spot_platforms or spot_units) and has_counts and has_coordinates else "medium"
    elif core_ok and imaging_reasons and not spot_reasons:
        route = "imaging"
        confidence = "high" if (imaging_platforms or imaging_units) and has_counts and has_coordinates else "medium"
    else:
        route, confidence = "unknown", "insufficient"

    uncertainties: list[str] = []
    if not has_counts:
        uncertainties.append("no count-matrix evidence")
    if not has_coordinates:
        uncertainties.append("no aligned spatial-coordinate evidence")
    if not platforms:
        uncertainties.append("platform metadata absent")
    if not units:
        uncertainties.append("observation unit absent")
    if route == "unknown" and not conflicts:
        uncertainties.append("insufficient compound evidence to choose a QC branch")

    return {
        "route": route,
        "confidence": confidence,
        "spot_skill": "spatial-transcriptomics-spot-qc" if route == "spot" else None,
        "imaging_skill": "spatial-transcriptomics-imaging-qc" if route == "imaging" else None,
        "spot_evidence": spot_reasons,
        "imaging_evidence": imaging_reasons,
        "conflicts": conflicts,
        "uncertainties": uncertainties,
    }


def _header(path: Path) -> list[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
            return next(csv.reader(handle))
    except (OSError, StopIteration, UnicodeError):
        return []


def inspect_path(path: Path) -> dict[str, Any]:
    """Collect cheap structural evidence from a directory or H5AD file."""
    if not path.exists():
        raise FileNotFoundError(path)
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    relative = [p.name if path.is_file() else p.relative_to(path).as_posix() for p in files]
    structures = [] if path.is_file() else [p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_dir()]
    columns: set[str] = set()
    platform_labels: set[str] = set()
    observation_units: set[str] = set()

    for file_path in files:
        lower = file_path.name.lower()
        if lower.endswith((".csv", ".csv.gz", ".tsv", ".tsv.gz")):
            columns.update(_header(file_path))
        if lower.endswith(".json") and file_path.stat().st_size <= 5_000_000:
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
                text = json.dumps(payload).lower()
                platform_labels.update(p for p in SPOT_PLATFORMS | IMAGING_PLATFORMS if p in text)
                for unit in SPOT_UNITS | IMAGING_UNITS:
                    if f'"{unit}"' in text:
                        observation_units.add(unit)
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass

    h5ad_files = [p for p in files if p.suffix.lower() == ".h5ad"]
    for h5ad in h5ad_files:
        try:
            import anndata as ad  # optional; the router still works without it

            obj = ad.read_h5ad(h5ad, backed="r")
            columns.update(map(str, obj.obs.columns))
            has_spatial = "spatial" in obj.obsm
            for key in ("platform", "technology", "observation_unit"):
                if key in obj.obs:
                    values = set(map(str, obj.obs[key].dropna().unique()[:20]))
                    (observation_units if key == "observation_unit" else platform_labels).update(values)
                if key in obj.uns:
                    values = obj.uns[key]
                    (observation_units if key == "observation_unit" else platform_labels).update(
                        [str(values)] if not isinstance(values, (list, tuple, set)) else map(str, values)
                    )
            obj.file.close()
        except Exception:
            has_spatial = False
        if has_spatial:
            structures.append("h5ad:obsm/spatial")

    lower_files = {value.lower() for value in relative}
    lower_structures = {value.lower() for value in structures}
    has_counts = bool(h5ad_files) or any(
        "matrix" in value or "cell_by_gene" in value or "exprmat" in value
        for value in lower_files
    )
    has_coordinates = (
        "h5ad:obsm/spatial" in lower_structures
        or {"x_centroid", "y_centroid"} <= {c.lower() for c in columns}
        or {"pxl_row_in_fullres", "pxl_col_in_fullres"} <= {c.lower() for c in columns}
        or any("tissue_positions" in value for value in lower_files)
    )
    return {
        "source": str(path),
        "files": sorted(lower_files),
        "structures": sorted(lower_structures),
        "columns": sorted({c.lower() for c in columns}),
        "platform_labels": sorted(_normalise(platform_labels)),
        "observation_units": sorted(_normalise(observation_units)),
        "has_count_matrix": has_counts,
        "has_spatial_coordinates": has_coordinates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--evidence-json", type=Path)
    args = parser.parse_args()
    if bool(args.path) == bool(args.evidence_json):
        parser.error("provide exactly one input path or --evidence-json")
    evidence = (
        json.loads(args.evidence_json.read_text(encoding="utf-8"))
        if args.evidence_json else inspect_path(args.path)
    )
    result = {"evidence": evidence, **classify_evidence(evidence)}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
