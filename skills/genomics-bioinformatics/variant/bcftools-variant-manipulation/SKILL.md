---
name: "bcftools-variant-manipulation"
description: "CLI for VCF/BCF: filter, merge, annotate, query, normalize, compute stats. Core post-variant-calling: quality filtering, multi-sample merging, rsID annotation, genotype extraction. Samtools companion in HTSlib. Use GATK for complex indel realignment during calling; use VCFtools for population genetics stats."
license: "MIT"
---

# bcftools — VCF/BCF Variant Manipulation Toolkit

## Overview

bcftools is the standard command-line toolkit for processing VCF (Variant Call Format) and BCF (Binary Call Format) files in the HTSlib ecosystem. It covers the complete post-variant-calling workflow: format conversion, quality filtering, variant normalization, multi-sample merging, annotation with external databases, genotype extraction, and QC statistics. bcftools uses streaming by design — most commands read from stdin and write to stdout, making it ideal for memory-efficient pipelines on large cohorts.

## When to Use

- Filtering variants by quality (QUAL, DP, AF) after variant calling
- Merging VCF files from multiple samples into a joint call set
- Adding rsIDs or gene annotations to variant calls
- Extracting specific fields (genotypes, allele depths) as tabular output
- Normalizing indel representations and splitting multi-allelic records
- Calling variants from pileup output (mpileup + call)
- Computing per-sample and overall VCF QC statistics
- Use `GATK HaplotypeCaller` instead when calling variants with local realignment in human samples
- Use `VCFtools` instead for population genetics statistics (Fst, LD, Hardy-Weinberg)
- Use `bcftools` in the HTSlib pipeline; use `picard` for duplicate-marking and library metrics

## Prerequisites

- **Installation**: bcftools 1.17+ (part of HTSlib suite with samtools)
- **Input requirements**: VCF or BGzipped+tabix-indexed VCF (`.vcf.gz + .vcf.gz.tbi`) for region queries
- **Companion tools**: `samtools` for BAM processing; `tabix` for VCF indexing

> **Check before installing**: The tool may already be available in the current environment (e.g., inside a `pixi` / `conda` env). Run `command -v bcftools` first and skip the install commands below if it returns a path. When running inside a pixi project, invoke the tool via `pixi run bcftools` rather than bare `bcftools`.

```bash
# Bioconda (recommended — installs HTSlib suite)
conda install -c bioconda bcftools

# Homebrew (macOS)
brew install bcftools

# Verify
bcftools --version | head -1
# bcftools 1.20

# Index a VCF for region queries
bcftools index -t variants.vcf.gz   # creates .tbi
bcftools index -c variants.vcf.gz   # creates .csi (for chromosomes > 512 Mb)
```

## Quick Start

```bash
# Typical post-calling workflow: normalize → filter → annotate → extract
bcftools norm -d any -f reference.fa variants.vcf.gz \
  | bcftools filter -i 'QUAL>20 && DP>10' \
  | bcftools annotate -a dbSNP.vcf.gz -c ID \
  | bcftools view -O z -o final.vcf.gz

# Index the output
bcftools index -t final.vcf.gz

# Count variants at each stage
bcftools stats final.vcf.gz | grep "^SN"
```

## Core API

### Module 1: VCF/BCF I/O and Format Conversion

Convert between text VCF and binary BCF; compress and index for random access.

```bash
# VCF → compressed BCF (fastest format for piping)
bcftools view -O b -o variants.bcf variants.vcf

# BCF → VCF (for human-readable output)
bcftools view -O v -o variants.vcf variants.bcf

# VCF → bgzipped + indexed (standard archive format)
bcftools view -O z -W -o variants.vcf.gz variants.vcf
# -W automatically creates .tbi index after writing
```

```bash
# Extract specific samples
bcftools view -s sample1,sample2 -O z -o subset.vcf.gz variants.vcf.gz

# Exclude samples (prefix with ^)
bcftools view -s ^outlier_sample -O z -o cleaned.vcf.gz variants.vcf.gz

# Extract by region (fast; requires index)
bcftools view -r chr1:1000000-2000000 variants.vcf.gz -O v -o chr1_region.vcf

# Streaming pipeline: no intermediate files
samtools mpileup -Ou input.bam | bcftools call -m -Oz -o calls.vcf.gz
```

