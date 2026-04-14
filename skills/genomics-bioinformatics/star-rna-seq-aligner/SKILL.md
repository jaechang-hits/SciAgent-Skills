---
name: "star-rna-seq-aligner"
description: "Splice-aware RNA-seq read aligner producing sorted BAM files and splice junction tables. Performs genome index generation and two-pass alignment for improved junction detection. Outputs coordinate-sorted BAM, splice junctions (SJ.out.tab), alignment statistics (Log.final.out), and optional gene count tables. Use Salmon instead for ultra-fast pseudoalignment; use STAR when you need a genome-aligned BAM for downstream tools (variant calling, visualization, ENCODE pipelines)."
license: "MIT"
---

# STAR — Spliced RNA-seq Aligner

## Overview

STAR (Spliced Transcripts Alignment to a Reference) aligns RNA-seq reads to a genome in a splice-aware manner, identifying novel and annotated splice junctions in a single pass. It generates coordinate-sorted BAM files compatible with samtools, IGV, deeptools, and GATK. STAR's 2-pass mode re-aligns reads using junctions discovered in the first pass, improving sensitivity for novel splice sites. With `--quantMode GeneCounts`, STAR simultaneously produces gene-level read count tables without requiring a separate featureCounts or HTSeq step.

## When to Use

- Aligning bulk RNA-seq reads to a reference genome when downstream tools require a BAM file (variant calling, visualization, deeptools)
- Running ENCODE-compliant RNA-seq pipelines that mandate genome alignment
- Discovering novel splice junctions and alternative splicing events in the dataset
- Generating gene count tables alongside BAM alignment in a single step with `--quantMode GeneCounts`
- Processing long reads or reads with high mismatch rates by tuning `--outFilterMismatchNmax`
- Use **Salmon** instead when you only need transcript/gene quantification and do not need a BAM file — Salmon is 20-50× faster

## Prerequisites

- **Software**: STAR ≥ 2.7.0 (conda or compiled binary)
- **Reference files**: genome FASTA + GTF annotation (same assembly)
- **RAM**: 30–32 GB for human/mouse genome index; 8–16 GB for smaller genomes
- **Disk**: ~25 GB for human genome index, ~5–10 GB per sample BAM

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v STAR` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run STAR` rather than bare `STAR`.

```bash
# Install with conda (recommended)
conda install -c bioconda star

# Verify
STAR --version
# STAR_2.7.11a

# Or compile from source
git clone https://github.com/alexdobin/STAR
cd STAR/source && make STAR
```

## Quick Start

```bash
# 1. Generate genome index (~30 min, run once)
STAR --runMode genomeGenerate \
     --runThreadN 8 \
     --genomeDir genome/star_index \
     --genomeFastaFiles genome/GRCh38.fa \
     --sjdbGTFfile genome/gencode.v47.gtf \
     --sjdbOverhang 100    # ReadLength - 1

# 2. Align paired-end reads (~10-20 min)
STAR --runThreadN 8 \
     --genomeDir genome/star_index \
     --readFilesIn sample_R1.fastq.gz sample_R2.fastq.gz \
     --readFilesCommand zcat \
     --outSAMtype BAM SortedByCoordinate \
     --outFileNamePrefix results/sample/

# 3. Index the BAM
samtools index results/sample/Aligned.sortedByCoord.out.bam
```

## Workflow

### Step 1: Prepare Reference Files

Download a genome FASTA and matching GTF annotation (same assembly version).

```bash
# Download GRCh38 genome and GENCODE annotation
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_47/GRCh38.primary_assembly.genome.fa.gz
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_47/gencode.v47.primary_assembly.annotation.gtf.gz

gunzip GRCh38.primary_assembly.genome.fa.gz gencode.v47.primary_assembly.annotation.gtf.gz
mkdir -p genome/star_index

echo "Genome and GTF ready."
ls -lh GRCh38.primary_assembly.genome.fa gencode.v47.primary_assembly.annotation.gtf
```

