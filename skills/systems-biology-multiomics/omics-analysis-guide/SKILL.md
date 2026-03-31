---
name: omics-analysis-guide
description: "Comprehensive decision guide for analyzing omics data (transcriptomics, proteomics) using a three-tiered approach: validated pipelines first, standard workflows second, custom analysis last. Covers quality control strategies, normalization method selection, missing value imputation, statistical test selection based on data properties, and result visualization. Consult this guide when planning a bulk RNA-seq or proteomics differential analysis to choose the right tools, tests, and preprocessing steps."
license: CC-BY-4.0
---

# Omics Data Analysis Guide

## Overview

This guide provides a structured decision framework for analyzing omics data, covering bulk RNA-seq transcriptomics and pre-quantified proteomics. It follows a three-tiered approach that prioritizes validated pipelines (e.g., DESeq2, edgeR) over ad hoc methods, ensuring reproducibility and statistical rigor. The guide helps researchers select appropriate quality control methods, normalization strategies, imputation approaches, and statistical tests based on the properties of their data.

**Scope**: Analysis of already-quantified data. For raw data processing (alignment, quantification), refer to specialized pipeline skills.

**Data types covered**:
- **Transcriptomics**: Bulk RNA-seq (count matrices from tools like featureCounts, HTSeq, or STAR)
- **Proteomics**: Pre-quantified protein abundance data (intensity matrices from MaxQuant, DIA-NN, or similar)

## Key Concepts

### Three-Tiered Analysis Approach

The three-tiered approach provides a principled order of operations for omics analysis. The tiers are strictly ordered: always attempt Tier 1 before Tier 2, and Tier 2 before Tier 3.

**Tier 1 -- Validated Pipelines** (always try first):
Use published, benchmarked pipelines with known performance characteristics. For bulk RNA-seq, DESeq2 and edgeR are the gold standard. Search literature (PubMed, Google Scholar) and consortia resources (ENCODE, TCGA) for validated workflows. When searching, try multiple queries:
- `"[DATA_TYPE]" "[ANALYSIS_TYPE]" validated pipeline best practices`
- `"[DATA_TYPE]" analysis workflow "[ORGANISM]" published`
- `"[TOOL_NAME]" validation benchmark comparison`

When a validated pipeline is found, record: pipeline name and version, reference DOI, validation benchmark results, recommended parameters, and known limitations.

**Tier 2 -- Standard Workflows** (when no validated pipeline exists):
Assemble a workflow from well-established components: standard QC, normalization, statistical testing, and visualization. Each component should follow community best practices as described in this guide.

**Tier 3 -- Custom Analysis** (last resort):
Reserved for novel data types, specialized research questions, or multi-omics integration that cannot be addressed by standard workflows. Custom analysis requires:
- All QC steps from Tier 2 as a baseline
- Explicit assumption checking and validation at each step
- Cross-validation or independent validation when possible
- Complete documentation of all methods, parameters, and rationale
- Seed values for all random processes to ensure reproducibility

### Quality Control Methods

Quality control must be performed before any statistical analysis. Poor data quality leads to unreliable results regardless of the statistical methods used. QC operates at two levels: sample-level (detecting problematic samples) and feature-level (detecting unreliable measurements).

**Sample-level QC**:

- **PCA + Isolation Forest for outlier detection**: Standardize data, perform PCA on the sample space, then apply Isolation Forest to identify outlier samples. The Isolation Forest algorithm detects anomalies by measuring how easily a point can be isolated from the rest of the data. Investigate flagged samples before removing them -- they may represent genuine biological variation rather than technical artifacts.
- **Sample correlation analysis**: Calculate the pairwise Pearson or Spearman correlation matrix between all samples. In well-behaved experiments, replicates within the same condition should show high correlation (r > 0.8). Samples with consistently low correlation (r < 0.5) across all other samples may indicate poor RNA quality, sample degradation, or mislabeling. Remove or investigate these samples.
- **Batch effect assessment**: Use PCA combined with silhouette scoring to quantify the degree of batch separation. Project samples onto the first few principal components, then compute the silhouette score using batch labels. A silhouette score > 0.3 indicates strong batch separation that will confound biological comparisons. Apply batch correction methods such as ComBat (parametric or non-parametric) or include batch as a covariate in the statistical model.

