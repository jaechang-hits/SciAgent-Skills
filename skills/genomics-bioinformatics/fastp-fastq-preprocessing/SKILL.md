---
name: "fastp-fastq-preprocessing"
description: "All-in-one FASTQ quality control and adapter trimming tool. Automatically detects and removes Illumina adapters, filters low-quality reads, corrects paired-end overlaps, and generates HTML+JSON QC reports in a single fast pass. 3-10× faster than Trim Galore/Trimmomatic. Use as the first step before STAR, BWA-MEM2, or Salmon alignment in any NGS pipeline."
license: "MIT"
---

# fastp — Fast FASTQ Quality Control and Adapter Trimming

## Overview

fastp performs adapter trimming, quality filtering, and QC reporting for Illumina FASTQ files in a single multi-threaded pass. It automatically detects adapter sequences from paired-end read overlaps — eliminating the need to specify adapters manually. fastp corrects mismatches in paired-end overlap regions, filters reads by quality score and length, removes polyX tails (polyA for RNA-seq), and generates interactive HTML and machine-readable JSON QC reports. Being 3–10× faster than Trim Galore and Trimmomatic while providing comparable or better results, fastp has become the standard preprocessing step before alignment in WGS, RNA-seq, and ChIP-seq pipelines.

## When to Use

- Trimming Illumina adapters and low-quality bases before alignment in any NGS pipeline (RNA-seq, WGS, WES, ChIP-seq, ATAC-seq)
- Generating per-sample QC reports (HTML + JSON) as the first step of a pipeline, before MultiQC aggregation
- Processing paired-end reads where adapter auto-detection from overlap is preferred over manual adapter specification
- Removing polyA tails from RNA-seq reads from 3′ end-enriched protocols (Smart-seq, QuantSeq)
- Splitting a FASTQ file by UMI or by index for demultiplexing workflows
- Use **Trim Galore** as an alternative when TrimGalore's detailed per-base quality report from FastQC is required alongside trimming
- Use **Trimmomatic** as an alternative for fine-grained control of sliding-window trimming steps

## Prerequisites

- **Software**: fastp (conda or pre-compiled binary)
- **Input**: raw Illumina FASTQ files (single-end or paired-end, .fastq or .fastq.gz)

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v fastp` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run fastp` rather than bare `fastp`.

```bash
# Install with conda
conda install -c bioconda fastp

# Or download pre-compiled binary (Linux)
wget https://github.com/OpenGene/fastp/releases/download/v0.24.0/fastp
chmod +x fastp
./fastp --version
# fastp 0.24.0

# Verify
fastp --version
```

## Quick Start

```bash
# Paired-end adapter trimming with QC report
fastp \
    -i sample_R1.fastq.gz \
    -I sample_R2.fastq.gz \
    -o sample_R1.trimmed.fastq.gz \
    -O sample_R2.trimmed.fastq.gz \
    -h sample_qc.html \
    -j sample_qc.json \
    --thread 8

echo "Trimmed reads in: sample_R1.trimmed.fastq.gz"
```

## Workflow

### Step 1: Single-End Adapter Trimming

Run fastp on single-end FASTQ with automatic adapter detection.

```bash
# Single-end with auto adapter detection
fastp \
    -i sample.fastq.gz \
    -o sample.trimmed.fastq.gz \
    -h sample_qc.html \
    -j sample_qc.json \
    --thread 8 \
    --qualified_quality_phred 20 \
    --length_required 36

echo "Input reads:   $(zcat sample.fastq.gz | wc -l | awk '{print $1/4}')"
echo "Output reads:  $(zcat sample.trimmed.fastq.gz | wc -l | awk '{print $1/4}')"
```

### Step 2: Paired-End Adapter Trimming

Process paired-end FASTQ files with overlap-based adapter detection and correction.

```bash
# Paired-end with overlap-based adapter auto-detection
fastp \
    -i sample_R1.fastq.gz \
    -I sample_R2.fastq.gz \
    -o sample_R1.trimmed.fastq.gz \
    -O sample_R2.trimmed.fastq.gz \
    -h sample_qc.html \
    -j sample_qc.json \
    --thread 8 \
    --correction \
    --detect_adapter_for_pe \
    --qualified_quality_phred 20 \
    --length_required 36

# Specify adapters explicitly (if auto-detection fails)
# fastp -i R1.fq.gz -I R2.fq.gz \
#   --adapter_sequence AGATCGGAAGAGCACACGTCTGAACTCCAGTCA \
#   --adapter_sequence_r2 AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT \
#   -o R1.out.fq.gz -O R2.out.fq.gz
```

### Step 3: Quality Filtering and Read Length Trimming

Configure quality and length thresholds for stricter or more lenient filtering.

```bash
# Strict quality filtering (e.g., for variant calling)
fastp \
    -i sample_R1.fastq.gz \
    -I sample_R2.fastq.gz \
    -o sample_R1.filtered.fastq.gz \
    -O sample_R2.filtered.fastq.gz \
    -h sample_qc.html \
    -j sample_qc.json \
    --thread 8 \
    --qualified_quality_phred 25 \
    --unqualified_percent_limit 20 \
    --length_required 50 \
    --max_len1 150 \
    --max_len2 150 \
    --low_complexity_filter \
    --complexity_threshold 30

echo "Filtering complete. Check sample_qc.html for pass/fail rates."
```

