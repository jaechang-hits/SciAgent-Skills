---
name: "cellchat-cell-communication"
description: "Infer and visualize intercellular communication from scRNA-seq with CellChat (R). Build CellChat from Seurat/counts → subset CellChatDB ligand-receptor pairs → over-expressed genes per group → communication probabilities → pathway signaling → network centrality (senders/receivers/influencers) → chord/heatmap/bubble plots → cross-condition compare. Human, mouse. Use liana for pure-Python."
license: "MIT"
---

# CellChat — Cell-Cell Communication Analysis

## Overview

CellChat is an R package that infers and visualizes intercellular signaling networks from single-cell RNA-seq data. Starting from a normalized expression matrix and cluster labels, CellChat identifies ligand-receptor interactions supported by CellChatDB — a manually curated database of over 2,000 validated ligand-receptor pairs in human and mouse. Communication probability is modeled using the law of mass action, combining expression levels of ligands, receptors, and cofactors. CellChat aggregates pair-level probabilities into pathway-level signaling networks and quantifies each cell group's role as a signal sender, receiver, mediator, or influencer. The result is a rich, interpretable picture of which cell types talk to which, through which signaling pathways, and how these patterns change between conditions.

## When to Use

- Characterizing which cell types are the dominant senders or receivers of paracrine and autocrine signals in a tissue atlas or disease sample
- Identifying specific ligand-receptor pairs mediating communication between a cell population of interest (e.g., tumor cells → T cells, fibroblasts → epithelial cells)
- Comparing intercellular signaling networks between two conditions (e.g., healthy vs. diseased, treatment vs. control) to find rewired or lost communication
- Discovering pathway-level signaling programs (e.g., MHC-II, COLLAGEN, VEGF) enriched in a particular cell-cell interaction
- Prioritizing targets for perturbation experiments by ranking signaling pathways by their aggregate communication strength or network centrality
- Use **liana** (Python/R) instead when you want a pure-Python workflow or a consensus ranking across multiple ligand-receptor databases (CellChat, CellPhoneDB, Connectome, NicheNet)
- Use **NicheNet** (R) instead when you need ligand-to-target gene regulatory inference — predicting which ligands from sender cells regulate which target genes in receiver cells

## Prerequisites

- **R packages**: `CellChat` (>= 2.0), `Seurat` (>= 4.0, for Seurat-based input), `NMF`, `ggplot2`, `ggalluvial`, `igraph`, `dplyr`, `patchwork`, `reticulate` (optional)
- **Data requirements**: Normalized scRNA-seq count matrix (genes × cells) and a cell group identity vector (cluster labels or cell types). Raw counts are acceptable if normalized inside CellChat.
- **Species**: CellChatDB available for human and mouse; other species require custom database construction
- **Memory**: 8 GB RAM minimum for datasets with 10,000–50,000 cells; 32 GB+ recommended for larger datasets

```r
# Install CellChat from GitHub (CRAN version may lag)
if (!requireNamespace("BiocManager", quietly = TRUE))
  install.packages("BiocManager")
BiocManager::install(c("BiocNeighbors", "ComplexHeatmap"))

install.packages("devtools")
devtools::install_github("jinworks/CellChat")

# Core dependencies
install.packages(c("NMF", "ggplot2", "ggalluvial", "igraph",
                   "dplyr", "patchwork", "circlize", "RColorBrewer"))
```

## Quick Start

```r
library(CellChat)
library(Seurat)

# Assume `seurat_obj` is a processed Seurat object with cell type identities in Idents()
data.input <- GetAssayData(seurat_obj, assay = "RNA", slot = "data")  # normalized counts
meta       <- data.frame(labels = Idents(seurat_obj), row.names = names(Idents(seurat_obj)))

cellchat <- createCellChat(object = data.input, meta = meta, group.by = "labels")
cellchat@DB <- CellChatDB.human  # or CellChatDB.mouse

cellchat <- subsetData(cellchat)
cellchat <- identifyOverExpressedGenes(cellchat)
cellchat <- identifyOverExpressedInteractions(cellchat)
cellchat <- computeCommunProb(cellchat, type = "triMean")
cellchat <- filterCommunication(cellchat, min.cells = 10)
cellchat <- computeCommunProbPathway(cellchat)
cellchat <- aggregateNet(cellchat)

# Quick summary
print(cellchat)
# e.g. "An object of class CellChat created from a single dataset
#  with 8 cell groups and 312 inferred ligand-receptor pairs"
```

