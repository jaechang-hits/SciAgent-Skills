---
name: "multiqc-qc-reports"
description: "Aggregates QC from 150+ bioinformatics tools into one interactive HTML report. Scans FastQC, samtools, STAR, HISAT2, Trim Galore, featureCounts, Kallisto, Salmon, Picard, GATK logs; merges per-sample stats with plots. For NGS pipeline-wide QC. Use FastQC directly for single-sample; MultiQC for multi-sample reporting."
license: "GPL-3.0"
---

# MultiQC — Multi-Sample QC Report Aggregator

## Overview

MultiQC automatically searches directories for QC log files from 150+ bioinformatics tools and aggregates statistics across all samples into a single interactive HTML report. It parses outputs from FastQC, samtools flagstat, STAR, HISAT2, Trim Galore, Salmon, Kallisto, featureCounts, Picard, GATK, and many more — eliminating the need to manually review per-sample QC files. Reports include interactive bar plots, scatter plots, heatmaps, and tables with configurable warnings and pass/fail thresholds.

## When to Use

- Reviewing QC metrics across 10+ samples at once after FastQC, alignment, or quantification
- Final QC checkpoint before differential expression or variant analysis
- Sharing QC summaries with collaborators or including in publications
- Identifying batch effects, outlier samples, or failed sequencing runs
- Combining QC from multi-step pipelines (trimming → alignment → quantification) into one view
- Use FastQC directly instead for initial single-sample QC exploration
- For custom QC metrics not from standard tools, use Python/R directly; MultiQC parses tool outputs only

## Prerequisites

- **Python packages**: `multiqc`
- **Input requirements**: Output files from bioinformatics tools (FastQC `.zip`, samtools `.flagstat`, STAR `Log.final.out`, etc.) — MultiQC finds them automatically
- **Environment**: Python 3.8+

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v multiqc` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run multiqc` rather than bare `multiqc`.

```bash
pip install multiqc

# Verify
multiqc --version
# MultiQC v1.25.0

# With conda (recommended for bioinformatics)
conda install -c bioconda multiqc
```

## Workflow

### Step 1: Generate Tool-Specific QC Files

MultiQC aggregates existing output — first run your QC tools.

```bash
# FastQC on all FASTQ files
mkdir -p qc/fastqc
fastqc data/*.fastq.gz -o qc/fastqc/ -t 8

# samtools flagstat on all BAM files
for bam in results/*.bam; do
    samtools flagstat $bam > qc/$(basename $bam .bam).flagstat
done
echo "QC files generated: $(ls qc/ | wc -l)"
```

### Step 2: Run MultiQC on a Directory

MultiQC recursively scans for recognized QC files.

```bash
# Basic run: scan current directory recursively
multiqc .

# Specify output directory and report name
multiqc . -o reports/ -n project_qc_report

# Scan specific subdirectories only
multiqc qc/fastqc/ results/star/ logs/trimming/ -o reports/

# Output: reports/project_qc_report.html
echo "Report: reports/project_qc_report.html"
```

### Step 3: Configure Report Behavior

Use `multiqc_config.yaml` to set custom thresholds, sample naming, and module order.

```yaml
# multiqc_config.yaml — place in working directory
title: "RNA-seq QC Report — Project X"
subtitle: "Analysis date: 2026-02"
intro_text: "Quality control summary for all 48 samples."

# Sample name cleaning: remove path prefixes and suffixes
fn_clean_exts:
  - ".fastq.gz"
  - "_R1"
  - ".sorted"

# Thresholds for pass/warn/fail coloring
general_stats_addcols:
  FastQC:
    pct_duplication:
      max: 40
      warn: 30

# Module run order
module_order:
  - fastqc
  - trimgalore
  - star
  - featurecounts
  - samtools
```

```bash
# Run with config file
multiqc . --config multiqc_config.yaml -o reports/
```

### Step 4: Use MultiQC Modules and Filters

Control which tools and samples are included.

```bash
# Run only specific modules
multiqc . --module fastqc --module samtools

# Exclude specific modules
multiqc . --exclude fastqc

# Include only files matching a pattern
multiqc . --filename "*.flagstat" --filename "*_fastqc.zip"

# Ignore specific directories or files
multiqc . --ignore "tmp/" --ignore "*.bam"

# Add sample name regex substitution
multiqc . --replace-names "sample_" ""
```

### Step 5: Export Data for Downstream Analysis

Extract machine-readable statistics from the MultiQC report.

```bash
# Export data tables (CSV, JSON, YAML, TSV)
multiqc . -o reports/ --data-format json
# Generates: reports/multiqc_data/multiqc_data.json

# Export flat CSV tables per tool
multiqc . -o reports/ --export
ls reports/multiqc_data/
# multiqc_fastqc.txt, multiqc_samtools_stats.txt, ...

# Extract general stats as pandas DataFrame
python3 - << 'EOF'
import json
import pandas as pd
with open("reports/multiqc_data/multiqc_general_stats.json") as f:
    data = json.load(f)
df = pd.DataFrame(data).T
print(df.head())
print(f"Shape: {df.shape}")
EOF
```

### Step 6: Automate in Pipeline Scripts

Integrate MultiQC as the final step of any QC pipeline.

