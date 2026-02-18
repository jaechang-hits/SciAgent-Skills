---
name: "snakemake-workflow-engine"
description: "Python-based workflow management system for reproducible, scalable pipelines. Define rules with file-based dependencies; Snakemake automatically determines the execution order and parallelism. Supports local, SLURM, LSF, AWS, and Google Cloud execution via profiles; per-rule conda/Singularity environments. Use for bioinformatics NGS pipelines, ML training workflows, and any multi-step file-processing analysis. Use Nextflow instead for Groovy-based dataflow pipelines or when nf-core ecosystem integration is required."
license: "MIT"
---

# Snakemake — Python Workflow Engine

## Overview

Snakemake is a Python-based workflow management system that scales analyses from laptop to HPC and cloud. Workflows are defined as rules with explicit input/output file dependencies; Snakemake resolves the execution order automatically and runs independent steps in parallel. Rules can call shell commands, Python/R/Julia scripts, or inline Python. Per-rule conda or Singularity environments make workflows fully reproducible. Widely used in bioinformatics for NGS, genome assembly, and variant-calling pipelines.

## When to Use

- Building reproducible multi-step bioinformatics pipelines (align → sort → call variants → annotate)
- Scaling the same workflow from local development to SLURM cluster without code changes
- Processing multiple samples identically using wildcard-based rules
- Managing dependencies automatically — only rerun steps whose inputs changed
- Deploying per-rule conda or Singularity environments for tool isolation
- Generating visual DAGs and dry-run previews before committing computational resources
- Use `Nextflow` instead when you need Groovy DSL + dataflow channels, or when leveraging the nf-core community pipeline library
- For simple shell loops, use bash scripts; Snakemake is worth the overhead only for 3+ sequential steps with branching
- Use `Prefect` or `Airflow` instead for data engineering workflows with dynamic task graphs or time-based scheduling

## Prerequisites

- **Python packages**: `snakemake`, `graphviz` (for DAG visualization)
- **Environment**: Python 3.11+; conda/mamba recommended for per-rule environments
- **Data requirements**: Input files, reference files; output paths defined as rules

```bash
# Install via conda (includes optional dependencies)
conda install -c conda-forge -c bioconda snakemake

# Minimal pip install
pip install snakemake

# Verify
snakemake --version
# 8.x.x
```

## Quick Start

```python
# Snakefile — minimal 2-rule pipeline
SAMPLES = ["sampleA", "sampleB"]

rule all:             # Target rule: request final outputs
    input:
        expand("results/{sample}.sorted.bam", sample=SAMPLES)

rule align:
    input:
        fastq="data/{sample}.fastq",
        ref="refs/genome.fa"
    output:
        bam="results/{sample}.sorted.bam"
    threads: 4
    shell:
        "bwa mem -t {threads} {input.ref} {input.fastq} "
        "| samtools sort -@ {threads} -o {output.bam}"
```

```bash
# Run: dry-run first, then execute
snakemake -n            # dry-run: show what would run
snakemake --cores 8     # execute with 8 cores
```

## Core API

### Module 1: Rule Definition

Each rule defines one analysis step with inputs, outputs, and an execution method.

```python
# Shell rule: run a command with {input} and {output} placeholders
rule fastqc:
    input:
        fastq="data/{sample}.fastq"
    output:
        html="qc/{sample}_fastqc.html",
        zip="qc/{sample}_fastqc.zip"
    log:
        "logs/fastqc/{sample}.log"
    shell:
        "fastqc {input.fastq} -o qc/ 2> {log}"
```

```python
# Run rule: inline Python for logic-heavy steps
rule parse_stats:
    input:
        txt="results/{sample}.flagstat.txt"
    output:
        csv="results/{sample}.stats.csv"
    run:
        import re, csv
        lines = open(input.txt).readlines()
        mapped = re.search(r"(\d+) mapped", "".join(lines)).group(1)
        with open(output.csv, "w") as f:
            csv.writer(f).writerow([wildcards.sample, mapped])
```

```python
# Script rule: delegate to external R/Python/Julia script
rule plot_coverage:
    input:
        depth="results/{sample}.depth.txt"
    output:
        pdf="results/{sample}.coverage.pdf"
    script:
        "scripts/plot_coverage.R"
    # In the R script, access via snakemake object:
    # depth_file <- snakemake@input[["depth"]]
    # pdf_path <- snakemake@output[["pdf"]]
```

### Module 2: Wildcards and Pattern Expansion

Wildcards let one rule process any number of samples; `expand()` generates all required file paths.

