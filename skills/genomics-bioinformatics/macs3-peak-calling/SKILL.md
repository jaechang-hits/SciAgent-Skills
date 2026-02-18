---
name: "macs3-peak-calling"
description: "Calls narrow and broad peaks from ChIP-seq and ATAC-seq BAM files using a Poisson model. MACS3 callpeak identifies enriched genomic regions (transcription factor binding sites or histone marks) against an input/IgG control; outputs BED narrowPeak/broadPeak files for downstream motif analysis, annotation, and differential binding. Use narrow peaks for TF ChIP-seq and ATAC-seq; use broad peaks for H3K27me3, H3K9me3, and other broad histone marks."
license: "BSD-3-Clause"
---

# MACS3 — ChIP-seq and ATAC-seq Peak Caller

## Overview

MACS3 (Model-based Analysis of ChIP-seq) identifies regions of significant read enrichment (peaks) from ChIP-seq, ATAC-seq, CUT&RUN, and CUT&TAG experiments. It models the fragment length distribution from paired-end data or estimates it from mono-nucleosomal read shifting in single-end data, then applies a Poisson model to identify fold-enrichment over an input/IgG control. MACS3 produces BED-format narrowPeak (for transcription factors) or broadPeak (for histone marks) files with signal and q-value tracks for visualization in IGV or UCSC Genome Browser.

## When to Use

- Calling transcription factor binding peaks from ChIP-seq experiments (use `--nomodel --extsize 200` or let MACS3 estimate fragment length)
- Identifying open chromatin regions from ATAC-seq experiments (use `--nomodel --shift -100 --extsize 200 -f BAMPE`)
- Calling broad histone modification peaks (H3K27me3, H3K9me3, H3K36me3) with `--broad`
- Generating peak signal tracks (bedGraph/bigWig) for genome browser visualization with `-B --SPMR`
- Performing differential binding analysis: MACS3 peaks as input to DiffBind or DESeq2
- Use **HMMRATAC** (part of MACS3) for nucleosome-resolution ATAC-seq peak calling
- Use **SPP** or **HOMER** as alternatives; MACS3 is the ENCODE-recommended standard

## Prerequisites

- **Python packages**: `macs3` (Python ≥ 3.8)
- **Input**: Sorted BAM files (with index) from ChIP-seq or ATAC-seq alignment (e.g., using STAR or Bowtie2)
- **Optional**: Input/IgG control BAM for background normalization

```bash
# Install with pip or conda
pip install macs3
# or
conda install -c bioconda macs3

# Verify
macs3 --version
# macs3 3.0.2
```

## Quick Start

```bash
# Call peaks for TF ChIP-seq (narrow peaks, with input control)
macs3 callpeak \
    -t chip.bam \
    -c input.bam \
    -f BAM \
    -g hs \
    -n sample_tf \
    --outdir peaks/ \
    -q 0.05

# Output: peaks/sample_tf_peaks.narrowPeak
wc -l peaks/sample_tf_peaks.narrowPeak
```

## Workflow

### Step 1: Prepare Input BAM Files

MACS3 requires sorted, indexed BAM files from genome alignment.

```bash
# Sort and index ChIP and control BAMs (if not already done)
samtools sort -@ 8 chip_raw.bam -o chip.bam
samtools sort -@ 8 input_raw.bam -o input.bam
samtools index chip.bam
samtools index input.bam

# Check read counts
echo "ChIP reads: $(samtools view -c -F 4 chip.bam)"
echo "Input reads: $(samtools view -c -F 4 input.bam)"
```

### Step 2: Call Narrow Peaks (TF ChIP-seq)

Use the default mode for transcription factor binding site identification.

```bash
# TF ChIP-seq with input control
macs3 callpeak \
    -t chip.bam \
    -c input.bam \
    -f BAM \
    -g hs \
    -n tf_chip \
    --outdir peaks/ \
    -q 0.05 \
    --keep-dup auto

echo "Peaks called: $(wc -l < peaks/tf_chip_peaks.narrowPeak)"
echo "Summit file: peaks/tf_chip_summits.bed"

# Without input control (less recommended)
macs3 callpeak \
    -t chip.bam \
    -f BAM \
    -g hs \
    -n tf_noinput \
    --outdir peaks/ \
    --nolambda
```

### Step 3: Call Broad Peaks (Histone Marks)

Use `--broad` for spread histone modifications like H3K27me3 or H3K36me3.