```bash
#!/bin/bash
# Complete RNA-seq QC pipeline → MultiQC summary
SAMPLES=(ctrl_rep1 ctrl_rep2 treat_rep1 treat_rep2)
OUTDIR="pipeline_output"
mkdir -p $OUTDIR/{fastqc,star,featurecounts,flagstat}

for sample in "${SAMPLES[@]}"; do
    # FastQC
    fastqc data/${sample}.fastq.gz -o $OUTDIR/fastqc/ -t 4
    # STAR alignment
    STAR --runThreadN 8 --genomeDir refs/star_index \
         --readFilesIn data/${sample}.fastq.gz \
         --outSAMtype BAM SortedByCoordinate \
         --outFileNamePrefix $OUTDIR/star/${sample}/
    # samtools flagstat
    samtools flagstat $OUTDIR/star/${sample}/Aligned.sortedByCoord.out.bam \
        > $OUTDIR/flagstat/${sample}.flagstat
done

# Final MultiQC report
multiqc $OUTDIR/ -o $OUTDIR/qc_report/ -n "full_pipeline_qc"
echo "Report ready: $OUTDIR/qc_report/full_pipeline_qc.html"
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-o, --outdir` | `.` | directory path | Output directory for report and data |
| `-n, --filename` | `multiqc_report` | any string | Report filename (without extension) |
| `-m, --module` | all | tool name | Run only specified module(s) |
| `--ignore` | — | glob pattern | Ignore matching files or directories |
| `--export` | False | flag | Export flat tab-delimited data files |
| `--data-format` | `tsv` | `tsv`, `json`, `yaml` | Format for exported data files |
| `--config` | auto-detected | YAML file path | Custom config file with thresholds and naming |
| `--replace-names` | — | regex, replacement | Clean sample names in report |
| `--fn_clean_exts` | (built-in) | list in config | File extensions to strip from sample names |
| `--profile-runtime` | False | flag | Show per-module runtime profiling |

## Common Recipes

### Recipe: Add MultiQC to a Snakemake Pipeline

```python
# In Snakefile: collect all QC outputs, then run MultiQC
rule multiqc:
    input:
        expand("qc/fastqc/{sample}_fastqc.zip", sample=SAMPLES),
        expand("qc/flagstat/{sample}.flagstat", sample=SAMPLES)
    output:
        html="reports/multiqc_report.html",
        data=directory("reports/multiqc_data")
    shell:
        "multiqc qc/ -o reports/ -n multiqc_report"
```

### Recipe: Parse MultiQC Output in Python

```python
import json
import pandas as pd

# Load general stats from JSON export
with open("reports/multiqc_data/multiqc_general_stats.json") as f:
    stats = json.load(f)

df = pd.DataFrame(stats).T
print(f"Samples: {len(df)}")
print(f"Metrics: {list(df.columns[:5])}")

# Flag samples with low mapping rate
if "STAR_mqc-generalstats-star-uniquely_mapped_percent" in df.columns:
    low_mapping = df[df["STAR_mqc-generalstats-star-uniquely_mapped_percent"] < 70]
    print(f"Samples with <70% mapping: {list(low_mapping.index)}")
```

### Recipe: Compare QC Before and After Trimming

```bash
# Run FastQC on raw and trimmed reads, then combine in one report
mkdir -p qc/{raw,trimmed}

fastqc data/*.fastq.gz -o qc/raw/ -t 8
trim_galore data/*.fastq.gz --paired -o trimmed/
fastqc trimmed/*_trimmed.fastq.gz -o qc/trimmed/ -t 8

multiqc qc/raw/ qc/trimmed/ \
    -o reports/ -n raw_vs_trimmed \
    --dirs --dirs-depth 1  # use directory names in sample labels
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `multiqc_report.html` | HTML | Interactive report with all plots and tables |
| `multiqc_data/multiqc_general_stats.txt` | TSV | Per-sample summary statistics (all tools) |
| `multiqc_data/multiqc_*.txt` | TSV | Per-tool detailed statistics tables |
| `multiqc_data/multiqc_data.json` | JSON | Full data (if `--data-format json`) |
| `multiqc_data/multiqc_sources.txt` | TSV | Mapping of source files to samples |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty report (no modules found) | QC files not in scanned directories | Specify directories explicitly: `multiqc qc/ logs/ results/` |
| Wrong sample names in report | File extensions or paths not cleaned | Add `fn_clean_exts` to config or use `--replace-names` |
| Module missing from report | Log file format changed in tool version | Update MultiQC: `pip install --upgrade multiqc`; check GitHub issues |
| Duplicate sample names | Multiple files map to same sample name | Use `--sample-names` or fix `fn_clean_exts` in config |
| Report very slow to open | Too many samples (>500) in one report | Split by project or condition; use `--flat` for simpler rendering |
| FastQC data not parsed | FastQC ZIP not in expected location | Run MultiQC from root of project; ensure `*_fastqc.zip` files exist |
| `ModuleNotFoundError` | Missing optional module dependencies | `pip install multiqc[all]` for all extras |

## References

- [MultiQC documentation](https://multiqc.info/docs/) — official user guide and module list
- [GitHub: ewels/MultiQC](https://github.com/ewels/MultiQC) — source code and community modules
- Ewels et al. (2016) "MultiQC: summarize analysis results for multiple tools and samples in a single report" — [Bioinformatics 32(19)](https://doi.org/10.1093/bioinformatics/btw354)
- [MultiQC supported tools](https://multiqc.info/modules/) — full list of 150+ supported modules