```python
# Define sample list (from config or glob)
SAMPLES = ["ctrl_rep1", "ctrl_rep2", "treat_rep1", "treat_rep2"]

rule all:
    input:
        # expand() generates: qc/ctrl_rep1_fastqc.html, qc/ctrl_rep2_fastqc.html, ...
        expand("qc/{sample}_fastqc.html", sample=SAMPLES),
        expand("results/{sample}.bam", sample=SAMPLES)

# Access wildcard values inside shell/run
rule align:
    input:
        "data/{sample}.fastq"
    output:
        "results/{sample}.bam"
    shell:
        "echo Processing {wildcards.sample}; "
        "bwa mem refs/genome.fa {input} | samtools view -b > {output}"
```

```python
# Wildcard constraints prevent ambiguous matches
rule process:
    input:
        "data/{sample}_{rep}.fastq"
    output:
        "results/{sample}_{rep}.txt"
    wildcard_constraints:
        sample="[A-Za-z]+",   # letters only
        rep="\d+"             # digits only

# multiext: multiple outputs sharing a common path base
rule bwa_index:
    input:
        "refs/genome.fa"
    output:
        multiext("refs/genome.fa", ".amb", ".ann", ".bwt", ".pac", ".sa")
    shell:
        "bwa index {input}"
```

### Module 3: Configuration and Parameters

Config files externalize settings; `params` passes rule-level values without file dependencies.

```python
# Snakefile: declare config file
configfile: "config/config.yaml"

# config/config.yaml:
# samples: [ctrl, treat]
# threads:
#   align: 8
#   sort: 4
# min_mapq: 20

SAMPLES = config["samples"]

rule filter_reads:
    input:
        "results/{sample}.bam"
    output:
        "results/{sample}.filtered.bam"
    params:
        mapq=config["min_mapq"]    # from config, not a file
    threads:
        config["threads"]["sort"]
    shell:
        "samtools view -q {params.mapq} -b {input} > {output}"
```

```python
# Dynamic params via lambda functions
rule trim:
    input:
        fastq="data/{sample}.fastq"
    output:
        trimmed="trimmed/{sample}.fastq"
    params:
        # Adapt quality threshold based on sample name
        quality=lambda wildcards: 25 if "ctrl" in wildcards.sample else 20
    shell:
        "fastp -q {params.quality} -i {input.fastq} -o {output.trimmed}"
```

### Module 4: Resources and Environments

Declare computational resources for scheduler integration; use conda/Singularity for tool isolation.

```python
# Resource declaration (used by SLURM/LSF profiles)
rule variant_calling:
    input:
        bam="results/{sample}.deduped.bam",
        ref="refs/genome.fa"
    output:
        vcf="variants/{sample}.vcf.gz"
    resources:
        mem_mb=16000,       # memory in MB
        runtime=240,        # max walltime in minutes
        disk_mb=20000       # scratch disk space
    threads: 8
    shell:
        "bcftools mpileup -f {input.ref} {input.bam} "
        "| bcftools call -m -Oz -o {output.vcf}"
```

```python
# Conda environment per rule (for reproducibility)
rule star_align:
    input:
        reads="data/{sample}.fastq",
        genome_dir="refs/star_index/"
    output:
        bam="star_out/{sample}/Aligned.sortedByCoord.out.bam"
    conda:
        "envs/star.yaml"
    # envs/star.yaml:
    # channels:
    #   - bioconda
    # dependencies:
    #   - star=2.7.10b
    #   - samtools=1.17
    threads: 8
    shell:
        "STAR --runThreadN {threads} --genomeDir {input.genome_dir} "
        "--readFilesIn {input.reads} --outSAMtype BAM SortedByCoordinate"
```

```python
# Singularity/Apptainer container
rule gatk_haplotypecaller:
    input:
        bam="results/{sample}.bam",
        ref="refs/genome.fa"
    output:
        gvcf="gvcfs/{sample}.g.vcf.gz"
    container:
        "docker://broadinstitute/gatk:4.4.0.0"
    shell:
        "gatk HaplotypeCaller -I {input.bam} -R {input.ref} "
        "-O {output.gvcf} -ERC GVCF"
```

### Module 5: Execution and Cluster Profiles

Execute locally, on clusters, or in cloud; profiles configure executors without changing the Snakefile.

```bash
# Local execution
snakemake --cores 8                   # use 8 CPU cores
snakemake --cores all                 # use all available cores

# Dry run: show tasks without executing
snakemake -n --cores 8
# Output: 12 of 24 steps are complete. 12 jobs to run.

# Force rerun (ignore existing outputs)
snakemake --forceall --cores 8

# Visualize DAG as PDF
snakemake --dag | dot -Tpdf > workflow_dag.pdf
```

```bash
# SLURM cluster profile (profiles/slurm/config.yaml)
# executor: slurm
# jobs: 50
# default-resources:
#   mem_mb: 2000
#   runtime: 60
# use-conda: true

# Run with profile (cluster submit + monitor)
snakemake --profile profiles/slurm --cores 128

# Override resources at runtime
snakemake --profile profiles/slurm \
    --set-resources variant_calling:mem_mb=32000 --cores 128

# Override threads
snakemake --set-threads align=16 --cores 64
```