**Feature-level QC**:

- **Missing value pattern analysis**: Calculate the percentage of missing values per feature and per sample. Visualize the missing value pattern as a heatmap to identify systematic patterns. Test the correlation between mean feature intensity (across non-missing values) and the feature's missing rate to diagnose the missing value mechanism (MCAR, MAR, or MNAR).
- **Feature detection filtering**: Count how many samples detect each feature. Features detected in fewer than 50% of samples (adjustable threshold) carry too much imputation uncertainty and should generally be filtered out. For RNA-seq, apply a minimum count threshold (e.g., at least 10 counts in at least 3 samples) to remove genes with negligible expression.
- **Distribution assessment**: Examine the overall distribution of values per sample using density plots or boxplots. Look for samples with shifted distributions, bimodal patterns, or unusually high/low total signal, which may indicate technical problems.

### Missing Value Mechanisms

Understanding the mechanism behind missing values is critical for choosing the correct imputation strategy, particularly in proteomics data. The three mechanisms require fundamentally different imputation approaches, and misidentification leads to systematic bias in downstream results.

**MCAR (Missing Completely At Random)**:
No relationship between missingness and any observed or unobserved variable. Missingness is purely random -- equivalent to randomly deleting values from the data. Diagnosis: no significant correlation between mean feature intensity and the feature's missing rate. In practice, pure MCAR is uncommon in omics data but may occur due to random technical failures.

**MAR (Missing At Random)**:
Missingness depends on observed variables (e.g., batch, sample group) but not on the missing value itself. For example, all proteins may be more likely to be missing in samples from a specific batch due to a systematic processing issue, but the missingness does not depend on the protein's abundance. Diagnosis: missingness correlates with batch or group labels but not with feature intensity after conditioning on these variables.

**MNAR (Missing Not At Random)**:
Missingness depends on the unobserved value itself. This is the most common mechanism in proteomics: low-abundance proteins fall below the mass spectrometer's detection limit, causing a direct relationship between low intensity and high missingness. Diagnosis: significant negative correlation between mean feature intensity and missing rate (features with lower average intensity across detected samples have higher missing rates). MNAR requires left-censored imputation methods (e.g., minprob) that generate values in the low-abundance range rather than imputing from the observed distribution.

**Practical diagnostic procedure**:
1. For each feature, calculate the mean intensity across non-missing values and the fraction of missing values
2. Compute the Spearman correlation between these two vectors
3. If the correlation is significantly negative (p < 0.05, rho < -0.3), the mechanism is likely MNAR
4. If no significant correlation exists, the mechanism is likely MCAR or MAR
5. To distinguish MAR from MCAR, test whether missingness correlates with known covariates (batch, group)

### Normalization Methods

The choice of normalization depends on the data type, distribution properties, and downstream analysis method. Normalization corrects for systematic technical variation (e.g., sequencing depth, loading differences) while preserving biological signal.

**RNA-seq count data**:
- **DESeq2 size factors** (median-of-ratios): Computes a per-sample scaling factor based on the median ratio of each gene's count to its geometric mean across samples. Robust to highly expressed genes that dominate total count.
- **edgeR TMM** (trimmed mean of M-values): Computes a scaling factor by trimming extreme log-fold-changes and absolute expression values, then taking a weighted mean. Robust to asymmetric differential expression.
- Do not apply external normalization (log2, RPKM, quantile) to count data before using these tools. They expect raw counts.

**Proteomics / continuous intensity data**:
- **Median normalization**: Scale each sample so that all sample medians are equal to the global median. Robust to outliers and appropriate when most proteins are not differentially abundant.
- **Quantile normalization**: Force all sample distributions to be identical by replacing values with the average across samples at each rank. Strongest correction but assumes that the global distribution of protein abundances is similar across all conditions.
- **Z-score normalization**: Standardize each feature independently to mean=0, std=1. Useful when downstream methods (e.g., clustering, machine learning) assume standardized input. Removes magnitude information.
- **Total intensity normalization**: Scale each sample by its total measured signal. Appropriate when total protein load varies systematically across samples (e.g., different amounts of starting material).

