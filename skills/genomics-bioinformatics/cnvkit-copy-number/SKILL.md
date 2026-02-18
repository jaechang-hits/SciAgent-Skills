---
name: "cnvkit-copy-number"
description: "Detect somatic copy number variants (CNVs) from WES, WGS, or targeted sequencing BAM files with CNVkit v0.9.x. Pipeline: calculate bin-level coverage in target/antitarget regions, normalize against a reference, segment copy ratios with CBS or HMM, call amplifications and deletions, generate scatter/diagram plots, estimate tumor purity and ploidy, and export to VCF/SEG. Both CLI and Python API (cnvlib) shown. Use GATK CNV instead for deep WGS with population-scale controls; use CNVkit for targeted or exome sequencing where antitarget bins are critical."
license: "Apache-2.0"
---

# CNVkit Copy Number Analysis

## Overview

CNVkit detects somatic copy number variants (CNVs) from whole-exome sequencing (WES), whole-genome sequencing (WGS), or targeted panel BAM files. It calculates read depth in both on-target (capture) bins and off-target (antitarget) bins, corrects for GC bias and library depth, segments the log2 copy ratio profile with circular binary segmentation (CBS) or a hidden Markov model (HMM), and calls amplifications and deletions. CNVkit provides both a CLI (`cnvkit.py`) and a Python API (`cnvlib`) for integration into analysis pipelines, and produces scatter plots, chromosome diagrams, heatmaps, and export files in VCF, BED, and SEG formats.

## When to Use

- Calling somatic copy number variants from tumor-normal paired exome (WES) or targeted panel sequencing
- Detecting copy number alterations in tumor-only samples using a pooled normal reference
- Running CNV analysis on whole-genome sequencing (WGS) data with the `--method wgs` mode
- Estimating tumor purity and ploidy for samples where purity is unknown, to interpret copy ratio calls
- Generating SEG format copy number files for GISTIC2, cBioPortal, or IGV visualization
- Identifying focal amplifications (e.g., ERBB2, MYC) or homozygous deletions (e.g., CDKN2A, RB1)
- Use **GATK CNV** (`gatk DenoiseReadCounts` / `gatk ModelSegments`) instead for deep WGS cohorts with large matched panel-of-normals (PoN); CNVkit is better suited for targeted/exome data
- Use **Control-FREEC** instead when you need allele-frequency-based B-allele fraction modeling alongside CNV calling

## Prerequisites

- **Software**: CNVkit v0.9.x, Python 3.8+, R (for CBS segmentation), samtools
- **Python packages**: `cnvlib` (installed as part of CNVkit), `matplotlib`, `pandas`
- **Input files**: sorted, indexed BAM files (tumor ± matched normal); BED file of capture targets; reference genome FASTA; access to R with DNAcopy package for CBS
- **Data requirements**: minimum ~50× mean target coverage for WES; WGS works at 20-30×

```bash
# Install CNVkit via conda (recommended — handles R/DNAcopy dependency)
conda install -c bioconda cnvkit

# Or via pip (requires R + DNAcopy already installed)
pip install cnvkit

# Verify
cnvkit.py version
# cnvkit 0.9.10

# Install R DNAcopy (for CBS segmentation)
Rscript -e 'if (!requireNamespace("BiocManager")) install.packages("BiocManager"); BiocManager::install("DNAcopy")'

# Index BAM files if not already indexed
samtools index tumor.bam
samtools index normal.bam
```

## Quick Start

```bash
# One-command paired tumor/normal CNV analysis (WES)
cnvkit.py batch tumor.bam \
    --normal normal.bam \
    --targets targets.bed \
    --fasta GRCh38.fa \
    --output-dir cnvkit_results/ \
    --diagram --scatter \
    --method hybrid

# Output files in cnvkit_results/:
#   tumor.targetcoverage.cnn   — target bin coverage
#   tumor.antitargetcoverage.cnn — antitarget coverage
#   tumor.cnr                  — copy number ratios
#   tumor.cns                  — segmented copy numbers
#   tumor-scatter.png          — genome-wide scatter plot
#   tumor-diagram.pdf          — chromosome diagram
echo "CNV analysis complete"
```

## Workflow

### Step 1: Create Copy Number Reference

