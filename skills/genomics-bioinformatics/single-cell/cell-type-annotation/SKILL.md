---
name: "cell-type-annotation"
description: "scRNA-seq cell type annotation - read before any annotation skills. Chooses and runs the route: name clusters manually from canonical markers (scanpy, runnable code here), transfer labels with CellTypist or a popV/scANVI on a reference, or do both and validate one against other. Covers package availability, tissue- and state-matched references, marker panels, confidence and marker validation of transferred labels, doublets, unresolved clusters. Tool-specific code lives in celltypist/popv-cell-annotation and scvi-tools-single-cell."
license: "CC-BY-4.0"
---

# Single-Cell RNA-seq Cell Type Annotation

## Routes at a Glance

Choose the route; the tool skills hold the code for each automated route.

| Route | Fits when | Needs | In default sandbox | Code |
|-------|-----------|-------|--------------------|------|
| A. Manual markers | Well-characterized tissue, small dataset, or no reference matches tissue and state | `scanpy` | Installed | This skill, Workflow step 4 |
| B. CellTypist transfer | A pre-trained model matches tissue and state | `celltypist` | Installed | `celltypist-cell-annotation` |
| C. Ensemble transfer | You have labelled reference data | `popv` or `scvi-tools` | **Not installed** - install first | `popv-cell-annotation`, `scvi-tools-single-cell` |
| D. Both, compared, step-wise | Labels feed a biological claim; rare populations | A plus B or C | A + B installed | Workflow steps 4 and 7 |

Spatial data is not covered here: Xenium/MERFISH/CosMx cells go to
`spatial-transcriptomics-cell-type-annotation`, Visium spots to
`spatial-transcriptomics-deconvolution-cell2location`.

Ask the route as D2 in the Pre-flight Interview and say which routes run as-is:
route C needs `popv` or `scvi-tools` installed first.

## Overview

Cell type annotation is the process of assigning biological identities to computationally defined clusters in single-cell RNA-seq data. It is one of the most consequential analytical decisions in a scRNA-seq project: annotation errors propagate into downstream analyses of differential expression, trajectory inference, and cell-cell communication. This skill chooses among routes A-D above and holds the code for route A.

It synthesizes community know-how on CellTypist (Dominguez Conde et al., Science 2022), popV (Luecken et al., Nature Methods 2024), and classical marker-based approaches, following standards established by the Human Cell Atlas project.

Routes A to C run from effort-intensive but transparent (manual) to efficient and scalable (automated). They are not mutually exclusive: route D runs automated transfer to generate hypotheses and validates them with manual marker inspection. For high-stakes biological claims — rare cell types, novel disease states, clinical applications — use route D and resolve discordant labels explicitly before publication.

## Key Concepts

### Clusters Are Not Cell Types

Leiden/Louvain clusters group transcriptionally similar cells. One type can split
across clusters (over-clustering) or two can merge (under-clustering); annotate at
the resolution the question needs.

### Marker Evidence

The strongest evidence is a canonical marker that also ranks high in this dataset's
`rank_genes_groups`. Data-only markers are hypotheses; single-study markers are
supporting evidence. Require at least two co-expressed markers per type.

### Reference Match and Confidence

A reference or model is valid only for the tissue and state it was built from; a
mismatched one still labels every cell, confidently. Low-confidence cells flag novel
types, doublets, or transitional states - review them, do not accept the label.

### Label Vocabulary

Use Cell Ontology (CL) names and state the granularity (lineage, type, or state) so
labels compare across datasets.

## Pre-flight Interview

Settle these with the user before writing any analysis code. The Decision
Framework below explains the reasoning; this block is the machine-readable
form of it.

