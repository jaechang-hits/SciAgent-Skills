---
name: "spatial-transcriptomics-spot-qc"
description: "Spot/bin spatial transcriptomics QC for Visium, Visium HD, Slide-seq and related capture-location assays. Validate raw counts, aligned coordinates, sample and bin metadata; run SpotSweeper local count/detected-feature outliers and conditional mitochondrial regional-artifact detection; visualize and integrate evidence, validate expected impact, and require D2 before creating a filtered copy. For Xenium/CosMx/MERFISH cells use spatial-transcriptomics-imaging-qc."
license: "CC-BY-4.0"
---

# Spot/Bin Spatial Transcriptomics QC

## Overview

Assess spot/bin data without treating capture locations as segmented cells.
SpotSweeper is the primary spatial engine. Produce auditable metrics,
recommendations and expected filtering impact while preserving source counts
and observations. A local-outlier flag or 3-MAD-like fence is supporting
evidence, never an automatic final exclusion rule.

Before planning, read both bundled references:

- `/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-spot-qc/references/spotsweeper-workflow.md`
- `/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-qc/references/integrated-assessment.md`

The Supervisor must pass this Skill and those required reference contents to
WorkflowPlanner; the Planner does not read Skills itself.

## When to Use

- QC a Space Ranger Visium section before downstream analysis
- QC a selected Visium HD bin resolution while preserving its bin size
- Detect low-count or low-detected-feature spots relative to spatial neighbours
- Inspect regional mitochondrial artifacts when mitochondrial signal is measured
- Compare spot/bin QC distributions and expected impact across slides or samples
- Use `spatial-transcriptomics-imaging-qc` instead for Xenium, CosMx or MERFISH segmented cells
- Use `spatial-transcriptomics-qc` first when the observation unit is uncertain

## Prerequisites

SpotSweeper is the required spot/bin engine, not an optional enhancement.
Install it before writing any QC code, just as a Python skill installs its
required package before importing it. This runtime uses R 4.5/Bioconductor
3.22; do not switch to a development Bioconductor release.

Run this bootstrap first. It installs only missing packages, then loads
SpotSweeper and checks the functions required by this workflow:

```python
import subprocess

r_code = r'''
if (!requireNamespace("BiocManager", quietly=TRUE))
  install.packages("BiocManager", repos="https://cloud.r-project.org")
missing <- c("SpotSweeper", "zellkonverter")[
  !vapply(c("SpotSweeper", "zellkonverter"), requireNamespace,
          quietly=TRUE, FUN.VALUE=logical(1))
]
if (length(missing))
  BiocManager::install(missing, version="3.22", ask=FALSE, update=FALSE)
suppressPackageStartupMessages({
  library(SpotSweeper)
  library(zellkonverter)
  library(SpatialExperiment)
})
required <- c("localOutliers", "findArtifacts", "plotQCmetrics")
stopifnot(all(required %in% getNamespaceExports("SpotSweeper")))
cat("SpotSweeper", as.character(packageVersion("SpotSweeper")), "import OK\n")
'''

result = subprocess.run(
    ["Rscript", "-e", r_code],
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.returncode != 0:
    raise RuntimeError(f"SpotSweeper bootstrap failed:\n{result.stderr}")
```

Obtain the runtime's required slow-install approval before running the bootstrap
when installation is needed. If installation or import fails, preserve the
exact error. Only then may the workflow record `engine_unavailable` and offer
labeled common QC; never describe common QC as SpotSweeper-equivalent.

Required data:

- integer-like raw count matrix with unique spot/bin IDs;
- two finite coordinates aligned one-to-one with observations;
- explicit sample/slide identifiers;
- platform and observation unit; for HD, selected `bin_size_um`;
- validated feature annotation before mitochondrial calculations.

## Pre-flight Interview

Inspect first. This pipeline has no optional polygon decision. Ask D2 only after
the final recommendation and impact bundle exists.

```yaml
decisions:
  - id: D2
    param: applyFiltering
    kind: required
    source: user
    ask: "I have shown the final integrated rule, cutoff/flag plots, expected impact and biological-loss risk. Should I create a separately named filtered copy using this exact rule set?"
    default: null
    skip_if: "assessment/recommendation only, or no Exclude candidate observations"
```

## Workflow

### Step 1: Confirm Spot/Bin Routing and Capabilities

Require compound spot/bin evidence from the router. Recheck matrix, IDs,
coordinates, sample groups and platform metadata; never route from a filename
alone.

```python
from pathlib import Path
import json

classification = json.loads(Path("qc_input_classification.json").read_text())
if classification["route"] != "spot":
    raise ValueError("spot QC requires confirmed spot/bin routing")
print(classification["confidence"], classification["spot_evidence"])
```