### Step 4: RNA-seq polyA Tail Removal

Remove polyA tails from 3′-enriched RNA-seq protocols before alignment.

```bash
# Remove polyA tails (QuantSeq 3′ mRNA-seq)
fastp \
    -i quantseq_R1.fastq.gz \
    -o quantseq_R1.trimmed.fastq.gz \
    -h quantseq_qc.html \
    -j quantseq_qc.json \
    --thread 8 \
    --trim_poly_x \
    --poly_x_min_len 10 \
    --qualified_quality_phred 20 \
    --length_required 25

# For Smart-seq2 paired-end with polyA
fastp \
    -i smartseq_R1.fastq.gz \
    -I smartseq_R2.fastq.gz \
    -o smartseq_R1.trimmed.fastq.gz \
    -O smartseq_R2.trimmed.fastq.gz \
    --trim_poly_x --poly_x_min_len 10 \
    --thread 8 \
    -h smartseq_qc.html -j smartseq_qc.json
```

### Step 5: Parse QC Report JSON for Pipeline Monitoring

Extract key QC metrics from fastp's JSON output for automated quality gates.

```python
import json
from pathlib import Path

def parse_fastp_json(json_path: str) -> dict:
    with open(json_path) as f:
        data = json.load(f)
    
    before = data["summary"]["before_filtering"]
    after = data["summary"]["after_filtering"]
    
    return {
        "total_reads_in":  before["total_reads"],
        "total_reads_out": after["total_reads"],
        "pct_passed":      after["total_reads"] / before["total_reads"] * 100,
        "q30_rate_before": before["q30_rate"] * 100,
        "q30_rate_after":  after["q30_rate"] * 100,
        "mean_len_before": before["read1_mean_length"],
        "mean_len_after":  after["read1_mean_length"],
        "adapter_trimmed": data["filtering_result"]["adapter_trimmed"],
    }

metrics = parse_fastp_json("sample_qc.json")
for key, val in metrics.items():
    print(f"{key:25s}: {val:.1f}" if isinstance(val, float) else f"{key:25s}: {val:,}")

# Quality gate: fail if < 70% reads pass filter
if metrics["pct_passed"] < 70:
    print("WARNING: Low pass rate — check raw data quality")
```

### Step 6: Batch Preprocessing Pipeline

Process multiple samples sequentially with per-sample QC summaries.

```bash
#!/bin/bash
# Batch paired-end preprocessing for multiple samples
SAMPLES=(ctrl_1 ctrl_2 treat_1 treat_2)
DATA="data"
OUT="trimmed"
QC="qc/fastp"
THREADS=8

mkdir -p "$OUT" "$QC"

for sample in "${SAMPLES[@]}"; do
    echo "=== Processing $sample ==="
    fastp \
        -i "$DATA/${sample}_R1.fastq.gz" \
        -I "$DATA/${sample}_R2.fastq.gz" \
        -o "$OUT/${sample}_R1.fastq.gz" \
        -O "$OUT/${sample}_R2.fastq.gz" \
        -h "$QC/${sample}.html" \
        -j "$QC/${sample}.json" \
        --thread $THREADS \
        --correction \
        --detect_adapter_for_pe \
        --qualified_quality_phred 20 \
        --length_required 36 \
        2>&1 | grep -E "Read[12]|Filtering|Adapter|passed"
done

# Aggregate QC metrics
python3 - << 'EOF'
import json, pandas as pd
from pathlib import Path

rows = []
for jf in sorted(Path("qc/fastp").glob("*.json")):
    with open(jf) as f: data = json.load(f)
    after = data["summary"]["after_filtering"]
    before = data["summary"]["before_filtering"]
    rows.append({
        "sample": jf.stem,
        "reads_in": before["total_reads"],
        "reads_out": after["total_reads"],
        "pct_passed": round(after["total_reads"]/before["total_reads"]*100, 1),
        "q30_after": round(after["q30_rate"]*100, 1),
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("fastp_summary.tsv", sep="\t", index=False)
EOF

# Run MultiQC to aggregate all fastp JSON reports
multiqc qc/fastp/ -o qc/ -n fastp_multiqc_report
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-i / -I` | required | file path | Input FASTQ (R1 and R2 for paired-end) |
| `-o / -O` | required | file path | Output trimmed FASTQ (R1 and R2) |
| `-h / -j` | — | file path | HTML and JSON QC report output paths |
| `--thread` | `3` | 1–16 | CPU threads; 8 is a good balance |
| `--qualified_quality_phred` | `15` | 0–40 | Minimum base quality (Phred); 20 = 1% error |
| `--length_required` | `15` | 1–1000 | Minimum read length after trimming; discard shorter reads |
| `--correction` | off | flag | Correct mismatches in PE overlap region |
| `--detect_adapter_for_pe` | off | flag | Enable overlap-based adapter auto-detection for PE data |
| `--adapter_sequence` | auto | string | Explicit R1 adapter; overrides auto-detection |
| `--trim_poly_x` | off | flag | Trim polyX (polyA/polyT) tails; use for 3′-enriched RNA-seq |
| `--low_complexity_filter` | off | flag | Filter reads with low complexity (< 30% complexity by default) |
| `--split` | off | integer | Split output into N files per direction (for parallelism) |

