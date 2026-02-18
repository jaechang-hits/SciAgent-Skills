---
name: "single-cell-annotation-guide"
description: "Decision framework for choosing between manual marker-based, automated (CellTypist), and reference-based (popV) cell type annotation strategies in single-cell RNA-seq analysis. Covers a three-tier strategy: Tier 1 (manual canonical markers), Tier 2 (CellTypist pre-trained models), and Tier 3 (popV ensemble label transfer). Use when planning or troubleshooting cell type annotation in any scRNA-seq project."
license: "CC-BY-4.0"
---

# Single-Cell RNA-seq Cell Type Annotation Guide

## Overview

Cell type annotation is the process of assigning biological identities to computationally defined clusters in single-cell RNA-seq data. It is one of the most consequential analytical decisions in a scRNA-seq project: annotation errors propagate into downstream analyses of differential expression, trajectory inference, and cell-cell communication. This guide presents a three-tier decision strategy — manual marker-based annotation first, automated reference-free classification second, and ensemble reference-based label transfer third — and explains when each approach is most appropriate.

The guide synthesizes community know-how on CellTypist (Dominguez Conde et al., Science 2022), popV (Luecken et al., Nature Methods 2024), and classical marker-based approaches, following standards established by the Human Cell Atlas project.

The three tiers represent a progression from effort-intensive but transparent (manual) to efficient and scalable (automated). They are not mutually exclusive: best practice is to run automated annotation first to generate hypotheses and then validate with manual marker inspection. For high-stakes biological claims — rare cell types, novel disease states, clinical applications — all three tiers should be used in parallel and discordant results resolved explicitly before publication.

## Key Concepts

### Cell Type Markers and Cluster Identity

A cell type marker is a gene whose expression distinguishes one cell population from all others in a dataset. Canonical markers are those validated across many studies and tissues — for example, CD3E for T cells, CD19 and MS4A1 (CD20) for B cells, CD14 for classical monocytes, and EPCAM for epithelial cells. Effective markers fulfill three criteria: they are highly expressed in the target cell type (high sensitivity), they are absent or very low in all other cell types (high specificity), and their identity is confirmed by at least two independent markers.

Clusters produced by algorithms such as Leiden or Louvain represent groups of transcriptionally similar cells; they do not inherently correspond to biological cell types. A single true cell type may appear as multiple clusters if the resolution parameter is too high (overclustering), and biologically distinct cell types may be merged if resolution is too low. Annotation quality depends on both the quality of the clustering and the quality of the evidence used to assign identities.

### Reference Atlases and Label Transfer

Reference atlases are large, curated scRNA-seq datasets with expert-validated cell type labels that serve as a "ground truth" for annotation of new query datasets. Prominent examples include the Human Cell Atlas (HCA), the Human Lung Cell Atlas (HLCA, 2.4M cells), Tabula Sapiens (500K cells across 28 tissues), and the Human BM Atlas for bone marrow. Label transfer is the computational process of projecting query cells onto the reference space and assigning labels based on proximity.

Label transfer quality depends critically on biological match between query and reference. Adult tissue query data annotated with a fetal reference will produce systematic errors for cell types that differ between developmental stages. Similarly, a blood-derived reference will poorly annotate tumor-infiltrating immune cells, which have altered transcriptional programs compared to their circulating counterparts.

### Annotation Confidence and Validation

Automated annotation tools produce confidence scores (probability or agreement rate) that quantify the certainty of each cell's label. These scores should never be ignored. Cells with low confidence scores may represent novel cell types absent from the reference, doublets (two cells captured together), or transitional states along a differentiation continuum.

Validation refers to verifying that automated labels are consistent with independent biological evidence — typically canonical marker gene expression. Even when an automated method reports high confidence, a few minutes spent visualizing marker genes in a UMAP or dotplot is essential to catch systematic misannotations, especially for rare or disease-specific cell populations absent from training data.

### Doublets and Technical Artifacts

Doublets are droplets containing two or more cells, which appear as a single cell with an anomalously high gene count and mixed transcriptional identity. Annotating doublets before removing them produces spurious "cell types" that combine markers from two real populations (e.g., an apparent NK-B cell hybrid). Tools such as Scrublet and DoubletFinder should be applied before annotation; doublets should be marked and excluded from the annotation workflow.

