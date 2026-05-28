---
name: "bedtools-genomic-intervals"
description: "Genomic interval ops on BED/BAM/GFF/VCF. Find overlaps, merge intervals, compute coverage, extract FASTA, find nearest features. Core for ChIP-seq peak annotation, region filtering, genome arithmetic. Use tabix for indexed single-region queries; use deeptools for normalized bigWig coverage."
license: "GPL-2.0"
---

# bedtools — Genomic Interval Analysis Toolkit

## Overview

bedtools is the standard toolkit for operating on genomic intervals in BED, BAM, GFF, and VCF formats. It solves the core problem of genome arithmetic: finding overlaps between feature sets, computing coverage, extracting sequences, merging adjacent regions, and annotating features with nearest neighbors. bedtools operates on sorted coordinate lists and runs at C speed, making it practical for whole-genome analyses.

## When to Use

- Intersecting ChIP-seq peaks with gene annotations to find promoter-overlapping peaks
- Merging overlapping ATAC-seq peaks or called regions across replicates
- Computing read coverage depth over target capture regions
- Extracting FASTA sequences for motif discovery or primer design
- Finding the nearest gene to each regulatory element or variant
- Subtracting blacklist or repeat regions from peak calls
- Expanding genomic intervals by fixed distance (promoter regions)
- Use `tabix` instead for fast indexed queries of a single genomic region
- For normalized coverage bigWig tracks, use `deeptools bamCoverage` instead
- Use `mosdepth` instead for whole-genome per-base depth (10× faster)

## Prerequisites

- **Python packages**: None required (command-line only)
- **Input requirements**: BED/BAM/GFF/VCF files; FASTA reference for `getfasta`; genome file (chromosome sizes) for `slop`/`flank`/`genomecov`
- **Sorting**: Most operations require coordinate-sorted input

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v bedtools` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run bedtools` rather than bare `bedtools`.

```bash
# Bioconda (recommended)
conda install -c bioconda bedtools

# Homebrew (macOS)
brew install bedtools

# Verify
bedtools --version
# bedtools v2.31.0

# Create genome file from FASTA index
samtools faidx reference.fa
cut -f1,2 reference.fa.fai > genome.txt  # chr → size table
```

## Quick Start

```bash
# Find peaks overlapping genes, then merge overlapping peaks
bedtools intersect -a peaks.bed -b genes.bed -wa -wb > peaks_with_genes.bed
bedtools merge -i peaks.bed > merged_peaks.bed
bedtools coverage -a genes.bed -b reads.bam > gene_coverage.bed
```

## Core API

### Module 1: Interval Intersection and Overlap Analysis

Find regions that overlap between two feature sets.

```bash
# Basic intersection: output overlapping regions
bedtools intersect -a peaks.bed -b genes.bed

# Report original A and B features for each overlap
bedtools intersect -a peaks.bed -b genes.bed -wa -wb

# Count B overlaps per A feature (adds column)
bedtools intersect -a peaks.bed -b genes.bed -c
# Output: chr1  1000  2000  peak1  gene_count

# Peaks with ANY overlap (report each peak once)
bedtools intersect -a peaks.bed -b genes.bed -u

# Peaks with NO overlap in B (invert filter)
bedtools intersect -a peaks.bed -b blacklist.bed -v
```

```bash
# Require reciprocal 50% overlap both ways
bedtools intersect -a exp1.bed -b exp2.bed -f 0.5 -F 0.5 -r

# Same-strand intersections only
bedtools intersect -a peaks.bed -b genes.bed -s

# Multiple database files with overlap counts per file
bedtools intersect -a query.bed -b enhancers.bed promoters.bed \
    -names enh prom -C

# Memory-efficient mode for pre-sorted large files
bedtools intersect -a sorted_peaks.bed -b sorted_genes.bed -sorted
```

### Module 2: Interval Merging and Arithmetic

Combine overlapping intervals and perform set operations.

```bash
# Merge overlapping and adjacent intervals
sort -k1,1 -k2,2n peaks.bed | bedtools merge -i stdin

# Merge intervals within 500 bp of each other
bedtools merge -i peaks.bed -d 500

# Merge and count original features
bedtools merge -i peaks.bed -c 1 -o count
# Output: chr1  1000  5000  3 (3 original peaks merged)

# Merge and collapse feature names
bedtools merge -i peaks.bed -c 4 -o collapse -delim ";"
# Output: chr1  1000  5000  peak1;peak2;peak3
```