Build a reference from one or more normal BAM files. This corrects for systematic biases (GC content, mappability) and sets the neutral baseline.

```bash
# Option A: Paired normal reference (single matched normal)
cnvkit.py reference normal.targetcoverage.cnn normal.antitargetcoverage.cnn \
    --fasta GRCh38.fa \
    -o reference_normal.cnn

# Option B: Flat reference (no normal; uses GC/mappability correction only)
# Use when no matched normal is available
cnvkit.py reference \
    --targets targets.bed \
    --fasta GRCh38.fa \
    --output flat_reference.cnn

# Option C: Pooled normal reference from multiple normals (most robust)
cnvkit.py batch \
    normal1.bam normal2.bam normal3.bam \
    --normal \
    --targets targets.bed \
    --fasta GRCh38.fa \
    --output-reference pooled_reference.cnn \
    --output-dir normals_cov/

echo "Reference created: pooled_reference.cnn"
```

### Step 2: Calculate Coverage in Target and Antitarget Bins

Bin the target BED file and compute per-bin read depth for tumor and normal samples.

```bash
# First, create accessible bins from the target BED
cnvkit.py target targets.bed \
    --annotate refFlat.txt \
    --split \
    -o targets.split.bed

cnvkit.py antitarget targets.bed \
    --access data/access-5k-mappable.hg38.bed \
    -o antitargets.bed

# Calculate coverage for tumor sample
cnvkit.py coverage tumor.bam targets.split.bed \
    -o tumor.targetcoverage.cnn

cnvkit.py coverage tumor.bam antitargets.bed \
    -o tumor.antitargetcoverage.cnn

echo "Coverage files:"
echo "  tumor.targetcoverage.cnn"
echo "  tumor.antitargetcoverage.cnn"
```

```python
# Python API equivalent: compute coverage with cnvlib
import cnvlib

# Load and inspect coverage files
target_cov = cnvlib.read("tumor.targetcoverage.cnn")
antitarget_cov = cnvlib.read("tumor.antitargetcoverage.cnn")

print(f"Target bins: {len(target_cov)}")
print(f"Antitarget bins: {len(antitarget_cov)}")
print(f"Mean target depth: {target_cov['depth'].mean():.1f}×")
print(f"Median target depth: {target_cov['depth'].median():.1f}×")

# Check coverage distribution
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4))
target_cov["depth"].clip(upper=500).hist(bins=50, ax=ax, color="#2c6fad", alpha=0.7)
ax.set_xlabel("Read depth")
ax.set_ylabel("Bin count")
ax.set_title("Target bin coverage distribution")
plt.tight_layout()
plt.savefig("coverage_distribution.png", dpi=150)
print("Saved: coverage_distribution.png")
```

### Step 3: Normalize and Correct Copy Ratios

Normalize tumor coverage against the reference (correcting for GC bias, library depth, and target efficiency).

```bash
# Fix sample-level biases relative to the reference
cnvkit.py fix \
    tumor.targetcoverage.cnn \
    tumor.antitargetcoverage.cnn \
    pooled_reference.cnn \
    -o tumor.cnr

echo "Copy number ratios: tumor.cnr"
# tumor.cnr columns: chromosome, start, end, gene, log2, depth, weight
```

```python
# Inspect copy ratio file with cnvlib Python API
import cnvlib
import pandas as pd

cnr = cnvlib.read("tumor.cnr")
print(f"Total bins: {len(cnr)}")
print(f"Chromosomes: {sorted(cnr.chromosome.unique())}")

# Convert to DataFrame and inspect
df = cnr.data
print(f"\nLog2 copy ratio summary:")
print(df["log2"].describe().round(3))

# Flag high-amplitude events
high_amp = df[df["log2"] >= 2.0]
hom_del  = df[df["log2"] <= -3.0]
print(f"\nHigh amplitude bins (log2 >= 2.0): {len(high_amp)}")
print(f"Homozygous deletion bins (log2 <= -3.0): {len(hom_del)}")
if not high_amp.empty:
    print(high_amp[["chromosome", "start", "end", "gene", "log2"]].head())
```

### Step 4: Segment Copy Number Ratios

Identify contiguous regions of similar copy ratio using CBS (Circular Binary Segmentation) or HMM segmentation.

