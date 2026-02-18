---
name: "salmon-rna-quantification"
description: "Ultra-fast RNA-seq transcript and gene-level quantification using quasi-mapping (no BAM required). Builds a k-mer index from a transcriptome FASTA, then quantifies reads in minutes. Outputs transcript-level TPM/count tables (quant.sf) with optional GC-bias and sequence-bias correction. Integrates directly with tximeta/tximport for DESeq2 or edgeR. Use STAR instead when a genome-aligned BAM is required for variant calling or visualization."
license: "GPL-3.0"
---

# Salmon — Fast RNA-seq Quantification

## Overview

Salmon quantifies transcript abundance from RNA-seq reads using quasi-mapping — matching reads to a k-mer index of the transcriptome without full genome alignment. This makes Salmon 20–50× faster than alignment-based tools while producing accurate TPM and estimated count values. Salmon corrects for sequence-specific bias (`--seqBias`), GC-content bias (`--gcBias`), and fragment length distribution automatically. Output `quant.sf` files integrate directly with `tximeta` (R) or `pydeseq2` (Python) for differential expression analysis. For improved accuracy, decoy-aware indexing uses the full genome to identify spurious quasi-mappings.

## When to Use

- Performing fast RNA-seq quantification when you do not need a genome-aligned BAM file
- Running large-scale RNA-seq studies where alignment speed is a bottleneck (Salmon is 20-50× faster than STAR + featureCounts)
- Computing TPM and estimated counts from bulk RNA-seq for differential expression with DESeq2 or edgeR
- Correcting for GC bias, fragment length, and sequence context bias with `--gcBias --seqBias`
- Estimating transcript-level uncertainty via bootstrap resampling with `--numBootstraps`
- Use **STAR** instead when you need a genome-aligned BAM for downstream tools (variant calling, deeptools, IGV visualization)
- Use **Kallisto** as an alternative for similar speed; Salmon provides better bias correction and decoy-aware indexing

## Prerequisites

- **Software**: Salmon ≥ 1.10 (conda or pre-compiled binary)
- **Reference**: transcriptome FASTA (cDNA sequences, e.g., GENCODE or Ensembl) + genome FASTA for decoy-aware indexing
- **Python packages**: `pandas` for parsing output; `pydeseq2` for differential expression

```bash
# Install with conda (recommended)
conda install -c bioconda salmon

# Verify
salmon --version
# salmon 1.10.3

# Or download pre-compiled binary
wget https://github.com/COMBINE-lab/salmon/releases/download/v1.10.0/salmon-1.10.0_linux_x86_64.tar.gz
tar xzvf salmon-1.10.0_linux_x86_64.tar.gz
export PATH="$PWD/salmon-latest_linux_x86_64/bin:$PATH"
```

## Quick Start

```bash
# 1. Build transcriptome index (~5 min)
salmon index -t transcriptome.fa -i salmon_index/ -p 8

# 2. Quantify paired-end reads (~2-5 min per sample)
salmon quant \
    -i salmon_index/ \
    -l A \
    -1 sample_R1.fastq.gz \
    -2 sample_R2.fastq.gz \
    -p 8 \
    --gcBias --validateMappings \
    -o results/sample1/

# Output: results/sample1/quant.sf
head results/sample1/quant.sf
```

## Workflow

### Step 1: Download Transcriptome Reference

Fetch a transcript FASTA from GENCODE or Ensembl (cDNA sequences only — not genome).

```bash
# Human transcriptome from GENCODE (recommended)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_47/gencode.v47.transcripts.fa.gz
gunzip gencode.v47.transcripts.fa.gz

# Count transcripts
grep -c "^>" gencode.v47.transcripts.fa
# ~252,000 transcripts

echo "Reference ready."
ls -lh gencode.v47.transcripts.fa
```

### Step 2: Build Salmon Index

Index the transcriptome for quasi-mapping. Add genome decoys for improved accuracy.

```bash
# Standard index (fast, sufficient for most analyses)
salmon index \
    -t gencode.v47.transcripts.fa \
    -i salmon_index/ \
    -p 8
echo "Standard index complete."

# Decoy-aware index (recommended for accuracy — uses full genome as decoy)
# Step 1: create decoy list from genome chromosome names
grep "^>" GRCh38.primary_assembly.genome.fa | cut -d " " -f 1 | sed 's/>//' > decoys.txt

# Step 2: concatenate transcriptome + genome
cat gencode.v47.transcripts.fa GRCh38.primary_assembly.genome.fa > gentrome.fa

# Step 3: build decoy-aware index
salmon index \
    -t gentrome.fa \
    -d decoys.txt \
    -i salmon_decoy_index/ \
    -p 8
echo "Decoy-aware index complete."
```

### Step 3: Quantify Single-End Reads

Run Salmon on single-end FASTQ files.

```bash
# Single-end quantification
salmon quant \
    -i salmon_index/ \
    -l A \
    -r sample1.fastq.gz \
    -p 8 \
    --seqBias \
    --validateMappings \
    -o results/sample1/

echo "Mapping rate: $(grep 'Mapping rate' results/sample1/logs/salmon_quant.log | tail -1)"
echo "Output: results/sample1/quant.sf"
```