### Module 6: Special Output Types and Utilities

Handle temporary files, protected outputs, checkpoints, and output validation.

```python
# temp: auto-delete after downstream rules consume it
rule sort_bam:
    input:
        "results/{sample}.raw.bam"
    output:
        temp("results/{sample}.sorted_temp.bam")  # deleted after indexing
    shell:
        "samtools sort {input} -o {output}"

# protected: write-protect final outputs (prevent overwrite)
rule final_report:
    input:
        "results/{sample}.vcf.gz"
    output:
        protected("reports/{sample}.final.vcf.gz")
    shell:
        "cp {input} {output}"
```

```python
# directory: rule that outputs a directory
rule denovo_assembly:
    input:
        fastq="data/{sample}.fastq"
    output:
        directory("assemblies/{sample}/")
    shell:
        "spades.py -s {input.fastq} -o {output}"

# touch: create empty flag file (for ordering-only dependencies)
rule validate_bam:
    input:
        "results/{sample}.bam"
    output:
        touch("checkpoints/{sample}.validated")
    shell:
        "samtools quickcheck {input} && echo OK"

# ensure: validate output properties before considering rule complete
rule download_reference:
    output:
        ensure("refs/genome.fa", min_size=1_000_000)
    shell:
        "wget -O {output} https://example.com/genome.fa"
```

## Key Concepts

### Rule Resolution and DAG

Snakemake works **backward from targets**: given a list of desired output files, it builds a DAG of rules needed to produce them. Rules not needed for the current targets are ignored.

```python
# rule all: declare all final outputs here
# Without this, snakemake runs only the first rule
rule all:
    input:
        expand("results/{sample}.vcf.gz", sample=SAMPLES),
        expand("qc/{sample}_fastqc.html", sample=SAMPLES)
```

### Wildcards vs Expand

- `{sample}` in rule input/output = wildcard: filled by Snakemake at execution time
- `expand("results/{sample}.bam", sample=SAMPLES)` = Python: generates a list of strings NOW (used in `rule all`)

## Common Workflows

### Workflow 1: Standard NGS QC Pipeline

**Goal**: FastQC → trim → align → sort → dedup → flagstat for multiple samples.

```python
configfile: "config/config.yaml"
SAMPLES = config["samples"]

rule all:
    input:
        expand("qc/{sample}_fastqc.html", sample=SAMPLES),
        expand("results/{sample}.flagstat.txt", sample=SAMPLES)

rule fastqc:
    input:  "data/{sample}.fastq"
    output: "qc/{sample}_fastqc.html", "qc/{sample}_fastqc.zip"
    shell:  "fastqc {input} -o qc/"

rule trim:
    input:  "data/{sample}.fastq"
    output: "trimmed/{sample}.fastq"
    shell:  "fastp -q 20 -i {input} -o {output}"

rule align:
    input:
        fastq="trimmed/{sample}.fastq",
        ref="refs/genome.fa"
    output: temp("results/{sample}.raw.bam")
    threads: 8
    shell:
        "bwa mem -t {threads} {input.ref} {input.fastq} | samtools view -b > {output}"

rule sort_dedup:
    input:  "results/{sample}.raw.bam"
    output:
        bam="results/{sample}.bam",
        bai="results/{sample}.bam.bai"
    threads: 4
    shell:
        "samtools sort -@ {threads} {input} | samtools markdup -r - {output.bam} "
        "&& samtools index {output.bam}"

rule flagstat:
    input:  "results/{sample}.bam"
    output: "results/{sample}.flagstat.txt"
    shell:  "samtools flagstat {input} > {output}"
```

### Workflow 2: Running on a SLURM Cluster

**Goal**: Deploy the same Snakefile to HPC with per-job resource allocation.

```bash
# 1. Create profiles/slurm/config.yaml
mkdir -p profiles/slurm
cat > profiles/slurm/config.yaml << 'EOF'
executor: slurm
jobs: 100
default-resources:
  mem_mb: 4000
  runtime: 60
use-conda: true
latency-wait: 30
rerun-incomplete: true
EOF

# 2. Add resources to compute-heavy rules in Snakefile
# resources:
#   mem_mb=16000, runtime=120

# 3. Submit
snakemake --profile profiles/slurm --cores 256 -n  # dry-run
snakemake --profile profiles/slurm --cores 256      # submit

# 4. Monitor
snakemake --profile profiles/slurm --report report.html  # after completion
```

## Key Parameters

