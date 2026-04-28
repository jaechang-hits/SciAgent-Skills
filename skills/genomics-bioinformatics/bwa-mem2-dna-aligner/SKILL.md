---
name: "bwa-mem2-dna-aligner"
description: "Fast short-read DNA aligner for WGS/WES/ChIP-seq. 2× faster BWA-MEM successor; outputs SAM/BAM with read group headers for GATK. Primary plus supplementary records for chimeric reads. Use STAR for RNA-seq splice-aware alignment; Bowtie2 is a comparable alternative."
license: "MIT"
---

# BWA-MEM2 — DNA Short-Read Aligner

## Overview

BWA-MEM2 aligns short DNA reads (Illumina, 50–250 bp) to a reference genome using the BWT-FM index. It is the standard aligner for whole-genome sequencing (WGS), whole-exome sequencing (WES), ChIP-seq, and ATAC-seq DNA alignment. BWA-MEM2 is 2× faster than the original BWA-MEM while producing identical results. It outputs SAM format with proper read group (`@RG`) headers required by GATK HaplotypeCaller and Picard tools. For paired-end reads, it marks proper pairs and resolves chimeric/split reads into supplementary alignments.

## When to Use

- Aligning WGS or WES Illumina reads to a reference genome for variant calling (SNP, indel, SV)
- ChIP-seq or ATAC-seq DNA alignment to produce BAM files for peak calling with MACS3
- Producing GATK-compatible BAM files with `@RG` read group tags
- Aligning reads ≥ 50 bp; for shorter reads (< 50 bp), BWA-backtrack may be more appropriate
- Re-aligning legacy FASTQ files to an updated reference genome assembly
- Use **STAR** instead for RNA-seq reads that span splice junctions
- Use **Bowtie2** as an alternative for local alignment or when index size must be minimized

## Prerequisites

- **Software**: bwa-mem2 (conda or pre-compiled binary), samtools
- **Reference**: genome FASTA (e.g., GRCh38, hg19, mm10)
- **RAM**: ~28 GB for human genome index; 6–8 GB for mouse

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v bwa-mem2` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run bwa-mem2` rather than bare `bwa-mem2`.

```bash
# Install with conda (recommended)
conda install -c bioconda bwa-mem2 samtools

# Or download pre-compiled binary
wget https://github.com/bwa-mem2/bwa-mem2/releases/download/v2.2.1/bwa-mem2-2.2.1_x64-linux.tar.bz2
tar -jxf bwa-mem2-2.2.1_x64-linux.tar.bz2
export PATH="$PWD/bwa-mem2-2.2.1_x64-linux:$PATH"

# Verify
bwa-mem2 version
# 2.2.1
```

## Quick Start

```bash
# 1. Build genome index (~30 min, run once)
bwa-mem2 index GRCh38.fa

# 2. Align paired-end reads and sort
bwa-mem2 mem -t 16 -R "@RG\tID:sample1\tSM:sample1\tPL:ILLUMINA" \
    GRCh38.fa sample1_R1.fastq.gz sample1_R2.fastq.gz \
    | samtools sort -@ 8 -o sample1.sorted.bam

# 3. Index the BAM
samtools index sample1.sorted.bam
echo "Aligned reads: $(samtools view -c -F 4 sample1.sorted.bam)"
```

## Workflow

### Step 1: Download Reference Genome

Obtain the reference genome FASTA file matching the target assembly.

```bash
# Download GRCh38 primary assembly (human)
wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.15_GRCh38/seqs_for_alignment_pipelines.ucsc_ids/GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.gz
gunzip GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.gz
mv GCA_000001405.15_GRCh38_no_alt_analysis_set.fna GRCh38.fa

# Or use ENSEMBL/GENCODE
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_47/GRCh38.primary_assembly.genome.fa.gz
gunzip GRCh38.primary_assembly.genome.fa.gz

echo "Reference size: $(du -sh GRCh38.fa)"
```

### Step 2: Build BWA-MEM2 Index

Index the reference genome — required once per genome, takes ~25-35 min for human.

```bash
# Build index (~28 GB RAM required for human genome)
bwa-mem2 index GRCh38.fa

# This creates: GRCh38.fa.0123, GRCh38.fa.amb, GRCh38.fa.ann,
#               GRCh38.fa.bwt.2bit.64, GRCh38.fa.pac
echo "Index files: $(ls GRCh38.fa.* | wc -l) created"
ls -lh GRCh38.fa.*
```

### Step 3: Align Paired-End Reads

Align FASTQ reads with a read group header required for GATK compatibility.

