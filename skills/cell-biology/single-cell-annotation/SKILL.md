---
name: single-cell-annotation
description: "Guide to annotating cell types in scRNA-seq. Covers manual marker-based, automated (CellTypist, scAnnotate), and reference-based (scArches, Azimuth, SingleR) approaches with a decision framework. Markers for blood/immune, epithelial, stromal lineages; validation and pitfalls. See scanpy-scrna-seq (prep), celltypist-cell-annotation (auto), scvi-tools (DL transfer)."
license: CC-BY-4.0
---

# Single Cell RNA-seq Cell Type Annotation

## Overview

Cell type annotation is the process of assigning biological identity labels to clusters or individual cells in single-cell RNA-seq data. Accurate annotation is a prerequisite for virtually all downstream analyses -- differential expression, trajectory inference, cell-cell communication, and compositional analysis all depend on correct cell type labels.

This guide covers three complementary approaches (manual marker-based, automated classification, and reference-based label transfer), provides a decision framework for selecting the right tool, and documents key marker genes and validation strategies. It is intended for researchers who have already completed preprocessing (filtering, normalization, dimensionality reduction, clustering) and need to assign biological meaning to their clusters.

## Key Concepts

### Three Annotation Approaches

**Manual marker-based annotation** identifies cell types by examining expression of known marker genes in each cluster. This approach uses tools such as Scanpy or Seurat and is best suited for small datasets, novel cell types, or situations requiring high confidence. It demands domain expertise but offers the most interpretable results.

**Automated annotation** uses pre-trained classifiers (CellTypist, scAnnotate) to assign cell type labels without manual curation. This is best for standard tissues, quick preliminary annotation, and large datasets where manual review of every cluster is impractical. Automated tools differ in their model architectures, training data, and granularity of predictions -- selecting the right model for your tissue context is essential.

**Reference-based label transfer** maps labels from a well-annotated reference dataset to query data using methods such as scArches, scANVI, Azimuth, or SingleR. This works well for well-characterized tissues and leverages the investment in public atlas projects such as the Human Cell Atlas and Tabula Muris. The quality of transferred labels depends heavily on the similarity between the reference and query datasets.

### Key Marker Genes by Cell Type

Marker genes are the foundation of manual annotation and serve as validation anchors for automated methods. The following are widely accepted markers for major lineages.

**Blood/Immune:**
- **T cells**: CD3D, CD3E (pan-T); CD4, CD8A (subtypes)
- **B cells**: CD19, MS4A1 (CD20), CD79A
- **Monocytes/Macrophages**: CD14, CD68, LYZ
- **NK cells**: NCAM1 (CD56), NKG7, KLRD1
- **Dendritic cells**: FCER1A, CD1C

**Epithelial:**
- **General epithelial**: EPCAM, KRT18, KRT19
- **Lung AT1**: AGER, PDPN
- **Lung AT2**: SFTPC, SFTPA1
- **Intestinal**: VIL1, MUC2

**Stromal:**
- **Fibroblasts**: COL1A1, DCN, LUM
- **Endothelial**: PECAM1 (CD31), VWF, CDH5
- **Smooth muscle**: ACTA2, MYH11, TAGLN

### Annotation Confidence and Hierarchical Labeling

Cell type annotation should be performed hierarchically: assign broad categories first (e.g., immune vs. stromal vs. epithelial), then refine to subtypes (e.g., CD4+ T cells, CD8+ T cells). This reduces error propagation and makes uncertain assignments easier to manage. Confidence levels should be documented for each annotation -- high confidence when multiple markers agree across methods, low confidence when only a single method or marker supports the label.

A practical confidence scale:
- **High**: 3+ canonical markers enriched, automated and manual methods agree, expected proportions for tissue
- **Medium**: 1-2 markers enriched, partial method agreement, or unusual proportions that are biologically plausible
- **Low**: Weak marker expression, methods disagree, or cluster may represent a technical artifact

### Cell States vs. Cell Types

A critical distinction in annotation is between cell types (lineage-defined identities) and cell states (transient functional programs within a type). For example, naive CD4+ T cells and activated CD4+ T cells are the same cell type in different states. Mixing states and types in the same annotation column inflates apparent diversity and confuses downstream analysis. Best practice is to annotate cell type and cell state in separate metadata columns, using lineage markers for type and activation/proliferation signatures for state.