## Workflow

### Step 1: Create CellChat Object

Build a CellChat object from either a Seurat object or a raw count matrix with accompanying metadata.

```r
library(CellChat)
library(Seurat)

# --- Option A: from a Seurat object ---
# seurat_obj must have cell type identities set with Idents() or in meta.data
data.input <- GetAssayData(seurat_obj, assay = "RNA", slot = "data")  # log-normalized
meta <- data.frame(
  labels = Idents(seurat_obj),
  row.names = colnames(seurat_obj)
)
cellchat <- createCellChat(object = data.input, meta = meta, group.by = "labels")

# --- Option B: from a count matrix directly ---
# data.input: genes-by-cells normalized matrix (dgCMatrix or dense matrix)
# identity: named factor of cell group labels (length = ncol(data.input))
cellchat <- createCellChat(object = data.input, meta = data.frame(labels = identity),
                           group.by = "labels")

cat("Cell groups:", levels(cellchat@idents), "\n")
cat("Number of cells:", ncol(data.input), "\n")
# Cell groups: B_cell Endothelial Fibroblast Macrophage NK T_cell Tumor
# Number of cells: 12847
```

### Step 2: Set CellChatDB and Subset Interactions

Load the species-appropriate ligand-receptor database and optionally subset to a signaling category of interest.

```r
# Load database for the appropriate species
CellChatDB <- CellChatDB.human   # use CellChatDB.mouse for mouse data

# Inspect available signaling categories
unique(CellChatDB$interaction$annotation)
# [1] "Secreted Signaling"    "ECM-Receptor"          "Cell-Cell Contact"

# Option 1: Use all interactions (recommended for discovery)
cellchat@DB <- CellChatDB

# Option 2: Subset to secreted ligand-receptor pairs only (reduces noise)
CellChatDB.use <- subsetDB(CellChatDB, search = "Secreted Signaling",
                           key = "annotation")
cellchat@DB <- CellChatDB.use

# Subset the CellChat data slots to only genes in the database
cellchat <- subsetData(cellchat)
cat("Genes retained after database subset:", nrow(cellchat@data.signaling), "\n")
# Genes retained after database subset: 1842
```

### Step 3: Identify Over-Expressed Genes and Interactions

For each cell group, identify ligands and receptors that are significantly over-expressed compared to other groups.

```r
# Identify over-expressed genes per cell group (uses Seurat-style wilcoxon test)
cellchat <- identifyOverExpressedGenes(cellchat)

# Map over-expressed genes to ligand-receptor pairs in CellChatDB
cellchat <- identifyOverExpressedInteractions(cellchat)

# Inspect how many interactions were identified per group pair
df.net <- subsetCommunication(cellchat)
cat("Total inferred interactions:", nrow(df.net), "\n")
head(df.net[, c("source", "target", "ligand", "receptor", "prob")], 5)
#      source   target  ligand receptor      prob
# 1   B_cell Macrophage  CD22     PTPRC 0.0318
# 2 Fibroblast    Tumor   FN1     CD44  0.1072
# ...
```

### Step 4: Infer Cell-Cell Communication Probabilities

Compute communication probability for each ligand-receptor pair between every ordered pair of cell groups using the law of mass action. CellChat accounts for multi-subunit complexes and co-stimulatory/co-inhibitory cofactors.

```r
# Compute pairwise communication probability
# type = "triMean": uses 25th percentile × mean × 25th percentile for robustness
# type = "truncatedMean": uses trimmed mean with threshold parameter trim
cellchat <- computeCommunProb(
  cellchat,
  type          = "triMean",   # recommended default
  trim          = 0.1,         # fraction to trim (only used if type="truncatedMean")
  nboot         = 100,         # bootstrap iterations for p-value estimation
  seed.use      = 42,
  population.size = TRUE       # weight by population size (recommended)
)

# Filter out interactions with too few cells in sender or receiver groups
cellchat <- filterCommunication(cellchat, min.cells = 10)

# Summary of retained interactions
df.net <- subsetCommunication(cellchat)
cat("Interactions after filtering:", nrow(df.net), "\n")
cat("Significant interactions (p<0.05):", sum(df.net$pval < 0.05), "\n")
# Interactions after filtering: 247
# Significant interactions (p<0.05): 189
```

