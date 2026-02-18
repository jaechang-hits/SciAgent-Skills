---
name: "samtools-bam-processing"
description: "Command-line toolkit for SAM/BAM/CRAM alignment file manipulation. Sort, index, convert, filter, and QC sequencing alignments. Core commands: view (filter/convert), sort, index, flagstat, stats, depth, markdup, merge. Required for all NGS pipelines between alignment and variant calling or peak calling. Use pysam for Python-native BAM access; use deeptools for normalized coverage tracks."
license: "MIT"
---

# samtools — SAM/BAM/CRAM Alignment Toolkit

## Overview

samtools is the standard command-line toolkit for processing sequence alignment files in SAM, BAM, and CRAM formats. It handles the complete alignment file lifecycle: format conversion, coordinate sorting, index creation, quality control statistics, read filtering, duplicate marking, and multi-file merging. samtools is a near-universal component of NGS pipelines between alignment (STAR, BWA) and downstream analysis (variant calling, peak calling, coverage).

## When to Use

- Sorting BAM files by coordinate after alignment (required before indexing)
- Indexing sorted BAM files for random access and region queries
- Converting between SAM, BAM, and CRAM formats to save storage
- Generating alignment QC metrics: mapping rates, insert sizes, per-chromosome stats
- Filtering reads by mapping quality, FLAG bits, or genomic regions
- Marking or removing PCR duplicates before variant calling
- Merging multiple BAM files from different lanes or samples
- Calculating per-base depth or coverage breadth for target regions
- Use `pysam` instead for Python-native BAM manipulation in custom scripts
- Use `deeptools bamCoverage` instead when you need normalized bigWig coverage tracks
- Use `mosdepth` instead for whole-genome per-base depth (faster, parallelized)

## Prerequisites

- **Installation**: samtools 1.17+ recommended
- **Input requirements**: SAM/BAM/CRAM files; CRAM requires FASTA reference
- **Companion tools**: `samtools faidx` for FASTA indexing; `samtools sort` before `samtools index`

```bash
# Bioconda (recommended)
conda install -c bioconda samtools

# Homebrew (macOS)
brew install samtools

# Verify
samtools --version | head -1
```

## Quick Start

```bash
# Typical post-alignment workflow: sort → index → QC
samtools sort -@ 8 -o sorted.bam input.bam
samtools index sorted.bam
samtools flagstat sorted.bam
```

## Core API

### Module 1: BAM/SAM I/O and Format Conversion

Convert between SAM/BAM/CRAM formats and extract subsets.

```bash
# SAM → BAM (saves ~75% disk space)
samtools view -b -h input.sam -o output.bam

# BAM → CRAM (saves additional 40-50%)
samtools view -C -T reference.fa input.bam -o output.cram

# Filter: mapping quality ≥20, exclude unmapped (-F 4)
samtools view -q 20 -F 4 input.bam -o filtered.bam

# Extract specific region (requires index)
samtools view -h sorted.bam "chr1:1000000-2000000" -o region.bam

# Count reads matching filter
samtools view -c -F 4 input.bam
# Output: 45231923 (number of mapped reads)
```

```bash
# Extract reads as FASTQ (for realignment or de novo assembly)
samtools fastq -@ 4 -1 R1.fastq.gz -2 R2.fastq.gz -0 unpaired.fastq.gz input.bam

# Extract reads as FASTA
samtools fasta input.bam > reads.fasta

# Filter by read group
samtools view -r SAMPLE_001 multi_rg.bam -o sample001.bam
```

### Module 2: Sorting and Indexing

Organize BAM files for efficient random access.

```bash
# Sort by coordinate (required before indexing)
samtools sort -@ 8 -m 2G input.bam -o sorted.bam

# Sort by read name (required for fixmate/markdup)
samtools sort -n -@ 8 input.bam -o namesorted.bam

# Index sorted BAM (creates sorted.bam.bai)
samtools index sorted.bam

# For chromosomes > 512 Mbp: use CSI index instead
samtools index -c sorted.bam

# Group reads by name (fast, for fixmate — no full sort needed)
samtools collate -o collated.bam input.bam
```