### Step 2: Generate Genome Index

Build the STAR genome index — required once per genome/read-length combination.

```bash
# Standard human genome index (requires ~32 GB RAM)
STAR --runMode genomeGenerate \
     --runThreadN 16 \
     --genomeDir genome/star_index/ \
     --genomeFastaFiles GRCh38.primary_assembly.genome.fa \
     --sjdbGTFfile gencode.v47.primary_assembly.annotation.gtf \
     --sjdbOverhang 100

# For small genomes (e.g., E. coli ~4.6 Mb), reduce genomeSAindexNbases
# STAR --runMode genomeGenerate \
#      --genomeSAindexNbases 11 \
#      --genomeDir genome/ecoli_index/ ...

echo "Index complete: $(ls genome/star_index/ | wc -l) files"
```

### Step 3: Align RNA-seq Reads

Align single-end or paired-end FASTQ files to the indexed genome.

```bash
# Single-end alignment
STAR --runThreadN 8 \
     --genomeDir genome/star_index/ \
     --readFilesIn sample1.fastq.gz \
     --readFilesCommand zcat \
     --outSAMtype BAM SortedByCoordinate \
     --outSAMattributes NH HI AS NM MD \
     --outFileNamePrefix results/sample1/

# Paired-end alignment
STAR --runThreadN 8 \
     --genomeDir genome/star_index/ \
     --readFilesIn sample1_R1.fastq.gz sample1_R2.fastq.gz \
     --readFilesCommand zcat \
     --outSAMtype BAM SortedByCoordinate \
     --outSAMattributes NH HI AS NM MD \
     --outFileNamePrefix results/sample1/

echo "BAM: results/sample1/Aligned.sortedByCoord.out.bam"
```

### Step 4: Run 2-Pass Alignment for Improved Sensitivity

Two-pass mode collects splice junctions from the first pass and uses them as annotation for the second pass.

```bash
# First pass — collect splice junctions
STAR --runThreadN 8 \
     --genomeDir genome/star_index/ \
     --readFilesIn sample1_R1.fastq.gz sample1_R2.fastq.gz \
     --readFilesCommand zcat \
     --outSAMtype None \
     --outFileNamePrefix pass1/sample1/

# Second pass — realign with all junctions from pass 1
SJ_FILES=$(ls pass1/*/SJ.out.tab | tr '\n' ' ')

STAR --runThreadN 8 \
     --genomeDir genome/star_index/ \
     --readFilesIn sample1_R1.fastq.gz sample1_R2.fastq.gz \
     --readFilesCommand zcat \
     --sjdbFileChrStartEnd $SJ_FILES \
     --outSAMtype BAM SortedByCoordinate \
     --outFileNamePrefix results/sample1/

# Alternative: single-command 2-pass
STAR --runThreadN 8 \
     --genomeDir genome/star_index/ \
     --readFilesIn sample1_R1.fastq.gz sample1_R2.fastq.gz \
     --readFilesCommand zcat \
     --twopassMode Basic \
     --outSAMtype BAM SortedByCoordinate \
     --outFileNamePrefix results/sample1/
```

### Step 5: Check Alignment Statistics

Parse the alignment log to assess mapping rate and read quality.

```bash
# View the alignment summary
cat results/sample1/Log.final.out

# Parse key metrics with python
python3 - << 'EOF'
import re, sys
from pathlib import Path

log = Path("results/sample1/Log.final.out").read_text()
metrics = {}
for line in log.splitlines():
    if "|" in line:
        key, _, val = line.partition("|")
        metrics[key.strip()] = val.strip()

print(f"Unique mapping:     {metrics.get('Uniquely mapped reads %', 'N/A')}")
print(f"Multi-mapping:      {metrics.get('% of reads mapped to multiple loci', 'N/A')}")
print(f"Too many mismatches:{metrics.get('% of reads unmapped: too many mismatches', 'N/A')}")
print(f"Total input reads:  {metrics.get('Number of input reads', 'N/A')}")
EOF
```

