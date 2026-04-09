---
name: pysam-genomic-files
description: "Read/write SAM/BAM/CRAM alignments, VCF/BCF variants, FASTA/FASTQ sequences. Region queries, coverage/pileup analysis, variant filtering, read group extraction. Python wrapper for htslib with samtools/bcftools CLI access. For alignment pipelines use STAR/BWA; for variant calling use GATK/DeepVariant."
license: MIT
---

# Pysam — Genomic File Toolkit

## Overview

Pysam provides a Pythonic interface to htslib for reading, manipulating, and writing genomic data files. It handles SAM/BAM/CRAM alignments, VCF/BCF variants, and FASTA/FASTQ sequences with efficient region-based random access. Also exposes samtools and bcftools as callable Python functions.

## When to Use

- Reading and querying BAM/CRAM alignment files (region extraction, read filtering)
- Analyzing VCF/BCF variant files (genotype access, variant filtering, annotation)
- Extracting reference sequences from indexed FASTA files
- Calculating per-base coverage and pileup statistics
- Building custom bioinformatics pipelines that combine alignment + variant + sequence data
- Quality control of NGS data (mapping quality, flag filtering, coverage)
- For **alignment from FASTQ** (read mapping), use STAR, BWA, or minimap2 instead
- For **variant calling from BAM**, use GATK or DeepVariant instead

## Prerequisites

```bash
pip install pysam
```

**Note**: Requires htslib C library (bundled with pip install on most platforms). On some Linux systems, may need `libhts-dev` or equivalent. Index files (`.bai`, `.tbi`, `.fai`) required for random access — create with `pysam.index()`, `pysam.tabix_index()`, or `pysam.faidx()`.

## Quick Start

```python
import pysam

# Read BAM file, fetch reads in a region
with pysam.AlignmentFile("sample.bam", "rb") as bam:
    for read in bam.fetch("chr1", 1000, 2000):
        print(f"{read.query_name}: pos={read.reference_start}, mapq={read.mapping_quality}")
    print(f"Total reads in region: {bam.count('chr1', 1000, 2000)}")
```

## Core API

### 1. Alignment Files (SAM/BAM/CRAM)

Read, query, and write aligned sequencing reads.

```python
import pysam

# Open BAM (binary) or SAM (text) file
bam = pysam.AlignmentFile("sample.bam", "rb")  # rb=read BAM, r=read SAM, rc=read CRAM

# Fetch reads overlapping a region (requires .bai index)
for read in bam.fetch("chr1", 10000, 20000):
    print(f"Name: {read.query_name}")
    print(f"  Position: {read.reference_start}-{read.reference_end}")
    print(f"  MAPQ: {read.mapping_quality}")
    print(f"  CIGAR: {read.cigarstring}")
    print(f"  Sequence: {read.query_sequence[:30]}...")
    break

# Count reads in region (fast, no iteration needed)
n_reads = bam.count("chr1", 10000, 20000)
print(f"Reads in region: {n_reads}")

# Filter reads by quality and flags
for read in bam.fetch("chr1", 10000, 20000):
    if read.mapping_quality >= 30 and not read.is_unmapped and not read.is_duplicate:
        pass  # Process high-quality, mapped, non-duplicate reads

bam.close()
```

```python
# Write filtered reads to a new BAM file
with pysam.AlignmentFile("input.bam", "rb") as inbam:
    with pysam.AlignmentFile("filtered.bam", "wb", header=inbam.header) as outbam:
        for read in inbam.fetch("chr1", 10000, 20000):
            if read.mapping_quality >= 30:
                outbam.write(read)

# Index the output
pysam.index("filtered.bam")
print("Created filtered.bam + filtered.bam.bai")
```

### 2. Coverage and Pileup Analysis

Calculate per-base coverage statistics.

