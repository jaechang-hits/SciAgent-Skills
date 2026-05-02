---
name: omics-analysis-guide
description: Three-tiered approach to omics data analysis (transcriptomics, proteomics) covering validated pipelines, standard workflows, and custom methods
license: open
---

# Omics Data Analysis Guide: Three-Tiered Approach

---

## Metadata

**Short Description**: Comprehensive guide for analyzing omics data (transcriptomics, proteomics) using validated pipelines, standard workflows, or custom analysis methods.

**Authors**: HITS

**Version**: 1.0

**Last Updated**: December 2025

**License**: CC BY 4.0

**Commercial Use**: Allowed

## Citations and Acknowledgments

### If you use validated pipelines or tools (Option 1):
- **Citation**: Always cite the original publication associated with each tool or pipeline
- **Acknowledgment**: Cite the specific tools and methods used in your analysis

### If you use standard workflows (Option 2):
- **Acknowledgment Statement**: "Analysis performed using standard omics data analysis workflows and best practices"
- **Citation for RNA-seq analysis**: Dobin A, et al. STAR: ultrafast universal RNA-seq aligner. Bioinformatics. 2013;29(1):15-21. PMID: 23104886
- **Citation for proteomics**: Cox J, Mann M. MaxQuant enables high peptide identification rates, individualized p.p.b.-range mass accuracies and proteome-wide protein quantification. Nat Biotechnol. 2008;26(12):1367-72. PMID: 19029910

---

## Overview

This guide provides a three-tiered approach to omics data analysis, prioritizing validated pipelines and standard workflows before moving to custom analysis. Always start with Option 1 and proceed to subsequent options only if needed.

The guide covers:
- **Transcriptomics**: Bulk RNA-seq
- **Proteomics**: Pre-quantified protein abundance data (similar to bulk RNA-seq analysis)

**Note**: This guide focuses on analysis of already-quantified data. For raw data processing (alignment, quantification), refer to specialized tools and pipelines.

---

## Key Concepts

### Validated Pipeline vs. Standard Workflow vs. Custom Analysis
A **validated pipeline** is a specific tool with peer-reviewed benchmarking data demonstrating performance on data like yours (e.g., DESeq2 for RNA-seq counts, MaxQuant for label-free proteomics). A **standard workflow** is the canonical sequence of QC → normalization → statistical test → multiple-testing correction assembled from accepted community practice but tuned to your specific dataset. **Custom analysis** is bespoke statistical or computational modeling required when neither prior tier covers the data type or research question. The progression Option 1 → Option 2 → Option 3 trades reproducibility for flexibility — always exhaust earlier tiers first.

### Missing Value Mechanisms (MCAR / MAR / MNAR)
Missing data in omics arises from three distinct mechanisms with different correct treatments. **MCAR** (Missing Completely At Random) means missingness is independent of any value — safe to impute with mean, median, or KNN. **MAR** (Missing At Random) means missingness depends on observed variables but not the unobserved value — KNN or model-based imputation is appropriate. **MNAR** (Missing Not At Random) means missingness depends on the missing value itself, typical in proteomics where low-abundance proteins drop below detection — requires left-censored imputation (minprob/QRILC) below the detection limit. Choosing the wrong mechanism systematically biases downstream statistics.

### Test Assumptions and Test Selection
Parametric tests (Student's t-test, Welch's t-test) assume approximate normality and (for Student's) equal variances; they have higher power than non-parametric tests when assumptions hold. **Non-parametric tests** (Mann-Whitney U, permutation) make weaker assumptions and are correct under skewed distributions or small n, at the cost of statistical power. The choice depends on sample size (n < 10 favors non-parametric), normality (Shapiro-Wilk / Anderson-Darling at the feature level), variance homogeneity (Levene's test), and outlier prevalence.

### Multiple Testing Correction
Omics analyses test thousands of features simultaneously. Without correction, expected false positives at α=0.05 across 20,000 genes is 1,000. **Family-wise error rate (FWER)** corrections like Bonferroni control the probability of any false positive but are conservative. **False discovery rate (FDR)** corrections like Benjamini-Hochberg control the expected proportion of false positives among reported significant features and are the standard for omics. Always report adjusted p-values, never raw p-values, when calling significance.

---

## Decision Framework