### Step 5: Compute Pathway-Level Communication

Aggregate ligand-receptor pair probabilities into signaling pathway-level networks (e.g., COLLAGEN, MHC-II, VEGF).

```r
# Aggregate to pathway level
cellchat <- computeCommunProbPathway(cellchat)

# Build aggregate interaction count and weight networks
cellchat <- aggregateNet(cellchat)

# View significant pathways
cat("Significant signaling pathways:\n")
print(cellchat@netP$pathways)
# [1] "MHC-II"    "COLLAGEN"  "FN1"       "VEGF"      "CXCL"
# [6] "CCL"       "MIF"       "APP"       "GALECTIN"  ...

# Extract pathway-level communication probabilities between groups
df.pathways <- subsetCommunication(cellchat, slot.name = "netP")
head(df.pathways[, c("source", "target", "pathway_name", "prob")], 5)
#        source    target pathway_name     prob
# 1  Fibroblast     Tumor     COLLAGEN   0.2341
# 2  Macrophage  Fibroblast     MIF    0.1876
# ...
```

### Step 6: Analyze Network Centrality — Senders, Receivers, Influencers

Identify each cell group's network role by computing information flow measures: out-strength (sender), in-strength (receiver), betweenness (mediator), and eigenvector centrality (influencer).

```r
# Compute centrality measures for all pathways
cellchat <- netAnalysis_computeCentrality(cellchat, slot.name = "netP")

# Visualize centrality scores as a heatmap (rows=pathways, cols=cell groups)
# Each dot size: outgoing signal strength; color: incoming signal strength
netAnalysis_signalingRole_heatmap(
  cellchat,
  pattern    = "all",     # "outgoing", "incoming", or "all"
  signaling  = NULL,      # NULL = all pathways; or specify e.g. c("COLLAGEN","VEGF")
  height     = 10,
  color.heatmap = "OrRd"
)

# Identify dominant communication patterns using NMF
# outgoing patterns reveal which cell groups co-activate similar pathways
library(NMF)
selectK(cellchat, pattern = "outgoing")    # elbow plot to choose K
cellchat <- identifyCommunicationPatterns(
  cellchat,
  pattern = "outgoing",
  k       = 3,            # number of latent patterns; choose from selectK elbow
  width   = 8,
  height  = 6
)
```

### Step 7: Visualize — Chord Diagrams, Heatmaps, Bubble Plots

CellChat provides several visualization functions for both aggregate and pathway-specific interactions.

```r
library(ggplot2)
library(patchwork)

# --- 7a. Chord diagram: aggregate interaction count and weight ---
par(mfrow = c(1, 2))
netVisual_circle(
  cellchat@net$count,
  vertex.weight = as.numeric(table(cellchat@idents)),
  weight.scale  = TRUE,
  label.edge    = FALSE,
  title.name    = "Number of interactions"
)
netVisual_circle(
  cellchat@net$weight,
  vertex.weight = as.numeric(table(cellchat@idents)),
  weight.scale  = TRUE,
  label.edge    = FALSE,
  title.name    = "Interaction strength"
)

# --- 7b. Heatmap: cell-group × cell-group interaction matrix ---
p1 <- netVisual_heatmap(cellchat, measure = "count",  color.heatmap = "Blues")
p2 <- netVisual_heatmap(cellchat, measure = "weight", color.heatmap = "Reds")
p1 + p2

# --- 7c. Chord diagram for a specific pathway ---
netVisual_aggregate(
  cellchat,
  signaling      = "COLLAGEN",
  layout         = "chord",
  vertex.receiver = NULL   # NULL = show all groups as receivers
)

# --- 7d. Bubble plot: all significant interactions for chosen pathways ---
netVisual_bubble(
  cellchat,
  sources.use = NULL,   # NULL = all senders
  targets.use = NULL,   # NULL = all receivers
  signaling   = c("COLLAGEN", "MIF", "VEGF"),
  remove.isolate = FALSE
)
ggsave("bubble_plot_selected_pathways.pdf", width = 10, height = 8)
```

### Step 8: Compare Two CellChat Objects Across Conditions