```bash
# Subtract B from A (remove covered bases)
bedtools subtract -a peaks.bed -b blacklist.bed

# Remove entire A feature if ANY B overlap
bedtools subtract -a peaks.bed -b exclusion.bed -A

# Find genomic gaps (complement of covered regions)
bedtools complement -i merged.bed -g genome.txt
```

### Module 3: Coverage Analysis

Calculate depth and breadth of read coverage over features.

```bash
# Coverage stats per feature (count, bases covered, % covered)
bedtools coverage -a target_genes.bed -b aligned.bam
# Output: chr  start  end  gene  n_overlapping_reads  bases_covered  feature_len  fraction_covered

# Per-base depth within each feature
bedtools coverage -a targets.bed -b aligned.bam -d
# Output: chr  start  end  name  position  depth

# Coverage histogram per feature
bedtools coverage -a features.bed -b aligned.bam -hist
```

```bash
# Genome-wide BEDGRAPH (coverage per bin)
bedtools genomecov -ibam aligned.bam -bg -o coverage.bedgraph

# Include zero-coverage regions (for whole-genome coverage)
bedtools genomecov -ibam aligned.bam -bga > full_coverage.bedgraph

# Per-base depth for whole genome
bedtools genomecov -ibam aligned.bam -d > depth.txt

# Scaled BEDGRAPH (RPM normalization: total=50M reads → scale=1/50)
bedtools genomecov -ibam aligned.bam -bg -scale 0.00000002 > rpm.bedgraph

# Strand-specific coverage tracks
bedtools genomecov -ibam rnaseq.bam -bg -strand + > forward.bedgraph
bedtools genomecov -ibam rnaseq.bam -bg -strand - > reverse.bedgraph
```

### Module 4: Sequence Extraction and Nearest Feature

Extract genomic sequences and annotate features with neighbors.

```bash
# Extract FASTA sequences for each BED region
bedtools getfasta -fi genome.fa -bed regions.bed -fo sequences.fasta

# Strand-aware extraction (reverse complement - strand)
bedtools getfasta -fi genome.fa -bed regions.bed -s -fo stranded.fasta

# Custom FASTA headers (name + coords)
bedtools getfasta -fi genome.fa -bed peaks.bed -name -fo named.fasta

# Extract and concatenate exons (BED12 spliced transcripts)
bedtools getfasta -fi genome.fa -bed transcripts.bed12 -split -fo exons.fasta
```

```bash
# Find nearest gene to each peak (with distance)
bedtools closest -a peaks.bed -b genes.bed -d
# Output: peak fields... | gene fields... | distance_bp

# Nearest feature on same strand only
bedtools closest -a peaks.bed -b genes.bed -s -d

# Ignore overlapping features (find nearest non-overlapping)
bedtools closest -a peaks.bed -b genes.bed -io -d

# Multiple annotation databases
bedtools closest -a query.bed -b genes.bed enhancers.bed \
    -names genes enhancers -d
```

### Module 5: Interval Manipulation

Expand, contract, and shift genomic intervals.

```bash
# Expand regions by 500 bp on each side
bedtools slop -i peaks.bed -g genome.txt -b 500

# Asymmetric: 2000 bp upstream, 500 bp downstream of TSS
bedtools slop -i tss.bed -g genome.txt -l 2000 -r 500

# Strand-aware expansion (upstream = 5' side)
bedtools slop -i genes.bed -g genome.txt -l 1000 -r 200 -s

# Create flanking regions (not overlapping the feature)
bedtools flank -i genes.bed -g genome.txt -b 1000
bedtools flank -i genes.bed -g genome.txt -l 2000 -r 0 -s  # upstream only
```

## Key Concepts

### Coordinate Systems

BED files use **0-based half-open** intervals: start is 0-indexed (like Python), end is exclusive. A region chr1:1000-2000 in BED covers bases 1000–1999 (1000 bases).

```
chr1  1000  2000  peak1   ← covers positions 1000,1001,...,1999
# BED:  0-based start, exclusive end
# VCF:  1-based position (POS)
# GFF:  1-based start and end (both inclusive)
```

