---
name: "spatial-transcriptomics-qc"
description: "Spatial transcriptomics QC routing for ambiguous or generic requests. Inspect count matrices, coordinates, metadata, manifests and observation units; classify inputs as spot/bin (Visium/Visium HD) or segmented imaging-cell (Xenium/CosMx/MERFISH), then read the corresponding SpotSweeper or SpaceTrooper QC skill. Do not choose from filenames alone or invent a route when evidence conflicts."
license: "CC-BY-4.0"
---

# Spatial Transcriptomics QC Router

## Overview

Route a generic spatial-transcriptomics QC request to exactly one executable QC
pipeline. This entry does not perform QC and must not be handed to
WorkflowPlanner as if it contained the analysis workflow. It inventories the
input, establishes the observation unit, and requires the Supervisor to read
the selected specialist Skill in full before planning.

The two executable routes are:

- `spatial-transcriptomics-spot-qc`: Visium, Visium HD, Slide-seq and other
  spot/bin assays; primary spatial engine SpotSweeper.
- `spatial-transcriptomics-imaging-qc`: Xenium, CosMx, MERFISH and other
  segmented-cell imaging assays; primary spatial engine SpaceTrooper.

## Key Concepts

### Platform Is Evidence, Not the Routing Decision

A platform label is useful only when it agrees with the data structure.
Inspect the manifest or metadata together with the matrix, coordinates, and
observation IDs. A renamed `.h5ad` or copied CSV is not proof of platform.

### Observation Unit Determines the QC Family

Spot/bin assays quantify a capture location that may contain multiple cells.
Imaging assays quantify a segmented cell and may also provide cell boundaries,
controls, area/volume, FOV and segmentation geometry. Visium HD remains a bin
assay even when its bins approach cellular dimensions.

### Capability Is Separate From Route

Routing identifies the correct QC family. The selected Skill must still prove
whether coordinates, controls, mitochondrial signal, polygons, QScore inputs,
images and grouping fields are usable. Do not infer those capabilities from the
platform name.

## Decision Framework

```text
Generic spatial QC request
        |
        +--> inventory matrix + IDs + coordinates + metadata/manifest
        |
        +--> spot/bin observation evidence? ---- yes --> read spot-qc
        |
        +--> segmented-cell evidence? ---------- yes --> read imaging-qc
        |
        +--> both or neither -------------------------> report unknown/conflict
```

| Evidence | Route | Required follow-up |
|---|---|---|
| Visium/Visium HD metadata plus aligned tissue-position rows and spot/bin IDs | spot | Read `spatial-transcriptomics-spot-qc/SKILL.md` |
| Xenium/CosMx/MERFISH metadata plus cell IDs and cell-level coordinates/segmentation fields | imaging | Read `spatial-transcriptomics-imaging-qc/SKILL.md` |
| `.h5ad` with explicit compatible platform and observation-unit metadata | matching route | Verify raw counts and aligned `obsm["spatial"]` before delegation |
| `.h5ad` with coordinates but no platform/observation unit | unknown | Inspect `obs`, `uns`, source manifest and upstream export; do not guess |
| Platform label conflicts with structure or observation unit | unknown | Record both claims and ask for corrected metadata/source evidence |

## Best Practices

1. Inspect before asking the user. Inventory files, table headers, HDF5/AnnData
   schema, metadata and manifests first.
2. Require compound evidence. A route needs compatible matrix/ID/coordinate
   evidence plus platform, observation-unit, or characteristic structure.
3. Record the basis. Save the selected route, confidence, evidence, conflicts
   and uncertainty in `qc_input_classification.json`.
4. Read the specialist Skill after routing. The router is not a substitute for
   SpotSweeper or SpaceTrooper instructions.
5. Pass specialist content to WorkflowPlanner. The Planner does not search or
   read Skills itself; the Supervisor must include the selected Skill content
   and input-evidence summary in its delegation.
6. Stop on ambiguity. If evidence is insufficient or conflicting, report the
   limitation instead of silently choosing the more familiar workflow.

## Common Pitfalls

