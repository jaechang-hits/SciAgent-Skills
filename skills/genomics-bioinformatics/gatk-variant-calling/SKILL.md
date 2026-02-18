---
name: "gatk-variant-calling"
description: "GATK Best Practices pipeline for germline SNP and indel variant calling from WGS/WES BAM files. Runs HaplotypeCaller in GVCF mode per sample, consolidates with GenomicsDBImport, joint-genotypes with GenotypeGVCFs, and applies VQSR or hard filters. Requires BWA-MEM2-aligned, markdup, and BQSR-processed BAMs. Use DeepVariant instead for a faster deep-learning alternative; GATK is the ENCODE/NIH standard for research and clinical genomics."
license: "BSD-3-Clause"
---

# GATK — Germline Variant Calling Pipeline

## Overview

GATK (Genome Analysis Toolkit) implements the GATK Best Practices workflow for calling SNPs and indels from Illumina WGS and WES data. The pipeline runs HaplotypeCaller per sample (producing GVCF files), consolidates GVCFs with GenomicsDBImport, performs joint genotyping with GenotypeGVCFs, and filters variants with VQSR (Variant Quality Score Recalibration) or hard filters. GATK requires BWA-MEM2-aligned, duplicate-marked, and base quality score recalibrated (BQSR) BAM files as input. It integrates with Picard tools, samtools, and bcftools for pre- and post-processing. The GATK4 workflow is the NIH/ENCODE standard for germline variant calling in research and clinical genomics.

## When to Use

- Calling germline SNPs and indels from WGS or WES samples for population genetics or clinical variant analysis
- Running joint genotyping across multiple samples for cohort-scale studies (families, case-control)
- Applying base quality score recalibration (BQSR) to improve variant calling accuracy before HaplotypeCaller
- Generating GVCF files for scalable cohort expansion: add new samples without reprocessing existing ones
- Producing variant call sets for downstream annotation with Ensembl VEP, ANNOVAR, or SnpEff
- Use **DeepVariant** (Google) instead for a faster deep-learning approach with comparable accuracy
- Use **bcftools call** instead for rapid variant calling without assembly-based local realignment

## Prerequisites

- **Software**: GATK4, Java 17+, samtools, BWA-MEM2
- **Reference files**: genome FASTA + known variants VCF (dbSNP, 1000G, Mills indels)
- **Input**: duplicate-marked, sorted BAM with `@RG` read group headers (from BWA-MEM2)

```bash
# Install GATK4
wget https://github.com/broadinstitute/gatk/releases/download/4.6.0.0/gatk-4.6.0.0.zip
unzip gatk-4.6.0.0.zip
export GATK="$PWD/gatk-4.6.0.0/gatk"

# Or with conda
conda install -c bioconda gatk4

# Verify
gatk --version
# GATK v4.6.0.0

# Download GATK resource bundle files (GRCh38)
# From gs://gcp-public-data--broad-references/hg38/v0/ (requires gsutil or Broad FTP)
```

## Quick Start

```bash
GENOME="GRCh38.fa"
DBSNP="dbsnp_146.hg38.vcf.gz"

# Run HaplotypeCaller in GVCF mode
gatk HaplotypeCaller \
    -R $GENOME \
    -I sample1.markdup.bam \
    -O sample1.g.vcf.gz \
    -ERC GVCF \
    --dbsnp $DBSNP \
    --native-pair-hmm-threads 4

echo "GVCF: sample1.g.vcf.gz"
```

## Workflow

### Step 1: Base Quality Score Recalibration (BQSR)

Correct systematic errors in base quality scores before variant calling.