Batch effects — systematic technical differences between samples processed at different times, with different reagents, or on different platforms — can mimic cell type differences. If one batch contains more stressed cells (higher stress gene expression), they may cluster separately and be misannotated as a distinct cell type. Batch correction with Harmony, scVI, or BBKNN should be applied before annotation when multiple batches are present.

### Cell Ontology and Annotation Hierarchies

Cell ontologies are formal vocabularies that define cell type names, synonyms, and parent-child relationships. The Cell Ontology (CL), maintained by the OBO Foundry, is the standard used by the Human Cell Atlas and most major atlases. Using ontology-compliant cell type names (e.g., "CD8-positive, alpha-beta T cell" rather than "CD8 T cell") enables cross-dataset comparison and interoperability. CellTypist and popV return labels that map to the Cell Ontology when tissue-matched models are used.

Annotation hierarchies reflect that cell identities exist at multiple levels of granularity. At the coarsest level, cells are classified as broad lineages (immune, epithelial, stromal). At intermediate granularity, they are classified as cell types (T cell, B cell, macrophage). At the finest granularity, they are classified as cell states or subtypes (exhausted CD8 T cell, tissue-resident memory T cell, M1 macrophage). Choosing the right granularity for an annotation depends on the biological question and the depth of sequencing: underpowered studies should not attempt fine-grained annotation.

### Marker Gene Evidence Categories

Marker gene evidence is not all equally reliable. Evidence categories, from most to least reliable, are:

1. **Canonical published markers**: Genes with decades of protein-level validation, e.g., CD3 protein expression for T cells, CD19 for B cells.
2. **Computationally derived cluster-specific markers**: Genes found by differential expression between clusters in your dataset using `sc.tl.rank_genes_groups`. These are hypothesis-generating and require biological interpretation.
3. **Cross-validated markers**: Genes that are canonical and also appear as top markers from `rank_genes_groups` in your dataset. This is the strongest evidence — it means the marker's biology is reflected in your actual data.
4. **Single-study markers**: Genes described as markers in a single publication but not yet widely replicated. These should be treated as supporting evidence, not definitive.

When building a marker panel for annotation, prioritize cross-validated markers (Category 3) and use canonical published markers (Category 1) as anchors.

## Decision Framework

When planning a cell type annotation strategy, choose the tier based on dataset characteristics and scientific context:

```
Is the tissue and cell type composition well-characterized?
├── YES, standard tissue with clear markers (blood, lung, gut, brain)
│   ├── Dataset < 5,000 cells OR small team experiment
│   │   └── Tier 1: Manual marker-based annotation
│   │       (dotplot + violin + UMAP visualization)
│   └── Dataset ≥ 5,000 cells OR high-throughput study
│       ├── Standard tissue with pre-trained atlas available
│       │   └── Tier 2: CellTypist automated annotation
│       │       (select tissue-matched model, use majority_voting)
│       └── Need cross-atlas integration or rare cell types
│           └── Tier 3: popV ensemble label transfer
│               (requires reference AnnData + tissue label)
└── NO, novel tissue, disease state, or poorly characterized system
    ├── Reference atlas exists for related tissue
    │   └── Tier 3: popV ensemble label transfer
    │       (multiple methods + consensus = more robust)
    └── No good reference exists
        └── Tier 1: Manual annotation (cautious, exploratory)
            + Tier 2: CellTypist as validation
            (report as "putative" cell types, note limitations)
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Small dataset (<5,000 cells), well-characterized tissue | Tier 1: Manual markers | Automated tools provide marginal advantage; manual review is faster and more transparent |
| Large dataset (>50,000 cells), blood or immune tissue | Tier 2: CellTypist with Immune_All_High model | CellTypist has the most complete immune training data; scales without added complexity |
| Large dataset, lung or airway tissue | Tier 2: CellTypist with Human_Lung_Atlas model | HLCA-trained model provides granular lung-specific annotation |
| Novel disease condition or patient-derived samples | Tier 3: popV with tissue-matched reference | Ensemble consensus is more robust to distribution shift; produces a method-agreement score |
| Integration with published atlas (e.g., HLCA, HBA) | Tier 3: popV | Designed for atlas-query integration; maintains label ontology compatibility |
| Rare cell types (<1% of dataset) | Tier 3: popV + manual inspection | Rare populations benefit from multi-method ensemble; manual inspection catches misannotation |
| Fetal or developmental tissue | Tier 1 + Tier 3 with fetal reference | Fetal cell types are distinct from adult; use a matched fetal reference (Tabula Sapiens fetal) |
| Mixed or uncertain tissue composition | Tier 2 (CellTypist) then Tier 1 validation | CellTypist provides a quick hypothesis; validate each predicted type with markers |
| Benchmark or methods comparison study | All three tiers in parallel | Triangulating annotation from multiple strategies increases credibility |

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
   - *How to avoid*: Before selecting a reference, check its tissue of origin, developmental stage (fetal vs. adult), health status (normal vs. diseased), and species. Use the CellTypist model table (`celltypist.models.models_description()`) or the popV reference documentation to confirm match. If no matched reference exists, use Tier 1 manual annotation as the primary approach and flag the uncertainty.

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

4. **Tier 1 — Manual marker-based annotation**:
   - Create a dotplot with top candidate markers for each expected cell type.
   - For each cluster, identify the marker gene set with highest dot size (fraction expressing) and dot color (mean expression).
   - Assign a provisional label based on co-expression of at least two canonical markers.
   - Flag clusters with ambiguous or mixed marker profiles for further scrutiny.

5. **Tier 2 — CellTypist automated annotation (if applicable)**:
   - Select the model matching the tissue from `celltypist.models.models_description()`.
   - Ensure input AnnData is log1p-normalized to 10,000 counts before running.
   - Run `celltypist.annotate(adata, model=model, majority_voting=True)`.
   - Store results in `adata.obs["celltypist_cell_type"]` and `adata.obs["celltypist_conf_score"]`.
   - Flag cells with confidence score below 0.5 for manual review.
   - Decision point: If > 20% of cells are low-confidence, consider whether a better-matched model exists or switch to Tier 3.

6. **Tier 3 — popV ensemble label transfer (if applicable)**:
   - Prepare a reference AnnData with column `cell_type` containing validated labels.
   - Ensure both query and reference contain raw count matrices in `adata.X`.
   - Run `popv.process_query(query_adata, ref_adata, ...)` and `popv.annotate_data(query_adata)`.
   - Store consensus labels in `adata.obs["popv_prediction"]` and agreement scores in `adata.obs["popv_score"]`.
   - Inspect the per-method label breakdown for cells with low agreement scores.

7. **Cross-validation and refinement**:
   - Compare Tier 1, Tier 2, and Tier 3 labels per cluster using a confusion matrix or sankey plot.
   - For clusters where all methods agree, assign the consensus label with high confidence.
   - For clusters where methods disagree, perform targeted marker visualization and assign a label based on biological reasoning.
   - Document discordant clusters and the evidence used to resolve them.

8. **Final annotation and export**:
   - Write final cell type labels to `adata.obs["cell_type"]`.
   - Write annotation confidence tier to `adata.obs["annotation_method"]` (manual/celltypist/popv/manual_refined).
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
- `celltypist-cell-annotation` — Tier 2 automated annotation tool using pre-trained logistic regression models for 100+ cell types across blood, lung, gut, brain, and other tissues
- `popv-cell-annotation` — Tier 3 ensemble label transfer tool using 10+ methods with majority voting; use for robust annotation of novel or heterogeneous datasets
- `scvi-tools-single-cell` — Deep generative models for batch correction (scVI) and semi-supervised annotation (scANVI); use scANVI as an alternative to popV for joint integration and annotation
- `harmony-batch-correction` — Batch correction for PCA embeddings; apply before annotation when integrating samples from multiple donors or processing batches
- `anndata-data-structure` — Core data container for all scRNA-seq analysis; required for understanding how annotations are stored and propagated in AnnData objects
- `cellxgene-census` — Source of large curated reference atlases (Human Cell Atlas, Tabula Sapiens) for use as label transfer references in popV workflows
- `muon-multiomics-singlecell` — Multi-modal single-cell analysis; annotation of multi-omics data (RNA+ATAC, CITE-seq) requires considering the additional modalities as supplementary evidence
- `mofaplus-multi-omics` — Multi-omics factor analysis; latent factors from MOFA+ can inform cell state annotation when transcriptional signatures are not sufficient
- `cellchat-cell-communication` — Downstream analysis of annotated single-cell data; ligand-receptor interaction inference depends entirely on having accurate cell type labels from annotation