```yaml
decisions:
  - id: D1
    param: tissueContext
    kind: required
    source: user
    ask: "Which tissue, and in what state (healthy, fetal, diseased, cultured, perturbed)?"
    default: null

  - id: D2
    param: annotationStrategy
    kind: required
    source: user
    ask: "Markers (A), a CellTypist model (B), an ensemble on your labelled reference (C), or markers and transfer compared (D)?"
    default: null

  - id: D3
    param: referenceAtlas
    kind: optional
    source: literature
    ask: "Which model or reference matches this tissue and state?"
    default: "best match for the stated tissue and state, named inside the B/C/D route options"
    skip_if: "markers-only annotation"

  - id: D4
    param: markerPanel
    kind: optional
    source: literature
    ask: "Which canonical markers define the expected populations?"
    default: "agent-drafted panel for the tissue and state, listed in the plan"
    skip_if: "label transfer only"

  - id: D5
    param: markerValidation
    kind: optional
    source: user
    ask: "Check assigned labels against canonical markers before accepting them?"
    default: "checked"
    skip_if: "markers-only annotation"

  - id: D6
    param: labelGranularity
    kind: required
    source: user
    ask: "Name broad lineages, or subtypes and activation states within them?"
    default: null

  - id: D7
    param: unresolvedClusters
    kind: optional
    source: user
    ask: "What should happen to clusters that match no expected type - labelled by their top markers, left unassigned, or investigated as possible doublets or artefacts?"
    default: "left unassigned and reported"

  - id: D8
    param: doubletHandling
    kind: optional_conditional
    source: data
    ask: "Clusters co-express two lineages and no doublet flag exists - remove doublets before annotating?"
    default: "run Scrublet per sample when adata.obs has no doublet flag"
    skip_if: "adata.obs already carries a doublet flag from upstream QC"
```

Ask D1, D2 and D6 together in one round; none depends on another. Skip any
the request already answers. D3 and D4 are proposed, not asked: write the
matched model into the D2 options (e.g. "B. CellTypist `Immune_All_Low`") and
list the marker panel in the plan. Both are only valid for the tissue **and**
the state they were built from - an adult reference applied to fetal or tumour
tissue still labels every cell, confidently and wrongly - so check them
against D1 before proposing. D5 defaults to checked because transfer has no
way to say "these cells are not in my reference"; markers are what make that
visible.

`celltypist-cell-annotation` and `scanpy-scrna-seq` repeat the shared
decisions word for word, so the question survives whichever skill is read;
when several are read, ask each once.

## Decision Framework

When planning a cell type annotation strategy, choose the route based on dataset characteristics and scientific context:

```
Is the tissue and cell type composition well-characterized?
├── YES, standard tissue with clear markers (blood, lung, gut, brain)
│   ├── Dataset < 5,000 cells OR small team experiment
│   │   └── A: Manual marker-based annotation
│   │       (dotplot + violin + UMAP visualization)
│   └── Dataset ≥ 5,000 cells OR high-throughput study
│       ├── Standard tissue with pre-trained atlas available
│       │   └── B: CellTypist automated annotation
│       │       (select tissue-matched model, use majority_voting)
│       └── Need cross-atlas integration or rare cell types
│           └── C: popV ensemble label transfer
│               (requires reference AnnData + tissue label)
└── NO, novel tissue, disease state, or poorly characterized system
    ├── Reference atlas exists for related tissue
    │   └── C: popV ensemble label transfer
    │       (multiple methods + consensus = more robust)
    └── No good reference exists
        └── D: Manual annotation (cautious, exploratory)
            with CellTypist as validation
            (report as "putative" cell types, note limitations)
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Small dataset (<5,000 cells), well-characterized tissue | A: Manual markers | Automated tools provide marginal advantage; manual review is faster and more transparent |
| Large dataset (>50,000 cells), blood or immune tissue | B: CellTypist with Immune_All_High model | CellTypist has the most complete immune training data; scales without added complexity |
| Large dataset, lung or airway tissue | B: CellTypist with Human_Lung_Atlas model | HLCA-trained model provides granular lung-specific annotation |
| Novel disease condition or patient-derived samples | C: popV with tissue-matched reference | Ensemble consensus is more robust to distribution shift; produces a method-agreement score |
| Integration with published atlas (e.g., HLCA, HBA) | C: popV | Designed for atlas-query integration; maintains label ontology compatibility |
| Rare cell types (<1% of dataset) | D: popV + manual inspection | Rare populations benefit from multi-method ensemble; manual inspection catches misannotation |
| Fetal or developmental tissue | D: markers + popV with fetal reference | Fetal cell types are distinct from adult; use a matched fetal reference (Tabula Sapiens fetal) |
| Mixed or uncertain tissue composition | D: CellTypist, then marker validation | CellTypist provides a quick hypothesis; validate each predicted type with markers |
| Benchmark or methods comparison study | D: A, B and C in parallel | Triangulating annotation from multiple strategies increases credibility |

## Best Practices

1. **Remove doublets before annotation**: Scrublet or DoubletFinder should be applied as part of QC, before any clustering or annotation step. Doublets score high on gene count and UMI metrics. Annotating them produces hybrid "cell types" that confuse downstream analyses and inflate the apparent cell type diversity. Apply doublet detection, mark predicted doublets in `adata.obs`, and exclude them before proceeding to annotation.

2. **Visualize canonical markers after any automated annotation**: Automated tools, including CellTypist and popV, can be wrong. After obtaining automated labels, always inspect canonical marker expression using a dotplot (`sc.pl.dotplot`), violin plot (`sc.pl.violin`), or feature plot on UMAP (`sc.pl.umap`). If a population labeled "B cell" does not express MS4A1 and CD19, the label is suspect. This step takes 15–30 minutes and catches the most common annotation errors.

3. **Use multiple independent methods and compare consensus**: No single annotation method is universally superior. Comparing at least two methods (e.g., CellTypist and manual markers, or CellTypist and popV) builds confidence in labels where methods agree and flags cells requiring deeper inspection where they disagree. popV's built-in method-agreement score (number of methods that agree divided by total methods) directly quantifies this; a score below 0.5 suggests the cell may be a novel or ambiguous type.

4. **Select reference atlases that match tissue, species, and developmental stage**: The most common cause of poor label transfer is biological mismatch between query and reference. An adult lung query dataset should be annotated with an adult lung reference (HLCA), not a pan-tissue reference trained on different proportions of cell types. If the reference uses different developmental stage, health status, or sequencing technology, label transfer accuracy drops significantly. When no perfectly matched reference exists, use popV's ensemble, which is more tolerant of imperfect matches than single-method transfer.

5. **Check annotation confidence scores and flag low-confidence cells**: Both CellTypist (confidence score, 0–1) and popV (popv_score, fraction of methods agreeing) provide per-cell confidence metrics. Cells with CellTypist confidence below 0.5 or popV score below 0.5 should be flagged for manual review rather than automatically assigned a label. These cells often represent rare populations, transitional states, or doublets that passed the initial QC filter. Publishing results without confidence thresholds obscures annotation uncertainty.

6. **Correct for batch effects before reference-based annotation**: When query data contains multiple batches or samples, integrate them (Harmony, scVI, or BBKNN) before label transfer. Uncorrected batch effects create spurious cluster structure that cross-sample annotation methods cannot distinguish from true biology. Run batch correction → compute joint UMAP → apply annotation, not annotation → batch correction.

7. **Use tissue-specific resolution when constructing annotation hierarchy**: Cell type granularity should match the biological question. For a study of broad immune composition, major lineage labels (T cell, B cell, myeloid, NK) may suffice. For studies of T cell function, sub-type resolution (CD4 naive, CD4 Treg, CD8 effector, CD8 exhausted) is needed. Use Leiden clustering at multiple resolutions and annotate at the granularity appropriate for the question — not the maximum possible granularity.

8. **Iterate between clustering resolution and annotation**: Overclustering (too many clusters) creates redundant splits within a single cell type; underclustering merges distinct cell types. After initial annotation, if two clusters receive the same label from multiple methods, consider merging them. If a labeled cluster is heterogeneous on marker inspection, increase resolution and re-cluster. This iteration is normal and should be documented in the methods section.

## Common Pitfalls

1. **Annotating with a single marker gene per cell type**: Assigning "T cell" based solely on CD3E expression will misannotate cells that briefly co-express CD3E during differentiation, doublets of CD3E+ T cells with other cell types, or low-quality cells with ambient RNA contamination.
   - *How to avoid*: Always require at least two to three canonical markers to be co-expressed in the same cluster before assigning a label. Use a dotplot showing all markers simultaneously across all clusters; the combination of positive and negative markers (marker genes expressed versus absent) is more informative than any single marker alone.

2. **Skipping doublet removal before annotation**: Doublets containing, for example, a T cell and a B cell will express both CD3E and CD19. They form their own cluster and may be annotated as an unusual "co-expressing" cell type that does not exist biologically.
   - *How to avoid*: Run Scrublet (`scrub.scrub_doublets()`) or DoubletFinder immediately after QC filtering, before any normalization or clustering. Set the expected doublet rate to the multiplet rate reported by the 10x Genomics cell ranger summary (typically 1–4% per thousand cells loaded). Filter cells with `predicted_doublet == True` from `adata.obs` before proceeding.

3. **Using an atlas from a mismatched tissue or developmental stage**: Annotating adult colon cells with a fetal intestine reference, or annotating diseased tissue with a healthy tissue reference, produces systematic label transfer errors that can affect all clusters in the dataset.
   - *How to avoid*: Before selecting a reference, check its tissue of origin, developmental stage (fetal vs. adult), health status (normal vs. diseased), and species. Use the CellTypist model table (`celltypist.models.models_description()`) or the popV reference documentation to confirm match. If no matched reference exists, use route A (manual annotation) as the primary approach and flag the uncertainty.

4. **Ignoring batch effects that mimic cell type differences**: A dataset with two batches, one processed fresh and one processed after a freeze-thaw cycle, may show stress-responsive gene up-regulation in the freeze-thaw batch. These cells cluster separately and can be mistaken for a "stressed" or "activated" cell subtype.
   - *How to avoid*: Plot the UMAP colored by batch/sample before annotation. If cells segregate by batch rather than by biology, apply Harmony, scVI, or BBKNN batch correction before annotation. Check that canonical markers — not batch-related genes — drive cluster identity.

5. **Overclustering before annotation**: Running Leiden at resolution 3.0 on a dataset of 20,000 cells may produce 80 clusters, many of which represent the same cell type at different transcriptional states or are simply noise-driven splits. Annotating all 80 clusters is laborious and produces an illusion of biological diversity.
   - *How to avoid*: Start with a moderate Leiden resolution (0.5–1.0) and annotate broad lineages first. Apply CellTypist or popV at this coarser level. Only increase resolution for clusters of biological interest where finer distinctions matter. Use cluster-level consistency metrics — such as the silhouette score or within-cluster marker enrichment — to assess whether additional splits are biologically meaningful.

6. **Not checking for cell-cycle state as a confounding factor**: Rapidly dividing cells (in S or G2/M phase) can cluster separately from resting cells of the same type because proliferation-related genes (MKI67, TOP2A, PCNA) drive cluster identity rather than lineage markers.
   - *How to avoid*: Score each cell for S-phase and G2M-phase signatures using `sc.tl.score_genes_cell_cycle` with established gene lists. Visualize cell cycle scores on UMAP. If a cluster is primarily defined by proliferation genes, label it as "[Cell Type] proliferating" rather than treating it as a distinct lineage. Optionally, regress out cell cycle scores if you want clusters to reflect lineage rather than cell state.

7. **Failing to validate low-frequency automated predictions with marker evidence**: Some automated annotation tools produce plausible-sounding labels for every cell, even for rare populations with only 50–200 cells. Without marker validation, a CellTypist label of "plasmablast" for a small cluster cannot be trusted.
   - *How to avoid*: For any cluster containing fewer than 500 cells, perform manual marker validation regardless of automated confidence scores. Examine at least three canonical positive markers and confirm that two to three negative markers are absent. For very rare populations (< 0.5% of cells), consider whether the biological question requires this level of granularity before reporting.

## Workflow

1. **Quality control and preprocessing**:
   - Filter cells by minimum gene count, maximum gene count, and percent mitochondrial reads.
   - Remove ambient RNA using SoupX or CellBender if droplet-based data.
   - Normalize to 10,000 counts per cell and log1p-transform (`sc.pp.normalize_total`, `sc.pp.log1p`).
   - Identify highly variable genes (`sc.pp.highly_variable_genes`).
   - Run PCA on the HVG-subset expression matrix.
   - Decision point: If multiple batches are present, apply batch correction (Harmony, scVI, BBKNN) to the PCA embedding before computing the neighbor graph.

2. **Doublet detection**:
   - Run Scrublet on each sample independently before merging (not on the merged object).
   - Set expected doublet rate from the 10x cell ranger summary or the empirical rule of 0.8% per 1,000 cells loaded.
   - Store predicted doublet scores in `adata.obs["doublet_score"]` and boolean flags in `adata.obs["predicted_doublet"]`.
   - Remove predicted doublets before clustering and annotation.

3. **Clustering**:
   - Compute a k-nearest neighbor graph (`sc.pp.neighbors`, k=15–30).
   - Run UMAP for visualization (`sc.tl.umap`).
   - Apply Leiden clustering at an initial resolution of 0.5–1.0.
   - Decision point: If clusters fewer than expected for the tissue, increase resolution. If more clusters than anticipated, consider that overclustering has occurred.

4. **Route A — Manual marker-based annotation**:
   - Create a dotplot with top candidate markers for each expected cell type.
   - For each cluster, identify the marker gene set with highest dot size (fraction expressing) and dot color (mean expression).
   - Assign a provisional label based on co-expression of at least two canonical markers.
   - Flag clusters with ambiguous or mixed marker profiles for further scrutiny.

   ```python
   import numpy as np
   import pandas as pd
   import scanpy as sc

   # Panel settled in D4 for this tissue and state; example: adult human PBMC.
   marker_panel = {
       "CD4 T cell": ["CD3E", "CD4", "IL7R"],
       "CD8 T cell": ["CD3E", "CD8A", "GZMK"],
       "NK cell": ["NKG7", "GNLY", "KLRD1"],
       "B cell": ["CD19", "MS4A1", "CD79A"],
       "Classical monocyte": ["CD14", "S100A8", "LYZ"],
       "Non-classical monocyte": ["FCGR3A", "CX3CR1", "LST1"],
       "Dendritic cell": ["FCER1A", "CST3", "CD1C"],
   }
   # Keep types with at least two markers present in the data.
   panel = {ct: [g for g in genes if g in adata.var_names] for ct, genes in marker_panel.items()}
   panel = {ct: genes for ct, genes in panel.items() if len(genes) >= 2}
   sc.pl.dotplot(adata, var_names=panel, groupby="leiden", standard_scale="var", save="_marker_panel.png")

   # Score every cell per type, average per cluster, propose the best-scoring type.
   for ct, genes in panel.items():
       sc.tl.score_genes(adata, genes, score_name=f"score_{ct}")
   score_cols = [f"score_{ct}" for ct in panel]
   cluster_scores = adata.obs.groupby("leiden", observed=True)[score_cols].mean()
   ranked = np.sort(cluster_scores.to_numpy(), axis=1)
   proposal = pd.DataFrame({
       "proposed": cluster_scores.idxmax(axis=1).str.removeprefix("score_"),
       "top_score": ranked[:, -1],
       "margin": ranked[:, -1] - ranked[:, -2],
   }, index=cluster_scores.index)
   # D7: no positive signal or no clear winner -> left unresolved, not forced.
   proposal.loc[(proposal["top_score"] <= 0) | (proposal["margin"] < 0.1), "proposed"] = "Unresolved"
   print(proposal.sort_values("top_score", ascending=False))
   ```

   The proposal is a starting point. Confirm each cluster against the dotplot
   (positive markers present, negative markers absent), edit the mapping, then
   store it:

   ```python
   cluster_to_type = proposal["proposed"].to_dict()  # edit after dotplot review
   adata.obs["manual_cell_type"] = adata.obs["leiden"].map(cluster_to_type).astype("category")
   print(adata.obs["manual_cell_type"].value_counts())
   ```

5. **Route B — CellTypist automated annotation (if applicable; code in `celltypist-cell-annotation`)**:
   - Select the model matching the tissue from `celltypist.models.models_description()`.
   - Ensure input AnnData is log1p-normalized to 10,000 counts before running.
   - Run `celltypist.annotate(adata, model=model, majority_voting=True)`.
   - Store results in `adata.obs["celltypist_cell_type"]` and `adata.obs["celltypist_conf_score"]`.
   - Flag cells with confidence score below 0.5 for manual review.
   - Decision point: If > 20% of cells are low-confidence, consider whether a better-matched model exists or switch to route C.

6. **Route C — popV ensemble label transfer (if applicable; code in `popv-cell-annotation`)**:
   - Prepare a reference AnnData with column `cell_type` containing validated labels.
   - Ensure both query and reference contain raw count matrices in `adata.X`.
   - Run `popv.process_query(query_adata, ref_adata, ...)` and `popv.annotate_data(query_adata)`.
   - Store consensus labels in `adata.obs["popv_prediction"]` and agreement scores in `adata.obs["popv_score"]`.
   - Inspect the per-method label breakdown for cells with low agreement scores.

7. **Route D — Cross-validation and refinement**:
   - Compare route A labels with route B and/or C labels per cluster using a confusion matrix or sankey plot.
   - For clusters where all methods agree, assign the consensus label with high confidence.
   - For clusters where methods disagree, perform targeted marker visualization and assign a label based on biological reasoning.
   - Document discordant clusters and the evidence used to resolve them.

   ```python
   # Automated label column: "majority_voting" (CellTypist) or "popv_prediction" (popV).
   auto_col = "majority_voting"

   def cluster_summary(obs: pd.DataFrame) -> pd.Series:
       counts = obs[auto_col].value_counts(normalize=True)
       return pd.Series({
           "manual": obs["manual_cell_type"].iloc[0],
           "auto_top": counts.index[0],
           "auto_frac": round(counts.iloc[0], 2),
       })

   agreement = adata.obs.groupby("leiden", observed=True).apply(cluster_summary)
   print(agreement)  # label vocabularies differ: compare by meaning, not string equality

   # D5: do the transferred labels express the markers they claim?
   sc.pl.dotplot(adata, var_names=panel, groupby=auto_col, standard_scale="var", save="_auto_vs_markers.png")
   ```

8. **Final annotation and export**:
   - Write final cell type labels to `adata.obs["cell_type"]`.
   - Write the method behind each label to `adata.obs["annotation_method"]` (manual/celltypist/popv/manual_refined).
   - Export the annotated object as `.h5ad` for downstream analysis.
   - Prepare a supplementary table listing each cell type, the markers used to validate it, the annotation method, and the number of cells.

## Protocol Guidelines

1. **Canonical marker reference for common tissue types**: For blood and immune tissue, use CD3E/CD3D (T cells), CD4/FOXP3 (CD4 T/Tregs), CD8A (CD8 T), NKG7/GNLY (NK), CD19/MS4A1 (B cells), MZB1/JCHAIN (plasma), CD14/S100A8 (classical monocytes), FCGR3A (non-classical monocytes), FCER1A/CST3 (conventional dendritic cells), CLEC4C/IL3RA (plasmacytoid dendritic cells). For lung, add EPCAM/KRT18 (epithelial), PECAM1/VWF (endothelial), COL1A1/DCN (fibroblast), and SFTPC/SFTPB (alveolar type II epithelial).

2. **CellTypist model selection**: Match the model to the tissue. For immune datasets use `Immune_All_High_Resolution` or `Immune_All_Low_Resolution`. For lung use `Human_Lung_Atlas`. For gut use `Human_Colon_Cell_Atlas` or `Cells_of_the_Human_Intestine`. For fetal use `Fetal_Human_Pancreas` or the appropriate fetal model. Run `celltypist.models.models_description()` for the full list with tissue metadata.

3. **popV reference selection**: The Human Lung Cell Atlas (HLCA), Tabula Sapiens, and the Human BM Atlas are the most commonly used references. Download them as AnnData from CELLxGENE Census or Zenodo. Subset the reference to the tissue matching the query before running popV to reduce computation time and improve transfer specificity.

4. **Reporting annotation in publications**: Methods sections should specify: (a) software and version for each annotation tool used, (b) which markers were used for manual validation, (c) which CellTypist model was used, (d) which reference atlas was used for label transfer, (e) how discordant labels between methods were resolved, and (f) the confidence threshold applied to filter uncertain annotations. Failing to report these details makes annotation results non-reproducible.

5. **Marker gene reference table for common cell types**:

| Cell Type | Positive Markers | Negative Markers |
|-----------|-----------------|-----------------|
| CD4 T cell | CD3E, CD4, IL7R | CD8A, CD19, CD14 |
| CD8 T cell | CD3E, CD8A, GZMK | CD4, CD19, CD14 |
| NK cell | NKG7, GNLY, KLRB1 | CD3E, CD19, CD14 |
| B cell | CD19, MS4A1, CD79A | CD3E, CD14, NKG7 |
| Plasma cell | MZB1, JCHAIN, IGHG1 | CD19, CD3E, CD14 |
| Classical monocyte | CD14, S100A8, LYZ | CD3E, CD19, FCGR3A |
| Non-classical monocyte | FCGR3A, CX3CR1, LST1 | CD14, CD3E, CD19 |
| Conventional DC | FCER1A, CST3, CD1C | CD3E, CD19, CD14 |
| Plasmacytoid DC | CLEC4C, IL3RA, JCHAIN | CD3E, CD19, CD14 |
| Alveolar macrophage | MARCO, FABP4, PPARG | CD14, CD3E, CD19 |
| AT2 epithelial (lung) | SFTPC, SFTPB, LAMP3 | CD45/PTPRC, VWF |
| Endothelial cell | PECAM1, VWF, CDH5 | EPCAM, CD45/PTPRC |
| Fibroblast | COL1A1, DCN, PDGFRA | EPCAM, CD45/PTPRC |
| Epithelial cell | EPCAM, KRT18, CDH1 | CD45/PTPRC, VWF |

6. **Tools for annotation QC and inter-rater reliability**: When multiple annotators independently assign labels to the same dataset, measure agreement using Cohen's kappa or Fleiss' kappa. Agreement above 0.8 indicates high consistency; agreement below 0.6 suggests the markers or clustering resolution used are insufficient to distinguish the cell types in question. The scArches and scPhere frameworks provide additional tools for mapping query cells onto reference manifolds and quantifying mapping quality.

7. **Ambient RNA decontamination before annotation**: In droplet-based scRNA-seq, ambient RNA from lysed cells contaminates all droplets. This means cells that do not express a marker gene may appear to express it at low levels due to contamination. Tools such as SoupX or CellBender estimate and remove ambient RNA contamination. Running decontamination before annotation reduces false-positive marker signals that can cause misannotation, particularly for rare cell types whose canonical markers appear as low-level "contamination" in neighboring clusters.

8. **Cell type composition as a sanity check**: After annotation, the expected proportion of each cell type should be biologically plausible. For a peripheral blood mononuclear cell (PBMC) dataset, expect 50–70% T cells, 10–15% B cells, 10–20% monocytes, and 5–10% NK cells. If annotation yields 90% monocytes in a PBMC sample, the annotation is almost certainly wrong. Compare proportions against published reference ranges for the tissue and experimental condition.

## Further Reading

- [CellTypist documentation and model zoo](https://www.celltypist.org/) — Official documentation, pre-trained model list with tissue annotations, and tutorials for automated cell type annotation with majority voting
- [popV GitHub repository](https://github.com/YosefLab/popV) — Installation, usage examples, and reference to the Luecken et al. 2024 Nature Methods benchmarking paper
- [Human Cell Atlas Data Portal](https://www.humancellatlas.org/) — Curated single-cell reference atlases for dozens of tissues across development and disease; source of reference data for label transfer
- [Dominguez Conde et al. Science 2022](https://doi.org/10.1126/science.abl5197) — CellTypist paper describing the pan-immune atlas and the logistic regression classifier; cite when using CellTypist
- [Luecken et al. Nature Methods 2024](https://doi.org/10.1038/s41592-024-02249-2) — popV benchmarking study comparing 10 annotation methods across 8 datasets; provides empirical guidance on method selection
- [Scanpy documentation: Clustering and annotation](https://scanpy.readthedocs.io/en/stable/tutorials/basics/clustering.html) — Official Scanpy tutorial for the full QC→preprocessing→clustering→annotation workflow
- [Best Practices for Single-Cell Analysis (Heumos et al., Nature Reviews Genetics 2023)](https://doi.org/10.1038/s41576-023-00586-w) — Community best-practices review covering all steps of scRNA-seq analysis including annotation; recommended as a primary reference for study design

## Related Skills

- `scanpy-scrna-seq` — Full scRNA-seq analysis pipeline in Scanpy covering QC, normalization, clustering, and basic marker-based annotation; use as the computational foundation before applying this guide's annotation strategy
- `celltypist-cell-annotation` — Route B automated annotation tool using pre-trained logistic regression models for 100+ cell types across blood, lung, gut, brain, and other tissues
- `popv-cell-annotation` — Route C ensemble label transfer tool using 10+ methods with majority voting; use for robust annotation of novel or heterogeneous datasets
- `scvi-tools-single-cell` — Deep generative models for batch correction (scVI) and semi-supervised annotation (scANVI); use scANVI as an alternative to popV for joint integration and annotation
- `harmony-batch-correction` — Batch correction for PCA embeddings; apply before annotation when integrating samples from multiple donors or processing batches
- `anndata-data-structure` — Core data container for all scRNA-seq analysis; required for understanding how annotations are stored and propagated in AnnData objects
- `cellxgene-census` — Source of large curated reference atlases (Human Cell Atlas, Tabula Sapiens) for use as label transfer references in popV workflows
- `muon-multiomics-singlecell` — Multi-modal single-cell analysis; annotation of multi-omics data (RNA+ATAC, CITE-seq) requires considering the additional modalities as supplementary evidence
- `mofaplus-multi-omics` — Multi-omics factor analysis; latent factors from MOFA+ can inform cell state annotation when transcriptional signatures are not sufficient
- `cellchat-cell-communication` — Downstream analysis of annotated single-cell data; ligand-receptor interaction inference depends entirely on having accurate cell type labels from annotation