When you have two conditions (e.g., healthy and diseased), merge the CellChat objects and compare signaling networks.

```r
# Assume cellchat_ctrl and cellchat_disease are pre-computed CellChat objects
object.list <- list(Control = cellchat_ctrl, Disease = cellchat_disease)
cellchat_merged <- mergeCellChat(object.list, add.names = names(object.list))

# --- Compare total interaction count and strength ---
compareInteractions(cellchat_merged, show.legend = FALSE,
                    group = c(1, 2), measure = "count")
compareInteractions(cellchat_merged, show.legend = FALSE,
                    group = c(1, 2), measure = "weight")

# --- Differential interaction chord diagram (gained/lost connections) ---
netVisual_diffInteraction(cellchat_merged, weight.scale = TRUE)

# --- Identify signaling pathways specific to each condition ---
rankNet(cellchat_merged, mode = "comparison", stacked = TRUE, do.stat = TRUE)

# --- Scatter plot: pathways shifted in information flow ---
rankNetPairwise(
  cellchat_merged,
  comparison = c(1, 2),
  slot.name  = "netP",
  measure    = "prob"
)
```

## Key Parameters

| Parameter | Function | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `type` | `computeCommunProb` | `"triMean"` | `"triMean"`, `"truncatedMean"`, `"thresholdedMean"`, `"median"` | Aggregation method for group-level expression; `triMean` is most stringent |
| `trim` | `computeCommunProb` | `0.1` | `0`–`0.25` | Fraction trimmed from each tail; only applies when `type="truncatedMean"` |
| `nboot` | `computeCommunProb` | `100` | `50`–`1000` | Bootstrap iterations for p-value estimation; higher = slower but more accurate |
| `population.size` | `computeCommunProb` | `TRUE` | `TRUE`, `FALSE` | Weight communication probability by cell group size; recommended for heterogeneous data |
| `min.cells` | `filterCommunication` | `10` | `5`–`50` | Minimum number of cells required per sender or receiver group to retain an interaction |
| `k` | `identifyCommunicationPatterns` | required | `2`–`6` (choose via `selectK`) | Number of latent communication patterns; use `selectK` elbow to select |
| `thresh` | `netAnalysis_computeCentrality` | `0.05` | `0.01`–`0.1` | P-value cutoff for retaining interactions in centrality analysis |
| `sources.use` | `netVisual_bubble` | `NULL` | cell group name(s) or index | Restrict sender cell groups in bubble plot; `NULL` = all |
| `targets.use` | `netVisual_bubble` | `NULL` | cell group name(s) or index | Restrict receiver cell groups in bubble plot; `NULL` = all |

## Key Concepts

### Communication Probability Model

CellChat quantifies communication probability using the law of mass action. For a ligand L expressed in cell group A and receptor R (potentially a multi-subunit complex) expressed in cell group B:

```
P(A → B | L-R) = hill(expr_L_A) × hill(expr_R1_B) × hill(expr_R2_B) × ...
```

where `hill(x) = x^n / (K^n + x^n)` (Hill function, n=1 by default), and expression values are group-aggregated using the chosen `type` argument. Multi-subunit receptor complexes require all subunits to be expressed; the probability is the product of Hill-transformed subunit expressions.

### CellChatDB Ligand-Receptor Database

CellChatDB is a curated database of experimentally validated ligand-receptor interactions organized into three categories:

```r
# Inspect the database structure
dim(CellChatDB.human$interaction)   # [1] 2293   17
head(CellChatDB.human$interaction[, c("interaction_name", "pathway_name",
                                       "ligand", "receptor", "annotation")], 4)
#   interaction_name pathway_name ligand receptor          annotation
# 1         TGFB1_TGFBR1_TGFBR2         TGFb  TGFB1  TGFBR1_TGFBR2  Secreted Signaling
# 2          WNT5A_FZD1_LRP5          WNT   WNT5A     FZD1_LRP5   Secreted Signaling
# 3             FN1_CD44             FN1    FN1      CD44        ECM-Receptor
# 4          NOTCH1_DLL4        NOTCH  NOTCH1       DLL4   Cell-Cell Contact
```