Write `qc_capabilities.tsv` and initialize observation accounting. Keep input,
join, analysis-view and later intentional-filtering losses distinct.

### Step 2: Load the Requested Resolution Without Filtering

For Visium HD, resolve the selected `binned_outputs/square_<N>um` directory;
for Visium, use the Space Ranger root. Preserve off-tissue observations and
create a named tissue analysis view.

```python
import pandas as pd
import scanpy as sc

MATRIX_H5 = "path/to/filtered_feature_bc_matrix.h5"
POSITIONS_CSV = "path/to/spatial/tissue_positions.csv"
positions = pd.read_csv(POSITIONS_CSV, index_col="barcode")
adata_full = sc.read_10x_h5(MATRIX_H5, gex_only=False)
adata_full.var_names_make_unique()
adata_full.layers["counts"] = adata_full.X.copy()
adata_full.obs = adata_full.obs.join(positions, how="left", validate="one_to_one")
adata_full.obsm["spatial"] = adata_full.obs[
    ["pxl_col_in_fullres", "pxl_row_in_fullres"]].to_numpy(float)
analysis_mask = adata_full.obs["in_tissue"].astype(int).eq(1).to_numpy()
adata = adata_full[analysis_mask].copy()
print(adata_full.n_obs, adata.n_obs)
```

Changing HD bin size loads a different observation set and requires separate
provenance; it is not a plotting parameter.

### Step 3: Compute Common Metrics and Build the R Bridge

Calculate totals and detected features from raw counts. Add mitochondrial
metrics only after feature annotation proves they are meaningful.

```python
import numpy as np

X = adata.layers["counts"]
adata.obs["total_counts"] = np.asarray(X.sum(axis=1)).ravel()
adata.obs["detected_genes"] = np.asarray((X > 0).sum(axis=1)).ravel()
print(adata.obs[["total_counts", "detected_genes"]].describe())
```

Create a barcode-keyed AnnData bridge and construct a `SpatialExperiment` with
the same ID order. Do not let package defaults remove zero-count observations.

```python
import anndata as ad

bridge = ad.AnnData(X=adata.layers["counts"], obs=adata.obs.copy(),
                    var=adata.var.copy(),
                    obsm={"spatial": adata.obsm["spatial"].copy()})
bridge.write_h5ad("qc_bridge_input.h5ad", compression="gzip")
print(bridge.shape)
```

```r
suppressPackageStartupMessages({
  library(SpotSweeper)
  library(zellkonverter)
  library(SpatialExperiment)
})

sce <- readH5AD("qc_bridge_input.h5ad", X_name="counts", reader="R",
                use_hdf5=FALSE, obsm="spatial")
xy <- as.matrix(reducedDim(sce, "spatial"))
storage.mode(xy) <- "double"
rownames(xy) <- colnames(sce)
spe <- SpatialExperiment(
  assays=assays(sce), rowData=rowData(sce), colData=colData(sce),
  spatialCoords=xy, metadata=metadata(sce))
stopifnot(!anyDuplicated(colnames(spe)),
          identical(colnames(spe), rownames(spatialCoords(spe))))
metadata(spe)$platform <- unique(as.character(spe$platform))
```

### Step 4: Run SpotSweeper by Sample

Read
`/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-spot-qc/references/spotsweeper-workflow.md`
now. Run `localOutliers()` for `sum` and `detected` within each sample and save
package-native plots. Record actual version, neighbours, directions, cutoff,
workers and errors.

```r
stopifnot(requireNamespace("SpotSweeper", quietly=TRUE))
group_sizes <- table(spe_qc$sample_id)
n_neighbors <- min(36L, as.integer(min(group_sizes)) - 1L)
stopifnot(n_neighbors >= 2L)
spe_qc <- SpotSweeper::localOutliers(
  spe_qc, metric="sum", direction="lower", n_neighbors=n_neighbors,
  samples="sample_id", log=TRUE, cutoff=3, workers=1)
```

The robust cutoff detects local metric outliers only. Do not predeclare it as
the final filtering cutoff.

### Step 5: Run Conditional Mitochondrial Artifact Detection

Skip with an explicit input-incompatible reason when mitochondrial targets or
finite non-zero signal are absent.

```r
if (all(c("expr_chrM_ratio", "expr_chrM") %in% colnames(colData(spe_qc))) &&
    any(spe_qc$expr_chrM > 0, na.rm=TRUE)) {
  spe_qc <- SpotSweeper::findArtifacts(
    spe_qc, mito_percent="expr_chrM_ratio", mito_sum="expr_chrM",
    samples="sample_id", n_order=5, shape="hexagonal", log=TRUE,
    name="artifact", var_output=TRUE)
}
```