Use this tree to choose the right analysis tier for your data:

```
              Have you searched for a validated
              pipeline matching your data type?
                            │
              ┌─────────────┴─────────────┐
              │                           │
             NO                          YES
              │                           │
              ▼                           ▼
       Run Method 1            Did you find a validated
       (literature) AND        pipeline with benchmarks
       Method 2 (consortia     matching your data type
       workflows) FIRST        and biological question?
                                          │
                                  ┌───────┴───────┐
                                  │               │
                                 YES              NO
                                  │               │
                                  ▼               ▼
                          OPTION 1:        Is your data a
                          Use validated    common type
                          pipeline         (RNA-seq counts,
                          (e.g., DESeq2,   pre-quantified
                          edgeR, MaxQuant) proteomics)?
                                                  │
                                          ┌───────┴───────┐
                                          │               │
                                         YES              NO
                                          │               │
                                          ▼               ▼
                                  OPTION 2:        OPTION 3:
                                  Standard         Custom analysis
                                  workflow         (consult
                                  (QC → norm →     statistician;
                                   test → FDR)     document
                                                   thoroughly)
```

### Decision Table

| Data type | Sample size | Has validated pipeline? | Recommended tier | Specific tool / approach |
|-----------|-------------|--------------------------|------------------|--------------------------|
| Bulk RNA-seq counts | n ≥ 3/group | Yes (DESeq2, edgeR) | Option 1 | DESeq2 (negative binomial, default FDR < 0.05) |
| Pre-quantified proteomics, normal-distributed | n ≥ 5/group | Sometimes | Option 1 if pipeline matches; else Option 2 | limma or t-test + BH-FDR |
| Pre-quantified proteomics, MNAR-heavy | n ≥ 5/group | No (mechanism-specific) | Option 2 | minprob imputation → t-test or Mann-Whitney → BH-FDR |
| Small-cohort omics (n < 5) | n < 5 | Rarely | Option 2 with caution | Permutation test, report effect sizes; flag results as preliminary |
| Multi-omics integration | Variable | Limited | Option 3 | MOFA, DIABLO, or custom Bayesian model |
| Novel data type (e.g., spatial multi-omics) | Variable | No | Option 3 | Build from first principles; cross-validate |
| Time-series omics | n per timepoint | Sometimes (maSigPro, ImpulseDE2) | Option 1 if available; else Option 3 | maSigPro for transcriptomics; custom for proteomics |

---

## Option 1: Search for Validated Analysis Methods (Recommended First)

### 1.1 Search for Validated Analysis Pipelines

**IMPORTANT**: You MUST complete BOTH Method 1 AND Method 2 before proceeding to Option 2. Do not skip Method 2 even if Method 1 finds no results.

#### Method 1: Literature Search for Best Practices

Search for validated analysis methods using web search tools or literature databases (PubMed, Google Scholar).

**Search queries to try (use multiple):**
```
"[DATA_TYPE]" "[ANALYSIS_TYPE]" validated pipeline best practices
"[DATA_TYPE]" analysis workflow "[ORGANISM]" published
"[DATA_TYPE]" "[TOOL_NAME]" validation benchmark comparison
```

**Example for bulk RNA-seq:**
```
"RNA-seq" "differential expression" validated pipeline human
"DESeq2" "edgeR" comparison validation RNA-seq
```

**Example for proteomics:**
```
"proteomics" "differential abundance" analysis validated methods
"proteomics" normalization imputation best practices
```

**What to search for in results:**
- Published papers with validated analysis pipelines
- Benchmark studies comparing different tools
- Best practices guides from major consortia (e.g., ENCODE, TCGA)
- Tool documentation with validation data

**IMPORTANT**: Spend adequate time searching literature. Look through at least the first 10-15 search results and check supplementary materials of relevant papers.

#### Method 2: Review Standard Analysis Workflows

Review established workflows from major consortia and publications:
- ENCODE RNA-seq analysis pipeline
- TCGA analysis protocols
- Published benchmark studies

#### What to Do with Results:

**If you find validated pipelines or methods:**
1. **Record the pipeline/method name** and version
2. **Note the reference**: Record the publication DOI/PubMed ID
3. **Record validation details**: Benchmark results, recommended parameters, any limitations
4. **Document the workflow**: Step-by-step analysis procedure