```python
import pysam
import numpy as np

bam = pysam.AlignmentFile("sample.bam", "rb")

# Pileup: per-base coverage with read-level detail
for pileup_col in bam.pileup("chr1", 10000, 10100, min_mapping_quality=30):
    bases = [p.alignment.query_sequence[p.query_position]
             for p in pileup_col.pileups if not p.is_del and p.query_position is not None]
    print(f"Pos {pileup_col.reference_pos}: depth={pileup_col.nsegments}, bases={''.join(bases[:5])}")

# Quick coverage count per region (faster than pileup)
coverage = bam.count_coverage("chr1", 10000, 10100, quality_threshold=20)
# Returns tuple of 4 arrays (A, C, G, T counts per position)
total_cov = np.array(coverage).sum(axis=0)
print(f"Mean coverage: {total_cov.mean():.1f}x")

bam.close()
```

### 3. Variant Files (VCF/BCF)

Read, query, and filter genetic variants.

```python
import pysam

# Open VCF/BCF file
vcf = pysam.VariantFile("variants.vcf.gz")

# Iterate all variants
for record in vcf.fetch("chr1", 10000, 50000):
    print(f"{record.chrom}:{record.pos} {record.ref}>{','.join(record.alts or [])}")
    print(f"  QUAL={record.qual}, FILTER={list(record.filter)}")
    print(f"  INFO: {dict(record.info)}")

    # Access genotypes per sample
    for sample in record.samples:
        gt = record.samples[sample]["GT"]
        print(f"  {sample}: GT={gt}")
    break

vcf.close()
```

```python
# Filter variants and write to new VCF
with pysam.VariantFile("variants.vcf.gz") as vcf_in:
    with pysam.VariantFile("filtered.vcf.gz", "wz", header=vcf_in.header) as vcf_out:
        for record in vcf_in:
            if record.qual and record.qual >= 30 and "PASS" in record.filter:
                vcf_out.write(record)

pysam.tabix_index("filtered.vcf.gz", preset="vcf")
print("Created filtered.vcf.gz + filtered.vcf.gz.tbi")
```

### 4. Sequence Files (FASTA/FASTQ)

Random access to reference sequences and sequential reading of raw reads.

```python
import pysam

# FASTA: random access (requires .fai index)
fasta = pysam.FastaFile("reference.fasta")
seq = fasta.fetch("chr1", 10000, 10050)
print(f"Sequence ({len(seq)} bp): {seq}")
print(f"Available contigs: {fasta.references[:5]}")
print(f"Contig lengths: {dict(zip(fasta.references[:3], fasta.lengths[:3]))}")
fasta.close()

# Create FASTA index if needed
# pysam.faidx("reference.fasta")
```

```python
# FASTQ: sequential reading
with pysam.FastxFile("reads.fastq.gz") as fq:
    for i, entry in enumerate(fq):
        print(f"Read {entry.name}: {len(entry.sequence)} bp, mean_qual={sum(entry.get_quality_array())/len(entry.sequence):.1f}")
        if i >= 2:
            break
```

### 5. Read Groups and Sample Information

Extract and filter reads by read group (essential for multi-sample BAM files).

```python
import pysam

bam = pysam.AlignmentFile("multisample.bam", "rb")

# Access read group information from BAM header
print("Read groups in file:")
for rg_dict in bam.header.get("RG", []):
    print(f"  ID: {rg_dict['ID']}, Sample: {rg_dict.get('SM', 'N/A')}, Library: {rg_dict.get('LB', 'N/A')}, Platform: {rg_dict.get('PL', 'N/A')}")

# Get all samples in the BAM (from RG headers)
samples = set()
for rg_dict in bam.header.get("RG", []):
    if "SM" in rg_dict:
        samples.add(rg_dict["SM"])
print(f"Samples in BAM: {sorted(samples)}")

bam.close()
```



```python
# Filter reads by read group ID
def extract_reads_by_rg(bam_path, rg_id, output_path):
    """Extract all reads from a specific read group.

    WARNING: Uses fetch(until_eof=True), which scans the entire BAM sequentially.
    Multi-sample BAMs can be tens to hundreds of GB — this may be slow.
    For large files, prefer region-based filtering:
        for read in bam.fetch("chr1", start, end): ...
    Or use the samtools CLI equivalent (faster for one-off extractions):
        samtools view -b -r <rg_id> input.bam -o output.bam
    """
    with pysam.AlignmentFile(bam_path, "rb") as bam_in:
        with pysam.AlignmentFile(output_path, "wb", header=bam_in.header) as bam_out:
            for read in bam_in.fetch(until_eof=True):
                if read.has_tag("RG") and read.get_tag("RG") == rg_id:
                    bam_out.write(read)
    pysam.index(output_path)
    print(f"Extracted reads from RG:{rg_id} → {output_path}")

extract_reads_by_rg("multisample.bam", "SAMPLE_001_LaneA", "sample001_laneA.bam")
```

