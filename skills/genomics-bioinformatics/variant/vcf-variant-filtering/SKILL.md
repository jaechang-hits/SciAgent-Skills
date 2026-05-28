---
name: vcf-variant-filtering
description: "Guide to quality filtering raw VCF files before computing summary stats (Ts/Tv ratio, variant counts, AF distributions). Covers detecting raw VCFs via FILTER column and QUAL inspection, QUAL-based filtering with bcftools, Ts/Tv interpretation, and when NOT to filter. Read before any variant-level QC task. See bcftools-variant-manipulation for advanced filters, gatk-variant-calling for caller config, samtools-bam-processing for upstream alignment QC."
license: CC-BY-4.0
---

# VCF Variant Filtering Guide

## Overview

Raw VCF files produced by variant callers (GATK HaplotypeCaller, bcftools mpileup, DeepVariant, etc.) contain a mixture of true variants and artifacts from sequencing errors, alignment issues, and low-coverage regions. Computing summary statistics -- Ts/Tv ratio, variant counts, allele frequency distributions -- on unfiltered data yields unreliable results because false-positive calls disproportionately inflate transversion counts and depress the Ts/Tv ratio. This guide covers how to detect whether a VCF is raw, how to apply appropriate quality filters, when filtering is not appropriate, and how to interpret the resulting statistics correctly.

## Key Concepts

### VCF Quality Scores (QUAL Field)

The QUAL column in a VCF file represents the Phred-scaled probability that the variant site is polymorphic. A QUAL score of 30 means a 1-in-1000 chance the call is wrong; a QUAL of 20 means 1-in-100. Variant callers assign QUAL scores based on read evidence, base qualities, and mapping qualities. Low-QUAL variants (below 20-30) are enriched for sequencing errors and alignment artifacts. Filtering on QUAL is the simplest and most widely used first-pass quality control step.

Common QUAL thresholds and their interpretation:

| QUAL Score | Error Probability | Typical Use |
|------------|------------------|-------------|
| 10 | 1 in 10 | Very permissive; rarely appropriate for final calls |
| 20 | 1 in 100 | Lenient filtering; useful for somatic calling with supporting evidence |
| 30 | 1 in 1,000 | Standard default for germline variant filtering |
| 50 | 1 in 100,000 | Stringent; used in clinical or high-confidence applications |
| 100+ | Extremely low | Highly supported variants; may over-filter low-coverage regions |

For GATK-based workflows, VQSR or hard filtering on INFO annotations (QD, FS, MQ, etc.) may supplement or replace QUAL filtering. GATK's recommended hard filters for SNPs include QD < 2.0, FS > 60.0, MQ < 40.0, MQRankSum < -12.5, and ReadPosRankSum < -8.0.

### Ts/Tv Ratio Significance

The transition-to-transversion (Ts/Tv) ratio is a key quality metric for variant call sets. Transitions (A<->G, C<->T) are chemically favored over transversions (all other substitutions) due to the molecular structure of nucleotide bases. Expected Ts/Tv values serve as benchmarks:

- Whole-genome sequencing (WGS): approximately 2.0-2.1
- Whole-exome sequencing (WES): approximately 2.8-3.3 (higher due to CpG enrichment in coding regions)
- Raw/unfiltered call sets: often 1.5-1.8 or lower

A Ts/Tv ratio significantly below the expected range indicates contamination by false-positive transversion calls, which are the hallmark of sequencing errors. After proper quality filtering, the Ts/Tv ratio should rise to the expected range for the assay type.

### Raw vs Filtered VCFs

A "raw" VCF is the direct output of a variant caller before any quality filtering has been applied. A "filtered" VCF has had quality thresholds applied, either by hard filtering (QUAL, DP, QD, etc.) or by model-based filtering (GATK VQSR, CNN). Distinguishing between the two is critical because computing statistics on raw data without disclosure leads to incorrect conclusions.

Indicators that a VCF is raw or unfiltered:

- The filename contains "raw" (e.g., `sample_raw_variants.vcf`)
- The FILTER column contains only `.` (missing) for all records
- A large fraction of variants have QUAL scores below 30
- The Ts/Tv ratio is well below the expected range for the assay type

Indicators that a VCF has already been filtered:

- The FILTER column contains meaningful values (`PASS`, `LowQual`, `VQSRTrancheSNP99.90to100.00`)
- A filter command is recorded in the VCF header (`##FILTER=` and `##bcftools_viewCommand=` lines)

### FILTER Column Semantics

The FILTER column in VCF format has specific semantics defined by the VCF specification:

- `.` (dot) -- filter status has not been applied; the variant is unassessed
- `PASS` -- the variant passed all filters
- Any other value -- the variant failed the named filter(s); multiple filters are semicolon-separated

A common misconception is that `.` means the variant passed. In reality, `.` means no filter has been evaluated, so the variant's quality is unknown. Another misconception is that `PASS` in every row means the file is unfiltered -- some callers (e.g., DeepVariant) mark all emitted variants as PASS because they only output high-confidence calls.

To inspect the FILTER column programmatically:

```bash
# Count occurrences of each FILTER value
bcftools query -f '%FILTER\n' input.vcf | sort | uniq -c | sort -rn | head

# Check if any non-'.' FILTER values exist
bcftools query -f '%FILTER\n' input.vcf | grep -v '^\.$' | head
```

Understanding the FILTER column is the first step in any VCF quality assessment. Always inspect it before deciding whether additional filtering is needed.

## Decision Framework

```
Is the VCF raw or unfiltered?
├── Yes (FILTER='.', many low-QUAL variants)
│   ├── Does the user ask for RAW statistics specifically?
│   │   ├── Yes → Do NOT filter; compute on data as-is, note it is raw
│   │   └── No → Apply QUAL>=30 filter before computing statistics
│   └── Does the user specify a custom threshold?
│       ├── Yes → Use their threshold
│       └── No → Default to QUAL>=30
├── No (FILTER has PASS/other values, filtered header present)
│   ├── Does the user ask for additional filtering?
│   │   ├── Yes → Apply requested filter
│   │   └── No → Compute statistics on existing filtered set
│   └── Does the Ts/Tv ratio look suspicious despite filtering?
│       └── Yes → Investigate; may need stricter thresholds
└── Uncertain
    └── Inspect FILTER column and QUAL distribution to determine status
```

| Scenario | Action | Rationale |
|----------|--------|-----------|
| Raw VCF, general statistics requested | Apply QUAL>=30 before computing | Low-QUAL variants are enriched for errors and bias all statistics |
| Raw VCF, user explicitly asks for raw stats | Compute as-is, report that data is unfiltered | Respect the user's intent; they may be evaluating caller performance |
| Raw VCF, user specifies threshold (e.g., QUAL>=50) | Use the user-specified threshold | User has domain-specific requirements |
| Pre-filtered VCF (FILTER=PASS present) | Compute without additional QUAL filter | Double-filtering may remove true variants unnecessarily |
| VCF with mixed FILTER values | Filter to PASS-only with `bcftools view -f PASS` | Non-PASS variants were flagged for a reason |
| VQSR-filtered VCF | Respect existing tranche filtering | VQSR is a more sophisticated filter than simple QUAL thresholds |
| Small panel or targeted sequencing | Consider lower QUAL threshold (e.g., 20) | Small panels have different error profiles and fewer variants |

## Best Practices

1. **Always inspect the VCF before computing statistics.** Check the FILTER column distribution and QUAL score distribution before running any summary. A 30-second inspection prevents publishing misleading numbers. Use `bcftools query -f '%FILTER\n' input.vcf | sort | uniq -c | sort -rn | head` to get a quick overview.

2. **Use established CLI tools instead of custom parsers.** bcftools, vcftools, and similar domain-specific tools handle edge cases that custom parsers typically miss: multi-allelic sites, complex variants, missing genotypes, and proper transition/transversion classification. Writing a Python parser to count Ts/Tv is error-prone and unnecessary.

   ```bash
   # Preferred: use bcftools for Ts/Tv computation
   bcftools stats input.vcf | grep ^TSTV

   # Preferred: use bcftools for variant counts
   bcftools stats input.vcf | grep ^SN
   ```

3. **Report what filtering was applied (or not).** Every time you present VCF summary statistics, state clearly whether the data was filtered, what threshold was used, and how many variants passed. This is essential for reproducibility and for the reader to assess the validity of the results.