```bash
# Align with read group (required for GATK)
# @RG fields: ID (run ID), SM (sample name), PL (platform), LB (library), PU (flowcell)
bwa-mem2 mem \
    -t 16 \
    -R "@RG\tID:sample1_run1\tSM:sample1\tPL:ILLUMINA\tLB:lib1\tPU:flowcell1" \
    GRCh38.fa \
    sample1_R1.fastq.gz \
    sample1_R2.fastq.gz \
    | samtools sort -@ 8 -m 2G -o sample1.sorted.bam

samtools index sample1.sorted.bam
echo "Alignment complete."
echo "Total reads:   $(samtools view -c sample1.sorted.bam)"
echo "Mapped reads:  $(samtools view -c -F 4 sample1.sorted.bam)"
```

### Step 4: Mark PCR Duplicates

Remove or mark optical and PCR duplicates before variant calling.

```bash
# Option A: samtools markdup (fast)
samtools fixmate -m sample1.sorted.bam sample1.fixmate.bam
samtools sort -@ 8 -o sample1.fixmate.sorted.bam sample1.fixmate.bam
samtools markdup -@ 8 sample1.fixmate.sorted.bam sample1.markdup.bam
samtools index sample1.markdup.bam

echo "Duplication rate:"
samtools flagstat sample1.markdup.bam | grep "duplicate"

# Option B: Picard MarkDuplicates (GATK best practices)
picard MarkDuplicates \
    INPUT=sample1.sorted.bam \
    OUTPUT=sample1.markdup.bam \
    METRICS_FILE=sample1.dupmetrics.txt \
    REMOVE_DUPLICATES=false \
    CREATE_INDEX=true
cat sample1.dupmetrics.txt | grep -A2 "ESTIMATED"
```

### Step 5: Assess Alignment Quality

Generate alignment statistics and check key quality metrics.

```bash
# Full alignment statistics
samtools flagstat sample1.markdup.bam > sample1.flagstat.txt
cat sample1.flagstat.txt

# Coverage statistics
samtools coverage sample1.markdup.bam | head -30

# Parse key metrics with Python
python3 - << 'EOF'
from pathlib import Path

flagstat = Path("sample1.flagstat.txt").read_text()
for line in flagstat.splitlines():
    if any(kw in line for kw in ["total", "mapped", "properly paired", "duplicate"]):
        print(line)
EOF
```

### Step 6: Complete WGS/WES Pipeline → Variant Calling

Pipe BWA-MEM2 output directly into GATK HaplotypeCaller.

```bash
#!/bin/bash
# Complete WGS alignment → variant calling pipeline
GENOME="GRCh38.fa"
SAMPLE="sample1"
R1="data/${SAMPLE}_R1.fastq.gz"
R2="data/${SAMPLE}_R2.fastq.gz"
THREADS=16
OUTDIR="results/${SAMPLE}"
mkdir -p "$OUTDIR"

# Step 1: Align + sort
bwa-mem2 mem -t $THREADS \
    -R "@RG\tID:${SAMPLE}\tSM:${SAMPLE}\tPL:ILLUMINA\tLB:lib1\tPU:run1" \
    $GENOME $R1 $R2 \
    | samtools sort -@ 8 -o $OUTDIR/${SAMPLE}.sorted.bam
samtools index $OUTDIR/${SAMPLE}.sorted.bam

# Step 2: Mark duplicates
samtools fixmate -m $OUTDIR/${SAMPLE}.sorted.bam - \
    | samtools sort -@ 8 \
    | samtools markdup -@ 8 - $OUTDIR/${SAMPLE}.markdup.bam
samtools index $OUTDIR/${SAMPLE}.markdup.bam

# Step 3: GATK variant calling
gatk HaplotypeCaller \
    -R $GENOME \
    -I $OUTDIR/${SAMPLE}.markdup.bam \
    -O $OUTDIR/${SAMPLE}.g.vcf.gz \
    -ERC GVCF \
    --native-pair-hmm-threads 4

echo "Pipeline complete: $OUTDIR/${SAMPLE}.g.vcf.gz"
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-t` | `1` | 1–64 | CPU threads; use 8–16 for production runs |
| `-R` | — | `@RG\tID:...\tSM:...` | Read group string; **required** for GATK compatibility |
| `-k` | `19` | 10–28 | Minimum seed length; lower = more sensitive for shorter reads |
| `-w` | `100` | 50–500 | Band width for Smith-Waterman alignment |
| `-M` | off | flag | Mark split/supplementary reads as secondary (BWA-MEM style); needed for Picard compatibility |
| `-a` | off | flag | Output all alignments for single-end reads (for seeding; increases file size) |
| `-p` | off | flag | Treat input as interleaved paired-end FASTQ |
| `-c` | `500` | 100–10000 | Skip alignment for MEM count > threshold (reduces multi-mapper noise) |
| `-T` | `30` | 20–60 | Minimum alignment score threshold; lower = report more low-quality alignments |
| `-Y` | off | flag | Use soft clipping for supplementary alignments (recommended for GATK) |

## Common Recipes

### Recipe 1: Batch Align Multiple Samples

