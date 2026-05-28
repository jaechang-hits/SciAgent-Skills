---
name: "deseq2-differential-expression"
description: "Bulk RNA-seq DE with R/Bioconductor DESeq2. Negative binomial GLM, empirical Bayes shrinkage, Wald/LRT tests, multi-factor designs, Salmon tximeta import, apeglm LFC shrinkage, MA/volcano/heatmap viz. R gold standard. Use pydeseq2-differential-expression for Python; use edgeR for TMM normalization."
license: "LGPL-3.0"
---

# DESeq2 Differential Expression Analysis (R/Bioconductor)

## Overview

DESeq2 is the Bioconductor R package for differential gene expression analysis from bulk RNA-seq count data. It fits a negative binomial generalized linear model per gene, estimates dispersion parameters using empirical Bayes shrinkage across genes, and tests differential expression using Wald tests (two-group) or likelihood ratio tests (complex designs). DESeq2 is the R gold standard for RNA-seq DE analysis, with native Bioconductor integration for seamless import from Salmon (tximeta/tximport), featureCounts, or HTSeq.

## When to Use

- Identifying differentially expressed genes between two experimental conditions (treated vs. control, disease vs. healthy) from bulk RNA-seq count data
- Analyzing multi-factor designs that account for batch effects or covariates (e.g., `~ batch + condition`)
- Testing complex hypotheses with interaction terms (e.g., time × treatment) or reduced models using likelihood ratio tests (LRT)
- Importing Salmon pseudoalignment output via tximeta or tximport for transcript-level uncertainty propagation
- Performing LFC shrinkage with apeglm for ranked gene lists, volcano plots, and downstream pathway analysis
- Conducting time-series experiments or any design with more than two levels requiring model comparison
- Working in an R/Bioconductor ecosystem where integration with SummarizedExperiment, clusterProfiler, or EnhancedVolcano is needed
- Use **pydeseq2-differential-expression** instead for Python-based pipelines with the same statistical model
- Use **edgeR** for negative binomial DE with TMM normalization, quasi-likelihood F-tests, or TREAT testing
- Use **gseapy-gene-enrichment** after DE to interpret results at the pathway level

## Prerequisites

- **R packages**: `DESeq2` (Bioconductor), `tximeta` or `tximport` (Salmon import), `apeglm` (LFC shrinkage), `pheatmap`, `ggplot2`, `EnhancedVolcano`
- **Data requirements**: Raw (unnormalized) integer count matrix — gene rows × sample columns — plus a sample metadata data frame with matching column names. If using Salmon: per-sample `quant.sf` files and a transcript-to-gene mapping
- **Environment**: R ≥ 4.2, Bioconductor ≥ 3.16

```r
# Install Bioconductor packages
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

BiocManager::install(c("DESeq2", "tximeta", "tximport", "apeglm",
                        "EnhancedVolcano"))
install.packages(c("pheatmap", "ggplot2", "dplyr"))
```

## Quick Start

Complete two-group comparison from a count matrix in under 20 lines.

```r
library(DESeq2)

# Load count matrix (genes x samples) and metadata
counts <- as.matrix(read.csv("counts.csv", row.names = 1))
coldata <- read.csv("metadata.csv", row.names = 1)
coldata$condition <- factor(coldata$condition)

# Build DESeqDataSet, run full pipeline
dds <- DESeqDataSetFromMatrix(countData = counts,
                               colData   = coldata,
                               design    = ~ condition)
dds <- dds[rowSums(counts(dds)) >= 10, ]   # pre-filter
dds <- DESeq(dds)

# Extract results (treated vs. control)
res <- results(dds, contrast = c("condition", "treated", "control"),
               alpha = 0.05)
summary(res)
# LFC shrinkage for visualization
res_shrunk <- lfcShrink(dds, contrast = c("condition", "treated", "control"),
                         type = "apeglm", coef = 2)
```

## Workflow

### Step 1: Prepare Count Matrix and Sample Metadata

Build a `DESeqDataSet` from a gene × sample count matrix and a colData data frame. Column names of the count matrix must match row names of colData.