```python
from collections import defaultdict
import pysam

# Count reads per sample
def reads_per_sample(bam_path):
    """Count reads per sample from read group information.

    Two distinct "unknown" cases are tracked separately:
    - "no_sm_field":  RG header entry exists but is missing the SM (sample name) field.
    - "undefined_rg": A read carries an RG tag not declared in the BAM header.
    """
    counts = defaultdict(int)
    rg_to_sample = {}

    with pysam.AlignmentFile(bam_path, "rb") as bam:
        # Build RG → sample mapping from header
        for rg_dict in bam.header.get("RG", []):
            rg_id = rg_dict["ID"]
            # (a) RG header entry lacks SM field
            rg_to_sample[rg_id] = rg_dict.get("SM", "no_sm_field")

        # Count reads per resolved sample name
        for read in bam.fetch(until_eof=True):
            if read.has_tag("RG"):
                rg_id = read.get_tag("RG")
                # (b) Read's RG tag is not declared in the header
                sample = rg_to_sample.get(rg_id, "undefined_rg")
                counts[sample] += 1

    return dict(counts)

sample_counts = reads_per_sample("multisample.bam")
for sample, count in sorted(sample_counts.items()):
    print(f"  {sample}: {count:,} reads")
```

### 6. Samtools/Bcftools CLI Access

Call samtools and bcftools commands from Python.

```python
import pysam

# Sort BAM file
pysam.sort("-o", "sorted.bam", "input.bam")

# Index BAM
pysam.index("sorted.bam")

# View region as BAM
pysam.view("-b", "-o", "region.bam", "sorted.bam", "chr1:1000-2000")

# BCFtools: compress and index VCF
pysam.bcftools.view("-O", "z", "-o", "output.vcf.gz", "input.vcf")
pysam.tabix_index("output.vcf.gz", preset="vcf")

# Error handling
try:
    pysam.sort("-o", "output.bam", "nonexistent.bam")
except pysam.SamtoolsError as e:
    print(f"samtools error: {e}")
```

**CLI equivalents** (for reference — use Python API in automated pipelines):
```bash
# These are equivalent to the Python calls above:
samtools sort -o sorted.bam input.bam
samtools index sorted.bam
samtools view -b -o region.bam sorted.bam chr1:1000-2000
bcftools view -O z -o output.vcf.gz input.vcf
```

## Key Concepts

### Coordinate Systems

**Critical**: pysam uses **0-based, half-open** coordinates (Python convention):

| System | Start | End | Example: "bases 1000-2000" |
|--------|-------|-----|---------------------------|
| pysam Python API | 0-based | exclusive | `fetch("chr1", 999, 2000)` |
| samtools region string | 1-based | inclusive | `fetch("chr1:1000-2000")` |
| VCF file format | 1-based | — | `record.pos` = 1-based, `record.start` = 0-based |
| BED format | 0-based | exclusive | `chr1\t999\t2000` |

### Index File Requirements

| File Type | Index Extension | Create With |
|-----------|----------------|-------------|
| BAM | `.bai` | `pysam.index("file.bam")` |
| CRAM | `.crai` | `pysam.index("file.cram")` |
| FASTA | `.fai` | `pysam.faidx("file.fasta")` |
| VCF.gz | `.tbi` | `pysam.tabix_index("file.vcf.gz", preset="vcf")` |
| BCF | `.csi` | `pysam.tabix_index("file.bcf", preset="bcf")` |

Without an index, use `fetch(until_eof=True)` for sequential reading.

### File Mode Strings