```bash
# H3K27me3 broad histone mark
macs3 callpeak \
    -t h3k27me3.bam \
    -c input.bam \
    -f BAM \
    -g hs \
    -n h3k27me3 \
    --outdir peaks/ \
    --broad \
    --broad-cutoff 0.1 \
    -q 0.05

echo "Broad peaks: $(wc -l < peaks/h3k27me3_peaks.broadPeak)"

# H3K4me3 (sharp mark — use narrow peaks)
macs3 callpeak \
    -t h3k4me3.bam \
    -c input.bam \
    -f BAM \
    -g hs \
    -n h3k4me3 \
    --outdir peaks/ \
    -q 0.05
```

### Step 4: Call ATAC-seq Peaks

ATAC-seq requires special handling for the Tn5 insertion site.

```bash
# ATAC-seq with paired-end BAM (recommended)
macs3 callpeak \
    -t atac.bam \
    -f BAMPE \
    -g hs \
    -n atac_sample \
    --outdir peaks/ \
    --nomodel \
    --nolambda \
    -q 0.05 \
    --keep-dup all

echo "ATAC peaks: $(wc -l < peaks/atac_sample_peaks.narrowPeak)"

# Single-end ATAC-seq: shift reads to center on Tn5 cut site
macs3 callpeak \
    -t atac_se.bam \
    -f BAM \
    -g hs \
    -n atac_se \
    --outdir peaks/ \
    --nomodel \
    --shift -100 \
    --extsize 200 \
    --keep-dup all
```

### Step 5: Generate Signal Tracks for Visualization

Produce bedGraph and bigWig files for genome browser visualization.

```bash
# Generate bedGraph normalized to million reads (SPMR)
macs3 callpeak \
    -t chip.bam \
    -c input.bam \
    -f BAM \
    -g hs \
    -n chip_track \
    --outdir tracks/ \
    -B \
    --SPMR \
    --keep-dup auto

# Convert bedGraph to bigWig for IGV/UCSC
# Requires bedGraphToBigWig and chrom.sizes
sort -k1,1 -k2,2n tracks/chip_track_treat_pileup.bdg > tracks/chip_sorted.bdg
bedGraphToBigWig tracks/chip_sorted.bdg genome/hg38.chrom.sizes tracks/chip.bw

echo "BigWig track: tracks/chip.bw"
```

### Step 6: Annotate and Analyze Peaks

Parse narrowPeak output and annotate peaks to genomic features.

```python
import pandas as pd

# Load narrowPeak file
# Columns: chrom, start, end, name, score, strand, signalValue, pValue, qValue, peak
cols = ["chrom", "start", "end", "name", "score", "strand",
        "signalValue", "pValue", "qValue", "peak"]
peaks = pd.read_csv("peaks/tf_chip_peaks.narrowPeak", sep="\t",
                    header=None, names=cols)

print(f"Total peaks: {len(peaks)}")
print(f"Peaks on chr1: {(peaks['chrom'] == 'chr1').sum()}")
print(f"Median peak width: {(peaks['end'] - peaks['start']).median():.0f} bp")
print(f"Peaks with q-value < 0.01: {(peaks['qValue'] > 2).sum()}")  # -log10(q) > 2

# Filter high-confidence peaks
high_conf = peaks[peaks["qValue"] > 2].copy()  # q < 0.01
high_conf["width"] = high_conf["end"] - high_conf["start"]
print(f"\nHigh-confidence peaks: {len(high_conf)}")
high_conf.to_csv("high_confidence_peaks.bed", sep="\t", index=False, header=False,
                 columns=["chrom", "start", "end", "name", "score", "strand"])
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-t / --treatment` | required | BAM/BED/SAM | ChIP or ATAC treatment file |
| `-c / --control` | — | BAM/BED/SAM | Input/IgG control; omit `--nolambda` if absent |
| `-g / --gsize` | required | `hs`, `mm`, `ce`, `dm`, or integer | Effective genome size; `hs`=2.7e9 (human), `mm`=1.87e9 (mouse) |
| `-q / --qvalue` | `0.05` | 0–1 | FDR threshold for peak calling |
| `-p / --pvalue` | — | 0–1 | P-value cutoff (use instead of q-value for strict control) |
| `--broad` | off | flag | Call broad peaks for diffuse histone marks |
| `--broad-cutoff` | `0.1` | 0–1 | Q-value cutoff for broad region merging |
| `--nomodel` | off | flag | Skip fragment length modeling; required for ATAC-seq |
| `--extsize` | `200` | 50–1000 | Fragment extension size when `--nomodel` is set |
| `--shift` | `0` | -500–500 | Read shift in bp; use `-100` with `--extsize 200` for ATAC-seq |
| `--keep-dup` | `1` | `auto`, `all`, integer | Duplicate handling; `auto` uses Poisson model, `all` keeps all (ATAC-seq) |
| `-B / --bdg` | off | flag | Write bedGraph signal tracks |
| `--SPMR` | off | flag | Normalize bedGraph to signal per million reads |

