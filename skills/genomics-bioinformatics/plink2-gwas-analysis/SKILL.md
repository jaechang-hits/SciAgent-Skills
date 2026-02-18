---
name: "plink2-gwas-analysis"
description: "Genome-wide association study (GWAS) and population genetics analysis tool. Processes PLINK (.bed/.bim/.fam), VCF, and BGEN files; performs QC (MAF, HWE, missingness), identity-by-descent estimation, principal component analysis, and linear/logistic regression GWAS. Outputs Manhattan-plot-ready summary statistics. Use regenie or SAIGE instead for very large biobanks (>100k samples) with mixed models."
license: "GPL-3.0"
---

# PLINK2 — GWAS and Population Genetics

## Overview

PLINK2 is the high-performance successor to PLINK 1.9, designed for genome-wide association studies (GWAS) and population genetics analysis on large cohorts. It processes genotype data in PLINK binary format (.bed/.bim/.fam), VCF, and BGEN formats — performing sample and variant quality control (QC), kinship estimation, principal component analysis (PCA), and linear/logistic regression association testing. PLINK2 is 10–100× faster than PLINK 1.9 on most tasks due to multithreading and optimized I/O. Output files are compatible with downstream visualization (Manhattan/QQ plots) and meta-analysis tools.

## When to Use

- Running GWAS on a case-control or quantitative trait cohort after genotyping array QC
- Performing sample QC: missingness, heterozygosity outliers, sex check, cryptic relatedness
- Computing genome-wide LD pruning for PCA or relatedness estimation
- Running PCA on genotype data to identify population stratification
- Converting between PLINK binary, VCF, and BGEN formats
- Filtering variants by MAF, HWE, missingness, or INFO score in VCF/imputed data
- Use **regenie** or **SAIGE** instead for biobank-scale GWAS (>100k samples) requiring mixed model association to control for population structure
- Use **VCFtools** as an alternative for VCF-specific population genetics statistics

## Prerequisites

- **Software**: PLINK2 (pre-compiled binary; no pip/conda package)
- **Input**: PLINK binary files (.bed/.bim/.fam) or VCF/BGEN from array genotyping or imputation

```bash
# Download PLINK2 pre-compiled binary (Linux)
wget https://s3.amazonaws.com/plink2-assets/alpha6/plink2_linux_avx2_20241112.zip
unzip plink2_linux_avx2_20241112.zip
chmod +x plink2
export PATH="$PWD:$PATH"

# macOS
wget https://s3.amazonaws.com/plink2-assets/alpha6/plink2_mac_20241112.zip
unzip plink2_mac_20241112.zip

# Verify
plink2 --version
# PLINK v2.00a6LM

# Python for downstream analysis
pip install pandas numpy matplotlib scipy
```

## Quick Start

```bash
# Run GWAS: linear regression for quantitative trait
plink2 \
    --bfile cohort_qc \
    --pheno phenotypes.txt \
    --covar covariates.txt \
    --linear hide-covar \
    --out results/gwas_result \
    --threads 8

# View top hits
head results/gwas_result.*.glm.linear | sort -k12,12g | head -20
```

## Workflow

### Step 1: Convert VCF/Imputed Data to PLINK Binary Format

Convert input genotype data to PLINK binary format for fast processing.

```bash
# Convert VCF to PLINK binary
plink2 \
    --vcf cohort_genotyped.vcf.gz \
    --make-bed \
    --out cohort_plink \
    --threads 8

# Convert BGEN (imputed data from Michigan/TopMed imputation server)
plink2 \
    --bgen cohort_imputed.bgen ref-first \
    --sample cohort_imputed.sample \
    --make-bed \
    --out cohort_imputed_plink \
    --threads 8

echo "Files created:"
ls -lh cohort_plink.{bed,bim,fam}
echo "Samples: $(wc -l < cohort_plink.fam)"
echo "Variants: $(wc -l < cohort_plink.bim)"
```

### Step 2: Sample QC — Missingness and Heterozygosity

Remove samples with high missingness or heterozygosity outliers.

```bash
# Compute per-sample and per-variant missingness
plink2 \
    --bfile cohort_plink \
    --missing \
    --out qc/sample_missingness \
    --threads 8

# Remove samples with > 2% missingness and variants with > 5% missing
plink2 \
    --bfile cohort_plink \
    --mind 0.02 \
    --geno 0.05 \
    --make-bed \
    --out cohort_sample_qc \
    --threads 8

echo "After sample QC:"
echo "Samples: $(wc -l < cohort_sample_qc.fam)"
echo "Variants: $(wc -l < cohort_sample_qc.bim)"
```

### Step 3: Variant QC — MAF, HWE, and INFO Score Filtering