### Step 4: Quantify Paired-End Reads with Bias Correction

Run Salmon on paired-end FASTQ files with recommended bias correction flags.

```bash
# Paired-end with GC bias + sequence bias correction
salmon quant \
    -i salmon_decoy_index/ \
    -l A \
    -1 sample1_R1.fastq.gz \
    -2 sample1_R2.fastq.gz \
    -p 8 \
    --gcBias \
    --seqBias \
    --validateMappings \
    --numBootstraps 100 \
    -o results/sample1/

# quant.sf columns: Name, Length, EffectiveLength, TPM, NumReads
head results/sample1/quant.sf
```

### Step 5: Load and Summarize Quantification Output

Parse `quant.sf` to build a gene-level count matrix for differential expression.

```python
import pandas as pd
from pathlib import Path

# Load single-sample output
quant = pd.read_csv("results/sample1/quant.sf", sep="\t")
print(f"Transcripts quantified: {len(quant)}")
print(f"Total estimated reads: {quant['NumReads'].sum():.0f}")
print(f"Transcripts with TPM > 1: {(quant['TPM'] > 1).sum()}")
print(quant.sort_values("TPM", ascending=False).head())

# Build a multi-sample TPM matrix
samples = ["ctrl_1", "ctrl_2", "treat_1", "treat_2"]
tpm_matrix = pd.DataFrame({
    s: pd.read_csv(f"results/{s}/quant.sf", sep="\t").set_index("Name")["TPM"]
    for s in samples
})
print(f"\nTPM matrix: {tpm_matrix.shape}")
tpm_matrix.to_csv("tpm_matrix.tsv", sep="\t")
```

### Step 6: Aggregate to Gene Level and Run DESeq2

Summarize transcript-level estimates to gene level and perform differential expression.

```python
import pandas as pd
import re
from pathlib import Path
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats

# Aggregate transcript counts to gene level using Ensembl gene IDs
# quant.sf Name format: "ENST00000456328.2|ENSG00000223972.6|..."
def extract_gene_id(transcript_id):
    parts = transcript_id.split("|")
    return parts[1].split(".")[0] if len(parts) > 1 else transcript_id

samples = ["ctrl_1", "ctrl_2", "treat_1", "treat_2"]
count_frames = []
for s in samples:
    df = pd.read_csv(f"results/{s}/quant.sf", sep="\t")
    df["gene_id"] = df["Name"].apply(extract_gene_id)
    gene_counts = df.groupby("gene_id")["NumReads"].sum().round().astype(int)
    count_frames.append(gene_counts.rename(s))

count_matrix = pd.DataFrame(count_frames).fillna(0).astype(int)
metadata = pd.DataFrame({
    "condition": ["control", "control", "treated", "treated"]
}, index=samples)

# Run DESeq2
dds = DeseqDataSet(counts=count_matrix, metadata=metadata,
                   design_factors="condition",
                   inference=DefaultInference(n_cpus=4))
dds.deseq2()

stat_res = DeseqStats(dds, contrast=["condition", "treated", "control"],
                      inference=DefaultInference())
stat_res.summary()
results = stat_res.results_df
print(f"DE genes (padj < 0.05): {(results['padj'] < 0.05).sum()}")
print(results[results['padj'] < 0.05].sort_values('log2FoldChange').head())
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-l / --libType` | required | `A` (auto), `SF`, `SR`, `IU`, `IS`, `MS`, `MR` | Library strandedness; `A` auto-detects from first reads |
| `-p / --threads` | `1` | 1–64 | CPU threads; 8–16 is typical |
| `--gcBias` | off | flag | Correct for GC-content bias in fragment selection; recommended for most samples |
| `--seqBias` | off | flag | Correct for sequence-specific bias at read starts; recommended |
| `--validateMappings` | off | flag | Use selective alignment for improved accuracy; slight speed cost |
| `--numBootstraps` | `0` | 0–200 | Bootstrap replicates for uncertainty estimation; enables Sleuth/Swish |
| `--dumpCsvCounts` | off | flag | Dump raw counts to CSV alongside quant.sf |
| `-d / --decoys` | — | file | Decoy sequence list for decoy-aware indexing |
| `--rangeFactorizationBins` | `4` | 1–8 | Bins for range-factorization model; increases accuracy at small speed cost |
| `--skipQuant` | off | flag | Build index and exit; useful for cluster pipelines |

## Common Recipes

### Recipe 1: Batch Quantify All Samples

```bash
#!/bin/bash
# Quantify all paired-end samples with recommended settings
INDEX="salmon_decoy_index"
DATA="data"
OUT="results"
THREADS=12

SAMPLES=(ctrl_1 ctrl_2 treat_1 treat_2)
mkdir -p "$OUT"

for sample in "${SAMPLES[@]}"; do
    echo "Quantifying: $sample"
    salmon quant \
        -i "$INDEX" \
        -l A \
        -1 "$DATA/${sample}_R1.fastq.gz" \
        -2 "$DATA/${sample}_R2.fastq.gz" \
        -p "$THREADS" \
        --gcBias --seqBias --validateMappings \
        -o "$OUT/$sample/"
    echo "Done: $sample — mapping $(grep 'Mapping rate' $OUT/$sample/logs/salmon_quant.log | tail -1)"
done
echo "All samples quantified."
```

