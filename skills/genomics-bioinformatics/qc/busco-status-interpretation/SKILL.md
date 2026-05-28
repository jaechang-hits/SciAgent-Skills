---
name: busco-status-interpretation
description: "Guide to interpreting BUSCO completeness statuses: why Duplicated BUSCOs count as complete, parsing output files, computing/comparing completeness across proteomes/genomes, common counting mistakes. Use when running BUSCO QC, comparing assemblies, or reporting completeness. See also: prokka-genome-annotation for annotation workflows feeding BUSCO."
license: CC-BY-4.0
---

# BUSCO Status Interpretation Guide

## Overview

BUSCO (Benchmarking Universal Single-Copy Orthologs) is the standard tool for assessing genome, transcriptome, and proteome completeness by searching for conserved single-copy orthologs from the OrthoDB database. Correct interpretation of BUSCO output is essential for genome quality assessment, comparative genomics, and publication-ready reporting. The most common analytical error is excluding Duplicated BUSCOs from completeness counts, which artificially penalizes polyploid organisms and assemblies with legitimate gene duplications.

This guide covers BUSCO status categories, output file formats, parsing strategies, cross-proteome comparisons, lineage dataset selection, and common pitfalls in BUSCO interpretation.

---

## Key Concepts

### BUSCO Status Categories

BUSCO assigns each searched ortholog one of four statuses:

| Status | Abbreviation | Meaning | Count as Complete? |
|---|---|---|---|
| **Complete (single-copy)** | S | Found exactly once in the genome/proteome | YES |
| **Duplicated** | D | Found more than once (multiple copies) | YES |
| **Fragmented** | F | Partial match, likely incomplete gene model | NO |
| **Missing** | M | Not detected at all | NO |

The headline completeness percentage (C%) reported by BUSCO is always S + D combined. Individual category counts (S, D, F, M) are reported for transparency and should be included in publications.

### Why Duplicated Equals Complete

A Duplicated BUSCO means the ortholog IS present and fully intact in the genome or proteome -- it simply exists in more than one copy. This can occur through:

- Whole-genome duplication (common in plants, fish, and amphibians)
- Tandem or segmental duplication events
- Recent polyploidy
- Proteomes containing multiple isoforms per gene

The gene is not incomplete or absent. Excluding Duplicated BUSCOs from completeness counts would incorrectly penalize polyploid organisms, recently duplicated genomes, or proteomes that include isoform-level annotations. The correct completeness formula is always:

```
Completeness (%) = (Complete_single_copy + Duplicated) / Total_BUSCOs * 100
```

A high Duplicated fraction is not inherently problematic -- it is biologically informative. For example, the zebrafish genome (a teleost with an ancient whole-genome duplication) routinely shows 15-25% Duplicated BUSCOs, and this is expected.

### BUSCO Output Formats

BUSCO produces two primary output formats relevant to downstream analysis:

**Short summary format** -- a single-line notation found in `short_summary.*.txt`:

```
C:95.0%[S:90.0%,D:5.0%],F:3.0%,M:2.0%,n:255
```

Where C = Complete (S + D), S = Single-copy, D = Duplicated, F = Fragmented, M = Missing, and n = total BUSCO groups searched.

**Full table format** -- a TSV file (`full_table.tsv`) with per-ortholog results containing columns for BUSCO ID, Status, Sequence, Score, and Length. This file enables detailed per-gene analysis, filtering, and cross-species comparisons.

---

## Decision Framework

When deciding whether and how to use BUSCO for quality assessment:

```
Question: What are you assessing?
├── Genome assembly completeness
│   ├── Draft assembly → Run BUSCO in genome mode
│   └── Polished/final assembly → Run BUSCO in genome mode, report in publication
├── Transcriptome completeness
│   └── De novo assembly → Run BUSCO in transcriptome mode (expect higher D%)
├── Proteome / annotation completeness
│   └── Predicted proteins → Run BUSCO in protein mode
└── Comparing multiple assemblies
    └── Same lineage dataset across all → Use compare_proteome_completeness pattern
```

### Lineage Dataset Selection

| Organism type | Recommended lineage | Example dataset | Notes |
|---|---|---|---|
| Broad eukaryotic screen | eukaryota | `eukaryota_odb10` | Low resolution, useful for initial checks |
| Vertebrate | vertebrata or class-level | `mammalia_odb10`, `actinopterygii_odb10` | Class-level gives better resolution |
| Insect | insecta or order-level | `diptera_odb10`, `hymenoptera_odb10` | Order-level preferred when available |
| Plant | viridiplantae or more specific | `embryophyta_odb10`, `eudicots_odb10` | Plants often show high D% due to polyploidy |
| Fungus | fungi or division-level | `ascomycota_odb10`, `basidiomycota_odb10` | Match to known phylogenetic placement |
| Bacterium | bacteria or phylum-level | `proteobacteria_odb10` | Use `--auto-lineage-prok` for unknown bacteria |

**General rule**: Use the most specific lineage dataset that encompasses your organism. More specific datasets contain more BUSCOs and provide higher resolution, but using a dataset that does not include your organism will produce misleadingly low scores.