**Example result format:**
```
Data Type: Bulk RNA-seq
Analysis Goal: Differential expression
Pipeline: DESeq2 (v1.40.0)
Reference: Love MI, et al. Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. Genome Biol. 2014;15(12):550. PMID: 25516281
Validation: Validated in multiple benchmark studies, recommended for count data
Parameters: Default parameters, FDR < 0.05, log2FC > 1
```

**If no validated pipelines found in BOTH Method 1 AND Method 2:**
Only then proceed to **Option 2: Use Standard Workflows**

---

## Option 2: Use Standard Analysis Workflows

### When to Use This Option?
- No validated pipelines found for your specific data type
- Need to build a custom workflow from standard components
- Working with common data types (RNA-seq, proteomics)
- Want to follow community best practices

### 2.1 Overview of Standard Workflows

**RNA-seq (Bulk)**:
1. Quality control
2. Normalization and filtering (if count data, use DESeq2/edgeR normalization)
3. Statistical analysis (differential expression)
4. Multiple testing correction
5. Functional enrichment (optional)

**Proteomics (Pre-quantified)**:
1. Quality control
2. Missing value assessment and imputation
3. Normalization
4. Batch correction (if needed)
5. Statistical analysis (differential abundance)
6. Multiple testing correction

### 2.2 Essential Quality Control Steps

**CRITICAL**: Quality control must be performed before any statistical analysis. Poor data quality will lead to unreliable results regardless of statistical methods used.

#### Sample-Level Quality Control

**Check for outlier samples:**
- Use PCA + Isolation Forest to detect outlier samples
- Standardize data, perform PCA, then apply Isolation Forest
- Remove or investigate samples identified as outliers

**Check sample correlation:**
- Calculate correlation matrix between samples
- Low correlations (< 0.5) may indicate poor quality samples
- Remove samples with consistently low correlation

**Check for batch effects:**
- Use PCA + silhouette score to assess batch separation
- If silhouette score > 0.3, strong batch effect detected
- Apply batch correction (ComBat or similar) if needed

#### Feature-Level Quality Control

**Assess missing value patterns:**
- Calculate missing percentage per feature and per sample
- Test correlation between mean intensity and missingness
- Determine mechanism: MCAR (Missing Completely At Random), MAR (Missing At Random), or MNAR (Missing Not At Random)
- MNAR: Low intensity -> more missing (common in proteomics)
- MCAR: No relationship between intensity and missingness

**Check feature detection consistency:**
- Count how many features are detected in minimum number of samples
- Filter features detected in < 50% of samples (adjustable threshold)

### 2.3 Preprocessing Steps

#### Missing Value Imputation

**CRITICAL**: Choose imputation method based on missing value mechanism:

- **MNAR** (Missing Not At Random): Use minimum probability imputation (minprob)
  - Impute values below detection limit using normal distribution
  - Parameters: downshift=1.8, width=0.3

- **MCAR/MAR** (Missing Completely/At Random): Use KNN imputation
  - Use k-nearest neighbors (default: k=5) to impute missing values
  - More robust than mean/median imputation

- **Simple methods** (if few missing values):
  - Mean imputation: Replace with feature mean
  - Median imputation: Replace with feature median

#### Normalization

**For RNA-seq count data**: Normalization is typically handled by DESeq2/edgeR (size factors).

**For proteomics/continuous data**:
- **Median normalization**: Scale each sample to global median
- **Quantile normalization**: Make distributions identical across samples
- **Z-score normalization**: Standardize to mean=0, std=1
- **Total intensity normalization**: Scale to total intensity

### 2.4 Statistical Analysis: Choosing the Right Test

**CRITICAL**: Always check statistical test assumptions before performing analysis. Using the wrong test can lead to incorrect conclusions.

#### Step 1: Check Test Assumptions

**Key checks to perform:**

1. **Normality test**:
   - Use Shapiro-Wilk test for n < 50, Anderson-Darling for n >= 50
   - Sample subset of features (100 features) for speed
   - If >=70% of features are normal, data is considered normal

2. **Variance homogeneity test**:
   - Use Levene's test to check equal variances
   - If >=70% of features have equal variances, assume equal variance