## Common Recipes

### Recipe 1: Integrate fastp into a Snakemake Pipeline

```python
# Snakefile — fastp trimming rule
configfile: "config.yaml"
SAMPLES = config["samples"]

rule fastp_pe:
    input:
        r1 = "data/{sample}_R1.fastq.gz",
        r2 = "data/{sample}_R2.fastq.gz"
    output:
        r1 = "trimmed/{sample}_R1.fastq.gz",
        r2 = "trimmed/{sample}_R2.fastq.gz",
        html = "qc/{sample}_fastp.html",
        json = "qc/{sample}_fastp.json"
    threads: 8
    shell:
        """
        fastp -i {input.r1} -I {input.r2} \
              -o {output.r1} -O {output.r2} \
              -h {output.html} -j {output.json} \
              --thread {threads} \
              --correction --detect_adapter_for_pe \
              --qualified_quality_phred 20 \
              --length_required 36
        """
```

### Recipe 2: Aggregate fastp JSON Reports with Python

```python
import json
import pandas as pd
from pathlib import Path

qc_dir = Path("qc/fastp")
records = []

for jf in sorted(qc_dir.glob("*.json")):
    with open(jf) as f:
        d = json.load(f)
    b = d["summary"]["before_filtering"]
    a = d["summary"]["after_filtering"]
    records.append({
        "sample": jf.stem.replace("_fastp", ""),
        "reads_in_M": b["total_reads"] / 1e6,
        "reads_out_M": a["total_reads"] / 1e6,
        "pct_passed": a["total_reads"] / b["total_reads"] * 100,
        "q30_pct": a["q30_rate"] * 100,
        "mean_len_bp": a["read1_mean_length"],
        "adapter_pct": d["filtering_result"]["adapter_trimmed"] / b["total_reads"] * 100,
    })

df = pd.DataFrame(records).round(2)
print(df.to_string(index=False))

# Flag low-quality samples
low_q = df[df["pct_passed"] < 80]
if not low_q.empty:
    print(f"\nSamples with < 80% reads passing: {list(low_q['sample'])}")
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `*_R1.trimmed.fastq.gz` | FASTQ.gz | Trimmed R1 reads (adapters and low-quality bases removed) |
| `*_R2.trimmed.fastq.gz` | FASTQ.gz | Trimmed R2 reads (paired-end only) |
| `*.html` | HTML | Interactive QC report with per-base quality, GC content, adapter plots |
| `*.json` | JSON | Machine-readable QC metrics for automation and MultiQC parsing |
| `fastp.log` | Text | stderr summary with pass/fail read counts and filtering statistics |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Adapter not detected in SE mode | SE reads require explicit adapter or `--adapter_sequence` | Use `--detect_adapter_for_pe` only for PE; specify adapter for SE: `--adapter_sequence AGATCGGAAGAGC` |
| Very high adapter content (> 50%) | Short inserts (small RNA, miRNA) or poor library prep | Check library protocol; use `--overlap_len_require 10` to adjust overlap sensitivity |
| Too many reads filtered (< 60% pass) | Over-strict quality thresholds or low-quality sequencing run | Relax `--qualified_quality_phred` to 15; lower `--length_required` to 25 |
| JSON output missing fields | Old fastp version | Upgrade: `conda update fastp` or download latest binary from GitHub |
| MultiQC not parsing fastp JSON | JSON file not in the scanned directory | Run `multiqc qc/` not `multiqc .`; verify JSON files exist with `ls qc/*.json` |
| Output FASTQ is empty | All reads filtered (wrong input or extreme thresholds) | Verify input FASTQ with `zcat sample.fq.gz \| head -8`; run without `--low_complexity_filter` first |
| Slow performance on large files | Low thread count | Increase `--thread` to 8–12; ensure input is on fast storage (SSD) |
| polyA not removed | `--trim_poly_x` not set | Add `--trim_poly_x --poly_x_min_len 10` for 3′-enriched protocols |

## References

- [fastp GitHub: OpenGene/fastp](https://github.com/OpenGene/fastp) — source code, changelog, and usage guide
- Chen S et al. (2018) "fastp: an ultra-fast all-in-one FASTQ preprocessor" — *Bioinformatics* 34(17):i884-i890. [DOI:10.1093/bioinformatics/bty560](https://doi.org/10.1093/bioinformatics/bty560)
- [fastp documentation](https://github.com/OpenGene/fastp#readme) — full parameter reference and recipes
- [MultiQC fastp module](https://multiqc.info/modules/fastp/) — aggregating fastp JSON reports across samples