- **Choosing Xenium from `cells.csv` alone.** Generic cell tables are common.
  **How to avoid:** require a count matrix, cell IDs, aligned coordinates and
  compatible platform/segmentation evidence.
- **Treating Visium HD as segmented-cell imaging.** Small bins are not cell
  polygons. **How to avoid:** route Space Ranger binned outputs to spot QC.
- **Trusting an `.h5ad` filename.** Export names lose provenance. **How to
  avoid:** inspect `obs`, `uns`, `obsm`, raw-count layers and the source manifest.
- **Reading only this router before planning.** It contains no engine workflow.
  **How to avoid:** read the selected specialist Skill and any references it
  marks required before delegating to WorkflowPlanner.
- **Using both QC Skills on one observation table.** That duplicates metrics
  and mixes incompatible semantics. **How to avoid:** select one route; process
  genuinely mixed inputs as separate objects with separate accounting.
- **Inferring polygons or QScore from an imaging route.** Imaging classification
  proves neither. **How to avoid:** let the imaging Skill run its independent
  capability and D1 checks.

## Workflow

1. Inventory input files without extracting over the source or mutating the
   only copy.
2. Verify a raw or integer-like count matrix and unique observation IDs.
3. Verify coordinates are finite and align one-to-one with observations.
4. Inspect manifest, platform/technology fields, observation-unit fields,
   characteristic table columns, and directory structure.
5. Read the bundled detector at
   `/SciAgent-Skills/skills/genomics-bioinformatics/spatial-transcriptomics/spatial-transcriptomics-qc/scripts/detect_spatial_qc_input.py`,
   copy it unchanged into the analysis workspace, and run that workspace copy as
   a reproducible summary aid:

   ```bash
   python detect_spatial_qc_input.py /path/to/input \
     > qc_input_classification.json
   ```

6. Review the detector evidence. It is a guardrail, not authority: resolve any
   mismatch against the actual schema and source documentation.
7. Select exactly one route. When `route=unknown`, stop and state what evidence
   is missing or conflicting.
8. Read the exact selected entrypoint:

   ```text
   skills/genomics-bioinformatics/spatial-transcriptomics/
     spatial-transcriptomics-spot-qc/SKILL.md
   ```

   or:

   ```text
   skills/genomics-bioinformatics/spatial-transcriptomics/
     spatial-transcriptomics-imaging-qc/SKILL.md
   ```

9. Before calling WorkflowPlanner, provide the specialist Skill content and a
   concise evidence summary containing route, platform, observation unit,
   matrix layer, coordinate columns, ID field, sample/FOV fields, capabilities,
   uncertainty and relevant file paths.

## Protocol Guidelines

- A file list is only the start of inspection; inspect schemas and metadata.
- `filtered_feature_bc_matrix.h5` plus `spatial/tissue_positions*` is compound
  spot evidence; `binned_outputs/square_*um` remains spot/bin evidence.
- A cell matrix plus unique `cell_id`, cell centroids and segmentation/FOV
  fields is compound imaging evidence.
- Coordinates alone do not distinguish routes.
- Counts plus coordinates do not prove polygon, control, mitochondrial, image
  or QScore capability.
- Preserve classification evidence with the downstream QC report.

## Further Reading

- 10x Genomics Space Ranger output overview: https://www.10xgenomics.com/support/software/space-ranger/latest/analysis/outputs/output-overview
- 10x Genomics Xenium output overview: https://www.10xgenomics.com/support/software/xenium-onboard-analysis/latest/analysis/xoa-output-overview
- SpatialExperiment data model: https://bioconductor.org/packages/SpatialExperiment
- AnnData format specification: https://anndata.readthedocs.io/en/latest/fileformat-prose.html

## Related Skills

- `spatial-transcriptomics-spot-qc` — executable spot/bin QC pipeline.
- `spatial-transcriptomics-imaging-qc` — executable segmented imaging-cell QC pipeline.
- `spatial-transcriptomics-cell-type-annotation` — annotation after imaging-cell QC.
- `spatial-transcriptomics-deconvolution-cell2location` — cell-type proportions after spot QC.