### Step 6: Generate Gene Count Tables

Enable simultaneous gene counting during alignment using `--quantMode GeneCounts`.

```bash
# Align and count simultaneously
STAR --runThreadN 8 \
     --genomeDir genome/star_index/ \
     --readFilesIn sample1_R1.fastq.gz sample1_R2.fastq.gz \
     --readFilesCommand zcat \
     --outSAMtype BAM SortedByCoordinate \
     --quantMode GeneCounts \
     --outFileNamePrefix results/sample1/

# ReadsPerGene.out.tab has 4 columns:
# gene_id  unstranded  stranded_fwd  stranded_rev
head results/sample1/ReadsPerGene.out.tab

# Load into pandas (select column based on library strandedness)
python3 - << 'EOF'
import pandas as pd

df = pd.read_csv("results/sample1/ReadsPerGene.out.tab",
                 sep="\t", header=None, skiprows=4,
                 names=["gene_id", "unstranded", "fwd", "rev"])
# For unstranded library: use column 2 (unstranded)
counts = df.set_index("gene_id")["unstranded"]
print(f"Genes with counts > 0: {(counts > 0).sum()}")
print(counts[counts > 0].sort_values(ascending=False).head())
EOF
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `--runThreadN` | `1` | 1–64 | CPU threads for alignment |
| `--sjdbOverhang` | `99` | ReadLength-1 | Splice junction overhang; set to ReadLength-1 |
| `--outSAMtype` | `SAM` | `BAM SortedByCoordinate`, `BAM Unsorted` | Output format and sort order |
| `--outFilterMismatchNmax` | `10` | 0–33 | Max mismatches per read; lower for stricter mapping |
| `--outFilterMultimapNmax` | `10` | 1–9999 | Max genomic loci per read; reads exceeding limit marked unmapped |
| `--quantMode` | `–` | `GeneCounts`, `TranscriptomeSAM` | Enable gene counting or transcriptome BAM |
| `--twopassMode` | `None` | `None`, `Basic` | Enable 2-pass alignment for novel junction discovery |
| `--alignIntronMax` | `1000000` | 1–1e9 | Maximum intron length; reduce for bacterial genomes |
| `--outReadsUnmapped` | `None` | `Fastx` | Write unmapped reads to FASTQ |
| `--genomeSAindexNbases` | `14` | 10–14 | SA index size; set log2(GenomeSize)/2 − 1 for small genomes |

## Common Recipes

### Recipe 1: Batch Align All Samples

```bash
#!/bin/bash
# Align all paired-end samples in a directory
SAMPLES=(ctrl_1 ctrl_2 treat_1 treat_2)
INDEX="genome/star_index"
DATA="data"
OUT="results"
THREADS=12

mkdir -p "$OUT"
for sample in "${SAMPLES[@]}"; do
    echo "Aligning: $sample"
    mkdir -p "$OUT/$sample"
    STAR --runThreadN "$THREADS" \
         --genomeDir "$INDEX" \
         --readFilesIn "$DATA/${sample}_R1.fastq.gz" "$DATA/${sample}_R2.fastq.gz" \
         --readFilesCommand zcat \
         --outSAMtype BAM SortedByCoordinate \
         --quantMode GeneCounts \
         --twopassMode Basic \
         --outFileNamePrefix "$OUT/$sample/"
    samtools index "$OUT/$sample/Aligned.sortedByCoord.out.bam"
    echo "Done: $sample — $(grep 'Uniquely mapped reads %' $OUT/$sample/Log.final.out | awk '{print $NF}')"
done
```

### Recipe 2: Build Gene Count Matrix Across Samples

```python
import pandas as pd
from pathlib import Path

results_dir = Path("results")
samples = ["ctrl_1", "ctrl_2", "treat_1", "treat_2"]
strandedness = "unstranded"  # or "fwd" / "rev"