```r
library(DESeq2)
library(dplyr)

# Load raw count matrix (genes as rows, samples as columns)
counts <- as.matrix(read.csv("featureCounts_matrix.csv", row.names = 1))
# Or from featureCounts tab-delimited output — skip first comment line
# fc <- read.table("featurecounts_output.txt", header = TRUE, skip = 1, row.names = 1)
# counts <- as.matrix(fc[, 7:ncol(fc)])  # columns 7+ are sample counts

# Load sample metadata
coldata <- data.frame(
    condition = factor(c("control", "control", "control",
                          "treated", "treated", "treated")),
    batch     = factor(c("A", "A", "B", "A", "B", "B")),
    row.names = colnames(counts)
)

# Build DESeqDataSet
dds <- DESeqDataSetFromMatrix(countData = counts,
                               colData   = coldata,
                               design    = ~ condition)

cat("Samples:", ncol(dds), "\n")
cat("Genes:", nrow(dds), "\n")
cat("Condition levels:", levels(coldata$condition), "\n")
```

### Step 2: Import from Salmon via tximeta

When reads were quantified with Salmon, use `tximeta` to import transcript-level estimates with proper offset correction that accounts for transcript length and GC bias.

```r
library(tximeta)

# Build a coldata with a "files" column pointing to quant.sf files
quant_dirs <- file.path("salmon_output", coldata$sample_id, "quant.sf")
coldata$files <- quant_dirs
coldata$names <- coldata$sample_id

# Import with tximeta — automatically fetches transcript metadata from Ensembl
se <- tximeta(coldata)           # SummarizedExperiment with transcript-level data

# Summarize to gene level (requires Ensembl or custom txdb)
gse <- summarizeToGene(se)       # gene-level SummarizedExperiment

# Build DESeqDataSet from the SummarizedExperiment
dds <- DESeqDataSet(gse, design = ~ condition)

cat("Gene-level SE dimensions:", dim(gse), "\n")
cat("Assay names:", assayNames(gse), "\n")
# Assay "counts" = estimated counts; "abundance" = TPM; "length" = eff. lengths
```

### Step 3: Pre-Filtering and Quality Control

Remove genes with very low counts to improve statistical power and reduce the multiple testing burden. Explore sample quality with PCA on variance-stabilized counts.

```r
library(ggplot2)

# Pre-filter: keep genes with at least 10 reads total
keep <- rowSums(counts(dds)) >= 10
dds <- dds[keep, ]
cat("Genes after pre-filtering:", nrow(dds), "\n")

# Variance-stabilizing transformation for QC visualization
vsd <- vst(dds, blind = TRUE)    # blind = TRUE for exploratory QC

# PCA plot
pca_data <- plotPCA(vsd, intgroup = c("condition", "batch"), returnData = TRUE)
percent_var <- round(100 * attr(pca_data, "percentVar"))

ggplot(pca_data, aes(PC1, PC2, color = condition, shape = batch)) +
    geom_point(size = 3) +
    xlab(paste0("PC1: ", percent_var[1], "% variance")) +
    ylab(paste0("PC2: ", percent_var[2], "% variance")) +
    ggtitle("PCA — Variance-Stabilized Counts") +
    theme_bw()

ggsave("pca_plot.pdf", width = 6, height = 5)
cat("Saved pca_plot.pdf\n")
```

### Step 4: Run DESeq() — Normalization, Dispersion, and Model Fitting

`DESeq()` runs three sequential steps: (1) median-of-ratios size factor estimation, (2) gene-wise and shrunken dispersion estimation, (3) negative binomial GLM fitting and Wald statistics.

```r
# Run full DESeq2 pipeline
dds <- DESeq(dds)

# Inspect size factors (library normalization)
cat("Size factors:\n")
print(sizeFactors(dds))
# Expected range: 0.3–3.0; outliers indicate library quality issues

# Dispersion plot — should show decreasing dispersion trend with mean
plotDispEsts(dds, main = "Dispersion Estimates")

# Inspect fitted model coefficients
resultsNames(dds)
# [1] "Intercept" "condition_treated_vs_control"
```

### Step 5: Extract Results and Apply FDR Correction

Use `results()` to extract Wald test statistics. Specify the contrast explicitly for clarity. Independent filtering maximizes the number of detectable genes.

