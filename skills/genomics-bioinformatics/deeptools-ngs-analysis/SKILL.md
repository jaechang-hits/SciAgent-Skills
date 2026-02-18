---
name: deeptools-ngs-analysis
description: "NGS analysis CLI toolkit for ChIP-seq, RNA-seq, ATAC-seq. BAM→bigWig conversion with normalization (RPGC, CPM, RPKM), sample correlation/PCA, heatmaps and profile plots around genomic features, enrichment fingerprints. For alignment use STAR/BWA; for peak calling use MACS2."
license: BSD-3-Clause
---

# deepTools — NGS Data Analysis Toolkit

## Overview

deepTools is a command-line toolkit for processing and visualizing high-throughput sequencing data. It converts BAM alignments to normalized coverage tracks (bigWig), performs quality control (correlation, PCA, fingerprint), and generates publication-quality heatmaps and profile plots around genomic features. Supports ChIP-seq, RNA-seq, ATAC-seq, and MNase-seq.

## When to Use

- Converting BAM files to normalized bigWig coverage tracks
- Comparing ChIP-seq treatment vs input control (log2 ratio tracks)
- Assessing sample quality: replicate correlation, PCA, coverage depth
- Evaluating ChIP enrichment strength (fingerprint plots)
- Creating heatmaps and profile plots around TSS, peaks, or other genomic regions
- Analyzing ATAC-seq data with Tn5 offset correction
- Generating strand-specific RNA-seq coverage tracks
- For **read alignment**, use STAR, BWA, or bowtie2 instead
- For **peak calling**, use MACS2 or HOMER instead
- For **BAM/VCF file manipulation**, use pysam instead

## Prerequisites

```bash
pip install deeptools
# Verify installation
bamCoverage --version
```

**Input requirements**: BAM files must be sorted and indexed (`.bai` file present). Generate index with `samtools index input.bam`. BED files for genomic regions (genes, peaks) in standard 3+ column format.

## Quick Start

```bash
# Convert BAM to normalized bigWig
bamCoverage --bam sample.bam --outFileName sample.bw \
    --normalizeUsing RPGC --effectiveGenomeSize 2913022398 \
    --binSize 10 --numberOfProcessors 8

# Create heatmap around TSS
computeMatrix reference-point -S sample.bw -R genes.bed \
    -b 3000 -a 3000 --referencePoint TSS -o matrix.gz
plotHeatmap -m matrix.gz -o heatmap.png --colorMap RdBu
```

## Core API

### 1. BAM to Coverage Conversion

Convert BAM alignments to normalized coverage tracks (bigWig or bedGraph).

```bash
# Basic conversion with RPGC normalization
bamCoverage --bam input.bam --outFileName output.bw \
    --normalizeUsing RPGC --effectiveGenomeSize 2913022398 \
    --binSize 10 --numberOfProcessors 8 \
    --extendReads 200 --ignoreDuplicates

# CPM normalization (simpler, no genome size needed)
bamCoverage --bam input.bam --outFileName output.bw \
    --normalizeUsing CPM --binSize 10 -p 8

# RNA-seq: strand-specific coverage
bamCoverage --bam rnaseq.bam --outFileName forward.bw \
    --filterRNAstrand forward --normalizeUsing CPM -p 8
# IMPORTANT: Never use --extendReads for RNA-seq (spans splice junctions)
```

### 2. Sample Comparison

Compare treatment vs control or generate ratio tracks.

```bash
# Log2 ratio: treatment / control
bamCompare -b1 treatment.bam -b2 control.bam -o log2ratio.bw \
    --operation log2 --scaleFactorsMethod readCount \
    --extendReads 200 -p 8

# Subtract control from treatment
bamCompare -b1 treatment.bam -b2 control.bam -o subtract.bw \
    --operation subtract --scaleFactorsMethod readCount
```

### 3. Quality Control

Assess sample quality, replicate concordance, and enrichment strength.

