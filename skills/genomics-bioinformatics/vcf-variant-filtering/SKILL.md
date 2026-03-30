---
name: vcf-variant-filtering
description: "Mandatory quality filtering for raw/unfiltered VCF files before computing summary statistics. Covers detection of raw VCFs, QUAL-based filtering with bcftools, and why unfiltered Ts/Tv ratios are unreliable."
license: CC-BY-4.0
compatibility: Python 3.10+, bcftools 1.9+
metadata:
  authors: HITS
  version: "1.0"
---

# VCF Variant Filtering Guide

## Overview

This guide covers mandatory quality filtering of VCF files before computing summary statistics such as Ts/Tv ratio, variant counts, or allele frequency distributions. Raw/unfiltered VCF files contain sequencing errors that inflate transversions and depress the Ts/Tv ratio, leading to incorrect results.

---

## Rule 1 (MANDATORY): Filter Raw VCFs Before Computing Statistics

**CRITICAL: You MUST check whether a VCF file contains raw/unfiltered variants and apply quality filtering BEFORE computing any summary statistics.**

### Why This Matters

Raw VCF files from variant callers (e.g., GATK HaplotypeCaller, bcftools mpileup) contain:
- Low-confidence calls from sequencing errors
- Artifacts from alignment issues
- False positive variants with low QUAL scores

These errors disproportionately affect transversions, which:
- Inflates the transversion count
- Depresses the Ts/Tv ratio (typically from ~2.0-2.1 for whole genome to much lower values)
- Makes all downstream statistics unreliable

### How to Detect Raw/Unfiltered VCFs

Check these indicators:
1. **Filename**: Look for "raw" in the filename (e.g., `sample_raw_variants.vcf`)
2. **FILTER column**: If all records have `.` (missing) or all have `PASS`, the file may be unfiltered
3. **QUAL distribution**: Check if there are many low-QUAL variants

```bash
# Check FILTER column values
bcftools query -f '%FILTER\n' input.vcf | sort | uniq -c | sort -rn | head

# Check QUAL distribution
bcftools query -f '%QUAL\n' input.vcf | awk '{if($1<30) low++; else high++} END {print "QUAL<30:", low, "QUAL>=30:", high}'
```

### Step 1: Apply Quality Filter

```bash
# MANDATORY: Filter by QUAL >= 30 before any statistics
bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - > filtered_stats.txt
```

### Step 2: Extract Statistics from Filtered Output

```bash
# Extract Ts/Tv ratio from filtered VCF
bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - | grep ^TSTV | cut -f5
```

---

## Rule 2: When NOT to Filter

Do NOT apply additional filtering when:
- The question explicitly asks for statistics on the raw/unfiltered VCF
- The VCF has already been filtered (FILTER column contains meaningful values like `PASS`, `LowQual`, etc.)
- The question specifies a different filtering threshold

**Key principle**: If the question says "raw variants" or "unfiltered", and asks for statistics on those specific variants, compute on the data as-is. Only apply default filtering when the question asks for a general statistic without specifying raw/unfiltered.

---

## Rule 3: Prefer CLI Tools Over Custom Parsers

**CRITICAL: Use bcftools, vcftools, or other domain-specific CLI tools instead of writing custom Python VCF parsers.**

```bash
# Good: Use bcftools for Ts/Tv
bcftools stats input.vcf | grep ^TSTV

# Good: Use bcftools for variant counts
bcftools stats input.vcf | grep ^SN

# Bad: Writing a custom Python parser to count transitions/transversions
```

CLI tools handle edge cases correctly:
- Multi-allelic sites
- Indels vs SNPs
- Missing genotypes
- Complex variants

---

## Common Statistics and How to Compute Them

### Ts/Tv Ratio

```bash
# From filtered VCF
bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - | grep ^TSTV
# Output columns: TSTV, id, ts, tv, ts/tv, ts(1st ALT), tv(1st ALT), ts/tv(1st ALT)
```

### Variant Counts by Type

```bash
# Summary numbers from filtered VCF
bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - | grep ^SN
```

### Per-Sample Statistics

```bash
# Per-sample stats
bcftools stats -s - input.vcf | grep ^PSC
```

---

## Checklist

Before reporting VCF summary statistics, verify:

- [ ] Checked whether the VCF is raw/unfiltered (filename, FILTER column)
- [ ] Applied QUAL >= 30 filter if the VCF is raw (unless question explicitly asks for raw stats)
- [ ] Used bcftools/vcftools CLI tools instead of custom parsers
- [ ] Reported the filtering applied (or lack thereof) in the answer
- [ ] Did not over-filter when the question asks about unfiltered data