Filter variants by minor allele frequency, Hardy-Weinberg equilibrium, and imputation quality.

```bash
# Variant QC: MAF, HWE, missingness
plink2 \
    --bfile cohort_sample_qc \
    --maf 0.01 \
    --hwe 1e-6 \
    --geno 0.05 \
    --make-bed \
    --out cohort_variantqc \
    --threads 8

echo "After variant QC:"
echo "Variants remaining: $(wc -l < cohort_variantqc.bim)"

# For imputed data: also filter by INFO score (using VCF INFO field)
# plink2 --bfile cohort_variantqc --var-min-qual 0.8 --make-bed --out cohort_info_qc
```

### Step 4: LD Pruning and PCA for Population Stratification

Compute principal components from LD-pruned variants.

```bash
# LD pruning: remove one variant from each pair with r² > 0.2
plink2 \
    --bfile cohort_variantqc \
    --indep-pairwise 50 5 0.2 \
    --out qc/ld_pruned \
    --threads 8

# Compute PCA on LD-pruned variants (top 20 PCs)
plink2 \
    --bfile cohort_variantqc \
    --extract qc/ld_pruned.prune.in \
    --pca 20 \
    --out pca/cohort_pca \
    --threads 8

echo "PCA files: pca/cohort_pca.eigenvec (PCs) and pca/cohort_pca.eigenval (variance)"
head pca/cohort_pca.eigenvec
```

### Step 5: Run GWAS Association Analysis

Perform logistic regression (case-control) or linear regression (quantitative trait).

```bash
# Case-control GWAS: logistic regression with covariates
plink2 \
    --bfile cohort_variantqc \
    --pheno phenotypes.txt \
    --1 \
    --covar covariates.txt \
    --covar-variance-standardize \
    --logistic hide-covar \
    --ci 0.95 \
    --out results/gwas_cc \
    --threads 8

# Quantitative trait GWAS: linear regression
plink2 \
    --bfile cohort_variantqc \
    --pheno phenotypes.txt \
    --covar covariates.txt \
    --covar-variance-standardize \
    --linear hide-covar \
    --ci 0.95 \
    --out results/gwas_qt \
    --threads 8

echo "GWAS complete. Files: results/gwas_*.glm.*"
wc -l results/gwas_qt.*.glm.linear
```

### Step 6: Plot Manhattan and QQ Plots

Visualize GWAS results with Python.

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chi2

# Load GWAS results (PLINK2 linear output)
df = pd.read_csv("results/gwas_qt.PHENO1.glm.linear", sep="\t",
                 usecols=["#CHROM", "POS", "ID", "P"])
df.columns = ["CHR", "POS", "SNP", "P"]
df = df.dropna(subset=["P"])
df["P"] = pd.to_numeric(df["P"], errors="coerce")
df = df[df["P"] > 0].copy()
df["-log10P"] = -np.log10(df["P"])

print(f"Variants: {len(df)}")
print(f"Genome-wide significant (p<5e-8): {(df['P'] < 5e-8).sum()}")

# Manhattan plot
fig, ax = plt.subplots(figsize=(14, 4))
colors = plt.cm.Set1.colors
chrom_pos = 0
ticks = []
for chrom, group in df.groupby("CHR", sort=False):
    col = colors[int(chrom) % 2] if str(chrom).isdigit() else "gray"
    ax.scatter(group["POS"] + chrom_pos, group["-log10P"],
               c=[col], s=2, alpha=0.7)
    ticks.append((chrom_pos + group["POS"].mean(), str(chrom)))
    chrom_pos += group["POS"].max() + 1e7

ax.axhline(-np.log10(5e-8), color="red", linestyle="--", lw=1, label="p=5×10⁻⁸")
ax.set_xticks([t[0] for t in ticks[::2]])
ax.set_xticklabels([t[1] for t in ticks[::2]], fontsize=6)
ax.set_xlabel("Chromosome")
ax.set_ylabel("-log₁₀(p)")
ax.set_title("GWAS Manhattan Plot")
plt.tight_layout()
plt.savefig("manhattan.png", dpi=150)
print("Saved: manhattan.png")
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `--maf` | — | 0–0.5 | Minor allele frequency threshold; `0.01` removes singletons |
| `--hwe` | — | 0–1 | Hardy-Weinberg equilibrium p-value threshold; `1e-6` typical |
| `--geno` | — | 0–1 | Maximum variant missingness; `0.05` = 5% |
| `--mind` | — | 0–1 | Maximum sample missingness; `0.02` = 2% |
| `--linear` / `--logistic` | — | flag | Regression mode: linear for quantitative, logistic for case-control |
| `--covar` | — | file path | Covariate file (FID IID COV1 COV2...); add PCs here |
| `--pca` | — | integer | Number of PCs to compute from LD-pruned data |
| `--indep-pairwise` | — | window step r² | LD pruning: window size (variants), step, r² threshold |
| `--threads` | `1` | 1–64 | CPU threads; 8–16 typical for cluster |
| `--ci` | — | 0–1 | Confidence interval for effect size output (0.95 for 95% CI) |
| `--1` | off | flag | Recode phenotype: 1=control, 2=case → 0=control, 1=case (logistic) |