## Decision Framework

When selecting an annotation approach and tool:

```
Question: What type of tissue/cells are you annotating?
├── Human immune cells
│   ├── Dataset > 100k cells → CellTypist (fast, atlas-trained)
│   └── Dataset < 100k cells → CellTypist + manual marker validation
├── Mouse tissues
│   └── Reference atlas available → scArches + Mouse Cell Atlas
├── Novel/rare cell types
│   └── No reference available → Manual annotation with Scanpy/Seurat
├── Developmental data
│   └── Continuous cell states → scArches (handles trajectories)
└── Cross-species comparison
    └── Limited reference transfer → Manual markers only
```

| Scenario | Recommended Tool | Rationale |
|----------|------------------|-----------|
| Human immune cells | CellTypist | Pre-trained on large immune atlases with fine-grained cell types |
| Mouse tissues | scArches + Mouse Cell Atlas | Comprehensive mouse reference with broad tissue coverage |
| Novel cell types | Manual + Scanpy/Seurat | Requires domain expertise; no pre-trained model available |
| Large datasets (>100k cells) | CellTypist | Scales efficiently; majority voting improves cluster labels |
| Cross-species analysis | Manual markers | Reference transfer across species is unreliable |
| Developmental data | scArches | Handles continuous states and transitional populations |
| Quick preliminary scan | CellTypist | Fast turnaround for initial assessment before deep analysis |
| Multi-tissue atlas project | Azimuth + manual | Azimuth provides consistent labels across tissues; manual review catches tissue-specific subtypes |
| Cancer/tumor samples | Manual + SingleR | Tumor heterogeneity requires careful manual curation; SingleR provides cell-by-cell scores |

**General strategy**: Start with automated annotation (CellTypist or Azimuth) for a rapid first pass, then validate and refine with manual marker inspection. Use reference-based transfer when a high-quality, tissue-matched atlas is available. Always treat automated labels as hypotheses to be confirmed, not final answers.

## Best Practices

1. **Combine multiple annotation approaches**: Never rely on a single method. Use automated tools for initial labeling, then validate with known marker genes. Cross-method agreement is the strongest evidence for correct annotation.

2. **Perform quality control before annotation**: Remove low-quality cells, detect doublets (expected rate: ~0.8% per 1,000 cells captured), and check for ambient RNA contamination before assigning labels. Annotating noisy data propagates errors downstream.

3. **Annotate hierarchically**: Start with broad lineage assignments (immune, epithelial, stromal), then refine to subtypes. This catches gross errors early and provides a fallback when fine-grained annotation is uncertain.

4. **Validate with multiple marker sets**: Do not rely on a single gene to define a cell type. Require co-expression of 2-3 canonical markers and check that the top differentially expressed genes for each cluster match expected biology.

5. **Consider biological context**: The same marker gene can indicate different cell types in different tissues (e.g., EPCAM marks epithelial cells broadly but is also expressed in some tumor contexts). Always interpret markers in the context of tissue type, disease state, and developmental stage.

6. **Document confidence levels**: Record which annotations are high-confidence (multiple methods agree, strong markers) versus uncertain (single method, weak markers, small cluster). This transparency helps downstream analysts make informed decisions.

7. **Use a validation checklist**: Systematically verify cluster purity (>80% cells with same label), marker consistency, biological plausibility of cell type proportions, cross-method agreement, and absence of multi-lineage doublet signatures.

## Common Pitfalls

1. **Doublet clusters masquerading as novel cell types**: Clusters expressing markers from two distinct lineages (e.g., T cell + monocyte markers) are usually doublets, not real biological populations.
   - *How to avoid*: Run doublet detection tools (Scrublet, DoubletFinder) before annotation. Flag any cluster with strong markers from multiple lineages for manual review.

2. **Ambient RNA contamination inflating marker expression**: Background mRNA from lysed cells causes low-level expression of abundant genes (e.g., hemoglobin, albumin) across all clusters, leading to false positive marker hits.
   - *How to avoid*: Apply decontamination tools (SoupX, CellBender) before annotation. Be suspicious of markers that appear at uniformly low levels across all clusters rather than being enriched in specific clusters.