```bash
# Sample correlation heatmap
multiBamSummary bins --bamfiles rep1.bam rep2.bam rep3.bam \
    -o counts.npz --binSize 10000 -p 8
plotCorrelation -in counts.npz --corMethod pearson \
    --whatToShow heatmap -o correlation.png
# Good: replicates cluster with r > 0.9

# PCA of samples
plotPCA -in counts.npz -o pca.png --plotTitle "Sample PCA"

# ChIP enrichment fingerprint
plotFingerprint -b input.bam chip.bam -o fingerprint.png \
    --extendReads 200 --ignoreDuplicates
# Good ChIP: steep rise curve; flat diagonal = poor enrichment

# Coverage depth assessment
plotCoverage -b sample.bam -o coverage.png --ignoreDuplicates -p 8

# Fragment size distribution (paired-end)
bamPEFragmentSize -b sample.bam -o fragsize.png
```

### 4. Heatmaps and Profile Plots

Visualize signal around genomic features (TSS, peaks, gene bodies).

```bash
# Reference-point mode: signal around TSS
computeMatrix reference-point -S chip.bw -R genes.bed \
    -b 3000 -a 3000 --referencePoint TSS -o matrix.gz -p 8

# Scale-regions mode: signal across gene bodies
computeMatrix scale-regions -S chip.bw -R genes.bed \
    -b 1000 -a 1000 --regionBodyLength 5000 -o matrix.gz -p 8

# Generate heatmap
plotHeatmap -m matrix.gz -o heatmap.png \
    --colorMap RdBu --kmeans 3 --sortUsing mean

# Generate profile plot
plotProfile -m matrix.gz -o profile.png \
    --plotType lines --colors blue red

# Multiple signal files: compare marks
computeMatrix reference-point -S h3k4me3.bw h3k27me3.bw -R genes.bed \
    -b 3000 -a 3000 --referencePoint TSS -o multi_matrix.gz
plotHeatmap -m multi_matrix.gz -o multi_heatmap.png
```

### 5. Read Filtering and Processing

Filter reads before analysis or correct for assay-specific biases.

```bash
# Filter by mapping quality and fragment size
alignmentSieve --bam input.bam --outFile filtered.bam \
    --minMappingQuality 10 --minFragmentLength 150 \
    --maxFragmentLength 700

# ATAC-seq: apply Tn5 offset correction (+4/-5 bp shift)
alignmentSieve --bam atac.bam --outFile shifted.bam --ATACshift
# Then index: samtools index shifted.bam

# GC bias correction (only if significant bias detected)
computeGCBias -b input.bam --effectiveGenomeSize 2913022398 \
    -g genome.2bit --GCbiasFrequenciesFile gc_freq.txt -p 8
correctGCBias -b input.bam --effectiveGenomeSize 2913022398 \
    --GCbiasFrequenciesFile gc_freq.txt -o corrected.bam
```

### 6. Enrichment Analysis

Quantify signal enrichment at specific regions.

```bash
# Signal enrichment at peak regions
plotEnrichment -b chip.bam input.bam --BED peaks.bed \
    -o enrichment.png --ignoreDuplicates -p 8
```

## Key Concepts

### Normalization Methods

| Method | Formula | When to Use | Requires |
|--------|---------|-------------|----------|
| **RPGC** | 1× genome coverage | ChIP-seq, ATAC-seq | `--effectiveGenomeSize` |
| **CPM** | Counts per million | Any assay, quick comparison | Nothing |
| **RPKM** | Per kb per million | RNA-seq gene-level | Nothing |
| **BPM** | Bins per million | Similar to CPM | Nothing |
| **None** | Raw counts | Not recommended for comparison | Nothing |

**Rule**: Use RPGC for ChIP-seq/ATAC-seq (accounts for genome size). Use CPM for quick comparisons. Use RPKM for RNA-seq gene-level analysis.

### Effective Genome Sizes

| Organism | Assembly | Effective Size |
|----------|----------|---------------|
| Human | GRCh38/hg38 | 2,913,022,398 |
| Mouse | GRCm38/mm10 | 2,652,783,500 |
| Zebrafish | GRCz11 | 1,368,780,147 |
| *Drosophila* | dm6 | 142,573,017 |
| *C. elegans* | ce10/ce11 | 100,286,401 |