## Common Recipes

### Recipe 1: Batch Peak Calling for Multiple Samples

```bash
#!/bin/bash
# Call peaks for multiple ChIP-seq samples with the same input
INPUT="input.bam"
GENOME="hs"
OUTDIR="peaks"
mkdir -p "$OUTDIR"

SAMPLES=(H3K4me3 H3K27ac H3K27me3 CTCF)
MODES=(narrow narrow broad narrow)

for i in "${!SAMPLES[@]}"; do
    sample="${SAMPLES[$i]}"
    mode="${MODES[$i]}"
    echo "Calling peaks: $sample ($mode)"
    
    if [ "$mode" == "broad" ]; then
        BROAD_FLAG="--broad --broad-cutoff 0.1"
    else
        BROAD_FLAG=""
    fi
    
    macs3 callpeak \
        -t "${sample}.bam" \
        -c "$INPUT" \
        -f BAM \
        -g "$GENOME" \
        -n "$sample" \
        --outdir "$OUTDIR" \
        $BROAD_FLAG \
        -q 0.05 \
        --keep-dup auto
    
    echo "$sample: $(wc -l < $OUTDIR/${sample}_peaks.*Peak) peaks"
done
```

### Recipe 2: Reproducible Peaks with IDR (Irreproducible Discovery Rate)

```bash
# Call peaks on individual replicates (lenient thresholds for IDR)
for rep in rep1 rep2; do
    macs3 callpeak \
        -t "chip_${rep}.bam" \
        -c input.bam \
        -f BAM \
        -g hs \
        -n "tf_${rep}" \
        --outdir peaks/ \
        -p 0.1 \
        --keep-dup auto
done

# Run IDR to find reproducible peaks
# pip install idr
idr --samples peaks/tf_rep1_peaks.narrowPeak peaks/tf_rep2_peaks.narrowPeak \
    --input-file-type narrowPeak \
    --output-file peaks/tf_idr_peaks.txt \
    --idr-threshold 0.05 \
    --plot

echo "IDR peaks: $(wc -l < peaks/tf_idr_peaks.txt)"
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `*_peaks.narrowPeak` | BED6+4 | Narrow peaks with signal, p-value, q-value, summit offset |
| `*_peaks.broadPeak` | BED6+3 | Broad peaks (when `--broad`): chrom, start, end, signal, p-val, q-val |
| `*_summits.bed` | BED3+2 | Peak summit positions (1 bp) with score; use for motif analysis |
| `*_treat_pileup.bdg` | bedGraph | Treatment signal track (when `-B`) |
| `*_control_lambda.bdg` | bedGraph | Control/local lambda track (when `-B`) |
| `*_model.r` | R script | Fragment size model; run `Rscript *_model.r` to plot |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Very few peaks called | Stringent q-value or low read depth | Relax to `-p 1e-3`; check sequencing depth (≥10M aligned reads recommended) |
| Too many peaks (>100k) | Threshold too loose or no input control | Add `--control input.bam`; use `-q 0.01`; filter on signalValue |
| Peak calling fails with "no reads" | BAM file is not sorted or indexed | Run `samtools sort` and `samtools index` before MACS3 |
| ATAC-seq peaks in mitochondria | High mtDNA content | Filter: `samtools view -h chip.bam | grep -v chrM | samtools view -bS > filtered.bam` |
| Fragment model fails | Too few reads or unusual read length | Add `--nomodel --extsize 200` to skip modeling |
| bedGraph output very large | High coverage data without normalization | Add `--SPMR` to normalize to signal per million reads |
| `--broad` misses narrow peaks | Signal is actually sharp | Check ChIP target: TFs and H3K4me3 need narrow mode |
| `gsize` mismatch | Using wrong genome size for assembly | Use `hs` for hg19/hg38, `mm` for mm9/mm10; or provide exact integer |

## References

- [MACS3 GitHub: macs3-project/MACS](https://github.com/macs3-project/MACS) — source code, documentation, and changelog
- Zhang Y et al. (2008) "Model-based Analysis of ChIP-Seq (MACS)" — *Genome Biology* 9:R137. [DOI:10.1186/gb-2008-9-9-r137](https://doi.org/10.1186/gb-2008-9-9-r137)
- [ENCODE ATAC-seq pipeline](https://www.encodeproject.org/atac-seq/) — ENCODE standardized ATAC-seq workflow using MACS3
- [IDR framework](https://github.com/nboley/idr) — irreproducible discovery rate for reproducible peak calls