3. **Over-clustering creating artificial cell type distinctions**: Setting clustering resolution too high splits genuine cell types into multiple clusters that differ only by technical noise or cell cycle phase, not by biology.
   - *How to avoid*: Start with moderate resolution and increase only if clusters show clearly distinct marker profiles. Merge clusters that share the same top markers. Test multiple resolutions and compare results.

4. **Reference mismatch degrading label transfer accuracy**: Using a reference dataset from a different tissue, species, or condition leads to poor label transfer because the reference does not contain the cell types present in the query.
   - *How to avoid*: Always verify that the reference covers the expected cell types. Check gene overlap between reference and query. Use tissue-matched references and inspect transferred label confidence scores.

5. **Confusing cell states with cell types**: Activated vs. resting T cells, or proliferating vs. quiescent fibroblasts, represent different states of the same cell type -- not distinct cell types. Labeling them as separate types inflates the cell type count.
   - *How to avoid*: Distinguish activation/proliferation signatures (e.g., MKI67, cell cycle genes) from lineage-defining markers. Annotate the base cell type first, then add state annotations as a separate metadata column.

6. **Over-interpreting small clusters without validation**: Clusters with fewer than 25 cells may represent technical artifacts, residual doublets, or sampling noise rather than genuine rare populations.
   - *How to avoid*: Require a minimum cell count threshold. Validate rare populations with independent data or orthogonal methods (e.g., flow cytometry, spatial transcriptomics). Check whether the cluster persists across biological replicates.

7. **Ignoring batch effects before annotation**: Uncorrected batch effects can cause cells of the same type to cluster separately by batch, leading to redundant or inconsistent annotations.
   - *How to avoid*: Apply batch correction (Harmony, scVI, BBKNN) before clustering and annotation. Verify that clusters contain cells from multiple batches where expected.

## Workflow

1. **Step 1: Quality control and preprocessing**
   - Filter low-quality cells (low gene count, high mitochondrial fraction)
   - Detect and remove doublets with Scrublet or DoubletFinder
   - Apply ambient RNA correction with SoupX or CellBender if needed
   - Normalize and log-transform the data
   - Decision point: If data contains multiple batches, apply batch correction before proceeding

2. **Step 2: Initial marker-based assessment**
   - Cluster the data at moderate resolution
   - Compute differentially expressed genes per cluster
   - Visualize known markers to assign broad lineage labels

   ```python
   import scanpy as sc

   # Calculate marker genes for clusters
   sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')

   # Visualize top markers
   sc.pl.rank_genes_groups(adata, n_genes=25, sharey=False)

   # Plot known markers
   markers = {
       'T cells': ['CD3D', 'CD3E', 'CD4', 'CD8A'],
       'B cells': ['CD19', 'MS4A1', 'CD79A'],
       'Monocytes': ['CD14', 'FCGR3A', 'LYZ'],
       'NK cells': ['NCAM1', 'NKG7', 'GNLY']
   }

   sc.pl.dotplot(adata, markers, groupby='leiden')
   ```

3. **Step 3: Automated annotation for validation**
   - Run CellTypist or another automated tool on the preprocessed data
   - Compare automated labels with manual marker-based assignments
   - Investigate discrepancies between methods

   ```python
   # CellTypist example (fast, accurate for immune cells)
   import celltypist
   from celltypist import models

   # Download immune cell model
   model = models.Model.load(model='Immune_All_Low.pkl')

   # Predict cell types
   predictions = celltypist.annotate(adata, model=model, majority_voting=True)
   adata = predictions.to_adata()
   ```

4. **Step 4: Reference-based refinement**
   - Select a tissue-matched reference dataset
   - Transfer labels using scArches, Azimuth, or SingleR
   - Check confidence scores and flag low-confidence transfers

   ```python
   # scArches example for label transfer
   import scarches as sca

   # Load pre-trained reference model
   model = sca.models.SCANVI.load_query_data(
       adata=adata,  # Your query data
       reference_model="path/to/reference_model"
   )

   # Transfer labels
   model.train(max_epochs=100)
   adata.obs['transferred_labels'] = model.predict()
   ```