---

## Best Practices

1. **Always report all four categories (S, D, F, M)**: Do not report only the headline C% value. Reviewers and readers need the breakdown to assess whether high completeness comes from single-copy genes (expected for haploid organisms) or duplicated genes (expected for polyploids). This is now a standard expectation in genome papers.

2. **Use the same lineage dataset for all comparisons**: When comparing assemblies or proteomes, every run must use the identical lineage dataset and BUSCO version. Mixing lineage datasets (e.g., comparing one assembly run with `eukaryota_odb10` against another with `metazoa_odb10`) produces incomparable results.

3. **Choose the most specific lineage available**: More specific lineage datasets provide more BUSCO markers and finer resolution. A vertebrate genome assessed with `eukaryota_odb10` (255 markers) gives a much coarser picture than one assessed with `mammalia_odb10` (9,226 markers).

4. **Interpret Duplicated percentage in biological context**: High D% in plants, teleost fish, or salmonids is expected due to known whole-genome duplication events. High D% in a haploid bacterium, however, may indicate assembly artifacts (e.g., uncollapsed haplotypes or contamination).

5. **Run BUSCO on the correct input type**: Use genome mode for assemblies (FASTA of contigs/scaffolds), transcriptome mode for de novo transcriptome assemblies, and protein mode for predicted proteomes. Using the wrong mode produces misleading results because BUSCO applies different search strategies for each.

6. **Include BUSCO version and dataset in methods sections**: Reproducibility requires reporting the exact BUSCO version, OrthoDB dataset version, and any non-default parameters used. Example: "Completeness was assessed with BUSCO v5.4.7 using the mammalia_odb10 dataset."

7. **Validate with BUSCO's built-in plotting**: Use `generate_plot.py` to create the standard BUSCO stacked bar chart for visual comparison across assemblies. This standardized visualization is widely recognized by reviewers.

---

## Common Pitfalls

1. **Counting only single-copy BUSCOs as "complete"**: This is the most frequent error. Filtering for `Status == 'Complete'` alone misses all Duplicated entries, which are fully intact orthologs.
   - *How to avoid*: Always filter for both statuses: `df['Status'].isin(['Complete', 'Duplicated'])`. Verify your total matches the C% in the short summary.

2. **Comparing results across different lineage datasets**: BUSCO scores from `eukaryota_odb10` (255 groups) and `insecta_odb10` (1,367 groups) are not comparable because they search for different sets of orthologs with different expected counts.
   - *How to avoid*: Standardize on a single lineage dataset for all assemblies in a comparison. Document the dataset in your methods.

3. **Interpreting high Duplicated percentage as an assembly error**: For polyploid organisms (many plants, some fish, some amphibians), high D% is biologically correct. Flagging it as an error can lead to unnecessary reassembly or incorrect filtering.
   - *How to avoid*: Check the organism's known ploidy level and duplication history before interpreting D%. Compare against published BUSCO results for closely related species.

4. **Using a lineage dataset that does not encompass the organism**: Running a fungal genome through `insecta_odb10` will produce near-zero completeness, not because the assembly is poor but because the wrong orthologs are being searched.
   - *How to avoid*: Use `--auto-lineage` for unknown organisms, or verify phylogenetic placement before selecting a dataset. Check the OrthoDB taxonomy browser.

5. **Ignoring Fragmented BUSCOs during troubleshooting**: A high Fragmented percentage often indicates real problems -- truncated gene models, poor assembly in genic regions, or incomplete polishing -- that are actionable.
   - *How to avoid*: Investigate the full_table.tsv for Fragmented entries. Check whether they cluster in specific genomic regions or functional categories. Consider additional polishing rounds if F% is above 5-10%.

6. **Not accounting for BUSCO version differences**: BUSCO v3, v4, and v5 use different algorithms, datasets, and scoring thresholds. Results are not directly comparable across major versions.
   - *How to avoid*: Re-run all samples with the same BUSCO version when performing comparisons. Note the version in all reports.

7. **Reporting completeness without the total BUSCO count (n)**: Saying "95% complete" is ambiguous without knowing whether that is 95% of 255 BUSCOs (eukaryota) or 95% of 9,226 BUSCOs (mammalia).
   - *How to avoid*: Always report n alongside percentages. Use the notation format: `C:95.0%[S:90.0%,D:5.0%],F:3.0%,M:2.0%,n:255`.

---

## Workflow

1. **Select lineage dataset**
   - Identify the organism's taxonomic placement
   - Choose the most specific available OrthoDB lineage dataset
   - If uncertain, run `busco --auto-lineage` first

2. **Run BUSCO**
   - Execute BUSCO in the appropriate mode (genome, transcriptome, or protein)
   - Record the exact command, version, and dataset for reproducibility

3. **Parse short summary**
   - Extract the C/S/D/F/M/n values from the short summary file:

```python
import re

def parse_busco_summary(filepath):
    """Parse BUSCO short summary file."""
    with open(filepath) as f:
        text = f.read()

    # Extract the summary line
    match = re.search(
        r'C:(\d+\.?\d*)%\[S:(\d+\.?\d*)%,D:(\d+\.?\d*)%\],'
        r'F:(\d+\.?\d*)%,M:(\d+\.?\d*)%,n:(\d+)',
        text
    )

    if match:
        return {
            'complete_pct': float(match.group(1)),  # S + D
            'single_copy_pct': float(match.group(2)),
            'duplicated_pct': float(match.group(3)),
            'fragmented_pct': float(match.group(4)),
            'missing_pct': float(match.group(5)),
            'total': int(match.group(6))
        }
    return None
```

4. **Parse full table for detailed analysis**
   - Load the full_table.tsv for per-ortholog investigation:

```python
import pandas as pd

def parse_busco_full_table(filepath):
    """Parse BUSCO full_table.tsv output."""
    df = pd.read_csv(filepath, sep='\t', comment='#',
                     names=['Busco_id', 'Status', 'Sequence', 'Score', 'Length'])

    # Count by status
    counts = df['Status'].value_counts()
    print(counts)

    # Complete = Complete + Duplicated
    n_complete = counts.get('Complete', 0) + counts.get('Duplicated', 0)
    print(f"\nTotal complete (S+D): {n_complete}")

    return df
```

5. **Count complete BUSCOs correctly**
   - Include both Complete and Duplicated statuses:

```python
def count_complete_buscos(busco_results):
    """Count complete BUSCOs (single-copy + duplicated).

    Args:
        busco_results: DataFrame with columns including 'Status'
                       Status values: 'Complete', 'Duplicated', 'Fragmented', 'Missing'

    Returns:
        int: Count of complete orthologs
    """
    complete_statuses = ['Complete', 'Duplicated']
    n_complete = busco_results['Status'].isin(complete_statuses).sum()

    n_single = (busco_results['Status'] == 'Complete').sum()
    n_duplicated = (busco_results['Status'] == 'Duplicated').sum()
    n_fragmented = (busco_results['Status'] == 'Fragmented').sum()
    n_missing = (busco_results['Status'] == 'Missing').sum()

    print(f"Complete (single-copy): {n_single}")
    print(f"Duplicated: {n_duplicated}")
    print(f"Total complete: {n_complete} (single + duplicated)")
    print(f"Fragmented: {n_fragmented}")
    print(f"Missing: {n_missing}")

    return n_complete
```

   - Common mistake to avoid:

```python
# WRONG: Only counting single-copy as "complete"
n_complete = (busco_results['Status'] == 'Complete').sum()  # Misses duplicated!

# CORRECT: Count both single-copy and duplicated
n_complete = busco_results['Status'].isin(['Complete', 'Duplicated']).sum()
```

6. **Compare across assemblies or proteomes**
   - When benchmarking multiple assemblies, compute completeness uniformly:

```python
def compare_proteome_completeness(busco_results_dict):
    """Compare BUSCO completeness across multiple proteomes.

    Args:
        busco_results_dict: {proteome_name: busco_dataframe}
    """
    summary = []
    for name, df in busco_results_dict.items():
        n_complete = df['Status'].isin(['Complete', 'Duplicated']).sum()
        n_total = len(df)
        pct = 100 * n_complete / n_total
        summary.append({
            'Proteome': name,
            'Complete': n_complete,
            'Total': n_total,
            'Completeness_pct': round(pct, 1)
        })

    summary_df = pd.DataFrame(summary).sort_values('Completeness_pct', ascending=False)
    print(summary_df.to_string(index=False))
    return summary_df
```

7. **Report results**
   - Include all four categories (S, D, F, M) and the total (n)
   - Use BUSCO notation format in text and generate the standard bar plot for figures
   - State the BUSCO version, lineage dataset, and mode in the methods section

---

## Further Reading

- [BUSCO User Guide](https://busco.ezlab.org/busco_userguide.html) -- Official documentation covering installation, usage modes, lineage datasets, and interpretation guidelines
- [Manni et al. (2021) "BUSCO Update"](https://doi.org/10.1093/molbev/msab199) -- The BUSCO v5 paper describing the current framework, metaeuk integration, and auto-lineage selection (Molecular Biology and Evolution)
- [OrthoDB](https://www.orthodb.org/) -- The underlying database of orthologs that BUSCO uses; useful for understanding lineage dataset composition and ortholog definitions
- [Simao et al. (2015) "BUSCO"](https://doi.org/10.1093/bioinformatics/btv351) -- The original BUSCO paper establishing the completeness assessment framework (Bioinformatics)

---

## Related Skills

- `prokka-genome-annotation` -- Prokaryotic genome annotation pipeline; BUSCO is commonly run on Prokka-predicted proteomes to assess annotation completeness
- `samtools-bam-processing` -- BAM file processing; alignment quality metrics complement BUSCO completeness for assembly QC
- `multiqc-qc-reports` -- Aggregated QC reporting; MultiQC can incorporate BUSCO results into unified quality reports across samples