bedtools converts internally — input format is auto-detected. Problems arise when mixing tools with different conventions.

### Sorting Requirements

Most bedtools operations require **coordinate-sorted** input. Pre-sort with:

```bash
sort -k1,1 -k2,2n input.bed > sorted.bed
# For large files, use -S 4G for 4 GB sort buffer
sort -k1,1 -k2,2n -S 4G --parallel=8 input.bed > sorted.bed
```

The `-sorted` flag in `bedtools intersect` uses a sweep algorithm that requires sorted input but uses O(1) memory instead of O(N).

## Common Workflows

### Workflow 1: ChIP-seq Peak Annotation

**Goal**: Annotate peaks with overlapping genes, distances to TSS, and filter blacklisted regions.

```bash
#!/bin/bash
PEAKS="peaks.bed"
GENES="refseq_genes.bed"
TSS="refseq_tss.bed"       # BED with TSS positions
BLACKLIST="encode_blacklist_hg38.bed"
GENOME="hg38.genome"

# 1. Remove blacklisted regions
bedtools subtract -a $PEAKS -b $BLACKLIST -A > peaks_clean.bed
echo "After blacklist filter: $(wc -l < peaks_clean.bed) peaks"

# 2. Annotate with overlapping gene (allow 2 kb from gene body)
bedtools slop -i $GENES -g $GENOME -b 2000 > genes_padded.bed
bedtools intersect -a peaks_clean.bed -b genes_padded.bed -wa -wb \
    > peaks_gene_overlap.bed

# 3. For non-overlapping peaks: find nearest gene
bedtools intersect -a peaks_clean.bed -b genes_padded.bed -v > peaks_distal.bed
bedtools closest -a peaks_distal.bed -b $TSS -d > peaks_distal_nearest.bed

echo "Promoter peaks: $(wc -l < peaks_gene_overlap.bed)"
echo "Distal peaks: $(wc -l < peaks_distal.bed)"
```

### Workflow 2: Coverage Analysis for WES Target Regions

**Goal**: Calculate on-target read depth and coverage breadth for exome sequencing QC.

```bash
#!/bin/bash
BAM="sample.deduped.bam"
TARGETS="capture_targets.bed"

# Per-target coverage statistics
bedtools coverage -a $TARGETS -b $BAM > per_target_coverage.bed

# Summary: total targets, mean depth, % at ≥20×
awk 'BEGIN{n=0; depth=0; covered=0}
     {n++; depth+=$7; if($8>=20) covered++}
     END{printf "Targets: %d\nMean depth: %.1f×\n%% at 20×: %.1f%%\n",
         n, depth/n, covered/n*100}' per_target_coverage.bed

# Per-base depth for IGV visualization
bedtools coverage -a $TARGETS -b $BAM -d > per_base_depth.txt
echo "Per-base depth written to per_base_depth.txt"
```

## Key Parameters

| Parameter | Command | Default | Range/Options | Effect |
|-----------|---------|---------|---------------|--------|
| `-f` | intersect, coverage | 1e-9 | 0.0–1.0 | Min fraction of A that must overlap |
| `-F` | intersect, coverage | 1e-9 | 0.0–1.0 | Min fraction of B that must overlap |
| `-r` | intersect | — | flag | Require reciprocal overlap (`-f` AND `-F`) |
| `-s` | Most | — | flag | Strand-aware (same strand only) |
| `-v` | intersect | — | flag | Report features with NO overlap (invert) |
| `-c` | intersect | — | flag | Append overlap count per A feature |
| `-d` | merge | 0 | integer | Max gap to merge (bp) |
| `-bg` | genomecov | — | flag | BEDGRAPH output format |
| `-scale` | genomecov | 1.0 | float | Multiply coverage by constant (for RPM) |
| `-sorted` | intersect, closest | — | flag | Use sweep algorithm (sorted input required) |
| `-b` | slop | — | integer | Expand interval by N bp on both sides |
| `-D` | closest | — | ref/a/b | Report signed distance (upstream negative) |

## Best Practices

1. **Always sort before bedtools**: Most bedtools commands fail silently on unsorted input. Sort with `sort -k1,1 -k2,2n input.bed` before any bedtools operation.

2. **Use `-sorted` for large files**: For pre-sorted files, `-sorted` reduces memory from O(N) to O(1). Required when intersecting multi-gigabyte BED files.