5. **Step 5: Consensus and validation**
   - Compare labels from all three approaches
   - Resolve conflicts by examining markers and cluster composition
   - Apply the validation checklist:
     - Cluster purity: >80% cells with same label per cluster
     - Marker consistency: top DE genes match expected markers
     - Biological plausibility: expected proportions for tissue type
     - Cross-method agreement: manual and automated annotations align
     - Reference quality: >70% cells successfully transferred
     - Doublet check: no clusters with multi-lineage markers
   - Document confidence levels and record uncertain calls

6. **Step 6: Troubleshooting**
   - If all clusters look similar: increase clustering resolution, verify normalization
   - If too many small clusters: decrease resolution, merge similar clusters based on shared markers
   - If automated tools give inconsistent results: check input normalization requirements, try multiple tools, fall back to manual annotation
   - If no clear markers for a cluster: consider transitional state, residual doublets, or low-quality cells
   - If reference transfer fails: check batch correction, ensure overlapping gene sets, verify tissue match
   - If cell type proportions seem implausible: compare against published atlases for the same tissue; consider whether dissociation protocols may have depleted fragile cell types
   - If a known cell type is missing: check whether it was filtered during QC or merged into an adjacent cluster at the current resolution

## Validation Checklist

Use this checklist after completing annotation to verify quality before proceeding to downstream analysis:

- [ ] **Cluster purity**: >80% of cells in each cluster share the same label
- [ ] **Marker consistency**: Top differentially expressed genes per cluster match expected canonical markers for the assigned cell type
- [ ] **Biological plausibility**: Cell type proportions are reasonable for the tissue (e.g., immune cells dominate in PBMC, epithelial cells dominate in gut)
- [ ] **Cross-method agreement**: Manual marker-based and automated annotations converge on the same labels for the majority of clusters
- [ ] **Reference transfer quality**: >70% of cells receive high-confidence transferred labels when using reference-based methods
- [ ] **Doublet exclusion**: No remaining clusters show multi-lineage marker expression patterns
- [ ] **Batch balance**: Each cluster contains cells from multiple batches (where expected), confirming that annotations are not driven by batch effects
- [ ] **Documentation**: Confidence levels recorded, uncertain annotations flagged, and methodology documented for reproducibility

## Further Reading

- [Scanpy documentation -- Clustering and annotation](https://scanpy.readthedocs.io/en/stable/tutorials.html) -- Official tutorials covering preprocessing, clustering, marker gene analysis, and visualization for cell type annotation
- [Dominguez Conde, C. et al. (2022). Cross-tissue immune cell analysis reveals tissue-specific features in humans. Science, 376(6594)](https://doi.org/10.1126/science.abl5197) -- CellTypist paper describing the automated annotation framework and cross-tissue immune cell models
- [Luecken, M.D. & Theis, F.J. (2019). Current best practices in single-cell RNA-seq analysis: a tutorial. Molecular Systems Biology, 15(6)](https://doi.org/10.15252/msb.20188746) -- Comprehensive best practices review covering the full single-cell analysis pipeline including annotation strategies
- [Lotfollahi, M. et al. (2022). Mapping single-cell data to reference atlases by transfer learning. Nature Biotechnology, 40](https://doi.org/10.1038/s41587-021-01001-7) -- scArches paper on reference-based label transfer using architectural surgery for deep learning models
- [Pasquini, G. et al. (2021). Automated methods for cell type annotation on scRNA-seq data. Computational and Structural Biotechnology Journal, 19](https://doi.org/10.1016/j.csbj.2021.01.015) -- Comparative review of automated cell type annotation methods with benchmarking across datasets

## Related Skills

- `scanpy-scrna-seq` -- Preprocessing pipeline for single-cell RNA-seq data; provides the clustering and marker gene analysis used in manual annotation
- `celltypist-cell-annotation` -- Dedicated automated cell type annotation tool; implements the automated classification approach described in this guide
- `scvi-tools-single-cell` -- Deep learning framework for single-cell analysis including scANVI for semi-supervised label transfer and scVI for batch integration prior to annotation