col_map = {"unstranded": 1, "fwd": 2, "rev": 3}
col = col_map[strandedness]

counts = {}
for sample in samples:
    count_file = results_dir / sample / "ReadsPerGene.out.tab"
    df = pd.read_csv(count_file, sep="\t", header=None, skiprows=4)
    counts[sample] = df.set_index(0)[col]

matrix = pd.DataFrame(counts)
matrix = matrix[matrix.sum(axis=1) > 0]  # drop zero-count genes
matrix.to_csv("gene_count_matrix.tsv", sep="\t")
print(f"Count matrix: {matrix.shape} (genes × samples)")
print(matrix.head())
```

### Recipe 3: Integrate with DESeq2 via pydeseq2

```python
import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference

# Load count matrix from STAR output
counts = pd.read_csv("gene_count_matrix.tsv", sep="\t", index_col=0).T
metadata = pd.DataFrame({
    "condition": ["control", "control", "treated", "treated"]
}, index=counts.index)

# Run DESeq2
dds = DeseqDataSet(counts=counts, metadata=metadata,
                   design_factors="condition",
                   inference=DefaultInference(n_cpus=4))
dds.deseq2()
print("DESeq2 complete — see dds.varm['LFC'] for results")
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `Aligned.sortedByCoord.out.bam` | BAM | Coordinate-sorted aligned reads; index with `samtools index` |
| `SJ.out.tab` | TSV | Splice junction table with coverage, motif, and novelty flags |
| `Log.final.out` | Text | Alignment statistics: unique mapping %, multimappers %, etc. |
| `ReadsPerGene.out.tab` | TSV | Gene counts (4 columns: unstranded/fwd/rev) when `--quantMode GeneCounts` |
| `Unmapped.out.mate1/2` | FASTQ | Unmapped reads (when `--outReadsUnmapped Fastx`) |
| `Log.out` | Text | Verbose run log; check for warnings and parameter echoes |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Unique mapping < 60% | Wrong genome assembly or species contamination | Verify genome FASTA matches sample species; run FastQC to check overrepresented sequences |
| `Fatal error: genome files not found` | Wrong `--genomeDir` path or incomplete index | Re-run `genomeGenerate`; check `genomeDir` contains `Genome`, `SA`, `SAindex` files |
| Out of memory during genome generation | Not enough RAM for genome SA index | Add `--genomeSAindexNbases 13` (or lower) for small genomes; request ≥32 GB RAM for human |
| `.gz` files not decompressed | Missing `--readFilesCommand zcat` | Add `--readFilesCommand zcat` for gzip-compressed inputs |
| `Error: number of input files differ` | R1/R2 read count mismatch | Verify FASTQ files with `zcat file.fastq.gz | wc -l`; re-download if corrupted |
| `ReadsPerGene.out.tab` missing | `--quantMode GeneCounts` not set | Re-run with `--quantMode GeneCounts` or use featureCounts on BAM |
| Very high multimapping (>20%) | Highly repetitive genome or wrong `--outFilterMultimapNmax` | Reduce `--outFilterMultimapNmax`; use `--outSAMmultNmax 1` to output only one alignment per read |
| Genome index takes too long | Large genome + slow disk | Use SSD storage; pre-built indices available from ENCODE and Ensembl |

## References

- [STAR GitHub repository](https://github.com/alexdobin/STAR) — source code, releases, and STAR manual PDF
- Dobin A et al. (2013) "STAR: ultrafast universal RNA-seq aligner" — *Bioinformatics* 29(1):15-21. [DOI:10.1093/bioinformatics/bts635](https://doi.org/10.1093/bioinformatics/bts635)
- [ENCODE RNA-seq alignment standards](https://www.encodeproject.org/rna-seq/) — ENCODE project guidelines using STAR
- [GENCODE genome annotations](https://www.gencodegenes.org/) — recommended GTF source for human/mouse STAR indices