```bash
# CBS segmentation (default; requires R DNAcopy)
cnvkit.py segment tumor.cnr \
    -o tumor.cns \
    --method cbs

# HMM segmentation (no R required; faster)
cnvkit.py segment tumor.cnr \
    -o tumor.hmm.cns \
    --method hmm

echo "Segments: tumor.cns"
# tumor.cns columns: chromosome, start, end, gene, log2, cn, depth, p_ttest, weight, probes
```

```python
# Python API: segment and inspect
import cnvlib
import subprocess

# Run segmentation via Python subprocess (mirrors CLI)
subprocess.run(
    ["cnvkit.py", "segment", "tumor.cnr", "-o", "tumor.cns", "--method", "cbs"],
    check=True
)

# Load and analyze segments
cns = cnvlib.read("tumor.cns")
df_seg = cns.data
print(f"Total segments: {len(df_seg)}")
print(f"\nSegment log2 summary:")
print(df_seg["log2"].describe().round(3))

# Large segments (>5 Mb) with copy gain or loss
large_events = df_seg[
    ((df_seg["end"] - df_seg["start"]) > 5_000_000) &
    (df_seg["log2"].abs() > 0.3)
].copy()
large_events["size_mb"] = (large_events["end"] - large_events["start"]) / 1e6
print(f"\nLarge CNV segments (>5 Mb, |log2|>0.3): {len(large_events)}")
print(large_events[["chromosome", "start", "end", "log2", "size_mb"]].head(8).to_string(index=False))
```

### Step 5: Call CNV States

Assign integer copy number states and classify amplifications and deletions.

```bash
# Call with default thresholds (diploid normal)
cnvkit.py call tumor.cns \
    -o tumor.call.cns \
    --ploidy 2

# Call with tumor purity estimate (if known)
cnvkit.py call tumor.cns \
    --purity 0.7 \
    --ploidy 2 \
    -o tumor.call.purity.cns

echo "Called CNVs: tumor.call.cns"
```

```python
# Parse called CNV file and classify events
import cnvlib
import pandas as pd

cns_called = cnvlib.read("tumor.call.cns")
df = cns_called.data

# Classify by log2 thresholds (diploid assumed)
# log2 >= 1.0 = high-level amplification (CN >= 4)
# log2 0.2–1.0 = copy gain (CN = 3)
# log2 -1.0–-0.2 = heterozygous deletion (CN = 1)
# log2 <= -3.5 = homozygous deletion (CN = 0)

def classify_cnv(log2):
    if log2 >= 1.0:    return "AMP"
    if log2 >= 0.2:    return "GAIN"
    if log2 <= -3.5:   return "HOMDEL"
    if log2 <= -1.0:   return "LOSS"
    return "NEUTRAL"

df["cnv_class"] = df["log2"].apply(classify_cnv)
print("CNV class counts:")
print(df["cnv_class"].value_counts().to_string())

# Focal amplifications in known oncogenes
oncogenes = ["ERBB2", "MYC", "EGFR", "CCND1", "CDK6", "MDM2", "KRAS"]
focal_amps = df[(df["cnv_class"] == "AMP") &
                (df["gene"].str.split(",").apply(
                    lambda genes: any(g in oncogenes for g in genes)))]
if not focal_amps.empty:
    print(f"\nFocal amplifications in oncogenes:")
    print(focal_amps[["chromosome", "start", "end", "gene", "log2", "cn"]].to_string(index=False))
```

### Step 6: Visualize CNV Profile

Generate scatter plots and chromosome diagrams to review the copy number landscape.

```bash
# Genome-wide scatter plot (CNR bins + segments)
cnvkit.py scatter tumor.cnr \
    -s tumor.cns \
    -o tumor-scatter.png

# Chromosome diagram (color-coded by CN state)
cnvkit.py diagram tumor.cnr \
    -s tumor.cns \
    -o tumor-diagram.pdf

# Heatmap across multiple samples
cnvkit.py heatmap sample1.cns sample2.cns sample3.cns \
    -o cohort_heatmap.pdf

echo "Plots saved: tumor-scatter.png, tumor-diagram.pdf, cohort_heatmap.pdf"
```