```bash
GENOME="GRCh38.fa"
KNOWN_SITES="dbsnp_146.hg38.vcf.gz Mills_and_1000G_gold_standard.indels.hg38.vcf.gz"
KNOWN_FLAGS=$(printf -- '--known-sites %s ' $KNOWN_SITES)

# Step 1a: Build recalibration table
gatk BaseRecalibrator \
    -R $GENOME \
    -I sample1.markdup.bam \
    $KNOWN_FLAGS \
    -O sample1.recal.table

# Step 1b: Apply recalibration
gatk ApplyBQSR \
    -R $GENOME \
    -I sample1.markdup.bam \
    --bqsr-recal-file sample1.recal.table \
    -O sample1.bqsr.bam

echo "BQSR BAM: sample1.bqsr.bam"
samtools flagstat sample1.bqsr.bam | head -3
```

### Step 2: Call Variants with HaplotypeCaller (GVCF Mode)

Run per-sample variant calling, producing an intermediate GVCF for joint genotyping.

```bash
# HaplotypeCaller in GVCF mode (recommended for cohort analysis)
gatk HaplotypeCaller \
    -R GRCh38.fa \
    -I sample1.bqsr.bam \
    -O gvcfs/sample1.g.vcf.gz \
    -ERC GVCF \
    --dbsnp dbsnp_146.hg38.vcf.gz \
    --native-pair-hmm-threads 4

# For WES: specify target intervals
# gatk HaplotypeCaller ... -L exome_targets.interval_list --interval-padding 100

echo "GVCF: gvcfs/sample1.g.vcf.gz"
zcat gvcfs/sample1.g.vcf.gz | grep -v "^#" | wc -l
```

### Step 3: Consolidate GVCFs with GenomicsDBImport

Merge per-sample GVCFs for efficient joint genotyping.

```bash
# Create sample map file: sample_name\tpath_to_gvcf
printf "ctrl_1\tgvcfs/ctrl_1.g.vcf.gz\n" > sample_map.txt
printf "ctrl_2\tgvcfs/ctrl_2.g.vcf.gz\n" >> sample_map.txt
printf "treat_1\tgvcfs/treat_1.g.vcf.gz\n" >> sample_map.txt
printf "treat_2\tgvcfs/treat_2.g.vcf.gz\n" >> sample_map.txt

# Import GVCFs into GenomicsDB for each chromosome
for CHR in chr1 chr2 chr3; do
    gatk GenomicsDBImport \
        --sample-name-map sample_map.txt \
        --genomicsdb-workspace-path genomicsdb/${CHR} \
        -L $CHR \
        --reader-threads 4
done

echo "GenomicsDB created for $(ls genomicsdb/ | wc -l) chromosomes"
```

### Step 4: Joint Genotyping with GenotypeGVCFs

Genotype all samples simultaneously across the GenomicsDB.

```bash
# Joint genotype all samples
mkdir -p vcfs
for CHR in chr1 chr2 chr3; do
    gatk GenotypeGVCFs \
        -R GRCh38.fa \
        -V gendb://genomicsdb/${CHR} \
        --dbsnp dbsnp_146.hg38.vcf.gz \
        -O vcfs/cohort_${CHR}.vcf.gz
done

# Merge per-chromosome VCFs
gatk MergeVcfs \
    $(ls vcfs/cohort_chr*.vcf.gz | sed 's/^/-I /') \
    -O vcfs/cohort_all.vcf.gz

echo "Joint genotyping complete: vcfs/cohort_all.vcf.gz"
gatk CountVariants -V vcfs/cohort_all.vcf.gz
```

### Step 5: Variant Filtration (Hard Filters)

Apply hard filters for small cohorts where VQSR is underpowered.