| Mode | Format | Direction |
|------|--------|-----------|
| `"rb"` | BAM (binary) | Read |
| `"r"` | SAM (text) | Read |
| `"rc"` | CRAM | Read |
| `"wb"` | BAM | Write |
| `"w"` | SAM | Write |
| `"wz"` | VCF.gz (compressed) | Write |

## Common Workflows

### Workflow 1: Coverage Analysis for Target Regions

**Goal**: Calculate coverage statistics for a set of target regions (e.g., exome capture targets).

```python
import pysam
import numpy as np

def coverage_for_regions(bam_path, regions, min_mapq=30):
    """Calculate coverage stats for a list of (chrom, start, end) regions."""
    results = []
    with pysam.AlignmentFile(bam_path, "rb") as bam:
        for chrom, start, end in regions:
            cov = np.array(bam.count_coverage(chrom, start, end,
                                               quality_threshold=min_mapq))
            total = cov.sum(axis=0)
            results.append({
                "region": f"{chrom}:{start}-{end}",
                "mean_cov": total.mean(),
                "min_cov": total.min(),
                "pct_above_20x": (total >= 20).mean() * 100,
            })
    return results

regions = [("chr1", 10000, 10500), ("chr1", 20000, 20500), ("chr2", 5000, 5500)]
stats = coverage_for_regions("sample.bam", regions)
for s in stats:
    print(f"{s['region']}: mean={s['mean_cov']:.1f}x, min={s['min_cov']}x, ≥20x={s['pct_above_20x']:.1f}%")
```

### Workflow 2: Variant Annotation with Read Support

**Goal**: For each variant in a VCF, count supporting reads from the BAM.

```python
import pysam

def annotate_variants_with_reads(vcf_path, bam_path, output_path):
    """Add read support counts to each variant."""
    with pysam.VariantFile(vcf_path) as vcf_in:
        # Add INFO field to header
        vcf_in.header.add_line(
            '##INFO=<ID=READ_SUPPORT,Number=1,Type=Integer,Description="Reads supporting alt allele">'
        )
        with pysam.VariantFile(output_path, "w", header=vcf_in.header) as vcf_out:
            with pysam.AlignmentFile(bam_path, "rb") as bam:
                for record in vcf_in:
                    alt_count = 0
                    for col in bam.pileup(record.chrom, record.start, record.stop,
                                           min_mapping_quality=30, truncate=True):
                        if col.reference_pos == record.start:
                            for p in col.pileups:
                                if (not p.is_del and p.query_position is not None and
                                    p.alignment.query_sequence[p.query_position] in (record.alts or [])):
                                    alt_count += 1
                    record.info["READ_SUPPORT"] = alt_count
                    vcf_out.write(record)

annotate_variants_with_reads("variants.vcf", "sample.bam", "annotated.vcf")
print("Created annotated.vcf with READ_SUPPORT field")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| mode string | `AlignmentFile`, `VariantFile` | — | `"rb"`, `"r"`, `"rc"`, `"wb"`, `"w"`, `"wz"` | File format and read/write direction |
| `min_mapping_quality` | `pileup()` | 0 | 0–60 | Filter reads below this MAPQ |
| `quality_threshold` | `count_coverage()` | 15 | 0–40 | Minimum base quality to count |
| `truncate` | `pileup()` | False | True/False | Truncate pileup to exact region (True) vs include overlapping reads (False) |
| `until_eof` | `fetch()` | False | True/False | Read all records sequentially without index |
| `multiple_iterators` | `fetch()` | False | True/False | Allow multiple simultaneous iterators (slight overhead) |
| `preset` | `tabix_index()` | — | `"vcf"`, `"bed"`, `"gff"`, `"sam"` | File format for tabix indexing |

## Best Practices

1. **Always use context managers** (`with` statement) for automatic file cleanup. Unclosed files can leak file descriptors.

2. **Create and verify index files first**: Most random-access operations fail silently or raise cryptic errors without indexes. Check for `.bai`/`.tbi`/`.fai` files before queries.

3. **Use `count()` instead of iterating to count reads**: `bam.count("chr1", 1000, 2000)` is much faster than `sum(1 for _ in bam.fetch(...))`.

4. **Use `count_coverage()` for coverage, `pileup()` for base-level detail**: `count_coverage()` is faster when you only need depth numbers. Use `pileup()` only when you need per-read, per-base information.

5. **Anti-pattern — mixing 0-based and 1-based coordinates**: Always double-check coordinate systems when combining pysam (0-based) with VCF files (1-based POS), BED files (0-based), or region strings (1-based). See Key Concepts table.

6. **Anti-pattern — forgetting `truncate=True` in pileup**: Without `truncate=True`, `pileup()` extends to the full extent of overlapping reads, which can be much larger than the requested region.

## Common Recipes

### Recipe: Extract Gene Sequences from Reference

```python
import pysam