Three categories cover distinct biological mechanisms:
- **Secreted Signaling**: classical paracrine/autocrine ligands (cytokines, growth factors, morphogens)
- **ECM-Receptor**: extracellular matrix components binding membrane receptors
- **Cell-Cell Contact**: juxtacrine signals requiring direct cell contact (Notch, Ephrin, Semaphorin)

### Network Centrality Roles

| Role | Centrality Measure | Interpretation |
|------|--------------------|----------------|
| **Sender** | Out-degree / out-strength | Cell groups that broadcast signals to many targets |
| **Receiver** | In-degree / in-strength | Cell groups that receive signals from many sources |
| **Mediator** | Betweenness centrality | Cell groups that bridge communication between other groups |
| **Influencer** | Eigenvector centrality | Cell groups connected to other highly-connected groups |

### Information Flow vs. Interaction Count

`aggregateNet` computes two complementary matrices:
- `cellchat@net$count`: number of statistically significant ligand-receptor pairs per cell-group pair (raw interaction count)
- `cellchat@net$weight`: sum of communication probabilities across all pairs (interaction strength / information flow)

High count with low weight indicates many weak interactions; high weight with low count indicates a few dominant pathways.

## Common Recipes

### Recipe: Extract All Significant Interactions as a Data Frame

Use when you want to export results, apply custom filtering, or feed interactions into downstream pathway analysis.

```r
# All ligand-receptor level interactions (p < 0.05)
df.lr <- subsetCommunication(cellchat, slot.name = "net")
df.lr_sig <- df.lr[df.lr$pval < 0.05, ]
cat("Significant LR interactions:", nrow(df.lr_sig), "\n")

# All pathway-level interactions
df.path <- subsetCommunication(cellchat, slot.name = "netP")

# Interactions involving specific cell groups
df.tumor_recv <- subsetCommunication(cellchat,
                                      targets.use = "Tumor",
                                      slot.name   = "net")
cat("Interactions targeting Tumor cells:", nrow(df.tumor_recv), "\n")

# Save to CSV for downstream analysis
write.csv(df.lr_sig,    "cellchat_lr_interactions.csv",    row.names = FALSE)
write.csv(df.path,      "cellchat_pathway_interactions.csv", row.names = FALSE)
write.csv(df.tumor_recv, "cellchat_tumor_receivers.csv",   row.names = FALSE)
```

### Recipe: Visualize Signaling Role of a Specific Pathway

Use when you want a detailed view of which cell types send and receive via one pathway.

```r
# Show chord diagram + violin plots for a single pathway
pathway <- "COLLAGEN"

# Chord diagram
netVisual_aggregate(cellchat, signaling = pathway, layout = "chord")
title(main = paste0(pathway, " signaling network"))

# Contribution of each LR pair to the pathway
netAnalysis_contribution(cellchat, signaling = pathway)

# Gene expression of constituent ligands and receptors
plotGeneExpression(
  cellchat,
  signaling  = pathway,
  enriched.only = TRUE,     # show only significantly enriched genes
  type       = "violin"
)
```

### Recipe: Save and Reload a CellChat Object

Use when checkpointing a completed run before visualization or comparison steps.

```r
# Save the completed CellChat object
saveRDS(cellchat, file = "cellchat_analysis.rds")
cat("Saved to cellchat_analysis.rds\n")

# Reload and resume analysis
cellchat_loaded <- readRDS("cellchat_analysis.rds")
cat("Cell groups:", levels(cellchat_loaded@idents), "\n")
cat("Pathways:", length(cellchat_loaded@netP$pathways), "\n")

# Verify the object is complete
slotNames(cellchat_loaded)
# [1] "data"          "data.signaling" "images"        "net"
# [5] "netP"          "meta"           "idents"        "var.features"
# [9] "DB"            "LR"             "options"
```

### Recipe: Python-Equivalent Workflow with liana

Use when your pipeline is Python-based or you want a consensus ranking across multiple LR databases.