```bash
# Separate SNPs and indels
gatk SelectVariants -V vcfs/cohort_all.vcf.gz --select-type-to-include SNP -O vcfs/snps.vcf.gz
gatk SelectVariants -V vcfs/cohort_all.vcf.gz --select-type-to-include INDEL -O vcfs/indels.vcf.gz

# Apply hard filters: SNPs
gatk VariantFiltration \
    -V vcfs/snps.vcf.gz \
    --filter-expression "QD < 2.0" --filter-name "QD2" \
    --filter-expression "FS > 60.0" --filter-name "FS60" \
    --filter-expression "MQ < 40.0" --filter-name "MQ40" \
    --filter-expression "MQRankSum < -12.5" --filter-name "MQRankSum-12.5" \
    -O vcfs/snps_filtered.vcf.gz

# Apply hard filters: Indels
gatk VariantFiltration \
    -V vcfs/indels.vcf.gz \
    --filter-expression "QD < 2.0" --filter-name "QD2" \
    --filter-expression "FS > 200.0" --filter-name "FS200" \
    --filter-expression "ReadPosRankSum < -20.0" --filter-name "ReadPosRankSum-20" \
    -O vcfs/indels_filtered.vcf.gz

# Merge filtered SNPs + indels
gatk MergeVcfs -I vcfs/snps_filtered.vcf.gz -I vcfs/indels_filtered.vcf.gz \
    -O vcfs/cohort_filtered.vcf.gz

echo "PASS variants: $(bcftools view -f PASS vcfs/cohort_filtered.vcf.gz | grep -v '^#' | wc -l)"
```

### Step 6: Parse VCF Results with Python

Extract variants, annotate with gene info, and prepare a DataFrame.

```python
import subprocess
import pandas as pd
import io

# Use bcftools query to extract fields from filtered VCF
result = subprocess.run(
    ["bcftools", "query",
     "-f", "%CHROM\t%POS\t%ID\t%REF\t%ALT\t%QUAL\t%FILTER\t%INFO/QD\t%INFO/FS\n",
     "-i", "FILTER='PASS'",
     "vcfs/cohort_filtered.vcf.gz"],
    capture_output=True, text=True
)

cols = ["CHR", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "QD", "FS"]
df = pd.read_csv(io.StringIO(result.stdout), sep="\t", names=cols)
df["QUAL"] = pd.to_numeric(df["QUAL"], errors="coerce")
df["QD"] = pd.to_numeric(df["QD"], errors="coerce")

print(f"PASS variants: {len(df)}")
print(f"SNPs:  {(df['REF'].str.len() == 1) & (df['ALT'].str.len() == 1)).sum()}")
print(f"Indels: {((df['REF'].str.len() > 1) | (df['ALT'].str.len() > 1)).sum()}")
print(df.head())
df.to_csv("pass_variants.tsv", sep="\t", index=False)
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `-ERC` | `NONE` | `GVCF`, `BP_RESOLUTION` | Emit reference confidence mode; `GVCF` for cohort workflows |
| `--native-pair-hmm-threads` | `4` | 1–32 | Threads for pair-HMM in HaplotypeCaller (most CPU-intensive step) |
| `-L` | whole genome | interval file or chr | Restrict calling to intervals (exome targets, BED regions) |
| `--dbsnp` | — | VCF path | dbSNP VCF for rsID annotation in output |
| `--stand-call-conf` | `30` | 0–100 | Min genotype quality score to emit a variant call |
| `-G` | `StandardAnnotation` | annotation group | Annotation modules to apply (StandardHCAnnotation for HaplotypeCaller) |
| `--sample-name-map` | — | TSV file | Sample-to-GVCF mapping for GenomicsDBImport |
| `--reader-threads` | `1` | 1–16 | Threads for GenomicsDBImport reading |
| `--filter-expression` | — | JEXL expression | Hard filter expression (e.g., `"QD < 2.0"`) |
| `--java-options` | — | `-Xmx4g` | Java heap size; use `-Xmx16g` for large genomes |

## Common Recipes

### Recipe 1: Single-Sample Variant Calling (No Cohort)

```bash
# For a single sample, skip GenomicsDBImport and call directly
gatk HaplotypeCaller \
    -R GRCh38.fa \
    -I sample.bqsr.bam \
    -O sample.vcf.gz \
    --dbsnp dbsnp_146.hg38.vcf.gz \
    --native-pair-hmm-threads 8

# Hard filter the single-sample VCF
gatk VariantFiltration \
    -V sample.vcf.gz \
    --filter-expression "QD < 2.0" --filter-name "QD2" \
    --filter-expression "FS > 60.0" --filter-name "FS60" \
    -O sample_filtered.vcf.gz