### Module 2: Variant Filtering

Apply quality thresholds and FLAG-based filters to retain high-confidence calls.

```bash
# Expression-based filter (include)
bcftools filter -i 'QUAL>20 && DP>10' variants.vcf.gz -O z -o filtered.vcf.gz

# Expression-based filter (exclude)
bcftools filter -e 'QUAL<10 || DP<5' variants.vcf.gz -O v -o filtered.vcf

# Soft filter: mark but keep (sets FILTER field to label)
bcftools filter -s LowQual -e 'QUAL<20' variants.vcf.gz -O z -o soft_filtered.vcf.gz
# Variants with QUAL<20 get FILTER="LowQual"; others get FILTER=PASS
```

```bash
# Keep only PASS variants
bcftools view -f PASS variants.vcf.gz -O z -o pass_only.vcf.gz

# SNP-only output
bcftools view --type snps variants.vcf.gz -O z -o snps.vcf.gz

# Indel-only output
bcftools view --type indels variants.vcf.gz -O z -o indels.vcf.gz

# Filter by allele frequency and depth
bcftools filter -i 'AF>0.1 && DP>20 && MQ>40' variants.vcf.gz -O z -o confident.vcf.gz

# Remove SNPs within 3 bp of indels
bcftools filter --SnpGap 3 variants.vcf.gz -O z -o gapfiltered.vcf.gz
```

### Module 3: VCF Query and Extraction

Transform VCF content into tabular text for downstream analysis.

```bash
# Extract chrom, position, ref, alt, quality
bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t%QUAL\n' variants.vcf.gz > variants.txt

# With header row (-H adds #-prefixed column names)
bcftools query -H -f '%CHROM\t%POS\t%REF\t%ALT\t%QUAL\n' variants.vcf.gz > variants.tsv

# Per-sample genotypes and allele depths
bcftools query -f '[%SAMPLE\t%GT\t%AD\n]' variants.vcf.gz > genotypes.txt
# Output: sample1  0/1  25,18  (ref_depth,alt_depth)
```

```bash
# Rare variants (AF < 1%)
bcftools query -i 'AF<0.01' -f '%CHROM\t%POS\t%REF\t%ALT\t%AF\n' \
    variants.vcf.gz > rare_variants.txt

# Count variants per chromosome
bcftools query -f '%CHROM\n' variants.vcf.gz | sort | uniq -c | sort -rn

# Extract genotype matrix across all samples
bcftools query -f '%CHROM:%POS\t[%GT\t]\n' -H variants.vcf.gz > genotype_matrix.tsv
```

### Module 4: Multi-file Operations

Combine VCF files from multiple samples (merge) or chromosomes (concat).

```bash
# Merge: join VCFs from DIFFERENT sample sets (same variants)
bcftools merge sample1.vcf.gz sample2.vcf.gz sample3.vcf.gz \
    -O z -o cohort.vcf.gz

# Merge with auto-indexing and threading
bcftools merge -O b -W --threads 4 sample*.vcf.gz > cohort.bcf

# Concat: join VCFs from SAME sample set (different chromosomes or batches)
bcftools concat chr1.vcf.gz chr2.vcf.gz chr3.vcf.gz -O z -o full.vcf.gz

# Concat with overlap handling (from batched calling)
bcftools concat -a --threads 4 batch*.vcf.gz -O z -o concat.vcf.gz
```

```bash
# Pipeline: merge → filter → normalize
bcftools merge sample1.vcf.gz sample2.vcf.gz \
    | bcftools filter -i 'QUAL>20' \
    | bcftools norm -d any -f genome.fa \
    | bcftools view -O z -o merged_clean.vcf.gz
bcftools index -t merged_clean.vcf.gz

# Extract genotype matrix from merged cohort
bcftools merge cohort*.vcf.gz | bcftools query -f '[%GT\t]\n' > gt_matrix.tsv
```