4. **Use QUAL>=30 as a sensible default, not a universal rule.** QUAL>=30 (1-in-1000 error rate) is a widely used default for first-pass filtering of germline variant calls. However, different applications may warrant different thresholds: somatic variant calling may use lower thresholds with additional evidence, while clinical applications may demand stricter cutoffs. When in doubt, QUAL>=30 is a defensible starting point.

5. **Combine filtering and statistics in a single pipeline.** Piping the filtered output directly into the statistics command avoids creating intermediate files and ensures you never accidentally compute statistics on the wrong file.

   ```bash
   # Filter and compute statistics in one pipeline
   bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - > filtered_stats.txt
   ```

6. **Validate filtering by checking the Ts/Tv ratio.** After filtering, the Ts/Tv ratio should be in the expected range for the assay type. If it is still low, consider that the variant caller may have systematic issues, the sample may have quality problems, or a stricter filter is needed.

7. **Preserve the original VCF.** Never overwrite the raw VCF with filtered output. Keep the raw file for auditability and in case you need to re-filter with different parameters.

## Common Pitfalls

1. **Computing statistics on raw VCF files without any filtering.** This is the most common and most consequential mistake. Raw Ts/Tv ratios can be 1.5 or lower, suggesting much worse data quality than actually exists, and variant counts will be inflated by thousands of false positives.
   - *How to avoid*: Always check the FILTER column before computing statistics. If FILTER is `.` for all records, apply QUAL>=30 filtering first.

2. **Assuming FILTER='.' means the variant passed.** The dot in the FILTER column means "not assessed," not "passed." Treating unassessed variants as high-quality leads to inclusion of many false positives.
   - *How to avoid*: Distinguish between `.` (unassessed), `PASS` (passed all filters), and named filters (failed). Use `bcftools query -f '%FILTER\n' | sort | uniq -c` to inspect.

3. **Writing custom Python parsers for Ts/Tv calculation.** Custom parsers frequently mishandle multi-allelic sites, complex variants, or edge cases in the VCF format. They also tend to be slower than optimized C-based tools.
   - *How to avoid*: Use `bcftools stats` for Ts/Tv computation. It is well-tested, fast, and handles all VCF edge cases correctly.

4. **Double-filtering a VCF that was already filtered.** Applying QUAL>=30 to a VCF that already went through VQSR or hard filtering can remove true variants that were assigned lower QUAL scores by the caller but passed model-based assessment.
   - *How to avoid*: Inspect the VCF header for filter command records (`##bcftools_viewCommand`, `##GATKCommandLine`) and the FILTER column for non-dot values before adding more filters.

5. **Using the wrong Ts/Tv expectation for the assay type.** Comparing a WES Ts/Tv of 3.0 against a WGS expectation of 2.1 would incorrectly suggest the data is too good, while comparing a WGS Ts/Tv of 2.0 against WES expectations would incorrectly suggest poor quality.
   - *How to avoid*: Know the expected Ts/Tv range for your assay type. WGS: 2.0-2.1; WES: 2.8-3.3; targeted panels: variable depending on target regions.

6. **Forgetting to report the filtering status in results.** Presenting a Ts/Tv ratio without stating whether or how the data was filtered makes the number uninterpretable and non-reproducible.
   - *How to avoid*: Always include a statement like "Ts/Tv computed after QUAL>=30 filtering (N variants passed)" or "Ts/Tv computed on unfiltered raw calls (N total variants)."

7. **Filtering on QUAL alone when richer annotations are available.** GATK and other callers provide INFO-level annotations (QD, FS, MQ, SOR, MQRankSum, ReadPosRankSum) that are more informative than QUAL alone. Relying solely on QUAL when these are available leaves quality on the table.
   - *How to avoid*: Check whether INFO annotations are present. If so, consider GATK hard filtering recommendations or VQSR as a more powerful alternative to simple QUAL filtering.

## Workflow

1. **Inspect the VCF metadata and FILTER column**
   - Check the VCF header for caller information and existing filter records
   - Examine the FILTER column distribution

   ```bash
   # View header for caller and filter information
   bcftools view -h input.vcf | grep -E '##(FILTER|source|GATKCommandLine|bcftools)'

   # Check FILTER column values
   bcftools query -f '%FILTER\n' input.vcf | sort | uniq -c | sort -rn | head
   ```

