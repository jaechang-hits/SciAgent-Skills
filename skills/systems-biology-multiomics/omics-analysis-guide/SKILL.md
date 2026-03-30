---
name: omics-analysis-guide
description: "Comprehensive guide for analyzing omics data (transcriptomics, proteomics) using a three-tiered approach: validated pipelines, standard workflows, or custom analysis methods. Covers QC, normalization, imputation, statistical testing, and visualization."
license: CC-BY-4.0
compatibility: Python 3.10+, R 4.0+
metadata:
  authors: HITS
  version: "1.0"
---

# Omics Data Analysis Guide: Three-Tiered Approach

## Overview

This guide provides a three-tiered approach to omics data analysis, prioritizing validated pipelines and standard workflows before moving to custom analysis. Always start with Option 1 and proceed to subsequent options only if needed.

The guide covers:
- **Transcriptomics**: Bulk RNA-seq
- **Proteomics**: Pre-quantified protein abundance data (similar to bulk RNA-seq analysis)

**Note**: This guide focuses on analysis of already-quantified data. For raw data processing (alignment, quantification), refer to specialized tools and pipelines.

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

**Remember**: Always start with validated pipelines (Option 1), then move to standard workflows (Option 2), and only use custom analysis (Option 3) when necessary. Document all steps and parameters for reproducibility. Quality control is essential at every stage of analysis. Always check statistical test assumptions before performing analysis.