### Module 5: Variant Annotation

Add identifiers, gene annotations, or external data to VCF records.

```bash
# Add rsIDs from dbSNP
bcftools annotate -a dbSNP.vcf.gz -c ID variants.vcf.gz -O z -o rsid_annotated.vcf.gz

# Annotate with BED file (adds gene names)
bcftools annotate -a genes.bed.gz \
    -h <(echo '##INFO=<ID=GENE,Number=1,Type=String,Description="Gene name">') \
    -c CHROM,FROM,TO,GENE \
    variants.vcf.gz -O z -o gene_annotated.vcf.gz

# Remove unwanted INFO fields
bcftools annotate -x INFO/AC,INFO/AN,INFO/MQ variants.vcf.gz -O v -o stripped.vcf
```

```bash
# Normalize: left-align indels, split multi-allelic records
bcftools norm -f reference.fa variants.vcf.gz -O v -o normalized.vcf

# Split multi-allelic sites into separate records
bcftools norm -m -any variants.vcf.gz -O v -o split.vcf

# Deduplicate overlapping records
bcftools norm -d any variants.vcf.gz -O z -o deduped.vcf.gz

# Full normalize pipeline
bcftools norm -m -any variants.vcf.gz | \
    bcftools norm -d any -f reference.fa | \
    bcftools view -O z -o normalized_split.vcf.gz
```

### Module 6: Statistics and QC

Generate summary metrics and per-sample variant counts.

```bash
# Full VCF statistics report
bcftools stats variants.vcf.gz > qc.stats.txt

# Extract Summary Numbers section only
grep "^SN" qc.stats.txt | cut -f3,4
# number of records:    45231
# number of SNPs:       38941
# number of indels:     6290
# ...

# Per-sample stats (PSC = per-sample counts)
bcftools stats -s - variants.vcf.gz | grep "^PSC" > per_sample.txt
# cols: id  sample  hom_RR  het  hom_AA  ts  tv  indel  missing  singleton
```

```bash
# Transition/transversion ratio (genome-wide QC)
bcftools stats variants.vcf.gz | grep "Ts/Tv"
# Ts/Tv ratio: 2.06 (healthy WGS; <1.8 or >2.2 suggests quality issues)

# Check for sample contamination (F-statistic per sample)
bcftools stats -s - variants.vcf.gz | grep "^PSC" | awk '{print $2, $9}'
# sample  F_missing (high = poor sample quality)

# Variant calling (mpileup → call pipeline)
samtools mpileup -Ou -f genome.fa *.bam | bcftools call -m -v -Oz -o calls.vcf.gz
bcftools stats calls.vcf.gz | grep "^SN"
```

## Key Concepts

### Output Format Flags

```
-O v  → VCF text (uncompressed)       default for human inspection
-O z  → bgzipped VCF (.vcf.gz)        standard for archiving
-O b  → binary BCF (compressed)        fastest for piping
-O u  → binary BCF (uncompressed)      fastest output (no compression)
```

**Rule**: Use `-O b` or `-O u` for intermediate pipeline steps (no I/O overhead). Use `-O z` for files you will store or index with tabix.

### Filter Expression Syntax

Expressions use INFO and FORMAT fields with comparison operators:

```bash
# INFO fields (one value per variant)
QUAL>20          # quality score
DP>10            # total depth
AF<0.05          # allele frequency
MQ>40            # mapping quality

# FORMAT fields (per-sample; use [] to iterate)
GT=="1/1"        # homozygous alternate
AD[1]>5          # alt allele depth > 5
GQ>20            # genotype quality

# Combined
QUAL>20 && DP>10 && AF>0.01
(GT=="0/0" || GT=="1/1") && GQ>30
```

## Common Workflows

### Workflow 1: Variant QC and Filtering Pipeline

**Goal**: Normalize, filter, and annotate a raw variant call set for downstream analysis.