| Parameter | Context | Default | Range/Options | Effect |
|-----------|---------|---------|---------------|--------|
| `--cores` | CLI | 1 | 1–N or `all` | Max concurrent jobs/threads |
| `threads:` | Rule | 1 | 1–N | Threads per rule (scales to `--cores`) |
| `mem_mb:` | `resources:` | None | integer | Memory in MB (used by SLURM profile) |
| `runtime:` | `resources:` | None | integer (min) | Max walltime per job |
| `--profile` | CLI | None | path | YAML profile for executor config |
| `--use-conda` | CLI | False | flag | Activate per-rule conda environments |
| `--use-apptainer` | CLI | False | flag | Enable Singularity/Apptainer containers |
| `-n` | CLI | False | flag | Dry-run (show tasks, don't execute) |
| `--forceall` | CLI | False | flag | Rerun all rules regardless of status |
| `--rerun-incomplete` | CLI | False | flag | Rerun rules with partial outputs |
| `configfile:` | Snakefile | None | YAML path | Load config dictionary from YAML |

## Best Practices

1. **Always define `rule all`**: Without it, only the first rule in the Snakefile runs. `rule all` collects all final outputs; Snakemake runs everything needed to produce them.

2. **Use `temp()` for large intermediates**: BAM files before deduplication, unsorted BAMs, and intermediate assemblies can be marked `temp()` to auto-delete after consumption — saves significant disk.

3. **Separate config from code**: Put sample lists, thread counts, file paths, and thresholds in `config.yaml`. Hard-coded values in Snakefiles make pipelines brittle and non-reusable.

4. **Test with `snakemake -n` first**: The dry-run shows exactly which rules will run and in what order. Run it before every production execution to confirm the DAG is correct.

5. **Use `log:` for every shell rule**: Redirect tool stderr/stdout to per-rule log files (`2> {log}`). Without logs, debugging cluster job failures is nearly impossible.

6. **Benchmark rules in production**: Add `benchmark: "benchmarks/{rule}/{sample}.txt"` to measure actual runtime and memory — essential data for tuning SLURM resource requests.

## Common Recipes

### Recipe: Generate Sample List from Files

```python
# Auto-discover samples from input directory (no hardcoded list)
from pathlib import Path

SAMPLES = [p.stem.replace(".fastq", "") for p in Path("data/").glob("*.fastq")]
print(f"Found {len(SAMPLES)} samples: {SAMPLES[:3]}...")

rule all:
    input:
        expand("results/{sample}.bam", sample=SAMPLES)
```

### Recipe: Conditional Execution Based on Config

```python
configfile: "config/config.yaml"

# Only run deduplication for WGS (not amplicon) data
rule dedup:
    input:
        "results/{sample}.sorted.bam"
    output:
        "results/{sample}.deduped.bam"
    run:
        if config.get("assay_type") == "WGS":
            shell("samtools markdup -r {input} {output}")
        else:
            shell("cp {input} {output}")
```

### Recipe: Aggregate Multiple Samples

```python
# Collect all per-sample stats into one summary table
rule multiqc:
    input:
        expand("qc/{sample}_fastqc.zip", sample=SAMPLES),
        expand("results/{sample}.flagstat.txt", sample=SAMPLES)
    output:
        "multiqc/multiqc_report.html"
    shell:
        "multiqc qc/ results/ -o multiqc/"
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `AmbiguousRuleException` | Multiple rules match same output | Add `wildcard_constraints:`, use `ruleorder rule_a > rule_b`, or rename outputs |
| `MissingOutputException` | Rule completed but output file absent | Check working directory in shell; verify output path; check disk space |
| `TargetFileException` | `rule all` requests a file no rule can produce | Verify `expand()` args match wildcard names; use `-n` to trace resolution |
| Cluster jobs all fail | Resources too low for tool | Increase `mem_mb` or `runtime`; check cluster queue with `squeue` |
| Conda env build fails | Package conflict or wrong channel | Add `conda-forge` before `bioconda`; pin package versions |
| Rule reruns unexpectedly | Output file timestamp older than input | Touch output files with `snakemake --touch`; or delete and rerun |
| `PermissionError` on protected output | `protected()` wrapper applied | Remove protection with `--force`; or delete and regenerate without `protected()` |

## Related Skills

- **samtools-bam-processing** — BAM sorting and indexing rules commonly used in Snakemake pipelines
- **bedtools-genomic-intervals** — interval operations in downstream annotation rules
- **neuropixels-analysis** — example of a complex multi-step pipeline that benefits from Snakemake

## References

- [Snakemake documentation](https://snakemake.readthedocs.io/) — rules, wildcards, profiles, API reference
- [Snakemake GitHub](https://github.com/snakemake/snakemake) — source, releases, issue tracker
- Mölder et al. (2021) "Sustainable data analysis with Snakemake" — [F1000Research 10:33](https://doi.org/10.12688/f1000research.29032.2)
- [Snakemake workflow catalog](https://snakemake.github.io/snakemake-workflow-catalog/) — community-maintained reference pipelines