```bash
#!/bin/bash
# Align all samples in parallel using GNU parallel or sequential loop
GENOME="GRCh38.fa"
SAMPLES=(ctrl_1 ctrl_2 treat_1 treat_2)
THREADS=12

for sample in "${SAMPLES[@]}"; do
    echo "=== Aligning $sample ==="
    bwa-mem2 mem -t $THREADS \
        -R "@RG\tID:${sample}\tSM:${sample}\tPL:ILLUMINA\tLB:lib1\tPU:run1" \
        $GENOME \
        data/${sample}_R1.fastq.gz \
        data/${sample}_R2.fastq.gz \
        | samtools sort -@ 4 -m 2G -o results/${sample}.sorted.bam
    samtools index results/${sample}.sorted.bam
    
    MAPPED=$(samtools view -c -F 4 results/${sample}.sorted.bam)
    TOTAL=$(samtools view -c results/${sample}.sorted.bam)
    echo "$sample: $MAPPED / $TOTAL reads mapped"
done
```

### Recipe 2: Parse Alignment Metrics with Python

```python
import subprocess
import pandas as pd
from pathlib import Path

samples = ["ctrl_1", "ctrl_2", "treat_1", "treat_2"]
metrics = []

for sample in samples:
    bam = f"results/{sample}.sorted.bam"
    result = subprocess.run(
        ["samtools", "flagstat", bam], capture_output=True, text=True
    )
    stats = {}
    for line in result.stdout.splitlines():
        if "total" in line:
            stats["total"] = int(line.split()[0])
        elif "mapped" in line and "%" in line:
            stats["mapped"] = int(line.split()[0])
            stats["pct_mapped"] = float(line.split("(")[1].split("%")[0])
        elif "properly paired" in line:
            stats["properly_paired"] = int(line.split()[0])
    stats["sample"] = sample
    metrics.append(stats)

df = pd.DataFrame(metrics).set_index("sample")
print(df[["total", "mapped", "pct_mapped", "properly_paired"]])
df.to_csv("alignment_metrics.tsv", sep="\t")
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `*.sorted.bam` | BAM | Coordinate-sorted aligned reads; index with `samtools index` |
| `*.sorted.bam.bai` | BAI | BAM index; required for random access by GATK and IGV |
| `*.flagstat.txt` | Text | Alignment summary: total/mapped/paired/duplicate counts and percentages |
| `*.markdup.bam` | BAM | Duplicate-marked BAM; use as input to GATK HaplotypeCaller |
| `*.dupmetrics.txt` | Text | Picard duplication metrics with estimated library size |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Low mapping rate (< 85%) | Genome mismatch, contamination, or low quality reads | Verify genome assembly matches sample; run FastQC; trim adapters with Trim Galore |
| `@RG` header missing error in GATK | `-R` flag not specified during alignment | Re-align with `-R "@RG\tID:...\tSM:...\tPL:ILLUMINA"` |
| Out of memory during indexing | Insufficient RAM for genome index | BWA-MEM2 requires ~28 GB for human; use classic bwa with less RAM if needed |
| Unbalanced paired-end counts | Interleaved FASTQ or file mismatch | Add `-p` for interleaved; verify R1/R2 read counts with `zcat r1.fq.gz \| wc -l` |
| `[E::bwa_idx_load_from_disk]` error | Index files missing or wrong prefix | Re-run `bwa-mem2 index genome.fa`; ensure all `.0123`, `.bwt.2bit.64` files exist |
| Slow alignment speed | Low thread count or slow I/O | Use `-t 16` or more; store data on SSD; pipe directly to `samtools sort` |
| Supplementary alignments causing issues | Split reads in downstream tools | Add `-M` flag to mark split reads as secondary (Picard compatibility) |
| GATK base quality score recalibration fails | Missing known variant VCF | Download dbSNP VCF for your genome assembly from NCBI or GATK resource bundle |

## References

- [BWA-MEM2 GitHub: bwa-mem2/bwa-mem2](https://github.com/bwa-mem2/bwa-mem2) — source code, pre-compiled binaries, and benchmarks
- Vasimuddin M et al. (2019) "Efficient Architecture-Aware Acceleration of BWA-MEM for Multicore Systems" — *IPDPS 2019*. [DOI:10.1109/IPDPS.2019.00041](https://doi.org/10.1109/IPDPS.2019.00041)
- Li H & Durbin R (2009) "Fast and accurate short read alignment with Burrows-Wheeler Aligner" — *Bioinformatics* 25(14):1754-1760. [DOI:10.1093/bioinformatics/btp324](https://doi.org/10.1093/bioinformatics/btp324)
- [GATK Best Practices for germline short variant discovery](https://gatk.broadinstitute.org/hc/en-us/articles/360035535932) — GATK workflow recommending BWA-MEM2 alignment