def get_gene_sequence(fasta_path, chrom, start, end, strand="+"):
    """Extract gene sequence, reverse-complement if on minus strand."""
    with pysam.FastaFile(fasta_path) as fasta:
        seq = fasta.fetch(chrom, start, end)
        if strand == "-":
            complement = str.maketrans("ACGTacgt", "TGCAtgca")
            seq = seq.translate(complement)[::-1]
        return seq

seq = get_gene_sequence("reference.fasta", "chr1", 10000, 11000, strand="-")
print(f"Gene sequence ({len(seq)} bp): {seq[:50]}...")
```

### Recipe: BAM Statistics Summary

```python
import pysam

def bam_summary(bam_path):
    """Quick summary statistics for a BAM file."""
    with pysam.AlignmentFile(bam_path, "rb") as bam:
        stats = {"total": 0, "mapped": 0, "unmapped": 0, "duplicates": 0, "mapq_ge30": 0}
        for read in bam.fetch(until_eof=True):
            stats["total"] += 1
            if read.is_unmapped:
                stats["unmapped"] += 1
            else:
                stats["mapped"] += 1
                if read.is_duplicate:
                    stats["duplicates"] += 1
                if read.mapping_quality >= 30:
                    stats["mapq_ge30"] += 1
        return stats

summary = bam_summary("sample.bam")
for k, v in summary.items():
    print(f"  {k}: {v:,}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: could not open alignment file` | Missing file or wrong mode string | Check file path; use `"rb"` for BAM, `"r"` for SAM |
| `ValueError: fetch called on bamfile without index` | No `.bai` index file | Run `pysam.index("file.bam")` first |
| Region returns unexpected reads | Reads overlapping boundaries are included | Use `truncate=True` in `pileup()` or filter by `read.reference_start >= start` |
| Coordinate off-by-one errors | Mixing 0-based (pysam) with 1-based (VCF, samtools) | See Key Concepts coordinate table; `record.pos` is 1-based, `record.start` is 0-based |
| `PileupProxy accessed after iterator finished` | Pileup iterator went out of scope | Store needed data from pileup columns immediately, don't save PileupProxy references |
| `SamtoolsError` from CLI calls | Invalid arguments or missing input | Wrap in `try/except pysam.SamtoolsError`; check samtools docs for argument syntax |
| Very slow iteration | Iterating all reads without region query | Use `fetch("chr1", start, end)` for targeted queries; use indexed files |
| Read group filter returns 0 reads | RG tag missing or wrong ID specified | Verify RG tag exists: `read.has_tag("RG")`; list available RGs from `bam.header.get("RG", [])` |

## Related Skills

- **biopython-molecular-biology** — sequence I/O and alignment; complementary for non-BAM sequence formats
- **pydeseq2-differential-expression** — downstream analysis of read counts from BAM coverage data
- **scanpy-scrna-seq** — single-cell analysis; pysam handles the upstream BAM processing

## References

- [Pysam documentation](https://pysam.readthedocs.io/) — official API reference
- [htslib](https://github.com/samtools/htslib) — underlying C library for genomic file formats
- [SAM format specification](https://samtools.github.io/hts-specs/SAMv1.pdf) — SAM/BAM format details
- Li et al. (2009) "The Sequence Alignment/Map format and SAMtools" — [Bioinformatics](https://doi.org/10.1093/bioinformatics/btp352)