```python
# Install: pip install liana
import liana
import scanpy as sc
import pandas as pd

# Load preprocessed AnnData (cells x genes, log-normalized)
adata = sc.read_h5ad("my_scrna.h5ad")
# adata.obs["celltype"] must contain cluster/cell-type labels

# Run liana with CellChat resource (consensus across CellChatDB, CellPhoneDB, NATMI, etc.)
liana.mt.rank_aggregate(
    adata,
    groupby   = "celltype",
    resource_name = "consensus",   # or "cellchat" for CellChat-only LR pairs
    expr_prop = 0.1,               # min fraction cells expressing ligand/receptor
    verbose   = True
)

# Results stored in adata.uns["liana_res"]
df = adata.uns["liana_res"]
df_sig = df[df["magnitude_rank"] < 0.05].sort_values("magnitude_rank")
print(df_sig[["source", "target", "ligand_complex", "receptor_complex",
              "magnitude_rank"]].head(10))
df_sig.to_csv("liana_interactions.csv", index=False)
```

## Expected Outputs

| Output | Type | Description |
|--------|------|-------------|
| `cellchat@net$count` | R matrix (n_groups × n_groups) | Number of significant LR interactions between each cell-group pair |
| `cellchat@net$weight` | R matrix (n_groups × n_groups) | Aggregate communication probability (information flow) between cell-group pairs |
| `cellchat@netP$pathways` | Character vector | Names of all inferred signaling pathways |
| `subsetCommunication(cellchat)` | data.frame | Table of all LR-level interactions with source, target, ligand, receptor, probability, p-value |
| `subsetCommunication(cellchat, slot.name="netP")` | data.frame | Pathway-level interaction table |
| Chord diagram (PDF/PNG) | Figure | Circular diagram showing interaction strength between cell groups |
| Heatmap (PDF/PNG) | Figure | Cell-group × cell-group interaction count or weight heatmap |
| Bubble plot (PDF/PNG) | Figure | Dot plot showing interaction probabilities per LR pair per group pair |
| Signaling role heatmap (PDF/PNG) | Figure | Pathway × cell-group centrality scores (sender/receiver roles) |

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `Error in computeCommunProb: all probabilities are zero` | Genes in CellChatDB not detected or filtered out | Confirm `subsetData()` retains genes: `nrow(cellchat@data.signaling) > 0`; check that expression matrix is log-normalized (not raw counts) and that gene names match CellChatDB (human: HGNC symbols; mouse: MGI symbols) |
| Warning: `groups with fewer than min.cells cells are removed` | Small clusters dropped at filtering step | Lower `min.cells` in `filterCommunication()` (e.g., `min.cells = 5`) or merge rare clusters before creating the CellChat object |
| `identifyCommunicationPatterns` NMF error or no convergence | Number of patterns `k` too high or data too sparse | Use `selectK()` to choose k from the elbow in cophenetic/dispersion curves; try `k=2` or `k=3` first |
| Memory error / session crash during `computeCommunProb` | Dataset too large for available RAM | Subsample to ≤30,000 cells per condition; or run `computeCommunProb` with `nboot = 50` to reduce bootstrap memory footprint |
| Chord diagram is unreadable (too many cell groups) | Many fine-grained clusters | Aggregate clusters into broader categories before creating CellChat object; or use `netVisual_heatmap` which scales better with many groups |
| `mergeCellChat` error: cell group labels do not match | Cell type names differ between objects | Harmonize `levels(cellchat_ctrl@idents)` and `levels(cellchat_disease@idents)` before merging; use `setIdent()` to rename groups |
| Gene symbols not recognized (all probabilities 0) | Mixed human/mouse gene naming convention | Confirm species: human genes are ALL CAPS (e.g., `TGFB1`); mouse genes are title case (e.g., `Tgfb1`). Set `CellChatDB.mouse` for mouse data |

## References

- [CellChat GitHub — jinworks/CellChat](https://github.com/jinworks/CellChat) — source code, tutorials, and vignettes
- [CellChat vignette (HTML)](https://htmlpreview.github.io/?https://github.com/jinworks/CellChat/blob/master/tutorial/CellChat-vignette.html) — official step-by-step tutorial
- [Jin et al. (2021) Nature Communications — CellChat original paper](https://doi.org/10.1038/s41467-021-21246-9) — algorithmic description, benchmarking, and case studies
- [CellChat comparison vignette](https://htmlpreview.github.io/?https://github.com/jinworks/CellChat/blob/master/tutorial/CellChat_comparison_with_different_databases.html) — comparing CellChatDB with CellPhoneDB and other databases
- [liana Python package documentation](https://liana-py.readthedocs.io/) — pure-Python alternative with consensus LR ranking across CellChat, CellPhoneDB, NATMI, and Connectome
