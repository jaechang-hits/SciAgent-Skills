---
name: busco-status-interpretation
description: "Correct interpretation of BUSCO completeness statuses. Covers why Duplicated BUSCOs count as complete, how to compute completeness across proteomes, and common counting mistakes."
license: CC-BY-4.0
compatibility: Python 3.10+, BUSCO 5.0+
metadata:
  authors: HITS
  version: "1.0"
---

# BUSCO Status Interpretation Guide

## Overview

This guide covers the correct interpretation of BUSCO (Benchmarking Universal Single-Copy Orthologs) status categories when counting complete orthologs across proteomes or genomes. The most common error is excluding Duplicated BUSCOs from completeness counts.

---

## Rule 1 (MANDATORY): Include Both Complete AND Duplicated as "Complete"

**CRITICAL: When counting "complete" orthologs across proteomes, include both "Complete" (single-copy) AND "Duplicated" statuses. Duplicated BUSCOs are still complete and present -- they just have more than one copy.**

### BUSCO Status Categories

| Status | Meaning | Count as Complete? |
|---|---|---|
| **Complete** (single-copy, S) | Found exactly once in the genome/proteome | YES |
| **Duplicated** (D) | Found more than once (multiple copies) | YES |
| **Fragmented** (F) | Partial match, likely incomplete | NO |
| **Missing** (M) | Not found at all | NO |

### Why Duplicated = Complete

A duplicated BUSCO means:
- The ortholog IS present in the genome/proteome
- It has been duplicated (e.g., via whole-genome duplication, tandem duplication)
- The gene is fully intact and functional in at least one copy
- It is NOT incomplete or absent

Excluding duplicated BUSCOs would incorrectly penalize polyploid organisms, recently duplicated genomes, or proteomes with isoforms.

### Correct Computation

```python
import pandas as pd

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

### Common Mistake

```python
# WRONG: Only counting single-copy as "complete"
n_complete = (busco_results['Status'] == 'Complete').sum()  # Misses duplicated!

# CORRECT: Count both single-copy and duplicated
n_complete = busco_results['Status'].isin(['Complete', 'Duplicated']).sum()
```

---

## Rule 2: Parsing BUSCO Output Files

### Short Summary Format

BUSCO short summary files typically contain:

```
# BUSCO version is: 5.x.x
# The lineage dataset is: eukaryota_odb10
# Summarized benchmarking in BUSCO notation:
	C:95.0%[S:90.0%,D:5.0%],F:3.0%,M:2.0%,n:255
```

Where:
- `C` = Complete (S + D combined)
- `S` = Single-copy
- `D` = Duplicated
- `F` = Fragmented
- `M` = Missing
- `n` = Total BUSCO groups searched

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

### Full Table Format

```python
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

---

## Rule 3: Comparing Completeness Across Proteomes

When comparing BUSCO completeness across multiple proteomes:

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

---

## Checklist

Before reporting BUSCO completeness results, verify:

- [ ] "Complete" count includes BOTH single-copy AND duplicated
- [ ] Only "Fragmented" and "Missing" are excluded from completeness
- [ ] The BUSCO lineage dataset used is appropriate for the organism
- [ ] Individual category counts (S, D, F, M) are reported for transparency
- [ ] Completeness percentage matches: C% = (S + D) / n * 100