### computeMatrix Modes

| Mode | Use When | Key Params |
|------|----------|------------|
| `reference-point` | Signal around a fixed point (TSS, peak summit) | `-b`, `-a`, `--referencePoint` |
| `scale-regions` | Signal across variable-length features (gene bodies) | `-b`, `-a`, `--regionBodyLength` |

## Common Workflows

### Workflow: ChIP-seq QC and Visualization

```bash
#!/bin/bash
# Complete ChIP-seq QC + visualization pipeline
CHIP="chip.bam"
INPUT="input.bam"
GENES="genes.bed"
PEAKS="peaks.bed"
GSIZE=2913022398
THREADS=8

# 1. QC: sample correlation
multiBamSummary bins --bamfiles $INPUT $CHIP -o summary.npz -p $THREADS
plotCorrelation -in summary.npz --corMethod pearson --whatToShow heatmap -o correlation.png

# 2. QC: enrichment fingerprint
plotFingerprint -b $INPUT $CHIP -o fingerprint.png --extendReads 200 --ignoreDuplicates

# 3. Convert to normalized bigWig
bamCoverage --bam $CHIP --outFileName chip.bw --normalizeUsing RPGC \
    --effectiveGenomeSize $GSIZE --extendReads 200 --ignoreDuplicates -p $THREADS

# 4. Log2 ratio track
bamCompare -b1 $CHIP -b2 $INPUT -o log2ratio.bw --operation log2 \
    --scaleFactorsMethod readCount --extendReads 200 -p $THREADS

# 5. Heatmap at TSS
computeMatrix reference-point -S chip.bw log2ratio.bw -R $GENES \
    -b 3000 -a 3000 --referencePoint TSS -o tss_matrix.gz -p $THREADS
plotHeatmap -m tss_matrix.gz -o tss_heatmap.png --colorMap RdBu --kmeans 3

# 6. Profile at peaks
computeMatrix reference-point -S chip.bw -R $PEAKS \
    -b 2000 -a 2000 -o peak_matrix.gz -p $THREADS
plotProfile -m peak_matrix.gz -o peak_profile.png
```

### Workflow: ATAC-seq Analysis

```bash
#!/bin/bash
ATAC="atac.bam"
PEAKS="atac_peaks.bed"
GSIZE=2913022398
THREADS=8

# 1. Apply Tn5 offset correction (+4/-5 bp)
alignmentSieve --bam $ATAC --outFile shifted.bam --ATACshift -p $THREADS
samtools index shifted.bam

# 2. Generate RPGC-normalized coverage
bamCoverage --bam shifted.bam --outFileName atac.bw \
    --normalizeUsing RPGC --effectiveGenomeSize $GSIZE \
    --binSize 5 --extendReads -p $THREADS

# 3. Check nucleosome periodicity (expect 200bp/400bp peaks)
bamPEFragmentSize -b shifted.bam -o fragsize.png \
    --maxFragmentLength 1000 --binSize 1

# 4. Heatmap at ATAC peaks
computeMatrix reference-point -S atac.bw -R $PEAKS \
    -b 2000 -a 2000 -o atac_matrix.gz -p $THREADS
plotHeatmap -m atac_matrix.gz -o atac_heatmap.png --colorMap Blues --kmeans 2
```

## Key Parameters

| Parameter | Tool(s) | Default | Range | Effect |
|-----------|---------|---------|-------|--------|
| `--normalizeUsing` | bamCoverage, bamCompare | None | RPGC, CPM, RPKM, BPM, None | Coverage normalization method |
| `--effectiveGenomeSize` | bamCoverage, bamCompare | — | See table above | Required for RPGC normalization |
| `--binSize` | bamCoverage, multiBamSummary | 50 | 1–10000 | Resolution in bp; smaller = larger files |
| `--extendReads` | bamCoverage, bamCompare | False | integer (bp) | Extend to fragment length (ChIP: YES, RNA: NO) |
| `--ignoreDuplicates` | Most tools | False | True/False | Remove PCR duplicates |
| `--numberOfProcessors` | Most tools | 1 | 1–N cores | Parallel processing |
| `--operation` | bamCompare | log2 | log2, ratio, subtract, add, mean, reciprocal_ratio | Sample comparison operation |
| `--referencePoint` | computeMatrix | TSS | TSS, TES, center | Anchor point for reference-point mode |
| `-b` / `-a` | computeMatrix | 500 | 100–10000 bp | Upstream/downstream distance from reference |
| `--kmeans` | plotHeatmap | None | 1–20 | Number of clusters for heatmap rows |
| `--minMappingQuality` | Most tools | None | 0–60 | Minimum alignment quality filter |