### Module 3: Quality Control and Statistics

Generate alignment QC metrics and coverage reports.

```bash
# Quick summary: total, mapped, paired, properly paired
samtools flagstat sorted.bam
# Example output:
# 50000000 + 0 in total (QC-passed reads + QC-failed reads)
# 48523111 + 0 mapped (97.05% : N/A)
# 50000000 + 0 paired in sequencing
# 48490234 + 0 properly paired (96.98% : N/A)

# Per-chromosome mapped/unmapped read counts
samtools idxstats sorted.bam
# chr1  248956422  12345678  0
# chr2  242193529  11234567  0

# Comprehensive stats (insert sizes, GC content, base quality)
samtools stats -r reference.fa sorted.bam > full_stats.txt
grep "^SN" full_stats.txt | cut -f2,3  # Summary Numbers only

# Coverage report (min/max/mean per region/chromosome)
samtools coverage sorted.bam
```

```bash
# Per-base read depth for specific regions
samtools depth -b target_regions.bed sorted.bam > depth.txt
# Output: chr  pos  depth (e.g., chr1  1000  45)

# Statistics split by read group
samtools stats -S RG sorted.bam > per_rg_stats.txt
```

### Module 4: Read Filtering and FLAG Operations

Filter reads using SAM FLAG bits for specific subsets.

```bash
# FLAG reference — common masks:
# 1    = paired         4  = unmapped
# 2    = proper pair    8  = mate unmapped
# 16   = reverse strand 64 = R1 (first in pair)
# 128  = R2             256= secondary alignment
# 1024 = PCR duplicate  2048= supplementary

# Extract properly paired, mapped reads (FLAG 2 set, 4 unset)
samtools view -f 2 -F 4 sorted.bam -o proper_pairs.bam

# Extract R1 reads only
samtools view -f 64 sorted.bam -o R1.bam

# Remove secondary and supplementary alignments
samtools view -F 2304 sorted.bam -o primary.bam

# Extract reads from BED file regions
samtools view -L regions.bed -b sorted.bam -o regions.bam
```

### Module 5: Duplicate Handling

Mark or remove PCR duplicates before variant calling.

```bash
# Full duplicate marking workflow (collate → fixmate → sort → markdup)
samtools collate -@ 8 -o collated.bam input.bam
samtools fixmate -m -@ 8 collated.bam fixmated.bam
samtools sort -@ 8 -o sorted.bam fixmated.bam
samtools markdup -@ 8 sorted.bam marked.bam
samtools index marked.bam

# Check duplication rate
samtools flagstat marked.bam | grep "duplicates"
# Output: 2345678 + 0 duplicates (4.83%)
```

```bash
# NovaSeq optical duplicate detection (2500 pixel distance)
samtools markdup -d 2500 sorted.bam marked_novaseq.bam

# Remove duplicates instead of marking
samtools markdup -r sorted.bam deduped.bam

# Get duplication stats without writing output
samtools markdup -s sorted.bam /dev/null
```

### Module 6: Multi-file Operations and Region Analysis

Merge BAM files and perform region-level analysis.

```bash
# Merge multiple BAM files (all must be sorted)
samtools merge -@ 8 merged.bam lane1.bam lane2.bam lane3.bam

# Merge files listed in a text file (one per line)
samtools merge -b bam_list.txt -@ 8 merged.bam

# Merge with read group tags from filenames
samtools merge -r merged.bam sample1.bam sample2.bam

# Extract specific chromosome region from merged output
samtools view -h merged.bam chr1 -b -o chr1.bam
```

## Key Concepts

### SAM FLAG Bits

FLAGS encode read properties as a sum of bit values. Common filtering patterns:

| Common Filter | `-f` (require) | `-F` (exclude) | Selects |
|---------------|----------------|----------------|---------|
| Mapped reads | — | 4 | All aligned reads |
| Proper pairs | 2 | — | Properly paired, both mapped |
| Unique primary | — | 2308 | No secondary/supplementary/duplicate |
| R1 only | 64 | — | First-in-pair reads |
| Unmapped | 4 | — | Failed to align |

### CRAM vs BAM vs SAM

| Format | Size | Speed | Requires |
|--------|------|-------|---------|
| SAM | ~10× BAM | Slow I/O | Nothing |
| BAM | 1× | Fast | `.bai` index for random access |
| CRAM | ~0.6× BAM | Slightly slower | Reference FASTA + index |

Use CRAM for long-term storage; BAM for active analysis.

## Common Workflows

### Workflow 1: Post-Alignment QC and Preparation

**Goal**: Convert aligner output to analysis-ready BAM with QC metrics.

```bash
#!/bin/bash
SAMPLE="sample_001"
REF="reference.fa"
THREADS=8

# 1. Sort and index (aligner often outputs unsorted SAM/BAM)
samtools sort -@ $THREADS -o ${SAMPLE}.sorted.bam ${SAMPLE}.bam
samtools index ${SAMPLE}.sorted.bam

# 2. QC metrics
samtools flagstat ${SAMPLE}.sorted.bam > ${SAMPLE}.flagstat.txt
samtools stats -r $REF ${SAMPLE}.sorted.bam > ${SAMPLE}.stats.txt
samtools coverage ${SAMPLE}.sorted.bam > ${SAMPLE}.coverage.txt

# 3. Per-chromosome stats
samtools idxstats ${SAMPLE}.sorted.bam > ${SAMPLE}.idxstats.txt

echo "QC complete: $(grep 'mapped (' ${SAMPLE}.flagstat.txt | head -1)"
```

### Workflow 2: Full Duplicate-Marking Pipeline

**Goal**: Prepare BAM for GATK or other variant callers requiring deduplicated input.

```bash
#!/bin/bash
INPUT="aligned.bam"
FINAL="deduped.bam"
THREADS=8

# Collate → fixmate → sort → markdup
samtools collate -@ $THREADS -o collated.bam $INPUT
samtools fixmate -m -@ $THREADS collated.bam fixmated.bam
samtools sort -@ $THREADS -o sorted.bam fixmated.bam
samtools markdup -@ $THREADS -s sorted.bam $FINAL

# Clean up intermediates
rm collated.bam fixmated.bam sorted.bam

# Index and verify
samtools index $FINAL
samtools flagstat $FINAL | grep "duplic"
# Expected: 3-15% duplicates (WGS); 10-30% for amplicon
```

## Key Parameters

| Parameter | Command | Default | Range/Options | Effect |
|-----------|---------|---------|---------------|--------|
| `-@` | Most | 0 | 1–N cores | Additional compression/I/O threads |
| `-m` | sort | 768M | e.g., 2G, 4G | Memory per thread for sorting |
| `-q` | view | 0 | 0–60 | Minimum mapping quality filter |
| `-f` | view | 0 | FLAG bits | Include reads with ALL bits set |
| `-F` | view | 0 | FLAG bits | Exclude reads with ANY bit set |
| `-b` | view | — | flag | Output BAM format |
| `-C` | view | — | flag | Output CRAM (requires `-T`) |
| `-T` | view | — | FASTA path | Reference for CRAM output |
| `-d` | markdup | 0 | 0–2500 | Optical duplicate pixel distance |
| `-r` | markdup | — | flag | Remove duplicates (vs just mark) |
| `-n` | sort | — | flag | Sort by read name instead of position |
| `-c` | index | — | flag | Create CSI index (needed for chr > 512 Mb) |

## Best Practices

1. **Always sort before indexing**: `samtools index` requires coordinate-sorted input. Attempting to index an unsorted BAM will fail or produce incorrect results.

2. **Use `-@` for all production runs**: Most samtools commands are I/O-bound. Adding `-@ 8` provides near-linear speedup for compression/decompression with minimal overhead.