```python
# Custom scatter plot with matplotlib highlighting specific genes
import cnvlib
import matplotlib.pyplot as plt
import numpy as np

cnr = cnvlib.read("tumor.cnr")
cns = cnvlib.read("tumor.cns")

# Plot chr7 (EGFR locus) in detail
fig, ax = plt.subplots(figsize=(12, 4))
chrom = "chr7"
cnr_chr = cnr.data[cnr.data["chromosome"] == chrom]
cns_chr = cns.data[cns.data["chromosome"] == chrom]

# Bin dots
ax.scatter(cnr_chr["start"], cnr_chr["log2"],
           s=3, alpha=0.3, color="#aaa", label="Bins")
# Segment lines
for _, seg in cns_chr.iterrows():
    ax.hlines(seg["log2"], seg["start"], seg["end"],
              colors=("#d32f2f" if seg["log2"] > 0.3 else
                      "#1565c0" if seg["log2"] < -0.3 else "#666"),
              lw=3, label="_nolegend_")

# Mark EGFR
egfr_start, egfr_end = 55_019_017, 55_211_628
ax.axvspan(egfr_start, egfr_end, alpha=0.15, color="orange")
ax.text((egfr_start + egfr_end) / 2, ax.get_ylim()[1] * 0.85,
        "EGFR", ha="center", fontsize=9, color="darkorange")

ax.axhline(0, color="black", lw=0.8, ls="--")
ax.axhline(0.585, color="#d32f2f", lw=0.5, ls=":")   # gain threshold
ax.axhline(-1.0, color="#1565c0", lw=0.5, ls=":")    # loss threshold
ax.set_xlabel("Chromosome 7 position (bp)")
ax.set_ylabel("Log2 copy ratio")
ax.set_title(f"CNV Profile — {chrom}")
plt.tight_layout()
plt.savefig("chr7_cnv_scatter.png", dpi=150, bbox_inches="tight")
print("Saved: chr7_cnv_scatter.png")
```

### Step 7: Estimate Tumor Purity and Ploidy

Use CNVkit's purity/ploidy estimation to interpret absolute copy numbers.

```bash
# Estimate purity and ploidy from the segmented CNV profile
cnvkit.py call tumor.cns \
    --purity auto \
    --ploidy 2 \
    --method clonal \
    -o tumor.call.auto.cns \
    --center median

# Print purity/ploidy estimate embedded in header
head -5 tumor.call.auto.cns
```

```python
# Python API: purity/ploidy estimation with cnvlib
import cnvlib
from cnvlib import segmetrics

cns = cnvlib.read("tumor.cns")
cnr = cnvlib.read("tumor.cnr")

# Compute segment-level statistics
cns_with_stats = segmetrics.do_segmetrics(cnr, cns,
    location_stats=["mean", "median"],
    spread_stats=["stdev"])

# Export stats to CSV for review
df = cns_with_stats.data
df.to_csv("tumor_segment_stats.csv", index=False)
print(f"Segment stats saved: tumor_segment_stats.csv")
print(f"Segments: {len(df)}")
print(df[["chromosome", "start", "end", "log2", "cn", "mean", "stdev"]].head(8).to_string(index=False))
```

### Step 8: Export to VCF, BED, and SEG Formats

Export CNV calls for downstream tools (GISTIC2, cBioPortal, IGV, clinical reporting).

```bash
# Export to VCF (for clinical variant databases)
cnvkit.py export vcf tumor.call.cns \
    -o tumor.cnv.vcf

# Export to SEG format (for GISTIC2 and cBioPortal)
cnvkit.py export seg tumor.call.cns \
    -o tumor.seg

# Export to BED format (for bedtools/IGV)
cnvkit.py export bed tumor.call.cns \
    -o tumor.cnv.bed

echo "Exported:"
echo "  tumor.cnv.vcf   — VCF format"
echo "  tumor.seg       — SEG format (GISTIC2 / cBioPortal)"
echo "  tumor.cnv.bed   — BED format (IGV / bedtools)"
```