```r
# Extract results for the contrast of interest
res <- results(dds,
               contrast          = c("condition", "treated", "control"),
               alpha             = 0.05,   # FDR threshold for independent filtering
               lfcThreshold      = 0,      # Test H0: |LFC| = 0 (Wald test)
               independentFilter = TRUE)   # Maximize power via adaptive filtering

# Summary: how many genes are up/down/NA
summary(res)
# out of N with nonzero total read count:
# adjusted p-value < 0.05: ...
# LFC > 0 (up): ...
# LFC < 0 (down): ...
# outliers [Cook's distance]: ...
# low counts [below independent filtering threshold]: ...

# Convert to data frame and sort by adjusted p-value
res_df <- as.data.frame(res)
res_df <- res_df[order(res_df$padj, na.last = TRUE), ]

cat("Significant genes (padj < 0.05):", sum(res_df$padj < 0.05, na.rm = TRUE), "\n")
cat("Upregulated:", sum(res_df$padj < 0.05 & res_df$log2FoldChange > 0, na.rm = TRUE), "\n")
cat("Downregulated:", sum(res_df$padj < 0.05 & res_df$log2FoldChange < 0, na.rm = TRUE), "\n")

write.csv(res_df, "deseq2_all_results.csv")
```

### Step 6: LFC Shrinkage with apeglm

Shrink log2 fold changes using the adaptive t prior (apeglm). Use shrunk LFCs for MA plots, volcano plots, and gene ranking — NOT for significance calling (padj comes from the unshrunk Wald test).

```r
library(apeglm)

# apeglm shrinkage — specify coefficient name from resultsNames(dds)
res_shrunk <- lfcShrink(dds,
                         coef = "condition_treated_vs_control",
                         type = "apeglm",
                         res  = res)    # pass original results for speed

# Compare shrunk vs. unshrunk LFC
cat("Max |LFC| unshrunk:", max(abs(res$log2FoldChange), na.rm = TRUE), "\n")
cat("Max |LFC| shrunk:  ", max(abs(res_shrunk$log2FoldChange), na.rm = TRUE), "\n")

# Export shrunk results
res_shrunk_df <- as.data.frame(res_shrunk)
res_shrunk_df <- res_shrunk_df[order(res_shrunk_df$padj, na.last = TRUE), ]
write.csv(res_shrunk_df, "deseq2_shrunk_results.csv")

# Filter significant with effect size threshold
sig_genes <- res_shrunk_df[
    !is.na(res_shrunk_df$padj) &
    res_shrunk_df$padj < 0.05 &
    abs(res_shrunk_df$log2FoldChange) > 1, ]
cat("Significant (padj<0.05, |LFC|>1):", nrow(sig_genes), "\n")
write.csv(sig_genes, "deseq2_significant.csv")
```

### Step 7: Visualize — MA Plot, Volcano Plot, and Heatmap

```r
library(EnhancedVolcano)
library(pheatmap)

# --- MA Plot (base DESeq2) ---
plotMA(res_shrunk, ylim = c(-5, 5),
       main = "MA Plot (apeglm-shrunk LFC)",
       colSig = "firebrick", colNonSig = "grey60")
# Blue points are significantly DE genes; y-axis is shrunk log2FC

# --- Volcano Plot (EnhancedVolcano) ---
EnhancedVolcano(res_shrunk_df,
    lab        = rownames(res_shrunk_df),
    x          = "log2FoldChange",
    y          = "padj",
    pCutoff    = 0.05,
    FCcutoff   = 1.0,
    xlim       = c(-6, 6),
    title      = "Treated vs. Control",
    subtitle   = "apeglm-shrunk LFC | BH-adjusted p-value",
    legendLabels = c("NS", "LFC", "padj", "padj & LFC"))

ggsave("volcano_plot.pdf", width = 8, height = 7)

# --- Heatmap of top 50 DE genes ---
top50 <- head(rownames(sig_genes[order(sig_genes$padj), ]), 50)
mat   <- assay(vsd)[top50, ]            # variance-stabilized expression
mat   <- mat - rowMeans(mat)            # center by gene mean

annotation_col <- data.frame(
    Condition = coldata$condition,
    Batch     = coldata$batch,
    row.names = colnames(mat)
)

pheatmap(mat,
         annotation_col  = annotation_col,
         cluster_rows    = TRUE,
         cluster_cols    = TRUE,
         show_rownames   = TRUE,
         fontsize_row    = 6,
         filename        = "heatmap_top50.pdf",
         width           = 8,
         height          = 10)
cat("Saved volcano_plot.pdf and heatmap_top50.pdf\n")
```