```bash
#!/bin/bash
VCF="raw_calls.vcf.gz"
REF="reference.fa"
DBSNP="dbSNP_hg38.vcf.gz"
FINAL="variants_filtered_annotated.vcf.gz"

# 1. Normalize: left-align indels, split multi-allelic, deduplicate
bcftools norm -m -any $VCF \
    | bcftools norm -d any -f $REF \
    | bcftools view -O z -o normalized.vcf.gz
bcftools index -t normalized.vcf.gz

# 2. Filter by quality and depth
bcftools filter -i 'QUAL>20 && DP>10' normalized.vcf.gz \
    | bcftools filter --SnpGap 3 \
    | bcftools view -f PASS -O z -o filtered.vcf.gz
bcftools index -t filtered.vcf.gz

# 3. Annotate with rsIDs
bcftools annotate -a $DBSNP -c ID filtered.vcf.gz -O z -o $FINAL
bcftools index -t $FINAL

# Report variant counts
echo "Final variant count:"
bcftools stats $FINAL | grep "number of records"
```

### Workflow 2: Multi-sample Cohort Merging and Genotype Extraction

**Goal**: Merge per-sample VCFs into a cohort VCF; extract a genotype matrix for GWAS.

```bash
#!/bin/bash
SAMPLES=(sample1 sample2 sample3 sample4 sample5)

# 1. Ensure all VCFs are indexed
for s in "${SAMPLES[@]}"; do
    bcftools index -t ${s}.vcf.gz
done

# 2. Merge into cohort VCF (only sites present in ALL samples: -m none)
bcftools merge -m none "${SAMPLES[@]/%/.vcf.gz}" \
    -O z --threads 8 -o cohort.vcf.gz
bcftools index -t cohort.vcf.gz

# 3. Filter: PASS, SNPs only, MAF > 1%
bcftools view -f PASS --type snps cohort.vcf.gz \
    | bcftools filter -i 'AF>0.01 && AF<0.99' \
    | bcftools view -O z -o cohort_snps_filtered.vcf.gz

# 4. Extract numeric genotype matrix (for plink/R/Python)
bcftools query -H \
    -f '%CHROM\t%POS\t%REF\t%ALT\t[%GT\t]\n' \
    cohort_snps_filtered.vcf.gz > genotype_matrix.tsv
echo "Genotype matrix: $(wc -l < genotype_matrix.tsv) variants x ${#SAMPLES[@]} samples"
```

## Key Parameters

| Parameter | Command | Default | Range/Options | Effect |
|-----------|---------|---------|---------------|--------|
| `-O` | Most | `v` | `v`,`z`,`b`,`u` | Output format: VCF, bgzip-VCF, BCF, uncompressed BCF |
| `-r` | Most | — | `chr:pos-end` | Region filter (requires tabix index) |
| `-s` | Most | All | sample names | Include specific samples (prefix `^` to exclude) |
| `-i` | filter | — | expression | Include variants matching expression |
| `-e` | filter | — | expression | Exclude variants matching expression |
| `-f` | query | — | format string | Custom output format string |
| `--threads` | Most | 1 | 1–N | Compression/decompression threads |
| `-a` | annotate | — | file path | Annotation source (BED, VCF, TSV) |
| `-m` | norm | none | `-any`, `+any` | Split (−) or join (+) multi-allelic records |
| `-d` | norm | — | `all`,`any`,`snps` | Deduplication strategy |
| `-W` | view | — | flag | Auto-create index after writing |
| `-v` | call | — | flag | Output variant sites only (skip reference sites) |

## Best Practices

1. **Index before region queries**: `bcftools view -r chr1:...` requires a `.tbi` or `.csi` index. Always run `bcftools index -t output.vcf.gz` after creating any bgzipped VCF.

2. **Normalize before merging or annotation**: Different callers represent the same indel differently. Run `bcftools norm -m -any | bcftools norm -d any -f ref.fa` before merging to prevent duplicate records.

3. **Use `-O u` for pipeline intermediates**: Uncompressed BCF output (`-O u`) eliminates compression/decompression overhead in multi-step pipes — typically 2-3× faster than `-O z`.