```python
# Parse and summarize SEG file
import pandas as pd

seg = pd.read_csv("tumor.seg", sep="\t",
                  names=["sample", "chrom", "start", "end", "n_probes", "log2"],
                  comment="#")
print(f"SEG file: {len(seg)} segments")
print(seg.head())

# Count amplifications and deletions by chromosome arm
amp_count = (seg["log2"] >= 0.585).sum()
del_count  = (seg["log2"] <= -1.0).sum()
print(f"\nAmplifications (log2 >= 0.585): {amp_count}")
print(f"Deletions (log2 <= -1.0):       {del_count}")
seg.to_csv("tumor_seg_annotated.csv", index=False)
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `--method` (batch/coverage) | `"hybrid"` | `"hybrid"`, `"wgs"`, `"amplicon"` | Sequencing method; selects target binning strategy |
| `--segment-method` (segment) | `"cbs"` | `"cbs"`, `"hmm"`, `"haar"`, `"none"` | Segmentation algorithm; CBS requires R DNAcopy |
| `--ploidy` (call) | `2` | `1`–`6` | Assumed baseline ploidy for absolute CN calling |
| `--purity` (call) | `1.0` | `0.1`–`1.0` or `"auto"` | Tumor cell fraction; corrects log2 ratios for admixed normal |
| `--target-avg-size` (target) | `200` (WES) | `50`–`500` bp | Desired mean target bin size after splitting |
| `--antitarget-avg-size` | `150000` | `10000`–`500000` bp | Antitarget bin size (larger = fewer bins, less noise) |
| `--drop-low-coverage` (segment) | off | flag | Drop bins with depth < 5× before segmentation |
| `-p` / `--processes` (coverage) | `1` | `1`–CPU count | Parallel processes for coverage calculation |
| `--scatter` (batch) | off | flag | Automatically generate scatter plot |
| `--diagram` (batch) | off | flag | Automatically generate chromosome diagram |

## Common Recipes

### Recipe: Tumor-Only Analysis with Flat Reference

When to use: No matched normal is available; use a flat GC/mappability-corrected reference.

```bash
# Step 1: Create flat reference
cnvkit.py reference \
    --targets targets.bed \
    --fasta GRCh38.fa \
    --output flat_reference.cnn

# Step 2: Run batch on tumor-only
cnvkit.py batch tumor.bam \
    --reference flat_reference.cnn \
    --output-dir tumor_only_results/

echo "Tumor-only results: tumor_only_results/"
```

### Recipe: WGS Mode for Whole-Genome Data

When to use: Input is whole-genome sequencing (no capture BED needed).

```bash
# WGS mode uses a uniform genome-wide bin grid
cnvkit.py batch tumor_wgs.bam \
    --normal normal_wgs.bam \
    --method wgs \
    --fasta GRCh38.fa \
    --output-dir wgs_results/ \
    --scatter

echo "WGS CNV analysis complete: wgs_results/"
```

### Recipe: Snakemake Integration for Multi-Sample Cohort

When to use: Automate CNVkit for a cohort of paired tumor/normal samples.

```python
# Snakefile — CNVkit batch pipeline
configfile: "config.yaml"
SAMPLES = config["tumor_samples"]   # list of sample names
GENOME  = config["genome_fasta"]
TARGETS = config["targets_bed"]
POOLED  = config["pooled_reference"]  # pre-built pooled normal reference

rule all:
    input:
        expand("cnvkit/{sample}.call.cns", sample=SAMPLES),
        expand("cnvkit/{sample}-scatter.png", sample=SAMPLES),

rule cnvkit_batch:
    input:
        tumor  = "bam/{sample}.tumor.bam",
        ref    = POOLED,
    output:
        cnr    = "cnvkit/{sample}.cnr",
        cns    = "cnvkit/{sample}.cns",
        call   = "cnvkit/{sample}.call.cns",
        scatter = "cnvkit/{sample}-scatter.png",
    threads: 4
    shell:
        """
        cnvkit.py batch {input.tumor} \
            --reference {input.ref} \
            --targets {TARGETS} \
            --fasta {GENOME} \
            --output-dir cnvkit/ \
            --scatter --processes {threads}
        cnvkit.py call cnvkit/{wildcards.sample}.cns \
            --ploidy 2 -o {output.call}
        """
```

### Recipe: Export Gene-Level CNV Table

When to use: Summarize copy number status for a panel of cancer genes from a called CNS file.

```python
import cnvlib
import pandas as pd