### Step 8: Multi-Factor Design and Interaction Terms

For designs with batch correction, paired samples, or interaction effects between two variables.

```r
# --- Batch-corrected two-group comparison ---
dds_batch <- DESeqDataSetFromMatrix(countData = counts,
                                     colData   = coldata,
                                     design    = ~ batch + condition)
dds_batch <- dds_batch[rowSums(counts(dds_batch)) >= 10, ]
dds_batch <- DESeq(dds_batch)

res_batch <- results(dds_batch,
                      contrast = c("condition", "treated", "control"),
                      alpha    = 0.05)
cat("Significant (batch-corrected):", sum(res_batch$padj < 0.05, na.rm = TRUE), "\n")

# --- Interaction design: test whether treatment effect differs between genotypes ---
# H0: the effect of treatment is the same in WT and KO
coldata$genotype <- factor(coldata$genotype)  # "WT" or "KO"

dds_int <- DESeqDataSetFromMatrix(
    countData = counts, colData = coldata,
    design = ~ genotype + condition + genotype:condition
)
dds_int <- DESeq(dds_int)
resultsNames(dds_int)
# Interaction coefficient: "genotypeKO.conditiontreated"

# Extract interaction term — genes where treatment effect differs by genotype
res_int <- results(dds_int, name = "genotypeKO.conditiontreated", alpha = 0.05)
cat("Genes with significant interaction:", sum(res_int$padj < 0.05, na.rm = TRUE), "\n")

# --- Likelihood Ratio Test for complex designs (e.g., time series) ---
# LRT compares full model vs. reduced model
dds_lrt <- DESeq(dds_int, test = "LRT", reduced = ~ genotype + condition)
res_lrt  <- results(dds_lrt)
cat("Genes with genotype:condition interaction (LRT):",
    sum(res_lrt$padj < 0.05, na.rm = TRUE), "\n")
```

## Key Parameters

| Parameter | Function | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `design` | `DESeqDataSetFromMatrix()` | (required) | `~ var` or `~ cov + var` | Specifies the GLM formula; put batch/covariates before variable of interest |
| `contrast` | `results()` | `NULL` | `c(var, level1, level2)` or coefficient name | Defines the comparison; always specify explicitly for clarity |
| `alpha` | `results()` | `0.1` | `0.01`–`0.10` | FDR threshold used for independent filtering; does not change padj values |
| `lfcThreshold` | `results()` | `0` | `0`–`2` | Test H0: |LFC| ≤ threshold (TREAT-style test, more stringent) |
| `independentFilter` | `results()` | `TRUE` | `TRUE`/`FALSE` | Adaptive mean-count filtering to maximize the number of rejectible hypotheses |
| `type` | `lfcShrink()` | `"apeglm"` | `"apeglm"`, `"ashr"`, `"normal"` | Shrinkage prior; apeglm is fastest and best calibrated |
| `coef` | `lfcShrink()` | (required) | coefficient name from `resultsNames()` | Which model coefficient to shrink; must match `resultsNames()` output |
| `test` | `DESeq()` | `"Wald"` | `"Wald"`, `"LRT"` | Wald: two-group comparisons; LRT: model comparison for complex designs |
| `reduced` | `DESeq()` | `NULL` | formula without the term to test | Required for LRT; specifies the null model |
| `blind` | `vst()` / `rlog()` | `TRUE` | `TRUE`/`FALSE` | `TRUE` for QC/exploration; `FALSE` for downstream analysis using dispersion info |

## Key Concepts

### Negative Binomial Model and Dispersion

