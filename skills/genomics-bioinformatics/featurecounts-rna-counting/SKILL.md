---
name: "featurecounts-rna-counting"
description: "Counts aligned RNA-seq reads overlapping gene features in a GTF annotation. Takes sorted BAM files from STAR alignment and a GTF file; outputs a tab-delimited count matrix per gene across all samples. Handles strandedness (0=unstranded, 1=stranded, 2=reverse-stranded), paired-end, and multi-sample batch counting in a single command. Use Salmon instead for alignment-free quantification; use featureCounts when STAR BAMs already exist and a gene-level count matrix is needed."
license: "GPL-3.0"
---

# featureCounts — RNA-seq Read Counting

## Overview

featureCounts (part of the Subread package) assigns sequencing reads in BAM files to genomic features defined in a GTF/GFF annotation. It counts how many reads overlap each gene (or exon, intron, or custom feature), producing a gene × sample count matrix suitable for differential expression analysis with DESeq2 or edgeR. featureCounts processes multiple BAM files in a single command, reporting read assignment statistics (assigned, unassigned by category) alongside the count matrix. It is the standard counting step after STAR alignment in RNA-seq pipelines.

## When to Use

- Generating gene-level count matrices from STAR-aligned BAM files for DESeq2 or edgeR
- Counting reads from multiple samples simultaneously in a single featureCounts command
- Handling stranded RNA-seq libraries where sense/antisense assignment matters
- Producing exon-level or custom-feature counts (e.g., for splicing analysis with DEXSeq)
- Verifying strandedness of an RNA-seq library when protocol documentation is unavailable
- Use **Salmon** instead when no BAM file exists and fast pseudoalignment is preferred
- Use **HTSeq-count** as an alternative with slower but more flexible counting modes

## Prerequisites

- **Software**: Subread package (contains `featureCounts`)
- **Input**: Sorted BAM files from STAR or HISAT2, plus a matching GTF annotation file

```bash
# Install with conda (recommended)
conda install -c bioconda subread

# Verify
featureCounts -v
# featureCounts v2.0.6

# Alternative: install via apt (Ubuntu/Debian)
sudo apt-get install subread
```

## Quick Start

```bash
# Count reads for multiple samples (unstranded paired-end RNA-seq)
featureCounts \
    -a gencode.v47.annotation.gtf \
    -o counts/gene_counts.txt \
    -T 8 \
    -p --countReadPairs \
    results/sample1/Aligned.sortedByCoord.out.bam \
    results/sample2/Aligned.sortedByCoord.out.bam

echo "Count matrix: counts/gene_counts.txt"
head -3 counts/gene_counts.txt
```

## Workflow

### Step 1: Prepare BAM Files and GTF

Ensure BAM files are sorted and indexed, and the GTF matches the genome assembly.

```bash
# Verify BAM files are sorted
samtools view -H results/sample1/Aligned.sortedByCoord.out.bam | grep "SO:"
# Expected: SO:coordinate

# List BAMs to count
ls results/*/Aligned.sortedByCoord.out.bam | head -5

# Download GENCODE GTF (same version used for STAR indexing)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_47/gencode.v47.primary_assembly.annotation.gtf.gz
gunzip gencode.v47.primary_assembly.annotation.gtf.gz

echo "GTF lines: $(wc -l < gencode.v47.primary_assembly.annotation.gtf)"
```

### Step 2: Determine Library Strandedness

Test strandedness using a small read count to set the `-s` parameter correctly.

```bash
# Quick strandedness check: count 1 sample with all 3 modes
# Compare assigned rates: highest = correct mode
for strand in 0 1 2; do
    echo "=== Strandedness -s $strand ==="
    featureCounts \
        -a gencode.v47.primary_assembly.annotation.gtf \
        -o /tmp/test_s${strand}.txt \
        -T 4 \
        -p --countReadPairs \
        -s $strand \
        results/sample1/Aligned.sortedByCoord.out.bam 2>&1 \
        | grep "Successfully assigned"
done
# Rule: 0=unstranded if similar rates; 1 or 2 if one is much higher
```

### Step 3: Count Unstranded Paired-End RNA-seq

Standard configuration for unstranded libraries (most polyA-selected RNA-seq).