cns = cnvlib.read("tumor.call.cns")
df = cns.data

# Cancer genes of interest
cancer_genes = ["ERBB2", "MYC", "EGFR", "CDKN2A", "RB1", "TP53",
                "KRAS", "PTEN", "BRCA1", "BRCA2", "MDM2", "CDK4"]

rows = []
for gene in cancer_genes:
    hits = df[df["gene"].str.contains(gene, na=False)]
    if hits.empty:
        rows.append({"gene": gene, "log2_mean": float("nan"), "cn": "n/a", "status": "not_detected"})
    else:
        best = hits.loc[hits["log2"].abs().idxmax()]
        status = ("AMP" if best["log2"] >= 1.0 else
                  "GAIN" if best["log2"] >= 0.2 else
                  "HOMDEL" if best["log2"] <= -3.5 else
                  "LOSS" if best["log2"] <= -1.0 else "NEUTRAL")
        rows.append({"gene": gene, "log2_mean": round(best["log2"], 3),
                     "cn": best.get("cn", "?"), "status": status})

result_df = pd.DataFrame(rows)
print(result_df.to_string(index=False))
result_df.to_csv("cancer_gene_cnv_summary.csv", index=False)
print("\nSaved: cancer_gene_cnv_summary.csv")
```

## Expected Outputs

| Output File | Format | Description |
|-------------|--------|-------------|
| `tumor.targetcoverage.cnn` | CNN | Per-bin target region read depth and log2 coverage |
| `tumor.antitargetcoverage.cnn` | CNN | Per-bin antitarget region coverage (off-target reads) |
| `tumor.cnr` | CNR | Normalized log2 copy ratio per bin (GC/depth corrected) |
| `tumor.cns` | CNS | Segmented copy ratios (CBS/HMM output); one row per segment |
| `tumor.call.cns` | CNS | Called copy number states with integer CN and purity adjustment |
| `tumor-scatter.png` | PNG | Genome-wide scatter plot of bins + segment overlays |
| `tumor-diagram.pdf` | PDF | Chromosome arm diagram color-coded by CN state |
| `tumor.seg` | SEG | GISTIC2/cBioPortal-format segment file |
| `tumor.cnv.vcf` | VCF | VCF-format CNV calls for clinical databases |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| High noise in antitarget bins | Low off-target coverage (<0.1× mean) | Increase `--antitarget-avg-size` to 500kb; use `--drop-low-coverage` to exclude low bins before segmentation |
| CBS segmentation fails with `Error in DNAcopy` | R DNAcopy not installed or incompatible | Install via `BiocManager::install("DNAcopy")`; alternatively use `--method hmm` (no R required) |
| All segments near 0 (no CNVs detected) | Low tumor purity (<20%) or shallow coverage | Verify purity with `cnvkit.py call --purity auto`; check target coverage depth with `cnvkit.py coverage` |
| Wavy GC bias across chromosomes | GC normalization failed or flat reference used with biased tumor | Rebuild reference with matched normal BAMs; check `cnvkit.py reference` includes `--fasta` for GC correction |
| Many very short segments (over-segmentation) | CBS threshold too sensitive | Add `--threshold 0.2` or `--smooth-cbs` to reduce false segment boundaries; increase minimum segment size |
| `ImportError: No module named cnvlib` | CNVkit not installed in active environment | Activate the correct conda env: `conda activate cnvkit_env`; verify `cnvkit.py version` |
| Chromosome naming mismatch | BAM uses `1` but reference uses `chr1` or vice versa | Ensure BAM, BED, and FASTA all use the same chromosome naming convention |

## References

- [CNVkit documentation](https://cnvkit.readthedocs.io) — full CLI and API reference, algorithm details, and tutorials
- [Talevich E et al. (2016) PLoS Comput Biol 12(4): e1004873](https://doi.org/10.1371/journal.pcbi.1004873) — CNVkit original paper with algorithm description and benchmarks
- [CNVkit GitHub: etal/cnvkit](https://github.com/etal/cnvkit) — source code, issue tracker, and example datasets
- [UCSC Genome Browser data files](https://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/) — refFlat and access BED files used in CNVkit preprocessing
