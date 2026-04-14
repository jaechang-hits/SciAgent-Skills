---
name: "nextflow-workflow-engine"
description: "Dataflow-based scientific workflow engine for scalable bioinformatics pipelines. Nextflow defines processes (containerized tasks) connected by channels (data queues); supports local, HPC (SLURM/SGE), cloud (AWS/GCP/Azure), and Kubernetes execution with a single config change. Powers the nf-core community pipeline library. Use Snakemake instead for rule-based workflows with Python integration; use Nextflow for containerized, cloud-native, and nf-core-based pipelines."
license: "Apache-2.0"
---

# Nextflow — Scalable Scientific Workflow Engine

## Overview

Nextflow implements a dataflow programming model where **processes** (containerized execution units) consume and emit data through **channels** (asynchronous queues). This design enables implicit parallelization — processes run as soon as their input channels have data, without manual dependency management. Nextflow handles process orchestration across local machines, HPC clusters (SLURM, SGE, PBS), and cloud platforms (AWS Batch, Google Cloud Life Sciences, Azure Batch) by swapping a single configuration profile. The nf-core community provides 100+ validated Nextflow pipelines (RNA-seq, WGS, ChIP-seq, scRNA-seq) following best practices with automated testing.

## When to Use

- Building containerized bioinformatics pipelines that must run on HPC, AWS, and local environments without code changes
- Using nf-core community pipelines (nf-core/rnaseq, nf-core/sarek, nf-core/chipseq) out of the box
- Processing thousands of samples with implicit parallelization across a SLURM cluster
- Writing pipelines where each step runs inside a Docker or Singularity container for reproducibility
- Monitoring pipeline execution and resuming from checkpoints after failures with `-resume`
- Use **Snakemake** instead for Python-native rule-based workflows where Python integration is prioritized
- Use **WDL/Cromwell** instead for clinical genomics pipelines that require CWL/WDL standards compliance

## Prerequisites

- **Software**: Java 11+, Nextflow (self-contained launcher)
- **Containers**: Docker or Singularity for process isolation (recommended)
- **Optional**: nf-core tools for community pipeline management

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v nextflow` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run nextflow` rather than bare `nextflow`.

```bash
# Install Nextflow (self-contained JAR — no sudo required)
curl -s https://get.nextflow.io | bash
chmod +x nextflow
export PATH="$PWD:$PATH"

# Verify
nextflow -version
# Nextflow version 24.10.1

# Install nf-core tools (Python)
pip install nf-core

# Pull an nf-core pipeline
nextflow pull nf-core/rnaseq
```

## Quick Start

```groovy
// hello.nf — minimal Nextflow pipeline
nextflow.enable.dsl = 2

process GREET {
    input: val name
    output: stdout
    script: "echo 'Hello, ${name}!'"
}

workflow {
    Channel.of('World', 'Nextflow') | GREET | view
}
```

```bash
# Run the pipeline
nextflow run hello.nf
# Hello, World!
# Hello, Nextflow!
```

## Core API

### Module 1: Processes — Containerized Task Units

Define processes with inputs, outputs, and shell/script directives.

```groovy
// process_example.nf
nextflow.enable.dsl = 2

process ALIGN_READS {
    // Container for this process
    container 'quay.io/biocontainers/star:2.7.11a--h0033a41_0'
    
    // Resource directives
    cpus 16
    memory '32 GB'
    
    // I/O declarations
    input:
    tuple val(sample_id), path(reads_r1), path(reads_r2)
    path genome_index
    
    output:
    tuple val(sample_id), path("${sample_id}.Aligned.sortedByCoord.out.bam")
    path "${sample_id}.Log.final.out", emit: log
    
    // Shell command
    script:
    """
    STAR --runThreadN ${task.cpus} \\
         --genomeDir ${genome_index} \\
         --readFilesIn ${reads_r1} ${reads_r2} \\
         --readFilesCommand zcat \\
         --outSAMtype BAM SortedByCoordinate \\
         --outFileNamePrefix ${sample_id}.
    """
}
```

### Module 2: Channels — Data Queues Between Processes

Create and transform channels for flexible data routing.

```groovy
nextflow.enable.dsl = 2

workflow {
    // Value channel (broadcast)
    genome_ch = Channel.value(file("GRCh38.fa"))
    
    // List channel
    samples_ch = Channel.of('ctrl_1', 'ctrl_2', 'treat_1', 'treat_2')
    
    // File channel from glob pattern
    reads_ch = Channel.fromFilePairs("data/*_{R1,R2}.fastq.gz")
    // Emits: [sample_id, [R1_file, R2_file]]
    
    // From a CSV sample sheet
    sample_sheet = Channel.fromPath("samplesheet.csv")
        .splitCsv(header: true)
        .map { row -> tuple(row.sample, file(row.fastq_1), file(row.fastq_2)) }
    
    // Channel operators
    filtered = reads_ch
        .filter { id, files -> id.startsWith("ctrl") }
        .view { id, files -> "Processing: ${id}" }
}
```

### Module 3: Workflow Block — Pipeline DAG Definition