3. **Check chromosome naming consistency**: The single most common failure — some tools use `chr1`, others use `1`. Verify with `cut -f1 file.bed | sort -u` before running intersections.

4. **Apply blacklist early**: Run `bedtools subtract -b blacklist.bed -A` before any peak analysis. ENCODE blacklists remove artifactual signal in repetitive/high-copy regions.

5. **Use `-f 0.5 -r` for peak reproducibility**: When intersecting peaks across replicates, require 50% reciprocal overlap to avoid spurious short overlaps at interval boundaries.

6. **Validate BED format**: Malformed BED (wrong column count, text in numeric columns) causes silent failures. Test with `bedtools merge -i file.bed 2>&1 | head -5`.

## Common Recipes

### Recipe: Count Feature Overlaps Across Annotation Categories

```bash
# Report how many peaks overlap each category (genes, promoters, enhancers)
for category in genes.bed promoters.bed enhancers.bed repeats.bed; do
    label=$(basename $category .bed)
    count=$(bedtools intersect -a peaks.bed -b $category -u | wc -l)
    total=$(wc -l < peaks.bed)
    echo "$label: $count/$total ($(echo "scale=1; $count*100/$total" | bc)%)"
done
```

### Recipe: Create Promoter Regions from Gene Annotations

```bash
# Extract 2kb upstream of TSS for ChIP annotation
# For genes on + strand: TSS = start; on - strand: TSS = end
awk 'BEGIN{OFS="\t"} $6=="+" {print $1,$2,$2+1,$4,$5,$6}
                     $6=="-" {print $1,$3-1,$3,$4,$5,$6}' genes.bed > tss.bed

bedtools slop -i tss.bed -g genome.txt -l 2000 -r 500 -s > promoters.bed
echo "Created $(wc -l < promoters.bed) promoter regions"
```

### Recipe: Calculate Intersection Statistics

```bash
# Jaccard similarity between two peak sets (0=no overlap, 1=identical)
bedtools sort -i set1.bed > s1.bed
bedtools sort -i set2.bed > s2.bed
bedtools jaccard -a s1.bed -b s2.bed
# Output: intersection  union  jaccard  n_intersections
#         423456        2345678  0.1804  892
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty intersect output | Chromosome name mismatch (chr1 vs 1) | Check: `cut -f1 a.bed \| sort -u` vs `cut -f1 b.bed \| sort -u` |
| Memory error on large files | Not using `-sorted` flag | Pre-sort inputs and add `-sorted` to intersect/closest |
| `getfasta: sequence not found` | FASTA headers differ from BED chr names | Index FASTA: `samtools faidx genome.fa`; match names exactly |
| Zero coverage everywhere | BAM not indexed or BED/BAM chr mismatch | Run `samtools index file.bam`; verify chr naming |
| Merge doesn't merge expected features | Input not sorted by coordinate | Sort: `sort -k1,1 -k2,2n file.bed \| bedtools merge -i stdin` |
| `getfasta` produces wrong-strand sequence | Using `-s` without strand column in BED | Ensure BED col 6 has `+`/`-`; add strand: `awk '{$6="+"; print}' OFS="\t"` |
| Off-by-one in coordinates | Mixing 0-based BED and 1-based VCF/GFF | Convert GFF to BED: subtract 1 from start |
| Slow on large genomes | Processing unsorted files | Sort both files; use `-sorted`; pipe through sort without writing temp files |

## Related Skills

- **samtools-bam-processing** — BAM sorting, filtering, and QC before passing to bedtools
- **deeptools-ngs-analysis** — normalized coverage bigWig tracks and heatmaps from the BAM files bedtools processes
- **pysam-genomic-files** — Python-native BAM/BED manipulation for custom logic beyond bedtools

## References

- [bedtools documentation](https://bedtools.readthedocs.io/) — command reference and examples
- [GitHub: arq5x/bedtools2](https://github.com/arq5x/bedtools2) — source, releases, issue tracker
- Quinlan & Hall (2010) "BEDTools: a flexible suite of utilities for comparing genomic features" — [Bioinformatics 26(6)](https://doi.org/10.1093/bioinformatics/btq033)
- [ENCODE blacklist regions](https://github.com/Boyle-Lab/Blacklist) — curated problematic genomic regions