### Statistical Test Selection

Choosing the correct statistical test requires checking four data properties systematically. Sample a representative subset of features (~100) for efficiency when testing assumptions across the full feature set.

1. **Normality**: Use the Shapiro-Wilk test for groups with n < 50 samples, or the Anderson-Darling test for n >= 50. Apply the test to each group separately for each sampled feature. If >= 70% of features pass the normality criterion (p > 0.05), treat the data as approximately normally distributed overall.

2. **Variance homogeneity**: Use Levene's test (based on deviations from the group median, which is robust to non-normality). Test each sampled feature across groups. If >= 70% of features show non-significant Levene's test results (p > 0.05), assume equal variances.

3. **Sample size**: The number of biological replicates per group directly affects which tests are valid. With n < 5, parametric estimates of variance are unreliable regardless of the data distribution. With n < 10, non-parametric tests are generally safer. With n >= 10 and confirmed normality, parametric tests provide better statistical power.

4. **Outlier prevalence**: Calculate z-scores for each feature within each group. If more than 5% of values across the dataset have |z| > 3, outliers are prevalent enough to distort parametric test results. In this case, non-parametric tests (which operate on ranks rather than raw values) are more robust.

**Multiple testing correction**: Regardless of which test is chosen, always apply Benjamini-Hochberg FDR correction to all p-values when testing thousands of features simultaneously. Use `statsmodels.stats.multitest.multipletests(pvals, method='fdr_bh')` in Python or `p.adjust(pvals, method='BH')` in R. Report adjusted p-values (q-values) and use q < 0.05 as the significance threshold.

## Decision Framework

### Which Analysis Tier to Use

```
Question: What kind of omics analysis do you need?
|
+-- Is there a published, validated pipeline for your data type and goal?
|   +-- YES --> Tier 1: Use the validated pipeline (DESeq2, edgeR, etc.)
|   +-- NO
|       +-- Is your data a common type (bulk RNA-seq, proteomics)?
|           +-- YES --> Tier 2: Assemble standard workflow from established components
|           +-- NO  --> Tier 3: Custom analysis with extra validation
```

| Scenario | Recommended Tier | Rationale |
|----------|-----------------|-----------|
| Bulk RNA-seq differential expression | Tier 1 (DESeq2/edgeR) | Extensively validated negative binomial models for count data |
| Bulk RNA-seq with complex design (interaction, time series) | Tier 1 (DESeq2/edgeR with multi-factor design) | These tools support complex designs via formula interface |
| Pre-quantified proteomics, standard two-group comparison | Tier 2 (standard workflow) | Well-established QC, imputation, and testing components |
| Proteomics with validated published protocol | Tier 1 | Always prefer a validated method when available |
| Novel omics data type or multi-omics integration | Tier 3 (custom) | No standard pipeline exists; requires bespoke validation |
| Integration of RNA-seq and proteomics from same samples | Tier 3 (custom) | Multi-omics integration requires specialized methods (MOFA, mixOmics) |
| Standard analysis but with very small sample size (n < 3) | Tier 2 with caution | Use standard workflow but note severe power limitations in results |

### Which Statistical Test to Use

```
Question: What are the properties of your data?
|
+-- Sample size per group?
    +-- n < 5 --> Permutation test or Mann-Whitney U
    +-- n < 10 --> Mann-Whitney U (non-parametric, safer for small n)
    +-- n >= 10
        +-- Is data normally distributed? (Shapiro-Wilk / Anderson-Darling)
            +-- NO --> Mann-Whitney U
            +-- YES
                +-- Equal variances? (Levene's test)
                    +-- YES --> Student's t-test
                    +-- NO  --> Welch's t-test
```