Connect processes with channels to define the pipeline DAG.

```groovy
nextflow.enable.dsl = 2

include { FASTP } from './modules/fastp'
include { STAR_ALIGN } from './modules/star'
include { FEATURECOUNTS } from './modules/featurecounts'

workflow RNA_SEQ {
    take:
    reads_ch     // tuple: [sample_id, [R1, R2]]
    genome_idx   // path: STAR index directory
    gtf          // path: annotation GTF file
    
    main:
    // Trim reads
    FASTP(reads_ch)
    
    // Align trimmed reads
    STAR_ALIGN(FASTP.out.reads, genome_idx)
    
    // Count reads (join on sample_id)
    FEATURECOUNTS(STAR_ALIGN.out.bam, gtf)
    
    emit:
    counts = FEATURECOUNTS.out.counts
    logs   = STAR_ALIGN.out.log.mix(FASTP.out.log)
}

workflow {
    reads = Channel.fromFilePairs("data/*_{R1,R2}.fastq.gz")
    genome_idx = Channel.value(file("genome/star_index"))
    gtf = Channel.value(file("genome/annotation.gtf"))
    
    RNA_SEQ(reads, genome_idx, gtf)
    RNA_SEQ.out.counts | view
}
```

### Module 4: Configuration — Profiles for Different Environments

Configure execution profiles for local, HPC, and cloud environments.

```groovy
// nextflow.config — profile-based configuration
profiles {
    local {
        process.executor = 'local'
        process.cpus = 4
        process.memory = '8 GB'
        docker.enabled = true
    }
    
    slurm {
        process.executor = 'slurm'
        process.queue = 'batch'
        process.clusterOptions = '--account=myproject'
        singularity.enabled = true
        singularity.autoMounts = true
        
        // Per-process resource configuration
        process {
            withName: STAR_ALIGN {
                cpus = 16
                memory = '32 GB'
                time = '4h'
            }
            withName: FASTP {
                cpus = 8
                memory = '8 GB'
            }
        }
    }
    
    aws {
        process.executor = 'awsbatch'
        process.queue = 'arn:aws:batch:us-east-1:123456789:job-queue/my-queue'
        aws.region = 'us-east-1'
        aws.batch.cliPath = '/home/ec2-user/miniconda/bin/aws'
        docker.enabled = true
    }
}

// Global params
params {
    outdir    = 'results'
    genome    = 'GRCh38'
    max_cpus  = 16
    max_memory = '128 GB'
    max_time   = '72h'
}
```

### Module 5: Operators — Channel Transformations

Transform channels using built-in operators.

```groovy
nextflow.enable.dsl = 2

workflow {
    // Map: transform each element
    Channel.fromPath("data/*.fastq.gz")
        .map { file -> tuple(file.baseName.replaceAll(/_R[12]/, ''), file) }
        .groupTuple()   // group by sample_id → [sample_id, [R1, R2]]
        .view { id, files -> "Sample: ${id} (${files.size()} files)" }
    
    // Filter by condition
    Channel.of(1, 2, 3, 4, 5)
        .filter { it > 3 }
        .view()  // emits: 4, 5
    
    // Combine channels
    samples = Channel.of('A', 'B', 'C')
    refs = Channel.value(file("genome.fa"))
    samples.combine(refs).view()  // [A, genome.fa], [B, genome.fa], [C, genome.fa]
    
    // Collect all outputs into a list
    Channel.of(1, 2, 3).collect().view()  // [[1, 2, 3]]
}
```

### Module 6: Error Handling and Resuming

Handle failures, retry strategies, and pipeline resuming.

```groovy
// nextflow.config — retry and error handling
process {
    // Retry failed processes up to 3 times with increasing memory
    errorStrategy = { task.exitStatus in [137, 140] ? 'retry' : 'finish' }
    maxRetries = 3
    memory = { 8.GB * task.attempt }   // 8GB → 16GB → 24GB on retries
    
    // Ignore errors for optional steps
    withName: OPTIONAL_STEP {
        errorStrategy = 'ignore'
    }
}
```

```bash
# Resume a pipeline from the last successful checkpoint
nextflow run pipeline.nf -resume

# View process execution statistics
nextflow log amazing_fermi  # use run name from .nextflow.log

# Inspect work directories
ls work/ab/cdef1234*/
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-resume` | off | flag | Resume from last successful checkpoint using cached results |
| `-profile` | — | `local`, `slurm`, `aws`, custom | Select execution profile from nextflow.config |
| `-params-file` | — | JSON/YAML path | Load pipeline parameters from a file |
| `-w / --work-dir` | `./work` | directory path | Work directory for intermediate files |
| `process.cpus` | `1` | integer | Default CPUs per process; override with `withName` |
| `process.memory` | `1 GB` | memory string | Default memory per process |
| `process.executor` | `local` | `local`, `slurm`, `sge`, `awsbatch`, `k8s` | Job scheduler or cloud executor |
| `process.errorStrategy` | `terminate` | `retry`, `ignore`, `finish` | How to handle process failures |
| `process.maxRetries` | `0` | integer | Maximum automatic retries before failure |
| `docker.enabled` | `false` | boolean | Enable Docker container runtime |