## Common Recipes

### Recipe 1: Relatedness QC and Remove One from Each Related Pair

```bash
# Compute kinship coefficients (King-robust estimator)
plink2 \
    --bfile cohort_variantqc \
    --extract qc/ld_pruned.prune.in \
    --king-cutoff 0.0625 \
    --out qc/kinship \
    --threads 8

# Remove related individuals (king-cutoff auto-generates exclusion list)
plink2 \
    --bfile cohort_variantqc \
    --remove qc/kinship.king.cutoff.out.id \
    --make-bed \
    --out cohort_unrelated \
    --threads 8

echo "After relatedness QC: $(wc -l < cohort_unrelated.fam) samples"
```

### Recipe 2: Parse GWAS Results and Report Top Hits

```python
import pandas as pd
import numpy as np

def load_gwas_results(filepath: str, p_threshold: float = 5e-8) -> pd.DataFrame:
    """Load PLINK2 GWAS linear/logistic output and return genome-wide significant hits."""
    df = pd.read_csv(filepath, sep="\t",
                     usecols=["#CHROM", "POS", "ID", "REF", "ALT", "A1", "BETA", "SE", "P"])
    df.columns = ["CHR", "POS", "SNP", "REF", "ALT", "A1", "BETA", "SE", "P"]
    df = df.dropna(subset=["P"])
    df["P"] = pd.to_numeric(df["P"], errors="coerce")
    sig = df[df["P"] < p_threshold].sort_values("P")
    return sig

# Load results for one phenotype
hits = load_gwas_results("results/gwas_qt.PHENO1.glm.linear")
print(f"Genome-wide significant loci: {len(hits)}")
print(hits.head(10)[["CHR", "POS", "SNP", "BETA", "SE", "P"]])
hits.to_csv("gwas_top_hits.tsv", sep="\t", index=False)
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `*.glm.linear` | TSV | Linear GWAS results: CHR, POS, ID, BETA, SE, P per variant |
| `*.glm.logistic.hybrid` | TSV | Logistic GWAS results: OR, 95% CI, P per variant |
| `*.eigenvec` | TSV | PCA loadings: FID IID PC1 PC2 ... PC20 |
| `*.eigenval` | Text | Eigenvalues for PCA variance explained |
| `*.king.cutoff.out.id` | TSV | Sample IDs to remove for relatedness QC |
| `*.bed/.bim/.fam` | Binary | PLINK binary format after QC filtering |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Error: No samples left after --mind filter` | Missingness threshold too strict | Relax to `--mind 0.05`; check input data quality |
| Logistic regression fails to converge | Rare variant, few cases, or collinear covariates | Use `--logistic firth` for Firth regression; remove correlated covariates |
| PCA shows clear outlier cluster | Admixed population or sample contamination | Remove outliers using PC cutoffs; check ancestry with 1000 Genomes reference panel |
| `--hwe` removes too many variants | Population structure inflating HWE test | Apply HWE filter to controls only: `--hwe 1e-6 ctrl-only` |
| BGEN import fails | Wrong ref-first/ref-last flag | Check imputation server documentation; try `--bgen file.bgen ref-last` |
| Very slow association test | Too many covariates or large file | Pre-filter to GWAS-significant window; use `--threads 16` |
| Sex mismatch warnings | X chromosome heterozygosity outside sex-specific thresholds | Run `--check-sex` and remove F-statistic outliers |
| Memory error on large dataset | RAM insufficient for 500k+ variants | Use `--memory 32000` to cap RAM; split by chromosome |

## References

- [PLINK2 documentation](https://www.cog-genomics.org/plink/2.0/) — official command reference and tutorials
- [PLINK2 GitHub: chrchang/plink-ng](https://github.com/chrchang/plink-ng) — source code and releases
- Chang CC et al. (2015) "Second-generation PLINK: rising to the challenge of larger and richer datasets" — *GigaScience* 4:7. [DOI:10.1186/s13742-015-0047-8](https://doi.org/10.1186/s13742-015-0047-8)
- [GWAS best practices (Marees et al. 2018)](https://doi.org/10.1002/mpr.1608) — comprehensive QC and analysis guide