2. **Assess QUAL score distribution**
   - Determine the proportion of low-QUAL variants

   ```bash
   # Check QUAL distribution
   bcftools query -f '%QUAL\n' input.vcf | awk '{if($1<30) low++; else high++} END {print "QUAL<30:", low+0, "QUAL>=30:", high+0}'
   ```

   - Decision point: If most variants are QUAL>=30 and FILTER=PASS, skip to Step 4. If FILTER=`.` and many low-QUAL variants exist, proceed to Step 3.

3. **Apply quality filtering**
   - Use the appropriate threshold (default QUAL>=30 unless otherwise specified)

   ```bash
   # Apply QUAL>=30 filter
   bcftools view -i 'QUAL>=30' input.vcf -Oz -o filtered.vcf.gz
   bcftools index filtered.vcf.gz
   ```

4. **Compute summary statistics**
   - Extract Ts/Tv ratio, variant counts, and other metrics

   ```bash
   # Ts/Tv ratio from filtered VCF
   bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - | grep ^TSTV | cut -f5

   # Full summary numbers
   bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - | grep ^SN

   # Per-sample statistics
   bcftools stats -s - input.vcf | grep ^PSC
   ```

5. **Compare before and after filtering**
   - Count variants before and after to quantify the impact of filtering

   ```bash
   # Count variants before filtering
   bcftools view -H input.vcf | wc -l

   # Count variants after filtering
   bcftools view -i 'QUAL>=30' input.vcf | bcftools view -H | wc -l

   # Compare Ts/Tv before and after
   echo "=== Before filtering ==="
   bcftools stats input.vcf | grep ^TSTV
   echo "=== After QUAL>=30 filtering ==="
   bcftools view -i 'QUAL>=30' input.vcf | bcftools stats - | grep ^TSTV
   ```

6. **Validate and report**
   - Check that Ts/Tv is within the expected range for the assay type (WGS: 2.0-2.1, WES: 2.8-3.3)
   - If Ts/Tv is still below expected range after filtering, investigate sample quality or consider stricter thresholds
   - Report the filtering applied, number of variants before and after, and the resulting statistics
   - Include the bcftools command used so the analysis is fully reproducible

## Protocol Guidelines

1. **Pre-analysis inspection is non-negotiable.** Before any VCF analysis, run `bcftools query -f '%FILTER\n'` and examine the QUAL distribution. This takes seconds and prevents hours of wasted analysis on unreliable data.

2. **Default to QUAL>=30 for unlabeled VCFs.** When the filtering status is ambiguous and the user has not specified a threshold, QUAL>=30 is the standard community default. Document this choice explicitly in the output.

3. **Never silently filter.** If you apply filtering, always report it. If you choose not to filter, state why. Transparency in filtering decisions is fundamental to reproducible genomics.

4. **Use piped commands for efficiency.** Chain `bcftools view` and `bcftools stats` in a pipe rather than writing intermediate files. This is faster, uses less disk, and reduces the chance of analyzing the wrong file.

5. **Verify with Ts/Tv as a sanity check.** After any filtering operation, compute Ts/Tv as a quality control metric. If the ratio does not improve or remains outside the expected range, reassess the filtering strategy or investigate upstream data quality issues.

## Further Reading

- [bcftools documentation](https://samtools.github.io/bcftools/) -- Comprehensive reference for bcftools commands, filtering expressions, and statistics output format
- [VCF specification (v4.3+)](https://samtools.github.io/hts-specs/VCFv4.3.pdf) -- Formal definition of VCF format including FILTER column semantics, QUAL field, and INFO annotations
- [GATK Best Practices for Germline Short Variant Discovery](https://gatk.broadinstitute.org/hc/en-us/articles/360035535932-Germline-short-variant-discovery-SNPs-Indels) -- Recommended filtering strategies including VQSR and hard filtering thresholds for GATK-called variants

## Related Skills

- `bcftools-variant-manipulation` -- Detailed bcftools usage for subsetting, merging, annotating, and manipulating VCF files beyond simple filtering
- `gatk-variant-calling` -- Upstream variant calling with GATK HaplotypeCaller, including VQSR and hard filtering configuration
- `samtools-bam-processing` -- BAM file quality control and processing steps that precede variant calling and affect downstream VCF quality