## Common Workflows

### Workflow 1: Complete RNA-seq Pipeline (nf-core/rnaseq)

```bash
# Run nf-core/rnaseq with a samplesheet
# samplesheet.csv: sample,fastq_1,fastq_2,strandedness
cat > samplesheet.csv << 'EOF'
sample,fastq_1,fastq_2,strandedness
ctrl_1,data/ctrl_1_R1.fastq.gz,data/ctrl_1_R2.fastq.gz,auto
ctrl_2,data/ctrl_2_R1.fastq.gz,data/ctrl_2_R2.fastq.gz,auto
treat_1,data/treat_1_R1.fastq.gz,data/treat_1_R2.fastq.gz,auto
EOF

# Run nf-core/rnaseq (downloads pipeline and containers automatically)
nextflow run nf-core/rnaseq \
    -profile docker \
    --input samplesheet.csv \
    --genome GRCh38 \
    --outdir results/ \
    -resume

echo "Results in: results/star_salmon/  results/multiqc/"
```

### Workflow 2: Custom Modular Pipeline with Sub-workflows

```groovy
// main.nf — modular pipeline structure
nextflow.enable.dsl = 2

include { QC_TRIM     } from './subworkflows/qc_trim'
include { ALIGN_COUNT } from './subworkflows/align_count'
include { MULTIQC     } from './modules/multiqc'

workflow {
    // Input: sample sheet CSV
    ch_samples = Channel
        .fromPath(params.samplesheet)
        .splitCsv(header: true)
        .map { row -> tuple(row.sample, file(row.fastq_1), file(row.fastq_2)) }
    
    // QC and trimming
    QC_TRIM(ch_samples)
    
    // Alignment and counting
    ALIGN_COUNT(
        QC_TRIM.out.reads,
        file(params.genome_index),
        file(params.gtf)
    )
    
    // Aggregate QC
    all_logs = QC_TRIM.out.logs.mix(ALIGN_COUNT.out.logs).collect()
    MULTIQC(all_logs)
    
    // Publish count matrix
    ALIGN_COUNT.out.counts.view { id, file ->
        "Counts: ${id} → ${file}"
    }
}
```

## Common Recipes

### Recipe 1: Monitor Running Pipeline and View Logs

```bash
# View current pipeline run status
nextflow log

# Detailed log for a specific run
nextflow log amazing_fermi -f name,status,exit,duration,realtime,rss

# Watch pipeline progress in real-time
tail -f .nextflow.log

# Generate HTML execution report and timeline
nextflow run pipeline.nf -with-report report.html -with-timeline timeline.html
open report.html
```

### Recipe 2: Run nf-core Pipeline with Custom Config

```bash
# Create custom config for institutional HPC
cat > custom.config << 'EOF'
process {
    executor = 'slurm'
    queue = 'normal'
    clusterOptions = '--account=myproject'
    
    withName: STAR_ALIGN {
        cpus = 16
        memory = '32 GB'
        time = '4h'
    }
}

singularity {
    enabled = true
    autoMounts = true
    cacheDir = '/scratch/singularity_cache'
}
EOF

nextflow run nf-core/rnaseq \
    -profile singularity \
    -c custom.config \
    --input samplesheet.csv \
    --genome GRCh38 \
    --outdir results/ \
    -resume
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Cannot find a matching process` | DSL2 module not included | Add `include { PROCESS_NAME } from './modules/...'` |
| Work directory fills disk | Accumulated intermediate files | Run `nextflow clean -f` to remove old work directories |
| Container pull fails | Registry authentication or network issue | Pre-pull: `docker pull quay.io/biocontainers/tool:version`; use `--pull never` |
| `resume` doesn't skip completed steps | Process inputs changed or cache invalidated | Check if input files or params changed; use `nextflow log` to inspect cache |
| SLURM job pending indefinitely | Insufficient queue resources | Check with `squeue`; reduce `memory` and `cpus` in config |
| `OutOfMemoryError` in Java | Nextflow JVM heap too small | `export NXF_JVM_ARGS="-Xms1g -Xmx8g"` |
| Process output not found | Wrong output path in `output:` block | Check work directory: `ls work/xx/yyyyyy*/`; verify script creates expected files |
| nf-core pipeline fails checksum | Stale cached pipeline | `nextflow pull nf-core/rnaseq -r latest` to update |

## References

- [Nextflow documentation](https://www.nextflow.io/docs/latest/) — official language reference and executor guides
- [Nextflow GitHub: nextflow-io/nextflow](https://github.com/nextflow-io/nextflow) — source code and releases
- Di Tommaso P et al. (2017) "Nextflow enables reproducible computational workflows" — *Nature Biotechnology* 35:316-319. [DOI:10.1038/nbt.3820](https://doi.org/10.1038/nbt.3820)
- [nf-core](https://nf-co.re/) — community curated Nextflow pipelines with automated testing and containers