| Data Properties | Recommended Test | Notes |
|-----------------|-----------------|-------|
| n < 5, any distribution | Permutation test | Exact test; no distributional assumptions |
| n < 10, any distribution | Mann-Whitney U | Robust non-parametric rank test |
| n >= 10, normal, equal variance | Student's t-test | Classical parametric test |
| n >= 10, normal, unequal variance | Welch's t-test | Does not assume equal variances |
| n >= 10, non-normal | Mann-Whitney U | Non-parametric; robust to violations |
| RNA-seq count data | DESeq2 / edgeR | Use built-in negative binomial models, not generic tests |

### Which Imputation Method to Use

```
Question: What is the missing value mechanism?
|
+-- MNAR (low intensity correlates with missingness)?
|   +-- YES --> Minimum probability imputation (minprob)
|              Parameters: downshift=1.8, width=0.3
+-- MCAR or MAR?
    +-- Many missing values --> KNN imputation (k=5)
    +-- Few missing values  --> Mean or median imputation
```

| Mechanism | Method | Parameters | Rationale |
|-----------|--------|------------|-----------|
| MNAR | Minimum probability (minprob) | downshift=1.8, width=0.3 | Draws from a downshifted normal distribution to simulate values below detection limit |
| MCAR / MAR (many missing) | KNN imputation | k=5 neighbors | Leverages similar samples to estimate missing values; more robust than mean/median |
| MCAR / MAR (few missing) | Mean or median imputation | Per-feature | Simple and computationally efficient when missing rate is low (< 5%) |
| Mixed mechanism | Hybrid approach | Varies | Apply minprob to MNAR features and KNN to MCAR/MAR features separately |

## Best Practices

1. **Always start with Tier 1 (validated pipelines)**: Search PubMed, Google Scholar, and major consortia (ENCODE, TCGA) for published, benchmarked workflows before building your own. Check at least 10-15 search results and review supplementary materials of relevant benchmark papers.

2. **Perform quality control before any statistical analysis**: Run sample-level QC (PCA + Isolation Forest, correlation matrix, batch effect assessment) and feature-level QC (missing value patterns, detection filtering) before normalization or testing. Skipping QC is the most common source of unreliable results.

3. **Diagnose the missing value mechanism before choosing imputation**: Test the correlation between feature intensity and missingness rate. MNAR requires fundamentally different imputation (minprob) than MCAR/MAR (KNN). Using the wrong method introduces systematic bias.