## Best Practices

1. **Always extend reads for ChIP-seq**: Use `--extendReads 200` (or actual fragment length) — ChIP fragments are longer than reads.

2. **Never extend reads for RNA-seq**: `--extendReads` would span splice junctions, creating artifacts.

3. **Anti-pattern — comparing with different normalizations**: Always use the same normalization method across all samples in a comparison.

4. **Use `--region` for parameter testing**: Test on a single chromosome (`--region chr1:1-10000000`) before running on the full genome — saves hours.

5. **Always use `--numberOfProcessors`**: Most tools parallelize well — use all available cores.

6. **Anti-pattern — using RPGC without `--effectiveGenomeSize`**: Will silently produce wrong results. Always specify the correct genome size.

7. **Run QC before analysis**: Check fingerprint and correlation before investing time in heatmaps/profiles. Poor enrichment means downstream visualizations will be noise.

## Common Recipes

### Recipe: Multi-Sample Correlation Matrix

```bash
# Compare 6 samples across the genome
multiBamSummary bins --bamfiles sample{1..6}.bam \
    -o all_samples.npz --binSize 10000 -p 8 \
    --labels S1 S2 S3 S4 S5 S6

# Pearson correlation heatmap
plotCorrelation -in all_samples.npz --corMethod pearson \
    --whatToShow heatmap -o pearson_corr.png --plotNumbers

# Spearman correlation + PCA
plotCorrelation -in all_samples.npz --corMethod spearman \
    --whatToShow heatmap -o spearman_corr.png
plotPCA -in all_samples.npz -o pca.png
```

### Recipe: Gene Body Coverage Profile

```bash
# Scale-regions mode for gene body analysis
computeMatrix scale-regions -S sample.bw -R genes.bed \
    -b 1000 -a 1000 --regionBodyLength 5000 -o gene_body.gz -p 8
plotProfile -m gene_body.gz -o gene_body_profile.png \
    --plotType lines --perGroup
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `BAM index not found` | Missing `.bai` file | Run `samtools index input.bam` |
| Out of memory | Large genome, small bin size | Increase `--binSize`; process with `--region chr1` |
| Very slow processing | Single-threaded execution | Add `-p 8` (or available cores) |
| bigWig files very large | Bin size too small | Increase `--binSize 50` or larger |
| Flat ChIP fingerprint | Poor ChIP enrichment | Biological issue — consider repeating ChIP experiment |
| RNA-seq artifacts at exon boundaries | `--extendReads` used with RNA-seq | Remove `--extendReads` for RNA-seq data |
| ATAC-seq signal offset | Missing Tn5 correction | Apply `alignmentSieve --ATACshift` before analysis |
| Mismatched genome assemblies | BAM and BED use different assemblies | Verify both use same genome build (hg38 vs hg19) |

## Related Skills

- **pysam-genomic-files** — programmatic BAM/VCF manipulation for custom filtering before deepTools
- **matplotlib-scientific-plotting** — customize deepTools output figures beyond built-in options

## References

- [deepTools documentation](https://deeptools.readthedocs.io/) — official user guide and tool reference
- [deepTools Galaxy](https://deeptools.ie-freiburg.mpg.de/) — web-based interface
- Ramirez et al. (2016) "deepTools2: a next generation web server for deep-sequencing data analysis" — [Nucleic Acids Research](https://doi.org/10.1093/nar/gkw257)