```bash
mkdir -p counts

# Multi-sample batch counting: pass all BAMs as positional arguments
featureCounts \
    -a gencode.v47.primary_assembly.annotation.gtf \
    -o counts/gene_counts.txt \
    -T 8 \
    -p \
    --countReadPairs \
    -s 0 \
    -t exon \
    -g gene_id \
    results/ctrl_1/Aligned.sortedByCoord.out.bam \
    results/ctrl_2/Aligned.sortedByCoord.out.bam \
    results/treat_1/Aligned.sortedByCoord.out.bam \
    results/treat_2/Aligned.sortedByCoord.out.bam

echo "Count matrix: $(wc -l < counts/gene_counts.txt) genes"
# Also generates: counts/gene_counts.txt.summary (assignment stats)
cat counts/gene_counts.txt.summary
```

### Step 4: Count Stranded Libraries

For strand-specific libraries (TruSeq Stranded, QuantSeq), set the correct strandedness.

```bash
# Reverse-stranded library (most TruSeq Stranded protocols): -s 2
featureCounts \
    -a gencode.v47.primary_assembly.annotation.gtf \
    -o counts/gene_counts_stranded.txt \
    -T 8 \
    -p --countReadPairs \
    -s 2 \
    results/*/Aligned.sortedByCoord.out.bam

# Forward-stranded (e.g., Lexogen QuantSeq, Takara SMARTer): -s 1
# featureCounts ... -s 1 ...

echo "Stranded count complete."
head -2 counts/gene_counts_stranded.txt
```

### Step 5: Load Count Matrix into Python for DESeq2

Parse the featureCounts output file and prepare for differential expression.

```python
import pandas as pd

# featureCounts output has 6 metadata columns before count columns
counts_raw = pd.read_csv("counts/gene_counts.txt", sep="\t", comment="#")
print(f"Columns: {list(counts_raw.columns)}")

# Metadata columns: Geneid, Chr, Start, End, Strand, Length
# Count columns start at index 6
count_cols = counts_raw.columns[6:]  # BAM file paths as column names
counts = counts_raw.set_index("Geneid")[count_cols].copy()

# Rename columns to sample names (strip path and file extension)
import re
counts.columns = [re.sub(r".*/|Aligned\.sortedByCoord\.out\.bam", "", col)
                  for col in counts.columns]

print(f"Count matrix shape: {counts.shape}")  # (genes × samples)
print(f"Samples: {list(counts.columns)}")
print(f"Genes with counts > 0: {(counts.sum(axis=1) > 0).sum()}")
counts.to_csv("gene_count_matrix.tsv", sep="\t")
print("Saved: gene_count_matrix.tsv")
```

### Step 6: Run DESeq2 with featureCounts Matrix

Use the count matrix directly in pydeseq2 for differential expression.

```python
import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats

# Load count matrix (genes × samples)
counts = pd.read_csv("gene_count_matrix.tsv", sep="\t", index_col=0).T
print(f"Count matrix: {counts.shape} (samples × genes)")

# Sample metadata
metadata = pd.DataFrame({
    "condition": ["control", "control", "treated", "treated"]
}, index=counts.index)

# Filter low-count genes (recommended before DESeq2)
counts_filtered = counts.loc[:, counts.sum() > 10]
print(f"Genes after low-count filter: {counts_filtered.shape[1]}")

# Run DESeq2
dds = DeseqDataSet(counts=counts_filtered, metadata=metadata,
                   design_factors="condition",
                   inference=DefaultInference(n_cpus=8))
dds.deseq2()

stat_res = DeseqStats(dds, contrast=["condition", "treated", "control"],
                      inference=DefaultInference())
stat_res.summary()
results = stat_res.results_df
sig = results[results["padj"] < 0.05]
print(f"DE genes (padj < 0.05): {len(sig)}")
print(sig.sort_values("log2FoldChange", ascending=False).head())
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-a` | required | GTF/GFF3 path | Annotation file; must match genome assembly used for alignment |
| `-o` | required | file path | Output count table path (also creates `<output>.summary`) |
| `-T` | `1` | 1–64 | CPU threads; 8–16 is typical |
| `-s` | `0` | `0` (unstranded), `1` (stranded), `2` (reverse-stranded) | Library strandedness; wrong value causes major undercounting |
| `-p` | off | flag | Paired-end mode; reads counted as fragments not individual reads |
| `--countReadPairs` | off | flag | For PE: count pairs not reads (use with `-p`) |
| `-t` | `exon` | feature type string | Feature type to count from GTF column 3 |
| `-g` | `gene_id` | attribute string | GTF attribute to group features (use `gene_id` for genes) |
| `--minOverlap` | `1` | 1–100 | Minimum bases a read must overlap a feature to be counted |
| `--fracOverlap` | `0` | 0–1 | Fraction of read that must overlap; `0.2` for stricter counting |
| `-O` | off | flag | Allow reads to be assigned to multiple overlapping features |
| `-M` | off | flag | Count multi-mapping reads (default: only uniquely mapped) |