4. **Check statistical test assumptions explicitly**: Run normality tests (Shapiro-Wilk or Anderson-Darling) and variance homogeneity tests (Levene's) on a representative feature subset before selecting a test. Do not assume normality without evidence, especially for proteomics data.

5. **Always apply multiple testing correction**: Use Benjamini-Hochberg FDR correction on all p-values from feature-wise tests. Report adjusted p-values (q-values) with a threshold of 0.05. Reporting uncorrected p-values from thousands of simultaneous tests leads to massive false positive rates.

6. **Do not normalize RNA-seq count data externally before DESeq2/edgeR**: These tools implement their own normalization (size factors, TMM) designed for count data. Applying log-transformation or quantile normalization beforehand violates their model assumptions.

7. **Document all steps, parameters, and software versions**: Record the exact pipeline, tool versions, parameter settings, and filtering thresholds used. Save intermediate results at each stage. This is essential for reproducibility and peer review.

8. **Validate results when possible**: Use cross-validation, independent validation sets, or comparison with known biological results. For custom analyses (Tier 3), validation is especially critical since the workflow has not been externally benchmarked.

## Common Pitfalls

1. **Skipping the literature search and jumping straight to custom analysis**: Researchers often build ad hoc workflows when validated pipelines already exist, leading to suboptimal methods and non-reproducible results.
   - *How to avoid*: Complete both literature search (PubMed, Google Scholar) and consortia review (ENCODE, TCGA protocols) before proceeding to Tier 2 or 3. Document what you searched and why existing pipelines were insufficient.

2. **Using the wrong imputation method for the missing value mechanism**: Applying KNN imputation to MNAR data (e.g., proteomics below detection limit) fills in values that are systematically too high, inflating apparent abundance of low-level proteins.
   - *How to avoid*: Always test the correlation between feature intensity and missingness rate. If low-intensity features have more missing values, the mechanism is likely MNAR -- use minimum probability imputation.

3. **Ignoring batch effects**: Unaddressed batch effects can dominate biological signal in PCA and inflate false discovery rates in differential analysis.
   - *How to avoid*: Assess batch effects using PCA + silhouette score before statistical testing. If silhouette score > 0.3, apply batch correction (ComBat or equivalent) before downstream analysis.

4. **Applying parametric tests to non-normal data with small sample sizes**: Student's t-test assumes normality. With small samples (n < 10) and non-normal distributions, parametric tests have inflated Type I error rates.
   - *How to avoid*: Check normality with Shapiro-Wilk (n < 50) or Anderson-Darling (n >= 50). For small samples or non-normal data, use Mann-Whitney U or permutation tests.

5. **Omitting multiple testing correction**: Testing thousands of features generates hundreds of false positives at alpha = 0.05 even when no true differences exist.
   - *How to avoid*: Always apply Benjamini-Hochberg FDR correction. Use adjusted p-values (q < 0.05) for significance calls. Never report raw p-values from genome-wide or proteome-wide screens.

6. **Normalizing RNA-seq counts before DESeq2/edgeR**: Applying log2, RPKM, or quantile normalization to count data before feeding it to DESeq2 or edgeR breaks their negative binomial model assumptions and produces incorrect results.
   - *How to avoid*: Provide raw, untransformed count matrices to DESeq2/edgeR. These tools handle normalization internally via size factors (DESeq2) or TMM (edgeR).

7. **Filtering features too aggressively or not at all**: Keeping features detected in very few samples adds noise and reduces statistical power after multiple testing correction. Conversely, no filtering retains unreliable measurements dominated by imputation artifacts.
   - *How to avoid*: Filter features detected in fewer than 50% of samples as a default threshold. Adjust based on experimental design and missing value analysis. For RNA-seq, filter genes with very low counts across all samples (e.g., keep genes with >= 10 counts in >= 3 samples).

8. **Not accounting for confounding variables in the experimental design**: Ignoring known covariates (e.g., age, sex, tissue source) that correlate with both the condition of interest and the measured features leads to spurious differential results.
   - *How to avoid*: Include known confounders as covariates in the statistical model. In DESeq2, use multi-factor designs (e.g., `design = ~ batch + condition`). For proteomics with generic tests, use linear models that account for covariates or perform stratified analysis.

## Workflow

1. **Step 1: Search for Validated Pipelines (Tier 1)**
   - Search PubMed and Google Scholar for validated analysis pipelines matching your data type and analysis goal
   - Review established workflows from major consortia (ENCODE, TCGA, Human Protein Atlas)
   - Try multiple search queries:
     - `"[DATA_TYPE]" "[ANALYSIS_TYPE]" validated pipeline best practices`
     - `"[DATA_TYPE]" analysis workflow "[ORGANISM]" published`
     - `"[TOOL_NAME]" validation benchmark comparison`
   - Check at least 10-15 search results including supplementary materials
   - If a validated pipeline is found, record: pipeline name and version, reference DOI/PubMed ID, benchmark validation results, recommended parameters, and known limitations
   - Example result: DESeq2 v1.40.0, PMID 25516281, validated in multiple benchmark studies, default parameters with FDR < 0.05 and |log2FC| > 1
   - Decision point: If validated pipeline found, use it and skip to Step 6. Otherwise, proceed to Step 2.

2. **Step 2: Quality Control**
   - Run sample-level QC: PCA + Isolation Forest for outlier detection, sample correlation matrix, batch effect assessment (PCA + silhouette score)
   - Run feature-level QC: missing value pattern analysis (per-feature and per-sample), feature detection filtering (remove features in < 50% of samples)
   - Decision point: If batch effect detected (silhouette score > 0.3), apply ComBat or similar correction before proceeding

3. **Step 3: Preprocessing**
   - For proteomics: diagnose missing value mechanism using the diagnostic procedure:
     - Calculate mean intensity and missing rate per feature
     - Compute Spearman correlation between intensity and missingness
     - If rho < -0.3 and p < 0.05, mechanism is MNAR; otherwise MCAR/MAR
   - Apply appropriate imputation based on diagnosed mechanism:
     - MNAR: minimum probability imputation (downshift=1.8, width=0.3)
     - MCAR/MAR with many missing values: KNN imputation (k=5)
     - MCAR/MAR with few missing values (< 5%): mean or median imputation
   - Normalize the data:
     - For RNA-seq: skip external normalization (DESeq2/edgeR handle it internally)
     - For proteomics: log2-transform raw intensities first, then apply median or quantile normalization
   - Verify normalization by comparing sample distribution boxplots before and after

4. **Step 4: Statistical Testing**
   - For RNA-seq count data, use DESeq2 or edgeR directly:
   ```r
   library(DESeq2)
   dds <- DESeqDataSetFromMatrix(countData = count_matrix,
                                  colData = sample_metadata,
                                  design = ~ condition)
   dds <- DESeq(dds)
   res <- results(dds, contrast = c("condition", "treatment", "control"))
   # Filter significant results
   sig_res <- res[which(res$padj < 0.05 & abs(res$log2FoldChange) > 1), ]
   ```
   - For multi-factor designs with batch correction:
   ```r
   # Include batch as covariate; condition effect is tested
   dds <- DESeqDataSetFromMatrix(countData = count_matrix,
                                  colData = sample_metadata,
                                  design = ~ batch + condition)
   ```
   - For proteomics or continuous data:
     - Check assumptions on a feature subset: normality (Shapiro-Wilk or Anderson-Darling), variance homogeneity (Levene's test), sample size, outlier prevalence
     - Select the appropriate test using the Decision Framework (see above)
     - For each feature: extract group values, remove NaN, calculate means and log2 fold change, perform the selected test, record statistic and p-value
   - Apply Benjamini-Hochberg FDR correction to all p-values
   - Mark features with adjusted p-value < 0.05 and |log2FC| > 1 as significant
   - Key Python libraries: `scipy.stats` (ttest_ind, mannwhitneyu, shapiro, levene), `statsmodels.stats.multitest` (multipletests with method='fdr_bh')

5. **Step 5: Visualization and Interpretation**
   - Create a volcano plot for differential results:
     - X-axis: log2 fold change; Y-axis: -log10(adjusted p-value)
     - Color by significance status: upregulated (red/warm color), downregulated (blue/cool color), not significant (gray)
     - Add horizontal threshold line at -log10(0.05) for FDR cutoff
     - Add vertical threshold lines at log2FC = +1 and -1 for fold change cutoff
     - Label the top N most significant features by name
   - Create a PCA plot for QC assessment:
     - Standardize data (z-score) before PCA computation
     - Plot PC1 vs PC2 with explained variance percentages on axis labels
     - Color samples by condition, shape by batch (if applicable)
     - Label individual samples to identify potential outliers
     - Check that samples cluster by biological condition, not by batch
   - Create a sample correlation heatmap:
     - Compute pairwise Pearson or Spearman correlation between all samples
     - Display as a clustered heatmap with sample annotations
     - Verify that replicates within conditions cluster together
   - For proteomics: create a missing value heatmap to visualize the pattern of missingness across features and samples

6. **Step 6: Documentation and Validation**
   - Record all steps, parameters, tool versions, and filtering thresholds
   - Save intermediate results at each stage for reproducibility
   - Validate results using independent methods or known biological controls when possible
   - Decision point: If standard workflows (Tier 2) did not meet your needs, proceed to Tier 3 (custom analysis) with extra validation requirements

### Data-Type-Specific Workflow Notes

**RNA-seq (Bulk)**:
- Input is a count matrix (genes x samples) from featureCounts, HTSeq, or STAR
- Use DESeq2 or edgeR for the complete pipeline (normalization + statistical testing)
- Filter low-count genes before analysis (e.g., keep genes with >= 10 counts in >= 3 samples)
- DESeq2/edgeR use negative binomial models designed for count data -- do not apply generic t-tests to counts
- For functional enrichment after differential expression, prepare a ranked gene list from log2FC and use GSEA or GO enrichment tools (e.g., gseapy, clusterProfiler)

**Proteomics (Pre-quantified)**:
- Input is an intensity matrix (proteins x samples) from MaxQuant, DIA-NN, or similar
- Missing values are common, especially for low-abundance proteins -- always assess mechanism before imputation
- Normalization is separate from statistical testing (unlike RNA-seq)
- Log2-transform intensity values before normalization if working with raw intensities
- Batch effects are common in proteomics experiments with multiple MS runs -- always check and correct if present
- After differential abundance testing, consider pathway enrichment to interpret results in biological context

## Protocol Guidelines

1. **Result reporting format**: For each differential analysis, report a results table containing: feature ID, group means, log2 fold change, raw p-value, adjusted p-value (FDR), and significance flag. Include the total number of features tested, the number passing significance thresholds, and the thresholds used (e.g., q < 0.05, |log2FC| > 1). For RNA-seq, also report the baseMean (average normalized count across all samples).

2. **Reproducibility requirements**: Save the complete analysis environment (tool versions, package versions, random seeds). Store intermediate files at key checkpoints: after QC filtering, after imputation (proteomics), after normalization, and after statistical testing. Use version control for all analysis scripts. Record the exact commands or function calls used at each step.

3. **Visualization standards**: Volcano plots should include threshold lines for both fold change and adjusted p-value cutoffs. PCA plots should label individual samples and indicate group membership with colors and shapes. Heatmaps of top differential features should include hierarchical clustering dendrograms and sample annotations. All figures should have clear axis labels, legends, and titles.

4. **Sensitivity analysis**: When using thresholds (e.g., 50% detection filter, silhouette score > 0.3, q < 0.05), consider running the analysis with alternative thresholds to assess how sensitive the conclusions are to these choices. Report the robustness of key findings across threshold variations.

5. **Biological interpretation**: After identifying statistically significant features, interpret results in the context of known biology. Check whether top hits are consistent with expected biology or published literature. Consider pathway enrichment analysis (GSEA, GO enrichment) to identify coordinated changes across functionally related gene or protein sets.

## Further Reading

- [Love MI, Huber W, Anders S. Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. Genome Biology. 2014;15(12):550.](https://doi.org/10.1186/s13059-014-0550-8) -- The foundational DESeq2 paper describing the negative binomial model, shrinkage estimation, and size factor normalization for RNA-seq count data.
- [Robinson MD, McCarthy DJ, Smyth GK. edgeR: a Bioconductor package for differential expression analysis of digital gene expression data. Bioinformatics. 2010;26(1):139-140.](https://doi.org/10.1093/bioinformatics/btp616) -- The edgeR paper describing TMM normalization and negative binomial GLM-based testing for RNA-seq and other count-based assays.
- [Lazar C, Gatto L, Ferro M, Bruley C, Burger T. Accounting for the Multiple Natures of Missing Values in Label-Free Quantitative Proteomics Data Sets to Compare Imputation Strategies. J Proteome Res. 2016;15(4):1116-1125.](https://doi.org/10.1021/acs.jproteome.5b00981) -- Systematic comparison of imputation strategies for proteomics data, covering MCAR, MAR, and MNAR mechanisms and their impact on downstream analysis.
- [Ritchie ME, Phipson B, Wu D, et al. limma powers differential expression analyses for RNA-sequencing and microarray studies. Nucleic Acids Res. 2015;43(7):e47.](https://doi.org/10.1093/nar/gkv007) -- The limma-voom method for RNA-seq differential expression, an alternative to DESeq2/edgeR using linear models with precision weights.

## Related Skills

- `pydeseq2-differential-expression` -- Python implementation of DESeq2 for bulk RNA-seq differential expression analysis, directly implementing Tier 1 validated workflows from this guide
- `scanpy-scrna-seq` -- Single-cell RNA-seq analysis with scanpy; extends the transcriptomics concepts in this guide to single-cell resolution
- `kegg-pathway-analysis` -- Pathway enrichment analysis using KEGG, a common downstream step after identifying differentially expressed genes or proteins
- `statistical-analysis` -- General statistical testing methods and frameworks, complementing the test selection guidance in this guide