DESeq2 models each gene's count as Negative Binomial(mean = µ, dispersion = α), where mean µ depends on the experimental design through a log-linear model. The key innovation is **dispersion shrinkage**: gene-wise dispersion estimates are shrunk toward a fitted trend across all genes using an empirical Bayes approach, borrowing information across genes to stabilize estimates from small sample sizes.

### Size Factor Normalization

DESeq2 uses the **median-of-ratios** method: for each sample, compute the ratio of each gene's count to the geometric mean of that gene across all samples, then take the median ratio across all genes as the size factor. This is robust to differentially expressed genes and does not require any assumptions about the fraction of DE genes.

### Wald Test vs. Likelihood Ratio Test

- **Wald test** (default): tests a single coefficient `β = 0`; fast and appropriate for two-group comparisons and specific contrasts in multi-factor designs
- **LRT**: compares the full model to a `reduced` model by the likelihood ratio; appropriate for testing whether any level of a multi-level factor (e.g., 5 time points) has an effect, or for testing interaction terms as a group

### Cook's Distance Outlier Detection

DESeq2 computes Cook's distance per gene per sample to flag potential expression outliers. Genes where any sample has a Cook's distance above a threshold are automatically replaced with `NA` in the results. With `refit = TRUE` (default), outlier samples are excluded and the model is refit for that gene.

## Common Recipes

### Recipe: Multiple Contrasts from One Fitted Model

Efficient when comparing multiple treatment groups — fit `DESeq()` once, extract multiple contrasts.

```r
# Fit once
dds_multi <- DESeqDataSetFromMatrix(counts, coldata, design = ~ condition)
dds_multi <- dds_multi[rowSums(counts(dds_multi)) >= 10, ]
dds_multi <- DESeq(dds_multi)

# Extract contrasts — all vs. "control"
contrasts_list <- list(
    A_vs_ctrl = c("condition", "treatment_A", "control"),
    B_vs_ctrl = c("condition", "treatment_B", "control"),
    C_vs_ctrl = c("condition", "treatment_C", "control")
)

results_list <- lapply(names(contrasts_list), function(nm) {
    res <- results(dds_multi, contrast = contrasts_list[[nm]], alpha = 0.05)
    res_shrunk <- lfcShrink(dds_multi, contrast = contrasts_list[[nm]],
                             type = "apeglm", res = res)
    write.csv(as.data.frame(res_shrunk), paste0("results_", nm, ".csv"))
    cat(nm, "— significant:", sum(res$padj < 0.05, na.rm = TRUE), "\n")
    as.data.frame(res_shrunk)
})
names(results_list) <- names(contrasts_list)
```

### Recipe: Paired Sample Design

Eliminate within-subject variability by including subject as a blocking factor.

```r
# Paired design: each subject has pre- and post-treatment samples
coldata$subject   <- factor(c("S1","S1","S2","S2","S3","S3"))
coldata$timepoint <- factor(c("pre","post","pre","post","pre","post"))

dds_paired <- DESeqDataSetFromMatrix(counts, coldata,
                                      design = ~ subject + timepoint)
dds_paired <- dds_paired[rowSums(counts(dds_paired)) >= 10, ]
dds_paired <- DESeq(dds_paired)

res_paired <- results(dds_paired,
                       contrast = c("timepoint", "post", "pre"),
                       alpha    = 0.05)
cat("Significant (paired):", sum(res_paired$padj < 0.05, na.rm = TRUE), "\n")
```

### Recipe: Rank Genes for GSEA Using Shrunk LFC × -log10(pvalue)

Create a pre-ranked gene list for input to GSEA or gseapy's `prerank` function.

```r
# Build ranking metric: signed -log10(pvalue) with LFC direction
res_rank <- as.data.frame(res_shrunk)
res_rank <- res_rank[!is.na(res_rank$pvalue) & !is.na(res_rank$log2FoldChange), ]
res_rank$rank_metric <- sign(res_rank$log2FoldChange) *
                         (-log10(res_rank$pvalue + 1e-300))
res_rank <- res_rank[order(res_rank$rank_metric, decreasing = TRUE), ]

# Export as two-column TSv for fgsea or gseapy prerank
write.table(data.frame(gene  = rownames(res_rank),
                        score = res_rank$rank_metric),
            "gsea_ranked_list.rnk",
            sep = "\t", quote = FALSE, row.names = FALSE, col.names = FALSE)
cat("Ranked gene list saved:", nrow(res_rank), "genes\n")
```