Verify actual grid geometry before choosing `shape`, especially for HD or
non-Visium inputs.

### Step 6: Return Metrics and Integrate Evidence

Export the completed R result by ID and require exact Python/R ID equality
before joining. Then read the shared integrated-assessment reference.

```python
qc_from_r = pd.read_csv("qc_metrics_from_r.tsv", sep="\t",
                        dtype={"observation_id": str}).set_index("observation_id")
python_ids = pd.Index(adata.obs_names.astype(str), name="observation_id")
if len(python_ids.difference(qc_from_r.index)) or len(qc_from_r.index.difference(python_ids)):
    raise ValueError("Python/R observation IDs do not match exactly")
adata.obs = adata.obs.join(qc_from_r.reindex(python_ids), validate="one_to_one")
```

Assess correlated evidence domains, spatial coherence, sample effects and
biological alternatives. Produce metric rows and an integrated rule without
turning one package flag into exclusion.

### Step 7: Visualize, Validate Impact, Resolve D2 and Report

Create all major distributions, explicit cutoff overlays and spatial maps from
the same recommendation configuration. Validate overall and per-sample impact.

```python
class_order = ["Retain", "Review", "Exclude candidate"]
impact = adata.obs["qc_class"].value_counts().reindex(class_order, fill_value=0)
print(impact, (100 * impact / adata.n_obs).round(2))
```

If no exclusions exist or the request is assessment-only, record D2 as
`not_applicable`. Otherwise show the final bundle and ask D2 once for the exact
`rule_set_id`. Only an approved D2 may create a separately named filtered copy.

## Key Parameters

| Parameter | Default/reference | Decision rule |
|---|---|---|
| `bin_size_um` | user-selected Space Ranger output | fixed per loaded HD object; never silently switch |
| `n_neighbors` | 36 maximum | less than every sample size; reduce transparently |
| `cutoff` | 3 robust-z units | metric-level outlier evidence, not final filtering cutoff |
| `direction` | lower for `sum`/`detected` | higher only for validated bad-high metrics |
| `samples` | `sample_id` | never mix unrelated sections in one neighbourhood |
| `n_order` | 5 | only for measured mitochondrial regional artifacts |
| `shape` | actual array geometry | do not assume hexagonal for arbitrary bins |

## Common Recipes

### Quantify Impact Without Filtering

```python
impact = (adata.obs.assign(flagged=adata.obs["qc_class"].eq("Exclude candidate"))
          .groupby("sample_id", dropna=False)["flagged"].agg(["sum", "size"]))
impact["percent"] = 100 * impact["sum"] / impact["size"]
print(impact)
```

### Inspect a Package Outlier Column

```r
flag <- spe_qc$sum_outliers
print(table(flag, useNA="ifany"))
print(attributes(flag))
```

## Expected Outputs

- `qc_input_classification.json`, `qc_capabilities.tsv`
- `qc_environment_status.tsv`, `qc_execution_log.tsv`
- `qc_observation_accounting.tsv`, `qc_observation_flags.tsv`
- SpotSweeper package plots and cross-engine recommendation plots
- `qc_cutoff_recommendations.tsv`, candidate/rule/impact/validation tables
- `qc_filtering_recommendation.html`, `spatial_qc_report.html`
- optional `spatial_qc_filtered_copy.h5ad` only after D2

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `Rscript` or SpotSweeper unavailable | runtime/package/dependency missing | request the slow install when required, install and verify the approved 1.6.0 build; use labeled common QC only after an actual install/import attempt fails |
| No spatial map | positions were not joined by barcode | enforce one-to-one join and finite aligned coordinates |
| Local outlier call fails | groups smaller than neighbourhood | reduce neighbours transparently or mark input incompatible |
| `findArtifacts()` has no signal | mitochondrial targets absent or all zero | skip and record the reason; do not fabricate signal |
| HD result changes unexpectedly | another bin size was loaded | record and compare distinct observation sets |
| A coherent region is flagged | biology or regional artifact | inspect histology/region and multiple evidence domains |
| Outliers exist but no exclusion | integrated assessment incomplete or inconclusive | finish impact review; never promote the package cutoff automatically |

## Bundled Resources

- `references/spotsweeper-workflow.md` — required execution and bridge details.
- `../spatial-transcriptomics-qc/references/integrated-assessment.md` — required shared interpretation and D2 policy.

## References

- SpotSweeper Bioconductor package: https://bioconductor.org/packages/SpotSweeper
- SpotSweeper source: https://github.com/MicTott/SpotSweeper
- 10x Genomics Space Ranger outputs: https://www.10xgenomics.com/support/software/space-ranger/latest/analysis/outputs/output-overview
- SpatialExperiment package: https://bioconductor.org/packages/SpatialExperiment