4. **Verify Ts/Tv ratio after calling**: `bcftools stats variants.vcf.gz | grep Ts/Tv`. For human WGS, expect 2.0–2.1; exome 2.5–3.0. Values outside these ranges indicate quality problems.

5. **Filter before merge for large cohorts**: Filtering per-sample VCFs before merging reduces memory and I/O. Apply site-level QC (`QUAL>20 && DP>5`) to each sample before `bcftools merge`.

6. **Check chromosome naming consistency**: bcftools fails silently if merging `chr1`-style with `1`-style VCFs. Verify with `bcftools view -h file.vcf.gz | grep "^##contig"`.

## Common Recipes

### Recipe: Count Variants Before and After Filtering

```bash
echo "Before:" $(bcftools view -c 1 raw.vcf.gz | wc -l)
echo "PASS only:" $(bcftools view -f PASS raw.vcf.gz | bcftools view -c 1 | wc -l)
echo "SNPs PASS:" $(bcftools view -f PASS --type snps raw.vcf.gz | bcftools view -c 1 | wc -l)
```

### Recipe: Extract Heterozygous Sites for One Sample

```bash
bcftools view -s SAMPLE_A variants.vcf.gz \
    | bcftools filter -i 'GT="0/1"' \
    | bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\n' > het_sites.txt
echo "$(wc -l < het_sites.txt) heterozygous sites"
```

### Recipe: Compare Two VCF Files for Concordance

```bash
# Find variants unique to each file and shared
bcftools isec -p isec_dir file1.vcf.gz file2.vcf.gz
ls isec_dir/
# 0000.vcf: private to file1
# 0001.vcf: private to file2
# 0002.vcf: shared (from file1 perspective)
# 0003.vcf: shared (from file2 perspective)
echo "Shared: $(wc -l < isec_dir/0002.vcf) variants"
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Missing index` error | VCF not indexed (needed for `-r` region queries) | Run `bcftools index -t file.vcf.gz` |
| `[E::vcf_parse_format]` parse error | Malformed VCF FORMAT or INFO field | Validate: `bcftools view file.vcf.gz 2>&1 \| head -5`; check source tool version |
| Empty filter output | Expression too strict or field missing | Test expression: `bcftools view -h file.vcf.gz \| grep "##INFO=<ID=QUAL"` |
| Merge: sample duplication | Duplicate sample names across input VCFs | Rename with `bcftools reheader -s new_names.txt sample.vcf.gz` before merging |
| Wrong Ts/Tv ratio (<1.8) | Low-quality calls or poor coverage | Apply stricter quality filter (`QUAL>30 && DP>15`); check alignment quality |
| `concat` fails with overlap | Overlapping regions in input VCFs | Use `-a` flag: `bcftools concat -a file1.vcf.gz file2.vcf.gz` |
| Annotation mismatch | chr naming conflict (chr1 vs 1) | Check: `bcftools view -h file.vcf.gz \| grep contig`; rename with `bcftools annotate --rename-chrs` |
| `query` returns empty fields | FORMAT field not populated for sample | Check VCF header: `bcftools view -h file.vcf.gz \| grep FORMAT` |

## Related Skills

- **samtools-bam-processing** — BAM processing that feeds into bcftools variant calling pipeline
- **bedtools-genomic-intervals** — intersecting VCF variants with genomic features (genes, regions)
- **gget-genomic-databases** — Ensembl/NCBI queries to annotate variant gene context

## References

- [bcftools documentation](https://samtools.github.io/bcftools/bcftools.html) — complete command reference
- [GitHub: samtools/bcftools](https://github.com/samtools/bcftools) — source code, releases, issue tracker
- Danecek et al. (2021) "Twelve years of SAMtools and BCFtools" — [GigaScience 10(2)](https://doi.org/10.1093/gigascience/giab008)
- [VCF file format specification](https://samtools.github.io/hts-specs/VCFv4.3.pdf) — field definitions and encoding rules