### Recipe 2: Add Salmon to a Snakemake Pipeline

```python
# Snakefile — Salmon quantification rule
configfile: "config.yaml"

SAMPLES = config["samples"]

rule all:
    input:
        expand("results/{sample}/quant.sf", sample=SAMPLES)

rule salmon_index:
    input:
        transcriptome = config["transcriptome_fa"]
    output:
        directory("salmon_index")
    threads: 8
    shell:
        "salmon index -t {input.transcriptome} -i {output} -p {threads}"

rule salmon_quant:
    input:
        index = "salmon_index",
        r1 = "data/{sample}_R1.fastq.gz",
        r2 = "data/{sample}_R2.fastq.gz"
    output:
        quant = "results/{sample}/quant.sf"
    params:
        outdir = "results/{sample}"
    threads: 8
    shell:
        """
        salmon quant -i {input.index} -l A \
            -1 {input.r1} -2 {input.r2} \
            -p {threads} --gcBias --seqBias --validateMappings \
            -o {params.outdir}
        """
```

### Recipe 3: Filter Low-Expression Transcripts and Compute Fold Changes

```python
import pandas as pd
import numpy as np

samples = {
    "ctrl_1": "results/ctrl_1/quant.sf",
    "ctrl_2": "results/ctrl_2/quant.sf",
    "treat_1": "results/treat_1/quant.sf",
    "treat_2": "results/treat_2/quant.sf",
}

# Build TPM matrix
tpm = pd.DataFrame({
    name: pd.read_csv(path, sep="\t").set_index("Name")["TPM"]
    for name, path in samples.items()
})

# Filter: keep transcripts with TPM > 1 in at least 2 samples
expressed = (tpm > 1).sum(axis=1) >= 2
tpm_filt = tpm[expressed]
print(f"Expressed transcripts: {expressed.sum()} / {len(tpm)}")

# Simple log2 fold change (treat vs ctrl)
ctrl_mean = tpm_filt[["ctrl_1", "ctrl_2"]].mean(axis=1)
treat_mean = tpm_filt[["treat_1", "treat_2"]].mean(axis=1)
lfc = np.log2(treat_mean + 0.5) - np.log2(ctrl_mean + 0.5)
top_up = lfc.sort_values(ascending=False).head(10)
print("Top upregulated transcripts:")
print(top_up)
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `quant.sf` | TSV | Transcript-level quantification: Name, Length, EffectiveLength, TPM, NumReads |
| `quant.genes.sf` | TSV | Gene-level quantification (when `--geneMap` provided) |
| `logs/salmon_quant.log` | Text | Detailed log with mapping rate, processed reads, elapsed time |
| `aux_info/meta_info.json` | JSON | Run metadata: library type detected, mapping rate, num processed reads |
| `aux_info/fld.gz` | Binary | Fragment length distribution (paired-end) |
| `bootstrap/` | Binary | Bootstrap count distributions (when `--numBootstraps > 0`) |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Mapping rate < 50% | Wrong transcriptome species or assembly mismatch | Verify transcriptome FASTA matches sample organism; use genome-decoy index |
| Library type detection wrong | Ambiguous or mixed-strand library | Specify explicitly: `-l SF` (stranded fwd) or `-l SR` (stranded rev) |
| `quant.sf` all zeros | Index built from wrong reference | Rebuild index with correct transcriptome FASTA |
| Out of memory during indexing | Transcriptome + genome concatenation too large | Use standard index without genome decoy; or increase available RAM |
| Many low-mapping transcripts | No GC/seq bias correction | Add `--gcBias --seqBias --validateMappings`; helps with low-complexity regions |
| `meta_info.json` mapping rate < 30% | Reads are from a different molecule (e.g., rRNA contamination) | Check FastQC overrepresented sequences; verify library preparation |
| Gene-level output missing | `--geneMap` or `-g` not provided | Re-run with `-g gencode.v47.gtf` to get `quant.genes.sf` |
| Bootstrap takes too long | High `--numBootstraps` on slow disk | Reduce to `--numBootstraps 30` for most DE tests; use SSD |

## References

- [Salmon documentation](https://salmon.readthedocs.io/) — official usage guide and FAQ
- [Salmon GitHub: COMBINE-lab/salmon](https://github.com/COMBINE-lab/salmon) — source, releases, and issues
- Patro R et al. (2017) "Salmon provides fast and bias-aware quantification of transcript expression" — *Nature Methods* 14:417-419. [DOI:10.1038/nmeth.4197](https://doi.org/10.1038/nmeth.4197)
- [tximeta R package](https://bioconductor.org/packages/tximeta/) — recommended for importing Salmon output into R/Bioconductor with full provenance