3. **Run flagstat before any analysis**: `samtools flagstat` runs in seconds and catches alignment failures (low mapping rate, unexpected paired-end rates) before wasting time on downstream steps.

4. **Use the collate → fixmate → sort → markdup pipeline**: Running `samtools markdup` directly on coordinate-sorted BAM without fixmate produces incorrect duplicate detection. The mate information added by `fixmate -m` is essential.

5. **Prefer CRAM for archiving**: CRAM reduces storage 40-50% vs BAM with no loss. Always store the reference FASTA alongside CRAM files.

6. **Use `-L bed_file` for targeted analyses**: Restricting `samtools view` to BED-defined target regions (WES capture, amplicons) dramatically reduces I/O for downstream steps.

## Common Recipes

### Recipe: Batch Flagstat for Multiple Samples

```bash
# Process all BAM files in directory
for bam in *.sorted.bam; do
    echo "=== $bam ==="
    samtools flagstat $bam | grep -E "mapped|properly paired|duplicates"
done
```

### Recipe: Extract Unmapped Reads for De Novo Assembly

```bash
# Pull both unmapped reads (useful for pathogen detection)
samtools view -f 4 -b input.bam -o unmapped.bam
samtools fastq -@ 4 -1 unmapped_R1.fastq -2 unmapped_R2.fastq unmapped.bam
echo "Unmapped pairs ready for de novo assembly"
```

### Recipe: Downsample BAM to Target Coverage

```bash
# Estimate current depth, then subsample to ~30×
TOTAL=$(samtools flagstat input.bam | grep "mapped (" | head -1 | awk '{print $1}')
GENOME_SIZE=3100000000  # hg38
READ_LEN=150
CURRENT_COV=$(echo "scale=1; $TOTAL * $READ_LEN / $GENOME_SIZE" | bc)
TARGET_FRAC=$(echo "scale=3; 30 / $CURRENT_COV" | bc)
echo "Current: ${CURRENT_COV}×; subsample fraction: $TARGET_FRAC"
samtools view -b -s $TARGET_FRAC input.bam -o downsampled.bam
samtools index downsampled.bam
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `[bam_index_build2] fail to index` | BAM not sorted by coordinate | Sort first: `samtools sort -o sorted.bam input.bam` |
| `BAI index too large for chromosome` | Chromosome > 512 Mbp | Use CSI index: `samtools index -c input.bam` |
| `CRAM: reference not found` | Missing or wrong reference FASTA | Set `REF_PATH` env var or use `-T ref.fa` |
| Duplicate marking incorrect | `fixmate` step skipped | Run full pipeline: collate → fixmate → sort → markdup |
| `flagstat` shows 0% properly paired | Paired-end BAM missing mate info | Run `samtools fixmate` to populate mate coordinates |
| Very slow sorting | Low memory per thread | Increase `-m 4G`; reduce `-@` if memory-limited |
| Region query returns nothing | BAM not indexed or wrong coords | Run `samtools index`; use 1-based coords: `chr1:1000-2000` |
| `[E::hts_open_format] fail to open` | File path wrong or BAM corrupt | Verify path; test with `samtools quickcheck file.bam` |

## Related Skills

- **deeptools-ngs-analysis** — normalized bigWig coverage tracks and ChIP-seq visualization downstream of samtools
- **pysam-genomic-files** — Python API for BAM manipulation in custom scripts
- **bedtools-genomic-intervals** — genomic interval operations on BAM/BED files produced by samtools

## References

- [samtools documentation](https://www.htslib.org/doc/samtools.html) — official man pages and command reference
- [GitHub: samtools/samtools](https://github.com/samtools/samtools) — source, releases, issue tracker
- Danecek et al. (2021) "Twelve years of SAMtools and BCFtools" — [GigaScience 10(2)](https://doi.org/10.1093/gigascience/giab008)
- [SAM format specification](https://samtools.github.io/hts-specs/SAMv1.pdf) — FLAG bits, CIGAR strings, optional tags