### Recipe: Save and Reload Fitted DESeq2 Object

Avoid re-running the expensive `DESeq()` step in subsequent sessions.

```r
# Save fitted DDS object
saveRDS(dds, "dds_fitted.rds")
cat("Saved fitted DESeqDataSet to dds_fitted.rds\n")

# Reload in a new session
dds_loaded <- readRDS("dds_fitted.rds")
# Continue with results(), lfcShrink(), etc.
res_reloaded <- results(dds_loaded, contrast = c("condition", "treated", "control"))
```

## Expected Outputs

| File | Description |
|------|-------------|
| `deseq2_all_results.csv` | Full results table: baseMean, log2FoldChange, lfcSE, stat, pvalue, padj for all genes |
| `deseq2_shrunk_results.csv` | Results with apeglm-shrunk LFC; use for ranking and visualization |
| `deseq2_significant.csv` | Filtered results: padj < 0.05 and |LFC| > 1 |
| `pca_plot.pdf` | PCA of variance-stabilized counts; used to check batch structure and outliers |
| `dispersion_plot.pdf` | Gene-wise vs. fitted dispersions; should show tight cloud around trend |
| `volcano_plot.pdf` | Volcano plot with significance and LFC thresholds labeled |
| `heatmap_top50.pdf` | Hierarchically clustered heatmap of top 50 DE genes |
| `gsea_ranked_list.rnk` | Pre-ranked gene list for pathway enrichment (fgsea/gseapy) |
| `dds_fitted.rds` | Serialized DESeqDataSet for checkpoint/resume |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Error: design contains one or more variables with all samples having the same value` | A design factor has only one level | Check `table(coldata$condition)`; ensure all factor levels are present |
| `Model matrix not full rank` | Confounded design (e.g., batch perfectly correlated with condition) | Run `table(coldata$batch, coldata$condition)`; drop the confounded variable or collect more samples |
| All or most `padj = NA` | Genes flagged by independent filtering (low mean count) or Cook's outliers | Check `summary(res)` for count of filtered genes; relax `alpha` or verify data quality |
| No significant genes despite strong biology | Under-powered experiment or high within-group variability | Verify n ≥ 3 per group; check PCA for outliers; inspect p-value histogram (should show spike near 0) |
| `Error in lfcShrink`: coefficient not found | `coef` name does not match `resultsNames(dds)` | Run `resultsNames(dds)` and copy the exact coefficient string into `coef =` |
| `apeglm` fails with convergence warning | Extreme LFC estimates (sparse data or complete separation) | Switch to `type = "ashr"` which is more robust to these cases |
| Very large size factors (> 5) | Extremely different library sizes, or normalized counts accidentally used | Check `colSums(counts(dds))`; ensure input is raw integer counts from aligner/counter |
| Dispersion plot shows outlier cloud far from trend | Noisy or failed libraries; incorrect metadata grouping | Examine PCA; remove outlier samples; check that `design` formula matches biological groups |
| Volcano plot: no labeled points | `EnhancedVolcano` defaults label too few genes | Adjust `pCutoff` and `FCcutoff`; or set `selectLab = rownames(sig_genes)[1:20]` |

## References

- [DESeq2 Bioconductor page](https://bioconductor.org/packages/DESeq2) — Package home, vignette, and reference manual
- [DESeq2 vignette](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html) — Comprehensive worked example covering all design types
- [Love et al. (2014) Genome Biology](https://doi.org/10.1186/s13059-014-0550-8) — Original DESeq2 paper: moderated estimation of fold change and dispersion for RNA-seq data
- [Zhu et al. (2019) Bioinformatics](https://doi.org/10.1093/bioinformatics/bty895) — apeglm LFC shrinkage for DESeq2
- [tximeta Bioconductor page](https://bioconductor.org/packages/tximeta) — Salmon import with transcript-level metadata
- [EnhancedVolcano Bioconductor page](https://bioconductor.org/packages/EnhancedVolcano) — Publication-quality volcano plots for DE results