3. **Sample size check**:
   - n < 5: Very small, results unreliable
   - n < 10: Small, prefer non-parametric tests
   - n >= 10: Can use parametric tests if assumptions met

4. **Outlier check**:
   - Calculate z-scores, flag values with |z| > 3
   - If >5% outliers, prefer non-parametric tests

**Test selection logic:**
- **n < 5**: Permutation test or Mann-Whitney U test
- **n < 10**: Mann-Whitney U test (non-parametric)
- **Normal + Equal variance**: Student's t-test
- **Normal + Unequal variance**: Welch's t-test
- **Non-normal**: Mann-Whitney U test

#### Step 2: Perform Statistical Test

**Implementation steps:**

1. For each feature:
   - Extract values for group1 and group2
   - Remove NaN values
   - Calculate means and log2 fold change
   - Perform selected test (t-test, Welch's t-test, or Mann-Whitney U)
   - Record statistic and p-value

2. Apply FDR correction:
   - Use Benjamini-Hochberg procedure (FDR_BH)
   - Adjust p-values for multiple testing
   - Mark features with p_adj < 0.05 as significant

**Key libraries:**
- `scipy.stats`: Statistical tests (ttest_ind, mannwhitneyu, shapiro, levene)
- `statsmodels.stats.multitest`: FDR correction (multipletests with method='fdr_bh')

### 2.5 Visualization

**Volcano Plot**:
- X-axis: Log2 fold change
- Y-axis: -Log10 adjusted p-value
- Color by significance: Upregulated (red), Downregulated (blue), Not significant (gray)
- Add threshold lines for fold change and p-value

**PCA Plot** (for quality control):
- Standardize data, perform PCA
- Plot PC1 vs PC2
- Label samples, check for outliers and batch effects

### 2.6 What to Do with Results

**Once you have completed the standard workflow:**
1. **Document all steps** and parameters used
2. **Save intermediate results** for reproducibility
3. **Validate results** using independent methods when possible
4. **Report key findings** with appropriate statistics

**If standard workflows don't meet your needs:**
Proceed to **Option 3: Custom Analysis**

---

## Option 3: Custom Analysis Methods (Last Resort)

### When to Use This Option?
- Novel data type not covered by standard workflows
- Specialized research questions requiring custom approaches
- Integration of multiple omics data types
- Advanced statistical modeling requirements

### 3.1 General Principles

#### Essential Requirements:
1. **Data Quality**: Ensure high-quality data before custom analysis
   - Perform all QC steps from Option 2
   - Remove outliers and batch effects
   - Validate technical replicates

2. **Statistical Rigor**:
   - Always check test assumptions before analysis
   - Use appropriate statistical tests for your data distribution
   - Apply multiple testing correction (FDR)
   - Validate assumptions

3. **Reproducibility**:
   - Document all steps and parameters
   - Use version control for code
   - Save intermediate results
   - Provide seed values for random processes

4. **Validation**:
   - Cross-validation when applicable
   - Independent validation set if available
   - Compare with known results when possible

#### Best Practices:
- **Start simple**: Begin with basic analyses before complex methods
- **Validate assumptions**: Test normality, independence, etc.
- **Use appropriate transformations**: Log transform if needed
- **Consider biological context**: Interpret results in light of known biology
- **Consult literature**: Review similar studies for guidance

---

## Quick Start Examples

### Example 1: Bulk RNA-seq Differential Expression Analysis

**Step 1**: Quality Control
- Check for outlier samples using PCA + Isolation Forest
- Check sample correlation matrix
- Remove low-quality samples

**Step 2**: For RNA-seq count data, use DESeq2 (typically in R)
```r
library(DESeq2)
dds <- DESeqDataSetFromMatrix(countData = count_matrix, colData = sample_metadata, design = ~ condition)
dds <- DESeq(dds)
res <- results(dds, contrast=c("condition", "treatment", "control"))
```

**Step 3**: Functional Enrichment (optional)
- Use GSEA or GO enrichment tools (gseapy, etc.)
- Prepare ranked gene list from log2FC
- Run enrichment analysis

### Example 2: Proteomics Differential Abundance Analysis

**Step 1**: Quality Control
- Check for outlier samples
- Assess missing values (determine mechanism: MCAR, MAR, or MNAR)

**Step 2**: Impute Missing Values
- If MNAR: Use minprob imputation
- If MCAR/MAR: Use KNN imputation

**Step 3**: Normalization
- Apply median or quantile normalization

**Step 4**: Check for Batch Effects
- Assess using PCA + silhouette score
- Apply batch correction if needed (ComBat or similar)

**Step 5**: Differential Abundance Analysis
- Check test assumptions (normality, variance, sample size)
- Select appropriate test (auto-select based on assumptions)
- Perform test, apply FDR correction
- Filter significant results (p_adj < 0.05)

**Step 6**: Visualization
- Create volcano plot
- Create PCA plot for QC

---

## Data Type-Specific Considerations

### RNA-seq (Bulk)
- **Count data**: Use DESeq2 or edgeR (negative binomial models)
- **Normalization**: Built into DESeq2/edgeR (size factors)
- **Filtering**: Remove low-count genes before analysis
- **Multiple testing**: Always apply FDR correction
- **Statistical test**: DESeq2/edgeR handle count data appropriately

### Proteomics (Pre-quantified)
- **Continuous data**: Similar to normalized RNA-seq data
- **Missing values**: Common, especially for low-abundance proteins
  - Assess missing mechanism (MCAR, MAR, MNAR)
  - Use appropriate imputation method
- **Normalization**: Median, quantile, or total intensity normalization
- **Statistical tests**:
  - Check normality and variance assumptions
  - Use t-test if normal, Mann-Whitney if non-normal
  - Always apply FDR correction
- **Batch effects**: Common in proteomics, check and correct if needed

---

## Best Practices

1. **Exhaust validated pipelines before building anything custom.** Run both literature search and consortium-workflow review before falling back to bespoke analysis. Rationale: validated pipelines have peer-reviewed benchmarking; novel methods require their own validation effort and reduce reproducibility.

2. **Perform sample-level QC before any statistical analysis.** Use PCA + Isolation Forest for outlier detection, sample correlation matrices, and PCA + silhouette score for batch effects. Rationale: a single outlier sample or unrecognized batch effect can dominate test statistics and produce uninterpretable results regardless of the test chosen.

3. **Diagnose the missing-value mechanism (MCAR / MAR / MNAR) before imputing.** Check the correlation between mean intensity and missingness rate per feature. Rationale: imputing MNAR data with KNN biases low-abundance features upward; imputing MCAR data with minprob biases everything downward. Mechanism-aware imputation prevents systematic distortion.

4. **Always check test assumptions, then choose the test — never the reverse.** Run Shapiro-Wilk / Anderson-Darling for normality and Levene's for variance homogeneity on a representative feature subset. Rationale: applying a t-test to non-normal small-n data inflates type I error; defaulting to Mann-Whitney on well-behaved data wastes power.

5. **Always apply FDR correction (Benjamini-Hochberg) for genome-wide tests.** Report `p_adj` (or `q-value`), not raw `p`. Rationale: with 20,000 genes tested at α=0.05, ~1,000 false positives are expected without correction — the result set is meaningless.

6. **Document every parameter and version, save intermediate outputs, and pin random seeds.** Record tool version, parameter values, normalization method, imputation method, test choice, FDR threshold, and the seed for any stochastic step. Rationale: omics pipelines have many tunable knobs; without exact provenance the analysis cannot be reproduced or audited.

7. **Validate findings on an independent dataset or with an orthogonal method whenever possible.** Examples: confirm DE genes via qPCR, replicate in a public dataset (GEO, ArrayExpress), or compare across batches. Rationale: even FDR-controlled hits can be false positives driven by batch artifacts, contamination, or normalization choices.

## Common Pitfalls

1. **Skipping QC and going directly to statistics.**
   *Problem*: Outlier samples and batch effects produce false signals that pass statistical tests, polluting the result list with artifacts.
   *How to avoid*: Always run sample-level PCA, correlation matrices, and outlier detection before any differential test. Treat QC as mandatory, not optional.

2. **Imputing missing values with a one-size-fits-all method.**
   *Problem*: Using mean imputation on MNAR proteomics data biases low-abundance proteins; using minprob on MCAR data biases everything below the detection limit downward.
   *How to avoid*: Diagnose the mechanism (correlation between intensity and missingness), then pick an appropriate imputer: minprob for MNAR, KNN for MCAR/MAR.

3. **Using t-tests on non-normal or small-n data.**
   *Problem*: Student's t-test assumes normality and (with pooled variance) equal variances; with n < 10 and skewed data, type I error inflates well above the nominal α.
   *How to avoid*: Run normality and variance tests first; use Welch's t-test for unequal variance, Mann-Whitney for non-normal, and permutation tests for n < 5.

4. **Reporting raw p-values without multiple testing correction.**
   *Problem*: Across thousands of features, raw p-values produce massive false discovery rates; the resulting "significant" gene lists are dominated by noise.
   *How to avoid*: Always apply Benjamini-Hochberg FDR (or BY for dependent tests) and report adjusted p-values. Set `p_adj < 0.05` (or `q < 0.05`) as the significance threshold.

5. **Confusing fold change with statistical significance.**
   *Problem*: A high log2 fold change at high p_adj is unreliable noise; a low log2 fold change at very low p_adj may be real but biologically negligible.
   *How to avoid*: Filter on both — typical thresholds are `|log2FC| > 1` AND `p_adj < 0.05`. Report effect sizes alongside p-values.

6. **Failing to correct for batch effects when present.**
   *Problem*: Batch effects masquerade as biological signal, especially in proteomics and multi-cohort studies; PC1 ends up reflecting batch rather than condition.
   *How to avoid*: Check batch separation with PCA + silhouette score; if silhouette > ~0.3, apply ComBat, limma's `removeBatchEffect`, or include batch as a covariate in the model.

7. **Treating Option 3 (custom analysis) as a shortcut.**
   *Problem*: Jumping straight to custom methods without first running standard workflows skips peer-reviewed validation and makes results harder to publish and reproduce.
   *How to avoid*: Document a clear justification for why Options 1 and 2 are inadequate before moving to Option 3, and validate any custom method on simulated or held-out data.

## References

### Pipelines and Tools
- **DESeq2**: https://bioconductor.org/packages/release/bioc/html/DESeq2.html — Love MI, Huber W, Anders S. *Genome Biology* 2014; 15:550. PMID: 25516281
- **edgeR**: https://bioconductor.org/packages/release/bioc/html/edgeR.html — Robinson MD, McCarthy DJ, Smyth GK. *Bioinformatics* 2010; 26(1):139-40.
- **STAR aligner**: https://github.com/alexdobin/STAR — Dobin A, et al. *Bioinformatics* 2013; 29(1):15-21. PMID: 23104886
- **MaxQuant**: https://www.maxquant.org/ — Cox J, Mann M. *Nat Biotechnol* 2008; 26(12):1367-72. PMID: 19029910
- **limma**: https://bioconductor.org/packages/release/bioc/html/limma.html — Ritchie ME, et al. *Nucleic Acids Res* 2015; 43(7):e47.
- **ComBat (sva package)**: https://bioconductor.org/packages/release/bioc/html/sva.html — Johnson WE, Li C, Rabinovic A. *Biostatistics* 2007; 8(1):118-27.

### Consortium Best Practices
- **ENCODE RNA-seq pipeline**: https://www.encodeproject.org/data-standards/rna-seq/
- **GTEx Analysis Protocol**: https://gtexportal.org/home/methods
- **TCGA Analysis Protocols**: https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/

### Statistical Methods
- **Benjamini-Hochberg FDR**: Benjamini Y, Hochberg Y. *J. R. Stat. Soc. B* 1995; 57(1):289-300.
- **Multiple imputation in proteomics review**: Lazar C, et al. *J Proteome Res* 2016; 15(4):1116-25.
- **scipy.stats**: https://docs.scipy.org/doc/scipy/reference/stats.html
- **statsmodels multiple testing**: https://www.statsmodels.org/stable/stats.html

### Data Repositories for Validation
- **GEO**: https://www.ncbi.nlm.nih.gov/geo/
- **ArrayExpress**: https://www.ebi.ac.uk/biostudies/arrayexpress
- **PRIDE (proteomics)**: https://www.ebi.ac.uk/pride/

---

**Remember**: Always start with validated pipelines (Option 1), then move to standard workflows (Option 2), and only use custom analysis (Option 3) when necessary. Document all steps and parameters for reproducibility. Quality control is essential at every stage of analysis. Always check statistical test assumptions before performing analysis.