## Common Recipes

### Recipe 1: Count with Subread Package via Python subprocess

```python
import subprocess
import re
from pathlib import Path

def run_featurecounts(bam_files: list, gtf: str, outfile: str,
                      threads: int = 8, strandedness: int = 0,
                      paired_end: bool = True) -> dict:
    """Run featureCounts and return assignment statistics."""
    cmd = [
        "featureCounts",
        "-a", gtf,
        "-o", outfile,
        "-T", str(threads),
        "-s", str(strandedness),
        "-t", "exon",
        "-g", "gene_id",
    ]
    if paired_end:
        cmd += ["-p", "--countReadPairs"]
    cmd += bam_files

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse summary from stderr
    stats = {}
    for line in result.stderr.splitlines():
        if "Assigned" in line:
            stats["assigned_pct"] = float(re.search(r"(\d+\.\d+)%", line).group(1))
    return stats

bams = list(Path("results").glob("*/Aligned.sortedByCoord.out.bam"))
bam_list = [str(b) for b in sorted(bams)]
stats = run_featurecounts(bam_list, "gencode.v47.primary_assembly.annotation.gtf",
                          "counts/gene_counts.txt")
print(f"Assigned reads: {stats.get('assigned_pct', 'N/A')}%")
```

### Recipe 2: Add featureCounts to a Snakemake Pipeline

```python
# Snakefile — featureCounts rule after STAR alignment
configfile: "config.yaml"
SAMPLES = config["samples"]

rule featurecounts:
    input:
        bams = expand("results/{sample}/Aligned.sortedByCoord.out.bam", sample=SAMPLES),
        gtf = config["gtf"]
    output:
        counts = "counts/gene_counts.txt",
        summary = "counts/gene_counts.txt.summary"
    params:
        strandedness = config.get("strandedness", 0)
    threads: 8
    shell:
        """
        featureCounts \
            -a {input.gtf} \
            -o {output.counts} \
            -T {threads} \
            -p --countReadPairs \
            -s {params.strandedness} \
            -t exon -g gene_id \
            {input.bams}
        """
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `gene_counts.txt` | TSV | Count matrix: gene metadata + one count column per BAM |
| `gene_counts.txt.summary` | TSV | Read assignment statistics per sample (Assigned, Unassigned_*)  |
| stderr log | Text | Per-sample assignment percentages and warnings |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Very low assigned rate (< 40%) | Wrong strandedness `-s` value | Test all 3 `-s` modes; match to library prep protocol |
| GTF not matching genome | Different assembly or annotation version | Verify genome + GTF are same version (e.g., both GRCh38/GENCODE v47) |
| `Error: Failed to open the annotation file` | GTF file path wrong or compressed | Decompress GTF; use absolute path |
| Count matrix has 0 for all genes | Wrong `-t` feature type | Check GTF column 3 with `awk '{print $3}' file.gtf \| sort -u \| head` |
| Multi-mapping reads not counted | `-M` not set | Add `-M` to count multi-mappers; may inflate counts for repetitive regions |
| Paired-end reads counted as single | `-p` flag missing | Add `-p --countReadPairs` for paired-end BAMs |
| Very slow on large BAM files | Low thread count | Increase `-T` to 8–16; ensure BAMs are sorted by coordinate |
| `gene_id` attribute missing | GFF3 file uses different attribute | Use `-g ID` for GFF3; check attributes with `grep -v "^#" file.gff3 \| head -5` |

## References

- [Subread documentation](https://subread.sourceforge.net/) — featureCounts user guide and parameter reference
- Liao Y, Smyth GK, Shi W (2014) "featureCounts: an efficient general purpose program for assigning sequence reads to genomic features" — *Bioinformatics* 30(7):923-930. [DOI:10.1093/bioinformatics/btt656](https://doi.org/10.1093/bioinformatics/btt656)
- [Subread GitHub: ShiLab-Bioinformatics/subread](https://github.com/ShiLab-Bioinformatics/subread) — source code and releases
- [RNAseq123 workflow](https://bioconductor.org/packages/RNAseq123/) — Bioconductor RNA-seq workflow using featureCounts → edgeR