echo "PASS variants: $(bcftools view -f PASS sample_filtered.vcf.gz | grep -v '^#' | wc -l)"
```

### Recipe 2: Run Full Pipeline with Snakemake

```python
# Snakefile — GATK BQSR + HaplotypeCaller
configfile: "config.yaml"
SAMPLES = config["samples"]
GENOME  = config["genome"]
DBSNP   = config["dbsnp"]
KNOWN   = config["known_sites"]

rule all:
    input: expand("gvcfs/{sample}.g.vcf.gz", sample=SAMPLES)

rule bqsr:
    input: bam="markdup/{sample}.markdup.bam"
    output: bam="bqsr/{sample}.bqsr.bam"
    shell:
        """
        gatk BaseRecalibrator -R {GENOME} -I {input.bam} \
             --known-sites {KNOWN} -O bqsr/{wildcards.sample}.recal.table &&
        gatk ApplyBQSR -R {GENOME} -I {input.bam} \
             --bqsr-recal-file bqsr/{wildcards.sample}.recal.table \
             -O {output.bam}
        """

rule haplotypecaller:
    input: bam="bqsr/{sample}.bqsr.bam"
    output: gvcf="gvcfs/{sample}.g.vcf.gz"
    threads: 4
    shell:
        "gatk HaplotypeCaller -R {GENOME} -I {input.bam} -O {output.gvcf} "
        "-ERC GVCF --dbsnp {DBSNP} --native-pair-hmm-threads {threads}"
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `*.g.vcf.gz` | GVCF | Per-sample GVCF with reference confidence blocks; input to GenomicsDBImport |
| `cohort_all.vcf.gz` | VCF | Joint-genotyped multi-sample VCF; unfiltered |
| `cohort_filtered.vcf.gz` | VCF | Filtered VCF; FILTER=PASS for passing variants |
| `*.recal.table` | BQSR | Base quality recalibration table from BaseRecalibrator |
| `*.bqsr.bam` | BAM | Recalibrated BAM; use as HaplotypeCaller input |
| `genomicsdb/` | Directory | GenomicsDB workspace per chromosome for joint genotyping |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `SAM/BAM file has no @RG header` | Missing read group from BWA-MEM2 | Re-align with `-R "@RG\tID:...\tSM:...\tPL:ILLUMINA"` |
| Java OutOfMemoryError | Insufficient heap size | Add `--java-options "-Xmx16g"` or more |
| HaplotypeCaller very slow | Single-threaded HMM | Add `--native-pair-hmm-threads 8`; use interval lists to parallelize by chr |
| Empty GVCF output | Wrong interval or no reads in region | Check `samtools view -c sample.bam chrN` for read counts |
| VQSR fails (< 10k variants) | Too few variants for training | Use hard filters instead of VQSR for small cohorts or exomes |
| GenomicsDB import fails on existing path | GenomicsDB workspace already exists | Delete existing workspace: `rm -rf genomicsdb/chr1` before re-running |
| `IndexOutOfBoundsException` | Chromosome name mismatch between BAM and reference | Ensure genome FASTA and BAM use same chr naming (chr1 vs 1) |
| BCFtools/tabix index missing | Tabix index (.tbi) not created | Run `gatk IndexFeatureFile -I file.vcf.gz` or `tabix -p vcf file.vcf.gz` |

## References

- [GATK documentation](https://gatk.broadinstitute.org/hc/en-us) — official pipeline guides and tool documentation
- [GATK Best Practices for germline short variants](https://gatk.broadinstitute.org/hc/en-us/articles/360035535932) — step-by-step protocol
- [GATK GitHub: broadinstitute/gatk](https://github.com/broadinstitute/gatk) — source code, releases, and resource bundle
- Van der Auwera GA & O'Connor BD (2020) *Genomics in the Cloud* — O'Reilly Media; comprehensive GATK4 guide
